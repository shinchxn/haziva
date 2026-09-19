# HAZIVA — COMPLETE RELOCATION ENGINE FORENSIC AUDIT
**SIH 26191 | Wayanad | Team Lead Audit**

---

## 1. EXECUTIVE SUMMARY

### Is Relocation Actually Implemented?
**PARTIALLY IMPLEMENTED.**
The relocation engine contains a complete offline GIS extraction and feature-building pipeline (`scripts/build_relocation_candidate_*.py`) that processes 794 real OpenStreetMap (OSM) public facilities in Wayanad, evaluates local hazard raster layers, calculates distance metrics to village reference points, and computes a transparent priority score. A PostGIS/SQLite database table (`relocation_sites`) is seeded from these GIS outputs, and a FastAPI endpoint (`GET /habitations/{habitation_id}/relocation`) serves these candidate sites to a interactive MapLibre frontend UI (`/relocation`).

However, several critical components remain **heuristic or incomplete**:
1. **Buildable Land Area & Capacity:** Physical land area and spatial GIS buildable boundaries are **not calculated from spatial geometry**. Instead, capacity is assigned via category-based lookup heuristics in `backend/app/database/seed.py` (e.g. Education = 650, Community = 900, Hospital = 300).
2. **Water & Resource Capacity:** Water availability, yield, per-capita water demand, electricity, and sanitation capacity are **completely uncalculated** (`water_status: UNKNOWN`).
3. **Existing Destination Population:** Destination village population is stored (Census 2011), but is **not subtracted** from candidate site capacity.
4. **Safety Gate Thresholds:** Due to missing high-resolution GSI raster coverage at specific OSM facility points, 100% of candidate sites are currently flagged with `safety_result: INSUFFICIENT_EVIDENCE` and fall into the `CONDITIONAL` ranking group.
5. **Fallback Endpoint Querying:** If a habitation has no directly matched relocation candidates in the database, `relocation_service.py` falls back to querying the first 5 records in the `relocation_sites` table or returning a hardcoded fallback site list.

### Can We Demonstrate It Honestly?
**YES, WITH TRANSPARENT QUALIFIERS.**
The candidate site locations, names, OSM categories, distance metrics, and baseline dynamic risk integrations are **100% real and GIS-derived**. The UI honestly renders candidates with `INSUFFICIENT_EVIDENCE` safety badges and conditional explanations. However, claiming that HAZIVA performs "AI-driven land buildability analysis" or "dynamic water resource allocation" is technically misleading and will fail judge scrutinization.

### Overall Relocation Engine Completion Status
- **Candidate Site Discovery & Extraction:** `COMPLETE` (794 real OSM public facilities)
- **Spatial Safety Screening:** `PARTIAL` (Raster sampling implemented, threshold rules unconfigured / GSI coverage gaps)
- **Accessibility & Road Proximity:** `PARTIAL` (Straight-line distance to village centroid + nearest OSM road distance implemented; network travel-time routing missing)
- **Facility Capacity:** `PARTIAL` (Category-based lookup heuristics seeded, spatial land-area calculation missing)
- **Water / Infrastructure Capacity:** `MISSING` (Hardcoded/Unknown)
- **Existing Destination Population Subtraction:** `MISSING`
- **Transparent Ranking & Explanation:** `COMPLETE` (Re-normalized weighted evidence scoring & human-readable explanations)
- **Database & API Integration:** `COMPLETE` (PostgreSQL/PostGIS `relocation_sites` table & FastAPI served)
- **Frontend Map & List UI:** `COMPLETE` (MapLibre rendering + site filters)

---

## 2. ACTUAL IMPLEMENTED PIPELINE & ARCHITECTURE

The actual codebase pipeline differs from the conceptual ideal as follows:

```
[RAW OSM INFRASTRUCTURE JSON]
       ↓ (scripts/build_relocation_candidate_facilities.py)
[794 PUBLIC CANDIDATE FACILITIES]
       ↓ (scripts/build_relocation_candidate_safety.py)
[HAZARD RASTER SAMPLING] (Slope, GSI 30m, Historical Scar, Dynamic Risk)
       ↓ (Safety Status: INSUFFICIENT_EVIDENCE / FLAG / PASS)
[ACCESSIBILITY ANALYSIS] (scripts/build_relocation_candidate_accessibility.py)
       ↓ (Straight-line village centroid km & nearest OSM road m)
[RANKING & PRIORITY ENGINE] (scripts/build_relocation_candidate_ranking.py)
       ↓ (transparent_priority_score = 0.35*V + 0.30*H + 0.20*D + 0.15*F)
[PROCESSED CSV / GPKG DATASETS] (data/processed/exposure/relocation/*)
       ↓ (backend/app/database/seed.py)
[DATABASE SEEDING] (PostGIS / SQLite table `relocation_sites`)
       ↓ (backend/app/services/relocation_service.py)
[FASTAPI REST API] (GET /habitations/{habitation_id}/relocation)
       ↓ (frontend/app/relocation/page.tsx)
[FRONTEND DASHBOARD & MAPLIBRE UI]
```

### Architectural Gaps vs Ideal Pipeline
- **Buildable Land Spatial Polygon Intersection:** `MISSING` (No buffer/slope/restricted area polygon clipping).
- **Water Hydrology Yield / Demand Balance:** `MISSING` (Hardcoded `water: True`).
- **Road Network Graph Routing:** `NOT_IMPLEMENTED` (Straight-line geodesic distance used instead of network routing).
- **Destination Existing Population Subtraction:** `MISSING` (Raw capacity used without subtracting destination population).

---

## 3. FILE-BY-FILE INVENTORY

