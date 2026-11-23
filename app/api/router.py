from fastapi import APIRouter

from app.api.routes import auth, dashboard, learning, practice, questions

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(questions.router)
api_router.include_router(practice.router)
api_router.include_router(learning.router)
api_router.include_router(dashboard.router)
