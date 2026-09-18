from datetime import datetime, timezone


def predict_risk(habitation_id: str, features: dict[str, float]):
    if not habitation_id:
        raise ValueError("Habitation id is required.")
    if not features:
        raise ValueError("Prediction features payload is required.")

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
    if susceptibility > 0.7:
        drivers.append("High landslide susceptibility")
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
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
