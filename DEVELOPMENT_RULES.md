# SIH 26191 — DEVELOPMENT RULES

## 1. Purpose

This document defines the mandatory development rules for the SIH 26191 project.

Every team member must follow these rules when writing code, creating datasets, training models, processing GIS data, designing APIs, or building the frontend.

The goal is to ensure that all six team members can work independently while producing one integrated system.

---

# 2. Core Product Rule

The project is a **disaster-management decision-support system**.

The system must follow:

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

The system must NOT become an autonomous evacuation system.

The correct principle is:

> **AI predicts and prioritizes. Humans verify. Authorities decide.**

---

# 3. V1 Scope Rule

V1 focuses on:

```text
Geography:
Wayanad, Kerala

Hazard:
Landslide

Dynamic driver:
Rainfall / forecast rainfall

Horizons:
Current
+24h
+72h
```

Do not expand the first prototype unnecessarily.

Do not add multiple hazards merely to make the project look more advanced.

---

# 4. Most Important Development Rule

## Build the forward-looking system first.

The first working pipeline must be:

```text
Current Conditions
        ↓
Forecast
        ↓
Feature Engineering
        ↓
Risk Model
        ↓
Current Risk
        ↓
24h Risk
        ↓
72h Risk
        ↓
Risk Trajectory
        ↓
Habitation Priority
        ↓
Relocation Candidates
        ↓
Safety Gate
        ↓
Capacity
```

Historical replay and backtesting come later.

Do not block the working prototype waiting for the historical validation system.

---

# 5. No Direct Push to Main

`main` is the stable branch.

No developer may directly push unfinished work to `main`.

Use:

```text
main
  ↑
Pull Request
  ↑
Feature Branch
```

Branch examples:

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
Create branch
      ↓
Develop
      ↓
Test
      ↓
Commit
      ↓
Push
      ↓
Pull Request
      ↓
Review
      ↓
Merge
```

---

# 6. Never Break Another Developer's Work

Before changing shared code:

1. Pull the latest branch.
2. Check recent commits.
3. Understand the existing implementation.
4. Make the smallest required change.
5. Test the affected functionality.

Do not rewrite another person's module simply because you prefer a different implementation.

If a change affects another person's interface, discuss it before merging.

---

# 7. Ownership Rules

## P1 — Dataset + ML Lead

Responsible for:

```text
Risk-engine foundation
Model architecture
Prediction pipeline
Risk trajectory
Model output contract
```

Primary area:

```text
ml/
```

---

## P2 — ML Engineer

Responsible for:

```text
Dataset preparation
Training data
Feature engineering
Training
Evaluation
Explainability
```

Primary areas:

```text
ml/data/
ml/features/
ml/training/
ml/explainability/
```

---

## P3 — Backend

Responsible for:

```text
PostgreSQL
PostGIS
FastAPI
Repositories
Services
API
ML ↔ backend integration
```

Primary area:

```text
backend/
```

---

## P4 — Frontend

Responsible for:

```text
Dashboard
Risk cards
Charts
Habitation UI
Relocation UI
System status
```

Primary area:

```text
frontend/
```

---

## P5 — Map / Geolocation

Responsible for:

```text
Interactive map
GIS visualization
Habitation locations
Hazard layers
Map interaction
Spatial UI
```

Primary areas:

```text
gis/
frontend/components/map/
```

---

## P6 — Relocation + Integration

Responsible for:

```text
Candidate-site search
Safety gate
Capacity assessment
Relocation evaluation
End-to-end integration
```

Primary area:

```text
relocation/
```

P6 must NOT become responsible for collecting or owning the main training dataset.

---

# 8. Shared Contract Rule

The following must be agreed before implementation:

```text
Database schema
API contract
Feature names
Risk output format
Risk levels
Trajectory labels
Relocation output format
```

Do not independently invent different names.

For example, if the backend uses:

```text
risk_score
```

the frontend must not independently expect:

```text
riskValue
```

unless an explicit API transformation exists.

---

# 9. Naming Convention

Use predictable names.

## Python

```text
snake_case
```

Example:

```python
risk_score
rainfall_24h
habitation_id
```

## JavaScript / TypeScript

```text
camelCase
```

Example:

```typescript
riskScore
rainfall24h
habitationId
```

## Database

Use:

```text
snake_case
```

Example:

```text
habitation_id
prediction_time
model_version
```

## API paths

Use lowercase resource-oriented paths:

```text
/habitations
/habitations/{id}
/habitations/{id}/risk
/habitations/{id}/relocation
```

---

# 10. No Magic Numbers

Do not place unexplained thresholds directly in code.

Bad:

```python
if risk > 70:
    priority = "HIGH"
