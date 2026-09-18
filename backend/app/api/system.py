from fastapi import APIRouter

from backend.app.schemas.system import SystemStatus
from backend.app.services.system_service import get_system_status

router = APIRouter(tags=["System"])


@router.get("/system/status", response_model=SystemStatus)
def system_status():
    return get_system_status()
