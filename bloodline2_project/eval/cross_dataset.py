import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_profiles import LEAKY_FIELDS, PROFILE_NUMERIC, load_accounts, new_model, summary

CATEGORICAL = ["kyc_tier"]


def matrix(df, columns=None):
    x = df[PROFILE_NUMERIC].astype(float).copy()
    for c in CATEGORICAL:
        x = x.join(pd.get_dummies(df[c].astype(str), prefix=c, dtype=float))
    return x.reindex(columns=columns, fill_value=0.0) if columns is not None else x


def fit(frames):
    df = pd.concat(frames, ignore_index=True)
    x = matrix(df)
    return new_model().fit(x, df["label"].values), list(x.columns)


def score(model, columns, df):
    return model.predict_proba(matrix(df, columns))[:, 1]


def compact(res):
    return {"pr_auc": res["pr_auc"], "roc_auc": res["roc_auc"],
            **{f"{k}_{m}": v[m] for k, v in res["bands"].items() for m in ("accuracy", "precision", "recall", "false_positive_rate")}}


def main():
    ap = argparse.ArgumentParser(description="Leave-one-dataset-out evaluation of the profile model")
    ap.add_argument("datasets", nargs="+")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--save-model", default=str(Path(__file__).resolve().parent.parent / "data" / "models_profile" / "profile_model_all.joblib"))
    args = ap.parse_args()

    data = {Path(p).stem: load_accounts(p)[0] for p in args.datasets}
    names = list(data)
    folds, rows = [], []
    for test in names:
        train = [n for n in names if n != test]
        model, cols = fit([data[n] for n in train])
        y, p = data[test]["label"].values, score(model, cols, data[test])
        res = summary(y, p)
        res["train_datasets"], res["train_samples"] = train, int(sum(len(data[n]) for n in train))
        res["top_features"] = [{"feature": f, "importance": round(float(v), 4)}
                               for f, v in sorted(zip(cols, model.feature_importances_), key=lambda t: -t[1])[:6]]
        singles = {}
        for n in train:
            m1, c1 = fit([data[n]])
            singles[n] = compact(summary(y, score(m1, c1, data[test])))
        res["single_dataset_baselines"] = singles
        res["single_dataset_mean"] = {k: round(float(np.mean([s[k] for s in singles.values()])), 4) for k in next(iter(singles.values()))}
        folds.append({"test_dataset": test, **res})
        rows.append((test, compact(res), res["single_dataset_mean"]))
        print(f"test {test}.json  trained on {', '.join(t + '.json' for t in train)}")
        print(f"   multi-dataset : {compact(res)}")
        print(f"   single (mean) : {res['single_dataset_mean']}")

    keys = list(rows[0][1])
    overall = {"multi_dataset_mean": {k: round(float(np.mean([r[1][k] for r in rows])), 4) for k in keys},
               "multi_dataset_std": {k: round(float(np.std([r[1][k] for r in rows])), 4) for k in keys},
               "single_dataset_mean": {k: round(float(np.mean([r[2][k] for r in rows])), 4) for k in keys}}

    final, cols = fit(list(data.values()))
    Path(args.save_model).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final, "columns": cols, "trained_on": names}, args.save_model)

    report = {"generated": datetime.now().isoformat(timespec="seconds"), "method": "leave-one-dataset-out",
              "datasets": {n: {"samples": int(len(d)), "mules": int(d["label"].sum())} for n, d in data.items()},
              "features": PROFILE_NUMERIC + [f"{c} (one-hot)" for c in CATEGORICAL],
              "excluded_fields": LEAKY_FIELDS + ["bank", "city"], "folds": folds, "overall": overall,
              "final_model": {"path": args.save_model, "trained_on": names, "columns": cols}}
    out = Path(args.out)
    json.dump(report, open(out / "cross_dataset_report.json", "w", encoding="utf-8"), indent=2)

    pct = lambda v: f"{v * 100:.1f}%"
    md = f"# Cross-dataset evaluation (leave one dataset out)\n\nGenerated {report['generated']}. "
    md += f"Each dataset is tested by a model trained on the other {len(names) - 1}. Bank and city are excluded because their values differ between datasets.\n\n"
    md += "| Test set | PR-AUC | ROC-AUC | Accuracy @0.40 | Precision @0.40 | Recall @0.40 | FPR @0.40 | Accuracy @0.70 | Precision @0.70 | Recall @0.70 | FPR @0.70 |\n|" + "---|" * 11 + "\n"
    for t, m, _ in rows:
        md += f"| {t}.json | {m['pr_auc']} | {m['roc_auc']} | " + " | ".join(pct(m[f"{b}_{k}"]) for b in ("medium", "high")
                                                                       for k in ("accuracy", "precision", "recall", "false_positive_rate")) + " |\n"
    mm, sm = overall["multi_dataset_mean"], overall["single_dataset_mean"]
    md += f"| **Mean** | {mm['pr_auc']} | {mm['roc_auc']} | " + " | ".join(pct(mm[f"{b}_{k}"]) for b in ("medium", "high")
                                                                       for k in ("accuracy", "precision", "recall", "false_positive_rate")) + " |\n"
    md += f"| Single-dataset training (mean) | {sm['pr_auc']} | {sm['roc_auc']} | " + " | ".join(pct(sm[f"{b}_{k}"]) for b in ("medium", "high")
                                                                       for k in ("accuracy", "precision", "recall", "false_positive_rate")) + " |\n"
    md += f"\nFinal model trained on all {len(names)} datasets: `{args.save_model}`.\n"
    (out / "cross_dataset_report.md").write_text(md, encoding="utf-8")
    print(f"MEAN multi : {mm}\nMEAN single: {sm}\nReports: {out / 'cross_dataset_report.md'}")


if __name__ == "__main__":
    main()
