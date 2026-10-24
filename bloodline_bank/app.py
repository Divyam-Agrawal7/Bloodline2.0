import asyncio
import json
import os
import random
import secrets
import sqlite3
import time
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

HERE = Path(__file__).parent
DETECTOR_URL = os.environ.get("DETECTOR_URL", "http://127.0.0.1:8000")
DETECTOR_DB = Path(os.environ.get("BLOODLINE_DB", HERE.parent / "bloodline2_project" / "data" / "bloodline.db"))
BANK_DB = HERE / "bank.db"
USER_PASSWORD = os.environ.get("USER_PASSWORD", "demo123")
ADMIN_USER, ADMIN_PASSWORD = "admin", os.environ.get("ADMIN_PASSWORD", "admin123")
CUSTOMER_ROLES = ("NORMAL", "SHOPKEEPER", "NEW_GENUINE", "BUSINESS", "PAYROLL", "TRADER")
RISKY_ROLES = ("MULE_L1", "MULE_L2", "MULE_EXIT", "MULE_VENDOR_ATTACK", "RECRUITER", "CASHOUT_EXTERNAL")
DEFAULT_SETTINGS = {"medium_seconds": 30, "high_seconds": 60, "medium_threshold": 0.40, "high_threshold": 0.70}
RANK = {"low": 0, "unknown": 0, "medium": 1, "high": 2, "blocked": 3}

app = FastAPI(title="Bloodline Bank")
sessions = {}
checks = {}
sim = {"task": None, "rate": 1.0, "concurrency": 4, "heed": 0.7, "ring_every": 20, "rings": set()}
detector = {"ok": None, "error": ""}
scan_gate = asyncio.Semaphore(6)


