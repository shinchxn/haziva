# SIH 26191 — PROJECT KNOWLEDGE

> **Single Source of Truth for the Development Team**

---

# 1. Project Identity

## Problem Statement

**SIH Problem Statement ID:** 26191

**Organization:** Ministry of Home Affairs

**Department:** National Disaster Response Force (NDRF), DM Division

**Theme:** Disaster Management

**Category:** Software

---

# 2. Project Name

## AI-Powered Dynamic Habitation Risk & Relocation Intelligence System

The system is a GIS-enabled disaster-management decision-support platform.

Its purpose is to help authorities move from:

```text
DISASTER
   ↓
DAMAGE
   ↓
REACTIVE RELOCATION
```

toward:

```text
CHANGING CONDITIONS
        ↓
FUTURE RISK
        ↓
EARLY IDENTIFICATION
        ↓
PRIORITY ASSESSMENT
        ↓
RELOCATION PLANNING
        ↓
CAPACITY CHECK
        ↓
AUTHORITY DECISION
```

The project is therefore not simply an "AI disaster prediction system."

Its central contribution is connecting:

```text
Risk
+
Vulnerability
+
Habitation Priority
+
Relocation
+
Destination Capacity
```

into one decision-support workflow.

---

# 3. Problem in Simple Words

Many communities live in locations that may repeatedly experience natural hazards.

When conditions become dangerous, authorities need answers to questions such as:

```text
Which areas are becoming risky?

Which habitations require attention first?

Who is more vulnerable?

Is the risk increasing?

Why is the risk increasing?

Where could people potentially be relocated?

Is the destination itself sufficiently safe?

Can that destination accommodate the population?

What still needs human verification?
```

The platform attempts to connect these questions instead of treating them as separate systems.

---

# 4. Core Product Principle

The complete system follows:

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

The operating principle is:

> **AI predicts and prioritizes. Humans verify. Authorities decide.**

The system must never represent an AI recommendation as an official evacuation or relocation order.

---

# 5. What the System Predicts

The system does **not** claim exact disaster occurrence.

It must not say:

> "A landslide will definitely happen at this exact location at this exact time."

Instead, it estimates:

> **Future risk based on current observations, forecasts, geographic conditions, exposure and vulnerability.**

Example:

```text
Habitation X

Current Risk     58
24h Risk         66
72h Risk         82

Trajectory:
RAPIDLY INCREASING
```

The numerical values above are illustrative.

Actual values must be produced by the implemented system.

---

# 6. V1 Scope

## Pilot Geography

```text
Wayanad, Kerala
```

The first implementation should not attempt to cover all of India.

Start with a manageable subset of Wayanad habitations and potential relocation areas.

---

## Initial Hazard

```text
Landslide
```

---

## Primary Dynamic Driver

```text
Rainfall
Forecast rainfall
```

---

## Prediction Horizons

The core V1 system focuses on:

```text
NOW
+
24 HOURS
+
72 HOURS
```

The architecture can later support longer horizons and additional hazards.

---

# 7. Future Expansion

Possible future hazards include:

```text
Flood
Landslide
Coastal erosion
Cloudburst
Extreme heat
Cyclone
```

However:

> **Additional hazards must not delay the first working landslide prototype.**

---

# 8. Complete Product Workflow

The main workflow is:

```text
                  DATA SOURCES
                       ↓
              DATA INGESTION
                       ↓
        ┌──────────────┴──────────────┐
        ↓                             ↓
   STATIC DATA                   DYNAMIC DATA
        ↓                             ↓
        └──────────────┬──────────────┘
                       ↓
                FEATURE ENGINE
                       ↓
                 RISK MODEL
                       ↓
            CURRENT / FUTURE RISK
                       ↓
                TRAJECTORY
                       ↓
              PRIORITY ENGINE
                       ↓
           RELOCATION SEARCH
                       ↓
                SAFETY GATE
                       ↓
             CAPACITY ENGINE
                       ↓
            EXPLANATION / EVIDENCE
                       ↓
             AUTHORITY VERIFICATION
                       ↓
                FINAL DECISION
```

---

# 9. The Five Core Engines

The conceptual product consists of five major intelligence layers.

