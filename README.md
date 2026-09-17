# SIH 26191 — Dynamic Habitation Risk & Relocation Intelligence

> **A GIS-enabled disaster-management decision-support platform for future risk assessment, habitation prioritization, and relocation planning.**

---

## 🚨 Overview

Natural hazards do not affect every habitation equally.

When environmental conditions change, authorities need to understand:

- Which habitations are becoming risky?
- Is the risk increasing over the next 24–72 hours?
- Which communities require attention first?
- Why is the risk increasing?
- Where could people potentially be relocated?
- Is the potential destination sufficiently safe?
- Can it accommodate the affected population?
- What still requires human verification?

**SIH 26191** aims to connect these questions into a single decision-support workflow.

Instead of stopping at a hazard map or a risk score, the platform connects:

```text
CHANGING CONDITIONS
        ↓
FUTURE RISK
        ↓
HABITATION IDENTIFICATION
        ↓
VULNERABILITY
        ↓
PRIORITY
        ↓
RELOCATION SEARCH
        ↓
SAFETY VERIFICATION
        ↓
CAPACITY ASSESSMENT
        ↓
AUTHORITY DECISION
```

---

## 🎯 Problem Statement

**SIH Problem Statement:** 26191  
**Organization:** Ministry of Home Affairs  
**Department:** NDRF — DM Division  
**Theme:** Disaster Management  
**Category:** Software

The project addresses the need for a proactive system that can transform changing hazard and environmental information into actionable habitation-level intelligence and relocation-planning support.

The system is designed as **decision support**, not autonomous disaster management.

> **AI predicts and prioritizes. Humans verify. Authorities decide.**

---

# 🧭 Core Workflow

The platform follows:

```text
PREDICT
   ↓
IDENTIFY
   ↓
PRIORITIZE
   ↓
FIND
   ↓
VERIFY
   ↓
DECIDE
```

### Detailed pipeline

```text
Static GIS Data
       +
Dynamic Environmental Data
       +
Weather Forecast
       ↓
Feature Engineering
       ↓
Future Risk Model
       ↓
NOW / +24h / +72h Risk
       ↓
Risk Trajectory
       ↓
Habitation Vulnerability
       ↓
Priority Assessment
       ↓
Relocation Candidate Search
       ↓
Safety Gate
       ↓
Capacity Assessment
       ↓
Evidence & Explanation
       ↓
Authority Verification
       ↓
Final Decision
```

---

# 🌍 V1 Scope

The first working prototype is intentionally focused.

| Component | V1 |
|---|---|
| Geography | Wayanad, Kerala |
| Primary hazard | Landslide |
| Dynamic driver | Rainfall / forecast rainfall |
| Current horizon | NOW |
| Future horizons | +24h, +72h |
| Interface | GIS-enabled decision dashboard |
| Prediction | Future risk |
| Relocation | Potential candidate identification |
| Decision | Human/authority controlled |

The architecture is designed for future expansion to additional hazards and regions.

---

# 🔬 What Does the System Predict?

The system does **not** claim that a disaster will definitely occur at an exact location and time.

Instead, it estimates future risk using available evidence.

For example:

```text
Habitation A

Current Risk     HIGH
24h Risk         HIGH
72h Risk         CRITICAL

Trajectory:
RAPIDLY INCREASING

Main Drivers:
• High landslide susceptibility
• Increasing rainfall
• High forecast rainfall
• Significant population exposure
• Limited accessibility
```

The actual values and explanations must come from the implemented data and model.

---

# 🧠 Intelligence Layers

The project is organized around five conceptual intelligence layers.

### 1. Multi-Hazard / Red-Zone Intelligence

Combines relevant hazard indicators and applies critical hazard constraints.

### 2. Predictive Risk

Estimates current and future risk from static and dynamic features.

### 3. Habitation Vulnerability

Considers differences between communities rather than treating all exposed populations equally.

### 4. Relocation Priority

Converts risk, exposure, vulnerability, accessibility and historical evidence into an assessment priority.

### 5. Destination Carrying Capacity

Checks whether potential relocation areas have sufficient land, water, infrastructure and accessibility.

---

# 📈 Risk Trajectory

The system does not rely only on the current risk value.

It tracks how risk changes:

```text
NOW       → 42
+24h      → 61
+72h      → 83
```

Possible trajectory states:

```text
DECREASING
STABLE
INCREASING
RAPIDLY INCREASING
CRITICAL
```

Trajectory is calculated from actual predictions.

---

# 👥 Vulnerability-Aware Prioritization

Hazard does not automatically mean equal impact.

The platform can consider indicators such as:

```text
Elderly / children
Disability
Population exposure
Housing fragility
Poverty proxy
Service accessibility
Critical infrastructure exposure
```