def db():
    conn = sqlite3.connect(BANK_DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    fresh = not BANK_DB.exists()
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, name TEXT, balance REAL,
            role TEXT, can_login INTEGER, opened TEXT);
        CREATE TABLE IF NOT EXISTS transfers (id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT, ts REAL,
            from_id TEXT, to_id TEXT, amount REAL, remarks TEXT, status TEXT, risk TEXT, score REAL,
            verdict TEXT, reasons TEXT, waited INTEGER, source TEXT);
        CREATE TABLE IF NOT EXISTS payees (owner TEXT, payee TEXT, PRIMARY KEY (owner, payee));
        CREATE TABLE IF NOT EXISTS account_status (account_id TEXT PRIMARY KEY, status TEXT,
            note TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value REAL);
        """)
        for k, v in DEFAULT_SETTINGS.items():
            c.execute("INSERT OR IGNORE INTO settings VALUES (?, ?)", (k, v))
        if fresh:
            if not DETECTOR_DB.exists():
                raise RuntimeError(f"Detector ledger not found at {DETECTOR_DB}; set BLOODLINE_DB")
            src = sqlite3.connect(DETECTOR_DB)
            rows = src.execute("SELECT id, pseudonymous_label, current_balance, role, open_date "
                               "FROM accounts WHERE bank_id = 'INTERNAL' OR role LIKE 'MULE%'").fetchall()
            src.close()
            for acc_id, name, bal, role, opened in rows:
                customer = role in CUSTOMER_ROLES
                bal = max(bal, random.uniform(80000, 400000)) if customer else bal
                c.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)",
                          (acc_id, name, round(bal, 2), role, int(customer), opened))


init_db()


def all_settings():
    with db() as c:
        return {r["key"]: r["value"] for r in c.execute("SELECT * FROM settings")}


def account(acc_id):
    with db() as c:
        r = c.execute("SELECT * FROM accounts WHERE id = ?", (acc_id,)).fetchone()
    return dict(r) if r else None


def status_of(acc_id):
    with db() as c:
        r = c.execute("SELECT status FROM account_status WHERE account_id = ?", (acc_id,)).fetchone()
    return r["status"] if r else None


def session(authorization: str = Header(default="")):
    s = sessions.get(authorization.removeprefix("Bearer ").strip())
    if not s:
        raise HTTPException(401, "Please log in")
    return s


def user_session(s=Depends(session)):
    if s["role"] != "user":
        raise HTTPException(403, "Customer login required")
    return s


def admin_session(s=Depends(session)):
    if s["role"] != "admin":
        raise HTTPException(403, "Admin login required")
    return s


@app.post("/api/login")
def login(body: dict):
    role, username, password = body.get("role"), (body.get("username") or "").strip().upper(), body.get("password")
    if role == "admin":
        if username != ADMIN_USER.upper() or password != ADMIN_PASSWORD:
            raise HTTPException(401, "Wrong admin username or password")
        acc_id = None
    else:
        acc = account(username)
        if not acc or not acc["can_login"] or password != USER_PASSWORD:
            raise HTTPException(401, "Wrong customer ID or password")
        acc_id = acc["id"]
    token = secrets.token_urlsafe(24)
    sessions[token] = {"role": "admin" if role == "admin" else "user", "account_id": acc_id}
    return {"token": token, "role": sessions[token]["role"], "account_id": acc_id}


@app.post("/api/logout")
def logout(authorization: str = Header(default="")):
    sessions.pop(authorization.removeprefix("Bearer ").strip(), None)
    return {"ok": True}


@app.get("/api/demo-logins")
def demo_logins():
    with db() as c:
        rows = c.execute("SELECT id, name FROM accounts WHERE role = 'NORMAL' ORDER BY id LIMIT 4").fetchall()
    return {"customers": [dict(r) for r in rows], "user_password": USER_PASSWORD,
            "admin": None if "ADMIN_PASSWORD" in os.environ else {"username": ADMIN_USER, "password": ADMIN_PASSWORD}}


async def scan(from_id, to_id, amount):
    st = all_settings()
    result = {"risk": "unknown", "score": None, "verdict": None, "reasons": [], "available": False,
              "counterfactual": None}
    try:
        async with scan_gate, httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{DETECTOR_URL}/scan", json={"payee_account_id": to_id, "amount": amount,
                                                           "sender_account_id": from_id})
            r.raise_for_status()
            d = r.json()
        detector.update(ok=True, error="")
        p = d["probability"]
        result.update(available=True, score=round(p, 4), verdict=d["verdict"],
                      reasons=d.get("plain_language_reasons", [])[:4], counterfactual=d.get("counterfactual"),
                      risk="high" if p >= st["high_threshold"] else "medium" if p >= st["medium_threshold"] else "low")
    except Exception as e:
        detector.update(ok=False, error=str(e) or type(e).__name__)

    status = status_of(to_id)
    if status == "blocked":
        result.update(risk="blocked", reasons=["This account has been blocked by the bank."] + result["reasons"])
    elif status == "flagged" and RANK[result["risk"]] < RANK["medium"]:
        result.update(risk="medium", reasons=["This account is under review by the bank."] + result["reasons"])
    elif status == "ignored" and result["risk"] in ("medium", "high"):
        result["risk"] = "low"
    result["wait_seconds"] = int(st["high_seconds"] if result["risk"] == "high"
                                 else st["medium_seconds"] if result["risk"] == "medium" else 0)
    return result


async def detector_feedback(path, body):
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            await c.post(f"{DETECTOR_URL}{path}", json=body)
    except Exception:
        pass


def record(from_id, to_id, amount, remarks, status, check, waited, source):
    ref = "BLB" + "".join(random.choices("0123456789", k=10))
    with db() as c:
        if status == "completed":
            c.execute("UPDATE accounts SET balance = round(balance - ?, 2) WHERE id = ?", (amount, from_id))
            c.execute("UPDATE accounts SET balance = round(balance + ?, 2) WHERE id = ?", (amount, to_id))
            c.execute("INSERT OR IGNORE INTO payees VALUES (?, ?)", (from_id, to_id))
        cur = c.execute("""INSERT INTO transfers (ref, ts, from_id, to_id, amount, remarks, status, risk, score,
                           verdict, reasons, waited, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (ref, time.time(), from_id, to_id, amount, remarks, status, check["risk"],
                         check["score"], check["verdict"], json.dumps(check["reasons"]), waited, source))
        return {"id": cur.lastrowid, "ref": ref, "status": status, "amount": amount, "to_id": to_id}


