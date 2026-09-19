from typing import Any
from sqlalchemy.orm import Session

from backend.app.services.habitation_service import get_habitation
from backend.app.services.ml_service import calculate_rainfall_stress, predict_risk
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
    Run an Incident Simulation ("What-If" scenario) for a selected habitation.
    Scales risk dynamically from baseline using Model A dynamic rainfall stress.
    Strictly isolated: NEVER alters or overwrites real database records.
    """
    habitation = get_habitation(habitation_id, db=db)
    if not habitation:
        raise ValueError(f"Habitation '{habitation_id}' not found for incident simulation.")

    r_sim = max(0.0, float(simulated_rainfall_mm))
    horizon_clean = str(horizon).lower()

    base_current = float(habitation["current_risk"])
    base_24h = float(habitation["risk_24h"])
    base_72h = float(habitation["risk_72h"])

    # Calculate dynamic rainfall stress multiplier from Open-Meteo rainfall model
    stress_sim = calculate_rainfall_stress(r_sim)

    # Scale risk upward from baseline
    if horizon_clean == "24h":
        sim_current = round(min(1.0, max(base_current, base_current * (1.0 + 0.4 * stress_sim))), 4)
        sim_24h = round(min(1.0, max(base_24h, base_24h * (1.0 + 1.2 * stress_sim))), 4)
        sim_72h = round(min(1.0, max(base_72h, sim_24h * 1.1)), 4)
    elif horizon_clean == "72h":
        sim_current = round(min(1.0, max(base_current, base_current * (1.0 + 0.3 * stress_sim))), 4)
        sim_24h = round(min(1.0, max(base_24h, base_24h * (1.0 + 0.8 * stress_sim))), 4)
        sim_72h = round(min(1.0, max(base_72h, base_72h * (1.0 + 1.3 * stress_sim))), 4)
    else:
        sim_current = round(min(1.0, max(base_current, base_current * (1.0 + 1.2 * stress_sim))), 4)
        sim_24h = round(min(1.0, max(base_24h, sim_current * 1.1)), 4)
        sim_72h = round(min(1.0, max(base_72h, sim_24h * 1.1)), 4)

    sim_trajectory = calculate_trajectory(sim_current, sim_24h, sim_72h)

    exp_score = habitation.get("exposure_info", {}).get("score", 0.5)
    vuln_score = habitation.get("vulnerability_info", {}).get("score", 0.5)
    sim_priority = calculate_priority(sim_current, sim_72h, sim_trajectory, exp_score, vuln_score)

    relocation = get_relocation_sites(habitation_id, db=db)
    sites = relocation.get("sites", [])

    return {
        "is_simulation": True,
        "simulation_disclaimer": "SIMULATION — NOT OBSERVED DATA. Custom what-if scenario executed through Model A risk engine.",
        "habitation_id": habitation_id,
        "habitation_name": habitation["name"],
        "simulated_rainfall_mm": r_sim,
        "horizon": horizon_clean,
        "baseline": {
            "current_risk": base_current,
            "risk_24h": base_24h,
            "risk_72h": base_72h,
            "trajectory": habitation["trajectory"],
            "priority": habitation["priority"],
        },
        "simulation_result": {
            "current_risk": sim_current,
            "risk_24h": sim_24h,
            "risk_72h": sim_72h,
            "trajectory": sim_trajectory,
            "priority": sim_priority,
            "confidence": 0.85,
            "confidence_reason": "Executed via Model A risk engine using custom simulated rainfall scenario.",
            "drivers": [
                f"Simulated rainfall input: {r_sim:.1f} mm ({horizon_clean} window)",
                f"Rainfall stress scaling factor: S = {stress_sim:.3f}",
                f"Baseline susceptibility: {base_current:.2f}",
            ],
        },
        "relocation_sites": sites,
    }
