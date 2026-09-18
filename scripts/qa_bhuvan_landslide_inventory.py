from pathlib import Path

import geopandas as gpd
import numpy as np


INPUT = Path(
    "data/processed/landslide/inventory/"
    "wayanad_bhuvan_landslides_wms_derived.geojson"
)


print("=" * 80)
print("BHUVAN LANDSLIDE INVENTORY QA")
print("=" * 80)


# --------------------------------------------------
# LOAD
# --------------------------------------------------

gdf = gpd.read_file(INPUT)

print()
print("Input:")
print(INPUT)

print()
print("Features:", len(gdf))
print("CRS:", gdf.crs)


# --------------------------------------------------
# PROJECT TO UTM
# --------------------------------------------------

gdf_utm = gdf.to_crs("EPSG:32643")

areas = gdf_utm.geometry.area

print()
print("-" * 80)
print("AREA STATISTICS")
print("-" * 80)

print(f"Minimum area: {areas.min():.2f} m²")
print(f"Maximum area: {areas.max():.2f} m²")
print(f"Mean area:    {areas.mean():.2f} m²")
print(f"Median area:  {areas.median():.2f} m²")

print()
print("Percentiles:")

for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]:
    print(
        f"P{p:02d}: {np.percentile(areas, p):.2f} m²"
    )


# --------------------------------------------------
# AREA BINS
# --------------------------------------------------

print()
print("-" * 80)
print("AREA DISTRIBUTION")
print("-" * 80)

bins = [
    0,
    100,
    500,
    1_000,
    5_000,
    10_000,
    50_000,
    100_000,
    500_000,
    float("inf"),
]

labels = [
    "<100 m²",
    "100–500 m²",
    "500–1,000 m²",
    "1,000–5,000 m²",
    "5,000–10,000 m²",
    "10,000–50,000 m²",
    "50,000–100,000 m²",
    "100,000–500,000 m²",
    ">500,000 m²",
]

counts = np.histogram(
    areas,
    bins=bins
)[0]

for label, count in zip(labels, counts):
    print(
        f"{label:20s}: {count}"
    )


# --------------------------------------------------
# GEOMETRY TYPES
# --------------------------------------------------

print()
print("-" * 80)
print("GEOMETRY TYPES")
print("-" * 80)

print(
    gdf.geometry.geom_type.value_counts()
)


# --------------------------------------------------
# TOTAL AREA
# --------------------------------------------------

total_area = areas.sum()

print()
print("-" * 80)
print("TOTAL")
print("-" * 80)

print(
    f"Total mapped area: {total_area:,.2f} m²"
)

print(
    f"Total mapped area: {total_area / 1_000_000:.4f} km²"
)


# --------------------------------------------------
# CENTROID EXTENT
# --------------------------------------------------

centroids = gdf_utm.geometry.centroid

print()
print("-" * 80)
print("CENTROID EXTENT")
print("-" * 80)

print(
    f"Easting:  {centroids.x.min():.2f}"
    f" → {centroids.x.max():.2f}"
)

print(
    f"Northing: {centroids.y.min():.2f}"
    f" → {centroids.y.max():.2f}"
)


# --------------------------------------------------
# SMALL POLYGON CHECK
# --------------------------------------------------

print()
print("-" * 80)
print("SMALL POLYGON CHECK")
print("-" * 80)

for threshold in [
    100,
    500,
    1_000,
    5_000,
]:

    count = int(
        (areas < threshold).sum()
    )

    percentage = (
        100 * count / len(areas)
    )

    print(
        f"< {threshold:>6,} m²:"
        f" {count:3d}"
        f" ({percentage:.2f}%)"
    )


print()
print("=" * 80)
print("QA COMPLETE")
print("=" * 80)