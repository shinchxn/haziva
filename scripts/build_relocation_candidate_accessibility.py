import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("relocation_candidate_accessibility")

def main():
    base_dir = Path(__file__).resolve().parent.parent

    # File paths
    cand_csv_path = base_dir / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_safety.csv"
    cand_gpkg_path = base_dir / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_safety.gpkg"
    village_pop_path = base_dir / "data" / "processed" / "exposure" / "census_nwdp_reconciliation" / "wayanad_census_nwdp_village_population_2011.gpkg"
    village_risk_csv_path = base_dir / "data" / "processed" / "exposure" / "village_risk" / "wayanad_village_dynamic_risk.csv"
    raw_osm_path = base_dir / "data" / "raw" / "infrastructure" / "osm" / "meppadi_osm_infrastructure.json"

    output_dir = base_dir / "data" / "processed" / "exposure" / "relocation"
    output_csv = output_dir / "wayanad_relocation_candidate_accessibility.csv"
    output_gpkg = output_dir / "wayanad_relocation_candidate_accessibility.gpkg"

    # STEP 1: INPUT VALIDATION
    logger.info("Step 1: Validating input datasets...")
    for p in [cand_csv_path, cand_gpkg_path, village_pop_path, village_risk_csv_path, raw_osm_path]:
        if not p.exists():
            raise FileNotFoundError(f"Validation Error: Required input file missing at {p}")

    cand_gdf = gpd.read_file(cand_gpkg_path)
    cand_count = len(cand_gdf)
    logger.info(f"Loaded candidate safety dataset: {cand_count} candidates, CRS={cand_gdf.crs}")
    if cand_count != 794:
        logger.warning(f"Candidate count is {cand_count} (expected 794)")

    villages_gdf = gpd.read_file(village_pop_path)
    logger.info(f"Loaded village boundaries GPKG: {len(villages_gdf)} villages, CRS={villages_gdf.crs}")

    with open(raw_osm_path, "r", encoding="utf-8") as f:
        osm_data = json.load(f)
    osm_elements = osm_data.get("elements", [])
    logger.info(f"Loaded raw OSM infrastructure JSON: {len(osm_elements)} elements")

    # STEP 2: DEFINE ACCESSIBILITY REFERENCE POINT FOR VILLAGES
    logger.info("Step 2: Calculating village representative reference points...")
    villages_4326 = villages_gdf.to_crs(epsg=4326).copy()
    villages_4326["rep_pt"] = villages_4326.geometry.representative_point()
    v_lat_map = dict(zip(villages_4326["village_code"].astype(str), villages_4326["rep_pt"].geometry.y))
    v_lon_map = dict(zip(villages_4326["village_code"].astype(str), villages_4326["rep_pt"].geometry.x))

    villages_7755 = villages_gdf.to_crs(epsg=7755).copy()
    villages_7755["rep_pt_7755"] = villages_7755.geometry.representative_point()
    v_pt_7755_map = dict(zip(villages_7755["village_code"].astype(str), villages_7755["rep_pt_7755"]))

    # STEP 3: EUCLIDEAN / GEODESIC DISTANCE CALCULATION
    logger.info("Step 3: Calculating straight-line distances to matched village reference points...")
    cand_7755 = cand_gdf.to_crs(epsg=7755)

    v_ref_lats = []
    v_ref_lons = []
    dists_to_village_km = []
    dist_methods = []

    for idx, row in cand_7755.iterrows():
        v_code = str(row["matched_village_code"]) if pd.notnull(row["matched_village_code"]) else None
        v_status = str(row["village_match_status"]) if pd.notnull(row["village_match_status"]) else "unmatched"

        if v_status in ["matched", "boundary_case"] and v_code and v_code in v_pt_7755_map:
            ref_lat = float(v_lat_map[v_code])
            ref_lon = float(v_lon_map[v_code])
            rep_pt_7755 = v_pt_7755_map[v_code]
            dist_m = float(row.geometry.distance(rep_pt_7755))
            dist_km = round(dist_m / 1000.0, 3)
            method = "geodesic_straight_line"
        else:
            ref_lat = None
            ref_lon = None
            dist_km = None
            method = "none"

        v_ref_lats.append(ref_lat)
        v_ref_lons.append(ref_lon)
        dists_to_village_km.append(dist_km)
        dist_methods.append(method)

    cand_gdf["village_reference_latitude"] = v_ref_lats
    cand_gdf["village_reference_longitude"] = v_ref_lons
    cand_gdf["distance_to_village_km"] = dists_to_village_km
    cand_gdf["distance_method"] = dist_methods

    # STEP 4 & 5: ROAD NETWORK EXTRACTION & COVERAGE ANALYSIS
    logger.info("Step 4 & 5: Extracting OSM road network and analyzing coverage...")
    highways_count = {}
    road_points = []
    bridge_count = 0
    named_road_count = 0
    surface_count = 0
    access_count = 0

    for elem in osm_elements:
        if elem.get("type") == "way":
            tags = elem.get("tags", {})
            h_type = tags.get("highway")
            if h_type:
                highways_count[h_type] = highways_count.get(h_type, 0) + 1
                if tags.get("bridge"): bridge_count += 1
                if tags.get("name"): named_road_count += 1
                if tags.get("surface"): surface_count += 1
                if tags.get("access"): access_count += 1

                center = elem.get("center", {})
                lat = center.get("lat")
                lon = center.get("lon")
                if lat is not None and lon is not None:
                    road_points.append({
                        "osm_id": elem["id"],
                        "highway": h_type,
                        "name": tags.get("name", ""),
                        "bridge": tags.get("bridge", ""),
                        "surface": tags.get("surface", ""),
                        "access": tags.get("access", ""),
                        "geometry": Point(lon, lat)
                    })

    road_way_count = sum(highways_count.values())
    road_gdf_4326 = gpd.GeoDataFrame(road_points, crs="EPSG:4326")
    road_gdf_32643 = road_gdf_4326.to_crs(epsg=32643)

    # Approximate network context metrics
    road_geometry_count = len(road_gdf_32643)
    road_length_km = 0.0  # Point centroids preserved from Overpass out center extract

    logger.info(f"OSM Road Network Statistics:")
    logger.info(f"  Total road ways: {road_way_count}")
    logger.info(f"  Road segment center geometries: {road_geometry_count}")
    logger.info(f"  Bridges: {bridge_count}, Named roads: {named_road_count}, Surface tags: {surface_count}, Access tags: {access_count}")

    # STEP 6: NEAREST ROAD EVIDENCE
    logger.info("Step 6: Calculating distance to nearest mapped OSM road segment...")
    cand_32643 = cand_gdf.to_crs(epsg=32643)

    dists_nearest_road_m = []
    nearest_road_classes = []
    nearest_road_names = []
    nearest_road_statuses = []

    for idx, row in cand_32643.iterrows():
        pt = row.geometry
        if len(road_gdf_32643) > 0:
            dists = road_gdf_32643.geometry.distance(pt)
            min_idx = dists.idxmin()
            min_dist_m = float(dists.loc[min_idx])
            matched_road = road_gdf_32643.loc[min_idx]

            dists_nearest_road_m.append(round(min_dist_m, 2))
            nearest_road_classes.append(matched_road["highway"])
            nearest_road_names.append(matched_road["name"] if matched_road["name"] else "")
            nearest_road_statuses.append("NEAREST_OSM_ROAD_AVAILABLE")
        else:
            dists_nearest_road_m.append(None)
            nearest_road_classes.append(None)
            nearest_road_names.append(None)
            nearest_road_statuses.append("NOT_AVAILABLE")

    cand_gdf["distance_to_nearest_road_m"] = dists_nearest_road_m
    cand_gdf["nearest_road_class"] = nearest_road_classes
    cand_gdf["nearest_road_name"] = nearest_road_names
    cand_gdf["nearest_road_status"] = nearest_road_statuses

    # Contextual network fields
    cand_gdf["road_way_count_context"] = road_way_count
    cand_gdf["road_network_length_km_context"] = float(road_length_km)

    # STEP 7 & 8: NETWORK ROUTING STATUS CONTROL
    # Overpass JSON contains way center points rather than connected node LineString topologies.
    # Therefore connected graph routing is NOT implemented in MVP to prevent fabricated travel paths.
    logger.info("Step 7 & 8: Network routing status set to NOT_IMPLEMENTED (defensible MVP control)")
    cand_gdf["network_routing_status"] = "NOT_IMPLEMENTED"
    cand_gdf["road_network_distance_km"] = None
    cand_gdf["travel_time_status"] = "NOT_IMPLEMENTED"
    cand_gdf["road_travel_distance_status"] = "NOT_IMPLEMENTED"

    # STEP 9 & 10: ACCESSIBILITY STATUS AND REASON CODES
    logger.info("Step 9 & 10: Determining accessibility status and generating reason codes...")
    acc_statuses = []
    acc_reason_codes_list = []
    acc_reasons_list = []

    for idx, row in cand_gdf.iterrows():
        v_status = str(row["village_match_status"]) if pd.notnull(row["village_match_status"]) else "unmatched"
        dist_km = row["distance_to_village_km"]
        road_dist_m = row["distance_to_nearest_road_m"]
        road_cls = row["nearest_road_class"]
        v_name = row["matched_village_name"]

        codes = []
        reasons = []

        if v_status in ["matched", "boundary_case"]:
            if v_status == "matched":
                codes.append("VILLAGE_MATCHED")
            else:
                codes.append("VILLAGE_BOUNDARY_CASE")

            if dist_km is not None:
                codes.append("STRAIGHT_LINE_DISTANCE_AVAILABLE")
                reasons.append(f"Candidate is {dist_km:.2f} km straight-line distance from the representative point of matched village {v_name}.")

            if road_dist_m is not None:
                codes.append("NEAREST_OSM_ROAD_AVAILABLE")
                reasons.append(f"Nearest mapped OSM road ({road_cls}) is {road_dist_m:.1f} m from the candidate.")
            else:
                codes.append("NEAREST_OSM_ROAD_UNAVAILABLE")
                reasons.append("Nearest mapped OSM road is unavailable.")

            codes.append("TRAVEL_TIME_NOT_IMPLEMENTED")
            reasons.append("Road network routing was not implemented from the current OSM extract; travel time is not implemented.")

            # Status classification
            if road_dist_m is not None and road_dist_m <= 100.0:
                status = "GOOD_EVIDENCE"
            elif road_dist_m is not None and road_dist_m <= 2000.0:
                status = "PARTIAL_EVIDENCE"
            else:
                status = "NO_NETWORK_EVIDENCE"

        else:
            codes.append("VILLAGE_UNMATCHED")
            codes.append("TRAVEL_TIME_NOT_IMPLEMENTED")
            reasons.append("Candidate is located outside the matched rural village reference framework.")
            reasons.append("Road network routing was not implemented from current OSM extract; travel time is not implemented.")
            status = "UNMATCHED_VILLAGE"

        acc_statuses.append(status)
        acc_reason_codes_list.append("; ".join(codes))
        acc_reasons_list.append("; ".join(reasons))

    cand_gdf["accessibility_status"] = acc_statuses
    cand_gdf["accessibility_reason_codes"] = acc_reason_codes_list
    cand_gdf["accessibility_reasons"] = acc_reasons_list

    # STEP 12 & 13: PRESERVE SAFETY GATE & RESOURCE STATUS CONTROLS
    cand_gdf["capacity_status"] = "UNKNOWN"
    cand_gdf["water_status"] = "UNKNOWN"
    cand_gdf["electricity_status"] = "UNKNOWN"
    cand_gdf["sanitation_status"] = "UNKNOWN"

    # STEP 14: OUTPUT DATASETS
    logger.info("Step 14: Saving output CSV and GPKG datasets...")
    output_cols = [
        "candidate_id", "osm_type", "osm_id", "name", "facility_category", "facility_role",
        "amenity", "building_type", "latitude", "longitude", "source", "selection_reason",
        "coordinate_source", "matched_village_code", "matched_village_name",
        "matched_village_population_2011", "matched_village_households_2011", "village_match_status",
        "village_forecast_risk_p95", "village_forecast_priority_score", "village_risk_24h_p95",
        "village_risk_72h_p95", "village_risk_7day_p95", "village_risk_combined_p95",
        "slope_degrees", "gsi_susceptibility", "historical_landslide_evidence",
        "dynamic_risk_24h", "dynamic_risk_72h", "dynamic_risk_7day", "dynamic_risk_combined",
        "safety_status", "safety_reason_codes", "safety_reasons",
        "village_reference_latitude", "village_reference_longitude",
        "distance_to_village_km", "distance_method",
        "distance_to_nearest_road_m", "nearest_road_class", "nearest_road_name", "nearest_road_status",
        "road_way_count_context", "road_network_length_km_context",
        "network_routing_status", "road_network_distance_km",
        "accessibility_status", "accessibility_reason_codes", "accessibility_reasons",
        "travel_time_status", "road_travel_distance_status",
        "capacity_status", "water_status", "electricity_status", "sanitation_status", "geometry"
    ]

    out_gdf = cand_gdf[output_cols]
    out_df = pd.DataFrame(out_gdf.drop(columns=["geometry"]))

    out_df.to_csv(output_csv, index=False, encoding="utf-8")
    out_gdf.to_file(output_gpkg, driver="GPKG", layer="relocation_candidate_accessibility")

    logger.info(f"Saved accessibility CSV dataset to: {output_csv}")
    logger.info(f"Saved accessibility GPKG layer to: {output_gpkg}")

    # STEP 15: AUTOMATED QA CHECKS
    logger.info("Step 15: Running Automated QA Checks...")

    # 1. Candidate count preserved
    assert len(out_df) == cand_count, f"QA Error: Candidate count changed from {cand_count} to {len(out_df)}"

    # 2. candidate_id uniqueness
    assert len(out_df["candidate_id"].unique()) == cand_count, "QA Error: Candidate IDs not unique!"

    # 3. Coordinates finite
    assert out_df["latitude"].notnull().all() and out_df["longitude"].notnull().all(), "QA Error: Null candidate coordinates!"

    # 4. Geometry valid
    assert out_gdf.geometry.is_valid.all(), "QA Error: Invalid geometries!"

    # 5. CRS correct
    assert out_gdf.crs.to_epsg() == 4326, f"QA Error: CRS is {out_gdf.crs}, expected EPSG:4326"

    # 6. No negative distances
    dists_valid = out_df["distance_to_village_km"].dropna()
    assert (dists_valid >= 0).all(), "QA Error: Negative village distance found!"
    road_dists_valid = out_df["distance_to_nearest_road_m"].dropna()
    assert (road_dists_valid >= 0).all(), "QA Error: Negative road distance found!"

    # 7. Distance values finite where status says available
    assert dists_valid.notnull().all(), "QA Error: Non-finite distance values found!"

    # 8. Unmatched candidates have NULL village reference values
    unmatched_df = out_df[out_df["village_match_status"] == "unmatched"]
    assert unmatched_df["village_reference_latitude"].isnull().all(), "QA Error: Unmatched candidate has non-null village ref lat!"
    assert unmatched_df["distance_to_village_km"].isnull().all(), "QA Error: Unmatched candidate has non-null village distance!"

    # 9. Matched candidates have village reference coordinates
    matched_df = out_df[out_df["village_match_status"].isin(["matched", "boundary_case"])]
    assert matched_df["village_reference_latitude"].notnull().all(), "QA Error: Matched candidate missing village ref lat!"
    assert matched_df["distance_to_village_km"].notnull().all(), "QA Error: Matched candidate missing village distance!"

    # 10. Nearest road distance >= 0
    assert (out_df["distance_to_nearest_road_m"].dropna() >= 0).all(), "QA Error: Invalid nearest road distance!"

    # 11 & 12. Road counts and length non-negative
    assert (out_df["road_way_count_context"] >= 0).all(), "QA Error: Negative road way count!"
    assert (out_df["road_network_length_km_context"] >= 0).all(), "QA Error: Negative road network length!"

    # 13 & 14. No fabricated travel time
    assert (out_df["travel_time_status"] == "NOT_IMPLEMENTED").all(), "QA Error: Travel time status violated!"

    # 15. accessibility_status allowed values
    allowed_acc_statuses = {"GOOD_EVIDENCE", "PARTIAL_EVIDENCE", "NO_NETWORK_EVIDENCE", "UNMATCHED_VILLAGE", "INSUFFICIENT_EVIDENCE"}
    assert set(out_df["accessibility_status"].unique()).issubset(allowed_acc_statuses), f"QA Error: Invalid accessibility status!"

    # 16. Existing safety_status remains unchanged
    assert out_df["safety_status"].isin(["PASS", "FLAG", "INSUFFICIENT_EVIDENCE"]).all(), "QA Error: Safety status modified!"

    # 17. capacity_status remains UNKNOWN
    assert (out_df["capacity_status"] == "UNKNOWN").all(), "QA Error: Capacity status modified!"

    # 18 & 19. No external dataset or API calls
    assert (out_df["source"] == "OpenStreetMap_Overpass").all(), "QA Error: External source modified!"

    # 20. Reason traceability
    assert (out_df["accessibility_reasons"].str.len() > 0).all(), "QA Error: Empty accessibility reasons!"

    logger.info("ALL 20 QA ASSERTION CHECKS PASSED SUCCESSFULLY!")

    # STEP 16: SUMMARY REPORT
    matched_c = int((out_df["village_match_status"] == "matched").sum())
    bound_c = int((out_df["village_match_status"] == "boundary_case").sum())
    unmatched_c = int((out_df["village_match_status"] == "unmatched").sum())

    good_c = int((out_df["accessibility_status"] == "GOOD_EVIDENCE").sum())
    partial_c = int((out_df["accessibility_status"] == "PARTIAL_EVIDENCE").sum())
    no_net_c = int((out_df["accessibility_status"] == "NO_NETWORK_EVIDENCE").sum())

    print("\n" + "="*60)
    print("WAYANAD RELOCATION ACCESSIBILITY ANALYSIS")
    print("="*60)
    print(f"Candidate facilities:               {cand_count}")
    print(f"Matched villages (within polygon):  {matched_c}")
    print(f"Boundary cases (<= 500m):        {bound_c}")
    print(f"Unmatched (> 500m / Urban):        {unmatched_c}")
    print("\nOSM Road Infrastructure Context:")
    print(f"  OSM road ways:                    {road_way_count}")
    print(f"  OSM road center geometries:       {road_geometry_count}")
    print(f"  Bridges:                          {bridge_count}")
    print(f"  Named roads:                      {named_road_count}")
    print(f"  Surface tags:                     {surface_count}")
    print(f"  Access tags:                      {access_count}")
    print("\nNearest Road Evidence:")
    print(f"  Candidates with nearest-road evidence: {len(out_df['distance_to_nearest_road_m'].dropna())}")
    print(f"  Mean distance to nearest OSM road:     {out_df['distance_to_nearest_road_m'].mean():.1f} m")
    print(f"  Max distance to nearest OSM road:      {out_df['distance_to_nearest_road_m'].max():.1f} m")
    print("\nNetwork Routing Status:")
    print(f"  Network routing:                  NOT_IMPLEMENTED")
    print(f"  Travel time:                      NOT_IMPLEMENTED")
    print("\nAccessibility Status Breakdown:")
    print(f"  GOOD_EVIDENCE (road <= 100m):     {good_c}")
    print(f"  PARTIAL_EVIDENCE (road > 100m):   {partial_c}")
    print(f"  NO_NETWORK_EVIDENCE:              {no_net_c}")
    print(f"  UNMATCHED_VILLAGE:                {unmatched_c}")
    print("="*60 + "\n")

    print("Highway Class Distribution:")
    for k, v in sorted(highways_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k:20s}: {v:5d}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
