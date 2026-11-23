from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.progress import DashboardRead
from app.services.progress import build_dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardRead)
def dashboard(db: DbSession, user: CurrentUser):
    """Overview of the learner's activity, band trend, weaknesses and recent sessions."""
    return build_dashboard(db, user.id)
