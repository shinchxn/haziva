import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import shape


SCAN_FILE = Path(
    "data/raw/landslide/inventory/bhuvan_featureinfo_scan.json"
)

WAYANAD_BOUNDARY = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)


# --------------------------------------------------
# Load scan results
# --------------------------------------------------

with open(SCAN_FILE, "r", encoding="utf-8") as f:
    scan = json.load(f)

hits = []

for result in scan:
    for feature in result.get("features", []):
        hits.append(feature)


print("=" * 70)
print("BHUVAN LANDSLIDE OVERLAP CHECK")
print("=" * 70)

print(f"Total returned features: {len(hits)}")


if not hits:
    print("No features found.")
    raise SystemExit


# --------------------------------------------------
# Load Wayanad boundary
# --------------------------------------------------

wayanad = gpd.read_file(WAYANAD_BOUNDARY)

if wayanad.crs is None:
    raise ValueError("Wayanad boundary has no CRS.")

wayanad = wayanad.to_crs("EPSG:4326")

wayanad_geom = wayanad.geometry.union_all()


# --------------------------------------------------
# Check every Bhuvan feature
# --------------------------------------------------

for i, feature in enumerate(hits, start=1):

    geom = shape(feature["geometry"])

    props = feature.get("properties", {})

    district = props.get("District")
    year = props.get("Year")
    area = props.get("Area_sqm")

    intersects = geom.intersects(wayanad_geom)
    within = geom.within(wayanad_geom)

    intersection_area = 0

    if intersects:
        intersection = geom.intersection(wayanad_geom)
        intersection_area = intersection.area

    print()
    print("-" * 70)
    print(f"Feature #{i}")
    print(f"ID:       {feature.get('id')}")
    print(f"District: {district}")
    print(f"Year:     {year}")
    print(f"Area:     {area} m²")
    print(f"Intersects Wayanad: {intersects}")
    print(f"Fully within Wayanad: {within}")
    print(f"Intersection area: {intersection_area:.10f} square degrees")

    centroid = geom.centroid

    print(
        f"Centroid: {centroid.y:.6f}, {centroid.x:.6f}"
    )


print()
print("=" * 70)
print("CHECK COMPLETE")
print("=" * 70)