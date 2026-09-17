# SIH 26191 — System Architecture

## 1. Purpose

This document defines the technical architecture of the **AI-Powered Dynamic Habitation Risk & Relocation Intelligence System**.

The system is a **decision-support platform for disaster-management authorities**.

Its primary purpose is to transform changing environmental conditions into:

```text
Current Conditions
       ↓
Future Risk
       ↓
Risk Trajectory
       ↓
Habitation Priority
       ↓
Potential Relocation Sites
       ↓
Safety Verification
       ↓
Capacity Assessment
       ↓
Authority Decision
```

The system does **not** autonomously order evacuation or relocation.

> **AI predicts and prioritizes. Humans verify. Authorities decide.**

---

# 2. V1 Architecture Scope

## Pilot Geography

**Wayanad, Kerala**

## Initial Hazard

**Landslide**

## Primary Dynamic Driver

**Rainfall / Forecast Rainfall**

## Prediction Horizons

- Current
- +24 hours
- +72 hours

The architecture is designed to be extensible to additional hazards later, but V1 should remain focused on the initial landslide-risk use case.

---

# 3. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │     DATA SOURCES    │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
             STATIC DATA       DYNAMIC DATA     PERIODIC DATA
                  │                 │                 │
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                         ┌─────────────────────┐
                         │   DATA INGESTION    │
                         │   & VALIDATION      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    POSTGRESQL +     │
                         │      POSTGIS        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   FEATURE ENGINE    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      RISK MODEL     │
                         │   ML / Statistical  │
                         │       Engine        │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                 CURRENT RISK            FUTURE RISK
                                      +24h / +72h
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │  RISK TRAJECTORY    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ PRIORITY ENGINE     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ RELOCATION ENGINE   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
                  SAFETY GATE            CAPACITY ENGINE
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                         ┌─────────────────────┐
                         │     FASTAPI         │
                         │    BACKEND API      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   REACT FRONTEND    │
                         │  + GIS MAP CLIENT   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ AUTHORITY DASHBOARD │
                         └─────────────────────┘
```

The uploaded implementation specification defines the same core architecture: data sources → ingestion → static/dynamic data → feature engine → ML model → risk prediction → priority → relocation → FastAPI → React dashboard/GIS interface.

---

# 4. Architectural Principles

## 4.1 Forward Prediction First

The first implementation must prove:

```text
Current Conditions
        ↓
Future Risk
        ↓
Priority
        ↓
Relocation
        ↓
Capacity
```

Historical replay and backtesting are separate validation layers and should not block the first working prototype.

---

## 4.2 Static and Dynamic Data Are Separate

Static information changes slowly:

```text
DEM
Slope
Susceptibility
Population
Roads
Infrastructure
Administrative boundaries
```

Dynamic information changes with time:

```text
Rainfall
Rainfall accumulation
Weather forecast
Current environmental observations
```

This separation allows the system to update changing risk without repeatedly processing all geographic data.

---

## 4.3 Prediction Is Not a Disaster Guarantee

The system must not claim:

```text
"A landslide will definitely happen here tomorrow."
```

Instead, it estimates:

```text
"Risk is increasing under the current and projected conditions."
```

The output represents risk/probability/intervention priority rather than certainty of disaster occurrence.

---

## 4.4 Human-in-the-Loop

The system follows:

```text
AI
 ↓
Predict
 ↓
Prioritize
 ↓
Explain
 ↓
Suggest
 ↓
Authority Verification
 ↓
Final Decision
```

It does not autonomously issue relocation orders.

---

## 4.5 No False Precision

Every important dataset should retain metadata such as:

```text
Source
Observation date
Last updated
Spatial resolution
Coverage
Confidence
```

Old, estimated, simulated, or incomplete data must be labelled accordingly.

For example:

```text
Population:
Census 2011
Status: Baseline / Historical
```

rather than presenting it as current population.

---

# 5. Data Architecture

The data layer consists of three major categories.

## 5.1 Static Data

```text
DEM / Elevation
Slope
Landslide susceptibility
Historical hazard inventory
Population
Households
Buildings
Road network
Critical infrastructure
Land use
Administrative boundaries
Vulnerability indicators
```

These datasets are preprocessed and stored in the spatial database.

---

## 5.2 Dynamic Data

```text
Recent rainfall
Rainfall accumulation
Forecast rainfall
Current hazard observations
Other environmental observations
```

Dynamic observations are periodically updated.

The exact refresh rate depends on the actual source and its update frequency.

---

## 5.3 Periodic Data

Examples:

```text
Updated hazard layers
Satellite-derived observations
Updated infrastructure information
New GIS datasets
```

These are not necessarily refreshed continuously.

---

# 6. Data Flow

```text
External Source
      ↓
