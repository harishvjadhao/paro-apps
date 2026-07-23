# Nifty 200 Stock List Viewer - Requirements Draft

## 1. Objective

Build a ReactJS web application that displays stocks from the Nifty 200 index in a left-side panel and shows selected stock details in a right-side content area. The application must support ranking, grouping, and manual reordering of stocks based on defined technical criteria.

## 2. Primary Use Case

A user wants to browse Nifty 200 stocks, quickly identify stocks that match a screening condition such as `close price > 44-day moving average`, view stock-specific details, and reorder stocks in the list for review or prioritization.

## 3. Functional Requirements

### 3.1 Stock Universe

- The application must load and display stocks from the Nifty 200 universe.
- Each stock record should include at least:
  - Stock name
  - Symbol
  - Industry
  - Last close price
  - 44-day moving average
  - Screening status for `close > 44 MA`
- The system should be designed so additional stock fields can be added later.

### 3.2 Layout

- The UI must have a two-panel layout:
  - Left panel: stock list and grouping view
  - Right panel: selected stock details
- The layout must be responsive and usable on desktop and laptop screen sizes.
- The left panel should remain scrollable when the stock list is long.

### 3.3 Left Panel Stock List

- The left panel must display the list of Nifty 200 stocks.
- Stocks in the left panel must be grouped by industry.
- Each industry group should show a collapsible or clearly separated section.
- Each stock item should display summary information such as symbol, stock name, and screening indicator.
- The left panel should visually highlight the currently selected stock.

### 3.4 Selection Behavior

- When a user clicks a stock in the left panel, the application must display that stock's information in the right panel.
- Only one stock should be selected at a time.
- The selected stock state should remain visible until another stock is selected.

### 3.5 Right Panel Details

- The right panel must show details for the selected stock.
- The details view should include at minimum:
  - Stock name
  - Symbol
  - Industry
  - Last close price
  - 44-day moving average
  - Result of the condition `close > 44 MA`
- The design should allow future addition of more metrics such as volume, RSI, market cap, or trend signals.

### 3.6 Sorting and Ranking

- Stocks that satisfy `close price > 44-day moving average` should be ranked higher in the list.
- The application should place matching stocks at the top based on the active ranking criteria.
- Within each industry group, stocks should be sortable according to the selected criteria.
- Industry groups themselves should be ranked by strength using the percentage of stocks above 44 MA.
- If no custom ranking is applied, the default ranking should prioritize:
  1. Stocks where `close > 44 MA`
  2. Then alphabetical order by stock name

### 3.7 Manual Reordering

- The user must be able to move a stock up or down in the list.
- Reordering may be supported by buttons, drag-and-drop, or keyboard controls.
- Manual reordering should be constrained clearly:
  - Either within the same industry group only, or
  - Across the full list if the product owner prefers a global ranking model
- The final product requirement should explicitly choose one of the above behaviors.
- The UI must immediately reflect the updated order after a move action.

### 3.8 Grouping by Industry

- Stocks must be grouped by industry in the left panel.
- Each group should show the industry name and the number of stocks in that group.
- Each industry group header should also show:
  - Count of stocks where `close > 44 MA`
  - Total number of stocks in the industry group
  - Percentage of stocks in that industry where `close > 44 MA`
- The application should maintain grouping even when ranking criteria are applied.
- By default, industries should be ordered by highest percentage of stocks where `close > 44 MA`.
- If two industries have the same percentage, the secondary sort should be the higher count of stocks above 44 MA.
- If both percentage and count are equal, the tertiary sort should be alphabetical by industry name.
- The ordering of industries should remain configurable for future versions.

### 3.9 Search and Filter

- The user must be able to search stocks by stock name or symbol.
- The user must be able to filter stocks by industry.
- The user must be able to filter stocks based on screening status such as `close > 44 MA`.
- Search and filter should update the left panel results immediately.
- Search and filter should work together with grouping, ranking, and manual reordering.

### 3.10 Watchlist and Favorites

- The user must be able to mark a stock as favorite.
- The user must be able to add or remove a stock from a watchlist.
- The user must be able to switch between viewing all stocks and only watchlist or favorite stocks.
- Favorite and watchlist state should persist locally in the initial version.
- Favorite or watchlist stocks should be visually distinguished in the stock list.

## 4. Data Requirements

- The application needs a data source for Nifty 200 stock metadata and computed indicators.
- The preferred production data source should be a backend API implemented in Python.
- The frontend React application should fetch stock data from the backend API rather than embedding the full stock universe directly in the UI code.
- During early development, the backend may serve mock or static JSON until live market integration is ready.
- Initial implementation may use mock JSON data.
- The structure should support future integration with an API or database.
- The data model should support precomputed fields such as:
  - `closePrice`
  - `movingAverage44`
  - `isAbove44MA`
  - `industry`
  - `manualRank`

### 4.1 Backend API Requirements

- The system should provide a Python-based backend API for fetching and preparing Nifty 200 stock data.
- The backend may be implemented using FastAPI, Flask, or a similar Python web framework.
- The backend API should be responsible for:
  - Providing the Nifty 200 stock list
  - Returning stock metadata such as symbol, company name, and industry
  - Returning computed indicators such as 44-day moving average and `close > 44 MA`
  - Supporting sorting and grouping fields required by the frontend