```text
ENGINE 1
Multi-Hazard / Red-Zone Intelligence

ENGINE 2
Predictive Risk

ENGINE 3
Habitation Vulnerability

ENGINE 4
Relocation Priority

ENGINE 5
Destination Carrying Capacity
```

---

# 10. Engine 1 — Multi-Hazard / Red-Zone Intelligence

The project specification defines a multi-hazard framework.

The normalized hazard components are:

```text
Flood
Landslide
Coastal erosion
Cloudburst / rainfall-intensity proxy
```

The composite hazard score is:

```text
Hᵢ =
w_f · Fᵢ
+
w_l · Lᵢ
+
w_c · Cᵢ
+
w_cb · CBᵢ
```

where all individual hazard values are normalized to:

```text
0 → 1
```

and the weights sum to:

```text
1
```

---

# 11. Red-Zone Hard Veto

A critical hazard must not disappear because other hazard values are low.

An area can become Red when:

```text
max(Fᵢ, Lᵢ, Cᵢ, CBᵢ) ≥ T_critical
```

OR:

```text
Hᵢ ≥ T_multi
```

OR:

```text
The area falls inside an applicable statutory exclusion.
```

The project specification gives examples such as applicable CRZ restrictions and other formally defined statutory exclusions.

The important principle is:

> **A severe individual hazard can independently trigger a critical classification.**



---

# 12. Risk Classes

The project uses:

| Class | Meaning |
|---|---|
| 🟢 Green | No modelled constraint detected; NOT a safety guarantee |
| 🟡 Yellow | Moderate risk; monitor |
| 🟠 Orange | High risk; review / mitigation |
| 🔴 Red | Critical/statutory/high multi-hazard risk; habitation review required |

These labels must be consistent across the system.

---

# 13. Severity vs Confidence

These are different concepts.

Example:

```text
Severity:
🔴 Critical

Confidence:
🟡 Medium
```

A high-risk result can have medium confidence.

Confidence should consider factors such as:

```text
Data age
Spatial resolution
Coverage gaps
Source reliability
Input completeness
Forecast uncertainty
```

Never convert uncertainty into false certainty.

---

# 14. Engine 2 — Predictive Risk

This is the main forward-looking intelligence layer.

The objective is to estimate how risk may change under current and forecast conditions.

```text
CURRENT CONDITIONS
        +
FORECAST
        +
STATIC FEATURES
        ↓
RISK MODEL
        ↓
FUTURE RISK
```

Core horizons:

```text
NOW
T+24h
T+72h
```

The system should be designed so that additional horizons can be added later.

---

# 15. Static vs Dynamic Data

This separation is fundamental.

## Static / Slowly Changing

Examples:

```text
Elevation
DEM
Slope
Landslide susceptibility
Historical hazard inventory
Population baseline
Road network
Critical infrastructure
Land use
Settlement information
```

---

## Dynamic

Examples:

```text
Recent rainfall
Rainfall accumulation
Forecast rainfall
Current hazard observations
Live environmental indicators
```

Static data can be processed once and reused.

Dynamic data must be updated as new observations become available.

---

# 16. Input Feature Groups

## Hazard Features

```text
Landslide susceptibility
Slope
Elevation / terrain
Recent rainfall
Rainfall accumulation
Forecast rainfall
Historical hazard evidence
```

## Exposure Features

```text
Population
Households
Settlement density
Buildings
Critical infrastructure exposure
```

## Vulnerability Features

```text
Housing/service indicators
Accessibility
Distance to essential services
Other defensible vulnerability indicators
```

The exact final feature set must be documented.

---

# 17. Risk Trajectory

A single risk number is not enough.

The system should show how risk changes over time.

Example:

```text
NOW       42
+24h      61
+48h      74
+72h      83
```

Possible trajectory states:

```text
DECREASING
STABLE
INCREASING
RAPIDLY INCREASING
CRITICAL
```

The trajectory must be derived from actual predicted values.

It must not be manually assigned for demonstration purposes.

---

# 18. Why Trajectory Matters

Consider:

```text
Village A

Now     75
24h     74
72h     76
```

versus:

```text
Village B

Now     45
24h     65
72h     85
```

