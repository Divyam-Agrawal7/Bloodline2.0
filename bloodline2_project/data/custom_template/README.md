# Bloodline 2.0 — Custom Dataset Template

You can import your own real or custom synthetic transaction graphs into Bloodline 2.0.

## File Schemas

### 1. `accounts.csv` (Required)
| Column | Type | Required | Description |
|---|---|---|---|
| `id` | TEXT | **Yes** | Unique account identifier (e.g. `ACC-001`) |
| `bank_id` | TEXT | No | Bank identifier (default: `BANK_ALPHA`) |
| `open_date` | TEXT | No | ISO date `YYYY-MM-DD` (default: `2025-01-01`) |
| `kyc_tier` | TEXT | No | `TIER_1`, `TIER_2`, `TIER_3` |
| `is_mule` | INTEGER | No | `1` if known mule ground truth, `0` if legitimate |
| `role` | TEXT | No | `AGGREGATOR_L1`, `DISPERSAL_L2`, `CASH_OUT`, `LEGIT_RETAIL` |
| `initial_balance` | REAL | No | Account balance (default: `50000.0`) |

### 2. `transactions.csv` (Required)
| Column | Type | Required | Description |
|---|---|---|---|
| `id` | TEXT | **Yes** | Unique transaction ID (e.g. `TXN-001`) |
| `ts` | TEXT | **Yes** | ISO-8601 timestamp (e.g. `2026-10-23T10:00:00Z`) |
| `sender` | TEXT | **Yes** | Source account ID |
| `receiver` | TEXT | **Yes** | Destination account ID |
| `amount` | REAL | **Yes** | Transfer amount in ₹ |
| `channel` | TEXT | No | `UPI`, `IMPS`, `NEFT`, `RTGS` (default: `UPI`) |
| `ref` | TEXT | No | Transfer reference string |
| `is_mule_flow` | INTEGER | No | `1` if part of mule flow, `0` otherwise |
| `chain_id` | TEXT | No | Identifier linking related mule hops (e.g. `CHAIN-1`) |

### 3. `devices.csv` (Optional)
| Column | Type | Description |
|---|---|---|
| `account_id` | TEXT | Account ID |
| `device_id` | TEXT | Hardware fingerprint (e.g. `DEV-001`) |
| `ip` | TEXT | IP address |
| `phone` | TEXT | Contact telephone |

*(If omitted, default 1-to-1 synthetic hardware fingerprints are auto-generated)*

---

## Ingestion Command

```bash
# Ingest data from folder and retrain ML model
python data/ingest_custom.py --dir data/custom_template/ --retrain

# Or specify individual CSV files:
python data/ingest_custom.py --accounts my_accounts.csv --transactions my_txns.csv
```
