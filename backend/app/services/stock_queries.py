from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.models.stock import Stock
from app.models.stock_comment import StockComment
from app.models.stock_indicator import StockIndicator
from app.models.stock_price_history import StockPriceHistory


def get_stock_list(db: Session) -> list[dict]:
    latest_price_subquery = (
        select(
            StockPriceHistory.stock_id.label("stock_id"),
            func.max(StockPriceHistory.trade_date).label("max_trade_date"),
        )
        .group_by(StockPriceHistory.stock_id)
        .subquery()
    )

    price_subquery = (
        select(StockPriceHistory)
        .join(
            latest_price_subquery,
            (StockPriceHistory.stock_id == latest_price_subquery.c.stock_id)
            & (StockPriceHistory.trade_date == latest_price_subquery.c.max_trade_date),
        )
        .subquery()
    )

    latest_indicator_subquery = (
        select(
            StockIndicator.stock_id.label("stock_id"),
            func.max(StockIndicator.as_of_date).label("max_as_of_date"),
        )
        .group_by(StockIndicator.stock_id)
        .subquery()
    )

    indicator_subquery = (
        select(StockIndicator)
        .join(
            latest_indicator_subquery,
            (StockIndicator.stock_id == latest_indicator_subquery.c.stock_id)
            & (StockIndicator.as_of_date == latest_indicator_subquery.c.max_as_of_date),
        )
        .subquery()
    )

    query = (
        select(
            Stock,
            price_subquery.c.close_price,
            indicator_subquery.c.moving_average_44,
            indicator_subquery.c.is_above_44_ma,
            indicator_subquery.c.percent_above_44_ma,
        )
        .outerjoin(price_subquery, Stock.id == price_subquery.c.stock_id)
        .outerjoin(indicator_subquery, Stock.id == indicator_subquery.c.stock_id)
        .order_by(
            Stock.industry.asc(),
            case((Stock.is_favorite.is_(True), 0), else_=1),
            case((Stock.in_watchlist.is_(True), 0), else_=1),
            case((indicator_subquery.c.is_above_44_ma.is_(True), 0), else_=1),
            Stock.manual_rank.asc().nulls_last(),
            Stock.company_name.asc(),
        )
    )

    items = []
    for stock, close_price, moving_average_44, is_above_44_ma, percent_above_44_ma in db.execute(query).all():
        items.append(
            {
                "symbol": stock.symbol,
                "companyName": stock.company_name,
                "industry": stock.industry,
                "closePrice": close_price,
                "movingAverage44": moving_average_44,
                "isAbove44MA": bool(is_above_44_ma or False),
                "percentAbove44MA": percent_above_44_ma,
                "isFavorite": stock.is_favorite,
                "inWatchlist": stock.in_watchlist,
                "manualRank": stock.manual_rank,
            }
        )

    return items


def get_stock_detail(db: Session, symbol: str) -> dict | None:
    latest_price = (
        select(StockPriceHistory)
        .join(Stock, Stock.id == StockPriceHistory.stock_id)
        .where(Stock.symbol == symbol)
        .order_by(desc(StockPriceHistory.trade_date))
        .limit(1)
    )

    latest_indicator = (
        select(StockIndicator)
        .join(Stock, Stock.id == StockIndicator.stock_id)
        .where(Stock.symbol == symbol)
        .order_by(desc(StockIndicator.as_of_date))
        .limit(1)
    )

    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    price = db.scalar(latest_price)
    indicator = db.scalar(latest_indicator)
    if stock is None:
        return None

    return {
        "symbol": stock.symbol,
        "companyName": stock.company_name,
        "industry": stock.industry,
        "series": stock.series,
        "isinCode": stock.isin_code,
        "yahooTicker": stock.yahoo_ticker,
        "closePrice": price.close_price if price else None,
        "movingAverage44": indicator.moving_average_44 if indicator else None,
        "isAbove44MA": indicator.is_above_44_ma if indicator else False,
        "percentAbove44MA": indicator.percent_above_44_ma if indicator else None,
        "isFavorite": stock.is_favorite,
        "inWatchlist": stock.in_watchlist,
        "lastUpdatedAt": indicator.updated_at if indicator else None,
    }


def get_stock_comments(db: Session, symbol: str) -> list[dict]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        return []

    comments = db.scalars(
        select(StockComment)
        .where(StockComment.stock_id == stock.id)
        .order_by(StockComment.created_at.desc(), StockComment.id.desc())
    ).all()

    return [
        {
            "id": comment.id,
            "comment": comment.comment,
            "createdAt": comment.created_at,
            "updatedAt": comment.updated_at,
        }
        for comment in comments
    ]


def get_stock_timeline(db: Session, symbol: str, limit: int = 100) -> list[dict]:
    stock = db.scalar(select(Stock).where(Stock.symbol == symbol))
    if stock is None:
        return []

    history_rows = db.execute(
        select(StockPriceHistory, StockIndicator)
        .outerjoin(
            StockIndicator,
            (StockIndicator.stock_id == StockPriceHistory.stock_id)
            & (StockIndicator.as_of_date == StockPriceHistory.trade_date),
        )
        .where(
            StockPriceHistory.stock_id == stock.id,
        )
        .order_by(StockPriceHistory.trade_date.desc())
        .limit(limit)
    ).all()

    history = list(history_rows)

    history.reverse()

    return [
        {
            "tradeDate": price_item.trade_date,
            "openPrice": price_item.open_price,
            "highPrice": price_item.high_price,
            "lowPrice": price_item.low_price,
            "closePrice": price_item.close_price,
            "volume": price_item.volume,
            "movingAverage44": indicator_item.moving_average_44 if indicator_item else None,
        }
        for price_item, indicator_item in history
    ]