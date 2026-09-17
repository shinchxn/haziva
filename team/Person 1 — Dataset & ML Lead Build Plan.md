# PERSON 1 — DATASET & ML LEAD

## Main Goal

Build the complete **hazard, exposure, vulnerability, and rainfall dataset foundation** for the SIH 26191 prototype.

The final output must be a clean, habitation-level dataset that Person 2 can directly use for model training and future-risk prediction.

The core focus is:

**Raw Data → Clean Data → Habitation-Level Features → Model-Ready Dataset**

---

# 1. Tech Stack

Use:

- **Python**
- **Pandas**
- **NumPy**
- **GeoPandas**
- **Shapely**
- **Rasterio** where raster/terrain data requires it
- **GDAL** where required for GIS preprocessing
- **PostGIS-compatible geographic formats**
- CSV / GeoJSON / GeoPackage for intermediate datasets

---

# 2. Build the Wayanad Dataset Foundation

Create the initial dataset for the Wayanad pilot.

Organize the available data into:

```text
WAYANAD DATA
│
├── Habitations
├── Terrain
├── Landslide Susceptibility
├── Historical Hazard Evidence
├── Rainfall
├── Forecast Rainfall
├── Population
├── Households
├── Roads / Accessibility
├── Critical Infrastructure
└── Vulnerability Indicators
```

The dataset must be organized around the **habitation/location** that the prediction system will ultimately analyze.

---

# 3. Habitation Master Dataset

Create the master habitation table.

Each habitation should have a unique identifier.

Example:

```text
habitation_id
habitation_name
latitude
longitude
geometry
```

This ID must remain consistent across the entire project.

It becomes the connection between:

**Dataset → ML → Backend → Dashboard → Map → Relocation**

---

# 4. Terrain Features

Prepare the terrain information required for landslide-risk prediction.

Where available, extract/prepare:

- Elevation
- Slope
- Terrain-related features required by the model

The output must be associated with the relevant habitation/location.

Example:

```text
Habitation A
Elevation: ...
Slope: ...
```

---

# 5. Landslide Hazard Features

Prepare the available landslide-related information.

Include relevant data such as:

- Landslide susceptibility
- Historical landslide evidence
- Hazard inventory information
- Other supported hazard indicators

Convert the geographic information into habitation-level features where required.

---

# 6. Rainfall Dataset

Prepare rainfall information for the prediction system.

Include:

- Recent rainfall
- Rainfall accumulation
- Relevant previous-period rainfall
- Forecast rainfall
- Forecast accumulation

Organize rainfall according to the prediction horizons required by the project:

```text
CURRENT
24 HOURS
72 HOURS
```

The final structure must allow Person 2 to distinguish current conditions from future forecast conditions.

---

# 7. Population & Exposure Dataset

Prepare habitation-level exposure information.

Include available:

- Population
- Households
- Population density
- Critical infrastructure exposure

Connect the information to the habitation master ID.

Example:

```text
Habitation A

Population: ...
Households: ...
Density: ...
Critical assets: ...
```

---

# 8. Accessibility Dataset

Prepare geographic accessibility information.

Use available road/location data to create useful habitation-level features such as:

- Road accessibility
- Distance to important roads
- Distance to essential services
- Other supported accessibility indicators

Do not create assumptions that cannot be supported by the available data.

---

# 9. Vulnerability Dataset

Prepare the vulnerability indicators that can be supported by the available data.

Possible categories:

- Housing/service vulnerability
- Accessibility limitations
- Essential-service distance
- Other defensible vulnerability indicators

Keep vulnerability information separate from hazard information so the model can distinguish:

```text
HAZARD
+
EXPOSURE
+
VULNERABILITY
```

---

# 10. Geographic Data Processing

Process the geographic datasets so that different sources can be combined correctly.

Handle:

- Coordinate systems
- Geographic boundaries
- Spatial joins
- Point/polygon relationships
- Raster-to-location extraction where required
- Geometry validation

The final habitation dataset must use a consistent geographic reference system.

---

# 11. Feature Engineering

Create the model-ready features from the raw datasets.

Build the feature pipeline for:

