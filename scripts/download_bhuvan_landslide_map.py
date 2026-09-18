import requests
from pathlib import Path


WMS_URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"

OUTPUT = Path(
    "data/raw/landslide/inventory/wayanad_bhuvan_landslides.png"
)

# Exact Wayanad bounding box from our boundary
MIN_LON = 75.7722
MIN_LAT = 11.4427
MAX_LON = 76.4356
MAX_LAT = 11.9706

WIDTH = 2000
HEIGHT = 1600

params = {
    "SERVICE": "WMS",
    "VERSION": "1.3.0",
    "REQUEST": "GetMap",

    "LAYERS": "disaster:kl_landslides_new",
    "STYLES": "disaster:kl_landslide_style",

    "CRS": "EPSG:4326",

    # WMS 1.3.0 EPSG:4326 axis order = latitude,longitude
    "BBOX": f"{MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON}",

    "WIDTH": WIDTH,
    "HEIGHT": HEIGHT,

    "FORMAT": "image/png",
    "TRANSPARENT": "TRUE",
}

headers = {
    "User-Agent": "Haziva-SIH2026/1.0",
}

print("=" * 70)
print("DOWNLOADING BHUVAN WAYANAD LANDSLIDE MAP")
print("=" * 70)

response = requests.get(
    WMS_URL,
    params=params,
    headers=headers,
    timeout=180,
)

print("HTTP:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Bytes:", len(response.content))

response.raise_for_status()

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT.write_bytes(response.content)

print()
print("Saved:")
print(OUTPUT)