| File Path | Component | Purpose / Functionality | Implementation Status |
|-----------|-----------|-------------------------|-----------------------|
| [build_relocation_candidate_facilities.py](file:///d:/projects/haziva/scripts/build_relocation_candidate_facilities.py) | Offline GIS Pipeline | Extracts 794 candidate point/way facilities from raw Overpass OSM JSON (`meppadi_osm_infrastructure.json`). | `IMPLEMENTED` |
| [build_relocation_candidate_safety.py](file:///d:/projects/haziva/scripts/build_relocation_candidate_safety.py) | Offline GIS Pipeline | Samples Slope TIFF, GSI 30m TIFF, Historical Landslide TIFF, and Dynamic Risk TIFF at facility coordinates. | `PARTIAL` (Sampling real, rules unconfigured) |
| [build_relocation_candidate_accessibility.py](file:///d:/projects/haziva/scripts/build_relocation_candidate_accessibility.py) | Offline GIS Pipeline | Calculates geodesic straight-line distance to village representative point and distance to nearest OSM road. | `PARTIAL` (Euclidean distance real, graph routing missing) |
| [build_relocation_candidate_ranking.py](file:///d:/projects/haziva/scripts/build_relocation_candidate_ranking.py) | Offline GIS Pipeline | Computes `transparent_priority_score` (prototype_v2) and human-readable ranking explanations. | `IMPLEMENTED` |
| [relocation_site.py](file:///d:/projects/haziva/backend/app/models/relocation_site.py) | Backend Database Model | SQLAlchemy ORM model mapping to `relocation_sites` table in PostGIS/SQLite. | `IMPLEMENTED` |
| [seed.py](file:///d:/projects/haziva/backend/app/database/seed.py#L197-L249) | Backend Database Seeder | Seeds 794 candidate sites from CSV into `relocation_sites` table. Assigns heuristic capacity via `estimate_capacity()`. | `PARTIAL` (Heuristic capacity, fallback linking) |
| [relocation_service.py](file:///d:/projects/haziva/backend/app/services/relocation_service.py) | Backend Service | Queries `relocation_sites` by `habitation_id`. Includes fallback limit(5) query and hardcoded fallback dicts. | `PARTIAL` (Fallback hardcoded dicts present) |
| [relocation.py](file:///d:/projects/haziva/backend/app/api/relocation.py) | Backend API | Exposes `GET /habitations/{habitation_id}/relocation` endpoint returning `RelocationProfile`. | `IMPLEMENTED` |
| [page.tsx](file:///d:/projects/haziva/frontend/app/relocation/page.tsx) | Frontend Dashboard | Interactive UI page displaying candidate list, rejected list, site count cards, and MapLibre map. | `IMPLEMENTED` |
| [RelocationMap.tsx](file:///d:/projects/haziva/frontend/components/habitations/RelocationMap.tsx) | Frontend Map Component | MapLibre rendering component for candidate (green) and rejected (red) markers. | `IMPLEMENTED` |

---

## 4. DATABASE INVENTORY

### Table: `relocation_sites`
- **ORM Model:** `RelocationSite` ([relocation_site.py:L14-31](file:///d:/projects/haziva/backend/app/models/relocation_site.py#L14-L31))
- **Primary Key:** `site_id` (String(64)) — e.g. `OSM_way_839468866`
- **Foreign Key:** `habitation_id` -> `habitations.id`
- **Columns:**
  - `site_id`: String(64), Primary Key
  - `habitation_id`: String(64), Foreign Key
  - `name`: String(255) — e.g. "HIM Upper Primary School, Kalpetta"
  - `facility_category`: String(64) — e.g. "education", "community", "healthcare", "public_building"
  - `latitude`: Float (EPSG:4326)
  - `longitude`: Float (EPSG:4326)
  - `location`: Geometry(POINT, srid=4326)
  - `status`: String(32) — "candidate" or "rejected"
  - `safety_result`: String(64) — "INSUFFICIENT_EVIDENCE", "FLAG", "PASS"
  - `capacity`: Integer — e.g. 650, 900, 300, 450
  - `infrastructure_info`: JSON — `{"water": true, "shelter": true, "roads": true, "osm_type": "way"}`
  - `accessibility`: String(64) — e.g. "UNMATCHED_VILLAGE", "GOOD_EVIDENCE", "NEAREST_OSM_ROAD_AVAILABLE"
  - `rejection_reason`: Text
  - `transparent_priority_score`: Float — e.g. 0.6845
  - `ranking_explanation`: Text — Detailed human-readable justification

---

## 5. API ENDPOINT INVENTORY

| Method | Endpoint Path | Handler Function | Line | Source / Query | Response Model | Consumer |
|--------|---------------|------------------|------|----------------|----------------|----------|
| `GET` | `/habitations/{habitation_id}/relocation` | `get_habitation_relocation()` | [relocation.py:L12](file:///d:/projects/haziva/backend/app/api/relocation.py#L12) | DB query `RelocationSite` filtered by `habitation_id` (with limit 5 fallback) | `RelocationProfile` | `frontend/app/relocation/page.tsx` |

---

## 6. GIS DATA INVENTORY

| Dataset Name | File Path | Format / CRS | Usage in Relocation Engine |
|--------------|-----------|--------------|----------------------------|
| Raw OSM Infrastructure | `data/raw/infrastructure/osm/meppadi_osm_infrastructure.json` | GeoJSON/JSON | Source of 794 candidate public facility geometries & tags. |
| Village Population 2011 | `data/processed/exposure/census_nwdp_reconciliation/wayanad_census_nwdp_village_population_2011.gpkg` | GPKG (EPSG:7755 / 4326) | Village polygon boundaries & population matching. |
| Copernicus Slope | `data/processed/terrain/wayanad_copernicus_slope_degrees.tif` | GeoTIFF (EPSG:32643) | Sampled slope at candidate coordinates. |
| GSI Susceptibility | `data/processed/landslide/susceptibility/wayanad_gsi_susceptibility_copernicus_30m.tif` | GeoTIFF (EPSG:32643) | Sampled landslide susceptibility class (0-3). |
| Historical Landslide Presence | `data/processed/landslide/inventory/wayanad_historical_landslide_presence_copernicus_30m.tif` | GeoTIFF (EPSG:32643) | Sampled historical scar presence (0 or 1). |
| Model A 24h Dynamic Risk | `data/processed/predictions/wayanad_dynamic_risk_model_a_24h.tif` | GeoTIFF (EPSG:32643) | Sampled 24h ECMWF forecast risk at site. |
| Processed Candidate Ranking | `data/processed/exposure/relocation/wayanad_relocation_candidate_ranking.csv` | CSV / GPKG | Master processed relocation candidate dataset seeded to database. |

---

## 7. REAL VS MOCK DATA AUDIT TABLE

| Feature / Metric | Current Value | Real Source | Derived? | Mock? | Hardcoded? | Lineage & Audit Notes |
|------------------|---------------|-------------|----------|-------|------------|-----------------------|
| Origin Population | e.g. 14,845 | Census 2011 / NWDP Reconciliation GPKG | Yes | No | No | Real Census 2011 village population joined from `wayanad_census_nwdp_village_population_2011.gpkg`. |
| Candidate Geometry | Lat/Lon Point | OpenStreetMap (Overpass API) | Yes | No | No | Real geographic points/way centroids extracted in `build_relocation_candidate_facilities.py`. |
| Candidate Safety | `INSUFFICIENT_EVIDENCE` | Raster sampling (Slope, GSI, History) | Yes | No | No | Real spatial sampling performed in `build_relocation_candidate_safety.py`. Unconfigured thresholds default status to `INSUFFICIENT_EVIDENCE`. |
| Candidate Capacity | e.g. 650, 900, 300 | Category lookup heuristic | Yes | No | Yes (Rules) | Category lookup in `seed.py:estimate_capacity()` (Schools=650, Halls=900, Hospitals=300). NOT calculated from GIS land area. |
| Water Supply | `water: True` | None | No | No | Yes | Hardcoded dictionary flag in `seed.py:L236`. Hydrological yield and demand are NOT calculated. |
| Road Access Distance | e.g. 15.2 m | OSM Road Segment Centroids | Yes | No | No | Real Euclidean distance to nearest OSM highway calculated in `build_relocation_candidate_accessibility.py`. |
| Network Travel Time | `NOT_IMPLEMENTED` | None | No | No | No | Explicitly marked `NOT_IMPLEMENTED` in accessibility pipeline to avoid fake routing calculations. |
| Destination Existing Pop | Unused in subtraction | Census 2011 GPKG | Yes | No | No | Census population is stored in candidate table but NOT subtracted from facility capacity. |
| Transparent Score | e.g. 0.6845 | Multi-criteria weighted sum | Yes | No | No | Dynamically calculated via formula `0.35*VP + 0.30*HS + 0.20*DE + 0.15*FS` in `build_relocation_candidate_ranking.py`. |

---

## 8. DATA LINEAGE TRACE FOR A SINGLE CANDIDATE SITE

Candidate Site: **HIM Upper Primary School, Kalpetta (`OSM_way_839468866`)**

```
1. RAW OSM DATA:
   File: data/raw/infrastructure/osm/meppadi_osm_infrastructure.json
   Element: Way 839468866 | tags: {"amenity": "school", "name": "HIM Upper Primary School, Kalpetta"}
   Coordinates: lat=11.6118, lon=76.0824 (Way center)

2. FACILITY EXTRACTION:
   Script: scripts/build_relocation_candidate_facilities.py:L149
   Output Record: candidate_id="OSM_way_839468866", facility_category="education", facility_role="relocation_candidate"

3. SAFETY SCREENING:
   Script: scripts/build_relocation_candidate_safety.py:L192
   Sampled Values: slope=4.2°, gsi_susceptibility=0 (No coverage), historical_landslide=0, dynamic_risk_combined=0.182
   Rule Evaluation: GSI coverage missing -> safety_status="INSUFFICIENT_EVIDENCE"
   Reason Code: "NO_GSI_COVERAGE; NO_HISTORICAL_INVENTORY_COVERAGE"

4. ACCESSIBILITY ANALYSIS:
   Script: scripts/build_relocation_candidate_accessibility.py:L168
   Nearest OSM Road: distance_to_nearest_road_m = 15.2 m, nearest_road_class = "residential"
   Village Centroid Distance: distance_to_village_km = 1.42 km (Geodesic straight line)

5. TRANSPARENT RANKING & EXPLANATION:
   Script: scripts/build_relocation_candidate_ranking.py:L263
   Weights: Village Priority (35%), Hazard Suitability (30%), Cohort Distance (20%), Facility Category (15%)
   Calculated Score: transparent_priority_score = 0.6845
   Explanation: "Prototype-priority candidate under incomplete safety evidence: Candidate 'HIM Upper Primary School, Kalpetta'..."

6. DATABASE SEEDING:
   Script: backend/app/database/seed.py:L222
   Heuristic Capacity: estimate_capacity("education") -> capacity = 650
   ORM Object: RelocationSite(site_id="OSM_way_839468866", habitation_id="hab_627296", capacity=650, safety_result="INSUFFICIENT_EVIDENCE")

7. API ENDPOINT CONSUMPTION:
   Script: backend/app/services/relocation_service.py:L30 & backend/app/api/relocation.py:L12
   HTTP Response: GET /habitations/hab_627296/relocation -> JSON site array containing OSM_way_839468866

8. FRONTEND DISPLAY:
   Script: frontend/app/relocation/page.tsx:L300 & frontend/components/habitations/RelocationMap.tsx:L204
   UI Component: Renders green MapLibre marker, Candidate card, capacity=650, safety="INSUFFICIENT_EVIDENCE".
```

---

## 9. ACTUAL IMPLEMENTED FORMULAS

### 1. Transparent Priority Score (`prototype_v2`)
Implemented in `scripts/build_relocation_candidate_ranking.py:L263`:
$$\text{Score} = \frac{w_{\text{vp}} \cdot S_{\text{vp}} + w_{\text{hs}} \cdot S_{\text{hs}} + w_{\text{dist}} \cdot S_{\text{dist}} + w_{\text{fs}} \cdot S_{\text{fs}}}{w_{\text{vp}} + w_{\text{hs}} + w_{\text{dist}} + w_{\text{fs}}}$$
Where:
- $w_{\text{vp}} = 0.35$ (Village forecast priority score, re-weighted if unavailable)
- $w_{\text{hs}} = 0.30$ (Hazard suitability = $1 - \text{dynamic\_risk\_combined}$)
- $w_{\text{dist}} = 0.20$ (Cohort-relative straight-line distance index = $1 - \frac{d - d_{\min}}{d_{\max} - d_{\min}}$)
- $w_{\text{fs}} = 0.15$ (Facility category weight: Primary = 1.0, Potential = 0.6, Medical = 0.3, Other = 0.0)

### 2. Heuristic Facility Capacity
Implemented in `backend/app/database/seed.py:L47`:
$$\text{Capacity} = \begin{cases} 
650 & \text{if } \text{category} \in \{\text{education, school}\} \\
900 & \text{if } \text{category} \in \{\text{community, hall}\} \\
1500 & \text{if } \text{category} \in \{\text{stadium, sports}\} \\
300 & \text{if } \text{category} \in \{\text{hospital, medical}\} \\
450 & \text{otherwise}
\end{cases}$$

---

## 10. DESTINATION SAFETY GATE AUDIT

- **Is Safety Gate a Hard Constraint?**
  **NO, CURRENTLY A SOFT FILTER.**
  In `scripts/build_relocation_candidate_ranking.py:L58`, candidates are partitioned into three ranking groups based on `safety_status`:
  1. `ELIGIBLE` (`safety_status == "PASS"`)
  2. `CONDITIONAL` (`safety_status == "INSUFFICIENT_EVIDENCE"`)
  3. `DO_NOT_PRIORITIZE` (`safety_status == "FLAG"`)
  Candidates with `FLAG` are moved to the `DO_NOT_PRIORITIZE` group rather than being completely hard-purged from output datasets.

- **Current Operational Behavior:**
  Because GSI 30m susceptibility raster coverage has no data at certain discrete facility coordinates, 100% of candidate sites currently evaluate to `INSUFFICIENT_EVIDENCE` and fall into the `CONDITIONAL` group. No candidate site currently passes all hard safety gates.

---

## 11. CAPACITY AUDIT: LAND, WATER, INFRASTRUCTURE, ACCESSIBILITY

| Constraint Dimension | Real? | Formula / Rule | Data Source | Used in Final Capacity? |
|----------------------|-------|----------------|-------------|-------------------------|
| **Buildable Land Area** | `NO` | Fixed lookup by facility category | `seed.py:estimate_capacity()` | `YES` (Heuristic number used directly as capacity) |
| **Water Supply Yield** | `NO` | Hardcoded `water: True` | `seed.py:L236` | `NO` (Not calculated or checked against per-capita demand) |
| **Infrastructure Facilities** | `YES` | Category classification from OSM tags | `build_relocation_candidate_facilities.py` | `PARTIAL` (Used to weight candidate priority score) |
| **Accessibility / Distance** | `YES` | Straight-line distance to centroid + road proximity | `build_relocation_candidate_accessibility.py` | `PARTIAL` (Used in priority score; travel time is `NOT_IMPLEMENTED`) |
| **Destination Existing Population** | `NO` | Unused in capacity calculation | Census 2011 GPKG | `NO` (Existing village population is NOT subtracted from site capacity) |

---

## 12. FRONTEND UI AUDIT

- **Page:** `frontend/app/relocation/page.tsx`
- **Component:** `frontend/components/habitations/RelocationMap.tsx`
- **Displayed Values & Provenance:**
  - **Habitation Name:** REAL (Fetched from API `GET /habitations`)
  - **Candidate Count:** REAL API DATA (`relocation.sites.filter(s => s.status === 'candidate').length`)
  - **Rejected Count:** REAL API DATA (`relocation.sites.filter(s => s.status === 'rejected').length`)
  - **Site Marker Coordinates:** REAL (Point geometry from PostGIS/API)
  - **Site Safety Status:** REAL API DATA (Displays `INSUFFICIENT_EVIDENCE`, `PASS`, or `REVIEW`)
  - **Site Capacity:** REAL API DATA (Category heuristic from database, e.g. 650)
  - **Site Rejection Reason:** REAL API DATA (Populated if `rejection_reason` is non-null)

---

## 13. DISCONNECTED & FALLBACK COMPONENTS

1. **Service Layer Hardcoded Fallbacks:**
   In `backend/app/services/relocation_service.py:L50-L86`, if the database query fails or returns empty, the service returns a hardcoded list containing `"Kalpetta Government Higher Secondary School"` (Capacity 850, Safety PASS) and `"Community Hall, Meppadi"` (Capacity 420, Safety REVIEW).
2. **Generic Database Query Fallback:**
   In `backend/app/services/relocation_service.py:L25`, if no candidate sites match a given `habitation_id`, `db.query(RelocationSite).limit(5).all()` is executed, returning arbitrary candidate sites from other villages.

---

## 14. MISSING COMPONENTS FOR FULL PRODUCTION PIPELINE

1. **Spatial Buildable Land Area Polygon Clipping:** Buffer analysis around hazards, slope bounds (>15°), and statutory red zones to derive physical $m^2$ buildable footprint.
2. **Hydrological Water Balance Calculation:** $C_{\text{water}} = \frac{\text{Water Supply (L/day)}}{135 \text{ L/person/day}} - \text{Existing Village Pop}$.
3. **Road Graph Network Routing:** OSRM or NetworkX distance and travel time calculation.
4. **Subtractive Capacity Model:** $C_{\text{effective}} = \min(C_{\text{land}}, C_{\text{water}}, C_{\text{infra}}) - P_{\text{existing\_destination}}$.

---

## 15. FABRICATED / HARDCODED / MOCK COMPONENTS LIST

| Component | Location | Description |
|-----------|----------|-------------|
| `estimate_capacity()` | [seed.py:L47-L58](file:///d:/projects/haziva/backend/app/database/seed.py#L47-L58) | Hardcoded capacity lookup table (650, 900, 1500, 300, 450). |
| `infrastructure_info` dict | [seed.py:L235-L240](file:///d:/projects/haziva/backend/app/database/seed.py#L235-L240) | Hardcoded `{"water": True, "shelter": True, "roads": True}`. |
| Fallback Site Dicts | [relocation_service.py:L50-L86](file:///d:/projects/haziva/backend/app/services/relocation_service.py#L50-L86) | Hardcoded mock JSON dictionary returned if database query fails. |
| Fallback Seeding Link | [seed.py:L206](file:///d:/projects/haziva/backend/app/database/seed.py#L206) | Links unmatched facilities to primary village `hab_627296` (Mananthavady). |

---

## 16. DEMONSTRATION RISKS FOR HACKATHON JUDGES

1. **Judge Question:** *"How did you calculate this facility capacity of 650 people?"*
   - **Risk:** High. If claimed to be GIS-derived land buildability, a judge inspecting the code will discover it is a category lookup in `seed.py`.
2. **Judge Question:** *"Why are all candidate sites marked 'INSUFFICIENT_EVIDENCE'?"*
   - **Risk:** Medium. Must explain honestly that discrete point raster sampling encountered nodata values in the GSI susceptibility TIFF layer, triggering safety evidence rules.
3. **Judge Question:** *"Does this account for water availability at the site?"*
   - **Risk:** High. The UI displays water infrastructure, but no hydrological yield modeling exists.

---

## 17. PRIORITY FIXES FOR DEMONSTRATION

### P0 — Must Fix Before SIH Demonstration
1. **Remove Hardcoded Fallback Mock Dictionary:** Remove lines 50-86 in `relocation_service.py` to prevent static mock site leakage.
2. **Clarify Capacity Semantics in UI:** Rename UI label "Capacity" to "Estimated Facility Capacity (Category Heuristic)" or populate real estimated buildable area comments.
3. **Configure Default Raster Interpolation / Fallbacks:** Update `build_relocation_candidate_safety.py` with nearest-neighbor sampling or nearest valid pixel lookup so GSI raster coverage returns valid classes.

### P1 — Important Enhancements
1. **Subtract Destination Population:** Update capacity formula to subtract `matched_village_population_2011`.
2. **Integrate Real Road Distance into UI:** Expose `distance_to_nearest_road_m` in the frontend candidate site cards.

### P2 — Nice to Have
1. **Spatial Polygon Clipping for Buildable Land:** Run spatial overlay clipping of facility polygons against high slope (>15°) and GSI High hazard zones.

---

## 18. FINAL END-TO-END DEMONSTRATION STATUS SUMMARY

| Stage | Demonstrable with Real Data? | Explanation / Provenance |
|-------|------------------------------|--------------------------|
| **1. Origin Risk** | **YES** | Real Model A spatial susceptibility (p95 = 0.7511) for Mananthavady. |
| **2. Priority Ranking** | **YES** | Dynamically calculated from Census 2011 population & forecast risk trajectory. |
| **3. Relocation Candidate Search** | **YES** | 794 real OpenStreetMap public facilities in Wayanad extracted & mapped to PostGIS. |
| **4. Safety Gate** | **PARTIAL** | Spatial raster sampling implemented; status currently defaults to `INSUFFICIENT_EVIDENCE`. |
| **5. Facility Capacity** | **PARTIAL** | Heuristic category lookup (Schools=650, Halls=900); physical land area missing. |
| **6. Accessible Road Proximity** | **YES** | Geodesic straight-line distance & nearest OSM highway distance calculated. |
| **7. Candidate Ranking Explanation** | **YES** | Fully transparent weighted multi-criteria priority score & human-readable text output. |

---
*Audit completed by HAZIVA Team Lead Agent. No codebase modifications were performed during this audit.*