def validate(from_id, to_id, amount):
    amount = round(float(amount), 2)
    sender, payee = account(from_id), account(to_id)
    if amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if not payee:
        raise HTTPException(404, "No account with that number")
    if from_id == to_id:
        raise HTTPException(400, "You can't pay your own account")
    if status_of(from_id) == "blocked":
        raise HTTPException(403, "Your account is blocked. Please contact the bank.")
    if sender["balance"] < amount:
        raise HTTPException(400, "Insufficient balance")
    return amount


@app.get("/api/user/summary")
def user_summary(s=Depends(user_session)):
    acc = account(s["account_id"])
    return {"id": acc["id"], "name": acc["name"], "balance": acc["balance"], "opened": acc["opened"],
            "status": status_of(acc["id"])}


@app.get("/api/user/statement")
def user_statement(s=Depends(user_session)):
    me = s["account_id"]
    with db() as c:
        rows = c.execute("""SELECT t.*, a.name AS from_name, b.name AS to_name FROM transfers t
                            LEFT JOIN accounts a ON a.id = t.from_id LEFT JOIN accounts b ON b.id = t.to_id
                            WHERE t.from_id = ? OR (t.to_id = ? AND t.status = 'completed')
                            ORDER BY t.id DESC LIMIT 100""", (me, me)).fetchall()
    out = []
    for r in rows:
        debit = r["from_id"] == me
        out.append({"ref": r["ref"], "ts": r["ts"], "status": r["status"], "remarks": r["remarks"],
                    "counterparty": r["to_id"] if debit else r["from_id"],
                    "counterparty_name": r["to_name"] if debit else r["from_name"],
                    "debit": r["amount"] if debit else None, "credit": None if debit else r["amount"],
                    "risk": r["risk"] if debit else None})
    return out


@app.get("/api/user/payees")
def user_payees(s=Depends(user_session)):
    with db() as c:
        rows = c.execute("SELECT a.id, a.name FROM payees p JOIN accounts a ON a.id = p.payee "
                         "WHERE p.owner = ? ORDER BY a.name", (s["account_id"],)).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/user/payees")
def add_payee(body: dict, s=Depends(user_session)):
    pid = (body.get("payee_id") or "").strip().upper()
    acc = account(pid)
    if not acc:
        raise HTTPException(404, "No account with that number")
    if pid == s["account_id"]:
        raise HTTPException(400, "You can't add your own account as a payee")
    with db() as c:
        c.execute("INSERT OR IGNORE INTO payees VALUES (?, ?)", (s["account_id"], pid))
    return {"id": pid, "name": acc["name"]}


@app.delete("/api/user/payees/{pid}")
def remove_payee(pid: str, s=Depends(user_session)):
    with db() as c:
        c.execute("DELETE FROM payees WHERE owner = ? AND payee = ?", (s["account_id"], pid))
    return {"ok": True}


@app.get("/api/lookup/{acc_id}")
def lookup(acc_id: str, s=Depends(session)):
    acc = account(acc_id.strip().upper())
    if not acc:
        raise HTTPException(404, "No account with that number")
    return {"id": acc["id"], "name": acc["name"]}


@app.post("/api/user/precheck")
async def user_precheck(body: dict, s=Depends(user_session)):
    to_id = (body.get("to_id") or "").strip().upper()
    amount = validate(s["account_id"], to_id, body.get("amount", 0))
    check = await scan(s["account_id"], to_id, amount)
    check.update(id=secrets.token_hex(8), from_id=s["account_id"], to_id=to_id, amount=amount,
                 remarks=body.get("remarks", ""), issued_at=time.time(), payee_name=account(to_id)["name"])
    checks[check["id"]] = check
    return check


