from typing import Any
from sqlalchemy.orm import Session

from backend.app.services.habitation_service import get_habitation
from backend.app.services.ml_service import predict_risk
from backend.app.services.priority import calculate_priority
from backend.app.services.relocation_service import get_relocation_sites
from backend.app.services.trajectory import calculate_trajectory


def run_incident_simulation(
    habitation_id: str,
    simulated_rainfall_mm: float,
    horizon: str = "24h",
    db: Session | None = None,
) -> dict[str, Any]:
    """
    Execute a custom Incident Simulation ("What-If" scenario) for a selected habitation.
    Passes custom synthetic rainfall scenario through the production Model A ML inference pipeline.
    Strictly isolated: NEVER alters or overwrites baseline database state.
    """
    habitation = get_habitation(habitation_id, db=db)
    if not habitation:
        raise ValueError(f"Habitation '{habitation_id}' not found for incident simulation.")

    r_sim = max(0.0, float(simulated_rainfall_mm))
    horizon_clean = str(horizon).lower()

    base_current = float(habitation["current_risk"])
    base_24h = float(habitation["risk_24h"])
    base_72h = float(habitation["risk_72h"])
    base_priority = habitation.get("priority", "Not provided")
    base_trajectory = habitation.get("trajectory", "Stable")

    # Extract habitation terrain features for Model A inference
    exp_info = habitation.get("exposure_info", {})
    slope = float(exp_info.get("slope", 18.5))
    gsi_susceptibility = float(exp_info.get("gsi_susceptibility", base_current))

    # Construct dynamic rainfall feature payload based on simulation scenario & horizon
    if horizon_clean == "24h":
        obs_rain = r_sim
        fc_24h = r_sim
        fc_72h = r_sim * 1.3
    elif horizon_clean == "72h":
        obs_rain = r_sim * 0.4
        fc_24h = r_sim * 0.7
        fc_72h = r_sim
    else:
        obs_rain = r_sim
        fc_24h = r_sim * 1.1
        fc_72h = r_sim * 1.3

    feature_payload = {
        "slope_degrees": slope,
        "gsi_susceptibility": gsi_susceptibility,
        "susceptibility": base_current,
        "observed_rainfall_mm": obs_rain,
        "forecast_24h_mm": fc_24h,
        "forecast_72h_mm": fc_72h,
    }


    # Pass synthetic rainfall scenario through the EXACT production ML pipeline (Model A Random Forest)
    try:
        ml_prediction = predict_risk(habitation_id, feature_payload, hazard_type="landslide")
    except Exception as exc:
        raise RuntimeError(f"ML Model A inference failed during incident simulation: {exc}")

    sim_current = float(ml_prediction["risk"])
    sim_24h = float(ml_prediction["risk_24h"])
    sim_72h = float(ml_prediction["risk_72h"])
    susceptibility_proba = float(ml_prediction.get("susceptibility_proba", base_current))

    # Calculate simulated trajectory & priority using HAZIVA production logic
    sim_trajectory = calculate_trajectory(sim_current, sim_24h, sim_72h)
    exp_score = float(exp_info.get("score", 0.5))
    vuln_score = float(habitation.get("vulnerability_info", {}).get("score", 0.5))
    sim_priority = calculate_priority(sim_current, sim_72h, sim_trajectory, exp_score, vuln_score)

    # Re-evaluate relocation intelligence for real candidates under simulated origin risk
    try:
        relocation_res = get_relocation_sites(
            habitation_id,
            db=db,
            sim_priority=sim_priority,
            sim_risk=sim_current,
        )
        candidate_sites = relocation_res.get("sites", [])
    except Exception as exc:
        raise RuntimeError(f"Relocation evaluation failed during incident simulation: {exc}")

    drivers = [
        f"Synthetic rainfall scenario input: {r_sim:.1f} mm ({horizon_clean} window)",
        f"Model A terrain susceptibility probability: {susceptibility_proba:.2f}",
        f"Simulated trajectory: {sim_trajectory}",
        f"Simulated priority status: {sim_priority}",
    ]
    if ml_prediction.get("drivers"):
        drivers.extend([d for d in ml_prediction["drivers"] if d not in drivers])

    return {
        "is_simulation": True,
        "is_synthetic": True,
        "simulation_disclaimer": "SIMULATION — NOT OBSERVED DATA. Custom what-if scenario executed through trained Model A ML risk engine.",
        "habitation_id": habitation_id,
        "habitation_name": habitation["name"],
        "simulated_rainfall_mm": r_sim,
        "horizon": horizon_clean,
        "baseline": {
            "current_risk": base_current,
            "risk_24h": base_24h,
            "risk_72h": base_72h,
            "trajectory": base_trajectory,
            "priority": base_priority,
        },
        "simulation_result": {
            "current_risk": sim_current,
            "risk_24h": sim_24h,
            "risk_72h": sim_72h,
            "susceptibility_proba": susceptibility_proba,
            "trajectory": sim_trajectory,
            "priority": sim_priority,
            "confidence": 0.85,
            "confidence_reason": "Executed via trained Model A ML risk engine using custom simulated rainfall scenario.",
            "drivers": drivers,
        },
        "relocation": {
            "priority": sim_priority,
            "relocation_required": sim_current >= 0.60 or sim_priority in ["Immediate Assessment", "P1_CRITICAL", "P2_HIGH"],
            "urgency": "IMMEDIATE_EVACUATION" if sim_current >= 0.75 else ("ELEVATED_PREPAREDNESS" if sim_current >= 0.50 else "MONITORING"),
            "total_candidates": len(candidate_sites),
            "sites": candidate_sites,
        },
        "relocation_sites": candidate_sites,  # preserved for backwards compatibility
    }

