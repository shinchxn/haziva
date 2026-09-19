from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {"message": "Haziva backend API is running."}


def test_cors_middleware():
    response = client.options(
        '/habitations',
        headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
        },
    )
    assert response.status_code == 200
    assert response.headers.get('access-control-allow-origin') in {'*', 'http://localhost:3000'}



def test_get_habitations():
    response = client.get('/habitations')
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]['id'].startswith('hab_')
    assert payload[0]['priority'] in {'Low', 'Medium', 'High', 'Immediate Assessment'}


def test_get_habitation_by_id():
    response = client.get('/habitations/hab_627296')
    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == 'hab_627296'
    assert payload['population'] > 0
    assert payload['current_risk'] >= 0


def test_get_habitation_not_found():
    response = client.get('/habitations/non_existent_id')
    assert response.status_code == 404


def test_get_habitation_risk():
    response = client.get('/habitations/hab_627296/risk')
    assert response.status_code == 200
    payload = response.json()
    assert 'current' in payload
    assert 'risk_24h' in payload
    assert 'risk_72h' in payload
    assert 'confidence' in payload
    assert 'hazard_type' in payload
    assert isinstance(payload['drivers'], list)


def test_get_habitation_relocation():
    response = client.get('/habitations/hab_627327/relocation')
    assert response.status_code == 200
    payload = response.json()
    assert payload['habitation_id'] == 'hab_627327'
    assert isinstance(payload['sites'], list)
    assert len(payload['sites']) > 0


def test_get_habitation_trajectory():
    response = client.get('/habitations/hab_001/trajectory')
    assert response.status_code == 200
    payload = response.json()
    assert payload['habitation_id'] == 'hab_001'
    assert 'trajectory' in payload
    assert 'current' in payload
    assert 'risk_24h' in payload
    assert 'risk_72h' in payload
    assert 'hazard_type' in payload


def test_predict_route_valid():
    payload = {
        'habitation_id': 'hab_001',
        'hazard_type': 'landslide',
        'features': {
            'slope': 0.84,
            'rainfall': 0.92,
            'forecast_rainfall': 0.8,
            'susceptibility': 0.88,
            'population_exposure': 0.7,
            'accessibility': 0.6,
        },
    }
    response = client.post('/predict', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert 'risk' in body
    assert 'confidence' in body
    assert 'drivers' in body
    assert body['hazard_type'] == 'landslide'
    assert 'timestamp' in body


def test_predict_route_invalid_bounds():
    payload = {
        'habitation_id': 'hab_001',
        'features': {
            'slope': 2.5,
        },
    }
    response = client.post('/predict', json=payload)
    assert response.status_code == 400


def test_system_status():
    response = client.get('/system/status')
    assert response.status_code == 200
    body = response.json()
    assert body['model_status'] == 'ready'
    assert body['forecast_horizon'] == '72h'


def test_predict_route_unsupported_hazard():
    from backend.app.services.ml_service import predict_risk
    import pytest

    with pytest.raises(ValueError, match="is not supported yet"):
        predict_risk("hab_001", {"slope": 0.5}, hazard_type="tsunami")


def test_production_database_fallback_prevention(monkeypatch):
    import pytest
    from backend.app.core import database
    from backend.app.core.config import settings

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "TESTING", False)
    monkeypatch.setattr(settings, "DATABASE_URL", "postgresql+psycopg://invalid_user:invalid_pass@localhost:5432/invalid_db")
    monkeypatch.setattr(database, "_engine", None)

    # Disable sys.modules pytest detection temporarily for this test unit
    import sys
    orig_pytest = sys.modules.pop("pytest", None)
    try:
        with pytest.raises(RuntimeError, match="Production environment forbids falling back"):
            database.get_engine()
    finally:
        if orig_pytest is not None:
            sys.modules["pytest"] = orig_pytest
        monkeypatch.setattr(database, "_engine", None)


def test_trajectory_and_priority_helpers():
    from backend.app.services.trajectory import calculate_trajectory
    from backend.app.services.priority import calculate_priority

    assert calculate_trajectory(0.4, 0.7, 0.9) == 'Rapidly Increasing'
    assert calculate_priority(0.7, 0.9, 'Rapidly Increasing', 0.8, 0.7) == 'Immediate Assessment'