Data Adapter
      ↓
Validation
      ↓
Normalization
      ↓
Spatial Processing
      ↓
PostGIS
      ↓
Feature Extraction
      ↓
Risk Engine
```

Each source should have its own adapter where practical.

Example:

```text
Rainfall Source
      ↓
rainfall_adapter
      ↓
standard rainfall schema
      ↓
database
```

This prevents the ML engine from becoming dependent on a particular external provider.

---

# 7. Database Architecture

## PostgreSQL + PostGIS

PostgreSQL is the primary relational database.

PostGIS provides spatial storage and geographic operations.

The database should contain logical groups such as:

```text
habitations
hazard_layers
landslides
terrain
rainfall_observations
rainfall_forecasts
population
buildings
roads
infrastructure
vulnerability
relocation_sites
capacity_assessments
risk_predictions
risk_explanations
data_sources
```

---

## 7.1 Habitation

Conceptual fields:

```text
id
name
district
geometry
population
households
baseline_vulnerability
accessibility_score
created_at
updated_at
```

Geometry should use a consistent spatial reference system.

---

## 7.2 Risk Prediction

Conceptual structure:

```text
id
habitation_id
prediction_time
horizon
risk_score
risk_level
confidence
trajectory
model_version
created_at
```

Example:

```text
Habitation: H001

Current: 48
24h:     67
72h:     81

Trajectory:
INCREASING
```

The numerical values are examples only; actual values must come from the implemented model.

---

# 8. GIS Architecture

GIS is a core part of the system rather than a visualization-only component.

## GIS Responsibilities

```text
Spatial boundaries
        ↓
Habitation geometry
        ↓
Hazard intersection
        ↓
Terrain extraction
        ↓
Population exposure
        ↓
Road accessibility
        ↓
Infrastructure proximity
        ↓
Relocation-site analysis
```

---

## 8.1 Terrain Processing

Terrain processing can derive:

```text
Elevation
Slope
Terrain characteristics
```

from DEM data.

These features become inputs to the risk model.

---

## 8.2 Hazard Processing

Landslide-related GIS layers include:

```text
Landslide inventory
Landslide susceptibility
Historical hazard evidence
```

The system spatially associates these layers with habitations.

---

## 8.3 Accessibility

Road-network information is used to estimate:

```text
Road accessibility
Distance to major roads
Access to emergency services
Access to essential infrastructure
```

Accessibility contributes both to vulnerability/priority and relocation evaluation.

---

# 9. Feature Engineering Architecture

The Feature Engine combines static and dynamic information.

```text
                 HABITATION
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     STATIC FEATURES         DYNAMIC FEATURES
          │                       │
          ├─ slope                ├─ rainfall
          ├─ elevation            ├─ accumulation
          ├─ susceptibility       ├─ forecast rainfall
          ├─ population           └─ observations
          ├─ infrastructure
          └─ accessibility
                  │
                  ▼
           FEATURE VECTOR
                  │
                  ▼
             RISK MODEL
```

Potential feature groups:

### Hazard

```text
Landslide susceptibility
Slope
Elevation / terrain
Recent rainfall
Rainfall accumulation
Forecast rainfall
Historical hazard evidence
```

### Exposure

```text
Population
Households
Settlement density
Buildings
Critical infrastructure
```

### Vulnerability

```text
Housing/service indicators
Accessibility
Distance to essential services
Other defensible vulnerability indicators
```

The exact feature set must be documented and justified.

---

# 10. Machine Learning Architecture

## V1 Model Strategy

Start with an interpretable baseline.

Potential models:

```text
Logistic Regression
Random Forest
Gradient Boosting
XGBoost
LightGBM
```

The selected model must be determined by available data and validation performance.

Deep learning should not be introduced merely for complexity.

---

## 10.1 Training Pipeline

```text
Raw Data
    ↓
Cleaning
    ↓
Spatial Processing
    ↓
Feature Engineering
    ↓
