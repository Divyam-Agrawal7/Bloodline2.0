# Bloodline 2.0

A bank-side defence against money-mule fraud. It checks every payment before money moves. If the payee looks like a mule account, the customer gets a warning and a cooling-off pause. Analysts get tools to trace stolen money and act on it.

All data is synthetic.

| Folder | What it is | Port |
|---|---|---|
| [`bloodline2_project/`](bloodline2_project) | The detector: XGBoost, Isolation Forest and graph scoring, SHAP reasons, Money DNA lineage, next-hop prediction, case clock, Business Shield | 8000 |
| [`bloodline_bank/`](bloodline_bank) | A demo internet bank that uses the detector, with a customer login and an admin login | 8001 |

## Run it (Windows)

Needs Python 3.12.

```powershell
cd bloodline2_project
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt xgboost shap pandas joblib
cd ..\bloodline_bank
.\run.bat
```

`run.bat` starts both servers and opens http://127.0.0.1:8001. To start them by hand:

```powershell
cd bloodline2_project
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
cd ..\bloodline_bank
..\bloodline2_project\.venv\Scripts\python.exe -m uvicorn app:app --port 8001
```

## Logins

| Role | Username | Password |
|---|---|---|
| Customer | any customer account ID, e.g. `ACC00001` | `demo123` |
| Admin | `admin` | `admin123` |

## What's inside

**Customer (net banking):** balance, payees, statement and fund transfer. Before each transfer the payee is scanned:

- **Medium risk:** a 30-second pause before the customer can send anyway.
- **High risk:** a 60-second pause.

The pause is enforced on the server. The admin can change both lengths in Settings.

**Admin:**

- **Live monitor** and **Simulation:** many payments at once in real time, mule rings, and load bursts.
- **Suspicious accounts:** flag, block or ignore each account.
- **Pre-payment scan:** the full explanation behind any payee's score.
- **Analyst console:** Money DNA replay, ledger feed and mules directory.
- **Case queue**, **Business Shield**, and **Impact & ML eval**.

See [`bloodline_bank/README.md`](bloodline_bank/README.md) and [`bloodline2_project/README.md`](bloodline2_project/README.md) for details.

## Notes

- **Test with known accounts:** `ACC02228` is a known mule and scores high risk. `ACC02041` is a normal shop and scores low.
- **Medium warnings are rare:** the model is almost all-or-nothing. They mostly appear after an admin flags an account.
- **Resetting the bank:** delete `bloodline_bank/bank.db` to reset accounts and balances.
