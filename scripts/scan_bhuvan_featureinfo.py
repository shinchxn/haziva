import json
import time
from pathlib import Path

import requests
import geopandas as gpd
from shapely.geometry import Point


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

WMS_URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"

LAYER = "disaster:kl_landslides_new"

BOUNDARY_FILE = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

OUTPUT_FILE = Path(
    "data/raw/landslide/inventory/wayanad_bhuvan_featureinfo_scan.json"
)

GRID_SIZE = 20
QUERY_DELAY = 0.25


# --------------------------------------------------
# LOAD WAYANAD BOUNDARY
# --------------------------------------------------

print("=" * 70)
print("WAYANAD-ONLY BHUVAN LANDSLIDE SCAN")
print("=" * 70)

wayanad = gpd.read_file(BOUNDARY_FILE)

if wayanad.crs is None:
    raise ValueError("Wayanad boundary has no CRS.")

wayanad = wayanad.to_crs("EPSG:4326")

boundary = wayanad.geometry.union_all()

minx, miny, maxx, maxy = boundary.bounds

print()
print("Wayanad boundary:")
print(f"Longitude: {minx:.6f} → {maxx:.6f}")
print(f"Latitude:  {miny:.6f} → {maxy:.6f}")

# --------------------------------------------------
# GENERATE GRID
# --------------------------------------------------

points = []

for row in range(GRID_SIZE + 1):

    lat = miny + (maxy - miny) * row / GRID_SIZE

    for col in range(GRID_SIZE + 1):

        lon = minx + (maxx - minx) * col / GRID_SIZE

        point = Point(lon, lat)

        if boundary.contains(point):
            points.append((lat, lon))


print()
print(f"Grid points inside Wayanad: {len(points)}")


# --------------------------------------------------
# WMS GETFEATUREINFO
# --------------------------------------------------

headers = {
    "User-Agent": "Haziva-SIH2026/1.0",
    "Accept": "application/json",
}

results = []

session = requests.Session()
session.headers.update(headers)

for index, (lat, lon) in enumerate(points, start=1):

    # Tiny bbox around query point
    delta = 0.002

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": LAYER,
        "QUERY_LAYERS": LAYER,
        "INFO_FORMAT": "application/json",
        "FEATURE_COUNT": 10,
        "CRS": "EPSG:4326",

        # WMS 1.3.0 + EPSG:4326 uses latitude,longitude
        "BBOX": f"{lat-delta},{lon-delta},{lat+delta},{lon+delta}",

        "WIDTH": 101,
        "HEIGHT": 101,
        "I": 50,
        "J": 50,
    }

    try:

        response = session.get(
            WMS_URL,
            params=params,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        features = data.get("features", [])

        results.append(
            {
                "latitude": lat,
                "longitude": lon,
                "number_returned": len(features),
                "features": features,
            }
        )

        print(
            f"[{index:4}/{len(points)}] "
            f"{lat:.5f}, {lon:.5f} "
            f"→ {len(features)} feature(s)"
        )

    except Exception as e:

        print(
            f"[{index:4}/{len(points)}] "
            f"ERROR: {e}"
        )

        results.append(
            {
                "latitude": lat,
                "longitude": lon,
                "number_returned": 0,
                "features": [],
                "error": str(e),
            }
        )

    time.sleep(QUERY_DELAY)


# --------------------------------------------------
# SAVE
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2
    )


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

total_features = 0
query_hits = 0

for result in results:

    count = result.get(
        "number_returned",
        0
    )

    if count > 0:
        query_hits += 1
        total_features += count


print()
print("=" * 70)
print("SCAN COMPLETE")
print("=" * 70)

print(f"Queries:              {len(points)}")
print(f"Queries with features:{query_hits}")
print(f"Returned features:    {total_features}")

print()
print("Output:")
print(OUTPUT_FILE)

print()
print(
    "NOTE: FeatureInfo results are query-based and may contain "
    "duplicates. We will deduplicate polygon IDs before creating "
    "the final inventory."
)