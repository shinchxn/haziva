import requests
import json
from pathlib import Path

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

BBOX = "11.55,76.05,11.75,76.25"

QUERY = f"""
[out:json][timeout:90];
(
  way["building"]({BBOX});

  node["place"~"village|hamlet|town"]({BBOX});

  way["highway"]({BBOX});

  node["amenity"="hospital"]({BBOX});
  way["amenity"="hospital"]({BBOX});

  node["amenity"="clinic"]({BBOX});
  way["amenity"="clinic"]({BBOX});

  node["healthcare"="centre"]({BBOX});
  way["healthcare"="centre"]({BBOX});

  node["amenity"="school"]({BBOX});
  way["amenity"="school"]({BBOX});

  node["amenity"="fire_station"]({BBOX});
  way["amenity"="fire_station"]({BBOX});

  node["amenity"="shelter"]({BBOX});
  way["amenity"="shelter"]({BBOX});

  node["emergency"="assembly_point"]({BBOX});
  way["emergency"="assembly_point"]({BBOX});

  node["man_made"="water_works"]({BBOX});
  way["man_made"="water_works"]({BBOX});

  node["amenity"="drinking_water"]({BBOX});
  way["amenity"="drinking_water"]({BBOX});
);

out center tags;
"""

OUTPUT_DIR = Path("data/raw/infrastructure/osm")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "meppadi_osm_infrastructure.json"


def fetch():
    print("Connecting to OpenStreetMap Overpass...")

    headers = {
        "User-Agent": "Haziva-SIH2026/1.0 (educational disaster-management project)",
        "Accept": "application/json",
    }

    response = requests.post(
        OVERPASS_URL,
        data=QUERY.encode("utf-8"),
        headers=headers,
        timeout=180
    )

    print(f"HTTP status: {response.status_code}")

    if response.status_code != 200:
        print("Overpass response:")
        print(response.text[:3000])

    response.raise_for_status()

    return response.json()


def main():
    data = fetch()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print()
    print("Download successful!")
    print(f"Saved to: {OUTPUT_FILE}")
    print(f"Total elements: {len(data['elements'])}")
    print()

    counts = {}

    for element in data["elements"]:
        tags = element.get("tags", {})

        if "building" in tags:
            key = "buildings"
        elif "highway" in tags:
            key = "roads"
        elif tags.get("amenity") == "hospital":
            key = "hospitals"
        elif tags.get("amenity") == "clinic":
            key = "clinics"
        elif tags.get("healthcare") == "centre":
            key = "healthcare_centres"
        elif tags.get("amenity") == "school":
            key = "schools"
        elif tags.get("amenity") == "fire_station":
            key = "fire_stations"
        elif tags.get("amenity") == "shelter":
            key = "shelters"
        elif tags.get("emergency") == "assembly_point":
            key = "assembly_points"
        elif tags.get("man_made") == "water_works":
            key = "water_works"
        elif tags.get("amenity") == "drinking_water":
            key = "drinking_water"
        elif "place" in tags:
            key = "places"
        else:
            key = "other"

        counts[key] = counts.get(key, 0) + 1

    print("Counts:")
    for key, value in sorted(
        counts.items(),
        key=lambda x: -x[1]
    ):
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()