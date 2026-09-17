# PERSON 5 — MAP & GEOLOCATION DEVELOPER

## Main Goal

Build the complete **interactive GIS/map system** for the SIH 26191 prototype.

The map must make it possible to visually understand:

**Where the habitations are → Where risk exists → Which habitations are high priority → Where potential relocation sites are.**

The map must work with the real backend/API and project data.

---

# 1. Tech Stack

Use:

- **React** — map UI integration
- **MapLibre GL JS** — interactive map
- **GeoJSON** — geographic features and layers
- **PostGIS data through backend APIs** — geographic data source
- **REST APIs** — receive habitation, risk, priority and relocation information from Person 3's backend

Do not create a separate backend or database.

---

# 2. Build the Main Wayanad Map

Create the main interactive map for the Wayanad pilot area.

The initial map must display:

- Wayanad boundary
- Habitation locations
- Risk information
- Priority habitations
- Potential relocation sites

The map should open focused on the Wayanad study area.

---

# 3. Habitation Map Layer

Create a dedicated habitation layer.

Each habitation must have:

- Habitation ID
- Habitation name
- Latitude
- Longitude
- Current risk
- 24-hour risk
- 72-hour risk
- Risk trajectory
- Priority

The map marker/status must use the values received from the backend.

Example flow:

```text
Backend
   ↓
Habitation API
   ↓
Habitation location + risk data
   ↓
Map
   ↓
Habitation marker
```

---

# 4. Risk Visualization

Create a geographic risk visualization.

The user must be able to immediately identify different risk levels on the map.

Support the project's risk states:

- Low
- Medium
- High
- Critical

The risk visualization should update when new backend prediction data becomes available.

The frontend must not calculate the risk.

It only displays the model result received from the backend.

---

# 5. Priority Habitation Visualization

Show habitations requiring attention prominently.

Use the priority information from the backend.

Support:

- High
- Immediate Assessment

A user looking at the map should quickly identify:

> “Which habitations need attention?”

---

# 6. Habitation Selection

When the user clicks a habitation marker, open a map popup containing its essential information.

Example:

```text
Habitation Name

Current Risk: High
24h Risk: Very High
72h Risk: High

Trajectory:
Rapidly Increasing

Priority:
Immediate Assessment

[View Habitation Intelligence]
```

The **View Habitation Intelligence** action must connect to Person 4's habitation intelligence interface.

---

# 7. Relocation Site Layer

Create a separate relocation-site layer.

Display potential relocation sites received from the relocation backend.

Each site should contain:

- Site ID
- Location
- Candidate status
- Safety status
- Capacity
- Accessibility
- Infrastructure information

Example:

```text
◇ Relocation Site A

Status: Candidate
Safety: Pass
Capacity: 850
Access: Available
```

---

# 8. Rejected Relocation Sites

If the relocation system returns a rejected site, the map should be able to display it separately.

When selected:

```text
Relocation Site B

Status: Rejected

Reason:
Safety gate failed
```

The rejection reason must come from the relocation logic/backend.

---

# 9. Risk-to-Relocation Connection

Implement the geographic relationship between a high-priority habitation and its potential relocation sites.

When a high-priority habitation is selected:

```text
High-Priority Habitation
          ↓
Potential Relocation Sites
          ↓
Candidate Locations
```

The map should make the relationship spatially understandable.

---

# 10. Map Layers

Create independent geographic layers for:

```text
BASE MAP
   │
   ├── Wayanad Boundary
   ├── Risk Areas
   ├── Habitations
   ├── Priority Habitations
   ├── Relocation Sites
   └── Roads / Infrastructure
```

Provide layer controls so the user can turn relevant layers on/off.

---

# 11. Map Legend

Create a clear legend explaining the map symbols.

It should explain:

### Risk

- Low
- Medium
- High
- Critical

### Priority

- High
- Immediate Assessment

### Relocation

- Candidate
- Rejected

The legend should always make the map understandable.

---

# 12. Map Controls

Implement the essential map controls:

- Zoom in/out
- Pan
- Reset/fit to Wayanad
- Layer visibility
- Selected-location focus
- Habitation selection
- Relocation-site selection

---

# 13. Backend Integration

Connect the map to Person 3's APIs.

The map should consume backend data for:

### Habitations

```text
GET /habitations
GET /habitations/{id}
```

### Risk

```text
GET /habitations/{id}/risk
```

### Trajectory

```text
GET /habitations/{id}/trajectory
```

### Relocation

```text
GET /habitations/{id}/relocation
```

Use the actual API response structure agreed with Person 3.

Do not hard-code the project's final risk or relocation results.

---

# 14. GeoJSON Handling

Convert geographic API data into map-ready GeoJSON where required.

Support:

- Point features for habitations
- Point features for relocation sites
- Polygon features for boundaries/risk zones
- Line features for roads where available

Keep geographic data handling separate from the visual UI.

---

# 15. Map ↔ Dashboard Integration

The map must integrate with Person 4's dashboard.

Complete flow:

```text
COMMAND DASHBOARD
       ↓
WAYANAD MAP
       ↓
SELECT HABITATION
       ↓
HABITATION INFORMATION
       ↓
VIEW INTELLIGENCE
       ↓
CURRENT RISK
       ↓
24H RISK
       ↓
72H RISK
       ↓
PRIORITY
       ↓
RELOCATION SITES
```

The selected habitation ID must remain consistent throughout the flow.

---

# 16. Real-Time/Future Prediction Display

The prototype is designed around future prediction.

Therefore the map must be able to display updated:

- Current risk
- 24-hour risk
- 72-hour risk
- Risk trajectory
- Priority

When the backend produces updated predictions, the map should be capable of refreshing the displayed information.

The map itself does not perform the prediction.

---

# 17. Visual Priority

The map should make the following hierarchy immediately understandable:

```text
Wayanad
   ↓
Habitations
   ↓
Risk
   ↓
High-Priority Habitations
   ↓
Potential Relocation Sites
```

The most important information should be visually prominent without making the map cluttered.

---

# 18. Final Working Flow

The completed Person 5 module should support this complete interaction:

```text
OPEN SYSTEM
     ↓
WAYANAD MAP
     ↓
SEE HABITATIONS
     ↓
SEE RISK
     ↓
IDENTIFY HIGH-PRIORITY HABITATIONS
     ↓
CLICK HABITATION
     ↓
SEE CURRENT / 24H / 72H RISK
     ↓
SEE TRAJECTORY
     ↓
SEE PRIORITY
     ↓
SEE POTENTIAL RELOCATION SITES
     ↓
CLICK RELOCATION SITE
     ↓
SEE SITE STATUS + CAPACITY + SAFETY
```

---

# 19. Final Build Target

At the end, Person 5 should deliver a working **Wayanad GIS interface** where the user can visually move from:

**Risk → Habitation → Priority → Relocation**

and all displayed information comes from the project's actual backend/data pipeline.

### Person 5 owns:

**The complete geographic visualization and map interaction layer of the SIH 26191 system.**