A static dashboard might focus only on the current value.

The predictive system should also identify that Village B has rapidly escalating risk.

This supports earlier assessment and preparation.

---

# 19. Engine 3 — Habitation Vulnerability

Hazard alone does not determine impact.

Two habitations can experience similar hazard conditions but have different vulnerability.

The system can consider indicators such as:

```text
Elderly population
Children
Disability
SC/ST share
Poverty proxy
Housing fragility
Literacy deficit
Service accessibility
Population exposure
Infrastructure exposure
```

The project methodology proposes an explainable vulnerability structure using weighted indicators.

Example conceptual formula:

```text
Vᵢ =
0.15 · Elderly/Children
+
0.15 · Disability
+
0.15 · SC/ST share
+
0.15 · Poverty proxy
+
0.15 · Housing fragility
+
0.15 · Literacy deficit
+
0.10 · Service-access deficit
```

These indicators and weights must remain documented and defensible.



---

# 20. Exposure

Exposure represents what could be affected.

Examples:

```text
Population
Households
Buildings
Critical infrastructure
```

Exposure should remain conceptually separate from vulnerability.

Example:

```text
High population
=
High exposure

Fragile housing
=
High vulnerability
```

They should not automatically be treated as the same variable.

---

# 21. Explainability

Every important high-risk output should answer:

> **Why is this habitation high risk?**

Example:

```text
WHY?

✓ High landslide susceptibility
✓ High recent rainfall
✓ Heavy forecast rainfall
✓ High population exposure
✓ Limited accessibility
```

The explanation must come from actual input features/model evidence.

Never create generic explanations that do not correspond to the calculation.

---

# 22. Engine 4 — Relocation Priority

The system converts hazard, exposure and vulnerability into an operational priority.

The locked urgency formula is:

```text
Urgencyᵢ =
    0.45 · (Hᵢ × Exposureᵢ × Vᵢ)
  + 0.20 · Disaster_historyᵢ
  + 0.15 · Vᵢ
  + 0.10 · Access_deficitᵢ
  + 0.10 · Irreversibilityᵢ
```

Where:

```text
Hᵢ
= hazard score

Exposureᵢ
= population/building exposure

Vᵢ
= vulnerability

Disaster_historyᵢ
= normalized historical disaster evidence

Access_deficitᵢ
= evacuation/access limitation

Irreversibilityᵢ
= indicators such as active subsidence or repeated slope failure
```



---

# 23. Priority Tiers

The project uses:

```text
🔴 IMMEDIATE
🟠 SHORT-TERM
🟡 MEDIUM-TERM
```

## Immediate

Potential trigger:

```text
Statutory Red Zone
OR
Critical hazard + high vulnerability
```

## Short-Term

Potential trigger:

```text
High hazard
+
High vulnerability
+
No immediately ready relocation option
```

## Medium-Term

Potential trigger:

```text
Moderate/high risk
+
No immediate life threat
+
Mitigation/planned relocation may be possible
```

These categories support operational planning.

They are not automatic evacuation commands.

---

# 24. Important Relocation Principle

Destination capacity does **not** reduce the danger of the origin habitation.

For example:

```text
Origin:
CRITICAL RISK

Destination:
No suitable site
```

does NOT mean:

```text
Origin risk becomes lower.
```

Instead:

```text
Critical risk
      ↓
No suitable destination
      ↓
Escalation / alternative planning
```

The origin risk and destination feasibility are separate decisions.



---

# 25. Engine 5 — Destination Carrying Capacity

The system evaluates whether a potential destination can accommodate relocated people.

Capacity is not a single arbitrary number.

It considers:

```text
Land
Water
Infrastructure
Accessibility
```

Conceptually:

```text
LAND CAPACITY
      +
WATER CAPACITY
      +
INFRASTRUCTURE CAPACITY
      +
ACCESSIBILITY
      ↓
EFFECTIVE PLANNING CAPACITY
```

---

# 26. Land Capacity

The project methodology defines:

```text
C_land =
(buildable_area_ha × URDPFI_density_norm)
− existing_site_population
```

Reference density ranges in the project methodology include:

```text
Hill areas:
45–90 persons/ha

Plain areas:
75–125 persons/ha
```

