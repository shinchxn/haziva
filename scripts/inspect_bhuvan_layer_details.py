import xml.etree.ElementTree as ET
from pathlib import Path

CAPABILITIES = (
    Path("data")
    / "raw"
    / "landslide"
    / "inventory"
    / "bhuvan_wms_capabilities.xml"
)

LAYERS = [
    "disaster:KL_SLIM_2014_GCS",
    "disaster:KL_SLIM_2017",
    "disaster:KERALA_MERGE_gcs",
    "disaster:kl_landslides_new",
]


def local_name(tag):
    return tag.split("}")[-1]


def find_child(parent, wanted):
    for child in parent:
        if local_name(child.tag) == wanted:
            return child
    return None


print("=" * 70)
print("BHUvAN / NRSC WMS LOCAL METADATA INSPECTION")
print("=" * 70)

if not CAPABILITIES.exists():
    raise FileNotFoundError(
        f"Capabilities file not found:\n{CAPABILITIES}"
    )

print("Reading:", CAPABILITIES)
print("File size:", CAPABILITIES.stat().st_size, "bytes")

root = ET.parse(CAPABILITIES).getroot()

found = {}

for layer in root.iter():

    if local_name(layer.tag) != "Layer":
        continue

    name_elem = find_child(layer, "Name")

    if name_elem is None:
        continue

    name = name_elem.text

    if name not in LAYERS:
        continue

    title_elem = find_child(layer, "Title")
    abstract_elem = find_child(layer, "Abstract")

    details = {
        "title": title_elem.text if title_elem is not None else None,
        "abstract": abstract_elem.text if abstract_elem is not None else None,
        "crs": [],
        "bbox": [],
        "styles": [],
    }

    for child in layer:

        tag = local_name(child.tag)

        if tag in ("CRS", "SRS"):

            if child.text:
                details["crs"].append(child.text)

        elif tag == "BoundingBox":

            details["bbox"].append(dict(child.attrib))

        elif tag == "EX_GeographicBoundingBox":

            bbox_values = {}

            for sub in child:

                if sub.text:
                    bbox_values[local_name(sub.tag)] = sub.text

            details["bbox"].append(bbox_values)

        elif tag == "LatLonBoundingBox":

            details["bbox"].append(dict(child.attrib))

        elif tag == "Style":

            style_name = find_child(child, "Name")

            style_title = find_child(child, "Title")

            details["styles"].append({
                "name": style_name.text if style_name is not None else None,
                "title": style_title.text if style_title is not None else None,
            })

    found[name] = details


print()
print("=" * 70)
print("REQUESTED LAYERS")
print("=" * 70)

for layer_name in LAYERS:

    if layer_name not in found:

        print()
        print("NOT FOUND:", layer_name)
        continue

    info = found[layer_name]

    print()
    print("-" * 70)
    print("LAYER:", layer_name)
    print("TITLE:", info["title"])
    print("ABSTRACT:", info["abstract"])

    print()
    print("CRS/SRS:")

    for crs in info["crs"]:
        print("  ", crs)

    print()
    print("BOUNDING BOXES:")

    for bbox in info["bbox"]:
        print("  ", bbox)

    print()
    print("STYLES:")

    for style in info["styles"]:
        print("  ", style)


print()
print("=" * 70)
print("INSPECTION COMPLETE")
print("=" * 70)