# PERSON 6 — RELOCATION LOGIC & INTEGRATION

## Main Goal

Build the complete **Relocation Intelligence module** for the SIH 26191 prototype.

The module must answer:

> **When a habitation is identified as high priority, where are the potential safer relocation sites, are those sites actually suitable, and how many people can they support?**

Person 6 is responsible for the **relocation logic and connecting that logic to the complete system**.

---

# 1. Tech Stack

Use:

- **Python**
- **FastAPI** for relocation endpoints/integration
- **PostgreSQL + PostGIS** for geographic queries
- **GeoPandas / Shapely** where spatial processing is required
- Existing backend architecture from Person 3
- Existing frontend/map from Persons 4 and 5

Do not create a separate application or separate database.

---

# 2. Build the Relocation Intelligence Flow

Build this complete pipeline:

```text
High-Priority Habitation
          ↓
Find Potential Sites
          ↓
Safety Gate
          ↓
Buildable Land Check
          ↓
Water Check
          ↓
Accessibility Check
          ↓
Infrastructure Check
          ↓
Capacity Assessment
          ↓
Potential Relocation Site
```

A site should only become a valid candidate after passing the required safety and suitability checks.

---

# 3. Find Potential Relocation Sites

Build logic to identify geographic areas that could potentially serve as relocation sites for a high-priority habitation.

Consider:

- Geographic proximity
- Available/buildable land
- Hazard safety
- Road accessibility
- Water availability
- Essential infrastructure
- Population capacity

The system should produce a list of potential candidate sites.

---

# 4. Safety Gate

Build a **hard safety gate** before accepting a relocation site.

The safety gate must check whether the candidate conflicts with relevant hazard conditions.

Example:

```text
Candidate Site
      ↓
Hazard Safety Check
      ↓
PASS ─────────→ Continue
FAIL ─────────→ Reject
```

A site that fails a critical safety condition must not become a valid relocation recommendation merely because it has good capacity or infrastructure.

---

# 5. Candidate Site Evaluation

For every potential site, evaluate:

### Safety

- Hazard condition
- Relevant hazard susceptibility
- Safety-gate result

### Land

- Available land
- Buildable area
- Land capacity

### Water

- Water availability
- Estimated water capacity where data supports it

### Accessibility

- Road access
- Distance/access from affected habitation
- Accessibility condition

### Infrastructure

Where available:

- Healthcare
- Schools
- Roads
- Electricity
- Water infrastructure
- Other essential services

---

# 6. Capacity Assessment

Build the carrying-capacity calculation.

Capacity must not be based only on land area.

Evaluate separate constraints:

```text
Land Capacity
      ↓
Water Capacity
      ↓
Infrastructure Capacity
      ↓
Accessibility
      ↓
Effective Planning Capacity
```

Use the project's conservative principle:

```text
Effective Capacity =
minimum(
    land capacity,
    water capacity,
    infrastructure capacity
)
```

Only apply a capacity constraint when the required input is actually available.

All assumptions used for capacity calculations must be clearly represented in the result.

---

# 7. Candidate Result

Each relocation site returned by the system should contain information such as:

```text
Site ID
Location
Candidate Status
Safety Status
Hazard Check
Buildable Area
Land Capacity
Water Capacity
Infrastructure Capacity
Effective Capacity
Accessibility
```

Example:

```text
SITE-001

Status: Candidate
Safety Gate: PASS

Land Capacity: 1,000
Water Capacity: 900
Infrastructure Capacity: 850

Effective Capacity: 850

Accessibility: Available
```

---

# 8. Rejected Site Result

If a site fails a required condition, return it as rejected with the actual reason.

Example:

```text
SITE-002

Status: Rejected

Safety Gate: FAIL

Reason:
Candidate site intersects
high-hazard area.
```

Other possible reasons:

```text
Insufficient buildable land
Insufficient water capacity
Insufficient infrastructure
Poor accessibility
```

The reason must correspond to the actual failed check.

---

# 9. Relocation API

