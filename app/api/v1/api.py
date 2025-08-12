from fastapi import APIRouter
from app.api.v1.endpoints import (
    candidates,
    interviews,
    pipeline,
    agents
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    candidates.router,
    prefix="/candidates",
    tags=["candidates"]
)

api_router.include_router(
    interviews.router,
    prefix="/interviews",
    tags=["interviews"]
)

api_router.include_router(
    pipeline.router,
    prefix="/pipeline",
    tags=["pipeline"]
)

api_router.include_router(
    agents.router,
    prefix="/agents",
    tags=["agents"]
) 
) 