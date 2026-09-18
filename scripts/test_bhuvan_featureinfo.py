import requests
from pathlib import Path

WMS_URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"

LAYERS = [
    "disaster:KL_SLIM_2017",
    "disaster:KERALA_MERGE_gcs",
    "disaster:kl_landslides_new",
]

# Wayanad approximate bounding box
MIN_LON = 75.7722
MIN_LAT = 11.4427
MAX_LON = 76.4356
MAX_LAT = 11.9706

WIDTH = 1000
HEIGHT = 1000

# Test point near the center of Wayanad
TEST_LON = (MIN_LON + MAX_LON) / 2
TEST_LAT = (MIN_LAT + MAX_LAT) / 2

# Convert geographic point to image pixel
x = int((TEST_LON - MIN_LON) / (MAX_LON - MIN_LON) * WIDTH)
y = int((MAX_LAT - TEST_LAT) / (MAX_LAT - MIN_LAT) * HEIGHT)

print("=" * 70)
print("BHUvAN / NRSC GETFEATUREINFO TEST")
print("=" * 70)

print("Test coordinate:")
print("Longitude:", TEST_LON)
print("Latitude :", TEST_LAT)
print("Pixel    :", x, y)

for layer in LAYERS:

    print()
    print("-" * 70)
    print("LAYER:", layer)

    params = {
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer,
        "QUERY_LAYERS": layer,
        "INFO_FORMAT": "application/json",
        "CRS": "EPSG:4326",
        "BBOX": f"{MIN_LAT},{MIN_LON},{MAX_LAT},{MAX_LON}",
        "WIDTH": WIDTH,
        "HEIGHT": HEIGHT,
        "I": x,
        "J": y,
        "FEATURE_COUNT": 10,
    }

    try:

        response = requests.get(
            WMS_URL,
            params=params,
            timeout=60,
        )

        print("HTTP status:", response.status_code)
        print("Content type:", response.headers.get("Content-Type"))
        print("Response size:", len(response.content))

        print()
        print("RESPONSE:")
        print(response.text[:5000])

    except Exception as e:

        print("ERROR:", repr(e))

print()
print("=" * 70)
print("GETFEATUREINFO TEST COMPLETE")
print("=" * 70)