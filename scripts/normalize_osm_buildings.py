import json
import csv
from pathlib import Path

INPUT = Path(
    "data/raw/infrastructure/osm/meppadi_osm_infrastructure.json"
)

OUTPUT = Path(
    "data/processed/exposure/osm_buildings.csv"
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


def classify_building(building_type):
    residential = {
        "house",
        "residential",
        "detached",
        "apartments",
    }

    critical = {
        "school",
        "hospital",
        "college",
        "university",
        "library",
    }

    if building_type in residential:
        return "residential"

    if building_type in critical:
        return "critical"

    if building_type in {
        "commercial",
        "retail",
        "industrial",
        "warehouse",
        "hotel",
    }:
        return "economic"

    return "other"


with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)


rows = []

for element in data["elements"]:

    tags = element.get("tags", {})

    if "building" not in tags:
        continue

    building_type = tags.get("building", "unknown")

    rows.append({
        "osm_type": element.get("type"),
        "osm_id": element.get("id"),
        "building_type": building_type,
        "exposure_class": classify_building(building_type),
        "name": tags.get("name", ""),
    })


with open(OUTPUT, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "osm_type",
            "osm_id",
            "building_type",
            "exposure_class",
            "name",
        ],
    )

    writer.writeheader()
    writer.writerows(rows)


print(f"Building records: {len(rows)}")
print(f"Saved: {OUTPUT}")