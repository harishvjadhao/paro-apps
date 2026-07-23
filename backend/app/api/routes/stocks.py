from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.stock import Stock
from app.models.stock_comment import StockComment
from app.schemas.common import ApiResponse
from app.schemas.stocks import (
    StockCommentCreateRequest,
    StockCommentItem,
    StockCommentListData,
    StockCommentUpdateRequest,
    StockDetailData,
    StockListData,
    StockPreferenceRequest,
    StockReorderRequest,
    StockTimelineData,
)
from app.services.stock_queries import get_stock_comments, get_stock_detail, get_stock_list, get_stock_timeline


router = APIRouter(prefix="/stocks")


@router.get("", response_model=ApiResponse[StockListData])
def list_stocks(db: Session = Depends(get_db)) -> ApiResponse[StockListData]:
    items = get_stock_list(db)
    return ApiResponse(success=True, data=StockListData(items=items, total=len(items)), message="Stocks fetched successfully")


@router.get("/{symbol}", response_model=ApiResponse[StockDetailData])
def get_stock(symbol: str, db: Session = Depends(get_db)) -> ApiResponse[StockDetailData]:
    stock = get_stock_detail(db, symbol)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    return ApiResponse(success=True, data=StockDetailData(**stock), message="Stock details fetched successfully")


@router.get("/{symbol}/timeline", response_model=ApiResponse[StockTimelineData])
def get_stock_price_timeline(symbol: str, db: Session = Depends(get_db)) -> ApiResponse[StockTimelineData]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    items = get_stock_timeline(db, symbol)
    return ApiResponse(success=True, data=StockTimelineData(items=items), message="Stock timeline fetched successfully")


@router.get("/{symbol}/comments", response_model=ApiResponse[StockCommentListData])
def list_stock_comments(symbol: str, db: Session = Depends(get_db)) -> ApiResponse[StockCommentListData]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    items = get_stock_comments(db, symbol)
    return ApiResponse(success=True, data=StockCommentListData(items=items), message="Stock comments fetched successfully")


@router.post("/{symbol}/comments", response_model=ApiResponse[StockCommentItem])
def create_stock_comment(
    symbol: str,
    payload: StockCommentCreateRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[StockCommentItem]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    comment_text = payload.comment.strip()
    if not comment_text:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    comment = StockComment(stock_id=stock.id, comment=comment_text)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return ApiResponse(
        success=True,
        data=StockCommentItem(id=comment.id, comment=comment.comment, createdAt=comment.created_at, updatedAt=comment.updated_at),
        message="Stock comment created successfully",
    )


@router.put("/{symbol}/comments/{comment_id}", response_model=ApiResponse[StockCommentItem])
def update_stock_comment(
    symbol: str,
    comment_id: int,
    payload: StockCommentUpdateRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[StockCommentItem]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    comment = db.scalar(select(StockComment).where(StockComment.id == comment_id, StockComment.stock_id == stock.id))
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    comment_text = payload.comment.strip()
    if not comment_text:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    comment.comment = comment_text
    db.commit()
    db.refresh(comment)

    return ApiResponse(
        success=True,
        data=StockCommentItem(id=comment.id, comment=comment.comment, createdAt=comment.created_at, updatedAt=comment.updated_at),
        message="Stock comment updated successfully",
    )


@router.delete("/{symbol}/comments/{comment_id}", response_model=ApiResponse[dict])
def delete_stock_comment(
    symbol: str,
    comment_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    comment = db.scalar(select(StockComment).where(StockComment.id == comment_id, StockComment.stock_id == stock.id))
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")

    db.delete(comment)
    db.commit()

    return ApiResponse(success=True, data={"deleted": True}, message="Stock comment deleted successfully")


@router.post("/{symbol}/favorite", response_model=ApiResponse[StockDetailData])
def set_favorite(
    symbol: str,
    payload: StockPreferenceRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[StockDetailData]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    stock.is_favorite = payload.value
    db.commit()
    db.refresh(stock)

    detail = get_stock_detail(db, symbol)
    return ApiResponse(success=True, data=StockDetailData(**detail), message="Favorite updated successfully")


@router.post("/{symbol}/watchlist", response_model=ApiResponse[StockDetailData])
def set_watchlist(
    symbol: str,
    payload: StockPreferenceRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[StockDetailData]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    stock.in_watchlist = payload.value
    db.commit()
    db.refresh(stock)

    detail = get_stock_detail(db, symbol)
    return ApiResponse(success=True, data=StockDetailData(**detail), message="Watchlist updated successfully")


@router.post("/reorder", response_model=ApiResponse[StockListData])
def reorder_stocks(
    payload: StockReorderRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[StockListData]:
    symbol_to_rank = {item.symbol: item.manualRank for item in payload.items}
    stocks = db.scalars(select(Stock).where(Stock.symbol.in_(symbol_to_rank.keys()))).all()

    for stock in stocks:
        stock.manual_rank = symbol_to_rank[stock.symbol]

    db.commit()

    items = get_stock_list(db)
    return ApiResponse(success=True, data=StockListData(items=items, total=len(items)), message="Stock order updated successfully")