import geopandas as gpd
from pathlib import Path

INPUT = Path(
    "data/raw/boundaries/gadm41_IND_2.json"
)

OUTPUT = Path(
    "data/raw/boundaries/wayanad_boundary.geojson"
)

gdf = gpd.read_file(INPUT)

wayanad = gdf[
    (gdf["NAME_1"] == "Kerala") &
    (gdf["NAME_2"] == "Wayanad")
].copy()

if wayanad.empty:
    raise ValueError("Wayanad district was not found.")

wayanad.to_file(
    OUTPUT,
    driver="GeoJSON"
)

print("Wayanad boundary created successfully.")
print("Features:", len(wayanad))
print("CRS:", wayanad.crs)
print("Output:", OUTPUT)
print("Bounds:", wayanad.total_bounds)