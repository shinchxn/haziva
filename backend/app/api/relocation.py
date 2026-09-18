from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.relocation import RelocationProfile
from backend.app.services.habitation_service import get_habitation
from backend.app.services.relocation_service import get_relocation_sites

router = APIRouter(tags=["Relocation"])


@router.get("/habitations/{habitation_id}/relocation", response_model=RelocationProfile)
def get_habitation_relocation(habitation_id: str, db: Session = Depends(get_db)):
    del db
    if not get_habitation(habitation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habitation '{habitation_id}' not found.",
        )
    return get_relocation_sites(habitation_id)