- The backend should expose an endpoint to fetch the stock list for the left panel.
- The backend should expose an endpoint to fetch details for a selected stock if the product chooses detail-on-demand loading.
- The API response format should be stable and documented so the React frontend can consume it reliably.

### 4.2 External Market Data Source

- The Python backend should be designed to fetch stock data from one or more external market data sources.
- The file `ind_nifty200list.csv` provided in the project should be treated as the source-of-truth master list for the Nifty 200 universe in version 1.
- The backend should load stock universe metadata from `ind_nifty200list.csv` rather than discovering the constituent list dynamically from an external provider.
- The CSV columns `Company Name`, `Industry`, `Symbol`, `Series`, and `ISIN Code` should be imported into the backend master stock dataset.
- Version 1 may use the Python `yfinance` package as the primary data retrieval source for historical stock prices.
- The backend should use Yahoo Finance style NSE ticker symbols where required, such as `RELIANCE.NS`.
- The backend should maintain a ticker mapping between application stock symbols and provider-specific ticker symbols.
- The exact provider can be finalized later, but the architecture should allow integration with sources such as:
  - `yfinance` for prototype and local-first implementation
  - NSE-approved or licensed market data provider
  - Broker API
  - Internal CSV or database import pipeline
- If live market data is not available initially, the backend should support loading stock data from static files for development and testing.
- The final implementation must clearly define how end-of-day close price and 44-day moving average are calculated and refreshed.

### 4.2.1 Python Data Retrieval Packages

- The backend should use the following Python packages in version 1:
  - `fastapi` for backend API
  - `uvicorn` for running the API server locally
  - `sqlalchemy` for SQLite database interaction
  - `pydantic` for request and response validation
  - `yfinance` for historical stock data retrieval
  - `pandas` for indicator calculation and data transformation
  - `python-dotenv` for environment-based configuration
- If future scheduled sync is added, `apscheduler` may be included later.

### 4.2.2 Nifty 200 Master List Import Requirements

- The backend must read the Nifty 200 constituent list from `ind_nifty200list.csv` during initialization or seed flow.
- The CSV file should be stored in the repository and version-controlled.
- The CSV should be the canonical source for:
  - Company name
  - Industry
  - NSE symbol
  - Series
  - ISIN code
- The backend should map each NSE symbol to a Yahoo Finance symbol for price retrieval, typically by appending `.NS` where applicable.
- If a symbol requires custom mapping, the backend should support an override mapping table or configuration file.
- The backend should ignore or log duplicate symbol rows if encountered during import.
- The import process should be idempotent so repeated seed runs do not create duplicate stock master records.

### 4.3 Refresh and Update Behavior

- The requirements should define how often stock data is refreshed.
- For the initial version, end-of-day refresh is acceptable.
- The UI must provide a `Sync` button that allows the user to trigger a daily stock data refresh on demand.
- The `Sync` button should call the Python backend API to fetch the latest stock data and recompute indicators.
- The backend should update the stored stock data when sync is triggered.
- The UI should show sync status such as `idle`, `sync in progress`, `sync completed`, or `sync failed`.
- The UI should show the last successful sync timestamp.
- The system should prevent duplicate sync execution if a sync is already in progress.
- The system may restrict sync to once per day in the initial version unless explicitly overridden for admin or testing purposes.
- The backend should be designed so refresh frequency can later be changed to intraday if needed.
- The UI should handle API loading, empty, and error states gracefully.

### 4.4 Local Database Requirements

- The application should store fetched stock data in a local database that is free and runs inside the project environment.
- The preferred initial database should be SQLite because it is free, file-based, lightweight, and works well with a Python backend.
- The database should be stored as a local project file so setup remains simple for development and personal use.
- The backend should manage schema creation and migrations.
- The database should store at minimum:
  - Stock master data such as symbol, company name, and industry
  - Daily price snapshot data required for close price tracking
  - Computed indicator values such as 44-day moving average and `isAbove44MA`
  - Manual ordering or ranking overrides if persistence is enabled
  - Sync audit fields such as last sync time and sync status
- The database design should allow future migration to PostgreSQL or another server database if the project grows.

### 4.5 Suggested Database Choice

- Recommended database for version 1: SQLite
- Reasoning:
  - Free and open source
  - No separate server installation required
  - Easy to keep local to the project
  - Well supported in Python with SQLAlchemy or built-in SQLite libraries
  - Suitable for a Nifty 200 stock tracking application with end-of-day sync volume
- If multi-user access, high concurrency, or hosted deployment becomes important later, PostgreSQL should be the next upgrade path.

### 4.6 Sync Logs and Audit Data

- The backend must store sync execution history in the local database.
- Each sync log entry should include at minimum:
  - Sync start time
  - Sync end time
  - Sync status
  - Number of stocks processed
  - Number of stocks updated
  - Error message if sync fails
- The system should store the last successful sync summary for display in the UI.
- The design should allow storing multiple historical sync runs for later review.

## 5. Non-Functional Requirements

- The application must be built using ReactJS.
- The UI should respond quickly when selecting or reordering stocks.
- The codebase should be modular, with separate components for:
  - Side panel
  - Industry group section
  - Stock list item
  - Stock detail panel
- State management should be simple and maintainable.
- The application should be easy to extend with more screening criteria.

## 6. Suggested UI Behavior

- Left panel header should contain:
  - Title such as `Nifty 200 Stocks`
  - Active sort criteria
  - Search input
  - Filter controls
