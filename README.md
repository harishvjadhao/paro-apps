# Nifty 200 Stock Viewer

This repository contains a local full-stack application for browsing, syncing, and reviewing Nifty 200 stocks.

## Status

Core application flow is implemented.

The backend now supports two practical data paths:

- Default local bootstrap path: sample market data is generated into SQLite so the UI is immediately usable even when `yfinance` is blocked by local SSL or network restrictions.
- Real sync path: the UI `Sync` button still calls the live backend sync endpoint, which attempts to fetch real Yahoo Finance data and reports partial failure if data cannot be fetched.

## Structure

- `frontend`: React + TypeScript + Vite UI
- `backend`: FastAPI + SQLite + SQLAlchemy API
- `requirements.md`: source-of-truth specification
- `TRACKER.md`: implementation backlog and status tracker
- `BUILD_INSTRUCTIONS.md`: execution brief for implementation agents

## Setup

### Backend

Install dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

Seed stock metadata and populate local sample-backed market data:

```bash
cd backend
python -m app.scripts.seed_stocks
python -m app.scripts.run_sync
```

Run the API server:

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

Install dependencies:

```bash
cd frontend
npm install
```

Run the dev server:

```bash
cd frontend
npm run dev
```

Build the frontend:

```bash
cd frontend
npm run build
```

## Data Behavior

- `.env.example` defaults `BACKEND_DATA_SOURCE_MODE=mock`.
- In `mock` mode, local bootstrap syncs populate SQLite using deterministic sample price history so the app can render populated stock data offline or behind restrictive SSL interception.
- `POST /api/sync` still attempts live `yfinance` retrieval for the UI sync button.
- If live sync cannot fetch data, sync status and logs report the partial failure instead of silently pretending fresh data was loaded.

## Verified Commands

These commands were executed successfully in the current environment:

```bash
cd backend && python -m pip install -r requirements.txt
cd frontend && npm install
cd backend && python -m app.scripts.seed_stocks
cd backend && python -m app.scripts.run_sync
cd backend && python -m pytest
cd frontend && npm run build
cd frontend && npm run test -- --run
```

Notes:

- The frontend build succeeds in the current environment, but Vite prints a Node engine warning because the installed Node version is `20.9.0` and Vite 7 prefers `20.19+`.
- Frontend tests use `jsdom` with Vitest and are currently pinned to a Node-compatible `jsdom` version for this environment.
- Live `yfinance` requests currently fail in this environment due to a certificate chain restriction, which is why the sample-data bootstrap path is enabled for normal local usage.