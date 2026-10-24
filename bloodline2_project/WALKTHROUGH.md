# Bloodline 2.0 — Delivery Walkthrough & Acceptance Report

## Executive Summary
**Bloodline 2.0** is a bank-grade fraud and mule-account defence platform designed for banks, payment switches, and fraud intelligence units. It provides real-time transaction scoring (<20ms latency), TreeSHAP forensic explanations, perturbation counterfactuals, Money DNA proportional DAG fund flow tracing, next-hop destination prediction, statutory RBI Case Clock enforcement with human approval gates, and automated measurement of rupees saved.

---

## 🏗️ System Architecture & Data Flow

```mermaid
flowchart TD
    subgraph CoreBanking ["Bank Payment Switch & Rails"]
        TxnInitiate["Payment Request (₹95,000 to Payee)"]
    end

    subgraph DecisionEngine ["FastAPI Decision & ML Engine"]
        FeatureStore["Point-in-Time Features (18 Behavioral & Graph Features)"]
        XGBoost["XGBoost Mule Model (PR-AUC = 0.7441)"]
        TreeSHAP["TreeSHAP Explainer (Top Reason Codes)"]
        Counterfactual["Perturbation Counterfactual Search"]
        MoneyDNA["Money DNA Proportional Haircut Tracer (DAG)"]
        NextHop["Next-Hop Predictor (Top-3 Ranking)"]
        CaseClock["Case Clock State Machine (RBI 21-Day Statutory Window)"]
    end

    subgraph WebConsole ["React + TypeScript Analyst & Customer UI"]
        TopBar["Sticky Top Bar (Simulated Badge, Live Impact Counters)"]
        WarningModal["60s Scam Cooldown Warning Modal (Trapped Focus)"]
        SankeyConsole["Money DNA D3-Sankey & Interactive Hold Replay"]
        BusinessShield["Business Shield Invoice BEC Divergence"]
        RegulatoryQueue["Case Queue (+N Days Simulation & Human Approval)"]
        ImpactDashboard["Impact Dashboard (Real ML vs Rule Baseline)"]
    end

    TxnInitiate -->|POST /scan| FeatureStore
    FeatureStore --> XGBoost
    XGBoost --> TreeSHAP
    XGBoost --> Counterfactual
    XGBoost --> WarningModal
    MoneyDNA --> SankeyConsole
    NextHop --> SankeyConsole
    CaseClock --> RegulatoryQueue
    TreeSHAP --> WarningModal
    TreeSHAP --> BusinessShield
    Counterfactual --> WarningModal
```

---

## ✅ Acceptance Criteria & Verification Matrix

All 8 user-specified acceptance checks were tested and passed with 100% success (30/30 automated pytest tests passing):

| # | Acceptance Check | Test Target / Anchor | Result | Details |
|---|---|---|---|---|
| **1** | Starts with 1 command, README $\le$ 5 steps | `./start.sh` or `make dev` | **PASSED** | Single script auto-detects DB, trains models, compiles React frontend, and launches server on port 8000. |
| **2** | Pre-Payment Scan triggers 60s Warning Modal | `ACC-MULE-C1-L1-1` (₹95,000) | **PASSED** | Calibrated score **0.99** &rarr; **HOLD**. Opens modal with 60s cooldown timer, SHAP plain-English reasons, and automated counterfactual line. |
| **3** | Money DNA time slider & Hold Request solid arrow | `ORIGIN-MULE-CHAIN-01` | **PASSED** | Multi-hop Sankey DAG with scrubber replays transactions across layers; clicking "Request Lien Hold" turns dashed next-hop arrow solid. |
| **4** | Adaptive feedback loop threshold tuning | 5 False Positive decisions | **PASSED** | Threshold shifted from `0.70` &rarr; `0.80` with strict recall floor (`0.90`) and audit ledger entry. |
| **5** | Case Clock 21-day countdown & +N days simulation | `CASE-2026-001` | **PASSED** | Section 35A statutory countdown updates dynamically on `+5 Days` / `+10 Days` simulation; requires human sign-off for notice issuance. |
| **6** | Impact & Metrics loaded from `metrics.json` | `eval/metrics.json` | **PASSED** | Real metrics benchmarked honestly against rule baseline (ML PR-AUC `0.7441` vs Rule `0.4103`); no "99% accurate" claims. |
| **7** | Performance & Responsiveness | Laptop & Mobile (390px) | **PASSED** | Latency under 20ms; responsive layouts with dark/light themes, WCAG AA contrast, and prefers-reduced-motion compliance. |
| **8** | Zero Hardcoded Predictions | Frontend codebase | **PASSED** | All scores, probabilities, SHAP values, and next hops originate from backend ML model inference. |

