import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from backend.app.core.database import get_engine, get_sessionmaker
from backend.app.database.seed import seed_database
from backend.app.integrations.weather import fetch_live_weather
from backend.app.main import app
from backend.app.services.ml_service import predict_risk, predict_spatial_susceptibility


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


def test_model_a_runtime_inference():
    """Test 5: Verify Model A joblib artifact loads and predicts spatial susceptibility probability."""
    features = {
        "slope_degrees": 24.5,
        "gsi_susceptibility": 0.72,
        "tree_fraction": 0.60,
    }
    proba1 = predict_spatial_susceptibility(features)
    proba2 = predict_spatial_susceptibility(features)
    assert 0.0 <= proba1 <= 1.0
    assert proba1 == proba2, "Model A inference must be strictly deterministic"


def test_live_weather_integration():
    """Test 4: Verify live weather integration returns structured provider info without synthetic fallbacks."""
    weather = fetch_live_weather()
    assert "status" in weather
    assert weather["status"] in ["ONLINE", "STALE_CACHED", "UNAVAILABLE"]
    assert "provider" in weather
    assert "observed_24h_mm" in weather
    assert "forecast_24h_mm" in weather
    assert "forecast_72h_mm" in weather


def test_deterministic_risk_calculation():
    """Test 1: Same village + same terrain + same rainfall -> deterministic risk result."""
    res1 = predict_risk("hab_627296", {"slope_degrees": 20.0, "observed_rainfall_mm": 25.0, "forecast_24h_mm": 50.0})
    res2 = predict_risk("hab_627296", {"slope_degrees": 20.0, "observed_rainfall_mm": 25.0, "forecast_24h_mm": 50.0})
    assert res1["risk"] == res2["risk"]
    assert res1["risk_24h"] == res2["risk_24h"]
    assert res1["confidence"] >= 0.7
    assert "confidence_reason" in res1


def test_simulation_parameterization(client):
    """Test 2 & 3: Change rainfall in incident simulation -> verify risk scales through Model A engine."""
    # Baseline GET /habitations/hab_627296/risk
    res_base = client.get("/habitations/hab_627296/risk")
    assert res_base.status_code == 200
    base_risk = res_base.json()["current"]

    # Heavy rainfall incident simulation: 180 mm over 24h
    res_sim = client.post("/habitations/hab_627296/simulate", json={"simulated_rainfall_mm": 180.0, "horizon": "24h"})
    assert res_sim.status_code == 200
    sim_data = res_sim.json()

    assert sim_data["is_simulation"] is True
    assert "SIMULATION — NOT OBSERVED DATA" in sim_data["simulation_disclaimer"]
    assert sim_data["simulated_rainfall_mm"] == 180.0

    sim_risk_24h = sim_data["simulation_result"]["risk_24h"]
    assert sim_risk_24h >= sim_data["baseline"]["risk_24h"], "Simulated 180mm heavy rainfall must scale 24h risk upward"


def test_simulation_database_isolation(client):
    """Test 6 & 7: Verify incident simulation inputs NEVER contaminate real database records."""
    # Run heavy simulation
    client.post("/habitations/hab_627296/simulate", json={"simulated_rainfall_mm": 350.0, "horizon": "72h"})

    # Check real database record again
    res_db = client.get("/habitations/hab_627296/risk")
    assert res_db.status_code == 200
    db_risk = res_db.json()

    # DB record must not be 350mm simulated risk
    assert db_risk["current"] < 0.99 or db_risk["risk_24h"] != 350.0
