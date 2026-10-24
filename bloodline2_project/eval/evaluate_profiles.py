import argparse
import json
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (average_precision_score, confusion_matrix, precision_score, recall_score,
                             roc_auc_score)
from sklearn.model_selection import StratifiedKFold, train_test_split
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from app.ml.features import FEATURE_COLUMNS, FeatureStore

LEAKY_FIELDS = ["account_type", "mule_type", "fraud_network_id", "risk_score", "risk_flags", "is_mule",
                "account_id", "holder_name", "device_id", "ip_address", "phone", "data_origin"]
PROFILE_NUMERIC = ["account_age_days", "avg_monthly_balance_inr", "device_account_count", "ip_account_count",
                   "phone_account_count"]
PROFILE_CATEGORICAL = ["kyc_tier", "bank", "city"]
BANDS = {"medium": 0.40, "high": 0.70}


def load_accounts(path):
    raw = json.load(open(path, encoding="utf-8"))
    rows = raw["accounts"] if isinstance(raw, dict) else raw
    df = pd.DataFrame(rows)
    df["label"] = df["is_mule"].astype(bool).astype(int)
    as_of = raw.get("as_of_date") if isinstance(raw, dict) else None
    return df, as_of


def metrics_at(y, p, threshold):
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    n = len(y)
    return {"threshold": float(threshold), "accuracy": round(float((tp + tn) / n), 4),
            "precision": round(float(precision_score(y, pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y, pred, zero_division=0)), 4),
            "false_positive_rate": round(float(fp / max(1, fp + tn)), 4),
            "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}


def summary(y, p):
    out = {"samples": int(len(y)), "mules": int(y.sum()),
           "pr_auc": round(float(average_precision_score(y, p)), 4),
           "roc_auc": round(float(roc_auc_score(y, p)), 4) if len(set(y)) > 1 else None,
           "bands": {name: metrics_at(y, p, t) for name, t in BANDS.items()},
           "sweep": [metrics_at(y, p, t) for t in np.round(np.arange(0.1, 1.0, 0.1), 2)]}
    best = max(out["sweep"], key=lambda m: (2 * m["precision"] * m["recall"] / (m["precision"] + m["recall"]))
               if m["precision"] + m["recall"] else 0)
    out["best_f1_threshold"] = best["threshold"]
    return out


def build_profile_db(df, db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE accounts (id TEXT PRIMARY KEY, bank_id TEXT, open_date TEXT, kyc_tier TEXT, is_mule INTEGER,
            role TEXT, pseudonymous_label TEXT, initial_balance REAL, current_balance REAL,
            is_honeypot INTEGER DEFAULT 0, chain_id TEXT, layer INTEGER DEFAULT 0);
        CREATE TABLE devices (account_id TEXT, device_id TEXT, ip TEXT, phone TEXT);
        CREATE TABLE transactions (id TEXT PRIMARY KEY, ts TEXT, epoch_seconds INTEGER, sender TEXT, receiver TEXT,
            amount REAL, channel TEXT, ref TEXT, origin_txn_id TEXT, sender_bank TEXT, receiver_bank TEXT,
            is_mule_flow INTEGER DEFAULT 0, chain_id TEXT);
    """)
    for r in df.itertuples():
        conn.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, 0, 'UNKNOWN', ?, ?, ?, 0, NULL, 0)",
                     (r.account_id, r.bank, r.opened_date, r.kyc_tier, r.account_id,
                      r.avg_monthly_balance_inr, r.avg_monthly_balance_inr))
        conn.execute("INSERT INTO devices VALUES (?, ?, ?, ?)", (r.account_id, r.device_id, r.ip_address, r.phone))
    conn.commit()
    conn.close()


def test_current_model(df, as_of, models_dir):
    bundle = joblib.load(Path(models_dir) / "xgboost_mule_bundle.joblib")
    model, base = bundle["model"], bundle.get("thresh_base", 0.0035)
    epoch = int(datetime.fromisoformat(as_of).replace(tzinfo=timezone.utc).timestamp()) if as_of else 1792778400
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "profiles.db")
        build_profile_db(df, db)
        fs = FeatureStore(db)
        conn = fs._get_connection()
        feats = pd.DataFrame([fs.extract_point_in_time_features(a, epoch, None, conn=conn) for a in df["account_id"]])
        conn.close()
    raw = model.predict_proba(feats[FEATURE_COLUMNS])[:, 1]
    ratio = raw / (base + 1e-12)
    p = np.clip(1.0 / (1.0 + np.exp(-2.0 * np.log(ratio + 1e-12))), 0.01, 0.99)
    used = [c for c in FEATURE_COLUMNS if feats[c].nunique() > 1]
    res = summary(df["label"].values, p)
    res["signals_with_data"] = used
    res["score_spread"] = {"min": round(float(p.min()), 4), "median": round(float(np.median(p)), 4),
                           "max": round(float(p.max()), 4), "distinct": int(len(np.unique(np.round(p, 4))))}
    return res, p


def profile_matrix(df, columns=None):
    x = df[PROFILE_NUMERIC].astype(float).copy()
    for c in PROFILE_CATEGORICAL:
        x = x.join(pd.get_dummies(df[c].astype(str), prefix=c, dtype=float))
    return x.reindex(columns=columns, fill_value=0.0) if columns is not None else x


def new_model():
    return XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.08, subsample=0.9,
                         colsample_bytree=0.9, eval_metric="logloss", random_state=42)


def test_profile_model(df, test_size, out_model):
    x, y = profile_matrix(df), df["label"].values
    x_tr, x_te, y_tr, y_te, idx_tr, idx_te = train_test_split(x, y, df.index, test_size=test_size,
                                                              stratify=y, random_state=42)
    model = new_model().fit(x_tr, y_tr)
    p = model.predict_proba(x_te)[:, 1]
    res = summary(y_te, p)
    res["train_samples"] = int(len(y_tr))
    cv = []
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=42).split(x, y):
        m = new_model().fit(x.iloc[tr], y[tr])
        cv.append(average_precision_score(y[te], m.predict_proba(x.iloc[te])[:, 1]))
    res["cv_pr_auc_mean"], res["cv_pr_auc_std"] = round(float(np.mean(cv)), 4), round(float(np.std(cv)), 4)
    imp = sorted(zip(x.columns, model.feature_importances_), key=lambda t: -t[1])[:8]
    res["top_features"] = [{"feature": f, "importance": round(float(v), 4)} for f, v in imp]
    res["single_feature_roc_auc"] = {c: round(float(max(roc_auc_score(y, df[c]), 1 - roc_auc_score(y, df[c]))), 4)
                                     for c in PROFILE_NUMERIC}
    if out_model:
        Path(out_model).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": model, "columns": list(x.columns)}, out_model)
    errors = df.loc[idx_te].assign(score=p, pred=(p >= 0.5).astype(int))
    errors = errors[errors["pred"] != errors["label"]]
    return res, errors


def table(rows, cols):
    head = "| " + " | ".join(c for c, _ in cols) + " |\n|" + "---|" * len(cols) + "\n"
    return head + "".join("| " + " | ".join(f(r) for _, f in cols) + " |\n" for r in rows)


def report_md(name, a, b, errors):
    pct = lambda v: f"{v * 100:.1f}%"
    band_cols = [("Band", lambda r: r[0]), ("Threshold", lambda r: f"{r[1]['threshold']:.2f}"),
                 ("Accuracy", lambda r: pct(r[1]["accuracy"])), ("Precision", lambda r: pct(r[1]["precision"])),
                 ("Recall", lambda r: pct(r[1]["recall"])), ("False-positive rate", lambda r: pct(r[1]["false_positive_rate"])),
                 ("TP / FP / TN / FN", lambda r: f"{r[1]['tp']} / {r[1]['fp']} / {r[1]['tn']} / {r[1]['fn']}")]
    sweep_cols = [("Threshold", lambda m: f"{m['threshold']:.1f}"), ("Precision", lambda m: pct(m["precision"])),
                  ("Recall", lambda m: pct(m["recall"])), ("False-positive rate", lambda m: pct(m["false_positive_rate"]))]
    s = f"# Profile dataset evaluation: {name}\n\nGenerated {datetime.now().strftime('%Y-%m-%d %H:%M')}.\n\n"
    s += f"## A. Current Bloodline model, profile signals only\n\n{a['samples']} accounts, {a['mules']} mules. "
    s += f"PR-AUC **{a['pr_auc']}**, ROC-AUC **{a['roc_auc']}**.\n\n"
    s += f"Signals that had any data: {', '.join(a['signals_with_data']) or 'none'}. "
    s += f"Scores ranged {a['score_spread']['min']}–{a['score_spread']['max']} ({a['score_spread']['distinct']} distinct values).\n\n"
    s += table(list(a["bands"].items()), band_cols) + "\n" + table(a["sweep"], sweep_cols)
    s += f"\n## B. New profile-only model (trained on {b['train_samples']}, tested on {b['samples']})\n\n"
    s += f"PR-AUC **{b['pr_auc']}**, ROC-AUC **{b['roc_auc']}**. 5-fold cross-validated PR-AUC {b['cv_pr_auc_mean']} ± {b['cv_pr_auc_std']}.\n\n"
    s += table(list(b["bands"].items()), band_cols) + "\n" + table(b["sweep"], sweep_cols)
    s += "\nTop features: " + ", ".join(f"{f['feature']} ({f['importance']})" for f in b["top_features"]) + "\n\n"
    s += "Single-feature ROC-AUC (1.0 = that field alone separates mules perfectly): " + \
         ", ".join(f"{k} {v}" for k, v in b["single_feature_roc_auc"].items()) + "\n\n"
    s += f"## Misclassified test accounts (model B, threshold 0.5): {len(errors)}\n\n"
    if len(errors):
        s += table(errors.head(25).to_dict("records"), [("Account", lambda r: r["account_id"]),
                   ("Truth", lambda r: "mule" if r["label"] else "genuine"), ("Score", lambda r: f"{r['score']:.2f}"),
                   ("Age (days)", lambda r: str(r["account_age_days"])), ("KYC", lambda r: str(r["kyc_tier"])),
                   ("Device / IP / phone sharing", lambda r: f"{r['device_account_count']} / {r['ip_account_count']} / {r['phone_account_count']}")])
    return s


def main():
    ap = argparse.ArgumentParser(description="Evaluate Bloodline on an account-profile JSON dataset")
    ap.add_argument("dataset")
    ap.add_argument("--models", default=str(ROOT / "data" / "models"))
    ap.add_argument("--out", default=str(ROOT / "eval"))
    ap.add_argument("--test-size", type=float, default=0.3)
    ap.add_argument("--save-model", default=str(ROOT / "data" / "models_profile" / "profile_model.joblib"))
    args = ap.parse_args()

    df, as_of = load_accounts(args.dataset)
    a, _ = test_current_model(df, as_of, args.models)
    b, errors = test_profile_model(df, args.test_size, args.save_model)
    name = Path(args.dataset).name
    out = Path(args.out)
    json.dump({"dataset": name, "as_of": as_of, "excluded_fields": LEAKY_FIELDS, "current_model_profile_only": a,
               "profile_model": b}, open(out / "profile_report.json", "w", encoding="utf-8"), indent=2)
    (out / "profile_report.md").write_text(report_md(name, a, b, errors), encoding="utf-8")
    print(f"A current model:  PR-AUC {a['pr_auc']}  ROC-AUC {a['roc_auc']}  @0.40 {a['bands']['medium']}  @0.70 {a['bands']['high']}")
    print(f"   signals with data: {a['signals_with_data']}  score spread: {a['score_spread']}")
    print(f"B profile model:  PR-AUC {b['pr_auc']}  ROC-AUC {b['roc_auc']}  CV {b['cv_pr_auc_mean']}±{b['cv_pr_auc_std']}")
    print(f"   @0.40 {b['bands']['medium']}\n   @0.70 {b['bands']['high']}")
    print(f"   top features: {b['top_features'][:5]}")
    print(f"   single-feature ROC-AUC: {b['single_feature_roc_auc']}")
    print(f"Reports: {out / 'profile_report.md'}, {out / 'profile_report.json'}")


if __name__ == "__main__":
    main()
