from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.schemas.risk import RiskProfile, TrajectoryResponse
from backend.app.services.habitation_service import get_habitation, get_risk_profile
from backend.app.services.ml_service import predict_risk
from backend.app.services.trajectory import calculate_trajectory

router = APIRouter(tags=["Risk"])


@router.get("/habitations/{habitation_id}/risk", response_model=RiskProfile)
def get_risk(habitation_id: str, db: Session = Depends(get_db)):
    if not get_habitation(habitation_id, db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitation '{habitation_id}' not found.",
        )
    return get_risk_profile(habitation_id, db=db)


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest):
    return predict_risk(
        payload.habitation_id,
        payload.features if isinstance(payload.features, dict) else payload.features.model_dump(),
        hazard_type=payload.hazard_type,
    )


@router.get("/habitations/{habitation_id}/trajectory", response_model=TrajectoryResponse)
def get_trajectory(habitation_id: str, db: Session = Depends(get_db)):
    if not get_habitation(habitation_id, db=db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitation '{habitation_id}' not found.",
        )
    profile = get_risk_profile(habitation_id, db=db)
    current_val = profile["current"] if isinstance(profile, dict) else profile.current
    risk_24h_val = profile["risk_24h"] if isinstance(profile, dict) else profile.risk_24h
    risk_72h_val = profile["risk_72h"] if isinstance(profile, dict) else profile.risk_72h

    state = calculate_trajectory(current_val, risk_24h_val, risk_72h_val)
    return {
        "habitation_id": habitation_id,
        "trajectory": state,
        "current": current_val,
        "risk_24h": risk_24h_val,
        "risk_72h": risk_72h_val,
        "hazard_type": "landslide",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