The assumptions and selected value must be documented.



---

# 27. Capacity Constraints

A conservative planning approach can use:

```text
Effective Capacity =
MIN(
    Land Capacity,
    Water Capacity,
    Infrastructure Capacity
)
```

Accessibility should also be considered in site evaluation.

The capacity result should communicate whether it is:

```text
Measured
Estimated
Modelled
Requires Authority Verification
```

---

# 28. Relocation Pipeline

The relocation engine follows:

```text
High-Priority Habitation
        ↓
Candidate Areas
        ↓
Hazard Safety Gate
        ↓
Buildable Land
        ↓
Water
        ↓
Road / Accessibility
        ↓
Infrastructure
        ↓
Capacity
        ↓
Potential Candidate
```

---

# 29. Safety Gate

Safety is a hard constraint where appropriate.

A highly hazardous destination must not become acceptable simply because:

```text
Land = good
Water = good
Road = good
Infrastructure = good
```

Example:

```text
Candidate A

Hazard:
UNACCEPTABLE

Result:
REJECTED
```

The system should show:

```text
Rejected because:
High hazard conflict
```

---

# 30. Candidate Site Status

Candidate sites should have clear statuses.

Examples:

```text
POTENTIAL
SUITABLE FOR AUTHORITY ASSESSMENT
REJECTED
INSUFFICIENT DATA
REQUIRES VERIFICATION
```

Avoid claiming:

```text
SAFE
OFFICIALLY APPROVED
AUTHORIZED RELOCATION SITE
```

unless authoritative evidence explicitly supports that claim.

---

# 31. Data Sources

The project is expected to combine multiple data categories.

Potential source families include:

```text
NRSC / ISRO
GSI / National Landslide Forecasting Centre
IMD
Bhuvan / NRSC
Census of India
OpenStreetMap
Other authoritative/public datasets
```

The exact source used for each dataset must be recorded.

The project documents specifically identify NRSC/ISRO landslide information, GSI landslide information, IMD/weather data, Bhuvan/NRSC geospatial data, Census 2011 and OpenStreetMap as useful source categories.

---

# 32. Population Data Limitation

Census 2011 can provide important baseline population information.

However:

```text
Census 2011
≠
Current population
```

Therefore the application must not silently present historical census data as current real-time population.

Use a label such as:

```text
Population:
Census 2011 baseline
```

when that is the underlying source.

---

# 33. Live Data

The final architecture should support live inputs such as:

```text
Rainfall
Weather forecast
GIS updates
Government observations
```

The conceptual flow is:

```text
LIVE DATA
    ↓
INGESTION
    ↓
VALIDATION
    ↓
FEATURE UPDATE
    ↓
MODEL
    ↓
NEW RISK
    ↓
NEW PRIORITY
```

However, live ingestion should be implemented after the core prediction pipeline works.

---

# 34. Simulation Mode

The system may support simulation for development and demonstration.

Simulation is useful for testing:

```text
Risk increase
Risk decrease
Forecast changes
Priority changes
Relocation workflow
```

But simulated values must be clearly labelled:

```text
SIMULATION
```

Never display simulated values as real-time observations.

---

# 35. Historical Validation

Historical validation is a separate stage.

After the forward prediction system works:

```text
Historical Event
       ↓
Determine information available at T-72
       ↓
Feed information into SAME ENGINE
       ↓
Prediction
       ↓
Compare against actual event
```

The same prediction engine should be reused.

Do not redesign the model specifically to make one historical event look successful.

---

# 36. Historical Replay

Historical replay comes after historical validation.

Timeline:

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

The system can then visualize how risk and priority changed as the event approached.

This is a validation/demo layer.

It is not the first implementation target.

---

# 37. Prediction vs Validation

The team must keep these concepts separate.

## Prediction

Question:

> **What may happen under the current/projected conditions?**

Uses:

```text
Current conditions
Forecast
Terrain
Hazard
Exposure
Vulnerability
```

## Validation

Question:

> **Did the prediction perform reasonably when tested against historical events?**

Uses:

```text
Historical event data
Pre-event observations
Actual event outcome
```

---

# 38. First Working Milestone

The entire team should aim for this:

```text
SELECT HABITATION
        ↓
GET CURRENT CONDITIONS
        ↓
GET FUTURE FORECAST
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
PRIORITY
        ↓
POTENTIAL RELOCATION SITES
        ↓
SAFETY GATE
        ↓
CAPACITY
```

If this complete path works:

> **Prototype V1 is functional.**



---

# 39. Day 1 Target

The first development target is:

```text
DATA
  ↓
DATABASE
  ↓
MODEL
  ↓
API
  ↓
BASIC UI
```

Day 1 should establish the foundations.

---

# 40. Day 2 Target

Connect:

```text
Current Conditions
      ↓
Prediction
      ↓
24h / 72h Risk
      ↓
Trajectory
      ↓
Priority
      ↓
Relocation
      ↓
Capacity
```

The target is:

> **One complete end-to-end working flow.**

---

# 41. Day 3 Target

Focus on:

```text
Data correctness
Model sanity
API reliability
GIS correctness
Explainability
Relocation logic
UI polish
Demo reliability
```

Do not spend the final day adding unnecessary technologies.



---

# 42. Six-Person Team

## P1 — ML Lead

Owns:

```text
Future risk model
Prediction pipeline
24h / 72h prediction
Model integration
Risk trajectory
```

Deliverable:

```text
risk_engine
```

---

## P2 — ML/Data Engineer

Owns:

```text
Training dataset
Feature engineering
Data quality
Model evaluation
Explainability
Uncertainty/confidence
```

Deliverables:

```text
features/
training_dataset/
model_metrics/
```

---

## P3 — GIS/Data Engineer

Owns:

```text
Wayanad geographic data
Habitations
DEM
Slope
Landslide susceptibility
Population layers
Roads
Infrastructure
Candidate relocation geography
```

Deliverable:

```text
Wayanad GIS dataset
```

---

## P4 — Backend Engineer

Owns:

```text
PostgreSQL
PostGIS
FastAPI
Data ingestion
API
ML service integration
```

Core endpoints:

```text
GET /habitations

GET /habitations/{id}

GET /habitations/{id}/risk

GET /habitations/{id}/trajectory

GET /habitations/{id}/relocation

POST /predict
```

---

## P5 — Frontend / Map Engineer

Owns:

```text
React dashboard
Interactive map
Risk layers
Charts
Habitation details
Risk trajectory visualization
```

---

## P6 — Relocation + Integration

Owns:

```text
Candidate-site engine
Safety gate
Capacity assessment
Infrastructure checks
End-to-end integration
Final demo workflow
```

---

# 43. Team Dependency Flow

The major dependency chain is:

```text
P3 GIS/Data
     ↓
P1 + P2 ML
     ↓
P4 Backend
     ↓
P5 Frontend
     ↓
P6 Relocation / Integration
```

However, development should happen in parallel wherever interfaces are already defined.

---

# 44. Technical Stack

## Frontend

```text
React
MapLibre GL JS or Leaflet
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

## ML

```text
Python
pandas
NumPy
scikit-learn
```

Optional:

```text
XGBoost
LightGBM
```

only if justified.

## GIS

```text
GeoPandas
Rasterio
GDAL
PostGIS
```

---

# 45. Repository Structure

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

# 46. What V1 Must Do

V1 must demonstrate:

```text
✓ Wayanad pilot geography
✓ Habitation selection
✓ Current conditions
✓ Forecast conditions
✓ Risk prediction
✓ 24h prediction
✓ 72h prediction
✓ Risk trajectory
✓ Vulnerability
✓ Explainability
✓ Priority assessment
✓ Relocation candidate search
✓ Safety gate
✓ Capacity assessment
✓ Decision dashboard
```

---

# 47. What V1 Should NOT Depend On

Do not make these mandatory before the core prototype works:

```text
✗ Full India coverage
✗ Every possible hazard
✗ Autonomous evacuation
✗ Mobile application
✗ Deep learning
✗ Real-time satellite processing
✗ Historical replay UI
✗ Massive cloud infrastructure
✗ Dozens of external APIs
```

---

# 48. Innovation

The project should not be presented simply as:

> **"AI predicts disasters."**

The stronger system concept is:

```text
FUTURE RISK
      ↓
