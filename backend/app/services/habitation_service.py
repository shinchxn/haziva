from datetime import datetime, timezone
from sqlalchemy.orm import Session

try:
    from backend.app.models.habitation import Habitation
    from backend.app.models.risk import Risk
    HAS_ORM_MODELS = True
except ImportError:
    Habitation = None
    Risk = None
    HAS_ORM_MODELS = False

from backend.app.services.priority import calculate_priority
from backend.app.services.trajectory import calculate_trajectory


HABITATIONS = [
    {
        "id": "hab_001",
        "name": "Habitation A",
        "location": {
            "type": "Point",
            "coordinates": [76.0, 11.6]
        },
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
        "location": {
            "type": "Point",
            "coordinates": [76.08, 11.62]
        },
        "population": 900,
        "households": 190,
        "exposure_info": {
            "landslide_susceptibility": "Medium",
            "population_exposure": "Medium",
            "score": 0.55
        },
        "vulnerability_info": {
            "socioeconomic_vulnerability": "Low",
            "health_access": "Moderate",
            "score": 0.42
        },
        "accessibility_info": {
            "road_access": "Good",
            "evacuation_route": "Stable",
            "score": 0.35
        },
        "current_risk": 0.42,
        "risk_24h": 0.55,
        "risk_72h": 0.58,
        "confidence": 0.69,
        "drivers": [
            "Moderate susceptibility",
            "Accumulated rainfall",
            "Moderate terrain slope"
        ],
    },
]


def get_habitation(
    habitation_id: str,
    db: Session | None = None,
    hazard_type: str = "landslide"
):
    if HAS_ORM_MODELS and db is not None:
        try:
            db_hab = (
                db.query(Habitation)
                .filter(Habitation.id == habitation_id)
                .first()
            )

            if db_hab:
                risk_profile = get_risk_profile(
                    habitation_id,
                    db=db,
                    hazard_type=hazard_type
                )

                trajectory = calculate_trajectory(
                    risk_profile["current"],
                    risk_profile["risk_24h"],
                    risk_profile["risk_72h"],
                )

                exp_score = (
                    db_hab.exposure_info.get("score", 0.5)
                    if db_hab.exposure_info
                    else 0.5
                )

                vuln_score = (
                    db_hab.vulnerability_info.get("score", 0.5)
                    if db_hab.vulnerability_info
                    else 0.5
                )

                priority = calculate_priority(
                    risk_profile["current"],
                    risk_profile["risk_72h"],
                    trajectory,
                    exp_score,
                    vuln_score,
                )

                return {
                    "id": db_hab.id,
                    "name": db_hab.name,

                    # FIXED: use actual database coordinates
                    "location": {
                        "type": "Point",
                        "coordinates": [
                            float(db_hab.longitude),
                            float(db_hab.latitude)
                        ]
                    },

                    "latitude": float(db_hab.latitude),
                    "longitude": float(db_hab.longitude),

                    "population": db_hab.population or 0,
                    "households": db_hab.households or 0,
                    "exposure_info": db_hab.exposure_info or {},
                    "vulnerability_info": db_hab.vulnerability_info or {},
                    "accessibility_info": db_hab.accessibility_info or {},

                    "current_risk": risk_profile["current"],
                    "risk_24h": risk_profile["risk_24h"],
                    "risk_72h": risk_profile["risk_72h"],
                    "confidence": risk_profile["confidence"],
                    "priority": priority,
                    "trajectory": trajectory,
                }

        except Exception:
            pass

    for habitation in HABITATIONS:
        if habitation["id"] == habitation_id:

            risk_profile = get_risk_profile(
                habitation_id,
                db=db,
                hazard_type=hazard_type
            )

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


def get_habitation_summaries(
    db: Session | None = None,
    hazard_type: str = "landslide"
):
    summaries = []

    if HAS_ORM_MODELS and db is not None:
        try:
            db_habitations = db.query(Habitation).all()

            for db_hab in db_habitations:
                risk_profile = get_risk_profile(
                    db_hab.id,
                    db=db,
                    hazard_type=hazard_type
                )

                trajectory = calculate_trajectory(
                    risk_profile["current"],
                    risk_profile["risk_24h"],
                    risk_profile["risk_72h"],
                )

                exp_score = (
                    db_hab.exposure_info.get("score", 0.5)
                    if db_hab.exposure_info
                    else 0.5
                )

                vuln_score = (
                    db_hab.vulnerability_info.get("score", 0.5)
                    if db_hab.vulnerability_info
                    else 0.5
                )

                priority = calculate_priority(
                    risk_profile["current"],
                    risk_profile["risk_72h"],
                    trajectory,
                    exp_score,
                    vuln_score,
                )

                summaries.append({
                    "id": db_hab.id,
                    "name": db_hab.name,

                    # FIXED: actual database coordinates
                    "latitude": float(db_hab.latitude),
                    "longitude": float(db_hab.longitude),

                    "priority": priority,
                    "current_risk": risk_profile["current"],
                })

            if summaries:
                return summaries

        except Exception:
            pass

    for habitation in HABITATIONS:
        risk_profile = get_risk_profile(
            habitation["id"],
            db=db,
            hazard_type=hazard_type
        )

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


def get_risk_profile(
    habitation_id: str,
    db: Session | None = None,
    hazard_type: str = "landslide"
):
    if HAS_ORM_MODELS and db is not None:
        try:
            db_risk = (
                db.query(Risk)
                .filter(
                    Risk.habitation_id == habitation_id,
                    Risk.hazard_type == hazard_type
                )
                .order_by(Risk.timestamp.desc())
                .first()
            )

            if db_risk:
                return {
                    "current": db_risk.current_risk,
                    "risk_24h": db_risk.risk_24h,
                    "risk_72h": db_risk.risk_72h,
                    "confidence": db_risk.confidence,
                    "drivers": db_risk.drivers or [],
                }

        except Exception:
            pass

    for habitation in HABITATIONS:
        if habitation["id"] == habitation_id:
            return {
                "current": habitation["current_risk"],
                "risk_24h": habitation["risk_24h"],
                "risk_72h": habitation["risk_72h"],
                "confidence": habitation["confidence"],
                "drivers": habitation["drivers"],
            }

    return {
        "current": 0.0,
        "risk_24h": 0.0,
        "risk_72h": 0.0,
        "confidence": 0.0,
        "drivers": [],
    }

