# PERSON 4 — FRONTEND & UI DEVELOPER

## Main Goal

Build the complete **frontend/dashboard interface** for the SIH 26191 prototype.

The frontend must allow an authority/user to understand:

**Current Risk → Future Risk → Risk Trajectory → Priority → Relocation Intelligence**

The frontend receives all intelligence from the backend APIs and presents it clearly.

---

# 1. Tech Stack

Use:

- **React**
- **Next.js**
- **TypeScript**
- **Tailwind CSS**
- **Recharts** for risk/trajectory charts
- **MapLibre GL JS map integration** from Person 5
- REST API integration with Person 3's FastAPI backend

The frontend must be connected to the existing backend rather than implementing ML or relocation calculations itself.

---

# 2. Build the Main Command Dashboard

Create the main disaster-management dashboard.

The dashboard should contain:

```text
WAYANAD OVERVIEW

┌─────────────────────────────────────┐
│ Current Overall Status              │
│                                     │
│ High-Priority Habitations: XX      │
│ Immediate Assessments: XX          │
│                                     │
│ Current Risk / Future Risk         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│                                     │
│          INTERACTIVE MAP            │
│                                     │
└─────────────────────────────────────┘
```

The dashboard must provide an immediate overview of the Wayanad pilot.

---

# 3. Risk Summary Cards

Build dashboard cards for the important system-level information.

Show:

- Current risk status
- 24-hour risk
- 72-hour risk
- High-priority habitation count
- Immediate-assessment count
- Overall system status

Example:

```text
CURRENT RISK
HIGH

24H RISK
VERY HIGH

72H RISK
HIGH

PRIORITY
12 HABITATIONS
```

Values must come from the backend.

---

# 4. Habitation Intelligence Page

Build a detailed page for an individual habitation.

When the user selects a habitation from the map/dashboard, open:

```text
HABITATION INTELLIGENCE
```

Display:

- Habitation name
- Current risk
- 24h risk
- 72h risk
- Risk trajectory
- Priority
- Exposure
- Vulnerability
- Accessibility
- Major risk drivers

---

# 5. Current + Future Risk

Create a clear visual comparison:

```text
CURRENT        24 HOURS        72 HOURS

  HIGH          VERY HIGH        HIGH
```

The user should immediately understand how the risk is changing over time.

---

# 6. Risk Trajectory

Build a risk trajectory visualization.

Support the project's trajectory states:

- Stable
- Increasing
- Rapidly Increasing
- Decreasing
- Critical

Also provide a chart showing the available risk progression.

Example:

```text
RISK
HIGH │             ●
     │        ●
MED  │   ●
     │
LOW  └────────────────────
       NOW    24H    72H
```

Use **Recharts** for the chart.

---

# 7. “Why Is the Risk High?” Section

Build an explainability section.

When the backend provides risk drivers, display them clearly.

Example:

```text
WHY IS THIS HABITATION HIGH RISK?

✓ High landslide susceptibility
✓ High recent rainfall
✓ High forecast rainfall
✓ High population exposure
✓ Limited accessibility
```

The frontend must display the actual drivers returned by the backend.

Do not invent explanations in the frontend.

---

# 8. Risk vs Confidence

Clearly separate:

**Risk severity**

from

**Prediction confidence**

Example:

```text
RISK
HIGH

CONFIDENCE
72%
```

The interface must make it clear that:

> High risk does not automatically mean high certainty.

Use the confidence value supplied by the backend/model.

---

# 9. Exposure Information

Create an exposure section.

Display available information such as:

- Population
- Households
- Population density
- Critical infrastructure
- Other exposed assets

Example:

```text
EXPOSURE

Population       1,240
Households         320
Critical Assets      4
```

---

# 10. Vulnerability Information

Create a separate vulnerability section.

Display the vulnerability indicators provided by the backend.

Example:

```text
VULNERABILITY

Housing vulnerability
Accessibility limitation
Essential-service distance
```

Do not calculate vulnerability in the frontend.

---

# 11. Priority Section

Make the habitation's intervention priority clearly visible.

Support:

- Low
- Medium
- High
- Immediate Assessment