Training Dataset
    ↓
Train / Validation
    ↓
Model Training
    ↓
Evaluation
    ↓
Model Selection
    ↓
Saved Model
```

---

## 10.2 Prediction Pipeline

```text
Current Data
     +
Forecast Data
     +
Static Features
     ↓
Feature Engineering
     ↓
Trained Model
     ↓
Risk Probability
     ↓
Risk Score
     ↓
Risk Level
```

The model should produce predictions for the required horizons.

---

# 11. Future Risk Architecture

The primary prediction output is:

```text
             FUTURE RISK
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
       NOW       +24h      +72h
        │         │         │
        └─────────┼─────────┘
                  ▼
           RISK TRAJECTORY
```

Example:

```text
NOW       48
+24h      67
+72h      81

Trajectory:
INCREASING
```

The system should support trajectory categories such as:

```text
STABLE
INCREASING
RAPIDLY INCREASING
DECREASING
CRITICAL
```

---

# 12. Explainability Architecture

Every important high-risk prediction should have evidence explaining the result.

Example:

```text
WHY IS THIS HABITATION HIGH RISK?

✓ High landslide susceptibility
✓ High recent rainfall
✓ Heavy forecast rainfall
✓ High population exposure
✓ Limited accessibility
```

The explanation layer must use actual model features and calculated evidence.

It must never generate arbitrary reasons that are unrelated to the model output.

---

# 13. Priority Engine

Risk is converted into an operational assessment priority.

Conceptually:

```text
Risk
 +
Exposure
 +
Vulnerability
 +
Trajectory
        ↓
Priority Engine
        ↓
Assessment Priority
```

Possible categories:

```text
LOW
MEDIUM
HIGH
IMMEDIATE ASSESSMENT
```

Priority is intended to support authorities in deciding where attention and field verification should be directed.

It is not an automatic evacuation command.

---

# 14. Relocation Intelligence Architecture

Relocation begins after identifying a habitation requiring assessment.

```text
High-Priority Habitation
          ↓
Candidate Site Search
          ↓
Hazard Safety Gate
          ↓
Buildable Land
          ↓
Water Availability
          ↓
Road Accessibility
          ↓
Infrastructure
          ↓
Capacity Assessment
          ↓
Potential Relocation Candidate
```

---

# 15. Relocation Safety Gate

Safety constraints are applied before general scoring.

Conceptually:

```text
Candidate Site
      ↓
Is hazard acceptable?
      │
   ┌──┴──┐
   NO    YES
   │      │
REJECT    ↓
      Buildability
          ↓
       Water
          ↓
       Access
          ↓
   Infrastructure
```

A site with a critical hazard conflict should not become acceptable simply because it performs well on other attributes.

Rejected candidates should retain a reason:

```text
Site A
REJECTED

Reason:
High landslide hazard
```

---

# 16. Capacity Engine

Relocation capacity must not be represented by a single arbitrary number.

Capacity should be assessed separately:

```text
Land Capacity
Water Capacity
Infrastructure Capacity
Accessibility Capacity
```

Conceptually:

```text
             LAND
               │
             WATER
               │
        INFRASTRUCTURE
               │
        ACCESSIBILITY
               │
               ▼
      EFFECTIVE CAPACITY
```

A conservative planning approach can use:

```text
Effective Capacity =
MIN(
    Land Capacity,
    Water Capacity,
    Infrastructure Capacity
)
```

All assumptions must be documented.

Where reliable capacity information is unavailable, the system should mark the value as:

```text
Estimated
Requires Authority Verification
```

---

# 17. Backend Architecture

## FastAPI

FastAPI provides the application service layer between:

```text
Frontend
   ↕
FastAPI
   ↕
PostGIS
   ↕
ML / GIS / Relocation Services
```

The backend should orchestrate services rather than placing all business logic inside API routes.

---

# 18. Backend Service Layers

Conceptual structure:

```text
API Routes
    ↓
Service Layer
    ↓
Repository Layer
    ↓
PostGIS
```

Specialized services:

```text
RiskService
PredictionService
HabitationService
PriorityService
RelocationService
CapacityService
DataIngestionService
```

---

# 19. API Architecture

Initial API contract:

```text
GET /habitations

GET /habitations/{id}

GET /habitations/{id}/risk

GET /habitations/{id}/trajectory

