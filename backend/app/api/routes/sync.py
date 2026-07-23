from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.sync_log import SyncLog
from app.schemas.common import ApiResponse
from app.schemas.sync import SyncLogItem, SyncLogListData, SyncStatusData
from app.services.sync_service import get_latest_sync_status, run_sync


router = APIRouter(prefix="/sync")


@router.post("", response_model=ApiResponse[SyncStatusData])
def trigger_sync(db: Session = Depends(get_db)) -> ApiResponse[SyncStatusData]:
    result = run_sync(db, source="api")
    data = SyncStatusData(
        status=result.status,
        lastSuccessfulSyncAt=result.last_successful_sync_at,
        lastSyncStartedAt=result.last_sync_started_at,
        stocksProcessed=result.stocks_processed,
        stocksUpdated=result.stocks_updated,
        errorMessage=result.error_message,
    )
    return ApiResponse(success=result.status != "failed", data=data, message="Sync executed")


@router.get("/status", response_model=ApiResponse[SyncStatusData])
def sync_status(db: Session = Depends(get_db)) -> ApiResponse[SyncStatusData]:
    result = get_latest_sync_status(db)
    data = SyncStatusData(
        status=result.status,
        lastSuccessfulSyncAt=result.last_successful_sync_at,
        lastSyncStartedAt=result.last_sync_started_at,
        stocksProcessed=result.stocks_processed,
        stocksUpdated=result.stocks_updated,
        errorMessage=result.error_message,
    )
    return ApiResponse(success=True, data=data, message="Sync status fetched successfully")


@router.get("/logs", response_model=ApiResponse[SyncLogListData])
def sync_logs(db: Session = Depends(get_db)) -> ApiResponse[SyncLogListData]:
    logs = db.scalars(select(SyncLog).order_by(SyncLog.started_at.desc()).limit(20)).all()
    items = [
        SyncLogItem(
            id=log.id,
            startedAt=log.started_at,
            finishedAt=log.finished_at,
            status=log.status,
            stocksProcessed=log.stocks_processed,
            stocksUpdated=log.stocks_updated,
            errorMessage=log.error_message,
            source=log.source,
        )
        for log in logs
    ]
    return ApiResponse(success=True, data=SyncLogListData(items=items), message="Sync logs fetched successfully")