import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_sessionmaker
from backend.app.models.habitation import Habitation
from backend.app.models.risk import Risk
from backend.app.models.relocation_site import RelocationSite

client = TestClient(app)


def test_incident_simulation_scenario_a_low_rainfall():
    """Scenario A: Low hypothetical rainfall (20mm)."""
    response = client.post(
        "/habitations/hab_627296/simulate",
        json={"simulated_rainfall_mm": 20.0, "horizon": "24h"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["is_simulation"] is True
    assert data["is_synthetic"] is True
    assert "SIMULATION — NOT OBSERVED DATA" in data["simulation_disclaimer"]
    assert data["habitation_id"] == "hab_627296"
    assert data["simulated_rainfall_mm"] == 20.0

    # Baseline & simulation structure
    assert "baseline" in data
    assert "simulation_result" in data
    assert "relocation" in data

    sim_res = data["simulation_result"]
    assert 0.0 <= sim_res["current_risk"] <= 1.0
    assert 0.0 <= sim_res["risk_24h"] <= 1.0
    assert 0.0 <= sim_res["risk_72h"] <= 1.0
    assert isinstance(sim_res["drivers"], list)
    assert any("Synthetic rainfall scenario input" in d for d in sim_res["drivers"])

    # Relocation candidates evaluation
    reloc = data["relocation"]
    assert isinstance(reloc["sites"], list)
    if reloc["sites"]:
        first_site = reloc["sites"][0]
        assert "site_id" in first_site
        assert first_site["safety"] in {"PASS", "FLAG", "INSUFFICIENT_EVIDENCE"}
        assert first_site["capacity_status"] in {"HEURISTIC", "ESTIMATED", "UNKNOWN", None}


def test_incident_simulation_scenario_b_moderate_rainfall():
    """Scenario B: Moderate hypothetical rainfall (100mm)."""
    response = client.post(
        "/habitations/hab_627296/simulate",
        json={"simulated_rainfall_mm": 100.0, "horizon": "24h"},
    )
    assert response.status_code == 200
    data = response.json()

    sim_res = data["simulation_result"]
    base_res = data["baseline"]

    # Moderate rainfall should scale risk above baseline
    assert sim_res["current_risk"] >= base_res["current_risk"]
    assert sim_res["risk_24h"] >= base_res["risk_24h"]


def test_incident_simulation_scenario_c_high_rainfall():
    """Scenario C: High hypothetical rainfall (250mm)."""
    response = client.post(
        "/habitations/hab_627296/simulate",
        json={"simulated_rainfall_mm": 250.0, "horizon": "24h"},
    )
    assert response.status_code == 200
    data = response.json()

    sim_res = data["simulation_result"]
    reloc = data["relocation"]

    # High rainfall should trigger high/critical simulated risk and urgency
    assert sim_res["current_risk"] > 0.50
    assert reloc["relocation_required"] is True
    assert reloc["urgency"] in {"IMMEDIATE_EVACUATION", "ELEVATED_PREPAREDNESS"}


def test_database_baseline_isolation():
    """
    CRITICAL ISOLATION TEST:
    Verify that running an incident simulation does NOT modify database baseline records.
    """
    SessionFactory = get_sessionmaker()
    db = SessionFactory()

    try:
        hab_id = "hab_627296"

        # Query baseline records BEFORE simulation
        hab_before = db.query(Habitation).filter(Habitation.id == hab_id).first()
        risk_before = db.query(Risk).filter(Risk.habitation_id == hab_id).first()

        orig_risk_current = risk_before.current_risk if risk_before else None
        orig_risk_24h = risk_before.risk_24h if risk_before else None
        orig_risk_72h = risk_before.risk_72h if risk_before else None

        # Execute high-impact simulation
        sim_response = client.post(
            f"/habitations/{hab_id}/simulate",
            json={"simulated_rainfall_mm": 350.0, "horizon": "24h"},
        )
        assert sim_response.status_code == 200

        # Query baseline records AFTER simulation
        db.expire_all()
        risk_after = db.query(Risk).filter(Risk.habitation_id == hab_id).first()

        # Assert baseline database records remain 100% UNCHANGED
        assert risk_after.current_risk == orig_risk_current
        assert risk_after.risk_24h == orig_risk_24h
        assert risk_after.risk_72h == orig_risk_72h

    finally:
        db.close()


def test_simulation_non_existent_habitation():
    """Verify 404 response when simulation is requested for unknown habitation ID."""
    response = client.post(
        "/habitations/non_existent_hab_id/simulate",
        json={"simulated_rainfall_mm": 100.0, "horizon": "24h"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