```text
Terrain
+
Hazard
+
Rainfall
+
Exposure
+
Vulnerability
+
Accessibility
```

Examples of derived features:

- Rainfall accumulation
- Forecast rainfall accumulation
- Rainfall trend/change
- Population density
- Distance-based accessibility features
- Hazard × rainfall relationships where justified

Every engineered feature must have a clear definition.

---

# 12. Data Cleaning

Clean the combined dataset.

Handle:

- Missing values
- Duplicate habitations
- Invalid coordinates
- Invalid geographic geometries
- Inconsistent units
- Duplicate records
- Outliers
- Different naming conventions
- Different coordinate systems

Do not silently remove important data.

Where data is missing, preserve that information appropriately so Person 2 knows which features are incomplete.

---

# 13. Data Quality Checks

Create checks for:

### Geographic quality

```text
Valid coordinates
Valid geometry
Correct Wayanad location
```

### Dataset quality

```text
No duplicate habitation IDs
Required fields present
Correct data types
Valid numerical ranges
```

### Feature quality

```text
Rainfall values valid
Slope values valid
Population values valid
Hazard values valid
```

---

# 14. Model-Ready Dataset

Produce one clean dataset that Person 2 can directly use.

Example structure:

```text
habitation_id
latitude
longitude
elevation
slope
landslide_susceptibility
historical_hazard
recent_rainfall
rainfall_accumulation
forecast_rainfall_24h
forecast_rainfall_72h
population
households
population_density
critical_infrastructure
accessibility
vulnerability_features
```

The exact columns depend on the actual available data.

Do not add fake values just to complete columns.

---

# 15. Feature Documentation

For every final feature, document:

```text
Feature Name
Meaning
Source
Unit
Spatial Resolution
Time Period
Processing Method
Missing-Data Handling
```

Example:

```text
Feature:
rainfall_24h

Meaning:
Forecast rainfall accumulated over the next 24 hours.

Source:
Actual selected weather/forecast dataset.

Unit:
mm

Processing:
Aggregated to habitation location.
```

---

# 16. Dataset Output for Person 2

Person 2 must receive:

```text
Clean Dataset
+
Feature Definitions
+
Data Sources
+
Preprocessing Pipeline
+
Geographic Reference
+
Missing-Data Information
```

Person 2 should be able to begin model training directly from this output.

---

# 17. Dataset Integration With Person 3

The final habitation dataset must use stable IDs and geographic fields that Person 3 can load into PostgreSQL/PostGIS.

Required geographic information:

```text
habitation_id
latitude
longitude
geometry
```

Required intelligence inputs:

```text
hazard features
rainfall features
exposure features
vulnerability features
accessibility features
```

---

# 18. Risk Engine Input

Create the clean feature input that will eventually feed the project's risk engine.

The intended structure is:

```text
Habitation
    ↓
Terrain Features
    ↓
Hazard Features
    ↓
Current Rainfall
    ↓
Forecast Rainfall
    ↓
Exposure
    ↓
Vulnerability
    ↓
Accessibility
    ↓
MODEL-READY FEATURE VECTOR
```

This becomes the foundation for Person 2's prediction system.

---

# 19. Future Prediction Support

The dataset structure must support the project's forward-looking prediction.

Person 2 must be able to generate:

```text
CURRENT RISK
      +
24H RISK
      +
72H RISK
```

Therefore, current and forecast-dependent features must remain distinguishable.

---

# 20. Final Build Result

Person 1 must deliver a clean, geographically consistent, habitation-level **Wayanad risk dataset foundation** containing the project's available:

**Terrain + Landslide Hazard + Rainfall + Forecast + Population + Exposure + Vulnerability + Accessibility**

information.

The final pipeline should work as:

```text
RAW DATA
   ↓
CLEANING
   ↓
GIS PROCESSING
   ↓
SPATIAL JOIN
   ↓
FEATURE ENGINEERING
   ↓
DATA QUALITY CHECK
   ↓
HABITATION-LEVEL DATASET
   ↓
PERSON 2 — MODEL TRAINING
```

### Final output:

**A reliable model-ready dataset that Person 2 can immediately use to build the future-risk prediction system.**