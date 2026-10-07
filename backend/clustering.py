"""
Crime-series clustering and its evaluation.

The clustering lives here (instead of inline in app.py) so the Flask app and
the offline evaluation script run exactly the same algorithm with exactly the
same parameters.
"""

import json
import os
from collections import Counter

import numpy as np
from sklearn.cluster import HDBSCAN
from sklearn.decomposition import PCA

# Default pipeline settings. `python evaluate_clustering.py --compare` picks the
# best settings on tuning datasets, checks them on fresh held-out datasets, and
# writes them to cluster_config.json, which overrides these defaults for both
# the app and the evaluation.
DEFAULT_CONFIG = {
    # What gets embedded: "narrative" (text only) or "narrative+fields"
    # (category, weapon and entry method prepended to the narrative).
    "text": "narrative",
    # Reduce embeddings to this many dimensions with PCA before clustering
    # (None = cluster the raw 384-dim embeddings).
    "reduce_dims": None,
    "min_cluster_size": 3,
    "min_samples": 2,
    "cluster_selection_method": "eom",
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cluster_config.json")
HDBSCAN_KEYS = ("min_cluster_size", "min_samples", "cluster_selection_method")


def load_config():
    """Active pipeline settings: defaults, overridden by cluster_config.json if present."""
    config = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config.update({k: v for k, v in json.load(f).items() if k in DEFAULT_CONFIG})
    return config


def case_texts(df, mode="narrative"):
    """The text that is embedded for each case."""
    narratives = df["narrative"].astype(str)
    if mode == "narrative":
        return narratives.tolist()
    if mode == "narrative+fields":
        texts = []
        for (_, row), narrative in zip(df.iterrows(), narratives):
            parts = []
            for col, label in (("category", "Category"), ("weapon", "Weapon"),
                               ("entry_method", "Entry method")):
                value = str(row.get(col, "")).strip()
                if value and value.lower() != "unknown":
                    parts.append(f"{label}: {value}.")
            texts.append(" ".join(parts + [narrative]))
        return texts
    raise ValueError(f"Unknown text mode: {mode}")


def cluster_embeddings(embeddings, config=None, **overrides):
    """
    Optionally reduce dimensions with PCA, then run HDBSCAN.
    Returns one label per case (-1 = noise).
    """
    config = {**(config or load_config()), **overrides}
    X = np.asarray(embeddings, dtype=float)
    dims = config.get("reduce_dims")
    if dims and dims < min(X.shape):
        X = PCA(n_components=dims, random_state=0).fit_transform(X)
    params = {k: config[k] for k in HDBSCAN_KEYS if k in config}
    return HDBSCAN(**params).fit_predict(X)


# Tags that every generated case carries; anything else in the tags column is
# the name of the planted series the case belongs to.
GENERIC_TAGS = {"cold_case", "unsolved", ""}


def ground_truth_labels(df):
    """
    True series label for every case, or None for background (unlinked) cases.

    Uses an explicit `series` column if the CSV has one; otherwise reads the
    series name that generate_cases.py writes as the first tag
    (e.g. "highway_murders,cold_case,unsolved"). Returns None if the dataset
    carries no ground truth at all (e.g. a real uploaded dataset).
    """
    if "series" in df.columns:
        labels = [str(s).strip() or None for s in df["series"]]
    elif "tags" in df.columns:
        labels = []
        for tags in df["tags"].astype(str):
            series = [t.strip() for t in tags.split(",") if t.strip() not in GENERIC_TAGS]
            labels.append(series[0] if series else None)
    else:
        return None

    return labels if any(labels) else None


def _pairs(n):
    return n * (n - 1) // 2


def evaluate_clustering(true_labels, pred_labels, min_overlap=0.5):
    """
    Score predicted clusters against the planted series.

    true_labels: series name per case, None for background cases.
    pred_labels: HDBSCAN label per case, -1 for noise.

    Two views of the same question:

    * Series recovery: a planted series counts as recovered when a single
      predicted cluster holds at least `min_overlap` of the series' cases AND
      at least `min_overlap` of that cluster is the series (a majority both
      ways, so one giant catch-all cluster can't "recover" everything).
      Series-level precision = recovered series / clusters found;
      series-level recall = recovered series / planted series.

    * Pairwise precision/recall (standard for record linkage): over every pair
      of cases, precision = share of pairs put in the same cluster that really
      are the same series; recall = share of same-series pairs that were put in
      the same cluster. Background cases clustered together count against
      precision, which is the false-linkage cost an investigator would pay.
    """
    true_labels = list(true_labels)
    pred_labels = [int(p) for p in pred_labels]
    if len(true_labels) != len(pred_labels):
        raise ValueError("true_labels and pred_labels must be the same length")

    series_sizes = Counter(t for t in true_labels if t is not None)
    cluster_sizes = Counter(p for p in pred_labels if p != -1)
    joint = Counter(
        (t, p) for t, p in zip(true_labels, pred_labels) if t is not None and p != -1
    )

    # --- Series recovery ---
    per_series = []
    matched_clusters = set()
    for series, size in sorted(series_sizes.items()):
        overlaps = {p: n for (t, p), n in joint.items() if t == series}
        if overlaps:
            best_cluster, overlap = max(overlaps.items(), key=lambda kv: kv[1])
            coverage = overlap / size
            purity = overlap / cluster_sizes[best_cluster]
        else:
            best_cluster, overlap, coverage, purity = None, 0, 0.0, 0.0
        recovered = coverage >= min_overlap and purity >= min_overlap
        if recovered:
            matched_clusters.add(best_cluster)
        per_series.append({
            "series": series,
            "size": size,
            "best_cluster": best_cluster,
            "cases_in_best_cluster": overlap,
            "coverage": round(coverage, 3),
            "purity": round(purity, 3),
            "recovered": recovered,
        })

    n_series = len(series_sizes)
    n_clusters = len(cluster_sizes)
    n_recovered = sum(s["recovered"] for s in per_series)

    # --- Pairwise precision / recall ---
    true_pairs = sum(_pairs(n) for n in series_sizes.values())
    pred_pairs = sum(_pairs(n) for n in cluster_sizes.values())
    correct_pairs = sum(_pairs(n) for n in joint.values())
    pair_precision = correct_pairs / pred_pairs if pred_pairs else 0.0
    pair_recall = correct_pairs / true_pairs if true_pairs else 0.0
    pair_f1 = (
        2 * pair_precision * pair_recall / (pair_precision + pair_recall)
        if pair_precision + pair_recall else 0.0
    )

    series_cases = sum(series_sizes.values())
    series_cases_in_noise = sum(
        1 for t, p in zip(true_labels, pred_labels) if t is not None and p == -1
    )
    background_cases = sum(1 for t in true_labels if t is None)
    background_clustered = sum(
        1 for t, p in zip(true_labels, pred_labels) if t is None and p != -1
    )

    return {
        "num_cases": len(true_labels),
        "planted_series": n_series,
        "clusters_found": n_clusters,
        "series_recovered": n_recovered,
        "series_precision": round(n_recovered / n_clusters, 3) if n_clusters else 0.0,
        "series_recall": round(n_recovered / n_series, 3) if n_series else 0.0,
        "spurious_clusters": n_clusters - len(matched_clusters),
        "pairwise_precision": round(pair_precision, 3),
        "pairwise_recall": round(pair_recall, 3),
        "pairwise_f1": round(pair_f1, 3),
        "series_cases_left_as_noise": series_cases_in_noise,
        "series_cases": series_cases,
        "background_cases_clustered": background_clustered,
        "background_cases": background_cases,
        "min_overlap": min_overlap,
        "per_series": per_series,
    }
