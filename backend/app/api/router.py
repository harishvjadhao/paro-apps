from fastapi import APIRouter

from app.api.routes import health
from app.api.routes import settings, stocks, sync


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(settings.router, tags=["settings"])
api_router.include_router(stocks.router, tags=["stocks"])
api_router.include_router(sync.router, tags=["sync"])