@app.post("/api/user/transfer")
async def user_transfer(body: dict, s=Depends(user_session)):
    check = checks.get(body.get("check_id"))
    if not check or check["from_id"] != s["account_id"]:
        raise HTTPException(400, "This payment has expired. Please start again.")
    warned = check["risk"] in ("medium", "high")
    if body.get("decision") == "cancel":
        checks.pop(check["id"])
        if warned:
            await detector_feedback("/decision", {"account_id": check["to_id"], "outcome": "CANCELLED",
                                                  "analyst_note": "Bloodline Bank customer cancelled after warning"})
        return record(check["from_id"], check["to_id"], check["amount"], check["remarks"], "cancelled",
                      check, 0, "user")
    if check["risk"] == "blocked":
        checks.pop(check["id"])
        record(check["from_id"], check["to_id"], check["amount"], check["remarks"], "blocked", check, 0, "user")
        raise HTTPException(403, "Payments to this account are blocked by the bank")
    wait = check["issued_at"] + check["wait_seconds"] - time.time()
    if wait > 0:
        raise HTTPException(425, f"Please wait {int(wait) + 1}s before sending")
    validate(check["from_id"], check["to_id"], check["amount"])
    checks.pop(check["id"])
    if warned:
        await detector_feedback("/decision", {"account_id": check["to_id"], "outcome": "PROCEEDED",
                                              "analyst_note": "Bloodline Bank customer sent anyway after the pause"})
    return record(check["from_id"], check["to_id"], check["amount"], check["remarks"], "completed",
                  check, check["wait_seconds"], "user")


def _pick(roles, n=1, min_balance=0):
    q = ",".join("?" * len(roles))
    with db() as c:
        rows = c.execute(f"SELECT id, balance FROM accounts WHERE role IN ({q}) AND balance >= ? "
                         f"ORDER BY random() LIMIT ?", (*roles, min_balance, n)).fetchall()
    return [dict(r) for r in rows]


async def simulated_payment(from_id, to_id, amount, heeds=True, remarks="Sim payment"):
    try:
        amount = validate(from_id, to_id, amount)
    except HTTPException:
        return None
    check = await scan(from_id, to_id, amount)
    if check["risk"] == "blocked":
        return record(from_id, to_id, amount, remarks, "blocked", check, 0, "sim")
    if check["risk"] in ("medium", "high") and heeds and random.random() < sim["heed"]:
        return record(from_id, to_id, amount, remarks, "cancelled", check, 0, "sim")
    try:
        validate(from_id, to_id, amount)
    except HTTPException:
        return None
    return record(from_id, to_id, amount, remarks, "completed", check, 0, "sim")


async def mule_ring():
    mule = _pick(("MULE_L1",))
    victims = _pick(CUSTOMER_ROLES, random.randint(5, 9), 20000)
    if not mule or not victims:
        return
    mule_id = mule[0]["id"]
    await asyncio.gather(*[simulated_payment(v["id"], mule_id, random.uniform(8000, min(60000, v["balance"] * .4)),
                                             remarks="Job deposit") for v in victims])
    await asyncio.sleep(random.uniform(1, 3) / sim["rate"])
    pot = account(mule_id)["balance"] * random.uniform(.85, .95)
    exits = _pick(("MULE_L2", "MULE_EXIT"), random.randint(2, 4))
    for e in exits:
        await simulated_payment(mule_id, e["id"], pot / len(exits), heeds=False, remarks="Transfer")
        await asyncio.sleep(random.uniform(.3, 1) / sim["rate"])


def start_ring():
    task = asyncio.create_task(mule_ring())
    sim["rings"].add(task)
    task.add_done_callback(sim["rings"].discard)


async def one_random_payment():
    src = _pick(CUSTOMER_ROLES, 1, 5000)
    if not src:
        return
    src = src[0]
    roll = random.random()
    dst = _pick(RISKY_ROLES if roll < .1 else ("NEW_GENUINE",) if roll < .2 else CUSTOMER_ROLES)
    if dst and dst[0]["id"] != src["id"]:
        amt = min(src["balance"] * .3, random.lognormvariate(8.3, .9))
        await simulated_payment(src["id"], dst[0]["id"], amt)


async def sim_loop():
    n = 0
    while True:
        n += 1
        if n % sim["ring_every"] == 0:
            start_ring()
        await asyncio.gather(*[one_random_payment() for _ in range(sim["concurrency"])])
        await asyncio.sleep(1 / sim["rate"])


def sim_state():
    return {"on": sim["task"] is not None and not sim["task"].done(), "rate": sim["rate"],
            "concurrency": sim["concurrency"], "heed": sim["heed"], "ring_every": sim["ring_every"],
            "rings_running": len(sim["rings"])}


def stop_sim():
    if sim["task"] is not None and not sim["task"].done():
        sim["task"].cancel()
    sim["task"] = None
    for t in list(sim["rings"]):
        t.cancel()