GET /habitations/{id}/relocation

POST /predict
```

A prediction response can conceptually contain:

```json
{
  "habitation_id": "H001",
  "current_risk": 48,
  "risk_24h": 67,
  "risk_72h": 81,
  "trajectory": "INCREASING",
  "priority": "HIGH",
  "confidence": 0.78,
  "drivers": []
}
```

The actual API contract should be maintained separately in:

```text
docs/api-contract.md
```

---

# 20. Frontend Architecture

The frontend is a React-based authority dashboard.

Primary interface areas:

```text
Command Dashboard
Habitation Intelligence
Relocation
Data / System Status
```

---

## 20.1 Command Dashboard

Displays:

```text
Wayanad Map
Risk Zones
High-Priority Habitations
Current Risk
Future Risk
Overall Status
```

---

## 20.2 Habitation Intelligence

Displays:

```text
Current Risk
24h Risk
72h Risk
Risk Trajectory
Risk Drivers
Exposure
Vulnerability
Accessibility
```

---

## 20.3 Relocation View

Displays:

```text
Candidate Sites
Rejected Sites
Rejection Reasons
Potential Sites
Capacity
Safety Checks
Infrastructure
Accessibility
```

---

## 20.4 System Status

Displays:

```text
Last Data Update
Data Source
Source Status
Forecast Horizon
Data Completeness
Model Confidence
Uncertainty Indicators
```

---

# 21. Frontend-to-Backend Flow

```text
USER SELECTS HABITATION
          ↓
Frontend
          ↓
GET /habitations/{id}
          ↓
Backend
          ↓
PostGIS
          ↓
Habitation Data
          ↓
Frontend
          ↓
GET /habitations/{id}/risk
          ↓
Risk Service
          ↓
ML Model
          ↓
Risk Result
          ↓
Frontend Dashboard
```

For relocation:

```text
High-Risk Habitation
        ↓
GET /habitations/{id}/relocation
        ↓
Relocation Service
        ↓
Candidate Search
        ↓
Safety Gate
        ↓
Capacity Engine
        ↓
Candidate Results
        ↓
Frontend
```

---

# 22. End-to-End Prediction Flow

The primary V1 execution path is:

```text
SELECT HABITATION
        ↓
GET CURRENT CONDITIONS
        ↓
GET FUTURE FORECAST
        ↓
LOAD STATIC GIS FEATURES
        ↓
FEATURE ENGINEERING
        ↓
RUN MODEL
        ↓
CURRENT RISK
        ↓
24h RISK
        ↓
72h RISK
        ↓
RISK TRAJECTORY
        ↓
PRIORITY
        ↓
CANDIDATE RELOCATION SEARCH
        ↓
SAFETY GATE
        ↓
CAPACITY ASSESSMENT
        ↓
DASHBOARD
```

This complete path represents the first functional milestone.

---

# 23. Real-Time Architecture

Real-time operation is added after the core prediction pipeline works.

```text
LIVE RAINFALL
WEATHER FORECAST
GIS DATA
GOVERNMENT OBSERVATIONS
        ↓
DATA INGESTION
        ↓
VALIDATION
        ↓
FEATURE UPDATE
        ↓
RISK MODEL
        ↓
NEW PREDICTION
        ↓
PRIORITY UPDATE
        ↓
DASHBOARD UPDATE
```

The system should use scheduled polling for the MVP rather than building an unnecessarily complex streaming infrastructure.

Conceptually:

```text
Scheduler
    ↓
Fetch Latest Observation
    ↓
Validate
    ↓
Did Data Change?
    ↓
   YES
    ↓
Store Observation
    ↓
Identify Affected Areas
    ↓
Recalculate Risk
    ↓
Update Dashboard
```

The actual polling interval must respect the selected data source's real update frequency.

---

# 24. Live / Simulation Architecture

The data layer should support both live and simulation modes.

```text
                 DATA MANAGER
                     │
            ┌────────┴────────┐
            ▼                 ▼
        LIVE MODE       SIMULATION MODE
            │                 │
            └────────┬────────┘
                     ▼
                 RISK ENGINE
                     ↓
                  DASHBOARD
```

## Live Mode

Uses accessible, validated current observations.

## Simulation Mode

Uses controlled inputs to demonstrate how the system reacts to changing conditions.

Example:

```text
54 → 61 → 72 → 86