```

Better:

```python
HIGH_RISK_THRESHOLD = config.high_risk_threshold
```

The source and justification of important thresholds must be documented.

---

# 11. No Hard-Coded Fake Results

Do not write:

```text
Wayanad risk = 87
```

inside the frontend simply to make the dashboard look functional.

If a value is simulated, label it as simulated.

Correct:

```text
Data Mode:
SIMULATION
```

Incorrect:

```text
Live rainfall:
87 mm
```

when the number is actually hard-coded.

---

# 12. No Fake Live Data

This is one of the strictest rules.

Never present:

```text
mock data
demo data
simulated data
historical data
estimated data
```

as:

```text
LIVE
CURRENT
REAL-TIME
OFFICIAL
```

unless it actually is.

Every important dataset should have metadata:

```text
source
timestamp
status
coverage
confidence
```

---

# 13. Data Source Rule

Every externally sourced dataset must record:

```text
Dataset name
Source organization
Source URL/reference
Acquisition date
Observation date
Spatial resolution
Coverage
Processing performed
License/usage information where applicable
```

Do not put undocumented datasets into the production pipeline.

---

# 14. Data Quality Rule

Before data reaches the ML model, check:

```text
Missing values
Invalid coordinates
Duplicate records
Incorrect units
Timestamp problems
Spatial reference problems
Outliers
Coverage gaps
```

A dataset is not considered ready simply because it loads successfully.

---

# 15. Units Must Be Explicit

Never assume units.

Examples:

```text
Rainfall:
mm

Elevation:
meters

Distance:
meters / kilometers

Population:
persons

Area:
square meters / hectares
```

If conversion occurs, document it.

Example:

```text
rainfall_in = rainfall_mm / 25.4
```

must not appear without knowing the original unit.

---

# 16. Coordinate Reference System Rule

GIS data must have an explicitly known CRS.

Never assume that two datasets are compatible because they both contain latitude/longitude-looking numbers.

Before spatial operations:

```text
Check CRS
    ↓
Transform if required
    ↓
Validate geometry
    ↓
Perform spatial operation
```

Document the CRS used by the project database and important derived datasets.

---

# 17. Geometry Validation

GIS processing must check for:

```text
Invalid geometry
Empty geometry
Self-intersections
Incorrect polygons
Duplicate geometries
```

Do not silently ignore geometry errors.

Record or report the affected records.

---

# 18. Database Rule

PostgreSQL/PostGIS is the source of truth for application data.

Do not create competing copies of important application state in:

```text
JSON files
frontend state
CSV files
random local databases
```

Temporary processing files are allowed, but the final application dataset belongs in the database.

---

# 19. Database Migration Rule

Database schema changes must be reproducible.

Do not manually change production tables without a migration.

Every schema change should have a migration.

Examples:

```text
add_habitations_table
add_risk_predictions
add_relocation_sites
add_capacity_fields
```

---

# 20. API Rule

API endpoints must have documented request and response formats.

For every important endpoint define:

```text
Method
Path
Parameters
Request body
Response
Errors
Authentication requirements
```

Example:

```text
GET /habitations/{id}/risk
```

Response:

```json
{
  "habitation_id": "H001",
  "current_risk": 0.48,
  "risk_24h": 0.67,
  "risk_72h": 0.81,
  "trajectory": "INCREASING",
  "confidence": 0.78
}
```

Values above are structural examples, not required prediction values.

---

# 21. Risk Score Rule

Risk severity and confidence are different concepts.

Never combine them into one unexplained number.

Example:

```text
Risk:
HIGH

Confidence:
MODERATE
```

The system should be able to communicate:

```text
High risk + low confidence
```

without incorrectly presenting the prediction as certain.

---

# 22. Risk Level Rule

Risk categories must be defined centrally.

Example:

```text
LOW
MEDIUM
HIGH
CRITICAL
```

The exact numerical boundaries must be documented.

Do not let different developers independently define:

```text
HIGH = 60
```

in one module and:

```text
HIGH = 70
```

in another.

---

# 23. Risk Trajectory Rule

Trajectory is based on the actual risk sequence.

Example:

```text
Current = 42
24h     = 59
72h     = 78

