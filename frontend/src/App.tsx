import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  FiActivity,
  FiArrowDown,
  FiArrowUp,
  FiChevronDown,
  FiChevronRight,
  FiExternalLink,
  FiRefreshCcw,
  FiSearch,
  FiStar,
  FiTrendingUp,
} from "react-icons/fi";
import { MdOutlinePlaylistAddCheck } from "react-icons/md";

import {
  ChartHighlightDateItem,
  createChartHighlightDate,
  createStockComment,
  deleteChartHighlightDate,
  deleteStockComment,
  fetchStock,
  fetchChartHighlightDates,
  fetchStockComments,
  fetchSyncLogDetail,
  fetchStockTimeline,
  fetchStocks,
  fetchSyncLogs,
  fetchSyncStatus,
  reorderStocks,
  setFavorite,
  setWatchlist,
  StockCommentItem,
  StockListItem,
  StockTimelineItem,
  SyncLogItem,
  triggerSync,
  updateStockComment,
} from "./lib/api";

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "--";
  }
  return value.toFixed(2);
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return new Date(value).toLocaleString();
}

function formatShortDate(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

function formatSyncMode(value: string | null | undefined): string {
  if (!value) {
    return "--";
  }
  if (value === "single_stock") {
    return "Single Stock";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function syncStatusTone(status: string | null | undefined): string {
  if (status === "success") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (status === "partial") {
    return "bg-amber-100 text-amber-800";
  }
  if (status === "failed") {
    return "bg-rose-100 text-rose-800";
  }
  if (status === "running") {
    return "bg-sky-100 text-sky-800";
  }
  return "bg-stone-200 text-stone-700";
}

function toLocalDateKey(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function withVisibleMovingAverage(
  items: StockTimelineItem[],
): StockTimelineItem[] {
  if (!items.length) {
    return items;
  }

  return items.map((item, index, collection) => {
    if (item.movingAverage44 !== null) {
      return item;
    }

    const startIndex = Math.max(0, index - 43);
    const windowItems = collection.slice(startIndex, index + 1);
    const validCloses = windowItems
      .map((windowItem) => windowItem.closePrice)
      .filter((value): value is number => Number.isFinite(value));

    if (!validCloses.length) {
      return item;
    }

    const average =
      validCloses.reduce((sum, value) => sum + value, 0) / validCloses.length;

    return {
      ...item,
      movingAverage44: average,
    };
  });
}

function buildCandlestickMarks(items: StockTimelineItem[]): Array<{
  key: string;
  x: number;
  wickTop: number;
  wickBottom: number;
  bodyTop: number;
  bodyHeight: number;
  bodyWidth: number;
  volumeTop: number;
  volumeHeight: number;
  movingAverageY: number | null;
  hasComment: boolean;
  color: string;
}> {
  if (!items.length) {
    return [];
  }

  const width = 720;
  const height = 240;
  const topPadding = 12;
  const bottomPadding = 24;
  const leftPadding = 8;
  const rightPadding = 8;
  const highs = items.map((item) => item.highPrice ?? item.closePrice);
  const lows = items.map((item) => item.lowPrice ?? item.closePrice);
  const movingAverages = items
    .map((item) => item.movingAverage44)
    .filter((value): value is number => value !== null);
  const maxVolume = Math.max(...items.map((item) => item.volume ?? 0), 1);
  const maxPrice = Math.max(...highs, ...movingAverages);
  const minPrice = Math.min(...lows, ...movingAverages);
  const range = Math.max(maxPrice - minPrice, 1);
  const plotWidth = width - leftPadding - rightPadding;
  const volumeSectionHeight = 42;
  const volumeBottomPadding = 12;
  const gapBetweenSections = 10;
  const pricePlotBottom =
    height - bottomPadding - volumeSectionHeight - gapBetweenSections;
  const plotHeight = pricePlotBottom - topPadding;
  const step = items.length > 1 ? plotWidth / (items.length - 1) : plotWidth;
  const bodyWidth = Math.max(Math.min(step * 0.58, 10), 3);
  const volumeBarWidth = Math.max(Math.min(step * 0.66, 12), 4);
  const volumeBaseY = height - volumeBottomPadding;

  const yForPrice = (price: number) =>
    topPadding + ((maxPrice - price) / range) * plotHeight;

  return items.map((item, index) => {
    const open = item.openPrice ?? item.closePrice;
    const close = item.closePrice;
    const high = item.highPrice ?? Math.max(open, close);
    const low = item.lowPrice ?? Math.min(open, close);
    const bodyTopPrice = Math.max(open, close);
    const bodyBottomPrice = Math.min(open, close);
    const bodyTop = yForPrice(bodyTopPrice);
    const bodyBottom = yForPrice(bodyBottomPrice);
    const color = close >= open ? "#0f766e" : "#b45309";
    const volumeHeight = Math.max(
      ((item.volume ?? 0) / maxVolume) * volumeSectionHeight,
      1.5,
    );

    return {
      key: `${item.tradeDate}-${index}`,
      x: leftPadding + index * step,
      wickTop: yForPrice(high),
      wickBottom: yForPrice(low),
      bodyTop,
      bodyHeight: Math.max(bodyBottom - bodyTop, 1.5),
      bodyWidth,
      volumeTop: volumeBaseY - volumeHeight,
      volumeHeight,
      movingAverageY:
        item.movingAverage44 === null ? null : yForPrice(item.movingAverage44),
      hasComment: false,
      color,
    };
  });
}

function openChartinkStock(symbol: string): void {
  const normalizedSymbol = symbol.trim().toLowerCase();
  window.open(
    `https://chartink.com/stocks/${normalizedSymbol}.html`,
    "_blank",
    "noopener,noreferrer",
  );
}

const themeOptions = {
  default: {
    label: "Default",
    appShell:
      "min-h-screen bg-[radial-gradient(circle_at_top,#f5ebd9_0%,#efe6d4_32%,#e9dfd0_100%)] text-slate-900",
    panelBorder: "border-amber-950/10",
    panelShadow: "shadow-[0_14px_44px_rgba(64,39,12,0.10)]",
    mainPanelShadow: "shadow-[0_16px_52px_rgba(64,39,12,0.10)]",
    signalCard: "bg-amber-100 text-amber-900",
    adminThemeButtonActive: "border-stone-900 bg-stone-900 text-white",
    adminThemeButtonInactive:
      "border-stone-200 bg-white text-stone-600 hover:border-amber-300 hover:bg-amber-50",
  },
  sky: {
    label: "Sky Blue",
    appShell:
      "min-h-screen bg-[radial-gradient(circle_at_top,#e0f2fe_0%,#dbeafe_30%,#e0f7ff_100%)] text-slate-900",
    panelBorder: "border-sky-950/10",
    panelShadow: "shadow-[0_14px_44px_rgba(14,116,144,0.12)]",
    mainPanelShadow: "shadow-[0_16px_52px_rgba(14,116,144,0.12)]",
    signalCard: "bg-sky-100 text-sky-900",
    adminThemeButtonActive: "border-sky-700 bg-sky-700 text-white",
    adminThemeButtonInactive:
      "border-sky-200 bg-white text-sky-700 hover:border-sky-300 hover:bg-sky-50",
  },
} as const;

type ThemeName = keyof typeof themeOptions;

export default function App() {
  const queryClient = useQueryClient();
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<
    "all" | "above" | "favorites" | "watchlist"
  >("all");
  const [collapsedIndustries, setCollapsedIndustries] = useState<
    Record<string, boolean>
  >({});
  const [newComment, setNewComment] = useState("");
  const [newHighlightDate, setNewHighlightDate] = useState("");
  const [editingCommentId, setEditingCommentId] = useState<number | null>(null);
  const [editingCommentValue, setEditingCommentValue] = useState("");
  const [hoveredTimelineIndex, setHoveredTimelineIndex] = useState<
    number | null
  >(null);
  const [rightPanelView, setRightPanelView] = useState<"notes" | "admin">(
    "notes",
  );
  const [themeName, setThemeName] = useState<ThemeName>("default");
  const [selectedSyncLogId, setSelectedSyncLogId] = useState<number | null>(
    null,
  );

  const activeTheme = themeOptions[themeName];

  const stocksQuery = useQuery({
    queryKey: ["stocks"],
    queryFn: fetchStocks,
  });

  const syncStatusQuery = useQuery({
    queryKey: ["sync-status"],
    queryFn: fetchSyncStatus,
    refetchInterval: 30000,
  });

  const syncLogsQuery = useQuery({
    queryKey: ["sync-logs"],
    queryFn: fetchSyncLogs,
  });

  const syncLogDetailQuery = useQuery({
    queryKey: ["sync-log-detail", selectedSyncLogId],
    queryFn: () => fetchSyncLogDetail(selectedSyncLogId!),
    enabled: selectedSyncLogId !== null,
  });

  const chartHighlightDatesQuery = useQuery({
    queryKey: ["chart-highlight-dates"],
    queryFn: fetchChartHighlightDates,
  });

  useEffect(() => {
    if (selectedSymbol || !stocksQuery.data?.items.length) {
      return;
    }

    let isCancelled = false;

    async function chooseInitialStock(): Promise<void> {
      const items = stocksQuery.data?.items ?? [];

      for (const item of items) {
        try {
          const comments = await fetchStockComments(item.symbol);
          if (!isCancelled && comments.items.length > 0) {
            setSelectedSymbol(item.symbol);
            return;
          }
        } catch {
          break;
        }
      }

      if (!isCancelled) {
        setSelectedSymbol(items[0].symbol);
      }
    }

    void chooseInitialStock();

    return () => {
      isCancelled = true;
    };
  }, [selectedSymbol, stocksQuery.data]);

  const stockDetailQuery = useQuery({
    queryKey: ["stock", selectedSymbol],
    queryFn: () => fetchStock(selectedSymbol!),
    enabled: Boolean(selectedSymbol),
  });

  const stockCommentsQuery = useQuery({
    queryKey: ["stock-comments", selectedSymbol],
    queryFn: () => fetchStockComments(selectedSymbol!),
    enabled: Boolean(selectedSymbol),
  });

  const stockTimelineQuery = useQuery({
    queryKey: ["stock-timeline", selectedSymbol],
    queryFn: () => fetchStockTimeline(selectedSymbol!),
    enabled: Boolean(selectedSymbol),
  });

  const syncMutation = useMutation({
    mutationFn: triggerSync,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["stocks"] }),
        queryClient.invalidateQueries({ queryKey: ["sync-status"] }),
        queryClient.invalidateQueries({ queryKey: ["sync-logs"] }),
        queryClient.invalidateQueries({ queryKey: ["stock", selectedSymbol] }),
        queryClient.invalidateQueries({
          queryKey: ["sync-log-detail", selectedSyncLogId],
        }),
      ]);
    },
  });

  const favoriteMutation = useMutation({
    mutationFn: ({ symbol, value }: { symbol: string; value: boolean }) =>
      setFavorite(symbol, value),
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["stocks"] }),
        queryClient.invalidateQueries({
          queryKey: ["stock", variables.symbol],
        }),
      ]);
    },
  });

  const watchlistMutation = useMutation({
    mutationFn: ({ symbol, value }: { symbol: string; value: boolean }) =>
      setWatchlist(symbol, value),
    onSuccess: async (_, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["stocks"] }),
        queryClient.invalidateQueries({
          queryKey: ["stock", variables.symbol],
        }),
      ]);
    },
  });

  const reorderMutation = useMutation({
    mutationFn: reorderStocks,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["stocks"] }),
        queryClient.invalidateQueries({ queryKey: ["stock", selectedSymbol] }),
      ]);
    },
  });

  const createCommentMutation = useMutation({
    mutationFn: ({ symbol, comment }: { symbol: string; comment: string }) =>
      createStockComment(symbol, comment),
    onSuccess: async (_, variables) => {
      setNewComment("");
      await queryClient.invalidateQueries({
        queryKey: ["stock-comments", variables.symbol],
      });
    },
  });

  const updateCommentMutation = useMutation({
    mutationFn: ({
      symbol,
      commentId,
      comment,
    }: {
      symbol: string;
      commentId: number;
      comment: string;
    }) => updateStockComment(symbol, commentId, comment),
    onSuccess: async (_, variables) => {
      setEditingCommentId(null);
      setEditingCommentValue("");
      await queryClient.invalidateQueries({
        queryKey: ["stock-comments", variables.symbol],
      });
    },
  });

  const deleteCommentMutation = useMutation({
    mutationFn: ({
      symbol,
      commentId,
    }: {
      symbol: string;
      commentId: number;
    }) => deleteStockComment(symbol, commentId),
    onSuccess: async (_, variables) => {
      if (editingCommentId === variables.commentId) {
        setEditingCommentId(null);
        setEditingCommentValue("");
      }
      await queryClient.invalidateQueries({
        queryKey: ["stock-comments", variables.symbol],
      });
    },
  });

  const createChartHighlightMutation = useMutation({
    mutationFn: (highlightDate: string) =>
      createChartHighlightDate(highlightDate),
    onSuccess: async () => {
      setNewHighlightDate("");
      await queryClient.invalidateQueries({
        queryKey: ["chart-highlight-dates"],
      });
    },
  });

  const deleteChartHighlightMutation = useMutation({
    mutationFn: (highlightId: number) => deleteChartHighlightDate(highlightId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["chart-highlight-dates"],
      });
    },
  });

  const filteredItems = useMemo(() => {
    const items = stocksQuery.data?.items ?? [];
    const normalized = searchTerm.trim().toLowerCase();

    return items.filter((item) => {
      const matchesSearch =
        !normalized ||
        item.symbol.toLowerCase().includes(normalized) ||
        item.companyName.toLowerCase().includes(normalized) ||
        item.industry.toLowerCase().includes(normalized);

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "above" && item.isAbove44MA) ||
        (statusFilter === "favorites" && item.isFavorite) ||
        (statusFilter === "watchlist" && item.inWatchlist);

      return matchesSearch && matchesStatus;
    });
  }, [searchTerm, statusFilter, stocksQuery.data?.items]);

  const groupedItems = useMemo(() => {
    const groups = filteredItems.reduce<Record<string, StockListItem[]>>(
      (accumulator, item) => {
        const key = item.industry || "Unknown";
        accumulator[key] ??= [];
        accumulator[key].push(item);
        return accumulator;
      },
      {},
    );

    return Object.fromEntries(
      Object.entries(groups).sort((left, right) => {
        const [leftIndustry, leftItems] = left;
        const [rightIndustry, rightItems] = right;
        const leftAbove = leftItems.filter((item) => item.isAbove44MA).length;
        const rightAbove = rightItems.filter((item) => item.isAbove44MA).length;
        const leftPct = leftItems.length ? leftAbove / leftItems.length : 0;
        const rightPct = rightItems.length ? rightAbove / rightItems.length : 0;

        if (rightPct !== leftPct) {
          return rightPct - leftPct;
        }
        if (rightAbove !== leftAbove) {
          return rightAbove - leftAbove;
        }
        return leftIndustry.localeCompare(rightIndustry);
      }),
    );
  }, [filteredItems]);

  const industryNames = Object.keys(groupedItems);
  const areAllGroupsCollapsed =
    industryNames.length > 0 &&
    industryNames.every((industry) => Boolean(collapsedIndustries[industry]));

  function toggleIndustry(industry: string): void {
    setCollapsedIndustries((current) => ({
      ...current,
      [industry]: !current[industry],
    }));
  }

  function toggleAllIndustries(): void {
    setCollapsedIndustries((current) => {
      const nextCollapsed = !areAllGroupsCollapsed;

      return industryNames.reduce<Record<string, boolean>>(
        (accumulator, industry) => {
          accumulator[industry] = nextCollapsed;
          return accumulator;
        },
        { ...current },
      );
    });
  }

  function moveStockWithinIndustry(
    industry: string,
    symbol: string,
    direction: -1 | 1,
  ): void {
    const currentItems = groupedItems[industry] ?? [];
    const currentIndex = currentItems.findIndex(
      (item) => item.symbol === symbol,
    );
    const targetIndex = currentIndex + direction;
    if (
      currentIndex === -1 ||
      targetIndex < 0 ||
      targetIndex >= currentItems.length
    ) {
      return;
    }

    const reordered = [...currentItems];
    const [moved] = reordered.splice(currentIndex, 1);
    reordered.splice(targetIndex, 0, moved);

    reorderMutation.mutate(
      reordered.map((item, index) => ({
        symbol: item.symbol,
        manualRank: index + 1,
      })),
    );
  }

  function startEditingComment(comment: StockCommentItem): void {
    setEditingCommentId(comment.id);
    setEditingCommentValue(comment.comment);
  }

  function cancelEditingComment(): void {
    setEditingCommentId(null);
    setEditingCommentValue("");
  }

  function submitNewComment(): void {
    if (!selectedSymbol) {
      return;
    }

    const trimmedComment = newComment.trim();
    if (!trimmedComment) {
      return;
    }

    createCommentMutation.mutate({
      symbol: selectedSymbol,
      comment: trimmedComment,
    });
  }

  function submitUpdatedComment(commentId: number): void {
    if (!selectedSymbol) {
      return;
    }

    const trimmedComment = editingCommentValue.trim();
    if (!trimmedComment) {
      return;
    }

    updateCommentMutation.mutate({
      symbol: selectedSymbol,
      commentId,
      comment: trimmedComment,
    });
  }

  function submitChartHighlightDate(): void {
    const trimmedDate = newHighlightDate.trim();
    if (!trimmedDate) {
      return;
    }

    createChartHighlightMutation.mutate(trimmedDate);
  }

  function removeChartHighlightDate(highlightId: number): void {
    deleteChartHighlightMutation.mutate(highlightId);
  }

  function removeComment(commentId: number): void {
    if (!selectedSymbol) {
      return;
    }

    deleteCommentMutation.mutate({ symbol: selectedSymbol, commentId });
  }

  const allTimelineItems = stockTimelineQuery.data?.items ?? [];

  const visibleTimelineItems = useMemo(() => {
    const items =
      allTimelineItems.length <= 44
        ? allTimelineItems
        : allTimelineItems.slice(-44);
    return withVisibleMovingAverage(items);
  }, [allTimelineItems]);

  const commentDateKeys = useMemo(() => {
    return new Set(
      (stockCommentsQuery.data?.items ?? [])
        .map((comment) => toLocalDateKey(comment.createdAt))
        .filter((value): value is string => Boolean(value)),
    );
  }, [stockCommentsQuery.data?.items]);

  const globalHighlightDateKeys = useMemo(() => {
    return new Set(
      (chartHighlightDatesQuery.data?.items ?? [])
        .map((item) => toLocalDateKey(item.highlightDate))
        .filter((value): value is string => Boolean(value)),
    );
  }, [chartHighlightDatesQuery.data?.items]);

  const highlightedDateKeys = useMemo(() => {
    return new Set([...commentDateKeys, ...globalHighlightDateKeys]);
  }, [commentDateKeys, globalHighlightDateKeys]);

  const candlestickMarks = useMemo(
    () =>
      buildCandlestickMarks(visibleTimelineItems).map((mark, index) => ({
        ...mark,
        hasComment: highlightedDateKeys.has(
          toLocalDateKey(visibleTimelineItems[index]?.tradeDate) ?? "",
        ),
      })),
    [highlightedDateKeys, visibleTimelineItems],
  );

  const activeTimelineItems = visibleTimelineItems;

  const activeTimelineIndex = useMemo(() => {
    if (!activeTimelineItems.length) {
      return null;
    }
    if (
      hoveredTimelineIndex !== null &&
      hoveredTimelineIndex >= 0 &&
      hoveredTimelineIndex < activeTimelineItems.length
    ) {
      return hoveredTimelineIndex;
    }
    return activeTimelineItems.length - 1;
  }, [activeTimelineItems, hoveredTimelineIndex]);

  const activeTimelineItem =
    activeTimelineIndex === null
      ? null
      : activeTimelineItems[activeTimelineIndex];
  const activeCandlestickMark =
    activeTimelineIndex === null ? null : candlestickMarks[activeTimelineIndex];
  const latestSyncLog = syncLogsQuery.data?.items[0] ?? null;

  useEffect(() => {
    if (selectedSyncLogId !== null) {
      return;
    }

    if (latestSyncLog) {
      setSelectedSyncLogId(latestSyncLog.id);
    }
  }, [latestSyncLog, selectedSyncLogId]);

  const movingAveragePath = useMemo(() => {
    const segments = candlestickMarks.filter(
      (mark) => mark.movingAverageY !== null,
    );
    if (!segments.length) {
      return "";
    }

    return segments
      .map(
        (mark, index) =>
          `${index === 0 ? "M" : "L"} ${mark.x} ${mark.movingAverageY}`,
      )
      .join(" ");
  }, [candlestickMarks]);

  function startSync(mode: "full" | "incremental", symbol?: string): void {
    syncMutation.mutate({
      mode: symbol ? "single_stock" : mode,
      symbol,
    });
  }

  function renderSyncStatusChip(status: string | null | undefined) {
    return (
      <span
        className={[
          "rounded-full px-2 py-0.5 text-[8px] font-semibold uppercase tracking-[0.12em]",
          syncStatusTone(status),
        ].join(" ")}
      >
        {status ?? "idle"}
      </span>
    );
  }

  return (
    <div className={activeTheme.appShell}>
      <main className="mx-auto flex min-h-screen max-w-[1500px] flex-col gap-2 p-2 lg:flex-row lg:p-5">
        <aside
          className={[
            "w-full overflow-hidden rounded-[1.35rem] border bg-white/90 backdrop-blur lg:max-w-[410px]",
            activeTheme.panelBorder,
            activeTheme.panelShadow,
          ].join(" ")}
        >
          <div className="border-b border-stone-200 px-3 py-2.5 sm:px-4 sm:py-3.5">
            <div className="flex items-start justify-between gap-2.5">
              <div className="min-w-0">
                <h1 className="text-[1.45rem] font-semibold leading-none tracking-tight text-stone-900 sm:text-[1.65rem]">
                  PaRo
                </h1>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <button
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-stone-900 px-2.5 py-1.5 text-[12px] font-medium text-white transition hover:bg-stone-700"
                  onClick={() => toggleAllIndustries()}
                  type="button"
                >
                  {areAllGroupsCollapsed ? "Expand all" : "Collapse all"}
                </button>
                <button
                  className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-stone-900 px-2.5 py-1.5 text-[12px] font-medium text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-400"
                  onClick={() => startSync("incremental")}
                  disabled={syncMutation.isPending}
                  type="button"
                >
                  <FiRefreshCcw
                    className={syncMutation.isPending ? "animate-spin" : ""}
                  />
                  Last Sync
                </button>
                <div className="inline-flex shrink-0 items-center rounded-full border border-stone-200 bg-white p-0.5 shadow-sm">
                  <button
                    className={[
                      "rounded-full px-2.5 py-1.5 text-[12px] font-medium transition",
                      rightPanelView === "notes"
                        ? "bg-stone-900 text-white"
                        : "text-stone-600 hover:bg-stone-100 hover:text-stone-900",
                    ].join(" ")}
                    onClick={() => setRightPanelView("notes")}
                    type="button"
                  >
                    Notes
                  </button>
                  <button
                    className={[
                      "rounded-full px-2.5 py-1.5 text-[12px] font-medium transition",
                      rightPanelView === "admin"
                        ? "bg-stone-900 text-white"
                        : "text-stone-600 hover:bg-stone-100 hover:text-stone-900",
                    ].join(" ")}
                    onClick={() => setRightPanelView("admin")}
                    type="button"
                  >
                    Admin
                  </button>
                </div>
              </div>
            </div>
            <div className="mt-2 flex items-center gap-2 rounded-[0.95rem] border border-stone-200 bg-stone-50 px-2.5 py-1.5">
              <FiSearch className="text-[13px] text-stone-500" />
              <input
                className="w-full border-none bg-transparent text-[12px] outline-none placeholder:text-stone-400 sm:text-[13px]"
                placeholder="Search symbol, company, or industry"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </div>
            <div className="mt-2 grid grid-cols-2 gap-1.5 sm:grid-cols-4">
              {[
                ["all", "All"],
                ["above", "44 MA"],
                ["favorites", "Favorites"],
                ["watchlist", "Watchlist"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  className={[
                    "rounded-[0.9rem] border px-2 py-1.25 text-[9px] font-semibold uppercase tracking-[0.06em] transition sm:px-2.5 sm:py-1.5 sm:text-[10px]",
                    statusFilter === value
                      ? "border-stone-900 bg-stone-900 text-white"
                      : "border-stone-200 bg-white text-stone-600 hover:border-amber-300 hover:bg-amber-50",
                  ].join(" ")}
                  onClick={() =>
                    setStatusFilter(
                      value as "all" | "above" | "favorites" | "watchlist",
                    )
                  }
                  type="button"
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="max-h-[calc(100vh-170px)] overflow-y-auto px-2.5 py-2.5 sm:px-3 sm:py-3">
            {stocksQuery.isLoading ? (
              <p className="px-2 text-sm text-stone-500">Loading stocks...</p>
            ) : null}
            {stocksQuery.isError ? (
              <p className="px-2 text-sm text-red-600">
                Failed to load stock list.
              </p>
            ) : null}
            {!stocksQuery.isLoading &&
            !stocksQuery.isError &&
            filteredItems.length === 0 ? (
              <div className="rounded-3xl border border-dashed border-stone-300 bg-stone-50 px-5 py-8 text-center">
                <p className="text-[13px] font-semibold text-stone-700">
                  No stocks match the current filters.
                </p>
                <p className="mt-2 text-[12px] text-stone-500">
                  Try clearing the search term or switching back to the full
                  list.
                </p>
              </div>
            ) : null}
            {Object.entries(groupedItems).map(([industry, items]) => {
              const aboveCount = items.filter(
                (item) => item.isAbove44MA,
              ).length;
              const percentage = items.length
                ? Math.round((aboveCount / items.length) * 100)
                : 0;
              const isCollapsed = Boolean(collapsedIndustries[industry]);
              return (
                <section
                  key={industry}
                  className="mb-3 rounded-[1.35rem] border border-stone-200 bg-stone-50/70 p-2.5"
                >
                  <button
                    className="mb-2 flex w-full items-center justify-between gap-3 px-1.5 text-left"
                    onClick={() => toggleIndustry(industry)}
                    type="button"
                  >
                    <div className="flex items-center gap-3">
                      <span className="rounded-full border border-stone-200 bg-white p-1 text-sm text-stone-600">
                        {isCollapsed ? <FiChevronRight /> : <FiChevronDown />}
                      </span>
                      <div>
                        <h2 className="text-[11px] font-semibold uppercase tracking-[0.14em] text-stone-700">
                          {industry}
                        </h2>
                        <p className="text-[11px] text-stone-500">
                          {aboveCount} above 44 MA out of {items.length}
                        </p>
                      </div>
                    </div>
                    <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-semibold text-emerald-700">
                      {percentage}%
                    </span>
                  </button>
                  {!isCollapsed ? (
                    <div className="space-y-2">
                      {items.map((item, index) => (
                        <div
                          key={item.symbol}
                          className={[
                            "rounded-[1.1rem] border px-2.5 py-2.5 transition",
                            selectedSymbol === item.symbol
                              ? "border-stone-900 bg-stone-900 text-white shadow-lg"
                              : "border-stone-200 bg-white hover:border-amber-300 hover:bg-amber-50",
                          ].join(" ")}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <button
                              className="min-w-0 flex-1 text-left"
                              onClick={() => setSelectedSymbol(item.symbol)}
                              type="button"
                            >
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-[12px] font-semibold">
                                    {item.symbol}
                                  </span>
                                  <span
                                    className={[
                                      "rounded-full px-2 py-0.5 text-[8px] font-semibold uppercase tracking-[0.12em]",
                                      item.isAbove44MA
                                        ? "bg-emerald-200 text-emerald-900"
                                        : "bg-stone-200 text-stone-700",
                                    ].join(" ")}
                                  >
                                    {item.isAbove44MA ? "Above" : "Below"}
                                  </span>
                                  {renderSyncStatusChip(item.lastSyncStatus)}
                                </div>
                                <p
                                  className={
                                    selectedSymbol === item.symbol
                                      ? "mt-1 text-[10px] text-stone-300"
                                      : "mt-1 text-[10px] text-stone-500"
                                  }
                                >
                                  {item.companyName}
                                </p>
                                <p
                                  className={
                                    selectedSymbol === item.symbol
                                      ? "mt-1 text-[10px] text-stone-300"
                                      : "mt-1 text-[10px] text-stone-500"
                                  }
                                >
                                  Last sync {formatDate(item.lastSyncAt)}
                                </p>
                              </div>
                            </button>
                            <div className="text-right">
                              <p className="text-[12px] font-semibold">
                                {formatNumber(item.percentAbove44MA)}%
                              </p>
                              <p
                                className={
                                  selectedSymbol === item.symbol
                                    ? "text-[10px] text-stone-300"
                                    : "text-[10px] text-stone-500"
                                }
                              >
                                MA44 {formatNumber(item.movingAverage44)}
                              </p>
                            </div>
                          </div>
                          <div className="mt-2 flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <button
                                aria-label={`Toggle favorite for ${item.symbol}`}
                                className={[
                                  "rounded-full border p-1.5 transition",
                                  item.isFavorite
                                    ? "border-amber-300 bg-amber-100 text-amber-800"
                                    : "border-stone-200 bg-white text-stone-500 hover:border-amber-300 hover:text-amber-700",
                                ].join(" ")}
                                onClick={() =>
                                  favoriteMutation.mutate({
                                    symbol: item.symbol,
                                    value: !item.isFavorite,
                                  })
                                }
                                type="button"
                              >
                                <FiStar />
                              </button>
                              <button
                                aria-label={`Toggle watchlist for ${item.symbol}`}
                                className={[
                                  "rounded-full border p-1.5 transition",
                                  item.inWatchlist
                                    ? "border-emerald-300 bg-emerald-100 text-emerald-800"
                                    : "border-stone-200 bg-white text-stone-500 hover:border-emerald-300 hover:text-emerald-700",
                                ].join(" ")}
                                onClick={() =>
                                  watchlistMutation.mutate({
                                    symbol: item.symbol,
                                    value: !item.inWatchlist,
                                  })
                                }
                                type="button"
                              >
                                <MdOutlinePlaylistAddCheck />
                              </button>
                              <button
                                aria-label={`Open ${item.symbol} on Chartink`}
                                className="rounded-full border border-stone-200 bg-white p-1.5 text-stone-500 transition hover:border-sky-300 hover:text-sky-700"
                                onClick={() => openChartinkStock(item.symbol)}
                                type="button"
                              >
                                <FiExternalLink />
                              </button>
                            </div>
                            <div className="flex items-center gap-2">
                              {item.canRetrySync ? (
                                <button
                                  aria-label={`Sync ${item.symbol}`}
                                  className="rounded-full border border-sky-200 bg-sky-50 px-2.5 py-1 text-[10px] font-semibold text-sky-700 transition hover:border-sky-300 hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-40"
                                  disabled={syncMutation.isPending}
                                  onClick={() =>
                                    startSync("incremental", item.symbol)
                                  }
                                  type="button"
                                >
                                  Sync This Stock
                                </button>
                              ) : null}
                              <button
                                aria-label={`Move ${item.symbol} up`}
                                className="rounded-full border border-stone-200 bg-white p-1.5 text-stone-500 transition hover:border-amber-300 hover:text-amber-700 disabled:cursor-not-allowed disabled:opacity-40"
                                disabled={
                                  index === 0 || reorderMutation.isPending
                                }
                                onClick={() =>
                                  moveStockWithinIndustry(
                                    industry,
                                    item.symbol,
                                    -1,
                                  )
                                }
                                type="button"
                              >
                                <FiArrowUp />
                              </button>
                              <button
                                aria-label={`Move ${item.symbol} down`}
                                className="rounded-full border border-stone-200 bg-white p-1.5 text-stone-500 transition hover:border-amber-300 hover:text-amber-700 disabled:cursor-not-allowed disabled:opacity-40"
                                disabled={
                                  index === items.length - 1 ||
                                  reorderMutation.isPending
                                }
                                onClick={() =>
                                  moveStockWithinIndustry(
                                    industry,
                                    item.symbol,
                                    1,
                                  )
                                }
                                type="button"
                              >
                                <FiArrowDown />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="px-2 pb-2 text-xs text-stone-500">
                      Group collapsed.
                    </p>
                  )}
                </section>
              );
            })}
          </div>
        </aside>

        <section
          className={[
            "flex-1 rounded-[1.6rem] border bg-white/90 p-4 backdrop-blur lg:p-5",
            activeTheme.panelBorder,
            activeTheme.mainPanelShadow,
          ].join(" ")}
        >
          <div className="grid gap-3 xl:grid-cols-[1.45fr_0.85fr]">
            <div className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4">
              {stockDetailQuery.isLoading ? (
                <p className="text-sm text-stone-500">
                  Loading stock details...
                </p>
              ) : null}
              {stockDetailQuery.isError ? (
                <p className="text-sm text-red-600">
                  Failed to load stock details.
                </p>
              ) : null}
              {!selectedSymbol ? (
                <p className="text-sm text-stone-500">
                  Select a stock from the left panel to view detailed metrics.
                </p>
              ) : null}
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
                    Selected Stock
                  </p>
                  <h2 className="mt-1.5 text-[1.45rem] font-semibold text-stone-900 lg:text-[1.6rem]">
                    {stockDetailQuery.data?.companyName ??
                      selectedSymbol ??
                      "Choose a stock"}
                  </h2>
                  <p className="mt-1.5 text-[13px] text-stone-500">
                    {stockDetailQuery.data?.symbol ?? "--"}{" "}
                    {stockDetailQuery.data?.industry
                      ? `• ${stockDetailQuery.data.industry}`
                      : ""}
                  </p>
                </div>
                <div
                  className={[
                    "rounded-[1.1rem] px-3.5 py-2.5 text-left md:min-w-[180px] md:text-right",
                    activeTheme.signalCard,
                  ].join(" ")}
                >
                  <p className="text-[10px] uppercase tracking-[0.14em]">
                    Signal
                  </p>
                  <p className="mt-1 text-[14px] font-semibold">
                    {stockDetailQuery.data?.isAbove44MA
                      ? "Above 44 MA"
                      : "Below 44 MA"}
                  </p>
                </div>
              </div>

              <section className="mt-4 rounded-[1.05rem] border border-stone-200 bg-white p-3.5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                      Price Timeline
                    </p>
                  </div>
                  <div className="rounded-full bg-stone-100 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-stone-600">
                    44 Candles
                  </div>
                </div>

                {activeTimelineItem ? (
                  <div className="mt-3 grid gap-2 sm:grid-cols-6">
                    <div className="rounded-[0.9rem] bg-stone-100 px-2.5 py-2 text-[11px] text-stone-600">
                      <p className="uppercase tracking-[0.1em] text-[9px] text-stone-500">
                        Date
                      </p>
                      <p className="mt-1 font-semibold text-stone-800">
                        {formatShortDate(activeTimelineItem.tradeDate)}
                      </p>
                    </div>
                    <div className="rounded-[0.9rem] bg-stone-100 px-2.5 py-2 text-[11px] text-stone-600">
                      <p className="uppercase tracking-[0.1em] text-[9px] text-stone-500">
                        Open
                      </p>
                      <p className="mt-1 font-semibold text-stone-800">
                        {formatNumber(
                          activeTimelineItem.openPrice ??
                            activeTimelineItem.closePrice,
                        )}
                      </p>
                    </div>
                    <div className="rounded-[0.9rem] bg-stone-100 px-2.5 py-2 text-[11px] text-stone-600">
                      <p className="uppercase tracking-[0.1em] text-[9px] text-stone-500">
                        High
                      </p>
                      <p className="mt-1 font-semibold text-stone-800">
                        {formatNumber(
                          activeTimelineItem.highPrice ??
                            activeTimelineItem.closePrice,
                        )}
                      </p>
                    </div>
                    <div className="rounded-[0.9rem] bg-stone-100 px-2.5 py-2 text-[11px] text-stone-600">
                      <p className="uppercase tracking-[0.1em] text-[9px] text-stone-500">
                        Low
                      </p>
                      <p className="mt-1 font-semibold text-stone-800">
                        {formatNumber(
                          activeTimelineItem.lowPrice ??
                            activeTimelineItem.closePrice,
                        )}
                      </p>
                    </div>
                    <div className="rounded-[0.9rem] bg-stone-100 px-2.5 py-2 text-[11px] text-stone-600">
                      <p className="uppercase tracking-[0.1em] text-[9px] text-stone-500">
                        Close
                      </p>
                      <p className="mt-1 font-semibold text-stone-800">
                        {formatNumber(activeTimelineItem.closePrice)}
                      </p>
                    </div>
                    <div className="rounded-[0.9rem] bg-stone-100 px-2.5 py-2 text-[11px] text-stone-600">
                      <p className="uppercase tracking-[0.1em] text-[9px] text-stone-500">
                        44 MA
                      </p>
                      <p className="mt-1 font-semibold text-stone-800">
                        {formatNumber(activeTimelineItem.movingAverage44)}
                      </p>
                    </div>
                  </div>
                ) : null}

                <div className="mt-3 rounded-[1rem] border border-stone-200 bg-stone-50 p-3">
                  {stockTimelineQuery.isLoading ? (
                    <p className="text-[13px] text-stone-500">
                      Loading chart...
                    </p>
                  ) : null}
                  {stockTimelineQuery.isError ? (
                    <p className="text-[13px] text-red-600">
                      Failed to load chart data.
                    </p>
                  ) : null}
                  {!stockTimelineQuery.isLoading &&
                  !stockTimelineQuery.isError &&
                  !visibleTimelineItems.length ? (
                    <p className="text-[13px] text-stone-500">
                      No price history available.
                    </p>
                  ) : null}
                  {candlestickMarks.length ? (
                    <>
                      <div className="w-full">
                        <svg
                          viewBox="0 0 720 240"
                          preserveAspectRatio="none"
                          className="h-[240px] w-full max-w-full"
                        >
                          <rect
                            x="0"
                            y="0"
                            width="720"
                            height="240"
                            rx="16"
                            fill="#fafaf9"
                          />
                          {[44, 84, 124, 164].map((y) => (
                            <line
                              key={y}
                              x1="8"
                              x2="712"
                              y1={y}
                              y2={y}
                              stroke="#e7e5e4"
                              strokeWidth="1"
                            />
                          ))}
                          <line
                            x1="8"
                            x2="712"
                            y1="186"
                            y2="186"
                            stroke="#d6d3d1"
                            strokeWidth="1"
                          />
                          {activeCandlestickMark ? (
                            <line
                              x1={activeCandlestickMark.x}
                              x2={activeCandlestickMark.x}
                              y1="12"
                              y2="228"
                              stroke="#78716c"
                              strokeDasharray="4 4"
                              strokeWidth="1"
                            />
                          ) : null}
                          {movingAveragePath ? (
                            <path
                              d={movingAveragePath}
                              fill="none"
                              stroke="#2563eb"
                              strokeWidth="2.25"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          ) : null}
                          {candlestickMarks.map((mark) => (
                            <rect
                              key={`${mark.key}-volume`}
                              x={mark.x - mark.bodyWidth / 2}
                              y={mark.volumeTop}
                              width={mark.bodyWidth}
                              height={mark.volumeHeight}
                              rx="1.5"
                              fill={mark.color}
                              fillOpacity={mark.hasComment ? "0.45" : "0.28"}
                            />
                          ))}
                          {candlestickMarks.map((mark) => (
                            <g key={mark.key}>
                              {mark.hasComment ? (
                                <rect
                                  x={mark.x - mark.bodyWidth / 2 - 2.5}
                                  y={mark.bodyTop - 4}
                                  width={mark.bodyWidth + 5}
                                  height={Math.max(mark.bodyHeight + 8, 12)}
                                  rx="4"
                                  fill="#fef3c7"
                                  stroke="#f59e0b"
                                  strokeWidth="1.2"
                                />
                              ) : null}
                              <line
                                x1={mark.x}
                                x2={mark.x}
                                y1={mark.wickTop}
                                y2={mark.wickBottom}
                                stroke={mark.color}
                                strokeWidth={mark.hasComment ? "2.2" : "1.6"}
                              />
                              <rect
                                x={mark.x - mark.bodyWidth / 2}
                                y={mark.bodyTop}
                                width={mark.bodyWidth}
                                height={mark.bodyHeight}
                                rx="1.5"
                                fill={mark.color}
                              />
                              {mark.hasComment ? (
                                <circle
                                  cx={mark.x}
                                  cy={mark.wickTop - 6}
                                  r="2.5"
                                  fill="#f59e0b"
                                />
                              ) : null}
                            </g>
                          ))}
                          {candlestickMarks.map((mark, index) => (
                            <rect
                              key={`${mark.key}-hitbox`}
                              x={Math.max(mark.x - 6, 0)}
                              y="12"
                              width="12"
                              height="216"
                              fill="transparent"
                              onMouseEnter={() =>
                                setHoveredTimelineIndex(index)
                              }
                              onMouseLeave={() => setHoveredTimelineIndex(null)}
                            />
                          ))}
                        </svg>
                      </div>
                    </>
                  ) : null}
                </div>
              </section>

              <div className="mt-4 grid gap-2.5 md:grid-cols-3">
                <article className="rounded-[1.05rem] border border-stone-200 bg-white p-3.5">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                    Close Price
                  </p>
                  <p className="mt-1.5 text-[1.05rem] font-semibold text-stone-900">
                    {formatNumber(stockDetailQuery.data?.closePrice)}
                  </p>
                </article>
                <article className="rounded-[1.05rem] border border-stone-200 bg-white p-3.5">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                    44 Day MA
                  </p>
                  <p className="mt-1.5 text-[1.05rem] font-semibold text-stone-900">
                    {formatNumber(stockDetailQuery.data?.movingAverage44)}
                  </p>
                </article>
                <article className="rounded-[1.05rem] border border-stone-200 bg-white p-3.5">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                    % Above MA
                  </p>
                  <p className="mt-1.5 text-[1.05rem] font-semibold text-stone-900">
                    {formatNumber(stockDetailQuery.data?.percentAbove44MA)}%
                  </p>
                </article>
              </div>

              <div className="mt-4 grid gap-2.5 md:grid-cols-2">
                <article className="rounded-[1.05rem] border border-stone-200 bg-white p-3.5">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                    Identifiers
                  </p>
                  <dl className="mt-2.5 space-y-1.5 text-[13px] text-stone-700">
                    <div className="flex justify-between gap-4">
                      <dt>Yahoo</dt>
                      <dd>{stockDetailQuery.data?.yahooTicker ?? "--"}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Series</dt>
                      <dd>{stockDetailQuery.data?.series ?? "--"}</dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>ISIN</dt>
                      <dd>{stockDetailQuery.data?.isinCode ?? "--"}</dd>
                    </div>
                  </dl>
                </article>
                <article className="rounded-[1.05rem] border border-stone-200 bg-white p-3.5">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                    Data Freshness
                  </p>
                  <dl className="mt-2.5 space-y-1.5 text-[13px] text-stone-700">
                    <div className="flex justify-between gap-4">
                      <dt>Updated</dt>
                      <dd>
                        {formatDate(stockDetailQuery.data?.lastUpdatedAt)}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Sync Status</dt>
                      <dd>
                        {stockDetailQuery.data
                          ? formatSyncMode(stockDetailQuery.data.lastSyncStatus)
                          : "--"}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Favorite</dt>
                      <dd>
                        {stockDetailQuery.data?.isFavorite ? "Yes" : "No"}
                      </dd>
                    </div>
                    <div className="flex justify-between gap-4">
                      <dt>Watchlist</dt>
                      <dd>
                        {stockDetailQuery.data?.inWatchlist ? "Yes" : "No"}
                      </dd>
                    </div>
                  </dl>
                </article>
              </div>
            </div>

            <div className="space-y-3">
              {rightPanelView === "notes" ? (
                <section className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4">
                  <div className="rounded-[1rem] border border-stone-200 bg-white p-3">
                    <textarea
                      className="min-h-[128px] w-full resize-y rounded-[0.9rem] border border-stone-200 bg-stone-50 px-3 py-2 text-[13px] text-stone-700 outline-none placeholder:text-stone-400 focus:border-stone-400"
                      placeholder={
                        selectedSymbol
                          ? "Add a note for this stock..."
                          : "Select a stock to add notes"
                      }
                      value={newComment}
                      onChange={(event) => setNewComment(event.target.value)}
                      disabled={
                        !selectedSymbol || createCommentMutation.isPending
                      }
                    />
                    <div className="mt-3 flex justify-end">
                      <button
                        className="inline-flex items-center rounded-full bg-stone-900 px-3 py-1.5 text-[12px] font-medium text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-400"
                        onClick={() => submitNewComment()}
                        disabled={
                          !selectedSymbol ||
                          !newComment.trim() ||
                          createCommentMutation.isPending
                        }
                        type="button"
                      >
                        {createCommentMutation.isPending
                          ? "Saving..."
                          : "Add note"}
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 space-y-2.5">
                    {stockCommentsQuery.isLoading ? (
                      <p className="text-[13px] text-stone-500">
                        Loading notes...
                      </p>
                    ) : null}
                    {stockCommentsQuery.isError ? (
                      <p className="text-[13px] text-red-600">
                        Failed to load notes.
                      </p>
                    ) : null}
                    {!stockCommentsQuery.isLoading &&
                    !stockCommentsQuery.isError &&
                    !stockCommentsQuery.data?.items.length ? (
                      <p className="text-[13px] text-stone-500">
                        No notes yet.
                      </p>
                    ) : null}
                    {stockCommentsQuery.data?.items.map((comment) => {
                      const isEditing = editingCommentId === comment.id;
                      return (
                        <article
                          key={comment.id}
                          className="rounded-[1rem] border border-stone-200 bg-white p-3"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-[11px] font-semibold text-stone-700">
                                {formatDate(comment.createdAt)}
                              </p>
                              <p className="mt-0.5 text-[11px] text-stone-500">
                                Updated {formatDate(comment.updatedAt)}
                              </p>
                            </div>
                            {!isEditing ? (
                              <div className="flex items-center gap-3">
                                <button
                                  className="text-[11px] font-semibold text-stone-600 transition hover:text-stone-900"
                                  onClick={() => startEditingComment(comment)}
                                  type="button"
                                >
                                  Edit
                                </button>
                                <button
                                  className="text-[11px] font-semibold text-red-600 transition hover:text-red-700 disabled:cursor-not-allowed disabled:text-red-300"
                                  onClick={() => removeComment(comment.id)}
                                  disabled={deleteCommentMutation.isPending}
                                  type="button"
                                >
                                  {deleteCommentMutation.isPending
                                    ? "Deleting..."
                                    : "Delete"}
                                </button>
                              </div>
                            ) : null}
                          </div>

                          {isEditing ? (
                            <>
                              <textarea
                                className="mt-2 min-h-[88px] w-full resize-y rounded-[0.9rem] border border-stone-200 bg-stone-50 px-3 py-2 text-[13px] text-stone-700 outline-none placeholder:text-stone-400 focus:border-stone-400"
                                value={editingCommentValue}
                                onChange={(event) =>
                                  setEditingCommentValue(event.target.value)
                                }
                                disabled={updateCommentMutation.isPending}
                              />
                              <div className="mt-2 flex justify-end gap-2">
                                <button
                                  className="rounded-full border border-stone-200 bg-white px-3 py-1.5 text-[12px] font-medium text-stone-600 transition hover:border-stone-300 hover:bg-stone-100"
                                  onClick={() => cancelEditingComment()}
                                  type="button"
                                >
                                  Cancel
                                </button>
                                <button
                                  className="rounded-full bg-stone-900 px-3 py-1.5 text-[12px] font-medium text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-400"
                                  onClick={() =>
                                    submitUpdatedComment(comment.id)
                                  }
                                  disabled={
                                    !editingCommentValue.trim() ||
                                    updateCommentMutation.isPending
                                  }
                                  type="button"
                                >
                                  {updateCommentMutation.isPending
                                    ? "Saving..."
                                    : "Save"}
                                </button>
                              </div>
                            </>
                          ) : (
                            <p className="mt-2 whitespace-pre-wrap text-[13px] leading-5 text-stone-700">
                              {comment.comment}
                            </p>
                          )}
                        </article>
                      );
                    })}
                  </div>
                </section>
              ) : (
                <>
                  <section className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-[15px] font-semibold text-stone-900">
                          Sync Control
                        </h3>
                        <p className="mt-1 text-[12px] text-stone-500">
                          Run a full one-year refresh or an incremental sync
                          from the latest stored data.
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-2">
                      <button
                        className="inline-flex items-center justify-center rounded-full border border-stone-200 bg-white px-3 py-2 text-[12px] font-medium text-stone-700 transition hover:border-amber-300 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-40"
                        onClick={() => startSync("full")}
                        disabled={syncMutation.isPending}
                        type="button"
                      >
                        Full Sync
                      </button>
                      <button
                        className="inline-flex items-center justify-center rounded-full bg-stone-900 px-3 py-2 text-[12px] font-medium text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-400"
                        onClick={() => startSync("incremental")}
                        disabled={syncMutation.isPending}
                        type="button"
                      >
                        {syncMutation.isPending ? "Syncing..." : "Last Sync"}
                      </button>
                    </div>
                    <div className="mt-3 rounded-[1rem] bg-white p-3">
                      <div className="flex items-center gap-2">
                        {renderSyncStatusChip(syncStatusQuery.data?.status)}
                        <span className="text-[12px] text-stone-600">
                          {formatSyncMode(syncStatusQuery.data?.mode)}
                        </span>
                      </div>
                      <p className="mt-2 text-[12px] text-stone-600">
                        Processed {syncStatusQuery.data?.stocksProcessed ?? 0},
                        updated {syncStatusQuery.data?.stocksUpdated ?? 0},
                        failed {syncStatusQuery.data?.failedStocks ?? 0}
                      </p>
                      <p className="mt-1 text-[12px] text-stone-600">
                        Started{" "}
                        {formatDate(syncStatusQuery.data?.lastSyncStartedAt)}
                      </p>
                      <p className="mt-1 text-[12px] text-stone-600">
                        Successful{" "}
                        {formatDate(syncStatusQuery.data?.lastSuccessfulSyncAt)}
                      </p>
                      {syncStatusQuery.data?.errorMessage ? (
                        <p className="mt-2 text-[12px] text-rose-600">
                          {syncStatusQuery.data.errorMessage}
                        </p>
                      ) : null}
                    </div>
                  </section>

                  <section className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-[15px] font-semibold text-stone-900">
                          Theme
                        </h3>
                        <p className="mt-1 text-[12px] text-stone-500">
                          Switch the app look. Current theme stays the default.
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      {(
                        Object.entries(themeOptions) as Array<
                          [ThemeName, (typeof themeOptions)[ThemeName]]
                        >
                      ).map(([value, option]) => (
                        <button
                          key={value}
                          className={[
                            "rounded-[1rem] border px-3 py-2 text-[12px] font-semibold transition",
                            themeName === value
                              ? activeTheme.adminThemeButtonActive
                              : activeTheme.adminThemeButtonInactive,
                          ].join(" ")}
                          onClick={() => setThemeName(value)}
                          type="button"
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </section>

                  <section className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h3 className="text-[15px] font-semibold text-stone-900">
                          Chart Highlights
                        </h3>
                        <p className="mt-1 text-[12px] text-stone-500">
                          Global dates that highlight matching candles for every
                          stock.
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 rounded-[1rem] border border-stone-200 bg-white p-3">
                      <div className="flex flex-col gap-2 sm:flex-row">
                        <input
                          className="w-full rounded-[0.9rem] border border-stone-200 bg-stone-50 px-3 py-2 text-[13px] text-stone-700 outline-none focus:border-stone-400"
                          type="date"
                          value={newHighlightDate}
                          onChange={(event) =>
                            setNewHighlightDate(event.target.value)
                          }
                          disabled={createChartHighlightMutation.isPending}
                        />
                        <button
                          className="inline-flex items-center justify-center rounded-full bg-stone-900 px-3 py-2 text-[12px] font-medium text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:bg-stone-400"
                          onClick={() => submitChartHighlightDate()}
                          disabled={
                            !newHighlightDate ||
                            createChartHighlightMutation.isPending
                          }
                          type="button"
                        >
                          {createChartHighlightMutation.isPending
                            ? "Adding..."
                            : "Add date"}
                        </button>
                      </div>
                    </div>

                    <div className="mt-3 space-y-2.5">
                      {chartHighlightDatesQuery.isLoading ? (
                        <p className="text-[13px] text-stone-500">
                          Loading highlight dates...
                        </p>
                      ) : null}
                      {chartHighlightDatesQuery.isError ? (
                        <p className="text-[13px] text-red-600">
                          Failed to load highlight dates.
                        </p>
                      ) : null}
                      {!chartHighlightDatesQuery.isLoading &&
                      !chartHighlightDatesQuery.isError &&
                      !chartHighlightDatesQuery.data?.items.length ? (
                        <p className="text-[13px] text-stone-500">
                          No highlight dates added yet.
                        </p>
                      ) : null}
                      {chartHighlightDatesQuery.data?.items.map(
                        (item: ChartHighlightDateItem) => (
                          <article
                            key={item.id}
                            className="flex items-center justify-between gap-3 rounded-[1rem] border border-stone-200 bg-white px-3 py-2.5"
                          >
                            <div>
                              <p className="text-[13px] font-semibold text-stone-800">
                                {formatShortDate(item.highlightDate)}
                              </p>
                              <p className="mt-0.5 text-[11px] text-stone-500">
                                Added {formatDate(item.createdAt)}
                              </p>
                            </div>
                            <button
                              className="text-[11px] font-semibold text-red-600 transition hover:text-red-700 disabled:cursor-not-allowed disabled:text-red-300"
                              onClick={() => removeChartHighlightDate(item.id)}
                              disabled={deleteChartHighlightMutation.isPending}
                              type="button"
                            >
                              {deleteChartHighlightMutation.isPending
                                ? "Deleting..."
                                : "Delete"}
                            </button>
                          </article>
                        ),
                      )}
                    </div>
                  </section>

                  <section className="rounded-[1.25rem] border border-stone-200 bg-stone-900 p-4 text-stone-50">
                    <div className="flex items-center gap-3">
                      <FiActivity className="text-amber-300" />
                      <h3 className="text-[15px] font-semibold">Sync Status</h3>
                    </div>
                    <p className="mt-3 text-[1.35rem] font-semibold capitalize">
                      {syncStatusQuery.data?.status ?? "idle"}
                    </p>
                    <p className="mt-1 text-[12px] text-stone-300">
                      Mode: {formatSyncMode(syncStatusQuery.data?.mode)}
                    </p>
                    <p className="mt-2 text-[13px] text-stone-300">
                      Last started:{" "}
                      {formatDate(syncStatusQuery.data?.lastSyncStartedAt)}
                    </p>
                    <p className="mt-1 text-[13px] text-stone-300">
                      Last success:{" "}
                      {formatDate(syncStatusQuery.data?.lastSuccessfulSyncAt)}
                    </p>
                    <div className="mt-4 grid grid-cols-2 gap-2.5">
                      <div className="rounded-[1rem] bg-white/10 p-3">
                        <p className="text-[10px] uppercase tracking-[0.14em] text-stone-300">
                          Processed
                        </p>
                        <p className="mt-1.5 text-[1.05rem] font-semibold">
                          {syncStatusQuery.data?.stocksProcessed ?? 0}
                        </p>
                      </div>
                      <div className="rounded-[1rem] bg-white/10 p-3">
                        <p className="text-[10px] uppercase tracking-[0.14em] text-stone-300">
                          Updated
                        </p>
                        <p className="mt-1.5 text-[1.05rem] font-semibold">
                          {syncStatusQuery.data?.stocksUpdated ?? 0}
                        </p>
                      </div>
                    </div>
                    <p className="mt-2 text-[13px] text-stone-300">
                      Failed or partial:{" "}
                      {syncStatusQuery.data?.failedStocks ?? 0}
                    </p>
                    <div className="mt-4 flex justify-end">
                      <button
                        className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-[12px] font-medium text-stone-900 transition hover:bg-stone-100 disabled:cursor-not-allowed disabled:bg-stone-300 disabled:text-stone-600"
                        onClick={() => startSync("incremental")}
                        disabled={syncMutation.isPending}
                        type="button"
                      >
                        <FiRefreshCcw
                          className={
                            syncMutation.isPending ? "animate-spin" : ""
                          }
                        />
                        {syncMutation.isPending ? "Syncing..." : "Last Sync"}
                      </button>
                    </div>
                    {syncStatusQuery.data?.errorMessage ? (
                      <p className="mt-4 text-sm text-red-300">
                        {syncStatusQuery.data.errorMessage}
                      </p>
                    ) : null}
                    {favoriteMutation.isPending ||
                    watchlistMutation.isPending ||
                    reorderMutation.isPending ? (
                      <p className="mt-4 text-sm text-amber-200">
                        Updating preferences...
                      </p>
                    ) : null}
                  </section>

                  <section className="rounded-[1.25rem] border border-stone-200 bg-stone-50 p-4">
                    <div className="flex items-center gap-3">
                      <FiTrendingUp className="text-amber-700" />
                      <h3 className="text-[15px] font-semibold text-stone-900">
                        Recent Sync Logs
                      </h3>
                    </div>
                    <div className="mt-3 space-y-2.5">
                      {syncLogsQuery.data?.items.length ? (
                        syncLogsQuery.data.items
                          .slice(0, 5)
                          .map((log: SyncLogItem) => (
                            <button
                              key={log.id}
                              className={[
                                "w-full rounded-[1rem] border p-3 text-left transition",
                                selectedSyncLogId === log.id
                                  ? "border-stone-900 bg-stone-900 text-white"
                                  : "border-stone-200 bg-white hover:border-amber-300 hover:bg-amber-50",
                              ].join(" ")}
                              onClick={() => setSelectedSyncLogId(log.id)}
                              type="button"
                            >
                              <div className="flex items-center justify-between gap-3">
                                <div className="flex items-center gap-2">
                                  {renderSyncStatusChip(log.status)}
                                  <span
                                    className={
                                      selectedSyncLogId === log.id
                                        ? "text-[11px] font-semibold text-white"
                                        : "text-[11px] font-semibold text-stone-900"
                                    }
                                  >
                                    {formatSyncMode(log.mode)}
                                  </span>
                                </div>
                                <span
                                  className={
                                    selectedSyncLogId === log.id
                                      ? "text-[11px] text-stone-300"
                                      : "text-[11px] text-stone-500"
                                  }
                                >
                                  {formatDate(log.startedAt)}
                                </span>
                              </div>
                              <p
                                className={
                                  selectedSyncLogId === log.id
                                    ? "mt-2 text-[13px] text-stone-200"
                                    : "mt-2 text-[13px] text-stone-600"
                                }
                              >
                                Processed {log.stocksProcessed}, updated{" "}
                                {log.stocksUpdated}, failed {log.failedStocks}
                              </p>
                              {log.errorMessage ? (
                                <p className="mt-1 text-[13px] text-red-600">
                                  {log.errorMessage}
                                </p>
                              ) : null}
                            </button>
                          ))
                      ) : (
                        <p className="text-[13px] text-stone-500">
                          No sync logs yet.
                        </p>
                      )}
                    </div>
                    <div className="mt-3 space-y-2.5 rounded-[1rem] border border-stone-200 bg-white p-3">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
                          Run Detail
                        </p>
                        {syncLogDetailQuery.data ? (
                          <span className="text-[11px] text-stone-500">
                            {syncLogDetailQuery.data.items.length} stocks
                          </span>
                        ) : null}
                      </div>
                      {syncLogDetailQuery.isLoading ? (
                        <p className="text-[13px] text-stone-500">
                          Loading sync detail...
                        </p>
                      ) : null}
                      {syncLogDetailQuery.isError ? (
                        <p className="text-[13px] text-red-600">
                          Failed to load sync detail.
                        </p>
                      ) : null}
                      {!syncLogDetailQuery.isLoading &&
                      !syncLogDetailQuery.isError &&
                      !syncLogDetailQuery.data?.items.length ? (
                        <p className="text-[13px] text-stone-500">
                          No per-stock sync records yet.
                        </p>
                      ) : null}
                      {syncLogDetailQuery.data?.items.map((item) => (
                        <article
                          key={item.id}
                          className="rounded-[0.95rem] border border-stone-200 bg-stone-50 px-3 py-2.5"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="text-[12px] font-semibold text-stone-900">
                                {item.symbol}
                              </span>
                              {renderSyncStatusChip(item.status)}
                            </div>
                            <span className="text-[11px] text-stone-500">
                              {item.rowsWritten} rows
                            </span>
                          </div>
                          <p className="mt-1 text-[11px] text-stone-600">
                            Window {item.rangeStart ?? "--"} to{" "}
                            {item.rangeEnd ?? "--"}
                          </p>
                          {item.message ? (
                            <p className="mt-1 text-[11px] text-red-600">
                              {item.message}
                            </p>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  </section>
                </>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