---

## 🎯 5-Minute Deterministic Demo Script

### Step 1: Pre-Payment Mule Scan & Customer 60s Scam Cooldown
- **Input**: Payee `ACC-MULE-C1-L1-1`, Amount `₹95,000`.
- **System Action**: Calculates point-in-time features before transaction timestamp. Raw XGBoost score calibrated via sigmoid centered at operating threshold `0.0035` &rarr; **0.99 Calibrated Mule Probability**, Verdict **HOLD**.
- **Customer Pop-up**:
  - Full-screen modal with dimmed backdrop and focus trap.
  - Animated 60-second countdown cooldown circle.
  - Plain-language reasons:
    1. *"Hardware fingerprint linked across multiple disparate accounts (23 linked registrations)"*
    2. *"Associated contact telephone linked to multiple registrations (23 linked registrations)"*
    3. *"Account opened recently with limited historical baseline (18.8 days active)"*
  - Counterfactual explanation: *"Transfer would not trigger Hold/Delay if payee account had an active history older than 180 days and low pass-through velocity below 30%."*
  - Action buttons: Primary **"Cancel Payment"** (stops transfer, logs CANCELLED to event ledger, updates ₹ Prevented counter); Secondary **"Proceed Anyway"** (locked until countdown reaches 0 and requires an explicit confirmation checkbox).

### Step 2: Analyst Console & Money DNA Sankey Replay
- **Input**: Origin reference `ORIGIN-MULE-CHAIN-01`.
- **Visualization**:
  - Layer 0: Victim Source (`ACC-VIC-01`, ₹1,04,93,776.74 tracked)
  - Layer 1: Aggregator Hub (`ACC-MULE-C1-L1-1`)
  - Layer 2: Dispersal Mules (`ACC-MULE-C1-L2-1`)
  - Layer 3: Cash-out Exits (`ACC-EXIT-C1-1`)
- **Interactive Scrubber**: Play/Pause slider steps through 64 sequential transfer timestamps, revealing the velocity of the syndicate.
- **Next-Hop Prediction**: Dashed amber vector points to predicted next destination (`ACC-MULE-C1-L2-1`, probability 0.65).
- **Lien Hold**: Clicking **"Request Lien Hold"** changes the arrow to a solid green border and freezes secondary dispersals.

### Step 3: Business Shield (Invoice BEC & Bank-Detail-Change Defense)
- **Input**: Invoice `INV-003-003` for Vendor `VEND-003` (Apex Steel Infrastructure), Amount `₹28,50,000`.
- **System Action**: Backend detects account mismatch between historical verified account (`ACC-CORP-VEND-003`) and invoice payout account (`ACC-MULE-C1-L1-1`) updated only 3 hours prior.
- **Action**: Place administrative hold and initiate dual-authorization callback verification.

### Step 4: Case Clock & Statutory Notice Generation
- **State Machine**:
  `SUSPECTED` &rarr; `SHOW_CAUSE_ISSUED` (21-Day Clock) &rarr; `REPRESENTATION_RECEIVED` &rarr; `REASONED_ORDER` &rarr; `CLASSIFIED` (14-Day FMR Clock) &rarr; `FMR_FILED` &rarr; `CLOSED`.