- A `Sync` button to trigger daily stock refresh from the backend
- A display showing the last sync time and current sync state
- A last sync summary section showing total stocks processed, updated, and sync result
- Stock items should show a badge or indicator for `Above 44 MA`.
- Stock items should support favorite or watchlist indicators.
- Industry group headers should display summary text in a format such as `IT (8/14, 57.1% above 44 MA)`.
- Right panel should show a clean summary card for the selected stock.
- Empty state should be shown in the right panel when no stock is selected.

## 7. Version 1 Product Decisions

The following decisions are fixed for version 1 implementation:

1. Version 1 will support manual reordering only within the same industry group.
2. Industry grouping will remain fixed in version 1, even when ranking changes within a group.
3. The right-side stock detail panel for version 1 will show stock name, symbol, industry, last close price, 44-day moving average, screening result for `close > 44 MA`, favorite state, and watchlist state.
4. Version 1 data will come from the Python backend API, backed by local sample or static dataset support, with architecture ready for future live API integration.
5. The reordered list will persist after page refresh using backend storage in SQLite.
6. Version 1 will focus on `close > 44 MA` as the primary screening criterion, with support for additional technical criteria planned later.
7. Sync may be manually triggered multiple times by the user, but duplicate sync execution must be blocked while a sync is already in progress.
## 7.1 Remaining Open Item

The following item is still open for future live-data integration:

1. Which external market data provider should the Python backend integrate with when moving beyond local sample or static dataset mode?

## 8. Recommended Additional Requirements

These are worth adding now so the product does not become underspecified:

### 8.1 Search and Filter

- Advanced filter combinations can be added later, such as multi-criteria technical screening.

### 8.2 Persistence

- Manual ordering should be saved in local storage or backend storage.
- Last selected stock should optionally be restored when the user revisits the app.

### 8.3 Multiple Ranking Criteria

- The application should support changing the ranking criteria in the future.
- Example criteria:
  - Close above 44 MA
  - Percentage above 44 MA
  - Volume breakout
  - 52-week high proximity

### 8.4 Visual Indicators

- Stocks matching the active criteria should be visually emphasized.
- Industries with more matching stocks should optionally show a count or highlight.

### 8.5 Accessibility

- The application should support keyboard navigation.
- The selected stock and reorder controls should be accessible through keyboard interaction.
- The UI should have clear contrast and semantic labels.

## 9. Suggested Acceptance Criteria

1. User can see Nifty 200 stocks in the left panel grouped by industry.
2. User can click any stock and see its details in the right panel.
3. Stocks where `close > 44 MA` appear higher than non-matching stocks by default.
4. User can move a stock up or down and see the order update immediately.
5. Industry grouping remains visible while browsing and reordering.
5.1 Each industry group shows the count of stocks above 44 MA, total stocks, and percentage above 44 MA.
5.2 Industry groups are ordered by highest percentage of stocks above 44 MA by default.
6. The application handles a full Nifty 200 dataset without UI lag in normal usage.
7. User can trigger stock data sync from the UI and see sync status and last successful sync time.
8. User can search by stock name or symbol and filter by industry or screening condition.
9. User can mark stocks as favorite, add them to a watchlist, and view watchlist-only or favorite-only entries.
10. User can see a last sync summary and historical sync logs.

## 10. Suggested Next Version Scope

For version 2, consider adding:

- Live market data integration
- Advanced technical filters
- Watchlist support
- Notes per stock
- Export of ranked stock list

## 11. Additional Feature Suggestions

The following features can make the product more useful after the initial version is stable.

### 11.1 Advanced Screening

- Support additional moving averages such as 20 DMA, 50 DMA, 100 DMA, and 200 DMA.
- Add filters for `close above all major moving averages`.
- Add price crossing alerts such as `today crossed above 44 MA`.
- Add volume-based conditions such as `volume above 10-day average volume`.
- Add momentum indicators such as RSI, MACD, and rate of change.
- Add breakout conditions such as `near 52-week high` or `new 20-day breakout`.

### 11.2 Industry and Sector Insights

- Show the count of stocks per industry that satisfy the active screening condition.
- Rank industries by number of qualifying stocks.
- Show strongest and weakest industries based on selected criteria.
- Allow collapsing and expanding all industries quickly.

### 11.3 Better Stock Detail View

- Show mini price history chart for the selected stock.
- Show historical trend of moving averages.
- Show change from previous close and percentage change.
- Show market cap, PE ratio, 52-week high, 52-week low, and average volume.
- Show a technical summary card such as bullish, neutral, or bearish.

### 11.4 Watchlist and Shortlist Features

- Allow user to mark stocks as favorites.
- Allow user to create custom watchlists.
- Allow user to pin selected stocks at the top regardless of screen result.
- Allow user to add notes or review comments for each stock.

### 11.5 Alerts and Notifications

- Notify user when a stock newly satisfies `close > 44 MA`.
- Notify user when a synced stock changes industry ranking significantly.
- Show a daily summary of newly qualifying stocks after sync.
- Support optional email or desktop notifications in a later version.

### 11.6 Historical Analysis

- Store daily snapshots and allow the user to see past values.
- Show whether the stock has been above 44 MA for consecutive days.
- Show trend persistence such as `3-day`, `5-day`, or `10-day` strength.
- Compare current metrics with previous sync history.

### 11.7 User Productivity Features

