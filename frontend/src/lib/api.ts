import axios from "axios";

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
  error?: string | null;
}

export interface StockListItem {
  symbol: string;
  companyName: string;
  industry: string;
  closePrice: number | null;
  movingAverage44: number | null;
  isAbove44MA: boolean;
  percentAbove44MA: number | null;
  isFavorite: boolean;
  inWatchlist: boolean;
  manualRank: number | null;
  lastSyncStatus: string | null;
  lastSyncAt: string | null;
  lastSyncMessage: string | null;
  canRetrySync: boolean;
}

export interface StockListData {
  items: StockListItem[];
  total: number;
}

export interface StockDetailData extends StockListItem {
  series: string | null;
  isinCode: string | null;
  yahooTicker: string;
  lastUpdatedAt: string | null;
}

export interface StockCommentItem {
  id: number;
  comment: string;
  createdAt: string;
  updatedAt: string;
}

export interface StockCommentListData {
  items: StockCommentItem[];
}

export interface ChartHighlightDateItem {
  id: number;
  highlightDate: string;
  createdAt: string;
}

export interface ChartHighlightDateListData {
  items: ChartHighlightDateItem[];
}

export interface StockTimelineItem {
  tradeDate: string;
  openPrice: number | null;
  highPrice: number | null;
  lowPrice: number | null;
  closePrice: number;
  volume: number | null;
  movingAverage44: number | null;
}

export interface StockTimelineData {
  items: StockTimelineItem[];
}

export interface SyncStatusData {
  status: string;
  lastSuccessfulSyncAt: string | null;
  lastSyncStartedAt: string | null;
  stocksProcessed: number;
  stocksUpdated: number;
  errorMessage: string | null;
  mode: string | null;
  failedStocks: number;
}

export interface SyncLogItem {
  id: number;
  startedAt: string;
  finishedAt: string | null;
  status: string;
  stocksProcessed: number;
  stocksUpdated: number;
  errorMessage: string | null;
  source: string | null;
  mode: string | null;
  failedStocks: number;
}

export interface SyncLogListData {
  items: SyncLogItem[];
}

export interface SyncLogStockItem {
  id: number;
  stockId: number;
  symbol: string;
  syncMode: string;
  status: string;
  message: string | null;
  rangeStart: string | null;
  rangeEnd: string | null;
  startedAt: string;
  finishedAt: string | null;
  rowsWritten: number;
}

export interface SyncLogDetailData {
  id: number;
  startedAt: string;
  finishedAt: string | null;
  status: string;
  stocksProcessed: number;
  stocksUpdated: number;
  failedStocks: number;
  errorMessage: string | null;
  source: string | null;
  mode: string | null;
  items: SyncLogStockItem[];
}

export interface SyncTriggerRequest {
  mode: "full" | "incremental" | "single_stock";
  symbol?: string;
}

const client = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
});

export async function fetchStocks(): Promise<StockListData> {
  const response = await client.get<ApiResponse<StockListData>>("/stocks");
  return response.data.data;
}

export async function fetchStock(symbol: string): Promise<StockDetailData> {
  const response = await client.get<ApiResponse<StockDetailData>>(
    `/stocks/${symbol}`,
  );
  return response.data.data;
}

export async function fetchStockComments(
  symbol: string,
): Promise<StockCommentListData> {
  const response = await client.get<ApiResponse<StockCommentListData>>(
    `/stocks/${symbol}/comments`,
  );
  return response.data.data;
}

export async function fetchChartHighlightDates(): Promise<ChartHighlightDateListData> {
  const response = await client.get<ApiResponse<ChartHighlightDateListData>>(
    "/settings/chart-highlights",
  );
  return response.data.data;
}

export async function createChartHighlightDate(
  highlightDate: string,
): Promise<ChartHighlightDateItem> {
  const response = await client.post<ApiResponse<ChartHighlightDateItem>>(
    "/settings/chart-highlights",
    { highlightDate },
  );
  return response.data.data;
}

export async function deleteChartHighlightDate(
  highlightId: number,
): Promise<{ deleted: boolean }> {
  const response = await client.delete<ApiResponse<{ deleted: boolean }>>(
    `/settings/chart-highlights/${highlightId}`,
  );
  return response.data.data;
}

export async function fetchStockTimeline(
  symbol: string,
): Promise<StockTimelineData> {
  const response = await client.get<ApiResponse<StockTimelineData>>(
    `/stocks/${symbol}/timeline`,
  );
  return response.data.data;
}

export async function fetchSyncStatus(): Promise<SyncStatusData> {
  const response =
    await client.get<ApiResponse<SyncStatusData>>("/sync/status");
  return response.data.data;
}

export async function fetchSyncLogs(): Promise<SyncLogListData> {
  const response = await client.get<ApiResponse<SyncLogListData>>("/sync/logs");
  return response.data.data;
}

export async function fetchSyncLogDetail(
  syncLogId: number,
): Promise<SyncLogDetailData> {
  const response = await client.get<ApiResponse<SyncLogDetailData>>(
    `/sync/logs/${syncLogId}`,
  );
  return response.data.data;
}

export async function triggerSync(
  payload: SyncTriggerRequest,
): Promise<SyncStatusData> {
  const response = await client.post<ApiResponse<SyncStatusData>>(
    "/sync",
    payload,
  );
  return response.data.data;
}

export async function setFavorite(
  symbol: string,
  value: boolean,
): Promise<StockDetailData> {
  const response = await client.post<ApiResponse<StockDetailData>>(
    `/stocks/${symbol}/favorite`,
    { value },
  );
  return response.data.data;
}

export async function setWatchlist(
  symbol: string,
  value: boolean,
): Promise<StockDetailData> {
  const response = await client.post<ApiResponse<StockDetailData>>(
    `/stocks/${symbol}/watchlist`,
    { value },
  );
  return response.data.data;
}

export async function reorderStocks(
  items: Array<{ symbol: string; manualRank: number }>,
): Promise<StockListData> {
  const response = await client.post<ApiResponse<StockListData>>(
    "/stocks/reorder",
    { items },
  );
  return response.data.data;
}

export async function createStockComment(
  symbol: string,
  comment: string,
): Promise<StockCommentItem> {
  const response = await client.post<ApiResponse<StockCommentItem>>(
    `/stocks/${symbol}/comments`,
    { comment },
  );
  return response.data.data;
}

export async function updateStockComment(
  symbol: string,
  commentId: number,
  comment: string,
): Promise<StockCommentItem> {
  const response = await client.put<ApiResponse<StockCommentItem>>(
    `/stocks/${symbol}/comments/${commentId}`,
    { comment },
  );
  return response.data.data;
}

export async function deleteStockComment(
  symbol: string,
  commentId: number,
): Promise<{ deleted: boolean }> {
  const response = await client.delete<ApiResponse<{ deleted: boolean }>>(
    `/stocks/${symbol}/comments/${commentId}`,
  );
  return response.data.data;
}
