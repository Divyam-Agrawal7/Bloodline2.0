# Bloodline Bank

A demo internet bank that uses Bloodline 2.0 (`../bloodline2_project`) as its fraud detector.

| App | URL |
|---|---|
| Bloodline Bank | http://127.0.0.1:8001 |
| Bloodline 2.0 detector | http://127.0.0.1:8000 |

## Run

`run.bat` starts both servers with the detector's virtual environment and opens the bank. Or by hand:

```
cd ..\bloodline2_project
.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
cd ..\bloodline_bank
..\bloodline2_project\.venv\Scripts\python.exe -m uvicorn app:app --port 8001
```

## Logins

- **Customer**: any customer account ID from the detector ledger, such as `ACC00001`. Password `demo123`.
- **Admin**: `admin` / `admin123`.

Set `USER_PASSWORD`, `ADMIN_PASSWORD`, `DETECTOR_URL` or `BLOODLINE_DB` to change these.

## How it works

- Accounts are copied from `bloodline2_project/data/bloodline.db` into `bank.db` the first time the bank starts, so every payee has history for the detector to score. Customer balances are topped up for the demo. Delete `bank.db` to start over.
- Before a payment, the bank calls the detector's `/scan` on the payee. The mule probability maps to a risk band: medium at 0.40 or above, high at 0.70 or above.
- Medium risk pauses the payer for 30 seconds and high risk for 60. The server enforces the pause. You can change both pauses and both thresholds under **Admin → Settings**.
- Admin reviews override the model. **Flag** gives at least a medium warning. **Block** rejects all payments to and from the account and sends `/hold-request` to the detector. **Ignore** turns warnings off and reports a `FALSE_POSITIVE` to the detector.
- **Admin → Simulation** runs parallel random traffic, mule rings (several victims pay one mule at once, then the mule sweeps the money to exit accounts) and load bursts.
- The admin view also contains the Bloodline 2.0 analyst tools, reached through the bank at `/api/admin/detector/*`:
  - **Pre-payment scan**: risk gauge, SHAP reasons, counterfactual and next hops.
  - **Analyst console**: Money DNA chain replay, ledger feed and mules directory.
  - **Case queue**, **Business Shield**, and **Impact & ML eval**.

The retrained detector model is almost binary. It rarely scores anything between 0.40 and 0.70, so medium warnings mostly come from flagged accounts.
