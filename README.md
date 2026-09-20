# HAZIVA — Dynamic Habitation Risk & Relocation Intelligence System
**SIH Problem Statement 26191 | Ministry of Home Affairs — NDRF DM Division**
**Pilot Geography: Wayanad, Kerala | Primary Hazard: Landslide**

> **Core Philosophy:** *"AI prioritizes. Humans verify. Authorities decide."*

---

## 🚨 1. Overview & Vision

Natural hazard events (such as intense monsoon rainfall and landslides) do not impact every habitation equally. When severe weather hits mountainous terrain, disaster-management authorities require rapid, evidence-backed decision support to answer critical operational questions:

1. **Which habitations are becoming unsafe?**
2. **Is the risk worsening over the next 24 to 72 hours?**
3. **Which communities demand immediate assessment and deployment?**
4. **Why is the risk escalating (terrain susceptibility vs. dynamic rainfall stress)?**
5. **Where could affected populations be temporarily or permanently relocated?**
6. **Are destination facilities safe from landslides and accessible by road?**

**HAZIVA** addresses these challenges by uniting static geospatial terrain data, high-resolution landslide susceptibility layers, Census 2011 population exposure, dynamic rainfall forecast models, and OpenStreetMap public facility infrastructure into an integrated end-to-end decision-support dashboard.

---

## 🎯 2. Core Workflow

HAZIVA operates on a seven-stage decision pipeline:

```text
  PREDICT        IDENTIFY        PRIORITIZE        FIND        VERIFY        DECIDE
┌─────────┐    ┌──────────┐    ─────────────    ┌────────┐   ┌────────┐   ────────────
│ Dynamic │ ──>│ High-Risk│ ──>│ Habitation  │──>│ OSM    │──>│ Safety │──>│ Authority  │
│ Risk    │    │ Villages │    │ Priority    │   │ Shelters│   │ Gate   │   │ Verification│
└─────────┘    └──────────┘    ─────────────    └────────┘   └────────┘   ────────────
```

---

## 🔒 3. Strict Operating Modes & Data Lineage Rules

HAZIVA enforces a strict architectural boundary between baseline operational intelligence and what-if simulation:

### Mode A — Normal Dashboard (Real & Derived Data Only)
- **100% Data Provenance:** All baseline risk scores, trajectory forecasts, village priorities, and relocation candidate coordinates originate from verified source datasets (Census 2011, Copernicus 30m DEM, GSI 30m Susceptibility, ECMWF rainfall forecasts, and OpenStreetMap).
- **Zero Mock / Fallback Leakage:** Normal API queries return true spatially matched data. Habitations without candidate facilities inside their boundary return explicit `NO_DATA` responses without silent fallback query substitutions or static mock lists.
- **Scientifically Honest Semantics:** Capacity is explicitly labeled as `capacity_status: "HEURISTIC"` ("Category Heuristic: 650"), water availability is labeled as `"UNKNOWN"` ("Water Availability: Unknown — Verification Required"), and road proximity reports real spatial distances to mapped OSM highways.

### Mode B — Incident Simulation (Isolated What-If Scenarios)
- Executed via `POST /habitations/{id}/simulate`.
- Allows disaster response commanders to input custom rainfall intensity (e.g. 250mm/24h cloudburst) to model dynamic risk scaling and downstream effects.
- **Strictly Isolated:** Operates purely in-memory and **never mutates or overwrites** baseline database records or normal GET API responses.

---

## 🏗️ 4. System Architecture

```mermaid
flowchart TD
    subgraph Data Layer
        A1["Census 2011 & NWDP Population GPKG"]
        A2["Copernicus 30m DEM & Slope TIFF"]
        A3["GSI 30m Landslide Susceptibility TIFF"]
        A4["Historical Landslide Inventory TIFF"]
        A5["Open-Meteo / ECMWF Live Forecast API"]
        A6["OpenStreetMap Public Infrastructure JSON"]
    end

    subgraph Feature Processing & Model Engine
        B1["Spatial Grid Aggregation (30m Resolution)"]
        B2["Model A Spatial Susceptibility Engine (p95)"]
        B3["Dynamic Rainfall Stress Scaling Engine"]
        B4["Risk Trajectory Engine (NOW, +24h, +72h)"]
        B5["Vulnerability-Aware Priority Engine"]
    end

    subgraph Relocation Intelligence Pipeline
        C1["794 Real OSM Candidate Facilities"]
        C2["Geodesic & Road Network Proximity Analysis"]
        C3["Destination Safety Gate (Slope & Hazard Screening)"]
        C4["Multi-Criteria Priority Ranking Engine"]
    end

    subgraph API & Serving Layer
        D1["FastAPI Backend Framework"]
        D2["PostgreSQL / PostGIS & SQLite ORM"]
    end

    subgraph Presentation Layer
        E1["Next.js 16 Dashboard"]
        E2["MapLibre GL Interactive Map"]
    end

    A1 & A2 & A3 & A4 --> B1
    B1 --> B2
    A5 --> B3
    B2 & B3 --> B4
    B4 & A1 --> B5
    A6 --> C1
    C1 & A2 & A3 & B4 --> C2 & C3
    C2 & C3 --> C4
    B4 & B5 & C4 --> D1
    D1 <--> D2
    D1 <--> E1
    E1 <--> E2
```

