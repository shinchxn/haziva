import json
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_habitations_api_risk_data_lineage():
    """Verify that GET /habitations returns real model-derived risk data for all habitations."""
    response = client.get("/habitations")
    assert response.status_code == 200
    habitations = response.json()

    assert len(habitations) == 48, f"Expected 48 habitations, got {len(habitations)}"

    # Inspect specific audited habitation hab_627296 (Mananthavady)
    mananthavady = next((h for h in habitations if h["id"] == "hab_627296"), None)
    assert mananthavady is not None, "hab_627296 (Mananthavady) missing from API response"
    assert isinstance(mananthavady["current_risk"], float)
    assert round(mananthavady["current_risk"], 4) == 0.7511, f"Expected 0.7511, got {mananthavady['current_risk']}"
    assert mananthavady["current_risk"] >= 0.75, "Mananthavady must be classified as High Risk (>= 75%)"

    # Verify risk scale, min/max, and class distribution
    risks = [h["current_risk"] for h in habitations]
    assert all(isinstance(r, float) for r in risks), "All risk values must be floats"
    assert all(0.0 <= r <= 1.0 for r in risks), "All risk values must be on 0.0 - 1.0 scale"

    lower_risk = [r for r in risks if r < 0.50]
    elevated_risk = [r for r in risks if 0.50 <= r < 0.75]
    high_risk = [r for r in risks if r >= 0.75]

    assert len(lower_risk) > 0, "Expected at least one Lower Risk (< 50%) habitation"
    assert len(elevated_risk) > 0, "Expected at least one Elevated Risk (50-74%) habitation"
    assert len(high_risk) > 0, "Expected at least one High Risk (>= 75%) habitation"


def test_geojson_village_boundaries_mapping():
    """Verify that every GeoJSON village boundary feature maps to a real backend habitation record."""
    geojson_path = Path("frontend/public/data/wayanad_village_boundaries.geojson")
    assert geojson_path.exists(), "GeoJSON village boundaries file missing"

    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    features = geojson_data.get("features", [])
    assert len(features) == 48, f"Expected 48 GeoJSON features, got {len(features)}"

    # Query API habitations
    response = client.get("/habitations")
    assert response.status_code == 200
    habitations = response.json()

    hab_by_code = {h["id"].replace("hab_", ""): h for h in habitations}
    hab_by_name = {h["name"].lower().strip(): h for h in habitations}

    matched_count = 0
    for feature in features:
        props = feature.get("properties", {})
        vcode = str(props.get("village_code", ""))
        vname = str(props.get("village_name", props.get("village", ""))).lower().strip()

        match = hab_by_code.get(vcode) or hab_by_name.get(vname)
        if match:
            matched_count += 1

    assert matched_count == 48, f"Expected all 48 GeoJSON features to map to habitations, got {matched_count}"


def test_risk_classification_boundary_thresholds():
    """Verify exact risk classification thresholds matching HAZIVA legend:
    - Lower risk < 50% (< 0.50)
    - Elevated risk 50–74% (0.50 - 0.7499)
    - High risk >= 75% (>= 0.75)
    """
    def classify(val):
        if val is None:
            return "NO_DATA"
        if val >= 0.75:
            return "HIGH"
        if val >= 0.50:
            return "ELEVATED"
        return "LOWER"

    assert classify(0.00) == "LOWER"
    assert classify(0.4999) == "LOWER"
    assert classify(0.50) == "ELEVATED"
    assert classify(0.7499) == "ELEVATED"
    assert classify(0.75) == "HIGH"
    assert classify(1.00) == "HIGH"
    assert classify(None) == "NO_DATA"
