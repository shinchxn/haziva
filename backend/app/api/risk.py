from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.schemas.risk import RiskProfile
from backend.app.services.habitation_service import get_habitation, get_risk_profile
from backend.app.services.ml_service import predict_risk
from backend.app.services.trajectory import calculate_trajectory

router = APIRouter(tags=["Risk"])


@router.get("/habitations/{habitation_id}/risk", response_model=RiskProfile)
def get_risk(habitation_id: str, db: Session = Depends(get_db)):
    del db
    if not get_habitation(habitation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitation '{habitation_id}' not found.",
        )
    return get_risk_profile(habitation_id)


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    return predict_risk(payload.habitation_id, payload.features)


@router.get("/habitations/{habitation_id}/trajectory")
def get_trajectory(habitation_id: str, db: Session = Depends(get_db)):
    del db
    if not get_habitation(habitation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitation '{habitation_id}' not found.",
        )
    profile = get_risk_profile(habitation_id)
    state = calculate_trajectory(
        profile.current,
        profile.risk_24h,
        profile.risk_72h,
    )
    return {
        "habitation_id": habitation_id,
        "state": state,
        "trajectory": state,
        "current": profile.current,
        "risk_24h": profile.risk_24h,
        "risk_72h": profile.risk_72h,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
