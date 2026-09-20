from sqlalchemy.orm import Session

try:
    from backend.app.models.relocation_site import RelocationSite
    HAS_ORM_MODELS = True
except ImportError:
    RelocationSite = None
    HAS_ORM_MODELS = False

from backend.app.services.habitation_service import get_habitation


def get_relocation_sites(
    habitation_id: str,
    db: Session | None = None,
    sim_priority: str | None = None,
    sim_risk: float | None = None,
):
    habitation = get_habitation(habitation_id, db=db)
    if not habitation:
        return {"habitation_id": habitation_id, "sites": [], "status": "NO_DATA", "message": f"Habitation '{habitation_id}' not found."}

    target_hab_id = habitation["id"]

    if HAS_ORM_MODELS and db is not None:
        try:
            db_sites = db.query(RelocationSite).filter(RelocationSite.habitation_id == target_hab_id).all()
            if db_sites:
                sites = []
                for s in db_sites:
                    base_score = float(getattr(s, "transparent_priority_score", 0.5) or 0.5)
                    safety_val = s.safety_result or "INSUFFICIENT_EVIDENCE"
                    capacity_val = s.capacity
                    cap_status = getattr(s, "capacity_status", "HEURISTIC") or "HEURISTIC"
                    access_val = s.accessibility or "NEAREST_OSM_ROAD_AVAILABLE"

                    if sim_risk is not None:
                        # Re-weight score under simulated origin risk without altering DB
                        v_norm = min(1.0, max(0.0, float(sim_risk)))
                        calc_score = round(0.35 * v_norm + 0.65 * base_score, 4)
                        explanation = (
                            f"[SIMULATED SCENARIO] Candidate prioritized for simulated origin risk "
                            f"({sim_risk * 100:.0f}%, {sim_priority or 'Simulated'}). "
                            f"Candidate safety status: {safety_val}. "
                            f"Capacity ({capacity_val if capacity_val else 'Unverified'}) remains {cap_status}. "
                            f"Accessibility: {access_val}."
                        )
                    else:
                        calc_score = base_score
                        explanation = getattr(s, "ranking_explanation", None) or "Candidate site subject to authority verification."

                    sites.append({
                        "site_id": s.site_id,
                        "name": getattr(s, "name", None) or f"Facility {s.site_id}",
                        "facility_category": getattr(s, "facility_category", None) or "community",
                        "status": s.status or "candidate",
                        "safety": safety_val,
                        "capacity": capacity_val,
                        "capacity_status": cap_status,
                        "accessibility": access_val,
                        "infrastructure": s.infrastructure_info or {
                            "water": {"status": "UNKNOWN", "source": None, "label": "Water Availability: Unknown — Verification Required"},
                            "shelter": {"status": "VERIFIED", "source": "OpenStreetMap", "label": "Public Shelter/Facility"},
                            "roads": {"status": "VERIFIED", "source": "OpenStreetMap proximity", "label": access_val}
                        },
                        "location": {"type": "Point", "coordinates": [float(s.longitude), float(s.latitude)]},
                        "latitude": float(s.latitude),
                        "longitude": float(s.longitude),
                        "rejection_reason": s.rejection_reason,
                        "transparent_priority_score": calc_score,
                        "ranking_explanation": explanation,
                    })

                # Sort by transparent priority score descending
                sites.sort(key=lambda x: x["transparent_priority_score"], reverse=True)
                return {"habitation_id": habitation_id, "sites": sites, "status": "OK", "message": None}
        except Exception as err:
            raise RuntimeError(f"Relocation candidate retrieval failed: {err}")

    return {
        "habitation_id": habitation_id,
        "sites": [],
        "status": "NO_DATA",
        "message": "No verified relocation candidates available for this habitation."
    }