🟡    🟠    🟠    🔴
```

Simulation values must never be presented as real-world observations.

---

# 25. Historical Validation Architecture

Historical validation is a later layer built on the same prediction engine.

```text
Historical Disaster
        ↓
Historical Pre-Event Data
        ↓
T-72
T-48
T-24
T-12
T-6
T-1
        ↓
SAME RISK ENGINE
        ↓
Historical Predictions
        ↓
Compare With Actual Event
        ↓
Evaluation
```

The system should use only information that would have been available at each historical timestamp.

This prevents future information from leaking into historical predictions.

---

# 26. Historical Replay Architecture

After historical validation works, the system can expose it through a replay interface.

```text
T-72h
  ↓
T-48h
  ↓
T-24h
  ↓
T-12h
  ↓
T-6h
  ↓
T-0
```

The replay can visualize:

```text
Risk changes
Map changes
Priority changes
Relocation recommendations
```

Historical replay is therefore a validation/demo layer, not the foundation of the V1 architecture.

---

# 27. Model Confidence and Data Confidence

The system should distinguish:

```text
RISK SEVERITY
```

from:

```text
MODEL CONFIDENCE
```

For example:

```text
Risk:
HIGH

Confidence:
MODERATE
```

This means the predicted risk is high, but the available evidence/model certainty is limited.

Data quality should also be visible:

```text
Rainfall:
Available / Recent

Population:
Census 2011 / Baseline

Shelter Capacity:
Estimated / Requires Verification
```

---

# 28. Failure Handling

External data sources can become unavailable.

The architecture should therefore avoid making one external API a single point of failure.

```text
External Source
      ↓
Data Adapter
      ↓
Validation
      ↓
Storage
      ↓
Risk Engine
```

If a live source becomes unavailable:

```text
LIVE DATA UNAVAILABLE
        ↓
Use last validated observation
        OR
Simulation Mode
        ↓
Continue Demonstration
```

The dashboard must clearly indicate the data status.

---

# 29. Technology Stack

## Frontend

```text
React
MapLibre GL JS or Leaflet
Turf.js where required
Charting library
```

## Backend

```text
Python
FastAPI
```

## Database

```text
PostgreSQL
PostGIS
```

## Machine Learning

```text
Python
pandas
NumPy
scikit-learn

XGBoost / LightGBM
only if justified
```

## GIS Processing

```text
GeoPandas
Rasterio
GDAL
PostGIS
```

## Preprocessing

```text
QGIS
GDAL
```

The uploaded project architecture specifies PostgreSQL/PostGIS, FastAPI, React, GIS tooling, and Python ML libraries as the recommended stack.

---

# 30. Repository-to-Architecture Mapping

```text
data/
    ↓
Raw and processed datasets

gis/
    ↓
Geospatial processing and layers

ml/
    ↓
Feature engineering
Training
Prediction
Explainability
Models

priority/
    ↓
Habitation priority logic

relocation/
    ↓
Candidate search
Safety
Capacity
Ranking

backend/
    ↓
FastAPI
Services
Repositories
API

frontend/
    ↓
Dashboard
Map
Habitation
Relocation UI

tests/
    ↓
Integration
End-to-end validation

future/
    ↓
Historical validation
Historical replay
Live ingestion
Multi-hazard expansion
```

---

# 31. Six-Person Architecture Ownership

## P1 — Dataset + ML Lead

Owns:

```text
Risk model
Prediction pipeline
24h/72h prediction
Risk trajectory
risk_engine
```

---

## P2 — ML Engineer

Owns:

```text
Training dataset
Feature engineering
Data quality
Evaluation
Explainability
Model confidence
```

---

## P3 — GIS/Data Engineer

Owns:

```text
Wayanad GIS
Habitations
DEM
Slope
Hazard layers
Population
Roads
Infrastructure
Relocation geography
```

---

## P4 — Backend Engineer

Owns:

```text
PostgreSQL/PostGIS
FastAPI
Data ingestion
APIs
ML integration
Backend services
```

---

## P5 — Frontend/Map Engineer

Owns:

```text
React dashboard
Interactive map
Risk visualization
Charts
Habitation interface
Relocation interface
```

---

## P6 — Relocation + Integration Lead

Owns:

```text
Candidate-site engine
Safety gate
Capacity assessment
Infrastructure checks
End-to-end integration
Final demo workflow
```

These responsibilities follow the team ownership defined in the project implementation specification.

---

# 32. Development Sequence

## Phase 1 — Data Foundation

```text
GIS Data
    +
