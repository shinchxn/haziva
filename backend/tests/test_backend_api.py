from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_get_habitations():
    response = client.get('/habitations')
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]['id'] == 'hab_001'
    assert payload[0]['priority'] in {'Low', 'Medium', 'High', 'Immediate Assessment'}


def test_get_habitation_by_id():
    response = client.get('/habitations/hab_001')
    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == 'hab_001'
    assert payload['population'] > 0
    assert payload['current_risk'] >= 0


def test_get_habitation_risk():
    response = client.get('/habitations/hab_001/risk')
    assert response.status_code == 200
    payload = response.json()
    assert 'current' in payload
    assert 'risk_24h' in payload
    assert 'risk_72h' in payload
    assert 'confidence' in payload
    assert isinstance(payload['drivers'], list)


def test_predict_route():
    payload = {
        'habitation_id': 'hab_001',
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
    assert 'timestamp' in body


def test_trajectory_and_priority_helpers():
    from backend.app.services.trajectory import calculate_trajectory
    from backend.app.services.priority import calculate_priority

    assert calculate_trajectory(0.4, 0.7, 0.9) == 'Rapidly Increasing'
    assert calculate_priority(0.7, 0.9, 'Rapidly Increasing', 0.8, 0.7) == 'Immediate Assessment'
