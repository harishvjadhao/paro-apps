from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chart_highlight_date import ChartHighlightDate
from app.schemas.common import ApiResponse
from app.schemas.stocks import ChartHighlightDateCreateRequest, ChartHighlightDateItem, ChartHighlightDateListData


router = APIRouter(prefix="/settings")


@router.get("/chart-highlights", response_model=ApiResponse[ChartHighlightDateListData])
def list_chart_highlights(db: Session = Depends(get_db)) -> ApiResponse[ChartHighlightDateListData]:
    items = db.scalars(select(ChartHighlightDate).order_by(ChartHighlightDate.highlight_date.asc())).all()
    return ApiResponse(
        success=True,
        data=ChartHighlightDateListData(
            items=[
                ChartHighlightDateItem(id=item.id, highlightDate=item.highlight_date, createdAt=item.created_at)
                for item in items
            ]
        ),
        message="Chart highlight dates fetched successfully",
    )


@router.post("/chart-highlights", response_model=ApiResponse[ChartHighlightDateItem])
def create_chart_highlight(
    payload: ChartHighlightDateCreateRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[ChartHighlightDateItem]:
    existing = db.scalar(select(ChartHighlightDate).where(ChartHighlightDate.highlight_date == payload.highlightDate))
    if existing is not None:
        raise HTTPException(status_code=400, detail="Highlight date already exists")

    item = ChartHighlightDate(highlight_date=payload.highlightDate)
    db.add(item)
    db.commit()
    db.refresh(item)

    return ApiResponse(
        success=True,
        data=ChartHighlightDateItem(id=item.id, highlightDate=item.highlight_date, createdAt=item.created_at),
        message="Chart highlight date created successfully",
    )


@router.delete("/chart-highlights/{highlight_id}", response_model=ApiResponse[dict])
def delete_chart_highlight(highlight_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict]:
    item = db.get(ChartHighlightDate, highlight_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Highlight date not found")

    db.delete(item)
    db.commit()

    return ApiResponse(success=True, data={"deleted": True}, message="Chart highlight date deleted successfully")