---

## 📊 5. Data Provenance & Lineage Matrix

| Feature / Metric | Source Dataset | Resolution / Coverage | Processing / Derivation Method | Provenance Label |
|------------------|----------------|-----------------------|--------------------------------|------------------|
| **Village Population** | Census of India 2011 / NWDP Reconciliation | 48 Rural Villages, Wayanad | GPKG spatial join & Census population reconciliation | `Census 2011 Baseline` |
| **Terrain Slope** | Copernicus GLO-30 DEM | 30-meter Grid | Geospatial slope degree extraction (`rasterio`) | `Copernicus 30m DEM` |
| **Landslide Susceptibility** | Geological Survey of India (GSI) | 30-meter Grid | Re-projected GeoTIFF sampling (0=Low, 1=Moderate, 2=High) | `GSI 30m Susceptibility` |
| **Historical Landslides** | GSI / NLFC Inventory | Point & Polygon Inventory | Spatial presence sampling (0=None, 1=Scar Present) | `GSI Historical Inventory` |
| **Dynamic Rainfall Stress** | Open-Meteo / ECMWF Forecast | 24h / 72h Windows | Dynamic exponential stress function $S(R) = 1 - e^{-k R}$ | `ECMWF Dynamic Forecast` |
| **Relocation Candidates** | OpenStreetMap (Overpass API) | 794 Extracted Public Facilities | Extracted schools, community halls, hospitals, public buildings | `OpenStreetMap` |
| **Road Proximity** | OpenStreetMap Highway Network | 4,660 Road Segments | Geodesic straight-line distance to nearest mapped OSM road | `OSM Road Proximity` |
| **Facility Capacity** | Facility Category Rules | Category Heuristic | Schools=650, Halls=900, Stadiums=1500, Hospitals=300 | `Category Heuristic` |

---

## 🔌 6. API Inventory Reference

The FastAPI backend exposes the following REST endpoints:

| Method | Path | Description | Response Schema |
|--------|------|-------------|-----------------|
| `GET` | `/` | Root API health status | `{"message": "Haziva backend API is running."}` |
| `GET` | `/habitations` | List all 48 Wayanad habitations with current risk & priority | `list[HabitationSummary]` |
| `GET` | `/habitations/{id}` | Detailed habitation profile (exposure, vulnerability, accessibility) | `HabitationDetail` |
| `GET` | `/habitations/{id}/risk` | Dynamic risk breakdown (current, +24h, +72h, confidence, drivers) | `RiskProfile` |
| `GET` | `/habitations/{id}/trajectory` | Risk trajectory forecast state (`Rapidly Increasing`, `Stable`, etc.) | `TrajectoryResponse` |
| `GET` | `/habitations/{id}/relocation` | Relocation candidate & rejected sites for specified habitation | `RelocationProfile` |
| `POST` | `/predict` | Direct Model A feature prediction inference endpoint | `RiskProfile` |
| `POST` | `/habitations/{id}/simulate` | Isolated Incident Simulation ("What-If" custom rainfall scenario) | `SimulationResult` |
| `GET` | `/system/status` | Live system readiness, ECMWF weather provider, & update timestamp | `SystemStatus` |

Interactive OpenAPI Swagger documentation is available at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## 🛠️ 7. Environment Configuration

Copy `.env.example` to `.env` in the root directory:

```bash
# Server Configuration
ENVIRONMENT=development
TESTING=False
DATABASE_URL=sqlite:///haziva_dev.db

# For production PostgreSQL + PostGIS:
# DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/haziva

CORS_ORIGINS=["*"]
MODEL_STATUS=ready
FORECAST_HORIZON=72h
DATA_STATUS=available

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 8. Quick Start Guide

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18.0 or higher
- **Package Manager:** `npm` (or `pnpm` / `yarn`)

### 1. Installation & Environment Setup
Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/shinchxn/haziva.git
cd haziva

# Create Python virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install Python backend & GIS dependencies
pip install -r requirements.txt
```

### 2. Database Seeding
Initialize SQLite/PostGIS database and seed 48 habitations and 794 relocation candidate sites from processed GIS layers:

```bash
python -m backend.app.database.seed
```

### 3. Launch Backend API
Start the FastAPI development server:

```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```
*Backend API server will run at `http://localhost:8000`.*

### 4. Launch Frontend Dashboard
In a separate terminal window, start the Next.js development server:

```bash
cd frontend
npm install
npm run dev
```
*Frontend dashboard will run at `http://localhost:3000`.*

---

## 🧪 9. Running Verification Tests

Run the complete backend & data lineage integration test suite:

```bash
# Run all pytest suites
python -m pytest

# Run specific data lineage integration test
python -m pytest tests/test_relocation_lineage.py
```

---

## ⚡ 10. Incident Simulation and Relocation

HAZIVA includes a dedicated "What-If" Incident Simulation engine designed for controlled testing and disaster preparedness drills:

```
SYNTHETIC INCIDENT INPUT
        ↓
REAL HABITATION GEOMETRY & TERRAIN CONTEXT
        ↓
SAME TRAINED ML MODEL (Model A Random Forest)
        ↓
MODEL-GENERATED SIMULATED RISK
        ↓
RELOCATION PRIORITY & URGENCY
        ↓
REAL CANDIDATE RELOCATION SITES
        ↓
REAL GIS / SAFETY / ACCESSIBILITY EVIDENCE
        ↓
HUMAN AUTHORITY DECISION SUPPORT
```

Key principles of the simulation pipeline:
1. **Synthetic Incident Inputs**: Rain scenarios (e.g. 50mm, 150mm, 300mm) are synthetic for controlled what-if testing.
2. **Real Model Inference**: Synthetic dynamic inputs pass through the exact same feature-engineering and trained Random Forest model (`Model A` / `model_a_with_gsi.joblib`). Risk is never manually assigned.
   - **Features INSIDE Trained Model A (11 features)**: Copernicus 30m DEM slope (`slope_degrees` — 69.9% importance), GSI 1:50k NLSM susceptibility & coverage (`gsi_susceptibility` — 12.3%, `gsi_coverage` — 6.7%), and 8 ESA WorldCover 30m landcover fraction features (`grass_fraction`, `tree_fraction`, `crop_fraction`, `builtup_fraction`, `water_fraction`, `bare_fraction`, `wetland_fraction`, `shrub_fraction`).
   - **Features OUTSIDE Model A (System Architecture Layer)**: Dynamic Rainfall Stress ($S = 1 - e^{-\alpha R}$), Census 2011 Population & Exposure (used in village priority ranking), and OSM Facilities & Road Network (used in relocation candidate search).
3. **Real Relocation Candidates**: Evacuation facilities are drawn directly from the OSM relocation candidate dataset (`wayanad_relocation_candidate_ranking.csv`). HAZIVA **never fabricates synthetic relocation sites**.
4. **Truthfulness of Evidence**: Candidate site safety evidence (`INSUFFICIENT_EVIDENCE`), shelter capacity (`HEURISTIC`), water availability (`UNKNOWN`), and road proximity (`NEAREST_OSM_ROAD_AVAILABLE`) remain truthful based on real candidate GIS sampling.
5. **Baseline Isolation**: Incident simulations run purely in-memory. They **never persist to or overwrite baseline database records** (`current_risk`, `risk_24h`, `risk_72h`, or candidate status).


---

## 🛡️ 11. Scope & Decision-Support Disclaimer

1. **Decision Support Only:** HAZIVA is designed to assist disaster response commanders, NDRF officers, and district administration. It does **NOT** issue automated evacuation orders or replace human decision-making.
2. **Predictive Uncertainty:** Risk estimates reflect probabilistic multi-criteria spatial modeling based on available GIS rasters and forecast rainfall. They are **NOT** deterministic guarantees of landslide occurrences.
3. **Authority Verification Required:** All relocation candidate carrying capacities and resource availabilities are labeled as estimates requiring on-ground verification by local authorities before deployment.

---
*Built for SIH 26191 — Wayanad Landslide Risk Intelligence Platform.*