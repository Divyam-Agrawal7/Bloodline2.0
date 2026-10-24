from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.api.routes import router as api_router
from app.db.store import BloodlineDatastore
from app.policies.manager import PolicyManager

app = FastAPI(
    title="Bloodline 2.0 — Mule Network Detection and Tracing",
    version="2.0.0",
    description=(
        "Decision-support system for banks and payment providers combining transaction scoring, "
        "account mule indicators, graph investigation, Money DNA flow tracing, next-hop ranking, "
        "cooling-off review queues, and case clock workflows on synthetic data."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API routes at both / and /api/v1
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router)

# Static and Templates
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if (FRONTEND_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Probes required by API outline (Page 3 of README)
@app.get("/health", tags=["System Probes"])
def health_check():
    return {
        "status": "healthy",
        "service": "Bloodline-Core-Decision-Service",
        "environment": "synthetic-demo"
    }

@app.get("/ready", tags=["System Probes"])
def ready_check():
    from app.services.core_engine import CoreEngine
    import sqlite3
    engine = CoreEngine.get_instance()
    conn = sqlite3.connect(engine.db_path)
    acc_count = conn.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    txn_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.close()
    return {
        "status": "ready" if acc_count > 0 else "initializing",
        "accounts_loaded": acc_count,
        "transactions_loaded": txn_count,
        "mules_planted": 63,
        "banks": ["BANK_ALPHA", "BANK_BETA", "BANK_GAMMA"]
    }

@app.get("/", response_class=HTMLResponse, tags=["Web App"])
@app.get("/console", response_class=HTMLResponse, tags=["Web App"])
def serve_index(request: Request):
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"), status_code=200)
    return templates.TemplateResponse("console.html", {"request": request})

@app.get("/legacy-console", response_class=HTMLResponse, tags=["Web App"])
def serve_legacy_console(request: Request):
    return templates.TemplateResponse("console.html", {"request": request})
