"""API v1版本"""

from fastapi import APIRouter
from backend.api.v1.endpoints import movies, health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(movies.router, prefix="/movies", tags=["movies"])