The project methodology provides an explainable weighted vulnerability structure.

The purpose is to identify **which habitations may require greater attention**, not to make an autonomous evacuation decision.

---

# 📍 Relocation Intelligence

For a high-priority habitation, the system can search for potential relocation areas.

The process is:

```text
Priority Habitation
       ↓
Candidate Areas
       ↓
Safety Gate
       ↓
Buildable Land
       ↓
Water Availability
       ↓
Road / Accessibility
       ↓
Infrastructure
       ↓
Capacity
       ↓
Candidate Evaluation
```

### Safety comes first.

A hazardous location must not become acceptable merely because it has:

```text
Large land area
+
Good roads
+
Water
+
Infrastructure
```

Unsafe candidates can be rejected with an explanation.

---

# 🏗️ Carrying Capacity

Potential relocation destinations are evaluated using separate capacity dimensions:

```text
Land Capacity
Water Capacity
Infrastructure Capacity
Accessibility
```

A conservative planning approach may use:

```text
Effective Capacity =
MIN(
    Land Capacity,
    Water Capacity,
    Infrastructure Capacity
)
```

Capacity estimates must be clearly labelled when they are estimated or require authority verification.

---

# 🗺️ GIS Intelligence

The platform is designed around spatial decision-making.

The map can represent:

```text
Hazard
Risk
Habitations
Priority
Relocation Candidates
Rejected Candidates
Infrastructure
Accessibility
```

GIS information is not treated as decoration.

It is part of the decision pipeline.

---

# 📊 Decision Dashboard

The dashboard should quickly answer:

```text
Where is the risk?

Which habitations require attention?

Is risk increasing?

Why is the risk high?

Which locations could potentially be considered?

Are those locations sufficiently safe?

How much capacity may be available?

What still requires verification?
```

The dashboard is therefore more than a map.

---

# 🔎 Explainability

Every important prediction should be traceable to actual inputs and model evidence.

Example:

```text
WHY HIGH RISK?

✓ High landslide susceptibility
✓ High recent rainfall
✓ High forecast rainfall
✓ High population exposure
✓ Limited accessibility
```

The system must never generate generic explanations unrelated to the actual prediction.

---

# ⚠️ Risk ≠ Confidence

Risk severity and prediction confidence are separate.

Example:

```text
Risk:
HIGH

Confidence:
MODERATE
```

Confidence may depend on:

```text
Data freshness
Spatial coverage
Input completeness
Source reliability
Forecast uncertainty
```

A high-risk prediction should not automatically be presented as certain.

---

# 🔐 Human-in-the-Loop

The platform does not replace disaster-management authorities.

The intended decision chain is:

```text
AI
 ↓
Prediction & Prioritization
 ↓
Human Verification
 ↓
Authority Assessment
 ↓
Final Decision
```

Example:

```text
AI Assessment:
HIGH PRIORITY

Suggested Action:
FIELD VERIFICATION

Authority Status:
PENDING
```

The system must not present an AI recommendation as an official evacuation order.

---

# 🧪 Development Philosophy

The project follows several principles:

```text
Correctness
     +
Traceability
     +
Interpretability
     +
Safety
     +
Integration
```

rather than:

```text
More AI
More complexity
More technologies
```

A simple, explainable model is preferable to an unnecessarily complex model.

---

# 🤖 Machine Learning

The initial model should be interpretable and data-driven.

Potential progression:

```text
Baseline
   ↓
Logistic Regression
   ↓
Tree-Based Model
   ↓
Gradient Boosting / XGBoost / LightGBM
```

More complex models should only be introduced when justified by:

- Data availability
- Validation performance
- Interpretability
- Computational requirements
- Deployment requirements

Deep learning is not required merely to call the system AI-powered.

---

# 🗃️ Data

Potential data categories include:

### Terrain

```text
DEM
Elevation
Slope
Terrain characteristics
```

### Hazard

```text
Landslide susceptibility
Historical hazard evidence
```

### Weather

```text
Recent rainfall
Rainfall accumulation
Forecast rainfall
```

### Exposure

```text
Population
Households
Buildings
Critical infrastructure
```

### Accessibility

```text
Road network
Travel/access constraints
Essential-service distance
```

### Relocation

```text
Buildable land
Water
Infrastructure
Accessibility
Existing population
```

All external datasets must record their source, timestamp, coverage and processing history.

---

# 🏛️ Data Provenance

The project may use source families such as:

```text
NRSC / ISRO
GSI / NLFC
IMD
Bhuvan / NRSC
Census of India
OpenStreetMap
Other authoritative/public datasets
```

The exact dataset used for each feature must be documented.

Historical baseline data must not be silently presented as current live data.