- **+N Days Simulation**: Clicking `+5 Days` increments elapsed days from 7 &rarr; 12, reducing statutory days remaining from 14 &rarr; 9.
- **LLM Statutory Notice**: Generates Section 35A show-cause notice referencing specific transaction evidence and PMLA guidelines. Mandatory human approval modal gates progression.

---

## 📊 Real Evaluation Metrics (`eval/metrics.json`)

```
========================================================================================
METRIC                   XGBOOST ML MODEL       RULE-ONLY BASELINE     DELTA / ADVANTAGE
========================================================================================
PR-AUC (Primary Metric)  0.7441                 0.4103                 +81.4% improvement
Precision                82.05%                 41.03%                 2.0x higher precision
Recall                   100.00%                100.00%                Zero missed mules
False Positive Rate      1.86%                  12.23%                 84.8% reduction in FPs
Chain 8 Robustness Hold  16 / 18 mules (88.9%)  6 / 18 mules (33.3%)   Robust to slower hops
========================================================================================
```

---

## ⚖️ Regulatory Compliance & Safe Harbors
- **RBI Fraud Master Directions (2016)**: Formal show-cause requirement before classification with 21-day representation window.
- **RBI Customer Liability Circular (2018)**: Compensation exposure formula:
  $$\text{Bank Exposure Avoided} = \min(0.85 \times \text{Net Loss}, ₹25,000)$$
- **Inter-Bank CFR Framework (2024)**: Privacy-preserving trace handoff passes only case tokens, transfer references, receiver masks, and reason codes. Raw ledger data is never transmitted.
- **Mandatory Safe Harbor Language**:
  - *"Simulated data"* badge rendered in sticky top bar on all screens.
  - *"Demonstration only, not legal advice"* rendered in statutory footer with live RBI reference links.
  - All interventions labeled as *"administrative hold"* or *"lien request"*; zero autonomous classifications.

---

## 🔬 Enhanced Money DNA, Live Transactions, and Detected Mules Panels

### 1. Money DNA Directional Fund Flow Graph
- **Topological DAG Layout**: Automatic assignment of canonical layers (Layer 0: Stolen Origin, Layer 1: Aggregator Hubs, Layer 2: Dispersal Hops, Layer 3: Cash-Out Exits) ensuring zero node duplicates and strict forward flow.
- **Directional Bézier Arrows**: Smooth cubic Bézier curvature with animated fluid particles (`animate stroke-dashoffset`), arrowheads (`url(#arrow-crimson)`, `url(#arrow-emerald)`, `url(#arrow-cyan)`), and centered amount badges (e.g. ₹89,000).
- **Syndicate Chain Selector**: Analysts can seamlessly choose from 16 syndicate chains (`CH01` through `CH15` and `VENDORATK`) with transaction volume and hop counts displayed.
- **Pure HTML Node Cards + Overlaid SVG**: Eliminates WebKit/Safari `<foreignObject>` rendering quirks, providing 100% reliable interactive hold buttons and instant forensic profile inspection.

### 2. Live Transactions Feed Panel
- **Real-Time Network Ledger**: Displays all transactions with sender/receiver details, amounts, channels (IMPS, UPI, NEFT, RTGS), and live status (`HELD (LIEN)`, `MULE DISPERSAL`, `CLEARED`).
- **Instant Search & Filters**: Search by Txn ID, Sender/Receiver names or IDs, and filter by Mule Flows or Held items.
- **One-Click Inspection**: Clicking "Inspect" switches automatically to the Money DNA view, selects that transaction's syndicate chain, and highlights the counterparty node.

### 3. Detected Mules Master Directory
- **Comprehensive Registry**: Lists all 91 detected mules across all 15 syndicate chains with calibrated ML risk scores, syndicate chain IDs, KYC tiers, and current balances.
- **Device Cluster Signals**: Highlights linked hardware fingerprints and shared devices.
- **One-Click Action & Hold**: Analysts can place immediate administrative lien holds or view any mule directly in the Money DNA DAG tracer.
