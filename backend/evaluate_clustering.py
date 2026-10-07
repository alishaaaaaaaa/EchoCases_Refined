"""
Evaluate EchoCases crime-series detection against the planted series.

generate_cases.py plants 10 known series among ~150 unlinked background cases,
so we know the right answer. This script embeds the narratives with the same
model the app uses, clusters them with the same HDBSCAN settings, and reports
how many series were recovered plus pairwise precision / recall / F1.

Usage (from backend/):
    python generate_cases.py                       # writes cases.csv
    python evaluate_clustering.py                   # one run, app settings
    python evaluate_clustering.py --sweep           # also compare HDBSCAN settings
    python evaluate_clustering.py --seeds 5         # average over 5 regenerated datasets
"""

import argparse
import json
import os
import random

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pandas as pd

from clustering import (
    HDBSCAN_PARAMS,
    cluster_embeddings,
    evaluate_clustering,
    ground_truth_labels,
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # must match app.py


def load_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def evaluate_df(df, embedder, **params):
    truth = ground_truth_labels(df)
    if truth is None:
        raise SystemExit("No ground truth in this dataset (no `series` column or series tags).")
    embeddings = embedder.encode(df["narrative"].astype(str).tolist())
    pred = cluster_embeddings(embeddings, **params)
    return evaluate_clustering(truth, pred), embeddings, truth


def print_report(m, title):
    print(f"\n=== {title} ===")
    print(f"Cases: {m['num_cases']}  ({m['series_cases']} in planted series, "
          f"{m['background_cases']} background)")
    print(f"Series recovered:   {m['series_recovered']}/{m['planted_series']}  "
          f"(series recall {m['series_recall']:.0%})")
    print(f"Clusters found:     {m['clusters_found']}  "
          f"({m['spurious_clusters']} not matching any series; "
          f"series precision {m['series_precision']:.0%})")
    print(f"Pairwise precision: {m['pairwise_precision']:.3f}")
    print(f"Pairwise recall:    {m['pairwise_recall']:.3f}")
    print(f"Pairwise F1:        {m['pairwise_f1']:.3f}")
    print(f"Series cases left as noise:  {m['series_cases_left_as_noise']}/{m['series_cases']}")
    print(f"Background cases clustered:  {m['background_cases_clustered']}/{m['background_cases']}")
    print("\nPer series (recovered = one cluster holds a majority of the series "
          "and is mostly that series):")
    for s in m["per_series"]:
        mark = "OK  " if s["recovered"] else "MISS"
        print(f"  [{mark}] {s['series']:<24} {s['cases_in_best_cluster']}/{s['size']} in "
              f"cluster {s['best_cluster']}  (coverage {s['coverage']:.0%}, "
              f"purity {s['purity']:.0%})")


SWEEP = [
    {"min_cluster_size": 3, "min_samples": 1},
    {"min_cluster_size": 3, "min_samples": 2},
    {"min_cluster_size": 3, "min_samples": 3},
    {"min_cluster_size": 4, "min_samples": 2},
    {"min_cluster_size": 5, "min_samples": 2},
    {"min_cluster_size": 5, "min_samples": None},
]


def run_sweep(embeddings, truth):
    print("\n=== Parameter sweep (same embeddings) ===")
    print(f"{'min_cluster_size':>16} {'min_samples':>11} {'recovered':>9} "
          f"{'clusters':>8} {'pair P':>7} {'pair R':>7} {'pair F1':>7}")
    rows = []
    for params in SWEEP:
        m = evaluate_clustering(truth, cluster_embeddings(embeddings, **params))
        tag = "  <- app" if params == HDBSCAN_PARAMS else ""
        print(f"{params['min_cluster_size']:>16} {str(params['min_samples']):>11} "
              f"{m['series_recovered']:>6}/{m['planted_series']:<2} {m['clusters_found']:>8} "
              f"{m['pairwise_precision']:>7.3f} {m['pairwise_recall']:>7.3f} "
              f"{m['pairwise_f1']:>7.3f}{tag}")
        rows.append({"params": params, **{k: v for k, v in m.items() if k != "per_series"}})
    return rows


def run_seeds(n_seeds, embedder):
    """Regenerate the synthetic dataset with different seeds and average."""
    import generate_cases

    keys = ["series_recovered", "series_precision", "series_recall",
            "pairwise_precision", "pairwise_recall", "pairwise_f1"]
    results = []
    for seed in range(n_seeds):
        random.seed(seed)
        df = pd.DataFrame(generate_cases.generate_cases()).fillna("")
        m, _, _ = evaluate_df(df, embedder)
        results.append(m)
        print(f"seed {seed}: recovered {m['series_recovered']}/{m['planted_series']}, "
              f"pair P {m['pairwise_precision']:.3f}, R {m['pairwise_recall']:.3f}, "
              f"F1 {m['pairwise_f1']:.3f}")
    mean = {k: round(sum(r[k] for r in results) / n_seeds, 3) for k in keys}
    print(f"\nMean over {n_seeds} datasets: " + ", ".join(f"{k}={v}" for k, v in mean.items()))
    return {"seeds": n_seeds, "mean": mean, "runs": results}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="cases.csv", help="dataset with planted series (default: cases.csv)")
    ap.add_argument("--sweep", action="store_true", help="also compare other HDBSCAN settings")
    ap.add_argument("--seeds", type=int, default=0,
                    help="regenerate the dataset N times with different seeds and average")
    ap.add_argument("--out", default="eval_results.json", help="where to write the JSON results")
    args = ap.parse_args()

    embedder = load_embedder()
    output = {"embedding_model": EMBEDDING_MODEL, "hdbscan_params": HDBSCAN_PARAMS}

    if args.seeds:
        output["multi_seed"] = run_seeds(args.seeds, embedder)
    else:
        df = pd.read_csv(args.csv).fillna("")
        metrics, embeddings, truth = evaluate_df(df, embedder)
        print_report(metrics, f"{args.csv} with HDBSCAN{HDBSCAN_PARAMS}")
        output["metrics"] = metrics
        if args.sweep:
            output["sweep"] = run_sweep(embeddings, truth)

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved results to {args.out}")


if __name__ == "__main__":
    main()