- Search by stock symbol, company name, or industry.
- Add multi-select filters to narrow the list quickly.
- Add quick actions such as `move to top`, `favorite`, or `hide`.
- Support keyboard shortcuts for list navigation and reordering.
- Add export to CSV or Excel.

### 11.8 Admin and Operational Features

- Show sync logs with success or failure details.
- Show how many stocks were updated during the last sync.
- Add retry option when sync fails.
- Add a data health panel for missing prices or incomplete indicators.
- Add configurable sync source settings for switching data providers later.

### 11.9 Performance and Scalability Enhancements

- Add list virtualization if richer stock cards make the side panel heavier.
- Cache stock detail responses in the backend.
- Support background precomputation of indicators after sync.
- Add pagination or lazy loading if the universe expands beyond Nifty 200.

### 11.10 Nice-to-Have UX Features

- Dark mode and light mode.
- Customizable default sort order.
- Resizable left and right panels.
- Compact and detailed list view modes.
- Color-coded indicators for bullish and bearish conditions.

## 12. Recommended Feature Priority

If the goal is to keep the first release focused, prioritize these next:

1. Search and filter by symbol, name, and industry
2. Sync logs and last sync summary
3. Watchlist or favorites
4. Mini chart in stock details
5. Additional technical criteria beyond 44 MA

## 13. Build-Ready Technical Specification

The following sections should be added so an AI agent can build the application end to end with minimal ambiguity.

### 13.1 Fixed Technical Stack

- Frontend framework: ReactJS with Vite
- Frontend language: TypeScript preferred
- Styling approach for version 1: Tailwind CSS
- Backend framework: FastAPI in Python
- ORM or database access layer: SQLAlchemy
- Database: SQLite stored locally inside the project
- Market data retrieval package for version 1: yfinance
- Data processing library: pandas
- HTTP client on frontend: Axios
- Frontend server-state library: `@tanstack/react-query`
- Frontend utility library for conditional styling: `clsx`
- Frontend icon library: `react-icons`
- Frontend testing stack: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`
- Tailwind support packages: `tailwindcss`, `postcss`, `autoprefixer`
- Charting library for future detail charts: Recharts or Chart.js, optional for version 1

### 13.1.1 Frontend UI Package List

- The frontend should include at minimum the following packages:
  - `react`
  - `react-dom`
  - `typescript`
  - `vite`
  - `axios`
  - `@tanstack/react-query`
  - `clsx`
  - `react-icons`
  - `tailwindcss`
  - `postcss`
  - `autoprefixer`
  - `vitest`
  - `@testing-library/react`
  - `@testing-library/jest-dom`
  - `@testing-library/user-event`

### 13.2 Project Structure Requirement

- The implementation should be split into two folders at the project root:
  - `frontend` for the React application
  - `backend` for the Python API
- The repository should include a root `README.md` with setup and run instructions.
- The repository should include an `.env.example` file for backend configuration.
- The repository should include scripts or commands for starting frontend and backend independently.

### 13.3 Backend API Contract

- The backend API should expose at minimum the following endpoints:
  - `GET /api/stocks` to return the stock list for the left panel
  - `GET /api/stocks/{symbol}` to return details for a selected stock
  - `POST /api/sync` to trigger stock data sync
  - `GET /api/sync/status` to return current sync state and last sync summary
  - `GET /api/sync/logs` to return historical sync logs
  - `POST /api/stocks/{symbol}/favorite` to mark or unmark favorite state
  - `POST /api/stocks/{symbol}/watchlist` to add or remove a stock from watchlist
  - `POST /api/stocks/reorder` to update manual stock order
- The API should return JSON responses only.
- All API responses should include success and error payload structures.
- The API should return clear HTTP status codes for success, validation failure, not found, and server errors.

### 13.4 API Response Format

- Every API response should follow a consistent structure.
- Suggested response format:
  - `success`: boolean
  - `data`: response payload
  - `message`: short human-readable message
  - `error`: error object or null
- List responses should include item counts where useful.
- Sync status response should include:
  - `status`
  - `lastSuccessfulSyncAt`
  - `lastSyncStartedAt`
  - `stocksProcessed`
  - `stocksUpdated`
  - `errorMessage`

### 13.4.1 API Example Payloads

- Example response for `GET /api/stocks`:

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "symbol": "INFY",
        "companyName": "Infosys Ltd.",
        "industry": "Information Technology",
        "closePrice": 1582.4,
        "movingAverage44": 1540.85,
        "isAbove44MA": true,
        "percentAbove44MA": 2.69,
        "isFavorite": true,
        "inWatchlist": true,
        "manualRank": 2
      }
    ],
    "total": 200
  },
  "message": "Stocks fetched successfully",
  "error": null
}
```

- Example response for `GET /api/stocks/{symbol}`:

```json
{
  "success": true,
  "data": {
    "symbol": "INFY",
    "companyName": "Infosys Ltd.",
    "industry": "Information Technology",
    "series": "EQ",
    "isinCode": "INE009A01021",
    "yahooTicker": "INFY.NS",
    "closePrice": 1582.4,
    "movingAverage44": 1540.85,
    "isAbove44MA": true,
    "percentAbove44MA": 2.69,
    "isFavorite": true,
    "inWatchlist": true,
    "lastUpdatedAt": "2026-07-22T18:30:00Z"
  },
  "message": "Stock details fetched successfully",
  "error": null
}
```

