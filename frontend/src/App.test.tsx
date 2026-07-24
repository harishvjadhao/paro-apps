import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import App from "./App";

function buildDetail(
  symbol: string,
  overrides: Partial<ReturnType<typeof buildDetailBase>> = {},
) {
  return {
    ...buildDetailBase(symbol),
    ...overrides,
  };
}

function buildDetailBase(symbol: string) {
  const isAbb = symbol === "ABB";
  return {
    symbol,
    companyName: isAbb ? "ABB India" : "Tata Consultancy Services",
    industry: isAbb ? "Capital Goods" : "IT",
    closePrice: isAbb ? 297.56 : 4120.1,
    movingAverage44: isAbb ? 295.31 : 4050.4,
    isAbove44MA: true,
    percentAbove44MA: isAbb ? 0.76 : 1.72,
    isFavorite: symbol === "TCS",
    inWatchlist: false,
    manualRank: isAbb ? 2 : 1,
    series: "EQ",
    isinCode: "INE000000000",
    yahooTicker: `${symbol}.NS`,
    lastUpdatedAt: "2026-07-22T15:34:20.123855",
    lastSyncStatus: isAbb ? "failed" : "success",
    lastSyncAt: "2026-07-22T15:34:20.123855",
    lastSyncMessage: isAbb ? "No market data returned" : null,
    canRetrySync: isAbb,
  };
}

vi.mock("./lib/api", () => ({
  fetchStocks: vi.fn().mockResolvedValue({
    total: 2,
    items: [
      {
        symbol: "ABB",
        companyName: "ABB India",
        industry: "Capital Goods",
        closePrice: 297.56,
        movingAverage44: 295.31,
        isAbove44MA: true,
        percentAbove44MA: 0.76,
        isFavorite: false,
        inWatchlist: false,
        manualRank: 2,
        lastSyncStatus: "failed",
        lastSyncAt: "2026-07-22T15:34:20.123855",
        lastSyncMessage: "No market data returned",
        canRetrySync: true,
      },
      {
        symbol: "TCS",
        companyName: "Tata Consultancy Services",
        industry: "IT",
        closePrice: 4120.1,
        movingAverage44: 4050.4,
        isAbove44MA: true,
        percentAbove44MA: 1.72,
        isFavorite: true,
        inWatchlist: false,
        manualRank: 1,
        lastSyncStatus: "success",
        lastSyncAt: "2026-07-22T15:34:20.123855",
        lastSyncMessage: null,
        canRetrySync: false,
      },
    ],
  }),
  fetchStock: vi
    .fn()
    .mockImplementation(async (symbol: string) => buildDetail(symbol)),
  fetchChartHighlightDates: vi.fn().mockResolvedValue({ items: [] }),
  fetchSyncStatus: vi.fn().mockResolvedValue({
    status: "success",
    lastSuccessfulSyncAt: "2026-07-22T15:34:20.123855",
    lastSyncStartedAt: "2026-07-22T15:34:20.123855",
    stocksProcessed: 200,
    stocksUpdated: 200,
    errorMessage: null,
    mode: "incremental",
    failedStocks: 1,
  }),
  fetchSyncLogs: vi.fn().mockResolvedValue({
    items: [
      {
        id: 1,
        startedAt: "2026-07-22T15:34:20.123855",
        finishedAt: "2026-07-22T15:35:20.123855",
        status: "success",
        stocksProcessed: 200,
        stocksUpdated: 200,
        errorMessage: null,
        source: "bootstrap",
        mode: "full",
        failedStocks: 1,
      },
    ],
  }),
  fetchSyncLogDetail: vi.fn().mockResolvedValue({
    id: 1,
    startedAt: "2026-07-22T15:34:20.123855",
    finishedAt: "2026-07-22T15:35:20.123855",
    status: "partial",
    stocksProcessed: 200,
    stocksUpdated: 199,
    failedStocks: 1,
    errorMessage: "blocked",
    source: "bootstrap",
    mode: "full",
    items: [
      {
        id: 11,
        stockId: 1,
        symbol: "ABB",
        syncMode: "full",
        status: "failed",
        message: "No market data returned",
        rangeStart: "2026-07-01",
        rangeEnd: "2026-07-22",
        startedAt: "2026-07-22T15:34:20.123855",
        finishedAt: "2026-07-22T15:35:20.123855",
        rowsWritten: 0,
      },
    ],
  }),
  triggerSync: vi
    .fn()
    .mockResolvedValue({
      status: "partial",
      stocksProcessed: 200,
      stocksUpdated: 0,
      errorMessage: "blocked",
      mode: "incremental",
      failedStocks: 1,
    }),
  setFavorite: vi
    .fn()
    .mockImplementation(async (symbol: string, value: boolean) =>
      buildDetail(symbol, { isFavorite: value }),
    ),
  setWatchlist: vi
    .fn()
    .mockImplementation(async (symbol: string, value: boolean) =>
      buildDetail(symbol, { inWatchlist: value }),
    ),
  reorderStocks: vi.fn().mockResolvedValue({ total: 2, items: [] }),
  fetchStockComments: vi.fn().mockResolvedValue({ items: [] }),
  fetchStockTimeline: vi.fn().mockResolvedValue({ items: [] }),
  createStockComment: vi.fn(),
  updateStockComment: vi.fn(),
  deleteStockComment: vi.fn(),
  createChartHighlightDate: vi.fn(),
  deleteChartHighlightDate: vi.fn(),
}));

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

test("renders stocks, filters by search, and updates selected detail", async () => {
  renderApp();

  await screen.findByText("ABB India");
  expect(screen.getByText("Tata Consultancy Services")).toBeInTheDocument();
  expect(screen.getByText("Selected Stock")).toBeInTheDocument();
  expect(screen.getByText("Last Sync")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Sync ABB/i })).toBeInTheDocument();

  const search = screen.getByPlaceholderText(
    "Search symbol, company, or industry",
  );
  await userEvent.type(search, "TCS");

  await waitFor(() => {
    expect(
      screen.queryByRole("button", { name: /ABB India/i }),
    ).not.toBeInTheDocument();
  });

  await userEvent.click(screen.getByText("TCS"));

  await waitFor(() => {
    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Tata Consultancy Services",
      }),
    ).toBeInTheDocument();
  });
});

test("shows admin sync controls and sync detail", async () => {
  renderApp();

  await screen.findByText("ABB India");
  await userEvent.click(screen.getAllByRole("button", { name: "Admin" })[0]);

  expect(await screen.findByText("Sync Control")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Full Sync" })).toBeInTheDocument();
  expect(screen.getByText("Run Detail")).toBeInTheDocument();
  expect(screen.getByText("No market data returned")).toBeInTheDocument();
});
