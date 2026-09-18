import requests
import xml.etree.ElementTree as ET

WMS_URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"

LAYERS = [
    "disaster:KL_SLIM_2014_GCS",
    "disaster:KL_SLIM_2017",
    "disaster:KERALA_MERGE_gcs",
    "disaster:kl_landslides_new",
]

params = {
    "SERVICE": "WMS",
    "REQUEST": "GetCapabilities",
    "VERSION": "1.3.0",
}

print("=" * 60)
print("BHUvAN / NRSC LANDSLIDE LAYER INSPECTION")
print("=" * 60)

response = requests.get(
    WMS_URL,
    params=params,
    timeout=120
)

print("HTTP status:", response.status_code)
print("Response size:", len(response.content), "bytes")

if response.status_code != 200:
    raise RuntimeError("Failed to retrieve WMS capabilities")

root = ET.fromstring(response.content)

# WMS XML namespaces
ns = {
    "wms": "http://www.opengis.net/wms"
}

layers_found = {}

for layer in root.findall(".//wms:Layer", ns):
    name = layer.find("wms:Name", ns)

    if name is None:
        continue

    name_text = name.text

    if name_text in LAYERS:
        title = layer.find("wms:Title", ns)
        abstract = layer.find("wms:Abstract", ns)

        layers_found[name_text] = {
            "title": title.text if title is not None else "",
            "abstract": abstract.text if abstract is not None else "",
        }

print()
print("REQUESTED LAYERS")
print("=" * 60)

for layer_name in LAYERS:

    if layer_name in layers_found:

        info = layers_found[layer_name]

        print()
        print("FOUND:", layer_name)
        print("Title:", info["title"])
        print("Abstract:", info["abstract"])

    else:

        print()
        print("NOT FOUND:", layer_name)

print()
print("=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)