# Bloodline 2.0 — Bank-Grade Mule Defense & Fraud Interception Platform

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-blue.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38bdf8.svg)](https://tailwindcss.com/)
[![XGBoost](https://img.shields.io/badge/ML-XGBoost%20%2B%20SHAP-orange.svg)](https://xgboost.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Simulated Data & Statutory Safe Harbor**:
> All accounts, ledger entries, devices, invoices, and transaction topologies in this project are strictly **synthetic** (generated deterministically with fixed random seed 42).
> Bloodline 2.0 is an advisory decision-support system. It **never classifies anyone as a fraudster autonomously**, and **any action with legal effect mandates explicit human approval**.
> Regulatory values follow the Reserve Bank of India (RBI) Master Directions on Frauds (2016), Customer Liability Circular (2018), and Inter-Bank CFR Framework.
> Demonstration only, not legal advice.

---

## 🚀 Quickstart in 5 Steps or Fewer

Start the entire platform (backend, trained ML models, synthetic ledger, and production React UI) with one command:

```bash
# Step 1: Clone repository
git clone https://github.com/your-org/Bloodline2.0.git && cd Bloodline2.0

# Step 2: Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Run the one-command start script (or make dev)
./start.sh
# (Automatically seeds data/bloodline.db, trains ML models, compiles React frontend, and launches the server)

# Step 5: Open your browser
# Web Platform:     http://127.0.0.1:8000
# OpenAPI Docs:     http://127.0.0.1:8000/docs
```

To run the complete automated test suite (30 unit and end-to-end acceptance tests):
```bash
make test
# or: pytest tests/ -v
```

---

## 🏛️ System Architecture

Bloodline 2.0 embeds directly into core banking switches and payment rails to stop money-mule syndicates before funds exit to unrecoverable rails.

```
                    ┌──────────────────────────────────────────────┐
                    │       Payment Initiation / Switch Rail       │
                    └──────────────────────┬───────────────────────┘
                                           │ POST /scan (<20ms)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI DECISION ENGINE                                  │
│                                                                                        │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌──────────────────────────┐  │
│  │ Point-in-Time Feature │   │   Real Trained ML     │   │   TreeSHAP Explainer &   │  │
│  │ Store (18 behavioral  ├──►│  XGBoost Mule Model   ├──►│   Perturbation Search    │  │
│  │ & graph features)     │   │  (PR-AUC = 0.7441)    │   │     (Counterfactual)     │  │
│  └───────────────────────┘   └───────────────────────┘   └─────────────┬────────────┘  │
│                                                                        │               │
│  ┌───────────────────────┐   ┌───────────────────────┐                 ▼               │
│  │  Money DNA Lineage    │   │ Next-Hop Destination  │       ┌──────────────────────┐  │
│  │  Proportional Haircut │   │  Predictor (Top-3)    │       │ Verdict & Reason     │  │
│  │  DAG Flow Tracer      │   │ (Edge Classification) │       │ Codes (Allow/Delay/  │  │
│  └───────────────────────┘   └───────────────────────┘       │ Hold / Lien Request) │  │
│                                                              └──────────────────────┘  │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        REACT + TYPESCRIPT ANALYST CONSOLE                              │
│                                                                                        │
│  • Pre-Payment Scan & 60s Scam Cooldown Warning Modal (Trapped Focus & Cooldown)       │
│  • Analyst Console: D3-Sankey Money DNA Replay & Interactive "Request Hold"            │
│  • Business Shield: Invoice BEC Bank-Detail-Change Protection                          │
│  • Case Clock: 21-Day Show-Cause Statutory Countdown & Simulation (+N Days)           │
│  • Impact Dashboard: Live ₹ Prevented, RBI Compensation Avoided, & Real ML vs Baseline │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎬 5-Minute Deterministic Demo Walkthrough

The platform includes seeded anchors for an end-to-end audit demonstration:

### 1. Pre-Payment Scan & Customer 60s Warning Modal
- **Anchor**: Account `ACC-MULE-C1-L1-1`, Amount `₹95,000`.
- Navigate to **Pre-Payment Scan** or click **"Launch 5-Minute Demo Story"** from the Overview page.
- Click **"Run Real-Time Scan"**.
- The backend evaluates 18 point-in-time features, calculates calibrated mule probability **0.99**, and returns verdict **HOLD**.
- **Warning Modal Opens**: Displays a 60-second countdown cooldown, plain-language reasons (*"Hardware fingerprint linked across multiple accounts"*, *"Account opened recently with limited history"*), and the automated counterfactual (*"Transfer would not trigger Hold if payee account were older than 180 days and pass-through velocity below 30%"*).
- Clicking **"Cancel Payment"** logs the outcome to the audit ledger and immediately animates the **₹ Prevented** counter in the sticky top bar.

### 2. Money DNA Lineage & Interactive Lien Hold
- Navigate to **Analyst Console & Money DNA**.
- Observe the multi-layer Sankey DAG (`Victim` &rarr; `Layer 1 Mules` &rarr; `Layer 2 Dispersal` &rarr; `Cash-Out Exits`).
- Use the **Time Scrubber** with Play/Pause to replay how the transaction chain unfolded across minutes.
- Observe predicted downstream destination hops highlighted as dashed amber vectors.
- Click **"Request Lien Hold"** on `ACC-MULE-C1-L1-1`: the dashed arrow locks into a solid green hold border, records the administrative hold, and freezes secondary dispersion.

### 3. Business Shield (Invoice & BEC Tampering Defense)
- Navigate to **Business Shield (Invoices)**.
- Select invoice `INV-003-003` (Vendor `VEND-003` - Apex Steel Infrastructure, Amount `₹28,50,000`).
- The system flags an unauthorized bank detail divergence modified 3 hours ago into mule account `ACC-MULE-C1-L1-1`.
- Click **"Place Admin Hold & Verify"** to place a lien hold and prevent corporate fund diversion.

### 4. Case Clock State Machine & "+N Days" Simulation
- Navigate to **Case Queue (RBI Clock)**.
- Inspect `CASE-2026-001` subject to Section 35A of the Banking Regulation Act and RBI Master Directions.
- Click **"+5 Days"** or **"+10 Days"** to simulate the statutory 21-day show-cause countdown dynamically.
- Click **"Review Statutory Show-Cause Draft"** to inspect the LLM-generated dossier with specific transaction evidence.
- Click **"Approve & Issue Statutory Notice"** to satisfy the mandatory human approval gate.

### 5. Adaptive Feedback Loop & Threshold Tuning
- In the Case Queue or Analyst Console, mark a transaction as a **False Positive**.
- The backend feedback loop adjusts the operating threshold in observable steps (e.g. `0.70` &rarr; `0.72`) while enforcing a strict recall floor (`0.90`).
- The updated threshold is reflected immediately in the sticky top bar.

### 6. Impact Dashboard & Honest ML Evaluation
- Navigate to **Impact & ML Evaluation**.
- Real evaluation metrics loaded directly from `eval/metrics.json` are benchmarked honestly against the rule-only baseline:
  - **Machine Learning Model (XGBoost)**: PR-AUC **0.7441**, Precision **82.1%**, Recall **100%**, False Positive Rate **1.86%**.
  - **Rule-Only Baseline**: PR-AUC **0.4103**, Precision **41.0%**, Recall **100%**, False Positive Rate **12.23%**.
  - **Chain 8 Robustness Holdout**: 16/18 slower-velocity mules successfully detected.
  - **RBI Circular 2018 Exposure Avoidance**: Live calculation of avoided bank liability (`min(85% net loss, ₹25,000)`).

---

## 🛡️ Honesty & Safety Guardrails Enforced

1. **Simulated Data Badge**: Visible badge on every screen; explicit prototype boundary notices.
2. **Zero Hardcoded Predictions**: All scores, probabilities, and SHAP reason codes are generated dynamically by the backend ML models.
3. **No "99% Accurate" Claims**: Honest evaluation metrics read from disk with rule-only baseline comparison.
4. **Strict Banking Terminology**: Uses *"administrative hold"* and *"lien request"* instead of *"freeze"*.
5. **Human Approval Gates**: The system never classifies anyone as a fraudster autonomously; legal notices require human officer authorization.
6. **Statutory Reference Links**: Live links in footer to RBI Master Directions (2016), Customer Liability Circular (2018), and Indian Cyber Crime Coordination Centre (I4C).

---

## 📥 Providing Your Own Custom Dataset

You can easily import your own real or synthetic dataset (CSV or JSON) into Bloodline 2.0:

### 1. Ingestion CLI Tool
Use the built-in ingestion utility [`data/ingest_custom.py`](file:///Users/divyamagrawal/Documents/Bloodline2.0/data/ingest_custom.py):

```bash
# Ingest CSVs from a directory and retrain ML models on your data:
python data/ingest_custom.py --dir ./my_data_folder/ --retrain

# Or specify individual CSV files:
python data/ingest_custom.py --accounts accounts.csv --transactions txns.csv --retrain
```

Starter CSV templates and schemas are available in [`data/custom_template/`](file:///Users/divyamagrawal/Documents/Bloodline2.0/data/custom_template/):
- `accounts.csv`: `id, bank_id, open_date, kyc_tier, is_mule, role, initial_balance`
- `transactions.csv`: `id, ts, sender, receiver, amount, channel, ref`
- `devices.csv`: `account_id, device_id, ip, phone` (optional, auto-generated if omitted)

### 2. Direct SQLite Replacement
You can also overwrite [`data/bloodline.db`](file:///Users/divyamagrawal/Documents/Bloodline2.0/data/bloodline.db) directly with your own SQLite database matching the schema in `data/simulator.py`.

---

## 🧪 Verification & Acceptance Results

Run tests anytime with `pytest`:
```bash
$ pytest tests/ -v
============================== test session starts ==============================
tests/test_bloodline2_core.py::test_database_generation_and_seeding PASSED
tests/test_bloodline2_core.py::test_point_in_time_feature_extraction PASSED
tests/test_bloodline2_core.py::test_model_inference_engine PASSED
tests/test_bloodline2_core.py::test_counterfactual_explanation PASSED
tests/test_bloodline2_core.py::test_money_dna_lineage_builder PASSED
tests/test_bloodline2_core.py::test_next_hop_predictor PASSED
tests/test_bloodline2_core.py::test_cross_bank_trace_handoff PASSED
tests/test_bloodline2_core.py::test_case_clock_state_machine PASSED
tests/test_cases_and_policy.py::test_case_clock_lifecycle PASSED
tests/test_cases_and_policy.py::test_policy_manager_defaults PASSED
tests/test_cases_and_policy.py::test_audit_trail_immutability PASSED
tests/test_e2e_acceptance.py::test_frontend_spa_and_health PASSED
tests/test_e2e_acceptance.py::test_mule_scan_with_shap_and_counterfactual PASSED
tests/test_e2e_acceptance.py::test_legitimate_merchant_scan PASSED
tests/test_e2e_acceptance.py::test_money_dna_lineage_and_hold PASSED
tests/test_e2e_acceptance.py::test_case_clock_state_machine_and_simulation PASSED
tests/test_e2e_acceptance.py::test_adaptive_feedback_loop PASSED
tests/test_e2e_acceptance.py::test_real_metrics_and_rule_baseline PASSED
tests/test_e2e_acceptance.py::test_business_shield_invoice_attack_detection PASSED
tests/test_e2e_acceptance.py::test_cross_bank_trace_handoff PASSED
tests/test_graph_and_lineage.py::test_ego_network_extraction PASSED
tests/test_graph_and_lineage.py::test_money_dna_proportional_decay PASSED
tests/test_graph_and_lineage.py::test_shared_infrastructure_clustering PASSED
tests/test_prediction_and_vendor.py::test_next_hop_prediction_ranking PASSED
tests/test_prediction_and_vendor.py::test_vendor_bank_detail_change_alert PASSED
tests/test_prediction_and_vendor.py::test_vendor_legitimate_payout PASSED
tests/test_scoring.py::test_score_legitimate_account PASSED
tests/test_scoring.py::test_score_mule_aggregator PASSED
tests/test_scoring.py::test_scoring_latency_budget PASSED
tests/test_scoring.py::test_structured_reason_codes PASSED

============================== 30 passed in 1.54s ==============================
```

---

## 📂 Project Structure

```
Bloodline2.0/
├── app/
│   ├── api/routes.py              # Dual-mounted REST endpoints (/scan, /lineage, etc.)
│   ├── ml/
│   │   ├── features.py            # 18 point-in-time behavioral & graph features
│   │   ├── train.py               # Cost-sensitive XGBoost & IsolationForest training
│   │   └── engine.py              # Real-time inference, SHAP, counterfactual search
│   ├── services/
│   │   ├── core_engine.py         # Unified Money DNA, next-hop, case clock engine
│   │   └── llm_service.py         # Anthropic API & offline statutory notice generator
│   └── main.py                    # FastAPI application & SPA static server
├── config/
│   └── rules.yaml                 # Regulatory rules, Case Clock windows, exposure formulas
├── data/
│   ├── simulator.py               # 3-bank synthetic ledger generator (seed 42)
│   ├── bloodline.db               # SQLite database (5,000 accounts, 149,979 txns)
│   └── models/                    # Saved joblib model artifacts
├── eval/
│   └── metrics.json               # Genuine evaluation metrics (ML vs Rule baseline)
├── frontend/
│   ├── src/
│   │   ├── components/            # TopBar, RiskGauge, WarningModal, MoneyDNASankey, Footer
│   │   ├── pages/                 # Landing, Scan, AnalystConsole, CaseQueue, BusinessShield, Impact
│   │   ├── types.ts               # Shared TypeScript schemas
│   │   └── api.ts                 # Type-safe API client
│   └── dist/                      # Pre-compiled production bundle
├── tests/                         # Pytest test suite (30 tests)
├── Makefile                       # Convenient developer shortcuts
├── start.sh                       # One-command startup script
└── README.md                      # Documentation
```
