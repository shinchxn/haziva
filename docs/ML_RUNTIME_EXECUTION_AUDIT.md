# HAZIVA ML Runtime Execution Audit

This document audits the machine learning model architecture, feature preparation, model artifact loading, offline vs online inference paths, and dynamic risk calculation engine in HAZIVA.

## 1. Trained Model Specification

- **Active Model Artifact**: `models/spatial_baseline/model_a_with_gsi.joblib`
- **Model File Size**: 507 MB
- **Algorithm**: `RandomForestClassifier` (`n_estimators=300`, `min_samples_leaf=5`, `class_weight='balanced'`, `random_state=42`)
- **Target Variable**: `historical_landslide` (Binary classification: 0 = No historical landslide, 1 = Historical landslide evidence)
- **Primary Metric**: Average Precision / PR-AUC (Validation score evaluated on spatial train/test splits)

### Feature Matrix (11 Input Features)

1. `slope_degrees`: Slope in degrees derived from Copernicus DEM 30m.
2. `tree_fraction`: Tree canopy landcover fraction (ESA WorldCover 2021).
3. `shrub_fraction`: Shrubland cover fraction (ESA WorldCover 2021).
4. `grass_fraction`: Grassland cover fraction (ESA WorldCover 2021).
5. `crop_fraction`: Cropland fraction (ESA WorldCover 2021).
6. `builtup_fraction`: Built-up infrastructure fraction (ESA WorldCover 2021).
7. `bare_fraction`: Bare ground / exposed rock fraction (ESA WorldCover 2021).
8. `water_fraction`: Open water body fraction (ESA WorldCover 2021).
9. `wetland_fraction`: Wetland cover fraction (ESA WorldCover 2021).
10. `gsi_susceptibility`: Susceptibility score from Geological Survey of India 1:50k NLSM dataset.
11. `gsi_coverage`: Coverage indicator boolean (1 = GSI mapped, 0 = Unmapped/outside GSI domain).

---

## 2. Dual-Mode Inference Architecture

HAZIVA supports two complementary ML execution paths:

### Path A: Precomputed 30m Spatial Raster Aggregation (Default Operational Path)
- **Execution**: The trained RandomForest model (`model_a_with_gsi.joblib`) was evaluated offline over all 30m grid cells in Wayanad District (`scripts/run_spatial_model_inference.py`), outputting 30m spatial susceptibility GeoTIFF rasters.
- **Village Aggregation**: Zonal 95th percentile statistics ($P_{95}$) were computed across all 48 reconciled Census 2011 village boundaries (`wayanad_village_dynamic_risk.csv`).
- **Use Case**: Serves real-time dashboard risk profiles with zero latency.

### Path B: Live Model Inference Engine (`predict_risk` / `POST /predict`)
- **Execution**: The trained RandomForest model (`model_a_with_gsi.joblib`) is loaded into memory by `backend/app/services/ml_service.py`.
- **Inference**: Given feature vectors (`slope_degrees`, `landcover`, `gsi_susceptibility`), `model.predict_proba(X)[:, 1]` outputs the exact spatial susceptibility probability ($P_{ml}$).
- **Use Case**: Powers custom what-if scenario simulations and on-demand point feature predictions.

---

## 3. Dynamic Risk Calculation Formula

Dynamic risk $R_{dynamic}$ combines the static spatial landslide susceptibility probability $P_{ml}$ with dynamic rainfall stress $S_{rain}$:

$$S_{rain}(R) = 1 - e^{-\alpha \cdot R}$$

Where:
- $R$ is the rainfall accumulation in millimeters (observed 24h, forecast 24h, or forecast 72h).
- $\alpha = 0.015$ is the calibrated Wayanad rainfall stress parameter.

The final risk score $R_{dynamic} \in [0.0, 1.0]$ is computed as:

$$R_{dynamic} = \min\left(1.0, P_{ml} \cdot (1 + 1.2 \cdot S_{rain}(R))\right)$$

This formula guarantees that:
1. Low terrain susceptibility with zero rainfall yields baseline static risk.
2. Heavy rainfall (e.g. $180\text{ mm}$) dynamically scales risk upward proportional to terrain vulnerability.
3. Every risk value is deterministic, reproducible, and mathematically grounded.
