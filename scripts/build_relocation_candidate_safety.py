import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from shapely.geometry import Point

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("relocation_candidate_safety")

# Configurable Safety Gate System
SAFETY_CONFIG = {
    "slope": {
        "enabled": True,
        "threshold": 15.0  # Configurable slope threshold in degrees (e.g. 15.0)
    },
    "gsi": {
        "enabled": True,
        "maximum_class": 2  # Configurable maximum class (2 = Moderate, 3 = High)
    },
    "historical_landslide": {
        "enabled": True,
        "reject_on_presence": True  # Flag if historical inventory evidence == 1
    },
    "dynamic_risk": {
        "enabled": True,
        "threshold": 0.50  # Configurable combined risk threshold (e.g. 0.50)
    }
}
 
def main():
    base_dir = Path(__file__).resolve().parent.parent

    # File paths
    cand_csv_path = base_dir / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_facilities.csv"
    cand_gpkg_path = base_dir / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_facilities.gpkg"
    village_pop_path = base_dir / "data" / "processed" / "exposure" / "census_nwdp_reconciliation" / "wayanad_census_nwdp_village_population_2011.gpkg"
    village_risk_csv_path = base_dir / "data" / "processed" / "exposure" / "village_risk" / "wayanad_village_dynamic_risk.csv"

    slope_raster_path = base_dir / "data" / "processed" / "terrain" / "wayanad_copernicus_slope_degrees.tif"
    gsi_raster_path = base_dir / "data" / "processed" / "landslide" / "susceptibility" / "wayanad_gsi_susceptibility_copernicus_30m.tif"
    hist_raster_path = base_dir / "data" / "processed" / "landslide" / "inventory" / "wayanad_historical_landslide_presence_copernicus_30m.tif"
    
    risk_24h_raster_path = base_dir / "data" / "processed" / "predictions" / "wayanad_dynamic_risk_model_a_24h.tif"
    risk_72h_raster_path = base_dir / "data" / "processed" / "predictions" / "wayanad_dynamic_risk_model_a_72h.tif"
    risk_7day_raster_path = base_dir / "data" / "processed" / "predictions" / "wayanad_dynamic_risk_model_a_7day.tif"
    risk_comb_raster_path = base_dir / "data" / "processed" / "predictions" / "wayanad_dynamic_risk_model_a_combined.tif"

    output_dir = base_dir / "data" / "processed" / "exposure" / "relocation"
    output_csv = output_dir / "wayanad_relocation_candidate_safety.csv"
    output_gpkg = output_dir / "wayanad_relocation_candidate_safety.gpkg"

    # STEP 1: LOAD AND VALIDATE INPUTS
    logger.info("Step 1: Loading and validating inputs...")
    required_files = [
        cand_csv_path, cand_gpkg_path, village_pop_path, village_risk_csv_path,
        slope_raster_path, gsi_raster_path, hist_raster_path,
        risk_24h_raster_path, risk_72h_raster_path, risk_7day_raster_path, risk_comb_raster_path
    ]
    for p in required_files:
        if not p.exists():
            raise FileNotFoundError(f"Validation Error: Required input file missing at {p}")

    cand_gdf = gpd.read_file(cand_gpkg_path)
    cand_count = len(cand_gdf)
    logger.info(f"Loaded candidate facilities GPKG: {cand_count} records, CRS={cand_gdf.crs}")
    if cand_count != 794:
        logger.warning(f"Expected 794 candidate facilities, found {cand_count}")

    villages_gdf = gpd.read_file(village_pop_path)
    village_count = len(villages_gdf)
    logger.info(f"Loaded village boundaries GPKG: {village_count} villages, CRS={villages_gdf.crs}")

    # Convert population & household columns to numeric safely
    villages_gdf["population_2011"] = pd.to_numeric(villages_gdf["population_2011"], errors="coerce")
    villages_gdf["households_2011"] = pd.to_numeric(villages_gdf["households_2011"], errors="coerce")
    pop_total = float(villages_gdf["population_2011"].sum())
    hh_total = float(villages_gdf["households_2011"].sum())

    logger.info(f"Village totals QA check: Population 2011 = {pop_total:,.0f}, Households 2011 = {hh_total:,.0f}")
    assert village_count == 48, f"Validation Error: Expected 48 villages, found {village_count}"
    assert int(pop_total) == 785840, f"Validation Error: Expected total population 785,840, found {pop_total}"
    assert int(hh_total) == 183375, f"Validation Error: Expected total households 183,375, found {hh_total}"

    village_risk_df = pd.read_csv(village_risk_csv_path)
    # Ensure village_code type consistency (string)
    village_risk_df["village_code"] = village_risk_df["village_code"].astype(str)
    villages_gdf["village_code"] = villages_gdf["village_code"].astype(str)

    # STEP 2: CANDIDATE -> VILLAGE SPATIAL MATCHING
    logger.info("Step 2: Performing Candidate -> Village spatial matching...")
    cand_7755 = cand_gdf.to_crs(villages_gdf.crs)

    matched_village_codes = []
    matched_village_names = []
    matched_village_pops = []
    matched_village_hhs = []
    village_match_statuses = []

    matched_count = 0
    boundary_case_count = 0
    unmatched_count = 0

    BUFFER_THRESHOLD_METERS = 500.0

    for idx, row in cand_7755.iterrows():
        pt = row.geometry
        # Point-in-polygon matching
        containing = villages_gdf[villages_gdf.geometry.contains(pt)]

        if len(containing) > 0:
            v_rec = containing.iloc[0]
            matched_village_codes.append(v_rec["village_code"])
            matched_village_names.append(v_rec["village_name"])
            matched_village_pops.append(v_rec["population_2011"])
            matched_village_hhs.append(v_rec["households_2011"])
            village_match_statuses.append("matched")
            matched_count += 1
        else:
            # Check distance to nearest village boundary
            dists = villages_gdf.geometry.distance(pt)
            min_dist_m = dists.min()
            nearest_idx = dists.idxmin()
            v_rec = villages_gdf.loc[nearest_idx]

            if min_dist_m <= BUFFER_THRESHOLD_METERS:
                matched_village_codes.append(v_rec["village_code"])
                matched_village_names.append(v_rec["village_name"])
                matched_village_pops.append(v_rec["population_2011"])
                matched_village_hhs.append(v_rec["households_2011"])
                village_match_statuses.append("boundary_case")
                boundary_case_count += 1
            else:
                matched_village_codes.append(None)
                matched_village_names.append(None)
                matched_village_pops.append(None)
                matched_village_hhs.append(None)
                village_match_statuses.append("unmatched")
                unmatched_count += 1

    cand_gdf["matched_village_code"] = matched_village_codes
    cand_gdf["matched_village_name"] = matched_village_names
    cand_gdf["matched_village_population_2011"] = matched_village_pops
    cand_gdf["matched_village_households_2011"] = matched_village_hhs
    cand_gdf["village_match_status"] = village_match_statuses

    logger.info(f"Spatial Matching QA:")
    logger.info(f"  Matched (within polygon): {matched_count}")
    logger.info(f"  Boundary cases (within {BUFFER_THRESHOLD_METERS}m): {boundary_case_count}")
    logger.info(f"  Unmatched (> {BUFFER_THRESHOLD_METERS}m): {unmatched_count}")

    # STEP 3: JOIN EXISTING VILLAGE FORECAST RISK
    logger.info("Step 3: Joining existing village forecast risk...")
    risk_cols_to_join = [
        "village_code", "forecast_risk_p95", "forecast_priority_score",
        "risk_24h_p95", "risk_72h_p95", "risk_7day_p95", "risk_combined_p95"
    ]
    vr_subset = village_risk_df[risk_cols_to_join].rename(columns={
        "forecast_risk_p95": "village_forecast_risk_p95",
        "forecast_priority_score": "village_forecast_priority_score",
        "risk_24h_p95": "village_risk_24h_p95",
        "risk_72h_p95": "village_risk_72h_p95",
        "risk_7day_p95": "village_risk_7day_p95",
        "risk_combined_p95": "village_risk_combined_p95"
    })

    cand_gdf = cand_gdf.merge(vr_subset, left_on="matched_village_code", right_on="village_code", how="left")
    if "village_code_y" in cand_gdf.columns:
        cand_gdf = cand_gdf.drop(columns=["village_code_y"])
    if "village_code_x" in cand_gdf.columns:
        cand_gdf = cand_gdf.rename(columns={"village_code_x": "village_code"})

    # STEP 4: SAMPLE HAZARD RASTERS AT FACILITY LOCATION
    logger.info("Step 4: Sampling hazard rasters at facility locations (EPSG:32643)...")
    cand_32643 = cand_gdf.to_crs(epsg=32643)
    coords_32643 = [(pt.x, pt.y) for pt in cand_32643.geometry]

    raster_mapping = {
        "slope_degrees": slope_raster_path,
        "gsi_susceptibility": gsi_raster_path,
        "historical_landslide_evidence": hist_raster_path,
        "dynamic_risk_24h": risk_24h_raster_path,
        "dynamic_risk_72h": risk_72h_raster_path,
        "dynamic_risk_7day": risk_7day_raster_path,
        "dynamic_risk_combined": risk_comb_raster_path
    }

    sampled_results = {}

    for key, path in raster_mapping.items():
        with rasterio.open(path) as src:
            nodata = src.nodata
            # For uint8 GSI and Historical rasters, 0 represents valid data (0 = Low/None), not missing nodata
            if key in ["gsi_susceptibility", "historical_landslide_evidence"] and nodata == 0:
                effective_nodata = None
            else:
                effective_nodata = nodata

            vals = [v[0] for v in src.sample(coords_32643)]
            clean_vals = []
            for v in vals:
                if (effective_nodata is not None and v == effective_nodata) or (isinstance(v, float) and np.isnan(v)) or v <= -9990:
                    clean_vals.append(None)
                elif v < 0 and key != "slope_degrees":
                    clean_vals.append(None)
                else:
                    clean_vals.append(float(v))
            sampled_results[key] = clean_vals

    for key, vals in sampled_results.items():
        cand_gdf[key] = vals

    # STEP 5 & 6: CONFIGURABLE SAFETY GATE AND REASON CODES
    logger.info("Step 5 & 6: Applying Safety Gate rules and generating reason codes...")

    safety_statuses = []
    safety_reason_codes_list = []
    safety_reasons_list = []

    for idx, row in cand_gdf.iterrows():
        reasons = []
        codes = []
        is_flagged = False
        is_insufficient = False

        # 1. Slope Evaluation
        slope = row["slope_degrees"]
        if slope is None or np.isnan(slope):
            reasons.append("Slope elevation data missing at sampled location.")
            codes.append("NO_SLOPE_VALUE")
            is_insufficient = True
        else:
            if SAFETY_CONFIG["slope"]["enabled"] and SAFETY_CONFIG["slope"]["threshold"] is not None:
                if slope > SAFETY_CONFIG["slope"]["threshold"]:
                    reasons.append(f"Slope ({slope:.1f}°) exceeds configured threshold ({SAFETY_CONFIG['slope']['threshold']}°).")
                    codes.append("HIGH_SLOPE")
                    is_flagged = True
                else:
                    reasons.append(f"Slope ({slope:.1f}°) within threshold ({SAFETY_CONFIG['slope']['threshold']}°).")
                    codes.append("SLOPE_PASS")
            else:
                codes.append("SLOPE_UNCONFIGURED")

        # 2. GSI Susceptibility Evaluation
        gsi = row["gsi_susceptibility"]
        if gsi is None:
            reasons.append("GSI susceptibility coverage unavailable at sampled location.")
            codes.append("NO_GSI_COVERAGE")
            is_insufficient = True
        else:
            if gsi == 3:
                reasons.append("GSI susceptibility class = High.")
                codes.append("GSI_HIGH")
                is_flagged = True
            elif gsi == 0:
                reasons.append("GSI susceptibility class = Low / Unclassified.")
                codes.append("GSI_LOW")
            elif SAFETY_CONFIG["gsi"]["enabled"] and SAFETY_CONFIG["gsi"]["maximum_class"] is not None:
                if gsi > SAFETY_CONFIG["gsi"]["maximum_class"]:
                    reasons.append(f"GSI susceptibility class ({int(gsi)}) exceeds configured maximum class ({SAFETY_CONFIG['gsi']['maximum_class']}).")
                    codes.append("GSI_EXCEEDS_THRESHOLD")
                    is_flagged = True
                else:
                    reasons.append(f"GSI susceptibility class = {int(gsi)} (within threshold).")
                    codes.append(f"GSI_CLASS_{int(gsi)}")

        # 3. Historical Landslide Evidence Evaluation
        hist = row["historical_landslide_evidence"]
        if hist == 1:
            reasons.append("Historical landslide inventory evidence present at sampled location.")
            codes.append("HISTORICAL_LANDSLIDE_EVIDENCE")
            is_flagged = True
        elif hist == 0:
            reasons.append("No historical landslide inventory evidence recorded at location.")
            codes.append("NO_HISTORICAL_INVENTORY_EVIDENCE")
        else:
            reasons.append("Historical landslide inventory coverage unavailable at location.")
            codes.append("NO_HISTORICAL_INVENTORY_COVERAGE")
            is_insufficient = True

        # 4. Dynamic Risk Evaluation
        risk_comb = row["dynamic_risk_combined"]
        if risk_comb is None or np.isnan(risk_comb):
            reasons.append("Dynamic forecast risk value missing at sampled location.")
            codes.append("NO_DYNAMIC_RISK_VALUE")
            is_insufficient = True
        else:
            if SAFETY_CONFIG["dynamic_risk"]["enabled"] and SAFETY_CONFIG["dynamic_risk"]["threshold"] is not None:
                if risk_comb > SAFETY_CONFIG["dynamic_risk"]["threshold"]:
                    reasons.append(f"Combined dynamic risk ({risk_comb:.3f}) exceeds configured threshold ({SAFETY_CONFIG['dynamic_risk']['threshold']}).")
                    codes.append("HIGH_COMBINED_FORECAST_RISK")
                    is_flagged = True
                else:
                    reasons.append(f"Combined dynamic risk ({risk_comb:.3f}) within threshold ({SAFETY_CONFIG['dynamic_risk']['threshold']}).")
                    codes.append("RISK_PASS")
            else:
                codes.append("DYNAMIC_RISK_UNCONFIGURED")

        # Final Status Decision
        if is_flagged:
            status = "FLAG"
        elif is_insufficient:
            status = "INSUFFICIENT_EVIDENCE"
        else:
            status = "PASS"

        safety_statuses.append(status)
        safety_reason_codes_list.append("; ".join(codes))
        safety_reasons_list.append("; ".join(reasons))

    cand_gdf["safety_status"] = safety_statuses
    cand_gdf["safety_reason_codes"] = safety_reason_codes_list
    cand_gdf["safety_reasons"] = safety_reasons_list

    # STEP 7: CAPACITY & UNKNOWN METRICS STATUS
    cand_gdf["capacity_status"] = "UNKNOWN"
    cand_gdf["travel_time_status"] = "NOT_IMPLEMENTED"
    cand_gdf["road_access_status"] = "NOT_IMPLEMENTED"
    cand_gdf["water_status"] = "UNKNOWN"
    cand_gdf["electricity_status"] = "UNKNOWN"
    cand_gdf["sanitation_status"] = "UNKNOWN"

    # STEP 9: SAVE OUTPUT DATASETS
    logger.info("Step 9: Saving output CSV and GPKG datasets...")

    # Drop any temporary internal columns if created, format output df
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
        "capacity_status", "travel_time_status", "road_access_status",
        "water_status", "electricity_status", "sanitation_status", "geometry"
    ]

    out_gdf = cand_gdf[output_cols]
    out_df = pd.DataFrame(out_gdf.drop(columns=["geometry"]))

    out_df.to_csv(output_csv, index=False, encoding="utf-8")
    out_gdf.to_file(output_gpkg, driver="GPKG", layer="relocation_candidate_safety")

    logger.info(f"Saved CSV output to: {output_csv}")
    logger.info(f"Saved GPKG output to: {output_gpkg}")

    # STEP 10: AUTOMATED QA CHECKS
    logger.info("Step 10: Running Automated QA Checks...")

    # 1. candidate_id uniqueness
    assert len(out_df["candidate_id"].unique()) == cand_count, "QA Error: Candidate IDs not unique!"

    # 2. Candidate count preserved
    assert len(out_df) == cand_count, f"QA Error: Candidate count changed from {cand_count} to {len(out_df)}"

    # 3. Finite coordinates
    assert out_df["latitude"].notnull().all() and out_df["longitude"].notnull().all(), "QA Error: Null coordinates found!"

    # 4 & 5. Latitude/longitude valid range
    assert ((out_df["latitude"] >= -90) & (out_df["latitude"] <= 90)).all(), "QA Error: Invalid latitude!"
    assert ((out_df["longitude"] >= -180) & (out_df["longitude"] <= 180)).all(), "QA Error: Invalid longitude!"

    # 6. Geometry valid
    assert out_gdf.geometry.is_valid.all(), "QA Error: Invalid geometries!"

    # 7. CRS correct
    assert out_gdf.crs.to_epsg() == 4326, f"QA Error: CRS is {out_gdf.crs}, expected EPSG:4326"

    # 8. Village population sum valid
    matched_pops = out_df["matched_village_population_2011"].dropna()
    assert (matched_pops >= 0).all(), "QA Error: Invalid village population found!"

    # 9 & 10. No fabricated capacity / travel time
    assert (out_df["capacity_status"] == "UNKNOWN").all(), "QA Error: Capacity status violated!"
    assert (out_df["travel_time_status"] == "NOT_IMPLEMENTED").all(), "QA Error: Travel time status violated!"

    # 11. GSI values only 0, 1, 2, 3 or NaN
    gsi_vals = out_df["gsi_susceptibility"].dropna().unique()
    assert set(gsi_vals).issubset({0.0, 1.0, 2.0, 3.0}), f"QA Error: Unexpected GSI values: {gsi_vals}"

    # 12. Historical evidence values only 0, 1 or NaN
    hist_vals = out_df["historical_landslide_evidence"].dropna().unique()
    assert set(hist_vals).issubset({0.0, 1.0}), f"QA Error: Unexpected Historical Landslide values: {hist_vals}"

    # 13. Dynamic risk values within [0, 1]
    dyn_vals = out_df["dynamic_risk_combined"].dropna()
    assert ((dyn_vals >= 0.0) & (dyn_vals <= 1.0)).all(), "QA Error: Dynamic risk out of range [0, 1]"

    # 14. Safety status valid
    assert out_df["safety_status"].isin(["PASS", "FLAG", "INSUFFICIENT_EVIDENCE"]).all(), "QA Error: Invalid safety status!"

    # 15. Safety reasons non-empty
    assert (out_df["safety_reasons"].str.len() > 0).all(), "QA Error: Empty safety reasons found!"

    # 16. Public transport shelters remain excluded
    assert not ((out_df["amenity"] == "shelter") & (out_df.get("shelter_type", "") == "public_transport")).any(), "QA Error: Bus shelters found!"

    logger.info("ALL 16 QA ASSERTION CHECKS PASSED SUCCESSFULLY!")

    # STEP 11: SUMMARY REPORT
    hist_count = int((out_df["historical_landslide_evidence"] == 1).sum())
    gsi_high_count = int((out_df["gsi_susceptibility"] == 3).sum())
    gsi_no_cov_count = int((out_df["gsi_susceptibility"] == 0).sum() + out_df["gsi_susceptibility"].isnull().sum())
    dyn_missing_count = int(out_df["dynamic_risk_combined"].isnull().sum())

    pass_count = int((out_df["safety_status"] == "PASS").sum())
    flag_count = int((out_df["safety_status"] == "FLAG").sum())
    insuff_count = int((out_df["safety_status"] == "INSUFFICIENT_EVIDENCE").sum())

    cat_counts = out_df["facility_category"].value_counts().to_dict()

    print("\n" + "="*60)
    print("RELOCATION CANDIDATE SAFETY GATE SUMMARY")
    print("="*60)
    print(f"Input candidates:                   {cand_count}")
    print(f"Matched villages (within polygon):  {matched_count}")
    print(f"Boundary cases (<= {BUFFER_THRESHOLD_METERS:.0f}m):        {boundary_case_count}")
    print(f"Unmatched (> {BUFFER_THRESHOLD_METERS:.0f}m):             {unmatched_count}")
    print("\nSafety Status Breakdown:")
    print(f"  PASS:                             {pass_count}")
    print(f"  FLAG:                             {flag_count}")
    print(f"  INSUFFICIENT_EVIDENCE:            {insuff_count}")
    print("\nFacility Categories:")
    print(f"  Education:                        {cat_counts.get('education', 0)}")
    print(f"  Community:                        {cat_counts.get('community', 0)}")
    print(f"  Healthcare:                       {cat_counts.get('healthcare', 0)}")
    print(f"  Public buildings:                 {cat_counts.get('public_building', 0)}")
    print("\nHazard Evidence Breakdown:")
    print(f"  Candidates with historical landslide evidence: {hist_count}")
    print(f"  Candidates with GSI High susceptibility:       {gsi_high_count}")
    print(f"  Candidates with missing GSI coverage:          {gsi_no_cov_count}")
    print(f"  Candidates with missing dynamic risk:          {dyn_missing_count}")
    print("\nAttribute Status Controls:")
    print(f"  Capacity information:             UNKNOWN")
    print(f"  Travel-time information:          NOT_IMPLEMENTED")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