For example:

```text
Population:
Census 2011 baseline
```

is different from:

```text
Current population
```

---

# 🔄 Forward-Looking First

The first objective is a functioning forward prediction pipeline.

```text
CURRENT CONDITIONS
       ↓
FORECAST
       ↓
MODEL
       ↓
CURRENT RISK
       ↓
24h RISK
       ↓
72h RISK
       ↓
TRAJECTORY
       ↓
PRIORITY
       ↓
RELOCATION
       ↓
CAPACITY
```

Historical replay and backtesting are subsequent validation layers.

---

# 🧪 Historical Validation — Later Stage

After the forward system works, historical disasters can be used for validation.

The same prediction engine can be evaluated at historical points such as:

```text
T-72h
T-48h
T-24h
T-12h
T-6h
T-0
```

Only information that would have been available at each historical timestamp should be used.

This prevents future information from leaking into past predictions.

---

# 🏗️ Architecture

High-level architecture:

```text
                  DATA SOURCES
                       │
                       ▼
                DATA INGESTION
                       │
                       ▼
              DATA VALIDATION
                       │
                       ▼
              FEATURE ENGINEERING
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        STATIC FEATURES     DYNAMIC FEATURES
             │                   │
             └─────────┬─────────┘
                       ▼
                  RISK MODEL
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
           NOW       +24h       +72h
             └─────────┬─────────┘
                       ▼
                RISK TRAJECTORY
                       │
                       ▼
             PRIORITY ASSESSMENT
                       │
                       ▼
             RELOCATION ENGINE
                       │
                       ▼
                 SAFETY GATE
                       │
                       ▼
              CAPACITY ENGINE
                       │
                       ▼
                 FASTAPI
                       │
                       ▼
              WEB APPLICATION
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        COMMAND DASHBOARD       GIS MAP
```

---

# 🛠️ Technology Stack

## Frontend

- React
- MapLibre GL JS or Leaflet
- Recharts / charting library

## Backend

- Python
- FastAPI

## Database

- PostgreSQL
- PostGIS

## Machine Learning

- Python
- pandas
- NumPy
- scikit-learn
- XGBoost / LightGBM where justified

## GIS

- GeoPandas
- Rasterio
- GDAL
- PostGIS

---

# 📁 Repository Structure

```text
sih-26191/
│
├── README.md
├── PROJECT_KNOWLEDGE.md
├── ARCHITECTURE.md
├── DEVELOPMENT_RULES.md
├── TEAM.md
│
├── docs/
│   ├── problem-statement.md
│   ├── system-flow.md
│   ├── data-sources.md
│   ├── database-schema.md
│   ├── api-contract.md
│   ├── ml-methodology.md
│   └── relocation-methodology.md
│
├── team/
│   ├── person-1-dataset-ml-lead.md
│   ├── person-2-ml-engineer.md
│   ├── person-3-backend.md
│   ├── person-4-frontend.md
│   ├── person-5-map.md
│   └── person-6-relocation-integration.md
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── features/
│   └── relocation/
│
├── ml/
│   ├── data/
│   ├── features/
│   ├── training/
│   ├── prediction/
│   ├── explainability/
│   ├── models/
│   └── outputs/
│
├── gis/
│   ├── boundaries/
│   ├── terrain/
│   ├── hazard/
│   ├── habitation/
│   ├── accessibility/
│   ├── infrastructure/
│   ├── relocation/
│   └── outputs/
│
├── priority/
│
├── relocation/
│   ├── candidate_search/
│   ├── safety/
│   ├── capacity/
│   ├── evaluation/
│   ├── ranking/
│   └── relocation_engine/
│
├── backend/
│
├── frontend/
│
├── scripts/
│
├── tests/
│
└── future/
    ├── historical_validation/
    ├── historical_replay/
    ├── live_ingestion/
    └── multi_hazard/
```

---

# 👥 Team Structure

| Member | Responsibility |
|---|---|
| **P1** | Dataset + ML Lead |
| **P2** | ML Engineer |
| **P3** | Backend |
| **P4** | Frontend / UI |
| **P5** | Map / Geolocation |
| **P6** | Relocation + Integration |

### P1 — Dataset + ML Lead

Owns:

```text
Risk-engine foundation
Model architecture
Prediction pipeline
Risk trajectory
Model output contract
```

### P2 — ML Engineer

Owns:

```text
Training dataset
Feature engineering
Training
Evaluation
Explainability
```

### P3 — Backend

Owns:

```text
PostgreSQL
PostGIS
FastAPI
Repositories
Services
API
ML ↔ API integration
```

### P4 — Frontend

Owns:

```text
Dashboard
Risk cards
Charts
Habitation UI
Relocation UI
System status
```

