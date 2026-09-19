# HAZIVA Live Weather Architecture

This document specifies the live weather integration architecture for retrieving, parsing, caching, and applying real observed and forecast rainfall data to the HAZIVA risk engine.

## 1. Provider & Data Specification

- **Provider**: Open-Meteo Weather API / ECMWF IFS Forecast Model
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Target Coordinates**: Latitude `11.65°N`, Longitude `76.13°E` (Wayanad District Center)
- **Authentication**: Public / No API Key required (Open Data License)
- **Parameters**:
  - `latitude=11.65`
  - `longitude=76.13`
  - `current=precipitation,rain`
  - `hourly=precipitation,rain`
  - `past_days=3`
  - `forecast_days=3`
  - `timezone=Asia/Kolkata`

## 2. Dynamic Rainfall Data Pipeline

```
              ┌──────────────────────────────────────────────┐
              │  OPEN-METEO API (https://api.open-meteo.com) │
              └──────────────────────┬───────────────────────┘
                                     │
                        HTTP GET (JSON Payload)
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │ Weather Integration Module  │
                      │ (backend/app/integrations)  │
                      └──────────────┬──────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
     OBSERVED (24h)           FORECAST (+24h)          FORECAST (+72h)
(Past 24h precipitation)  (Sum hours 1-24 mm)     (Sum hours 1-72 mm)
            │                        │                        │
            ▼                        ▼                        ▼
     CURRENT STRESS            24H STRESS               72H STRESS
($S = 1 - e^{-\alpha R}$)  ($S = 1 - e^{-\alpha R}$)  ($S = 1 - e^{-\alpha R}$)
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                                     ▼
                           DYNAMIC RISK ENGINE
```

## 3. Data Classification & Labeling

The weather integration module enforces strict data labels:

1. **`OBSERVED`**: Real-time past precipitation accumulated over the preceding 24 hours.
2. **`FORECAST`**: Predicted future precipitation model output over +24h and +72h horizons.
3. **`SIMULATION`**: User-defined custom scenario inputs (e.g. "What if rainfall reaches 180mm?").

## 4. Caching & Failure Safety Policy

- **In-Memory Cache TTL**: 15 minutes (to avoid exceeding rate limits while guaranteeing fresh weather data).
- **Graceful Failure Behavior**:
  - If the API call fails or times out (5 seconds threshold):
    1. Returns cached weather observation/forecast if within 1 hour staleness.
    2. Marks data status flag as `STALE_CACHED` or `UNAVAILABLE`.
    3. Displays warning badge `LIVE DATA UNAVAILABLE` in the UI.
    4. **Strict Rule:** Never generates synthetic fake rainfall values.
