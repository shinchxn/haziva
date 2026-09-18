from backend.app.services.priority import calculate_priority
from backend.app.services.trajectory import calculate_trajectory


HABITATIONS = [
    {
        "id": "hab_001",
        "name": "Habitation A",
        "location": {"type": "Point", "coordinates": [76.0, 11.6]},
        "population": 1280,
        "households": 260,
        "exposure_info": {
            "landslide_susceptibility": "High",
            "population_exposure": "High",
            "score": 0.8,
        },
        "vulnerability_info": {
            "socioeconomic_vulnerability": "Moderate",
            "health_access": "Limited",
            "score": 0.7,
        },
        "accessibility_info": {
            "road_access": "Limited",
            "evacuation_route": "Risky",
            "score": 0.6,
        },
        "current_risk": 0.68,
        "risk_24h": 0.81,
        "risk_72h": 0.76,
        "confidence": 0.74,
        "drivers": [
            "High landslide susceptibility",
            "High recent rainfall",
            "High forecast rainfall",
        ],
    },
    {
        "id": "hab_002",
        "name": "Habitation B",
        "location": {"type": "Point", "coordinates": [76.08, 11.62]},
        "population": 900,
        "households": 190,
        "exposure_info": {"landslide_susceptibility": "Medium", "population_exposure": "Medium", "score": 0.55},
        "vulnerability_info": {"socioeconomic_vulnerability": "Low", "health_access": "Moderate", "score": 0.42},
        "accessibility_info": {"road_access": "Good", "evacuation_route": "Stable", "score": 0.35},
        "current_risk": 0.42,
        "risk_24h": 0.55,
        "risk_72h": 0.58,
        "confidence": 0.69,
        "drivers": ["Moderate susceptibility", "Accumulated rainfall", "Moderate terrain slope"],
    },
]


def get_habitation(habitation_id: str):
    for habitation in HABITATIONS:
        if habitation["id"] == habitation_id:
            risk_profile = get_risk_profile(habitation_id)
            trajectory = calculate_trajectory(
                risk_profile["current"],
                risk_profile["risk_24h"],
                risk_profile["risk_72h"],
            )
            priority = calculate_priority(
                risk_profile["current"],
                risk_profile["risk_72h"],
                trajectory,
                habitation["exposure_info"]["score"],
                habitation["vulnerability_info"]["score"],
            )
            return {
                **habitation,
                "latitude": habitation["location"]["coordinates"][1],
                "longitude": habitation["location"]["coordinates"][0],
                "current_risk": risk_profile["current"],
                "risk_24h": risk_profile["risk_24h"],
                "risk_72h": risk_profile["risk_72h"],
                "confidence": risk_profile["confidence"],
                "priority": priority,
                "trajectory": trajectory,
            }
    return None


def get_habitation_summaries():
    summaries = []
    for habitation in HABITATIONS:
        risk_profile = get_risk_profile(habitation["id"])
        trajectory = calculate_trajectory(
            risk_profile["current"],
            risk_profile["risk_24h"],
            risk_profile["risk_72h"],
        )
        priority = calculate_priority(
            risk_profile["current"],
            risk_profile["risk_72h"],
            trajectory,
            habitation["exposure_info"]["score"],
            habitation["vulnerability_info"]["score"],
        )
        summaries.append({
            "id": habitation["id"],
            "name": habitation["name"],
            "latitude": habitation["location"]["coordinates"][1],
            "longitude": habitation["location"]["coordinates"][0],
            "priority": priority,
            "current_risk": risk_profile["current"],
        })
    return summaries


def get_risk_profile(habitation_id: str):
    for habitation in HABITATIONS:
        if habitation["id"] == habitation_id:
            return {
                "current": habitation["current_risk"],
                "risk_24h": habitation["risk_24h"],
                "risk_72h": habitation["risk_72h"],
                "confidence": habitation["confidence"],
                "drivers": habitation["drivers"],
                "timestamp": "2026-09-18T10:00:00Z",
            }
    return None
