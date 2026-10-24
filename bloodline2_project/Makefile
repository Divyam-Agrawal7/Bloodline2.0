# Bloodline 2.0 - Bank-Grade Mule Defense Platform Makefile

.PHONY: all dev test build train data clean help

all: dev

help:
	@echo "Bloodline 2.0 Commands:"
	@echo "  make dev      - Start backend server and serve full web platform on http://127.0.0.1:8000"
	@echo "  make test     - Run pytest suite (30 unit & e2e acceptance checks)"
	@echo "  make build    - Compile and bundle React + TypeScript + Tailwind frontend"
	@echo "  make train    - Retrain XGBoost mule detection model and update eval/metrics.json"
	@echo "  make data     - Regenerate multi-bank synthetic ledger dataset (seed 42)"
	@echo "  make clean    - Remove build artifacts and caches"

dev:
	@./start.sh

test:
	@.venv/bin/pytest tests/ -v

build:
	@cd frontend && pnpm run build

train:
	@.venv/bin/python3 app/ml/train.py

data:
	@.venv/bin/python3 data/simulator.py

clean:
	@rm -rf frontend/dist __pycache__ .pytest_cache
