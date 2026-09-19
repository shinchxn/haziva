import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import get_db, get_engine, get_sessionmaker
from backend.app.database.seed import seed_database
from backend.app.main import app


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    engine = get_engine()
    SessionFactory = get_sessionmaker()
    db = SessionFactory()
    try:
        seed_database(db=db)
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def test_end_to_end_forward_pipeline(client):
    """
    Test the complete HAZIVA forward-prediction pipeline end-to-end:
    Real GIS data -> DB -> FastAPI -> /habitations -> /habitations/{id}/risk -> /trajectory -> /relocation
    """
    # 1. GET /habitations
    res_habs = client.get("/habitations")
    assert res_habs.status_code == 200, f"Failed /habitations: {res_habs.text}"
    habitations = res_habs.json()
    assert len(habitations) == 48, f"Expected 48 Wayanad habitations, got {len(habitations)}"

    test_hab = habitations[0]
    hab_id = test_hab["id"]
    assert "name" in test_hab
    assert "current_risk" in test_hab
    assert "priority" in test_hab

    # 2. GET /habitations/{id}
    res_detail = client.get(f"/habitations/{hab_id}")
    assert res_detail.status_code == 200, f"Failed /habitations/{hab_id}: {res_detail.text}"
    detail = res_detail.json()
    assert detail["id"] == hab_id
    assert detail["population"] > 0
    assert "exposure_info" in detail
    assert "vulnerability_info" in detail
    assert "accessibility_info" in detail

    # 3. GET /habitations/{id}/risk
    res_risk = client.get(f"/habitations/{hab_id}/risk")
    assert res_risk.status_code == 200, f"Failed /habitations/{hab_id}/risk: {res_risk.text}"
    risk = res_risk.json()
    assert 0.0 <= risk["current"] <= 1.0
    assert 0.0 <= risk["risk_24h"] <= 1.0
    assert 0.0 <= risk["risk_72h"] <= 1.0
    assert risk["confidence"] >= 0.7
    assert len(risk["drivers"]) > 0

    # 4. GET /habitations/{id}/trajectory
    res_traj = client.get(f"/habitations/{hab_id}/trajectory")
    assert res_traj.status_code == 200, f"Failed /habitations/{hab_id}/trajectory: {res_traj.text}"
    traj = res_traj.json()
    assert traj["habitation_id"] == hab_id
    assert traj["trajectory"].lower() in ["critical", "rapidly increasing", "increasing", "decreasing", "stable"]
    assert traj["risk_24h"] == risk["risk_24h"]

    # 5. GET /habitations/{id}/relocation for a habitation with candidate sites (e.g. hab_627327 Kalpetta)
    relo_hab_id = "hab_627327"
    res_relo = client.get(f"/habitations/{relo_hab_id}/relocation")
    assert res_relo.status_code == 200, f"Failed /habitations/{relo_hab_id}/relocation: {res_relo.text}"
    relo = res_relo.json()
    assert relo["habitation_id"] == relo_hab_id
    assert len(relo["sites"]) > 0

    first_site = relo["sites"][0]
    assert "site_id" in first_site
    assert "capacity" in first_site
    assert "safety" in first_site
    assert "status" in first_site
    assert "transparent_priority_score" in first_site
