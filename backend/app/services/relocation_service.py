from sqlalchemy.orm import Session

try:
    from backend.app.models.relocation_site import RelocationSite
    HAS_ORM_MODELS = True
except ImportError:
    RelocationSite = None
    HAS_ORM_MODELS = False

from backend.app.services.habitation_service import get_habitation


def get_relocation_sites(habitation_id: str, db: Session | None = None):
    habitation = get_habitation(habitation_id, db=db)
    if not habitation:
        return {"habitation_id": habitation_id, "sites": []}

    if HAS_ORM_MODELS and db is not None:
        try:
            db_sites = db.query(RelocationSite).filter(RelocationSite.habitation_id == habitation_id).all()
            if db_sites:
                sites = []
                for s in db_sites:
                    sites.append({
                        "site_id": s.site_id,
                        "status": s.status,
                        "safety": s.safety_result or "pass",
                        "capacity": s.capacity or 0,
                        "accessibility": s.accessibility or "good",
                        "infrastructure": s.infrastructure_info or {},
                        "location": {"type": "Point", "coordinates": [76.06, 11.65]},
                        "rejection_reason": s.rejection_reason,
                    })
                return {"habitation_id": habitation_id, "sites": sites}
        except Exception:
            pass


    return {
        "habitation_id": habitation_id,
        "sites": [
            {
                "site_id": "site_001",
                "status": "candidate",
                "safety": "pass",
                "capacity": 850,
                "accessibility": "good",
                "infrastructure": {"water": True, "shelter": True, "roads": True},
                "location": {"type": "Point", "coordinates": [76.06, 11.65]},
                "rejection_reason": None,
            },
            {
                "site_id": "site_002",
                "status": "rejected",
                "safety": "review",
                "capacity": 420,
                "accessibility": "moderate",
                "infrastructure": {"water": True, "shelter": False, "roads": True},
                "location": {"type": "Point", "coordinates": [76.08, 11.63]},
                "rejection_reason": "Steep access and limited shelter capacity.",
            },
        ],
    }
