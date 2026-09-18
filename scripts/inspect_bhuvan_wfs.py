import requests
import xml.etree.ElementTree as ET

WFS_URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/ows"

LAYERS = [
    "disaster:KL_SLIM_2014_GCS",
    "disaster:KL_SLIM_2017",
    "disaster:KERALA_MERGE_gcs",
    "disaster:kl_landslides_new",
]

params = {
    "SERVICE": "WFS",
    "REQUEST": "GetCapabilities",
    "VERSION": "2.0.0",
}

print("=" * 60)
print("BHUvAN / NRSC WFS INSPECTION")
print("=" * 60)

response = requests.get(
    WFS_URL,
    params=params,
    timeout=120
)

print("HTTP status:", response.status_code)
print("Response size:", len(response.content), "bytes")

if response.status_code != 200:
    print(response.text[:2000])
    raise RuntimeError("WFS request failed")

root = ET.fromstring(response.content)

# Handle XML namespaces generically
found = {}

for elem in root.iter():

    tag = elem.tag.split("}")[-1]

    if tag in ("FeatureType", "FeatureTypeList"):

        name_elem = None

        for child in elem.iter():
            child_tag = child.tag.split("}")[-1]

            if child_tag == "Name":
                name_elem = child
                break

        if name_elem is not None:
            found[name_elem.text] = True


print()
print("=" * 60)
print("REQUESTED FEATURE TYPES")
print("=" * 60)

for layer in LAYERS:

    if layer in found:
        print("FOUND:", layer)
    else:
        print("NOT FOUND:", layer)

print()
print("=" * 60)
print("ALL FEATURE TYPES CONTAINING 'LANDSLIDE'")
print("=" * 60)

for name in sorted(found):

    if "landslide" in name.lower() or "ls_" in name.lower():
        print(name)

print()
print("=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)