- Example response for `GET /api/sync/status`:

```json
{
  "success": true,
  "data": {
    "status": "success",
    "lastSuccessfulSyncAt": "2026-07-22T18:30:00Z",
    "lastSyncStartedAt": "2026-07-22T18:25:00Z",
    "stocksProcessed": 200,
    "stocksUpdated": 36,
    "errorMessage": null
  },
  "message": "Sync status fetched successfully",
  "error": null
}
```

### 13.4.2 Reorder API Payload Definition

- The `POST /api/stocks/reorder` endpoint should accept a simple version 1 payload.
- Recommended request body:

```json
{
  "symbol": "INFY",
  "industry": "Information Technology",
  "direction": "up"
}
```

- Allowed values for `direction` should be `up` or `down`.
- The backend should validate that the stock exists and belongs to the provided industry group.
- The backend should only reorder within the same industry group.

### 13.4.3 Favorite and Watchlist API Payloads

- The `POST /api/stocks/{symbol}/favorite` endpoint should accept:

```json
{
  "isFavorite": true
}
```

- The `POST /api/stocks/{symbol}/watchlist` endpoint should accept:

```json
{
  "inWatchlist": true
}
```

### 13.4.4 Stock Detail Response Shape

- The stock detail API response for version 1 should include at minimum:
  - `symbol`
  - `companyName`
  - `industry`
  - `series`
  - `isinCode`
  - `yahooTicker`
  - `closePrice`
  - `movingAverage44`
  - `isAbove44MA`
  - `percentAbove44MA`
  - `isFavorite`
  - `inWatchlist`
  - `lastUpdatedAt`

### 13.5 Database Schema Guidance

- The backend should define clear database tables.
- Minimum suggested tables:
  - `stocks`
  - `stock_price_history`
  - `stock_indicators`
  - `watchlist_entries`
  - `favorites`
  - `manual_rankings`
  - `sync_logs`
- The `stocks` table should include symbol, company name, industry, and active status.
- The `stocks` table should also include series, ISIN code, and Yahoo ticker mapping.
- The `stock_price_history` table should store date, close price, and optional volume.
- The `stock_indicators` table should store computed values such as movingAverage44 and isAbove44MA.
- The `manual_rankings` table should store the current user-defined order.
- The `sync_logs` table should store sync execution metadata and errors.

### 13.5.2 Recommended Version 1 Table Design

- For version 1, the database should use the following core tables:
  - `stocks`
  - `stock_price_history`
  - `stock_indicators`
  - `sync_logs`
- To keep the version 1 implementation simple for a local single-user app, `stocks` may also store:
  - favorite state
  - watchlist state
  - manual rank within industry
- If the implementation prefers stronger normalization, separate `favorites`, `watchlist_entries`, and `manual_rankings` tables may still be used.

### 13.5.3 Required Columns

- The `stocks` table should include at minimum:
  - `id`
  - `symbol`
  - `company_name`
  - `industry`
  - `series`
  - `isin_code`
  - `yahoo_ticker`
  - `is_active`
  - `is_favorite`
  - `in_watchlist`
  - `manual_rank`
  - `created_at`
  - `updated_at`
- The `stock_price_history` table should include at minimum:
  - `id`
  - `stock_id`
  - `trade_date`
  - `open_price`
  - `high_price`
  - `low_price`
  - `close_price`
  - `adj_close_price`
  - `volume`
  - `created_at`
- The `stock_indicators` table should include at minimum:
  - `id`
  - `stock_id`
  - `as_of_date`
  - `moving_average_44`
  - `is_above_44_ma`
  - `percent_above_44_ma`
  - `created_at`
  - `updated_at`
- The `sync_logs` table should include at minimum:
  - `id`
  - `started_at`
  - `finished_at`
  - `status`
  - `stocks_processed`
  - `stocks_updated`
  - `error_message`
  - `source`
  - `created_at`

### 13.5.4 Required Constraints and Indexes

- The `stocks.symbol` column should be unique.
- The `stocks.yahoo_ticker` column should be unique where possible.
- The `stock_price_history` table should enforce uniqueness on `stock_id + trade_date`.
- The `stock_indicators` table should enforce uniqueness on `stock_id + as_of_date`.
- The database should include indexes on:
  - `stocks.industry`
  - `stock_price_history.stock_id`
  - `stock_price_history.trade_date`
  - `stock_indicators.stock_id`
  - `sync_logs.started_at`

### 13.5.1 Seed and Import Flow

- The backend should include a seed or bootstrap step that imports `ind_nifty200list.csv` into the `stocks` table.
- The seed process should run automatically on first setup or be available through a documented command.
- The seed process should create or update stock master data without duplicating records.
- The application should be able to start even if price history is not yet available, as long as stock master data is present.

### 13.5.5 Required Backend Scripts

- The backend should include the following scripts or commands:
  - database initialization script
  - CSV seed or import script
  - stock sync script
  - optional reset or reseed script for local development
- The database initialization script should create all required SQLite tables.
- The CSV seed script should import `ind_nifty200list.csv`, generate Yahoo ticker mapping, and upsert stock master records.
- The stock sync script should:
  - load active stocks from the database
  - fetch daily historical data using `yfinance`
  - upsert rows into `stock_price_history`
  - calculate 44-day moving average using `pandas`
  - update `stock_indicators`
  - create a `sync_logs` entry for success or failure
