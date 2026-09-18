import json
import csv
from pathlib import Path

INPUT = Path(
    "data/raw/infrastructure/osm/meppadi_osm_infrastructure.json"
)

OUTPUT = Path(
    "data/processed/exposure/osm_facilities.csv"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def get_role(tags):
    amenity = tags.get("amenity")
    healthcare = tags.get("healthcare")

    if amenity == "hospital" or healthcare == "hospital":
        return "hospital"

    if amenity == "clinic" or healthcare == "clinic":
        return "clinic"

    if healthcare == "centre":
        return "healthcare_centre"

    if amenity == "school":
        return "school"

    if amenity == "shelter":
        return "shelter"

    if amenity == "fire_station":
        return "fire_station"

    if amenity == "police":
        return "police"

    if amenity == "drinking_water":
        return "water_point"

    if amenity == "community_centre":
        return "community_facility"

    return amenity or healthcare or "other"


with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)


rows = []

for element in data["elements"]:

    tags = element.get("tags", {})

    if not tags.get("amenity") and not tags.get("healthcare"):
        continue

    rows.append({
        "osm_type": element.get("type"),
        "osm_id": element.get("id"),
        "name": tags.get("name", ""),
        "amenity": tags.get("amenity", ""),
        "healthcare": tags.get("healthcare", ""),
        "facility_role": get_role(tags),
        "latitude": element.get("lat", ""),
        "longitude": element.get("lon", "")
    })


with open(OUTPUT, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "osm_type",
            "osm_id",
            "name",
            "amenity",
            "healthcare",
            "facility_role",
            "latitude",
            "longitude"
        ]
    )

    writer.writeheader()
    writer.writerows(rows)


print(f"Input facilities: {len(rows)}")
print(f"Saved: {OUTPUT}")