Example:

```text
INTERVENTION PRIORITY

IMMEDIATE ASSESSMENT
```

The priority must come from the backend.

---

# 12. Relocation Intelligence Section

Build a relocation section inside the habitation intelligence page.

Display:

```text
RELOCATION INTELLIGENCE

Potential Sites: 3

Site A
Safety: PASS
Capacity: 850

Site B
Safety: PASS
Capacity: 620

Site C
Rejected
Reason: Hazard safety gate failed
```

The frontend only displays the relocation results provided by Person 6/backend.

---

# 13. Relocation Site Details

When a candidate site is selected, show:

- Site location
- Candidate status
- Safety status
- Capacity
- Land capacity
- Water capacity
- Infrastructure capacity
- Accessibility
- Rejection reason if rejected

Provide a clear separation between:

**Candidate**

and

**Rejected**

sites.

---

# 14. Map Integration

Integrate Person 5's map into the dashboard.

The frontend must support:

```text
MAP
 ↓
Select Habitation
 ↓
Habitation Intelligence
```

and:

```text
Habitation Intelligence
 ↓
Relocation Sites
 ↓
View on Map
```

The selected habitation/site must remain synchronized between the UI and map.

---

# 15. System Status

Create a system/data status area.

Display available backend status information such as:

- Last data update
- Forecast horizon
- Data source status
- Data completeness
- Prediction confidence/uncertainty

Example:

```text
SYSTEM STATUS

Last update: 10:30 AM
Forecast: 72 hours
Weather data: Available
GIS data: Available
Model status: Ready
```

Use the actual backend status.

---

# 16. API Integration

Connect the frontend to Person 3's backend APIs.

Use the project endpoints:

```text
GET /habitations
GET /habitations/{id}
GET /habitations/{id}/risk
GET /habitations/{id}/trajectory
GET /habitations/{id}/relocation
GET /system/status
```

The frontend should update when backend prediction data changes.

---

# 17. Dashboard Navigation

Build simple navigation between:

```text
Dashboard
   │
   ├── Map
   │
   ├── Habitation Intelligence
   │
   ├── Relocation Intelligence
   │
   └── System Status
```

The primary workflow should remain focused on disaster-risk decision support.

---

# 18. Loading and Error States

Every API-driven section must handle:

### Loading

```text
Loading risk information...
```

### Error

```text
Unable to load risk information.
```

### No data

```text
No relocation information available.
```

The interface must not break when an API temporarily fails or data is unavailable.

---

# 19. Main User Flow

The completed frontend must support this complete journey:

```text
OPEN DASHBOARD
      ↓
SEE WAYANAD OVERVIEW
      ↓
SEE RISK MAP
      ↓
IDENTIFY HIGH-PRIORITY HABITATION
      ↓
SELECT HABITATION
      ↓
CURRENT RISK
      ↓
24H RISK
      ↓
72H RISK
      ↓
RISK TRAJECTORY
      ↓
WHY IS RISK INCREASING?
      ↓
EXPOSURE + VULNERABILITY
      ↓
INTERVENTION PRIORITY
      ↓
RELOCATION INTELLIGENCE
      ↓
CANDIDATE SITES
      ↓
CAPACITY + SAFETY
      ↓
VIEW ON MAP
```

---

# 20. Final UI Target

The final frontend should feel like a **professional disaster-management decision-support dashboard**, not a normal analytics website.

The most important information must be visible quickly:

**WHERE IS THE RISK?**

→ Map

**WHAT IS HAPPENING?**

→ Current Risk

**WHAT MAY HAPPEN?**

→ 24h / 72h Prediction

**IS THE RISK CHANGING?**

→ Trajectory

**WHY?**

→ Risk Drivers

**WHO NEEDS ATTENTION?**

→ Priority

**WHERE COULD THEY GO?**

→ Relocation Sites

**CAN THE SITE SUPPORT THEM?**

→ Capacity

---

## Final Build Result

Person 4 must deliver the complete frontend that connects:

**Backend Intelligence + Map + Risk Prediction + Priority + Relocation**

into one understandable interface for the SIH 26191 prototype.