"""
Evaluate EchoCases crime-series detection against the planted series.

generate_cases.py plants 10 known series among 150 unlinked background cases,
so we know the right answer. This script embeds the cases with the same model
the app uses, clusters them with the active settings (cluster_config.json if
present, otherwise the defaults in clustering.py), and reports how many series
were recovered plus pairwise precision / recall / F1.

Usage (from backend/):
    python generate_cases.py                    # writes cases.csv
    python evaluate_clustering.py                # one run on cases.csv
    python evaluate_clustering.py --sweep        # HDBSCAN settings on cases.csv
    python evaluate_clustering.py --seeds 5      # average over 5 regenerated datasets
    python evaluate_clustering.py --compare      # pick the best pipeline settings
                                                 # and save cluster_config.json
    python evaluate_clustering.py --retrieval    # score the similar-case search
                                                 # that feeds RAG (precision@k)

--compare chooses settings on tuning datasets (seeds 0..N-1) and then reports
the chosen settings and the default baseline on held-out datasets
(seeds 1000..1000+N-1) that played no part in the choice. Report the held-out
numbers.
"""

import argparse
import contextlib
import io
import itertools
import json
import os
import random

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pandas as pd

from clustering import (
    CONFIG_PATH,
    DEFAULT_CONFIG,
    case_texts,
    cluster_embeddings,
    evaluate_clustering,
    evaluate_retrieval,
    ground_truth_labels,
    load_config,
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # must match app.py
HELD_OUT_START = 1000
SUMMARY_KEYS = ["series_recovered", "series_precision", "series_recall",
                "pairwise_precision", "pairwise_recall", "pairwise_f1"]


def load_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def generate_dataset(seed):
    import generate_cases
    random.seed(seed)
    with contextlib.redirect_stdout(io.StringIO()):
        return pd.DataFrame(generate_cases.generate_cases()).fillna("")


class Embeddings:
    """Caches embeddings per (dataset, text mode) so comparisons don't re-encode."""

    def __init__(self, embedder):
        self.embedder = embedder
        self.cache = {}

    def get(self, key, df, mode):
        if (key, mode) not in self.cache:
            self.cache[(key, mode)] = self.embedder.encode(case_texts(df, mode))
        return self.cache[(key, mode)]


def score(df, truth, emb, config, key):
    vectors = emb.get(key, df, config["text"])
    return evaluate_clustering(truth, cluster_embeddings(vectors, config))


def mean_metrics(results):
    return {k: round(sum(r[k] for r in results) / len(results), 3) for k in SUMMARY_KEYS}


def describe(config):
    dims = config["reduce_dims"] or "none"
    return (f"text={config['text']:<16} pca={str(dims):<4} "
            f"mcs={config['min_cluster_size']} ms={config['min_samples']} "
            f"sel={config['cluster_selection_method']}")


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


def print_mean(label, mean, n):
    print(f"{label}: recovered {mean['series_recovered']}/10 "
          f"(series recall {mean['series_recall']:.0%}, series precision "
          f"{mean['series_precision']:.0%}), pairwise P {mean['pairwise_precision']:.3f} "
          f"R {mean['pairwise_recall']:.3f} F1 {mean['pairwise_f1']:.3f}  [mean of {n}]")


# --- single dataset ----------------------------------------------------------

SWEEP = [
    {"min_cluster_size": 2, "min_samples": 1},
    {"min_cluster_size": 3, "min_samples": 1},
    {"min_cluster_size": 3, "min_samples": 2},
    {"min_cluster_size": 3, "min_samples": 3},
    {"min_cluster_size": 4, "min_samples": 2},
    {"min_cluster_size": 5, "min_samples": 2},
]


def run_single(csv, emb, config, sweep):
    df = pd.read_csv(csv).fillna("")
    truth = ground_truth_labels(df)
    if truth is None:
        raise SystemExit("No ground truth in this dataset (no `series` column or series tags).")
    metrics = score(df, truth, emb, config, csv)
    print_report(metrics, f"{csv} with {describe(config)}")
    out = {"metrics": metrics}
    if sweep:
        print("\n=== HDBSCAN sweep (same embeddings, other settings unchanged) ===")
        print(f"{'min_cluster_size':>16} {'min_samples':>11} {'recovered':>9} "
              f"{'clusters':>8} {'pair P':>7} {'pair R':>7} {'pair F1':>7}")
        rows = []
        for params in SWEEP:
            cfg = {**config, **params}
            m = score(df, truth, emb, cfg, csv)
            tag = "  <- active" if all(config[k] == v for k, v in params.items()) else ""
            print(f"{params['min_cluster_size']:>16} {str(params['min_samples']):>11} "
                  f"{m['series_recovered']:>6}/{m['planted_series']:<2} {m['clusters_found']:>8} "
                  f"{m['pairwise_precision']:>7.3f} {m['pairwise_recall']:>7.3f} "
                  f"{m['pairwise_f1']:>7.3f}{tag}")
            rows.append({"config": cfg, **{k: m[k] for k in SUMMARY_KEYS}})
        out["sweep"] = rows
    return out


# --- multiple regenerated datasets --------------------------------------------

def datasets(seeds):
    out = []
    for seed in seeds:
        df = generate_dataset(seed)
        out.append((seed, df, ground_truth_labels(df)))
    return out


def run_seeds(n, offset, emb, config):
    results = []
    for seed, df, truth in datasets(range(offset, offset + n)):
        m = score(df, truth, emb, config, seed)
        results.append(m)
        print(f"seed {seed}: recovered {m['series_recovered']}/{m['planted_series']}, "
              f"pair P {m['pairwise_precision']:.3f}, R {m['pairwise_recall']:.3f}, "
              f"F1 {m['pairwise_f1']:.3f}")
    mean = mean_metrics(results)
    print()
    print_mean(describe(config), mean, n)
    return {"seeds": list(range(offset, offset + n)), "config": config, "mean": mean,
            "runs": [{k: r[k] for k in SUMMARY_KEYS} for r in results]}


GRID = {
    "text": ["narrative", "narrative+fields"],
    "reduce_dims": [None, 10, 25, 50],
    "min_cluster_size": [2, 3],
    "min_samples": [1, 2],
    "cluster_selection_method": ["eom", "leaf"],
}


def run_compare(n, emb):
    keys = list(GRID)
    configs = [dict(zip(keys, values)) for values in itertools.product(*GRID.values())]
    if DEFAULT_CONFIG not in configs:
        configs.append(dict(DEFAULT_CONFIG))

    print(f"Tuning on seeds 0-{n - 1}: trying {len(configs)} settings...")
    tuning = datasets(range(n))
    ranked = []
    for cfg in configs:
        mean = mean_metrics([score(df, truth, emb, cfg, seed) for seed, df, truth in tuning])
        ranked.append((cfg, mean))
    # Most series recovered first; pairwise F1 breaks ties.
    ranked.sort(key=lambda r: (r[1]["series_recall"], r[1]["pairwise_f1"]), reverse=True)

    print(f"\n{'rank':>4}  {'settings':<62} {'recovered':>9} {'pair P':>7} {'pair R':>7} {'pair F1':>7}")
    baseline_rank = next(i for i, (c, _) in enumerate(ranked) if c == DEFAULT_CONFIG)
    for i, (cfg, mean) in enumerate(ranked):
        if i < 10 or i == baseline_rank:
            tag = "  <- default" if cfg == DEFAULT_CONFIG else ""
            print(f"{i + 1:>4}  {describe(cfg):<62} {mean['series_recovered']:>9} "
                  f"{mean['pairwise_precision']:>7.3f} {mean['pairwise_recall']:>7.3f} "
                  f"{mean['pairwise_f1']:>7.3f}{tag}")

    best = ranked[0][0]
    held_seeds = range(HELD_OUT_START, HELD_OUT_START + n)
    print(f"\nHeld-out check on fresh seeds {held_seeds.start}-{held_seeds.stop - 1} "
          f"(not used to choose settings):")
    held = datasets(held_seeds)
    base_mean = mean_metrics([score(df, t, emb, DEFAULT_CONFIG, s) for s, df, t in held])
    best_mean = mean_metrics([score(df, t, emb, best, s) for s, df, t in held])
    print_mean("  default ", base_mean, n)
    print_mean("  selected", best_mean, n)

    result = {
        "tuning_seeds": list(range(n)),
        "held_out_seeds": list(held_seeds),
        "selected_config": best,
        "held_out_default": base_mean,
        "held_out_selected": best_mean,
        "tuning_ranking": [{"config": c, **m} for c, m in ranked],
    }

    if best_mean["series_recall"] > base_mean["series_recall"] or (
        best_mean["series_recall"] == base_mean["series_recall"]
        and best_mean["pairwise_f1"] > base_mean["pairwise_f1"]
    ):
        with open(CONFIG_PATH, "w") as f:
            json.dump({**best, "held_out_series_recall": best_mean["series_recall"],
                       "held_out_pairwise_f1": best_mean["pairwise_f1"]}, f, indent=2)
        print(f"\nSelected settings beat the default on held-out data. Saved to "
              f"{os.path.basename(CONFIG_PATH)}; the app and this script now use them.")
    else:
        print("\nSelected settings did not beat the default on held-out data, so "
              "cluster_config.json was not written.")
    return result


def run_retrieval(n, offset, emb, config):
    modes = [config["text"]] + [m for m in ("narrative", "narrative+fields") if m != config["text"]]
    seeds = range(offset, offset + n)
    print(f"Retrieval on seeds {seeds.start}-{seeds.stop - 1}: each series case is a query, "
          f"all other cases are ranked by cosine similarity.\n")
    data = datasets(seeds)
    out = {"seeds": list(seeds), "by_text_mode": {}}
    for mode in modes:
        runs = [evaluate_retrieval(emb.get(seed, df, mode), truth) for seed, df, truth in data]
        keys = [k for k in runs[0] if k not in ("per_series_precision@5", "queries")]
        mean = {k: round(sum(r[k] for r in runs) / n, 3) for k in keys}
        series = sorted(runs[0]["per_series_precision@5"])
        mean["per_series_precision@5"] = {
            s: round(sum(r["per_series_precision@5"][s] for r in runs) / n, 3) for s in series}
        out["by_text_mode"][mode] = mean

        tag = "  (used by the app)" if mode == config["text"] else ""
        print(f"--- embedding text: {mode}{tag} ---")
        print(f"  precision@1:  {mean['precision@1']:.3f}   (top result is from the same series)")
        print(f"  precision@5:  {mean['precision@5']:.3f}   (ceiling {mean['ceiling_precision@5']:.3f}, "
              f"random {mean['random_precision']:.3f})")
        print(f"  recall@5:     {mean['recall@5']:.3f}")
        print(f"  recall@10:    {mean['recall@10']:.3f}")
        print(f"  MRR:          {mean['mrr']:.3f}")
        if mode == config["text"]:
            print("  precision@5 by series:")
            for s, v in mean["per_series_precision@5"].items():
                print(f"    {s:<24} {v:.2f}")
        print()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", default="cases.csv", help="dataset with planted series (default: cases.csv)")
    ap.add_argument("--sweep", action="store_true", help="also compare HDBSCAN settings on --csv")
    ap.add_argument("--seeds", type=int, default=0,
                    help="regenerate the dataset N times and average (with --compare: N per split)")
    ap.add_argument("--seed-offset", type=int, default=None,
                    help="first seed for --seeds (default 0) or --retrieval (default 1000, "
                         "the held-out datasets)")
    ap.add_argument("--retrieval", action="store_true",
                    help="score the similar-case search that feeds RAG")
    ap.add_argument("--compare", action="store_true",
                    help="choose the best pipeline settings and save cluster_config.json")
    ap.add_argument("--out", default="eval_results.json", help="where to write the JSON results")
    args = ap.parse_args()

    emb = Embeddings(load_embedder())
    config = load_config()
    output = {"embedding_model": EMBEDDING_MODEL, "active_config": config}

    if args.retrieval:
        offset = HELD_OUT_START if args.seed_offset is None else args.seed_offset
        output["retrieval"] = run_retrieval(args.seeds or 5, offset, emb, config)
    elif args.compare:
        output["compare"] = run_compare(args.seeds or 5, emb)
    elif args.seeds:
        output["multi_seed"] = run_seeds(args.seeds, args.seed_offset or 0, emb, config)
    else:
        output.update(run_single(args.csv, emb, config, args.sweep))

    with open(args.out, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nSaved results to {args.out}")


if __name__ == "__main__":
    main()
