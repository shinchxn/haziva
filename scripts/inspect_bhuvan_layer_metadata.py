from pathlib import Path
import xml.etree.ElementTree as ET


XML_FILE = Path(
    "data/raw/landslide/inventory/bhuvan_wms_capabilities.xml"
)

TARGETS = {
    "disaster:KL_SLIM_2017",
    "disaster:KERALA_MERGE_gcs",
    "disaster:kl_landslides_new",
}


tree = ET.parse(XML_FILE)
root = tree.getroot()

ns = {
    "wms": "http://www.opengis.net/wms",
}

print("=" * 80)
print("BHUVAN LANDSLIDE LAYER METADATA")
print("=" * 80)

found = 0

for layer in root.findall(".//wms:Layer", ns):

    name_el = layer.find("wms:Name", ns)

    if name_el is None:
        continue

    name = name_el.text

    if name not in TARGETS:
        continue

    found += 1

    title = layer.findtext(
        "wms:Title",
        default="",
        namespaces=ns
    )

    abstract = layer.findtext(
        "wms:Abstract",
        default="",
        namespaces=ns
    )

    print()
    print("-" * 80)
    print(f"Layer:   {name}")
    print(f"Title:   {title}")
    print(f"Abstract:{abstract}")

    print("\nCRS:")
    for crs in layer.findall("wms:CRS", ns):
        print(" ", crs.text)

    print("\nStyles:")
    for style in layer.findall("wms:Style", ns):

        style_name = style.findtext(
            "wms:Name",
            default="",
            namespaces=ns
        )

        style_title = style.findtext(
            "wms:Title",
            default="",
            namespaces=ns
        )

        print(
            f"  {style_name} | {style_title}"
        )

    print("\nBounding boxes:")

    for bbox in layer.findall("wms:EX_GeographicBoundingBox", ns):

        west = bbox.findtext(
            "wms:westBoundLongitude",
            namespaces=ns
        )

        east = bbox.findtext(
            "wms:eastBoundLongitude",
            namespaces=ns
        )

        south = bbox.findtext(
            "wms:southBoundLatitude",
            namespaces=ns
        )

        north = bbox.findtext(
            "wms:northBoundLatitude",
            namespaces=ns
        )

        print(
            f"  lon: {west} → {east}"
        )

        print(
            f"  lat: {south} → {north}"
        )

    print("\nMetadata URLs:")

    for metadata in layer.findall(
        "wms:MetadataURL",
        ns
    ):

        url = metadata.find(
            "wms:OnlineResource",
            ns
        )

        if url is not None:
            print(
                " ",
                url.attrib
            )

print()
print("=" * 80)
print(f"TARGET LAYERS FOUND: {found}")
print("=" * 80)