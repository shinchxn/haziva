from datetime import datetime, timezone

SUPPORTED_HAZARDS = {"landslide"}


def predict_risk(habitation_id: str, features: dict[str, float], hazard_type: str = "landslide"):
    if not habitation_id:
        raise ValueError("Habitation id is required.")
    if not features:
        raise ValueError("Prediction features payload is required.")

    if hazard_type.lower() not in SUPPORTED_HAZARDS:
        raise ValueError(
            f"Hazard type '{hazard_type}' is not supported yet. "
            f"The currently implemented hazard module is 'landslide'."
        )


    slope = float(features.get("slope", 0.5))
    rainfall = float(features.get("rainfall", 0.5))
    forecast_rainfall = float(features.get("forecast_rainfall", 0.5))
    susceptibility = float(features.get("susceptibility", 0.5))
    population_exposure = float(features.get("population_exposure", 0.5))
    accessibility = float(features.get("accessibility", 0.5))

    risk = min(
        0.99,
        max(
            0.08,
            0.25 + 0.2 * slope + 0.2 * rainfall + 0.22 * forecast_rainfall + 0.18 * susceptibility + 0.12 * population_exposure + 0.08 * accessibility,
        ),
    )
    confidence = min(0.99, max(0.1, 0.3 + 0.45 * susceptibility + 0.1 * population_exposure + 0.1 * rainfall))

    drivers = []
    hazard_label = hazard_type.replace("_", " ").title()
    if susceptibility > 0.7:
        drivers.append(f"High {hazard_label.lower()} susceptibility")
    if rainfall > 0.75:
        drivers.append("High recent rainfall")
    if forecast_rainfall > 0.7:
        drivers.append("High forecast rainfall")
    if population_exposure > 0.6:
        drivers.append("High population exposure")
    if accessibility < 0.35:
        drivers.append("Limited evacuation accessibility")

    return {
        "risk": round(risk, 2),
        "confidence": round(confidence, 2),
        "drivers": drivers or ["Moderate terrain risk", "Rainfall accumulation observed"],
        "hazard_type": hazard_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