### P5 — Map / Geolocation

Owns:

```text
Interactive map
GIS visualization
Habitation locations
Hazard layers
Map interaction
```

### P6 — Relocation + Integration

Owns:

```text
Candidate-site search
Safety gate
Capacity assessment
Relocation evaluation
End-to-end integration
```

---

# 🌿 Git Workflow

`main` is the stable branch.

Developers work on feature branches:

```text
feature/p1-dataset-ml-lead
feature/p2-ml-engineer
feature/p3-backend
feature/p4-frontend
feature/p5-map
feature/p6-relocation-integration
```

Workflow:

```text
Feature Branch
      ↓
Development
      ↓
Testing
      ↓
Commit
      ↓
Push
      ↓
Pull Request
      ↓
Review
      ↓
Merge to main
```

### Never directly push unfinished work to `main`.

---

# 🔒 Development Safety Rules

The project must never:

- Fake live data
- Invent model accuracy
- Expose private API keys
- Present simulated data as real-time data
- Invent model explanations
- Bypass relocation safety constraints
- Present AI recommendations as government decisions
- Silently change API/database contracts
- Use unexplained thresholds
- Claim official approval without evidence

---

# 🧩 Data States

The application should clearly distinguish:

```text
LIVE
SIMULATION
HISTORICAL
ESTIMATED
STALE
UNAVAILABLE
```

Example:

```text
Rainfall
LIVE

Population
CENSUS 2011 BASELINE

Relocation Capacity
ESTIMATED

Authority Verification
PENDING
```

This prevents misleading users about the certainty or source of information.

---

# 🚀 First Working Milestone

The first complete prototype should support:

```text
SELECT HABITATION
        ↓
CURRENT CONDITIONS
        ↓
FORECAST
        ↓
RUN MODEL
        ↓
CURRENT RISK
        ↓
24h RISK
        ↓
72h RISK
        ↓
TRAJECTORY
        ↓
VULNERABILITY
        ↓
PRIORITY
        ↓
RELOCATION CANDIDATES
        ↓
SAFETY GATE
        ↓
CAPACITY
        ↓
DASHBOARD
```

If this flow works end-to-end, the core V1 prototype is functional.

---

# 🎬 Final Demonstration Flow

The intended demo should tell one continuous story:

```text
1. Open Command Dashboard
          ↓
2. Show Wayanad
          ↓
3. Select a habitation
          ↓
4. Show current conditions
          ↓
5. Show current risk
          ↓
6. Show +24h prediction
          ↓
7. Show +72h prediction
          ↓
8. Show risk trajectory
          ↓
9. Explain why risk is changing
          ↓
10. Show habitation priority
          ↓
11. Open relocation analysis
          ↓
12. Show candidate locations
          ↓
13. Show unsafe/rejected candidates
          ↓
14. Show capacity assessment
          ↓
15. Show authority verification state
```

---

# 💡 Innovation

The project should not be described merely as:

> **"An AI system that predicts disasters."**

The central idea is the connection:

```text
DYNAMIC CONDITIONS
       ↓
FUTURE RISK
       ↓
VULNERABLE HABITATION
       ↓
PRIORITY
       ↓
POTENTIAL RELOCATION
       ↓
SAFETY
       ↓
CAPACITY
       ↓
AUTHORITY DECISION
```

The platform transforms dynamic multi-source information into **explainable, habitation-level relocation intelligence**.

---

# 🧭 Product Vision

```text
        DATA
         ↓
      FEATURES
         ↓
       MODEL
         ↓
        RISK
         ↓
     TRAJECTORY
         ↓
      PRIORITY
         ↓
    RELOCATION
         ↓
       SAFETY
         ↓
      CAPACITY
         ↓
     VERIFICATION
         ↓
       DECISION
```

The objective is to help disaster-management authorities move from primarily reactive response toward more proactive, evidence-based planning.

---

# 📌 Core Principle

> **Predict early. Identify clearly. Prioritize intelligently. Find potential alternatives. Verify safety. Support informed decisions.**

---

## Project Status

**Current development focus:**

```text
V1 Forward-Looking Prototype
Wayanad
Landslide
Rainfall
NOW / +24h / +72h
```

Historical validation, live ingestion and multi-hazard expansion are planned as subsequent development stages.

---

## License

Add the project's final license here once the team decides the appropriate licensing model.

---

## Disclaimer

This project is a **prototype decision-support system for disaster-management planning**.

Its predictions, risk assessments and relocation candidates are not substitutes for official warnings, field assessment, statutory restrictions, engineering assessment or decisions by competent authorities.

All estimated or model-generated outputs should be interpreted according to their stated data source, confidence and verification status.