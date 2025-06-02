from fastapi import APIRouter
from app.config import settings

from app.api.auth import router as auth_router
from app.api.subscription import router as subscription_router
from app.api.agents import router as agents_router
from app.api.portfolio import router as portfolio_router

# Create the main API router
api_router = APIRouter(prefix=settings.API_PREFIX)

# Include all sub-routers
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    subscription_router,
    prefix="/subscription",
    tags=["Subscription"]
)

api_router.include_router(
    agents_router,
    prefix="/agents",
    tags=["Agents"]
)

api_router.include_router(
    portfolio_router,
    prefix="/portfolio",
    tags=["Portfolio"]
) 