@app.get("/api/admin/state")
def admin_state(s=Depends(admin_session)):
    with db() as c:
        feed = c.execute("""SELECT t.*, a.name AS from_name, b.name AS to_name FROM transfers t
                            LEFT JOIN accounts a ON a.id = t.from_id LEFT JOIN accounts b ON b.id = t.to_id
                            ORDER BY t.id DESC LIMIT 80""").fetchall()
        stats = c.execute("""SELECT COUNT(*) AS total,
                COALESCE(SUM(status = 'completed'), 0) AS completed,
                COALESCE(SUM(status = 'cancelled'), 0) AS cancelled,
                COALESCE(SUM(status = 'blocked'), 0) AS blocked,
                COALESCE(SUM(risk = 'high'), 0) AS high, COALESCE(SUM(risk = 'medium'), 0) AS medium,
                COALESCE(SUM(CASE WHEN status IN ('cancelled', 'blocked') AND risk IN ('medium', 'high', 'blocked')
                                  THEN amount END), 0) AS saved,
                COALESCE(SUM(risk IN ('medium', 'high') AND status = 'completed'), 0) AS sent_anyway
                FROM transfers""").fetchone()
        pending = c.execute("""SELECT COUNT(DISTINCT t.to_id) FROM transfers t
                LEFT JOIN account_status s ON s.account_id = t.to_id
                WHERE t.risk IN ('medium', 'high') AND s.status IS NULL""").fetchone()[0]
    return {"feed": [dict(r, reasons=json.loads(r["reasons"] or "[]")) for r in feed],
            "stats": dict(stats, pending_review=pending), "sim": sim_state(),
            "detector": dict(detector, url=DETECTOR_URL), "settings": all_settings()}


@app.post("/api/admin/sim")
async def admin_sim(body: dict, s=Depends(admin_session)):
    for key, lo, hi, cast in (("rate", .2, 10, float), ("concurrency", 1, 20, int), ("heed", 0, 1, float),
                              ("ring_every", 3, 200, int)):
        if key in body:
            sim[key] = max(lo, min(hi, cast(body[key])))
    if body.get("on") and not sim_state()["on"]:
        sim["task"] = asyncio.create_task(sim_loop())
    elif body.get("on") is False:
        stop_sim()
    return sim_state()


@app.post("/api/admin/sim/ring")
async def admin_ring(s=Depends(admin_session)):
    start_ring()
    return {"ok": True}


@app.post("/api/admin/sim/burst")
async def admin_burst(body: dict, s=Depends(admin_session)):
    count = max(1, min(100, int(body.get("count", 20))))
    started = time.time()
    await asyncio.gather(*[one_random_payment() for _ in range(count)])
    return {"count": count, "seconds": round(time.time() - started, 2)}


@app.get("/api/admin/suspicious")
def admin_suspicious(s=Depends(admin_session)):
    with db() as c:
        rows = c.execute("""
            SELECT a.id, a.name, a.balance, a.opened, st.status, st.note, st.ts AS reviewed_at,
                   COUNT(t.id) AS hits, MAX(t.score) AS max_score, MAX(t.ts) AS last_seen,
                   COUNT(DISTINCT t.from_id) AS payers,
                   COALESCE(SUM(t.amount), 0) AS attempted,
                   COALESCE(SUM(CASE WHEN t.status = 'completed' THEN t.amount END), 0) AS received,
                   MAX(CASE t.risk WHEN 'high' THEN 2 WHEN 'medium' THEN 1 ELSE 0 END) AS worst
            FROM accounts a
            LEFT JOIN transfers t ON t.to_id = a.id AND t.risk IN ('medium', 'high', 'blocked')
            LEFT JOIN account_status st ON st.account_id = a.id
            GROUP BY a.id HAVING hits > 0 OR st.status IS NOT NULL
            ORDER BY (st.status IS NOT NULL), worst DESC, last_seen DESC""").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["risk"] = {2: "high", 1: "medium"}.get(d.pop("worst"), "low")
        out.append(d)
    return out


