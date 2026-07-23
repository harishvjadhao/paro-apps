from datetime import datetime

from pydantic import BaseModel


class SyncStatusData(BaseModel):
    status: str
    lastSuccessfulSyncAt: datetime | None = None
    lastSyncStartedAt: datetime | None = None
    stocksProcessed: int
    stocksUpdated: int
    errorMessage: str | None = None


class SyncLogItem(BaseModel):
    id: int
    startedAt: datetime
    finishedAt: datetime | None
    status: str
    stocksProcessed: int
    stocksUpdated: int
    errorMessage: str | None
    source: str | None


class SyncLogListData(BaseModel):
    items: list[SyncLogItem]