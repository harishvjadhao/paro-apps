# Nifty 200 Stock Viewer

This repository contains a local full-stack application for browsing, syncing, and reviewing Nifty 200 stocks.

## Status

Core application flow is implemented.

The backend supports two practical data paths:

- Default local bootstrap path: sample market data can be generated into SQLite so the UI is immediately usable even when `yfinance` is blocked by local SSL or network restrictions.
- Real sync path: the UI sync controls call the live backend sync endpoint, which fetches real Yahoo Finance data and reports partial failure only for symbols that actually fail to download.

## Structure

- `frontend`: React + TypeScript + Vite UI
- `backend`: FastAPI + SQLite + SQLAlchemy API
- `requirements.md`: source-of-truth specification
- `TRACKER.md`: implementation backlog and status tracker
- `BUILD_INSTRUCTIONS.md`: execution brief for implementation agents
- `render.yaml`: Render backend service definition for demo deployment
- `frontend/vercel.json`: Vercel frontend configuration

## Setup

### Backend

Install dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

Copy the backend environment template when needed:

```bash
cd backend
copy .env.example .env
```

Seed stock metadata and populate local market data:

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
npm run dev -- --host
```

Build the frontend:

```bash
cd frontend
npm run build
```

For local frontend-to-backend wiring with an explicit API URL, copy `frontend/.env.example` to `frontend/.env` and set `VITE_API_BASE_URL`.

## Data Behavior

- `.env.example` defaults `BACKEND_DATA_SOURCE_MODE=mock`.
- In `mock` mode, local bootstrap syncs populate SQLite using deterministic sample price history so the app can render populated stock data offline or behind restrictive SSL interception.
- `POST /api/sync` uses live `yfinance` retrieval for the UI sync controls even when the default bootstrap path is mock-backed.
- Incremental and single-stock syncs mark a stock as partial when Yahoo returns data but there are no new rows to insert.
- Full sync now clears existing price history and indicator rows for the target stocks before fetching one year of data again.
- If live sync cannot fetch data for a symbol, sync status and logs report the partial failure instead of silently pretending fresh data was loaded.
- On startup, the backend now applies lightweight SQLite schema upgrades for older local databases so newly added stock-sync columns and sync-log fields do not require a manual DB reset.

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
- Live `yfinance` requests were verified in this environment during recent sync checks, including real single-stock and full-sync runs.

## Demo Deployment

This repo is prepared for a demo deployment using Vercel for the frontend and Render for the backend while keeping SQLite.

Important constraints:

- This is suitable for demo purposes only.
- SQLite remains a single-file database and is not a robust production multi-instance setup.
- Render must use a persistent disk, otherwise sync data and comments will be lost on redeploy or restart.
- Free-tier cold starts and long sync times can make full syncs feel slow.

### Deploy Backend To Render

Render should use Python `3.12.3` for this backend. The current dependency set relies on prebuilt wheels for packages like `pydantic-core` and `pandas`, and Render's default Python `3.14.x` can force unsupported source builds.

1. Push the repository to GitHub.
2. In Render, create a new Blueprint or Web Service from the repo.
3. Use the `render.yaml` file at the repository root.
4. Confirm the service root directory is `backend`.
5. Attach the persistent disk defined in `render.yaml` so SQLite lives at `/var/data/app.db`.
6. Set `BACKEND_CORS_ORIGIN` to your deployed frontend origin.
7. Override `BACKEND_DB_PATH=/var/data/app.db` if you are not using the default from `render.yaml`.
8. Keep `BACKEND_DATA_SOURCE_MODE=api` on Render so UI syncs use live Yahoo data.

Example:

```bash
BACKEND_CORS_ORIGIN=https://your-vercel-app.vercel.app,http://127.0.0.1:5173
```

After the first deploy, open a Render shell or one-off job and run:

```bash
cd backend
python -m app.scripts.seed_stocks
```

If you want initial market history before opening the UI, run one sync after seeding:

```bash
cd backend
python -m app.scripts.run_sync
```

### Deploy Frontend To Vercel

1. Import the repository into Vercel.
2. Set the project root to `frontend`.
3. Set the environment variable `VITE_API_BASE_URL` to your Render backend URL with `/api` appended.

Example:

```bash
VITE_API_BASE_URL=https://your-render-service.onrender.com/api
```

4. Deploy the project.

### Recommended Demo Flow

1. Deploy the backend first.
2. Seed stock metadata on Render.
3. Deploy the frontend on Vercel.
4. Verify stock list loading.
5. Run a single-stock sync before running a full sync.

### Deployment Checklist

1. Push the repo to GitHub.
2. Deploy the backend on Render from `render.yaml`.
3. Confirm the Render disk is mounted and `BACKEND_CORS_ORIGIN` is set.
4. Seed stocks on Render.
5. Optionally run one initial sync on Render.
6. Deploy the frontend on Vercel with `frontend` as the root.
7. Set `VITE_API_BASE_URL` in Vercel.
8. Verify `/stocks` loads from the deployed frontend.
9. Test a single-stock sync.
10. Only then test a full sync.