Trajectory = INCREASING
```

Possible states:

```text
STABLE
INCREASING
RAPIDLY INCREASING
DECREASING
CRITICAL
```

Do not manually assign trajectory labels to make a demonstration look better.

---

# 24. Prediction Rule

The model must predict risk from actual model features.

Do not create:

```text
risk_score = rainfall * 0.5 + population * 0.5
```

and call it ML unless this is explicitly documented as a baseline rule-based model.

If a statistical/ML model is used, preserve:

```text
model version
features
training dataset version
prediction timestamp
```

---

# 25. Model Rule

Start simple.

Preferred progression:

```text
Baseline
   ↓
Logistic Regression
   ↓
Tree-based model
   ↓
Gradient Boosting / XGBoost / LightGBM
   ↓
More complex models only if justified
```

Do not use deep learning simply because the project title contains AI.

The model must be justified by:

```text
Data availability
Performance
Interpretability
Computational requirements
Validation
```

---

# 26. Explainability Rule

If the dashboard says:

```text
Why is this habitation high risk?
```

the answer must come from actual model/input evidence.

Example:

```text
High susceptibility
High recent rainfall
High forecast rainfall
High population exposure
Limited accessibility
```

Do not generate generic explanations unrelated to the actual prediction.

---

# 27. No Data Leakage

Especially during historical validation, the model must not receive information that would not have been available at the prediction timestamp.

Correct:

```text
T-24 prediction
        ↓
Only information available by T-24
```

Incorrect:

```text
T-24 prediction
        ↓
Use rainfall measured after the disaster
```

Historical validation must preserve the original information timeline.

---

# 28. Historical Validation Rule

Historical validation is a separate layer.

When implemented:

```text
T-72
T-48
T-24
T-12
T-6
T-0
```

must run through the same prediction logic as the forward system wherever practical.

Do not build a completely different historical model just to produce better-looking validation results.

---

# 29. Relocation Rule

Relocation is not simply:

```text
Find highest score.
```

The order must be:

```text
Candidate Search
       ↓
Safety Gate
       ↓
Buildable Land
       ↓
Water
       ↓
Accessibility
       ↓
Infrastructure
       ↓
Capacity
       ↓
Candidate Evaluation
```

---

# 30. Safety Gate Is a Hard Constraint

A dangerous location cannot become acceptable merely because it scores well on:

```text
water
roads
land area
infrastructure
```

Example:

```text
Candidate A
Hazard:
UNACCEPTABLE

Result:
REJECTED
```

The rejection reason must be visible.

---

# 31. Capacity Rule

Do not represent relocation capacity as an arbitrary number.

Separate:

```text
Land Capacity
Water Capacity
Infrastructure Capacity
Accessibility
```

A conservative effective capacity may be:

```text
effective_capacity =
MIN(
    land_capacity,
    water_capacity,
    infrastructure_capacity
)
```

Only use this approach where its assumptions are appropriate and documented.

---

# 32. Estimated Data Rule

If capacity or infrastructure information is estimated:

```text
ESTIMATED
```

must be visible.

Example:

```text
Shelter Capacity:
1,200

Status:
Estimated — Authority Verification Required
```

Do not present estimates as officially approved capacities.

---

# 33. Authority Decision Rule

The final system should distinguish:

```text
AI Recommendation
```

from:

```text
Authority Decision
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

Never display:

```text
AI ORDER:
RELOCATE NOW
```

as if the system has legal authority.

---

# 34. Frontend Rule

The frontend must display the state of the data.

Useful labels include:

```text
LIVE
SIMULATION
HISTORICAL
ESTIMATED
STALE
UNAVAILABLE
```

Do not hide uncertainty to make the interface look cleaner.

---

# 35. Map Rule

The map must distinguish different information types.

At minimum:

```text
Hazard
Habitation
Risk
Priority
Relocation Candidate
Rejected Candidate
```

Do not overload one layer with multiple meanings.

---

# 36. Color Rule

Colors must have consistent semantic meaning.

For example:

```text
Green  → Low
Yellow → Medium
Orange → High
Red    → Critical
```

The exact palette can be changed during UI design, but the meaning must remain consistent throughout the application.

Never use red for something that means "safe" in another screen.

---

# 37. Dashboard Rule

The dashboard must answer these questions quickly:

```text
Where is the risk?
Which habitations require attention?
Is the risk increasing?
Why is the risk high?
What locations could be considered for relocation?
Are those locations safe?
How much capacity do they have?
What still requires human verification?
```

The dashboard is not merely a map.

---

# 38. Loading and Error States

Every data-dependent UI component must handle:

```text
Loading
Success
Empty
Error
Stale data
Unavailable source
```

Do not leave the user staring at an empty card when an API fails.

Example:

```text
Rainfall Data

⚠ Data unavailable
Last successful update:
14:20 IST
```

---

# 39. Backend Error Handling

Do not expose raw stack traces to users.

Bad:

```text
Traceback...
psycopg2...
```

Good:

```text
Unable to retrieve habitation risk.
Please retry or check data-source status.
```

Detailed errors should remain in server logs.

---

# 40. Logging Rule

Important operations should be traceable.

Log:

```text
Prediction execution
Model version
Data timestamp
Habitation ID
Processing errors
External data failures
API failures
Relocation evaluation failures
```

Never log secrets or sensitive credentials.

---

# 41. Environment Variables

Secrets must never be committed.

Do not commit:

```text
API keys
Database passwords
Private tokens
Cloud credentials
Secret URLs
```

Use:

```text
.env
```

locally and:

```text
.env.example
```

for required variable names.

Example:

```text
DATABASE_URL=
WEATHER_API_KEY=
MODEL_PATH=
```

`.env.example` must contain placeholders, not real credentials.

---

# 42. Frontend Security Rule

Do not expose server-only secrets to the browser.

Never put private credentials into frontend environment variables that are bundled into client-side JavaScript.

Sensitive operations must go through the backend.

Correct:

```text
Frontend
   ↓
FastAPI
   ↓
Private API
```

Not:

```text
Frontend
   ↓
Private API key
```

---

# 43. Testing Rule

Every developer must test their own module before opening a PR.

Minimum:

```text
Unit tests
Integration tests where applicable
Manual smoke test
```

Critical system path requires an end-to-end test.

---

# 44. First End-to-End Test

The project must eventually pass:

```text
Select habitation
      ↓
Retrieve current conditions
      ↓
Retrieve forecast
      ↓
Build features
      ↓
Run model
      ↓
Generate current risk
      ↓
Generate 24h risk
      ↓
Generate 72h risk
      ↓
Calculate trajectory
      ↓
Calculate priority
      ↓
Search relocation candidates
      ↓
Apply safety gate
      ↓
Calculate capacity
      ↓
Return dashboard result
```

This is the primary integration test.

---

# 45. Git Commit Rule

Commits should describe one logical change.

Good:

```text
feat: add habitation risk prediction endpoint
```

```text
feat: add relocation safety gate
```

```text
fix: handle missing rainfall observations
```

```text
docs: update API contract
```

Avoid:

```text
update
changes
final
final2
working
latest
```

---

# 46. Pull Request Rule

Every PR should explain:

```text
What changed?
Why was it changed?
What files/modules changed?
How was it tested?
Does it affect another developer?
Does it change an API/database/model contract?
```

If a contract changes, explicitly highlight it.

---

# 47. Documentation Rule

If implementation changes the architecture, update the relevant documentation.

Important documents:

```text
ARCHITECTURE.md
DEVELOPMENT_RULES.md
docs/database-schema.md
docs/api-contract.md
docs/ml-methodology.md
docs/relocation-methodology.md
```

Code and documentation must not contradict each other.

---

# 48. No Unnecessary Dependencies

Before adding a package, ask:

```text
Do we actually need it?
Is there already a package solving this?
Does it increase deployment complexity?
Does it work with the current stack?
```

Do not add large frameworks for small tasks.

---

# 49. No Premature Optimization

First make it:

```text
Correct
Testable
Understandable
Integrated
```

Then optimize.

Do not introduce:

```text
microservices
Kafka
Kubernetes
complex streaming architecture
distributed ML infrastructure
```

unless the actual project requirements justify them.

---

# 50. No "AI for the Sake of AI"

Every ML component must have a reason.

The system should answer:

```text
What is being predicted?
What data is used?
Why is ML appropriate?
How is it evaluated?
How is uncertainty represented?
```

If a simpler statistical method works, it is acceptable.

---

# 51. No Invented Accuracy

Never say:

```text
95% accurate
98% accurate
90% prediction
```

unless that number has actually been measured using a documented evaluation procedure.

Metrics must include:

```text
Dataset
Validation method
Metric
Population
Time period
Model version
```

---

# 52. No Invented Official Claims

Do not write:

```text
Government approved
Official evacuation zone
Official shelter
Government-certified safe land
```

unless the source explicitly establishes that status.

Use:

```text
Potential Candidate
Requires Verification
Estimated
Source: ...
```