VULNERABLE HABITATION
      ↓
PRIORITY ASSESSMENT
      ↓
POTENTIAL SAFER DESTINATION
      ↓
CARRYING CAPACITY
```

This connects predictive hazard intelligence to proactive relocation planning.

---

# 49. What Makes the Workflow Different

Traditional conceptual flow:

```text
Hazard Map
    ↓
Risk
```

This project:

```text
Dynamic Conditions
        ↓
Future Risk
        ↓
Risk Trajectory
        ↓
Vulnerable Habitation
        ↓
Priority
        ↓
Potential Relocation
        ↓
Safety Verification
        ↓
Capacity
        ↓
Authority Decision
```

The value is the **connection between these stages**.

---

# 50. Trust Requirements

The system must always distinguish:

```text
Observed
Predicted
Estimated
Simulated
Historical
Verified
Unverified
```

Examples:

```text
Observed rainfall
Predicted 24h risk
Estimated capacity
Historical population
Simulated forecast
Authority-verified site
```

These terms must not be mixed.

---

# 51. No False Precision

Do not show:

```text
Risk = 83.47291
```

unless that precision has a real meaning.

Similarly, do not claim:

```text
Relocation capacity = 5,237 people
```

when the number is based on a rough assumption.

The precision of the output should reflect the quality of the underlying data.

---

# 52. No False Accuracy

Never claim:

```text
95% accurate
98% accurate
90% prediction
```

without a documented evaluation.

When validation is eventually performed, report:

```text
Dataset
Time period
Validation method
Metrics
Model version
Limitations
```

---

# 53. No Autonomous Decision-Making

The system can provide:

```text
Risk
Priority
Suggested candidate
Safety assessment
Capacity estimate
```

The authority makes the final decision.

Correct:

```text
AI Assessment:
HIGH PRIORITY

Suggested:
FIELD VERIFICATION

Authority Decision:
PENDING
```

---

# 54. Core Demo Story

The final demonstration should tell one continuous story.

```text
A habitation is selected.
        ↓
Current conditions are examined.
        ↓
Forecast conditions are introduced.
        ↓
Risk is projected into the future.
        ↓
The trajectory shows whether risk is increasing.
        ↓
The system explains the main drivers.
        ↓
The habitation receives an assessment priority.
        ↓
Potential relocation areas are searched.
        ↓
Unsafe candidates are rejected.
        ↓
Remaining candidates are evaluated.
        ↓
Capacity is estimated.
        ↓
The authority receives evidence for verification
and decision-making.
```

---

# 55. Final Product Vision

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
                 FUTURE RISK MODEL
                         ↓
                    24h / 72h
                         ↓
                  RISK TRAJECTORY
                         ↓
                HABITATION PRIORITY
                         ↓
               RELOCATION INTELLIGENCE
                         ↓
                   SAFETY GATE
                         ↓
                CARRYING CAPACITY
                         ↓
                 EXPLANATION
                         ↓
               AUTHORITY VERIFICATION
                         ↓
                  FINAL DECISION
```

---

# 56. The One Sentence Every Team Member Should Know

> **We transform changing hazard and environmental conditions into explainable future-risk intelligence, habitation-level priority assessment, and safety- and capacity-aware relocation planning for disaster-management authorities.**

---

# 57. The One Rule Every Team Member Must Remember

> **Build the forward system first. Validate it against history later.**

The first target is:

```text
CURRENT
  ↓
FUTURE RISK
  ↓
PRIORITY
  ↓
RELOCATION
  ↓
CAPACITY
```

Only after that works:

```text
HISTORICAL DATA
       ↓
SAME ENGINE
       ↓
VALIDATION
       ↓
HISTORICAL REPLAY
```

---

# 58. Definition of a Successful Prototype

The project is successful at V1 when a user can select a Wayanad habitation and the system can execute:

```text
SELECT HABITATION
        ↓
CURRENT CONDITIONS
        ↓
FORECAST
        ↓
RISK MODEL
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
SAFETY CHECK
        ↓
CAPACITY CHECK
        ↓
EXPLAINABLE DASHBOARD
```

That is the **core product**.

Everything else is an extension of this foundation.