- The backend API may call the same sync service used by the standalone sync script to avoid duplicated business logic.

### 13.6 Sorting and Reordering Rules

- The implementation must define the exact ordering algorithm.
- Recommended version 1 rule:
  1. Group by industry
  2. Order industries by descending percentage of stocks where `isAbove44MA = true`
  3. If tied, order industries by descending count of stocks where `isAbove44MA = true`
  4. If still tied, order industries alphabetically by industry name
  5. Within each industry, show favorite or watchlist pinning if enabled
  6. Then prioritize stocks where `isAbove44MA = true`
  7. Then apply manual rank if present
  8. Then apply alphabetical ordering by stock name
- Manual reorder should initially work only within the same industry group to reduce complexity.
- If a stock is moved up or down, the backend should persist the revised order.

### 13.7 Sync Behavior Rules

- Clicking the `Sync` button should trigger a backend job immediately.
- The backend should fetch the latest available stock data, update stored records, compute indicators, and save a sync log entry.
- In version 1, the backend should use `yfinance` to retrieve historical daily data for supported Nifty 200 symbols.
- The backend should use `pandas` to calculate 44-day moving average from the retrieved daily close prices.
- The frontend should poll sync status until the job completes or fails.
- If sync is already running, the backend should reject duplicate sync requests with a clear message.
- If live provider integration is unavailable, the backend should fall back to a local mock dataset.
- The calculation for 44-day moving average should use the latest 44 valid trading sessions available in stored price history.

### 13.7.1 Sync Status State Machine

- The sync status should use only the following values in version 1:
  - `idle`
  - `running`
  - `success`
  - `failed`
- `idle` means no sync has started yet or no sync is currently active.
- `running` means a sync is in progress.
- `success` means the most recent sync completed successfully.
- `failed` means the most recent sync ended with an error.

### 13.7.2 Yahoo Ticker Mapping Rule and Exception Format

- The default Yahoo ticker mapping rule should be: `Symbol + ".NS"`.
- The backend should support an exception mapping file for symbols that do not work correctly with the default rule.
- The recommended exception mapping format should be JSON.
- Example file: `backend/data/yahoo_ticker_overrides.json`
- Example content:

```json
{
  "M&M": "M&M.NS",
  "BAJAJ-AUTO": "BAJAJ-AUTO.NS",
  "UNITDSPR": "UNITDSPR.NS"
}
```

- During seed or sync, the backend should first check the override mapping file and then fall back to the default `.NS` rule.

### 13.8 Frontend Screen Definition

- The app should have a single main page for version 1.
- The app should be implemented as a single-route frontend in version 1.
- The default route should be `/`.
- Main page layout:
  - Left sidebar for grouped stock list
  - Top controls in sidebar for search, filters, and sync button
  - Right content panel for selected stock detail
  - Optional top status strip for sync summary
- The watchlist and favorite filters should be available in the sidebar controls.
- Each industry header should include a compact industry strength summary showing `above 44 MA count / total count` and percentage.
- Empty states, loading states, and error states should be explicitly implemented.

### 13.9 Component Breakdown

- Minimum frontend components should include:
  - `AppShell`
  - `SidebarPanel`
  - `DetailPanel`
  - `SidebarHeader`
  - `AppTitle`
  - `StockFilters`
  - `SearchInput`
  - `IndustryFilterDropdown`
  - `ScreeningFilterDropdown`
  - `ViewToggle`
  - `SyncButton`
  - `IndustryGroup`
  - `IndustryGroupHeader`
  - `IndustryStrengthSummary`
  - `IndustryCollapseToggle`
  - `StockList`
  - `StockListItem`
  - `FavoriteToggle`
  - `WatchlistToggle`
  - `MoveUpButton`
  - `MoveDownButton`
  - `StockDetailPanel`
  - `StockDetailHeader`
  - `StockIdentityCard`
  - `StockMetricGrid`
  - `MetricCard`
  - `StockActionBar`
  - `SyncStatusBanner`
  - `LastSyncSummary`
  - `SyncSummaryCard`
  - `SyncLogPanel`
  - `SyncLogList`
  - `SyncLogItem`
  - `LoadingState`
  - `EmptySelectionState`
  - `EmptyListState`
  - `ErrorState`
- Each component should have a clear prop interface.
- Shared types for stock models and sync models should be centralized.

### 13.9.1 UI Component Responsibilities

- `AppShell` should manage the main two-panel layout.
- `SidebarPanel` should contain discovery and control components.
- `SidebarHeader` should contain search, filters, view toggles, and sync action.
- `IndustryGroup` should render one industry section containing its stock rows.
- `IndustryGroupHeader` should show the industry name, total count, above-44-MA count, and percentage up.
- `StockListItem` should show stock identity, signal badge, favorite state, watchlist state, and reorder controls.
- `DetailPanel` should render the selected stock information area.
- `StockDetailPanel` should show all detail content for the selected stock.
- `StockMetricGrid` should display key metrics such as close price, 44 DMA, and status.
- `SyncStatusBanner` and `SyncSummaryCard` should show sync progress and last sync result.
- `SyncLogPanel` should render historical sync entries.
- State components should handle loading, empty, and error scenarios without breaking layout.

### 13.10 State Management Requirements

- Frontend state should separate server state from local UI state.
- Recommended approach:
  - Server state for stock data, sync status, and logs
  - UI state for selected stock, filters, expanded groups, and temporary interactions
