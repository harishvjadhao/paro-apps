# PaRo Wireframe Prompt

Create a professional mid-fidelity wireframe for a desktop-first stock analysis web app called PaRo. The product is a Nifty 200 stock review workspace with a compact vertical navigation rail, a left stock discovery sidebar, and a right main analysis panel. The app supports industry-grouped stock browsing, search, quick filters, favorite and watchlist toggles, per-industry stock reordering, selected stock analysis, candlestick timeline with 44-day moving average overlay, comment-taking, sync controls, sync status, sync logs, and chart highlight date management.

The stock workspace must only display stocks that belong to the currently uploaded stock universe managed from Admin, for example an uploaded Nifty 200 stock list.

## Screens To Design

1. Main desktop stock workspace screen.
2. Separate Admin screen.
3. Empty state with no stock selected.
4. No search results state.
5. Sync running state.
6. Sync partial failure state.
7. Mobile responsive stacked layout.

## Layout And Structure

Design a desktop-first application shell with:

1. A full-height app canvas.
2. A compact vertical navigation rail on the far left with a soft rounded container, icon-first navigation, strong active-state highlight, generous vertical spacing, and a settings action anchored near the bottom.
3. A left sidebar for stock discovery and prioritization.
4. A right main analysis panel for the selected stock.
5. Card-based sections with rounded containers.
6. A vertically scrollable stock list.
7. A separate Admin section accessible from the navigation rail instead of a third panel.
8. Mobile adaptation that stacks sections in the order: navigation, controls, stock list, stock detail, comments, admin.

## Navigation Rail

Include a slim vertical icon-based navigation rail with a premium utility-sidebar feel.

Include these components:

1. Brand mark or app icon at the top.
2. Primary navigation icons for market workspace, signals or filters, watchlist or stock list, research, and admin.
3. A clear active-state treatment for the selected section.
4. A settings icon anchored near the bottom.
5. Minimal labels or tooltip behavior if needed, but keep the rail compact and mostly icon-driven.

## Left Sidebar

Include these components:

1. App title: PaRo.
2. Collapse all / Expand all control.
3. Quick sync button.
5. Search input with placeholder: Search symbol, company, or industry.
6. Filter chips: All, 44 MA, Favorites, Watchlist.
7. Industry groups ranked by percentage above 44 MA.
8. Group headers with:
   - Industry name
   - Count above 44 MA
   - Total stock count
   - Percentage above 44 MA
9. Stock rows with:
   - Symbol
   - Company name
   - Last sync timestamp
   - Above/Below 44 MA badge
   - Sync status chip
   - Percent above MA
   - MA44 value
   - Favorite toggle
   - Watchlist toggle
   - External chart button
   - Optional Sync This Stock button
   - Move up control
   - Move down control
10. A clearly highlighted selected stock row.
11. Empty state for no matching results.

## Main Analysis Panel

Include these sections:

1. Selected Stock header:
   - Selected Stock label
   - Company name
   - Symbol and industry
   - Signal card with Above 44 MA or Below 44 MA
2. Price Timeline section:
   - Section title: Price Timeline
   - Badge: 44 Candles
   - Top stat strip with Date, Open, High, Low, Close, 44 MA
   - Candlestick chart wireframe
   - 44-day moving average overlay line
   - Highlighted candles for note dates and global chart highlight dates
   - Hover or focus state on the active candle
3. Metric cards:
   - Close Price
   - 44 Day MA
   - % Above MA
4. Metadata cards:
   - Identifiers card with Yahoo, Series, ISIN
   - Data Freshness card with Updated, Sync Status, Favorite, Watchlist
5. Comments section:
   - Add comment textarea
   - Add comment button
   - Comments list with:
     - Created timestamp
     - Updated timestamp
     - Comment body
     - Edit action
     - Delete action
   - Edit mode with Cancel and Save actions
   - Empty, loading, and error states

## Separate Admin Section

Design Admin as its own dedicated screen or workspace, accessed from the navigation rail rather than embedded beside the stock detail panel.

Include these cards:

