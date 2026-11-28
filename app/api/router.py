from fastapi import APIRouter

from app.api.routes import (
    auth,
    clusters,
    dashboard,
    groups,
    learning,
    practice,
    questions,
    stories,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(clusters.router)
api_router.include_router(stories.router)
api_router.include_router(groups.router)
api_router.include_router(questions.router)
api_router.include_router(practice.router)
api_router.include_router(learning.router)
api_router.include_router(dashboard.router)