Integrate the relocation module with the existing backend.

Provide relocation information for a selected habitation.

The existing system expects:

```text
GET /habitations/{id}/relocation
```

This endpoint should return the relocation analysis for that habitation.

Example response structure:

```json
{
  "habitation_id": "hab_001",
  "priority": "Immediate Assessment",
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

Use the actual project backend schema agreed with Person 3.

---

# 10. Integration With Risk System

Connect relocation logic to the risk/priority result.

The flow must be:

```text
Risk Model
    ↓
Habitation Risk
    ↓
Priority
    ↓
Relocation Logic
```

For example:

```text
Habitation
    ↓
24h / 72h Risk
    ↓
Risk Trajectory
    ↓
Priority
    ↓
Relocation Analysis
```

The relocation module should use the backend's actual habitation priority.

Do not create a second risk model.

---

# 11. Integration With Map

Person 5's map must receive the relocation results.

The complete flow should work:

```text
High-Priority Habitation
          ↓
Relocation API
          ↓
Candidate Sites
          ↓
Map
          ↓
Display Candidate / Rejected Sites
```

Each site must contain geographic coordinates so Person 5 can display it on the map.

---

# 12. Integration With Frontend

Person 4's UI must be able to display:

- Candidate sites
- Rejected sites
- Safety result
- Capacity
- Accessibility
- Infrastructure
- Rejection reason

The frontend should receive this information from the backend.

---

# 13. Habitation-Specific Relocation

The relocation result must be connected to the selected habitation.

Example:

```text
Habitation A
     ↓
High Priority
     ↓
Relocation Analysis
     ↓
Site A
Site B
Site C
```

Different habitations may have different potential relocation sites.

Do not return one generic list for every habitation.

---

# 14. Relocation Ranking

After the safety gate removes unsuitable locations, organize the remaining candidate sites using the project's relevant suitability factors.

Consider:

- Safety
- Capacity
- Accessibility
- Infrastructure
- Distance/proximity
- Water availability
- Buildable land

The result should clearly distinguish:

**Eligible candidates** from **Rejected sites**.

Do not allow a ranking score to override a failed hard safety condition.

---

# 15. Integration With Database

Use the existing PostgreSQL/PostGIS database.

Store or retrieve:

```text
Relocation Sites
Site Geometry
Hazard Information
Land Information
Water Information
Infrastructure Information
Accessibility Information
Capacity Results
Safety-Gate Results
```

Coordinate with Person 3 for database/API integration.

Person 6 owns the relocation logic, not the overall database architecture.

---

# 16. End-to-End Integration

Person 6 must connect the completed project flow:

```text
CURRENT CONDITIONS
       ↓
FUTURE PREDICTION
       ↓
24H / 72H RISK
       ↓
RISK TRAJECTORY
       ↓
HABITATION PRIORITY
       ↓
RELOCATION LOGIC
       ↓
SAFETY GATE
       ↓
CAPACITY
       ↓
CANDIDATE SITES
       ↓
API
       ↓
DASHBOARD + MAP
```

This is the main integration responsibility.

---

# 17. Final User Flow

The finished system should allow:

```text
User opens Wayanad dashboard
        ↓
Selects high-priority habitation
        ↓
Views current / 24h / 72h risk
        ↓
Views priority
        ↓
Opens relocation intelligence
        ↓
System finds potential sites
        ↓
Safety gate checks sites
        ↓
Unsafe sites rejected
        ↓
Remaining sites evaluated
        ↓
Capacity calculated
        ↓
Candidate sites displayed
        ↓
Sites appear on map
```

---

# 18. Final Build Target

Person 6's completed module must provide a working **Risk → Relocation Intelligence connection**.

The system should be able to take:

**High-priority habitation**

and produce:

**Potential relocation sites + safety verification + capacity assessment + actual reasons for rejection.**

The final output must be usable by:

- Person 3's backend
- Person 4's dashboard
- Person 5's map

so the entire SIH 26191 prototype works as **one connected system**.