- React Query should be used for API state management.
- If no external state library is used, the code should still isolate API calls from UI components.

### 13.11 Validation and Error Handling

- The backend must validate all request payloads.
- Invalid reorder requests, invalid symbols, and duplicate sync actions should return clear error messages.
- The frontend must display meaningful error messages for failed sync, failed fetch, and missing stock data.
- The app should not crash if one stock record has incomplete or missing fields.

### 13.12 Testing Requirements

- The repository should include automated tests.
- Minimum tests should include:
  - Backend unit tests for moving average calculation
  - Backend API tests for stock list, stock details, sync trigger, and sync log endpoints
  - Frontend component tests for list rendering and stock selection
  - Frontend interaction tests for search, filter, favorites, watchlist, and reorder behavior
- A small mock dataset should be included for deterministic tests.

### 13.13 Sample Data Requirement

- The project should include a local sample dataset for development.
- The attached `ind_nifty200list.csv` file should be used as the default stock universe dataset for version 1.
- The dataset should contain enough sample records across multiple industries to validate grouping and ranking behavior.
- The sample dataset should include at least 20 to 30 stocks for development, even if the final dataset uses all Nifty 200 stocks.
- The format of the sample data should match the backend import structure.

### 13.14 Configuration Requirements

- The backend should support configuration via environment variables.
- Minimum configuration items should include:
  - Database file path
  - External data source mode such as `mock` or `live`
  - Sync enable or disable flag
  - CORS origin for frontend development
- Default local development values should be documented.

### 13.15 Definition of Done

- The app can be started locally with documented steps.
- The backend creates the SQLite database automatically if it does not exist.
- The backend can import `ind_nifty200list.csv` successfully into the stock master table.
- The frontend can fetch stocks from the backend and render the grouped list.
- Stock selection, search, filter, favorites, watchlist, reorder, and sync all work locally.
- Sync logs and last sync summary are visible in the UI.
- The app includes basic automated tests and passes them locally.
- The README explains how to run, sync, and test the app.

## 14. AI Build Brief

This section is intended to be given directly to an AI coding agent so it can implement the application end to end with minimal guessing.

### 14.1 Build Objective

- Build a complete full-stack local application for browsing and ranking Nifty 200 stocks.
- The application must include a React frontend, a Python backend API, a local SQLite database, sample development data, and run instructions.
- The implementation must be usable locally without requiring paid services.

### 14.2 Must Build

- A React frontend using Vite
- A Python FastAPI backend
- A SQLite database stored locally in the project
- A grouped stock list in the left sidebar
- A stock detail panel on the right
- Search and filter controls
- Favorite and watchlist support
- Manual up or down stock reordering
- A `Sync` button in the UI
- Sync status, last sync summary, and sync logs
- API integration between frontend and backend
- Local sample dataset and seed flow
- Automated tests for core backend and frontend behaviors
- A root README with setup and run instructions

### 14.3 Do Not Build In Version 1

- Authentication or user login
- Multi-user support
- Cloud deployment setup
- Real-time streaming market data
- Complex alert delivery such as email or SMS
- Advanced chart dashboards beyond a simple detail view
- Broker integrations
- Mobile app version

### 14.4 Mandatory Technical Choices

- Use React with TypeScript for the frontend.
- Use Tailwind CSS for version 1 UI styling.
- Use FastAPI for the backend.
- Use SQLite as the local database.
- Use SQLAlchemy for database interaction.
- Use `yfinance` as the version 1 stock data retrieval package.
- Use `pandas` for moving average calculation and data preparation.
- Use `axios` for frontend API calls.
- Use `@tanstack/react-query` for frontend server-state management.
- Use `clsx` for conditional class name composition.
- Use `react-icons` for UI action and status icons.
- Use a mock or static dataset for initial development if live provider integration is not available.
- Keep the code modular and readable.

### 14.5 Required Deliverables

- `frontend` folder with the React application
- `backend` folder with the FastAPI application
- Database models and migration or initialization logic
- Seed or mock data files
- CSV import logic for `ind_nifty200list.csv`
- Backend scripts for database init, CSV seed, and sync execution
- API routes for stocks, sync, favorites, watchlist, reorder, and logs
- Reusable frontend components and typed models
- Basic test suite
- `README.md`
- `.env.example`

### 14.6 Required User Flows

- User opens the app and sees grouped stocks by industry.
- User searches stocks by symbol or name.
- User filters by industry or `close > 44 MA` condition.
- User selects a stock and sees its details.
- User marks or unmarks a stock as favorite.
- User adds or removes a stock from watchlist.
- User switches the list view to all, favorites, or watchlist.
- User moves a stock up or down within its industry group.
- User clicks `Sync` and sees progress, completion state, and last sync summary.
- User opens sync logs and reviews previous sync runs.

### 14.7 Required API Endpoints

- `GET /api/stocks`
- `GET /api/stocks/{symbol}`
- `POST /api/sync`
- `GET /api/sync/status`
- `GET /api/sync/logs`
- `POST /api/stocks/{symbol}/favorite`
- `POST /api/stocks/{symbol}/watchlist`
- `POST /api/stocks/reorder`

### 14.7.1 Required API Contract Deliverables

- The implementation should include typed request and response models for all API endpoints.
- The implementation should include example JSON payloads in the backend documentation or README.
- The reorder endpoint should follow the version 1 request payload defined in the technical specification.

