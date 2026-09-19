import sys
import json
import logging
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("extract_candidate_facilities")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_osm_path = base_dir / "data" / "raw" / "infrastructure" / "osm" / "meppadi_osm_infrastructure.json"
    output_dir = base_dir / "data" / "processed" / "exposure" / "relocation"
    output_csv = output_dir / "wayanad_relocation_candidate_facilities.csv"
    output_gpkg = output_dir / "wayanad_relocation_candidate_facilities.gpkg"

    if not raw_osm_path.exists():
        raise FileNotFoundError(f"Required raw OSM dataset not found at: {raw_osm_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading raw OSM infrastructure JSON from {raw_osm_path}...")
    with open(raw_osm_path, "r", encoding="utf-8") as f:
        osm_data = json.load(f)

    elements = osm_data.get("elements", [])
    logger.info(f"Total OSM elements in JSON: {len(elements)}")

    total_elements = len(elements)
    nodes_inspected = 0
    ways_inspected = 0
    facilities_selected = 0
    facilities_rejected = 0
    facilities_node_coords = 0
    facilities_way_center_coords = 0
    facilities_missing_coords = 0
    excluded_bus_shelters = 0

    candidates = []

    for elem in elements:
        elem_type = elem.get("type")
        elem_id = elem.get("id")
        tags = elem.get("tags", {})

        if elem_type == "node":
            nodes_inspected += 1
        elif elem_type == "way":
            ways_inspected += 1

        amenity = tags.get("amenity")
        building = tags.get("building")
        healthcare = tags.get("healthcare")
        office = tags.get("office")
        shelter_type = tags.get("shelter_type")
        name = tags.get("name", "")

        # 1. Explicit Exclusion: Bus-stop shelters
        if amenity == "shelter" and shelter_type == "public_transport":
            excluded_bus_shelters += 1
            facilities_rejected += 1
            continue

        # 2. Explicit Exclusion: Non-relocation commercial/residential/infrastructure amenities & buildings
        if amenity in [
            "bus_stop", "parking", "fuel", "restaurant", "place_of_worship", "bank",
            "veterinary", "toilets", "cafe", "pub", "bar", "fast_food", "cinema",
            "marketplace", "theatre", "dentist"
        ]:
            facilities_rejected += 1
            continue

        if building in [
            "house", "residential", "industrial", "commercial", "shed", "retail",
            "apartments", "church", "mosque", "temple"
        ]:
            # Skip unless tags explicitly define a public community/health/education facility
            if not (
                amenity in ["school", "college", "university", "hospital", "clinic", "community_centre", "community_hall", "childcare", "police", "fire_station"]
                or healthcare
                or office == "government"
            ):
                facilities_rejected += 1
                continue

        category = None
        role = None
        selection_reason = None

        # A. Education
        if amenity in ["school", "college", "university"] or building in ["school", "college", "university"]:
            category = "education"
            role = "relocation_candidate"
            selection_reason = f"amenity={amenity}" if amenity in ["school", "college", "university"] else f"building={building}"

        # B. Community
        elif amenity in ["community_centre", "community_hall", "public_hall", "events_venue", "social_facility"] or tags.get("social_facility"):
            category = "community"
            role = "relocation_candidate"
            selection_reason = f"amenity={amenity}" if amenity else "social_facility"

        elif amenity == "childcare":
            category = "community"
            role = "potential_relocation_candidate"
            selection_reason = "amenity=childcare"

        # C. Healthcare / Medical Support
        elif amenity in ["hospital", "clinic"] or healthcare in ["hospital", "clinic", "centre"] or building in ["hospital", "clinic"]:
            category = "healthcare"
            role = "medical_support"
            selection_reason = f"healthcare={healthcare}" if healthcare else (f"amenity={amenity}" if amenity else f"building={building}")

        # D. Public / Government Buildings
        elif building in ["civic", "government", "public"] or office == "government" or amenity in ["police", "fire_station", "townhall"]:
            category = "public_building"
            role = "potential_relocation_candidate"
            selection_reason = f"office={office}" if office == "government" else (f"building={building}" if building else f"amenity={amenity}")

        if not category or not role:
            facilities_rejected += 1
            continue

        # Extract coordinates
        lat = None
        lon = None
        coord_src = None

        if elem_type == "node":
            lat = elem.get("lat")
            lon = elem.get("lon")
            coord_src = "node_latlon"
            if lat is not None and lon is not None:
                facilities_node_coords += 1
        elif elem_type == "way":
            center = elem.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
            coord_src = "way_center"
            if lat is not None and lon is not None:
                facilities_way_center_coords += 1

        if lat is None or lon is None or not (isinstance(lat, (int, float))) or not (isinstance(lon, (int, float))):
            facilities_missing_coords += 1
            logger.warning(f"Excluding candidate OSM {elem_type} {elem_id}: missing lat/lon coordinates")
            continue

        candidate_id = f"OSM_{elem_type}_{elem_id}"

        # Clean tags to preserve provenance in JSON string
        original_tags_json = json.dumps(tags, ensure_ascii=False)

        candidate_rec = {
            "candidate_id": candidate_id,
            "osm_type": elem_type,
            "osm_id": str(elem_id),
            "name": name,
            "facility_category": category,
            "facility_role": role,
            "amenity": amenity if amenity else "",
            "building_type": building if building else "",
            "shelter_type": shelter_type if shelter_type else "",
            "latitude": float(lat),
            "longitude": float(lon),
            "source": "OpenStreetMap_Overpass",
            "selection_reason": selection_reason,
            "coordinate_source": coord_src,
            "original_tags": original_tags_json
        }

        candidates.append(candidate_rec)
        facilities_selected += 1

    logger.info(f"Extraction summary:")
    logger.info(f"  Total elements inspected: {total_elements}")
    logger.info(f"  Nodes inspected: {nodes_inspected}")
    logger.info(f"  Ways inspected: {ways_inspected}")
    logger.info(f"  Facilities selected: {facilities_selected}")
    logger.info(f"  Facilities rejected: {facilities_rejected}")
    logger.info(f"  Facilities with node coords: {facilities_node_coords}")
    logger.info(f"  Facilities with way center coords: {facilities_way_center_coords}")
    logger.info(f"  Facilities missing coords: {facilities_missing_coords}")
    logger.info(f"  Excluded public transport shelters: {excluded_bus_shelters}")

    if not candidates:
        raise ValueError("No candidate facilities were extracted. Check extraction rules!")

    df = pd.DataFrame(candidates)

    # Convert to GeoDataFrame with Point geometry (EPSG:4326)
    geometry = [Point(lon, lat) for lon, lat in zip(df["longitude"], df["latitude"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    # Save to CSV and GPKG
    df.to_csv(output_csv, index=False, encoding="utf-8")
    gdf.to_file(output_gpkg, driver="GPKG", layer="relocation_candidates")

    logger.info(f"Saved CSV candidate dataset to: {output_csv}")
    logger.info(f"Saved GPKG candidate layer to: {output_gpkg}")

    # ============================================================
    # FINAL QA CHECKS
    # ============================================================
    logger.info("Running Final QA Checks...")

    # 1. Confirm candidate IDs are unique
    assert len(df["candidate_id"].unique()) == len(df), "QA Failed: Candidate IDs are not unique!"

    # 2. Confirm coordinates are finite
    assert df["latitude"].notnull().all() and df["longitude"].notnull().all(), "QA Failed: Null coordinates found!"
    assert not df["latitude"].isin([float("inf"), float("-inf")]).any(), "QA Failed: Infinite latitude found!"
    assert not df["longitude"].isin([float("inf"), float("-inf")]).any(), "QA Failed: Infinite longitude found!"

    # 3. Confirm latitude range (-90 to 90)
    assert ((df["latitude"] >= -90) & (df["latitude"] <= 90)).all(), "QA Failed: Latitude out of range [-90, 90]!"

    # 4. Confirm longitude range (-180 to 180)
    assert ((df["longitude"] >= -180) & (df["longitude"] <= 180)).all(), "QA Failed: Longitude out of range [-180, 180]!"

    # 5. Confirm geometry is valid
    assert gdf.geometry.is_valid.all(), "QA Failed: Invalid geometries found!"

    # 6. Confirm CRS is EPSG:4326
    assert gdf.crs.to_epsg() == 4326, f"QA Failed: CRS is {gdf.crs}, expected EPSG:4326!"

    # 7. Confirm no public_transport shelter appears as a relocation_candidate
    bus_shelter_mask = (df["amenity"] == "shelter") & (df["shelter_type"] == "public_transport")
    assert not bus_shelter_mask.any(), "QA Failed: Public transport shelter found in candidate dataset!"

    # 8. Confirm every candidate has a non-empty selection_reason
    assert (df["selection_reason"].str.len() > 0).all(), "QA Failed: Candidate with empty selection_reason found!"

    # 9. Confirm every candidate has coordinate_source in ["node_latlon", "way_center"]
    assert df["coordinate_source"].isin(["node_latlon", "way_center"]).all(), "QA Failed: Invalid coordinate_source found!"

    logger.info("ALL QA CHECKS PASSED SUCCESSFULLY!")

    # 10. Print facility-category counts
    print("\nCandidate Count by Facility Category:")
    print(df["facility_category"].value_counts().to_string())

    # 11. Print facility-role counts
    print("\nCandidate Count by Facility Role:")
    print(df["facility_role"].value_counts().to_string())

    # 12. Print the first 20 candidates
    print("\nFirst 20 Extracted Relocation Candidates:")
    preview_cols = ["candidate_id", "name", "facility_category", "facility_role", "selection_reason", "coordinate_source", "latitude", "longitude"]
    print(df[preview_cols].head(20).to_string())

if __name__ == "__main__":
    main()
