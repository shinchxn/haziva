from backend.app.services.habitation_service import get_habitation


def get_relocation_sites(habitation_id: str):
    habitation = get_habitation(habitation_id)
    if not habitation:
        return {"habitation_id": habitation_id, "sites": []}

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