@app.post("/api/admin/accounts/{acc_id}/action")
async def admin_action(acc_id: str, body: dict, s=Depends(admin_session)):
    action, note = body.get("action"), body.get("note") or ""
    if not account(acc_id):
        raise HTTPException(404, "No such account")
    statuses = {"flag": "flagged", "block": "blocked", "ignore": "ignored"}
    with db() as c:
        if action == "clear":
            c.execute("DELETE FROM account_status WHERE account_id = ?", (acc_id,))
        elif action in statuses:
            c.execute("INSERT OR REPLACE INTO account_status VALUES (?, ?, ?, ?)",
                      (acc_id, statuses[action], note, time.time()))
        else:
            raise HTTPException(400, "action must be flag, block, ignore or clear")
    if action == "block":
        await detector_feedback("/hold-request", {"account_id": acc_id})
    elif action in ("flag", "ignore"):
        await detector_feedback("/decision", {"account_id": acc_id,
                                              "outcome": "FALSE_POSITIVE" if action == "ignore" else "FLAGGED",
                                              "analyst_note": note or f"Bloodline Bank admin: {action}"})
    return {"id": acc_id, "status": statuses.get(action)}


@app.get("/api/admin/accounts/{acc_id}/scan")
async def admin_scan(acc_id: str, s=Depends(admin_session)):
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{DETECTOR_URL}/scan", json={"payee_account_id": acc_id, "amount": 20000})
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(502, f"Detector unavailable: {e}")


@app.get("/api/admin/accounts/{acc_id}/transfers")
def admin_account_transfers(acc_id: str, s=Depends(admin_session)):
    with db() as c:
        rows = c.execute("""SELECT t.*, a.name AS from_name, b.name AS to_name FROM transfers t
                            LEFT JOIN accounts a ON a.id = t.from_id LEFT JOIN accounts b ON b.id = t.to_id
                            WHERE t.from_id = ? OR t.to_id = ? ORDER BY t.id DESC LIMIT 50""",
                         (acc_id, acc_id)).fetchall()
    return [dict(r, reasons=json.loads(r["reasons"] or "[]")) for r in rows]


@app.post("/api/admin/settings")
def admin_settings(body: dict, s=Depends(admin_session)):
    limits = {"medium_seconds": (0, 600), "high_seconds": (0, 600),
              "medium_threshold": (0.01, 0.99), "high_threshold": (0.01, 0.99)}
    new = {k: max(lo, min(hi, float(body[k]))) for k, (lo, hi) in limits.items() if k in body}
    merged = {**all_settings(), **new}
    if merged["medium_threshold"] > merged["high_threshold"]:
        raise HTTPException(400, "Medium threshold must not be above the high threshold")
    with db() as c:
        for k, v in new.items():
            c.execute("UPDATE settings SET value = ? WHERE key = ?", (v, k))
    return all_settings()


@app.post("/api/admin/reset")
def admin_reset(s=Depends(admin_session)):
    stop_sim()
    with db() as c:
        c.executescript("DELETE FROM transfers; DELETE FROM payees; DELETE FROM account_status;")
    checks.clear()
    return {"ok": True}


DETECTOR_ROUTES = ("scan", "chains", "lineage/", "transactions", "mules", "hold-request", "trace-handoff",
                   "cases", "case/", "decision", "invoices", "vendor-check", "stats", "metrics", "thresholds")


@app.api_route("/api/admin/detector/{path:path}", methods=["GET", "POST"])
async def detector_proxy(path: str, request: Request, s=Depends(admin_session)):
    if not any(path == r or (r.endswith("/") and path.startswith(r)) for r in DETECTOR_ROUTES):
        raise HTTPException(404, "Unknown detector route")
    body = await request.body() if request.method == "POST" else None
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.request(request.method, f"{DETECTOR_URL}/{path}", params=request.query_params,
                                content=body, headers={"Content-Type": "application/json"})
        detector.update(ok=True, error="")
    except Exception as e:
        detector.update(ok=False, error=str(e) or type(e).__name__)
        raise HTTPException(502, f"Detector unavailable: {e}")
    try:
        return JSONResponse(r.json(), status_code=r.status_code)
    except ValueError:
        raise HTTPException(502, "Detector returned an invalid response")


@app.get("/")
def page():
    return FileResponse(HERE / "static" / "index.html")
