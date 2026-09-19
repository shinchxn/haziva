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

    target_hab_id = habitation["id"]

    if HAS_ORM_MODELS and db is not None:
        try:
            db_sites = db.query(RelocationSite).filter(RelocationSite.habitation_id == target_hab_id).all()
            if db_sites:
                sites = []
                for s in db_sites:
                    sites.append({
                        "site_id": s.site_id,
                        "name": getattr(s, "name", None) or f"Facility {s.site_id}",
                        "facility_category": getattr(s, "facility_category", None) or "shelter",
                        "status": s.status or "candidate",
                        "safety": s.safety_result or "INSUFFICIENT_EVIDENCE",
                        "capacity": s.capacity,
                        "capacity_status": getattr(s, "capacity_status", "HEURISTIC"),
                        "accessibility": s.accessibility or "NEAREST_OSM_ROAD_AVAILABLE",
                        "infrastructure": s.infrastructure_info or {
                            "water": {"status": "UNKNOWN", "source": None},
                            "shelter": {"status": "VERIFIED", "source": "OpenStreetMap"},
                            "roads": {"status": "VERIFIED", "source": "OpenStreetMap proximity"}
                        },
                        "location": {"type": "Point", "coordinates": [float(s.longitude), float(s.latitude)]},
                        "latitude": float(s.latitude),
                        "longitude": float(s.longitude),
                        "rejection_reason": s.rejection_reason,
                        "transparent_priority_score": getattr(s, "transparent_priority_score", 0.5),
                        "ranking_explanation": getattr(s, "ranking_explanation", "Candidate site subject to authority verification."),
                    })
                return {"habitation_id": habitation_id, "sites": sites, "status": "OK", "message": None}
        except Exception as err:
            pass

    return {
        "habitation_id": habitation_id,
        "sites": [],
        "status": "NO_DATA",
        "message": "No verified relocation candidates available for this habitation."
    }