Database
    +
ML Input Definition
    +
Relocation Schema
    +
Dashboard Shell
```

---

## Phase 2 — Prediction Engine

```text
Data
 ↓
Features
 ↓
Model
 ↓
24h / 72h Risk
```

---

## Phase 3 — Backend Integration

```text
ML
 ↓
FastAPI
 ↓
PostGIS
```

---

## Phase 4 — Relocation

```text
High-Risk Habitation
 ↓
Candidate Sites
 ↓
Safety Gate
 ↓
Capacity
```

---

## Phase 5 — Frontend Integration

```text
API
 ↓
Map
 ↓
Risk
 ↓
Prediction
 ↓
Priority
 ↓
Relocation
```

---

# 33. First Working System

The first successful system should be able to execute:

```text
             HABITATION
                  │
                  ▼
        CURRENT CONDITIONS
                  │
                  ▼
             FORECAST
                  │
                  ▼
          FEATURE ENGINE
                  │
                  ▼
             RISK MODEL
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
      NOW        +24h       +72h
       │          │          │
       └──────────┼──────────┘
                  ▼
          RISK TRAJECTORY
                  │
                  ▼
             PRIORITY
                  │
                  ▼
       RELOCATION SEARCH
                  │
                  ▼
            SAFETY GATE
                  │
                  ▼
          CAPACITY CHECK
                  │
                  ▼
             DASHBOARD
```

If this path works reliably, **Prototype V1 is functional**.

---

# 34. Security and Reliability Principles

The backend should:

- Validate all external inputs.
- Validate geographic identifiers.
- Avoid exposing internal database credentials.
- Keep configuration and secrets outside source code.
- Separate development and production configuration.
- Log model and data versions for predictions.
- Avoid trusting client-provided risk values.
- Keep model execution server-side.
- Record data-source timestamps.
- Provide meaningful API errors.

---

# 35. Architectural Extensibility

The architecture should be hazard-agnostic even though V1 focuses on landslides.

Future:

```text
                 HAZARD ENGINE
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   LANDSLIDE        FLOOD        COASTAL RISK
       │              │              │
       └──────────────┼──────────────┘
                      ▼
               COMMON RISK API
                      ↓
               PRIORITY ENGINE
                      ↓
             RELOCATION ENGINE
```

Future hazards may include:

```text
Flood
Cyclone
Extreme heat
Coastal erosion
Cloudburst-related risk
```

These should be added only after the V1 pipeline is stable.

---

# 36. What Is Explicitly Out of Scope for V1

Do not make these dependencies for the first working prototype:

```text
Full India coverage
Multiple complete hazard models
Autonomous evacuation
Mobile application
Complex deep-learning architecture
Real-time satellite processing
Historical replay UI
Large cloud infrastructure
Many external APIs
```

The first objective is:

> **Current conditions → future risk → priority → potential relocation → capacity.**

---

# 37. Final Architecture Principle

The project is not simply:

```text
AI
 ↓
Disaster Prediction
```

The core architecture is:

```text
                 HAZARD DATA
                      +
                WEATHER DATA
                      +
                   GIS DATA
                      +
                EXPOSURE DATA
                      +
              VULNERABILITY DATA
                      ↓
               FUTURE RISK ML
                      ↓
                24h / 72h
                      ↓
               RISK TRAJECTORY
                      ↓
             HABITATION PRIORITY
                      ↓
             RELOCATION SEARCH
                      ↓
                SAFETY GATE
                      ↓
             CAPACITY ASSESSMENT
                      ↓
             EVIDENCE / EXPLANATION
                      ↓
             AUTHORITY VERIFICATION
                      ↓
                FINAL DECISION
```

## Core System Statement

> **The platform transforms dynamic environmental and geospatial information into explainable future-risk intelligence, habitation-level priority assessment, and capacity-aware relocation planning for disaster-management authorities.**

## Development Rule

> **Build forward first. Validate backward later.**

The first question the architecture must answer is:

> **Can the system take current conditions and produce a useful future-risk, priority, and relocation-planning output?**

Only after that pipeline is operational should historical validation, historical replay, and live multi-source ingestion be expanded.