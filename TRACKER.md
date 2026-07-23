# Project Tracker

Use this tracker while building the application from `requirements.md`.

Status values:

- `Todo`
- `In Progress`
- `Done`
- `Blocked`

## Working Rules

1. Read `requirements.md` fully before implementation.
2. Keep this file updated as tasks move forward.
3. Break large items into smaller tasks when needed.
4. Do not stop at planning. Continue through implementation, validation, and documentation.
5. Mark blockers clearly with a short reason.

## Backlog

| ID | Phase | Task | Status | Notes |
|----|-------|------|--------|-------|
| 1 | Setup | Review `requirements.md` and confirm stack, scope, and conventions | Done | Reviewed build brief, requirements, and tracker before implementation. |
| 2 | Setup | Create `frontend` and `backend` project structure | Done | Created project directories and initial scaffold. |
| 3 | Setup | Add root `README.md` and `.env.example` placeholders | Done | Added initial README and env example; scaffold validated without errors. |
| 4 | Backend | Bootstrap FastAPI app and base routing | Done | App factory, CORS wiring, startup DB init, and health route added. |
| 5 | Backend | Add backend configuration and environment loading | Done | Settings module added with env-backed defaults. |
| 6 | Backend | Add SQLAlchemy setup and SQLite connection | Done | Engine, session factory, and DB dependency added. |
| 7 | Backend | Implement database initialization logic | Done | DB init now creates tables after model registration. |
| 8 | Data | Create database models for `stocks`, `stock_price_history`, `stock_indicators`, and `sync_logs` | Done | Core models added and validated. |
| 9 | Data | Add indexes and unique constraints required by the spec | Done | Constraints and indexes defined in model metadata. |
| 10 | Data | Implement CSV import logic for `ind_nifty200list.csv` | Done | Idempotent CSV seed service added. |
| 11 | Data | Add Yahoo ticker default mapping and override file support | Done | Default `.NS` mapping plus JSON override file added. |
| 12 | Data | Implement seed or bootstrap command to import stock master data | Done | Standalone seed script added. |
| 13 | Sync | Create sync service shared by API and scripts | Done | Shared sync service added for API and CLI use. |
| 14 | Sync | Integrate `yfinance` for historical daily data retrieval | Done | Historical download flow added in sync service. |
| 15 | Sync | Integrate `pandas` for 44-day moving average calculation | Done | 44 DMA calculation added in sync service. |
| 16 | Sync | Upsert daily data into `stock_price_history` | Done | Daily history upsert implemented. |
| 17 | Sync | Update `stock_indicators` with computed fields | Done | Latest indicator snapshot updates added. |
| 18 | Sync | Write sync log entries for success and failure cases | Done | Sync logs created and updated by the service. |
| 19 | Sync | Implement standalone sync command or script | Done | CLI sync script added. |
| 20 | API | Implement `GET /api/stocks` | Done | Stock list endpoint added with API response schema. |
| 21 | API | Implement `GET /api/stocks/{symbol}` | Done | Stock detail endpoint added. |
| 22 | API | Implement `POST /api/sync` | Done | Sync trigger endpoint added. |
| 23 | API | Implement `GET /api/sync/status` | Done | Sync status endpoint added. |
| 24 | API | Implement `GET /api/sync/logs` | Done | Sync log endpoint added. |
| 25 | API | Implement `POST /api/stocks/{symbol}/favorite` | Done | Favorite mutation endpoint added. |
| 26 | API | Implement `POST /api/stocks/{symbol}/watchlist` | Done | Watchlist mutation endpoint added. |
| 27 | API | Implement `POST /api/stocks/reorder` | Done | Reorder mutation endpoint added. |
| 28 | API | Add request and response schemas for all endpoints | Done | Shared request and response schemas added. |
| 29 | Frontend | Bootstrap React + TypeScript + Vite app | Done | Frontend scaffold is already in place and validated. |
| 30 | Frontend | Set up Tailwind CSS, React Query, Axios, clsx, and react-icons | Done | Frontend tooling and packages are already configured. |
| 31 | Frontend | Create app shell and two-panel layout | Done | Two-panel responsive shell now renders live backend data. |
| 32 | Frontend | Build sidebar header with search, filters, view toggles, and sync button | Done | Search, filter chips, and sync trigger are wired. |
| 33 | Frontend | Build grouped industry list with collapse support | Done | Industry groups are now collapsible in the sidebar. |
| 34 | Frontend | Build industry header summary with `above 44 MA / total` and percentage | Done | Industry summary metrics now render in group headers. |
| 35 | Frontend | Build stock list item with signal badge, favorite, watchlist, and reorder controls | Done | Controls and ranking signals added to stock items. |
| 36 | Frontend | Build right-side stock detail panel | Done | Detail panel now shows selected stock metrics and metadata. |
| 37 | Frontend | Build sync summary and sync status banner | Done | Sync status card and summary counts are rendered. |
| 38 | Frontend | Build sync log panel | Done | Recent sync log panel added. |
| 39 | Frontend | Connect stock list and stock detail APIs | Done | App shell is using stock list and detail endpoints. |
| 40 | Frontend | Implement search and filter behavior | Done | Search plus quick filters are working. |
| 41 | Frontend | Implement favorites and watchlist interactions | Done | Favorite and watchlist toggles are wired to backend mutations. |
| 42 | Frontend | Implement reorder interactions within industry group | Done | Up/down reorder is wired within the visible industry list. |
| 43 | Frontend | Implement sync trigger and polling behavior | Done | Sync trigger and status polling are wired. |
| 44 | Frontend | Add loading, empty, and error states | Done | Sidebar and detail panel now show clearer loading, empty, and error states. |
| 45 | Frontend | Ensure industry ordering by percentage above 44 MA | Done | Industry groups are sorted by percentage, then count, then name. |
| 46 | Testing | Add backend unit tests for indicator calculation | In Progress | API-level backend coverage exists; indicator-specific unit tests still remain. |
| 47 | Testing | Add backend API tests for stock, sync, favorite, watchlist, and reorder flows | Done | Pytest coverage added for stock list/detail, mutations, reorder, and sync status/logs. |
| 48 | Testing | Add frontend component tests for rendering and selection | Done | Vitest coverage added for rendering, search filtering, and selection updates. |
| 49 | Testing | Add frontend interaction tests for search, filters, sync, favorite, watchlist, and reorder | In Progress | Search and selection are covered; more interaction coverage still remains. |
| 50 | Docs | Document setup, seed, sync, run, and test commands in `README.md` | Done | README now documents sample bootstrap plus live sync behavior. |
| 51 | Validation | Run local validation for backend, frontend, and tests | In Progress | Backend and frontend tests now pass; broader test coverage still remains. |
| 52 | Finalize | Update tracker statuses and summarize completed work | In Progress | Summary now includes sample fallback plus passing backend/frontend tests. |

## Optional Subtasks

Use this section if a backlog item needs to be broken down further during implementation.

| Parent ID | Subtask | Status | Notes |
|-----------|---------|--------|-------|