### 14.8 Required Frontend Features

- Sidebar with grouped stocks by industry
- Industry headers showing `above 44 MA / total` and percentage up
- Highlighting for selected stock
- Search box and filter controls in sidebar header
- Favorite and watchlist indicators in each stock row
- Up and down reorder controls for each stock row
- Sync button and sync status banner
- Right-side stock detail panel
- Empty, loading, and error states
- Responsive desktop-first layout

### 14.9 Required Backend Features

- Import the stock universe from `ind_nifty200list.csv`
- Initialize the SQLite schema automatically or through a documented command
- Load initial sample stock data
- Persist stock metadata, price history, indicators, favorites, watchlist entries, manual order, and sync logs
- Compute 44-day moving average from stored price history
- Provide grouped or group-capable stock data to frontend
- Reject duplicate sync requests while sync is already running
- Record sync success and failure details
- Support mock sync behavior even before live market integration exists

### 14.10 Reordering Rule For Version 1

- Reordering must work only within the same industry group.
- The up and down action should update manual rank within that industry.
- The order should persist after refresh.
- Industry groups should be ordered by descending percentage of stocks above 44 MA.
- If no manual order exists, the list should default to:
  1. Stocks above 44 MA first
  2. Then alphabetical by stock name

### 14.11 Data Assumptions For Version 1

- Use `ind_nifty200list.csv` as the master list of Nifty 200 constituents for version 1.
- Use `yfinance` as the preferred version 1 source for historical daily price retrieval.
- Use a local sample dataset as fallback if `yfinance` data is unavailable or a symbol mapping is incomplete.
- The sample dataset should include multiple industries and enough records to validate grouping and ranking.
- Each stock should include enough historical price points to compute the 44-day moving average.
- Sync should retrieve or refresh daily history using `yfinance`, then recompute indicators and store them locally.

### 14.12 Error Handling Expectations

- The frontend must show useful messages when API calls fail.
- The backend must return structured validation and error responses.
- The app must continue working if one stock record is missing optional fields.
- Sync failures must be visible in both status view and sync logs.

### 14.13 Testing Expectations

- Add backend tests for moving average calculation, stock fetch, reorder, and sync behavior.
- Add frontend tests for rendering grouped stock list, stock selection, search and filter, favorite and watchlist toggles, and sync status display.
- Tests should run locally with documented commands.

### 14.14 Documentation Expectations

- The README must explain project structure.
- The README must explain how to install backend dependencies.
- The README must explain how to install frontend dependencies.
- The README must explain how to run frontend and backend locally.
- The README must explain how sync works in version 1.
- The README must explain how to run tests.

### 14.15 Build Constraints

- Keep the first implementation simple and local-first.
- Prefer clarity and maintainability over over-engineering.
- Avoid introducing services that require paid accounts.
- Avoid features not explicitly required for version 1.
- Ensure the app can be run by a developer on Windows with standard local tooling.

### 14.16 AI Agent Execution Instruction

- Read this entire file before implementation.
- Use the mandatory technical choices and required deliverables as fixed scope.
- If a requirement is ambiguous, prefer the simplest local-first implementation that satisfies the user flow.
- Do not skip tests, sample data, or documentation.
- Treat the app as complete only when frontend, backend, database initialization, sync flow, and core tests all work together locally.

## 15. Implementation Conventions

This section defines preferred implementation conventions so the AI agent does not need to guess operational details.

### 15.1 Backend Conventions

- Keep backend source code under `backend/app`.
- Use separate folders for `api`, `models`, `schemas`, `services`, and `db`.
- Keep database initialization logic in a dedicated module rather than mixing it into route files.
- Reuse a shared sync service from both API endpoints and standalone scripts.
- Store the SQLite file under `backend/data/app.db` by default.
- Store Yahoo ticker override mapping under `backend/data/yahoo_ticker_overrides.json`.

### 15.2 Frontend Conventions

- Keep frontend source code under `frontend/src`.
- Use folders for `components`, `pages`, `services`, `hooks`, `types`, and `utils`.
- Keep API request logic in a dedicated service layer.
- Keep React Query hooks separate from presentational UI components.
- Use a single page route for version 1 with the main screen mounted at `/`.

### 15.3 Script Conventions

- Provide documented commands for:
  - database initialization
  - CSV seed import
  - stock sync
  - frontend start
  - backend start
  - test execution
- Scripts may be implemented as Python entry points, CLI modules, or documented commands, but they must be reproducible from the README.

### 15.4 Sync Polling Conventions

- The frontend should poll sync status every 3 to 5 seconds while sync is running.
- Polling should stop immediately when sync reaches `success` or `failed` state.
- Polling should not continue in the background when no sync is active.

### 15.5 Documentation Conventions

- The README should include the following sections at minimum:
  - Project overview
  - Tech stack
  - Project structure
  - Backend setup
  - Frontend setup
  - Database initialization
  - CSV seed import
  - Sync process
  - Test commands
  - Notes on `yfinance` and ticker mapping

### 15.6 Testing Conventions

- Backend tests should live under `backend/tests`.
- Frontend tests should live under `frontend/src/tests` or `frontend/tests`.
- Tests should avoid live network dependency when possible by mocking `yfinance` and API responses.
- At least one test should verify industry ordering by percentage above 44 MA.