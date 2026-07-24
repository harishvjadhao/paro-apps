from datetime import date, datetime

from pydantic import BaseModel


class SyncTriggerRequest(BaseModel):
    mode: str
    symbol: str | None = None


class SyncStatusData(BaseModel):
    status: str
    lastSuccessfulSyncAt: datetime | None = None
    lastSyncStartedAt: datetime | None = None
    stocksProcessed: int
    stocksUpdated: int
    errorMessage: str | None = None
    mode: str | None = None
    failedStocks: int = 0


class SyncLogItem(BaseModel):
    id: int
    startedAt: datetime
    finishedAt: datetime | None
    status: str
    stocksProcessed: int
    stocksUpdated: int
    errorMessage: str | None
    source: str | None
    mode: str | None = None
    failedStocks: int = 0


class SyncLogStockItem(BaseModel):
    id: int
    stockId: int
    symbol: str
    syncMode: str
    status: str
    message: str | None
    rangeStart: date | None
    rangeEnd: date | None
    startedAt: datetime
    finishedAt: datetime | None
    rowsWritten: int


class SyncLogDetailData(BaseModel):
    id: int
    startedAt: datetime
    finishedAt: datetime | None
    status: str
    stocksProcessed: int
    stocksUpdated: int
    failedStocks: int
    errorMessage: str | None
    source: str | None
    mode: str | None = None
    items: list[SyncLogStockItem]


class SyncLogListData(BaseModel):
    items: list[SyncLogItem]