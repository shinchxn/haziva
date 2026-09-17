# PERSON 3 — BACKEND DEVELOPER

## Main Goal

Build the complete **backend system** that connects:

**Dataset/ML → Database → APIs → Frontend/Map/Relocation**

The backend is the central bridge between the intelligence produced by Persons 1–2 and the interfaces built by Persons 4–6.

---

# 1. Tech Stack

Use:

- **Python**
- **FastAPI**
- **PostgreSQL**
- **PostGIS**
- **Pydantic**
- **SQLAlchemy**
- **GeoAlchemy2** where required
- REST APIs
- Existing ML model/service from Persons 1–2

The backend must be structured so the ML/risk system can be connected without putting ML code into the frontend.

---

# 2. Build the Backend Architecture

Create this backend structure:

```text
Backend
│
├── API
│
├── Database
│
├── Habitation Services
│
├── Risk Services
│
├── Prediction Integration
│
├── Trajectory Services
│
├── Priority Services
│
├── Relocation Integration
│
└── System Status
```

The backend must act as the central integration layer.

---

# 3. PostgreSQL + PostGIS Database

Create the database foundation for the application.

Store geographic and intelligence data for:

### Habitations

- Habitation ID
- Name
- Location
- Geometry
- Population
- Households
- Exposure information
- Vulnerability information
- Accessibility information

### Risk

- Current risk
- 24-hour risk
- 72-hour risk
- Risk trajectory
- Confidence
- Prediction timestamp
- Risk drivers

### Relocation

- Site ID
- Location
- Geometry
- Safety status
- Candidate/rejected status
- Capacity
- Infrastructure information
- Accessibility
- Rejection reason

Use **PostGIS geometry fields** for geographic information.

---

# 4. Habitation API

Build:

```text
GET /habitations
```

This returns the available habitations with the information needed by the dashboard and map.

Example:

```json
{
  "id": "hab_001",
  "name": "Habitation A",
  "latitude": 11.6,
  "longitude": 76.0,
  "priority": "High",
  "current_risk": 0.72
}
```

---

# 5. Individual Habitation API

Build:

```text
GET /habitations/{id}
```

Return the complete available information for one habitation.

Include:

- Location
- Population
- Households
- Exposure
- Vulnerability
- Accessibility
- Current risk
- Future risk
- Priority

---

# 6. Risk API

Build:

```text
GET /habitations/{id}/risk
```

Return:

- Current risk
- 24-hour risk
- 72-hour risk
- Confidence
- Risk drivers
- Prediction timestamp

Example:

```json
{
  "current": 0.68,
  "risk_24h": 0.81,
  "risk_72h": 0.76,
  "confidence": 0.74,
  "drivers": [
    "High landslide susceptibility",
    "High recent rainfall",
    "High forecast rainfall"
  ]
}
```

The exact values must come from the actual prediction system.

---

# 7. Prediction Integration

Connect the backend to the ML model created by Persons 1–2.

The flow must be:

```text
Data
 ↓
Feature Engineering
 ↓
ML Model
 ↓
Prediction
 ↓
FastAPI
 ↓
Frontend
```

The backend should provide a clean interface for requesting or retrieving predictions.

---

# 8. Prediction Endpoint

Build:

```text
POST /predict
```

This endpoint should accept the required habitation/features input and return the model prediction.

Return information such as:

- Risk
- Confidence
- Risk drivers where available
- Prediction timestamp

The backend must not invent model results.

---

# 9. Risk Trajectory API

Build:

```text
GET /habitations/{id}/trajectory
```

Return the risk progression:

```text
Current
   ↓
24h
   ↓
72h
```

and the resulting trajectory state:

- Stable
- Increasing
- Rapidly Increasing
- Decreasing
- Critical

The trajectory must be generated from the actual risk values/model output.

---

# 10. Priority Integration

Connect risk results to the habitation priority system.

The backend must provide the priority result used by the frontend.

Example:

```text
Risk
 ↓
Future Risk
 ↓
Trajectory
 ↓
Exposure/Vulnerability
 ↓
Priority
```

Support:

- Low
- Medium
- High
- Immediate Assessment

