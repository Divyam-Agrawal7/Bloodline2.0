# Bloodline 2.0 Data Dictionary

## Core Schemas

### 1. Account Entity
| Field | Type | Description |
|---|---|---|
| `account_id` | String | Pseudonymous identifier (e.g., `ACC-MULE-HUB1`) |
| `pseudonymous_label` | String | Masked investigative alias |
| `account_type` | String | `COMMERCIAL`, `CHECKING`, `SAVINGS`, `EXCHANGE_GATEWAY`, `NEW_BUSINESS` |
| `balance` | Float | Current balance in institution |
| `status` | String | `ACTIVE`, `FROZEN`, `RESTRICTED`, `CLOSED` |
| `mule_score` | Float | Behavioral composite score [0.0 - 1.0] |
| `velocity_in_24h` | Float | Cumulative inbound amount past 24 hours |
| `velocity_out_24h` | Float | Cumulative outbound amount past 24 hours |
| `is_dormant_reactivated` | Boolean | True if account dormant >180 days suddenly transacts |

### 2. Transaction Edge
| Field | Type | Description |
|---|---|---|
| `transaction_id` | String | Unique transfer reference (e.g., `TXN-ORIGIN-75K`) |
| `sender_account_id` | String | Originating account |
| `receiver_account_id` | String | Destination account |
| `amount` | Float | Transfer currency amount |
| `currency` | String | Default: `USD` |
| `channel` | String | `FAST_PAY`, `WIRE`, `ACH`, `MOBILE_APP` |
| `timestamp` | ISO8601 | Payment creation timestamp |
| `status` | String | `COMPLETED`, `HELD`, `CANCELLED`, `RELEASED` |
| `is_tainted` | Boolean | Flag for Money DNA seed tracing |

### 3. Investigation Case
| Field | Type | Description |
|---|---|---|
| `case_id` | String | Unique case identifier (e.g., `CASE-2026-ALPHA-01`) |
| `current_state` | String | `suspected`, `show_cause_pending`, `representation_window`, `order_pending`, `classified`, `reported_closed`, `false_positive_closed` |
| `deadline_at` | ISO8601 | Configurable regulatory response deadline |
| `assigned_role_required` | String | `analyst`, `senior_investigator`, `compliance_officer` |
| `audit_history` | Array | Append-only sequence of state transitions with timestamp, actor, prior state, new state, and rationale |