when appropriate.

---

# 53. Uncertainty Rule

The system should communicate uncertainty rather than hiding it.

Example:

```text
Risk:
HIGH

Confidence:
MODERATE

Reason:
Forecast uncertainty + limited observation coverage
```

Uncertainty is part of the product, not a defect to hide.

---

# 54. Reproducibility Rule

A prediction should be reproducible from:

```text
Model version
Feature version
Input data
Input timestamp
Configuration
```

If someone asks:

> "Why did the system produce this result?"

the team should be able to trace the answer.

---

# 55. Model Versioning

Whenever the trained model changes, increment its version.

Example:

```text
landslide-risk-v1
landslide-risk-v2
```

Every prediction should record the model version.

---

# 56. Dataset Versioning

Training datasets should also have versions.

Example:

```text
training_dataset_v1
training_dataset_v2
```

Do not silently replace the dataset used for training.

---

# 57. Configuration Rule

Important configuration must be centralized.

Examples:

```text
Risk thresholds
Prediction horizons
Spatial resolution
Data refresh interval
Model path
Database configuration
```

Do not duplicate configuration across multiple files.

---

# 58. Integration Rule

Integration should happen continuously.

Do not wait until the final day to connect:

```text
ML
+
Backend
+
GIS
+
Frontend
+
Relocation
```

After each major module becomes functional, integrate it with the existing pipeline.

---

# 59. Demo Integrity Rule

During the final demonstration:

Every displayed result must have one of these states:

```text
LIVE
SIMULATION
HISTORICAL
ESTIMATED
```

The audience must be able to understand what they are seeing.

Never create a fake "live" dashboard purely for presentation.

---

# 60. Final Demo Flow

The intended demonstration should be:

```text
1. Open Command Dashboard
             ↓
2. Show Wayanad
             ↓
3. Select habitation
             ↓
4. Show current risk
             ↓
5. Show +24h prediction
             ↓
6. Show +72h prediction
             ↓
7. Show trajectory
             ↓
8. Show why risk changed
             ↓
9. Show habitation priority
             ↓
10. Open relocation analysis
             ↓
11. Show candidate locations
             ↓
12. Show rejected unsafe locations
             ↓
13. Show safety verification
             ↓
14. Show capacity
             ↓
15. Show authority verification state
```

---

# 61. Definition of Done

A feature is NOT complete merely because the code runs.

A feature is complete when:

```text
Code works
   +
Tests pass
   +
Errors handled
   +
Documentation updated
   +
No secrets committed
   +
Data provenance recorded
   +
API contract respected
   +
Integration verified
```

---

# 62. Conflict Resolution Rule

If two developers disagree about implementation:

### Step 1

Check:

```text
Problem Statement
ARCHITECTURE.md
API contract
Database schema
Team ownership
```

### Step 2

Prefer the solution that:

```text
Preserves existing contracts
Minimizes complexity
Improves reliability
Supports future extension
```

### Step 3

If still unresolved, the project lead makes the final integration decision.

---

# 63. Priority of Rules

When requirements conflict, use this order:

```text
1. Problem Statement
        ↓
2. Safety / correctness
        ↓
3. System architecture
        ↓
4. Data integrity
        ↓
5. API/database contracts
        ↓
6. Team ownership
        ↓
7. UI preferences
        ↓
8. Convenience
```

Never sacrifice correctness for visual appearance.

---

# 64. Golden Rules

Every team member must remember these:

```text
RULE 1
Do not push directly to main.

RULE 2
Do not fake live data.

RULE 3
Do not invent model accuracy.

RULE 4
Do not expose secrets.

RULE 5
Do not create unexplained thresholds.

RULE 6
Do not invent explanations.

RULE 7
Do not bypass the relocation safety gate.

RULE 8
Do not present AI recommendations as authority decisions.

RULE 9
Do not silently change shared API/database contracts.

RULE 10
Build the forward-looking pipeline first.

RULE 11
Keep risk severity separate from confidence.

RULE 12
Every important result must be traceable to its data and model version.
```

---

# 65. Final Engineering Principle

The project should always optimize for:

```text
TRUST
   +
TRACEABILITY
   +
INTERPRETABILITY
   +
SAFETY
   +
INTEGRATION
```

not merely:

```text
MORE AI
MORE FEATURES
MORE COMPLEXITY
```

The final system should demonstrate a clear chain of evidence:

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
AUTHORITY DECISION
```

If a developer cannot explain where a displayed result came from, that result is not ready for the final system.