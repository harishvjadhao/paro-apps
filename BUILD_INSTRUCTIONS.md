# Build Instructions For AI Agent

Use this file as the execution brief for building the project in this repository.

## Source Documents

1. `requirements.md`
   - This is the source of truth for product scope, technical stack, UI behavior, API contracts, database design, scripts, testing expectations, and implementation conventions.
2. `TRACKER.md`
   - This is the working backlog and progress tracker.

## Primary Instruction

Read `requirements.md` fully before implementation.

Then use `TRACKER.md` to execute the project end to end. Update tracker statuses continuously as work progresses.

Do not stop at scaffolding or planning. Continue until the application is fully runnable locally, tested at a basic level, and documented, unless you encounter a genuine blocker.

## Build Scope

Build a complete local full-stack application with:

- React + TypeScript + Vite frontend
- Tailwind CSS UI
- FastAPI backend
- SQLite database
- SQLAlchemy ORM
- `ind_nifty200list.csv` as the stock universe source of truth
- `yfinance` for historical stock retrieval
- `pandas` for 44-day moving average calculation

## Must Implement

- CSV import and stock master seeding
- Yahoo ticker mapping with override support
- Database initialization logic
- Daily stock sync flow
- Sync logs and sync status
- Stock list grouped by industry
- Industry header summary showing `above 44 MA / total` and percentage
- Default industry ordering by percentage above 44 MA
- Search and filters
- Favorite and watchlist support
- Manual up and down reorder within industry group
- Right-side stock detail panel
- API endpoints defined in `requirements.md`
- Frontend UI components defined in `requirements.md`
- Backend scripts defined in `requirements.md`
- Basic automated tests
- `README.md` with setup, seed, sync, run, and test instructions

## Execution Rules

1. Start by reviewing `requirements.md` and `TRACKER.md`.
2. Mark the first active item in `TRACKER.md` as `In Progress` before implementing it.
3. Move items to `Done` only after implementation and a relevant validation step.
4. If an item is too large, break it into subtasks inside `TRACKER.md`.
5. If blocked, mark the item `Blocked` with a clear note.
6. Keep implementation aligned with the version 1 rules in `requirements.md`.
7. Prefer the simplest local-first implementation that satisfies the requirements.
8. Reuse services and avoid duplicating business logic between API handlers and scripts.
9. Do not skip tests, seed flow, or documentation.
10. Treat the project as complete only when frontend, backend, database setup, seed import, sync flow, and basic tests work together locally.

## Recommended Phase Order

1. Setup and project scaffolding
2. Backend foundation and database
3. CSV seed and ticker mapping
4. Sync service and indicator computation
5. API endpoints
6. Frontend layout and components
7. Search, filters, favorites, watchlist, and reorder
8. Sync status and sync logs UI
9. Testing
10. Documentation and final validation

## Final Output Expectation

When implementation is complete, provide:

- summary of what was built
- summary of any remaining gaps
- how to run backend
- how to run frontend
- how to initialize the database
- how to import or seed stock data
- how to trigger sync
- how to run tests

## Short Execution Prompt

If you need a short prompt for another agent, use this:

"Read `requirements.md` as the build contract and use `TRACKER.md` as the execution tracker. Build the app end to end in this repository, keep the tracker updated, validate work as you go, and continue until the project is runnable locally with tests and documentation unless genuinely blocked."