The backend should expose the resulting priority through the habitation/risk APIs.

---

# 11. Risk Drivers

Store and return the actual factors contributing to the prediction.

Examples may include:

- Landslide susceptibility
- Slope
- Recent rainfall
- Accumulated rainfall
- Forecast rainfall
- Population exposure
- Accessibility
- Other model-supported features

Only return drivers that are actually available from the implemented model/feature pipeline.

---

# 12. Confidence

Return prediction confidence separately from risk severity.

Example:

```text
Risk: HIGH
Confidence: 74%
```

The API should make these separate fields so the frontend does not confuse them.

---

# 13. Relocation API

Integrate Person 6's relocation module.

Build:

```text
GET /habitations/{id}/relocation
```

Return:

- Habitation ID
- Potential relocation sites
- Candidate/rejected status
- Safety result
- Capacity
- Accessibility
- Infrastructure
- Rejection reason
- Site coordinates

Example:

```json
{
  "habitation_id": "hab_001",
  "sites": [
    {
      "site_id": "site_001",
      "status": "candidate",
      "safety": "pass",
      "capacity": 850
    }
  ]
}
```

---

# 14. Geographic API Support

Provide geographic information required by Person 5.

The API must be able to return:

- Habitation coordinates
- Risk-zone geometry where available
- Relocation-site coordinates
- Relevant infrastructure locations
- Other PostGIS geographic features required by the map

Use GeoJSON-compatible responses where appropriate.

---

# 15. System Status API

Build:

```text
GET /system/status
```

Return available system information such as:

```text
Last data update
Forecast horizon
Data availability
Model status
Data completeness
Prediction status
```

Example:

```json
{
  "model_status": "ready",
  "forecast_horizon": "72h",
  "data_status": "available",
  "last_update": "2026-09-17T10:30:00"
}
```

---

# 16. Real-Time/Future Prediction Integration

The backend must support the project's forward-looking workflow.

The intended flow is:

```text
Current Conditions
       ↓
Forecast Data
       ↓
Feature Update
       ↓
ML Prediction
       ↓
Current Risk
       ↓
24h Risk
       ↓
72h Risk
       ↓
Trajectory
       ↓
Priority
       ↓
Relocation
```

The API architecture should allow updated prediction results to replace previous results.

---

# 17. Frontend Integration

Person 4 should be able to build the complete dashboard using only the backend APIs.

The backend must provide everything needed for:

```text
Dashboard
Habitation Intelligence
Risk Cards
Risk Chart
Risk Drivers
Priority
Relocation
System Status
```

---

# 18. Map Integration

Person 5 should be able to build the complete map using the backend.

Provide geographic data for:

```text
Habitation
    ↓
Risk
    ↓
Priority
    ↓
Relocation Sites
```

All geographic IDs must remain consistent across the system.

---

# 19. End-to-End Integration

Connect all project components:

```text
P1/P2
Dataset + ML
     ↓
P3 Backend
     ↓
PostgreSQL/PostGIS
     ↓
FastAPI
     ↓
┌──────────┬───────────┬───────────┐
↓          ↓           ↓
P4 UI     P5 Map      P6 Relocation
```

The backend must become the single integration point.

---

# 20. Error Handling

Handle:

- Invalid habitation ID
- Missing prediction
- Missing geographic data
- ML service failure
- Database failure
- Relocation data unavailable
- Invalid API request

Return clean API errors that the frontend can display.

---

# 21. Final Working Flow

The backend must support this complete system flow:

```text
CURRENT DATA
     ↓
FORECAST
     ↓
ML MODEL
     ↓
RISK
     ↓
24H / 72H PREDICTION
     ↓
TRAJECTORY
     ↓
PRIORITY
     ↓
RELOCATION
     ↓
CAPACITY
     ↓
API
     ↓
DASHBOARD + MAP
```

---

# Final Build Target

Person 3 must deliver the **working backend/API layer** that allows the other team members to connect their modules into one system.

The finished backend must make this possible:

**Select Habitation → Get Current Risk → Get 24h/72h Risk → Get Trajectory → Get Priority → Get Relocation Sites → Get Capacity → Display Everything on Dashboard + Map.**