from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.habitation import HabitationDetail, HabitationSummary
from backend.app.services.habitation_service import get_habitation, get_habitation_summaries

router = APIRouter(tags=["Habitations"])


@router.get("/habitations", response_model=list[HabitationSummary])
def list_habitations(db: Session = Depends(get_db)):
    del db
    return get_habitation_summaries()


@router.get("/habitations/{habitation_id}", response_model=HabitationDetail)
def read_habitation(habitation_id: str, db: Session = Depends(get_db)):
    del db
    habitation = get_habitation(habitation_id)
    if not habitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitation '{habitation_id}' not found.",
        )
    return habitation
