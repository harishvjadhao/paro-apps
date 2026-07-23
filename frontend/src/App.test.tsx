import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";

import App from "./App";


function buildDetail(symbol: string, overrides: Partial<ReturnType<typeof buildDetailBase>> = {}) {
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
      },
    ],
  }),
  fetchStock: vi.fn().mockImplementation(async (symbol: string) => buildDetail(symbol)),
  fetchSyncStatus: vi.fn().mockResolvedValue({
    status: "success",
    lastSuccessfulSyncAt: "2026-07-22T15:34:20.123855",
    lastSyncStartedAt: "2026-07-22T15:34:20.123855",
    stocksProcessed: 200,
    stocksUpdated: 200,
    errorMessage: null,
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
      },
    ],
  }),
  triggerSync: vi.fn().mockResolvedValue({ status: "partial", stocksProcessed: 200, stocksUpdated: 0, errorMessage: "blocked" }),
  setFavorite: vi.fn().mockImplementation(async (symbol: string, value: boolean) => buildDetail(symbol, { isFavorite: value })),
  setWatchlist: vi.fn().mockImplementation(async (symbol: string, value: boolean) => buildDetail(symbol, { inWatchlist: value })),
  reorderStocks: vi.fn().mockResolvedValue({ total: 2, items: [] }),
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

  const search = screen.getByPlaceholderText("Search symbol, company, or industry");
  await userEvent.type(search, "TCS");

  await waitFor(() => {
    expect(screen.queryByRole("button", { name: /ABB India/i })).not.toBeInTheDocument();
  });

  await userEvent.click(screen.getByText("TCS"));

  await waitFor(() => {
    expect(screen.getByRole("heading", { level: 2, name: "Tata Consultancy Services" })).toBeInTheDocument();
  });
});
