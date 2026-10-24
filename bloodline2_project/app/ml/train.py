import argparse
import itertools
import json
import random
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.ensemble import IsolationForest
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, confusion_matrix, precision_score, recall_score
from sklearn.model_selection import StratifiedGroupKFold

from app.ml.features import FeatureStore, FEATURE_COLUMNS

SAMPLES_PER_ACCOUNT = 3
FOLDS = 5
ISO_COLUMNS = ["pass_through_ratio", "median_dwell_time_mins", "structuring_signal", "shared_device_count"]
PARAM_GRID = {
    "max_depth": [2, 3, 4],
    "learning_rate": [0.05, 0.1],
    "n_estimators": [150, 300],
    "min_child_weight": [1, 5],
}


def extract_training_dataset(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    fs = FeatureStore(db_path)
    latest = cur.execute("SELECT MAX(epoch_seconds) FROM transactions").fetchone()[0] or 0
    accounts = cur.execute("SELECT id, is_mule, role, chain_id FROM accounts WHERE role != 'HONEYPOT'").fetchall()
    rng = random.Random(42)
    records = []
    print(f"Extracting point-in-time features for {len(accounts)} accounts...")
    for acc in accounts:
        rows = cur.execute("""SELECT epoch_seconds, amount FROM transactions WHERE receiver = ? OR sender = ?
                              ORDER BY epoch_seconds""", (acc["id"], acc["id"])).fetchall()
        points = rng.sample(rows, min(SAMPLES_PER_ACCOUNT, len(rows))) if rows else [None]
        for t in points:
            epoch, amt = (t["epoch_seconds"] + 30, t["amount"]) if t else (latest + 60, 5000.0)
            feats = fs.extract_point_in_time_features(acc["id"], epoch, amt, conn=conn)
            feats.update(account_id=acc["id"], is_mule=int(acc["is_mule"]),
                         chain_id=acc["chain_id"] if acc["is_mule"] and acc["chain_id"] else "LEGIT")
            records.append(feats)
    conn.close()
    df = pd.DataFrame(records)
    df["group"] = np.where(df["chain_id"] == "LEGIT", df["account_id"], df["chain_id"])
    print(f"Dataset: {len(df)} samples from {df['account_id'].nunique()} accounts, "
          f"{df.loc[df.is_mule == 1, 'account_id'].nunique()} mule accounts in {df.loc[df.is_mule == 1, 'chain_id'].nunique()} rings")
    return df, latest


def rule_only_predict(df):
    cond1 = (df["account_age_days"] < 45) & (df["pass_through_ratio"] > 0.80) & (df["median_dwell_time_mins"] < 30)
    cond2 = df["structuring_signal"] >= 2
    cond3 = df["shared_device_count"] >= 1
    return (cond1 | cond2 | cond3).astype(int).values


def make_model(params, y):
    weight = float((y == 0).sum() / max(1, (y == 1).sum()))
    return xgb.XGBClassifier(subsample=0.8, colsample_bytree=0.8, scale_pos_weight=weight,
                             eval_metric="aucpr", random_state=42, **params)


def out_of_fold(df, params, folds):
    x, y = df[FEATURE_COLUMNS], df["is_mule"].values
    oof = np.zeros(len(df))
    for tr, te in folds:
        oof[te] = make_model(params, y[tr]).fit(x.iloc[tr], y[tr]).predict_proba(x.iloc[te])[:, 1]
    return oof


def confusion(y, pred):
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"precision": round(float(precision_score(y, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
            "false_positive_rate": round(float(fp / max(1, fp + tn)), 4),
            "true_positives": int(tp), "false_positives": int(fp), "true_negatives": int(tn), "false_negatives": int(fn)}


def pick_thresholds(y, p):
    sweep = []
    for t in np.round(np.arange(0.05, 1.0, 0.05), 2):
        m = confusion(y, (p >= t).astype(int))
        sweep.append({"threshold": float(t), **{k: m[k] for k in ("precision", "recall", "false_positive_rate")}})
    high = next((s["threshold"] for s in sweep if s["precision"] >= 0.97 and s["recall"] >= 0.80), 0.70)
    medium = max((s["threshold"] for s in sweep if s["recall"] >= 0.95 and s["threshold"] < high), default=min(0.40, high))
    return {"medium": medium, "high": high}, sweep


def train_and_evaluate(db_path="data/bloodline.db", model_dir="data/models", eval_dir="eval"):
    model_dir, eval_dir = Path(model_dir), Path(eval_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    df, latest = extract_training_dataset(db_path)
    x, y = df[FEATURE_COLUMNS], df["is_mule"].values
    folds = list(StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=42).split(x, y, df["group"]))

    results = []
    for values in itertools.product(*PARAM_GRID.values()):
        params = dict(zip(PARAM_GRID.keys(), values))
        score = average_precision_score(y, out_of_fold(df, params, folds))
        results.append((score, params))
        print(f"  {params} -> out-of-fold PR-AUC {score:.4f}")
    best_score, best_params = max(results, key=lambda r: r[0])
    print(f"Best settings: {best_params} (PR-AUC {best_score:.4f})")

    oof_raw = out_of_fold(df, best_params, folds)
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99).fit(oof_raw, y)
    oof_cal = np.zeros(len(df))
    for tr, te in folds:
        fold_cal = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99).fit(oof_raw[tr], y[tr])
        oof_cal[te] = fold_cal.predict(oof_raw[te])

    thresholds, sweep = pick_thresholds(y, oof_cal)
    ml = {"name": "XGBoost Mule Classifier (ring-held-out CV, isotonic calibration)",
          "pr_auc": round(float(average_precision_score(y, oof_cal)), 4),
          "operating_threshold": thresholds["high"], **confusion(y, (oof_cal >= thresholds["high"]).astype(int))}
    rule_pred = rule_only_predict(df)
    rule = {"name": "Standard Rule-Only Banking Policy",
            "pr_auc": round(float(average_precision_score(y, rule_pred)), 4), **confusion(y, rule_pred)}

    per_ring = {}
    for chain in sorted(df.loc[df.is_mule == 1, "chain_id"].unique()):
        mask = (df["chain_id"] == chain).values
        per_ring[chain] = round(float((oof_cal[mask] >= thresholds["medium"]).mean()), 3)
    c8 = df["chain_id"].astype(str).str.contains("08").values
    c8_detected, c8_total = int((oof_cal[c8] >= thresholds["medium"]).sum()), int(c8.sum())

    final = make_model(best_params, y).fit(x, y)
    iso = IsolationForest(n_estimators=100, contamination=0.015, random_state=42).fit(x[ISO_COLUMNS])
    joblib.dump(iso, model_dir / "isolation_forest.joblib")
    joblib.dump(shap.TreeExplainer(final), model_dir / "shap_explainer.joblib")
    joblib.dump({"model": final, "thresh_base": 0.0035, "calibrator": calibrator, "as_of_epoch": int(latest) + 60,
                 "recommended_thresholds": thresholds, "params": best_params},
                model_dir / "xgboost_mule_bundle.joblib")

    mule_samples = int(y.sum())
    metrics = {
        "evaluation_timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "method": f"{FOLDS}-fold cross-validation with whole mule rings held out; every score is out-of-fold",
        "dataset_summary": {"total_samples": int(len(df)), "train_samples": int(len(df) * (FOLDS - 1) / FOLDS),
                            "test_samples": int(len(df)), "test_mules": mule_samples,
                            "accounts": int(df["account_id"].nunique()),
                            "mule_accounts": int(df.loc[df.is_mule == 1, "account_id"].nunique())},
        "ml_model": ml,
        "rule_baseline": rule,
        "recommended_thresholds": thresholds,
        "threshold_sweep": sweep,
        "per_ring_recall_at_medium": per_ring,
        "cross_validation": {"best_params": best_params, "best_pr_auc_raw": round(float(best_score), 4),
                             "grid": [{"pr_auc": round(float(s), 4), **p} for s, p in sorted(results, key=lambda r: -r[0])]},
        "robustness_holdout_test": {"chain_id": "CH08 (Slow Hops Mule Style)", "detected_mules": c8_detected,
                                    "total_mules": c8_total,
                                    "robustness_score": round(c8_detected / max(1, c8_total), 3),
                                    "status": "PASSED" if c8_detected / max(1, c8_total) >= 0.70 else "FAILED"},
        "feature_importances": {c: round(float(v), 4) for c, v in zip(FEATURE_COLUMNS, final.feature_importances_)},
    }
    json.dump(metrics, open(eval_dir / "metrics.json", "w"), indent=2)

    print("=" * 60)
    print(f"ML model (out-of-fold): PR-AUC={ml['pr_auc']}, precision={ml['precision']}, recall={ml['recall']}, "
          f"FPR={ml['false_positive_rate']} at threshold {thresholds['high']}")
    print(f"Rule baseline:          PR-AUC={rule['pr_auc']}, precision={rule['precision']}, recall={rule['recall']}, "
          f"FPR={rule['false_positive_rate']}")
    print(f"Recommended thresholds: {thresholds}")
    print(f"Chain 8 robustness: {c8_detected}/{c8_total} ({metrics['robustness_holdout_test']['status']})")
    print("=" * 60)
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Train and evaluate the Bloodline mule model")
    ap.add_argument("--db", default="data/bloodline.db")
    ap.add_argument("--models", default="data/models")
    ap.add_argument("--eval", default="eval")
    a = ap.parse_args()
    train_and_evaluate(a.db, a.models, a.eval)
