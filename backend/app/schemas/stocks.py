from datetime import datetime
from datetime import date

from pydantic import BaseModel


class StockListItem(BaseModel):
    symbol: str
    companyName: str
    industry: str
    closePrice: float | None
    movingAverage44: float | None
    isAbove44MA: bool
    percentAbove44MA: float | None
    isFavorite: bool
    inWatchlist: bool
    manualRank: int | None


class StockListData(BaseModel):
    items: list[StockListItem]
    total: int


class StockDetailData(BaseModel):
    symbol: str
    companyName: str
    industry: str
    series: str | None
    isinCode: str | None
    yahooTicker: str
    closePrice: float | None
    movingAverage44: float | None
    isAbove44MA: bool
    percentAbove44MA: float | None
    isFavorite: bool
    inWatchlist: bool
    lastUpdatedAt: datetime | None


class StockCommentItem(BaseModel):
    id: int
    comment: str
    createdAt: datetime
    updatedAt: datetime


class StockCommentListData(BaseModel):
    items: list[StockCommentItem]


class StockCommentCreateRequest(BaseModel):
    comment: str


class StockCommentUpdateRequest(BaseModel):
    comment: str


class ChartHighlightDateItem(BaseModel):
    id: int
    highlightDate: date
    createdAt: datetime


class ChartHighlightDateListData(BaseModel):
    items: list[ChartHighlightDateItem]


class ChartHighlightDateCreateRequest(BaseModel):
    highlightDate: date


class StockTimelineItem(BaseModel):
    tradeDate: date
    openPrice: float | None
    highPrice: float | None
    lowPrice: float | None
    closePrice: float
    volume: int | None
    movingAverage44: float | None


class StockTimelineData(BaseModel):
    items: list[StockTimelineItem]


class StockPreferenceRequest(BaseModel):
    value: bool


class StockReorderItem(BaseModel):
    symbol: str
    manualRank: int


class StockReorderRequest(BaseModel):
    items: list[StockReorderItem]