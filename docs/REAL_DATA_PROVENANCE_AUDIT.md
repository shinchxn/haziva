# HAZIVA Real-Data Provenance Audit

This document establishes the strict data provenance for all inputs, models, features, rainfall feeds, and output indicators across the HAZIVA system. Every operational input has a verified, non-synthetic origin.

## 1. Operational Input Provenance Table

| Input Parameter | Source Dataset / Provider | Real / Derived / ML | Timestamp / Temporal Scope | Spatial Scope | Consumed By |
|---|---|---|---|---|---|
| **Digital Elevation Model (DEM)** | Copernicus GLO-30 DEM | Real | 2024 Release | Wayanad District (30m grid) | Terrain feature derivation |
| **Slope Degrees** | Derived from Copernicus DEM | Derived | Processing Pipeline | Wayanad District (30m grid) | ML Model A / B |
| **Landcover Fractions** | ESA WorldCover 10m 2021 (v200) | Real | 2021 Epoch | Wayanad District (Resampled 30m) | ML Model A / B |
| **GSI Susceptibility Map** | Geological Survey of India (GSI) 1:50k NLSM | Real | 2020-2022 Inventory | Wayanad District (Resampled 30m) | ML Model A |
| **Historical Landslides** | GSI Landslide Inventory + Bhuvan WFS | Real | 2010–2024 Historical Events | Wayanad District (Point & Polygon) | ML Training Labels |
| **Population & Households** | Census of India 2011 (Reconciled with NWDP) | Real | Census 2011 (785,840 pop) | 48 Rural Wayanad Villages | Exposure & Priority Engine |
| **Observed Rainfall** | Open-Meteo Historical / Live API | Real | Runtime / Past 24 Hours | Wayanad (Lat 11.6, Lon 76.1) | Dynamic Risk Engine |
| **Forecast Rainfall (24h/72h)** | Open-Meteo / ECMWF IFS Forecast API | Real | Runtime / +24h, +72h Forecast | Wayanad Grid (Lat 11.6, Lon 76.1) | 24h & 72h Risk Pipeline |
| **Spatial Susceptibility** | ML Model A (`model_a_with_gsi.joblib`) | ML-Derived | Trained Model Output | Pixel / Village Level | Base Risk Calculation |
| **Current / 24h / 72h Risk** | Dynamic Risk Engine (ML + Rainfall Stress) | Derived | Runtime Calculation | 48 Wayanad Villages | Dashboard / API |
| **Relocation Candidate Sites** | OpenStreetMap Overpass API (Schools, Community Centers, Stadiums) | Real | OSM Extract 2024 | Wayanad District (796 Facilities) | Relocation Intelligence |
| **Relocation Safety & Ranking** | Prototype Evidence Scoring (`prototype_v2`) | Derived | Pipeline Execution | 794 Candidate Facilities | Relocation Service |

---

## 2. Classification of System Components

To preserve scientific integrity during live demonstrations, all data elements are strictly categorized into one of three execution paths:

### A. Real-Data Operational Path (Production / Live Demo)
- Live weather observations and ECMWF/Open-Meteo forecasts.
- Trained ML spatial landslide susceptibility (`model_a_with_gsi.joblib`).
- Reconciled Census 2011 village boundaries and OSM candidate relocation facilities.
- **Strict Rule:** Never uses hardcoded sample arrays or silent fake weather fallbacks.

### B. Incident Simulation Path (What-If Mode)
- User-specified custom rainfall scenario inputs (e.g., 180 mm over 24h).
- Processed through the **exact same backend ML risk engine** as the real-data path.
- **Strict Rule:** Visually and technically isolated from real observed data and explicitly labeled `SIMULATION — NOT OBSERVED DATA`.

### C. Test Path (Automated Quality Assurance)
- Isolated pytest unit/integration fixtures.
- **Strict Rule:** Never rendered in production or live UI demonstrations.

---

## 3. Data Integrity & Verification Commitments

1. **No Synthetic Weather:** If live weather API feeds are unreachable, the system displays `LIVE DATA UNAVAILABLE` with the timestamp of the last verified observation.
2. **No Hardcoded Risk Numbers:** All displayed risk values ($0.0 - 1.0$) are dynamically computed from terrain susceptibility and rainfall stress ($1 - e^{-\alpha \cdot R}$).
3. **No Fake Evacuation Mandates:** Relocation candidates are tagged as `CONDITIONAL (Subject to Authority Verification)` under `prototype_v2`.