1. Stock Universe Upload card:
   - Upload stock list file action for CSV or spreadsheet import
   - Clear title explaining this controls which stocks appear in the main stock workspace
   - Helper text such as upload Nifty 200 stock list to define the active watchlist universe
   - File requirements summary showing expected fields such as company name, symbol, industry, series, and ISIN
   - Replace existing list action with confirmation state
   - Upload progress, success, validation, and failure states
   - Summary after upload showing total stocks imported, duplicates skipped, invalid rows, and last uploaded timestamp
   - Optional preview table of the first few imported stocks

2. Sync Control card:
   - Full Sync button
   - Incremental Sync or Last Sync button
   - Status chip
   - Mode
   - Stocks processed
   - Stocks updated
   - Failed stocks
   - Started timestamp
   - Last successful timestamp
   - Error message area
3. Theme card:
   - Default option
   - Sky Blue option
   - Selected theme state
4. Chart Highlights card:
   - Date picker
   - Label input for each highlight date, such as results day, breakout, review, or event
   - Color preview or color token associated with the chosen label
   - Add date button
   - List of highlight dates
   - Each highlight row shows date, label, and assigned highlight color
   - Dates with the same label must share the same color across the app
   - New labels should automatically receive a distinct color, while repeated labels reuse the existing color
   - Delete action
   - Empty state
5. Sync Status summary card:
   - Large current status
   - Mode
   - Last started
   - Last success
   - Processed count
   - Updated count
   - Failed or partial count
   - Quick sync action button
   - Error message region
6. Recent Sync Logs card:
   - List of recent sync runs
   - Each item shows status chip, mode, start timestamp, processed, updated, failed, and optional error
   - Selected log item highlighted
7. Run Detail panel:
   - Per-stock sync results
   - Symbol
   - Status chip
   - Rows written
   - Date window range
   - Item-level message or error
   - Empty, loading, and error states

## Interaction Requirements

Reflect these behaviors in the wireframe:

1. Selecting a stock updates the analysis panel and comments context.
2. Search and filters update results immediately.
3. Favorites and Watchlist filters show subsets.
4. 44 MA filter shows only stocks above 44 MA.
5. Reordering is within the same industry group only.
6. Favorite and watchlist controls have clear active and inactive states.
7. Full sync, incremental sync, and single-stock sync states should be represented.
8. Sync running disables conflicting actions.
9. Comments support add, edit, and delete flows inside the main panel.
10. Global chart highlight dates and comment dates both influence chart annotations.
11. Uploading a new stock universe from Admin changes which stocks are available in the main sidebar and watchlist workspace.
12. Only stocks from the active uploaded universe, such as the uploaded Nifty 200 list, can appear in the stock list and be synced.
13. Chart highlight dates can be grouped by label, and all dates with the same label must render with the same highlight color in charts and admin lists.

## State Coverage

Show these states explicitly where relevant:

1. Default loaded desktop stock workspace state.
2. Separate Admin screen active.
3. No stock selected.
4. Stock list loading.
5. Stock detail loading.
6. Chart loading.
7. Comments loading.
8. Sync detail loading.
9. Search returns no results.
10. No comments.
11. No chart data.
12. No highlight dates.
13. No sync logs.
14. Sync running.
15. Sync partial failure.
16. Sync failed.
17. Add comment disabled without a selected stock.
18. Add chart highlight disabled without a chosen date.
19. Edit comment mode.
20. Selected sync log with populated run detail.
21. Stock universe upload success state.
22. Stock universe upload validation error state.
23. Empty admin state before any stock universe is uploaded.

## Visual Direction

The wireframe should feel:

1. Analytical.
2. Premium.
3. Calm.
4. Dense without clutter.
5. Strongly hierarchical for fast scanning.

Use:

1. Rounded card containers.
2. Clear segmentation between list scanning and detailed analysis.
3. Compact but legible controls.
4. Serious typography.
5. Professional spacing.
6. Status chips and compact metric cards.

Avoid:

1. Generic admin-dashboard aesthetics.
2. Marketing hero sections.
3. Flashy trading UI motifs.
4. Dark-only assumptions.
5. Oversized decorative chart treatments.

## Fidelity Guidance

Generate mid-fidelity wireframes, not low-fidelity placeholder boxes and not polished final mockups. The output should clearly show:

1. Layout structure.
2. Component hierarchy.
3. Labels.
4. Key metrics.
5. Important actions.
6. Status indicators.
7. Empty, loading, and error states.
8. Interaction annotations where useful.
