# HAZIVA Incident Simulation Mode

This document specifies the design, backend execution engine, and user experience for HAZIVA Incident Simulation Mode ("What-If" Analysis).

## 1. Core Principles & Safety Boundaries

1. **User-Entered Input Boundary**: What-If scenario inputs are the ONLY user-entered values permitted in the operational demonstration.
2. **Backend Engine Reuse**: Simulations MUST exercise the exact same backend ML risk model (`model_a_with_gsi.joblib`) and dynamic rainfall-stress formula ($S = 1 - e^{-\alpha R}$) as the real-data path. Only the rainfall parameter is substituted.
3. **Strict Data Isolation**: Simulation results MUST NEVER overwrite, contaminate, or be saved to real database tables (`habitations`, `risks`, `relocation_sites`).
4. **Visual Labeling**: The UI MUST prominently label all simulated outputs with:
   `SIMULATION — NOT OBSERVED DATA`.

---

## 2. Simulation Execution Flow

```
                      OPERATOR / JUDGE
                             │
                             ▼
              [ CREATE INCIDENT / WHAT-IF ]
                             │
                - Select Habitation (e.g., Mananthavady)
                - Input Simulated Rainfall (e.g., 180 mm)
                - Select Horizon (24h or 72h)
                             │
                             ▼
              POST /habitations/{id}/simulate
                             │
                             ▼
                 BACKEND SIMULATION SERVICE
                             │
       ┌─────────────────────┴─────────────────────┐
       ▼                                           ▼
Fetch Real Habitation Static              Substitute Rainfall Input
Terrain Susceptibility ($P_{ml}$)              ($R_{sim} = 180\text{ mm}$)
       │                                           │
       └─────────────────────┬─────────────────────┘
                             │
                             ▼
                 DYNAMIC RISK ENGINE ($S = 1 - e^{-\alpha R}$)
                             │
                             ▼
                 SIMULATED RISK & TRAJECTORY
                             │
                             ▼
             SIDE-BY-SIDE UI COMPARISON PANEL
        (REAL OBSERVED vs. SIMULATED INCIDENT)
```

---

## 3. UI Demonstration Experience (Judge Scenario)

1. **Baseline View**: Judge selects a habitation (e.g. Mananthavady `hab_627296`) and views real current conditions:
   - Observed 24h Rainfall: `14.2 mm`
   - Current Risk: `0.42` (`Elevated`)
   - Forecast 24h: `28.5 mm`
2. **Trigger Incident Simulation**: Judge clicks `[ CREATE INCIDENT ]` modal, enters `180 mm` of rainfall over `24h`.
3. **Execution**: Frontend calls `POST /habitations/hab_627296/simulate` with payload `{"simulated_rainfall_mm": 180, "horizon": "24h"}`.
4. **Side-by-Side Result**: UI renders two side-by-side cards:
   - **REAL OBSERVED/FORECAST**: Risk `42%`, Trajectory `Stable`, Priority `High`.
   - **SIMULATED INCIDENT**: Risk `84%`, Trajectory `RAPIDLY INCREASING`, Priority `IMMEDIATE ASSESSMENT`.
5. **Clear Disclaimer**: Displays amber warning box:
   `SIMULATION — NOT OBSERVED DATA. Custom what-if scenario executed through Model A risk engine.`
