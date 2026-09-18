# Wayanad AI Risk & Relocation System — Data Dictionary

## 1. Purpose

This document defines the canonical datasets used by the system,
their source, spatial/temporal characteristics, role in ML,
and known limitations.

---

## 2. Data Layers

| Layer | Purpose |
|---|---|
| raw | Original external/source data. Never modify. |
| processed | Cleaned, aligned, normalized datasets |
| labels | ML target/ground-truth datasets |
| features | Canonical model-ready feature datasets |
| relocation | Candidate relocation sites and capacity data |

---

## 3. Static Hazard / Terrain

### DEM

- Path: `data/raw/dem/wayanad_srtm_gl1_30m.tif`
- Type: Raster
- Role: Base terrain
- Resolution: ~30 m
- Status: READY
- Used to derive: slope

### Slope

- Path: `data/processed/terrain/wayanad_slope_degrees.tif`
- Type: Raster
- CRS: EPSG:32643
- Resolution: ~30 m
- Role: Static hazard feature
- Status: READY
- NoData: -9999
- Important: slope is a continuous predictor, not a direct risk threshold.

### GSI Landslide Susceptibility

- Path: `data/processed/landslide/susceptibility/wayanad_gsi_susceptibility_aligned.tif`
- Type: Raster
- CRS: EPSG:32643
- Role: Static hazard feature
- Classes:
  - 0 = No GSI coverage
  - 1 = Low
  - 2 = Moderate
  - 3 = High
- Status: READY
- Important: 0 must NOT be interpreted as Low susceptibility.

---

## 4. Historical Landslide Labels

### Bhuvan WMS-derived candidate inventory

- Path: `data/processed/landslide/inventory/wayanad_bhuvan_landslides_wms_derived.geojson`
- Type: Vector
- Role: Historical event/presence source
- Status: PROVISIONAL
- Features: 386 candidate polygons
- Source: rendered Bhuvan WMS layer

Important limitation:
These are polygons detected from a rendered WMS image.
They must NOT be treated as an authoritative 386-event inventory.
Original feature attributes/dates are not preserved.

### 30 m Historical Landslide Presence

- Path: `data/processed/landslide/inventory/wayanad_historical_landslide_presence_30m.tif`
- Type: Raster
- Role: ML label
- Encoding:
  - 0 = no mapped historical landslide
  - 1 = mapped historical landslide
- Status: PROVISIONAL

Important:
0 means "no mapped landslide in this label source", not necessarily
"confirmed true negative".

Therefore this dataset should currently be treated as
historical landslide presence/background rather than perfect ground truth.

---

## 5. Land Cover

### ESA WorldCover

- Raw:
  `data/raw/landuse/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif`
- Processed:
  `data/processed/exposure/wayanad_worldcover_10m.tif`
- Feature rasters:
  `data/processed/exposure/worldcover/`
- Reference year: 2021
- Resolution: 10 m source, aggregated to ~30 m model grid
- Role: Exposure/context feature
- Status: READY

Derived fractions:

- tree_cover_fraction
- grassland_fraction
- cropland_fraction
- builtup_fraction
- bare_fraction
- water_fraction
- wetland_fraction

---

## 6. Population / Habitation

### Census population

- Path:
  `data/raw/population/census_2011_kerala_village_population/`
- Reference year: 2011
- Role: Historical population baseline
- Status: NEEDS CLEANUP / VERIFICATION

Important:
2011 population must not be presented as current 2026 population.

The current CSV appears malformed and must not yet become an ML source.

### LGD habitation/local-government data

- Path:
  `data/raw/habitation/lgd/LGD - Local Government Directory, Government of India.xlsx`
- Role: Administrative/habitation reference
- Status: NEEDS INSPECTION

---

## 7. Rainfall

### Historical rainfall

- Path:
  `data/raw/rainfall/observed/wayanad/wayanad_daily_rainfall_2015_2025.json`
- Role: Historical dynamic driver
- Status: READY WITH SPATIAL LIMITATION

### Accumulated rainfall

- Path:
  `data/raw/rainfall/accumulated/wayanad/wayanad_rainfall_accumulated_2015_2025.csv`
- Features:
  - rainfall_mm
  - rainfall_24h_mm
  - rainfall_72h_mm
  - rainfall_7day_mm
- Role: Dynamic rainfall features
- Status: READY

### Forecast rainfall

- Path:
  `data/raw/rainfall/forecast/wayanad/wayanad_rainfall_forecast_7day.json`
- Role: Future dynamic driver
- Horizons:
  - 24h
  - 72h
  - 7day
- Status: READY FOR PROTOTYPE

Important:
Current rainfall data is representative of a Wayanad coordinate,
not a complete spatial rainfall grid.

---

## 8. Infrastructure / Exposure

### OSM buildings

- Path: `data/processed/exposure/osm_buildings.csv`
- Role: Building exposure proxy
- Status: READY WITH LIMITATION

Important:
Building count is not equivalent to household or population count.

### OSM facilities

- Path: `data/processed/exposure/osm_facilities.csv`
- Role: Critical infrastructure exposure
- Status: READY WITH LIMITATION

Preserve original OSM classifications.
Do not automatically classify healthcare centres as PHCs.

### OSM raw infrastructure

- Path:
  `data/raw/infrastructure/osm/meppadi_osm_infrastructure.json`
- Coverage: Meppadi/Wayanad bounding box
- Status: PROVISIONAL

Important:
The current bounding box is not an exact administrative/panchayat boundary.

---

## 9. Missing / Required Datasets

### Required before final relocation system

- Exact habitation boundaries
- Reliable habitation/population mapping
- Relocation candidate sites
- Available land/capacity
- Water availability
- Road/accessibility network
- Safety constraints
- Critical infrastructure accessibility
- Event-dated historical landslide inventory

---

## 10. ML Problems

### Model A — Spatial Susceptibility

Static features:

DEM-derived terrain + GSI susceptibility + land cover

Target:

Historical mapped landslide presence

Purpose:

Estimate spatial susceptibility/background hazard.

---

### Model B — Future Dynamic Risk

Inputs:

- Spatial susceptibility
- Recent rainfall
- 24h rainfall
- 72h rainfall
- 7-day rainfall
- Forecast rainfall
- Other future dynamic drivers

Outputs:

- NOW
- 24H
- 72H

Purpose:

Estimate changing risk conditions.

This model is NOT ready for training until event-dated historical
landslide/rainfall relationships are established.

---

## 11. Canonical Dataset Rule

Every dataset must have one clearly defined role:

SOURCE → PROCESSED → CANONICAL FEATURE / LABEL → MODEL

Duplicate representations must be documented rather than silently
used as separate independent datasets.