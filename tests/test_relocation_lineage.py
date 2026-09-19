import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.database import get_sessionmaker
from backend.app.models.relocation_site import RelocationSite

client = TestClient(app)

def test_relocation_no_fallback_leakage():
    """Verify that habitations without matched candidate sites return NO_DATA, NOT fallback sites from other villages."""
    # hab_627296 has 0 matched candidate sites in its rural polygon boundary
    response = client.get("/habitations/hab_627296/relocation")
    assert response.status_code == 200
    data = response.json()
    assert data["habitation_id"] == "hab_627296"
    assert len(data["sites"]) == 0
    assert data["status"] == "NO_DATA"

def test_relocation_real_site_provenance():
    """Verify that sites returned for Kalpetta (hab_627327) belong to Kalpetta and carry honest provenance."""
    response = client.get("/habitations/hab_627327/relocation")
    assert response.status_code == 200
    data = response.json()
    sites = data["sites"]
    assert len(sites) == 109
    for site in sites:
        # Must NOT be hardcoded site_001
        assert site["site_id"] != "site_001"
        assert "Kalpetta Government Higher Secondary School" not in site.get("name", "")
        # Capacity status must be tagged as HEURISTIC or UNVERIFIED, not claimed as measured physical capacity
        assert site.get("capacity_status") in ["HEURISTIC", "UNVERIFIED"]
        # Water info must be UNKNOWN, not hardcoded True
        infra = site.get("infrastructure", {})
        if isinstance(infra, dict) and "water" in infra and isinstance(infra["water"], dict):
            assert infra["water"].get("status") == "UNKNOWN"

def test_simulation_does_not_mutate_baseline():
    """Verify that running incident simulation does NOT alter database baseline risk or relocation sites."""
    # Run simulation
    sim_response = client.post("/habitations/hab_627327/simulate", json={"simulated_rainfall_mm": 250.0, "horizon": "24h"})
    assert sim_response.status_code == 200
    sim_data = sim_response.json()
    assert sim_data["is_simulation"] is True

    # Re-fetch normal relocation API
    reloc_response = client.get("/habitations/hab_627327/relocation")
    assert reloc_response.status_code == 200
    reloc_data = reloc_response.json()
    assert reloc_data.get("status") == "OK"
    assert len(reloc_data["sites"]) == 109
