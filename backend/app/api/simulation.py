from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.simulation_service import run_incident_simulation

router = APIRouter(tags=["Incident Simulation"])


class SimulationRequest(BaseModel):
    simulated_rainfall_mm: float = Field(..., ge=0.0, description="Simulated rainfall in millimeters")
    horizon: str = Field(default="24h", description="Forecast horizon window (24h or 72h)")


@router.post("/habitations/{habitation_id}/simulate")
def simulate_habitation_incident(
    habitation_id: str,
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    """
    Execute a custom Incident Simulation ("What-If" scenario) for a selected habitation.
    Passes custom rainfall input through the exact backend Model A risk engine.
    Strictly isolated: does NOT persist or mutate database state.
    """
    try:
        return run_incident_simulation(
            habitation_id,
            simulated_rainfall_mm=payload.simulated_rainfall_mm,
            horizon=payload.horizon,
            db=db,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Incident simulation failed: {exc}",
        )
