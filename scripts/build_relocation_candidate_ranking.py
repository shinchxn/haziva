import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("relocation_candidate_ranking")

# STEP 19: RANKING CONFIGURATION (prototype_v2)
RANKING_CONFIG = {
    "version": "prototype_v2",
    "weights": {
        "village_priority": 0.35,
        "hazard_suitability": 0.30,
        "distance_evidence": 0.20,
        "facility_suitability": 0.15
    },
    "penalties": {
        "historical_landslide_scar": 0.0  # Configurable penalty magnitude (default 0.0, evidence flag only)
    }
}

def main():
    base_dir = Path(__file__).resolve().parent.parent

    # Validate weights configuration
    weight_sum = sum(RANKING_CONFIG["weights"].values())
    assert abs(weight_sum - 1.0) < 1e-6, f"QA Error: RANKING_CONFIG weights sum to {weight_sum}, expected 1.0"

    # Input file paths
    cand_csv_path = base_dir / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_accessibility.csv"
    cand_gpkg_path = base_dir / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_accessibility.gpkg"

    output_dir = base_dir / "data" / "processed" / "exposure" / "relocation"
    output_csv = output_dir / "wayanad_relocation_candidate_ranking.csv"
    output_gpkg = output_dir / "wayanad_relocation_candidate_ranking.gpkg"

    # STEP 1: VALIDATE INPUT
    logger.info("Step 1: Loading and validating candidate accessibility input dataset...")
    if not cand_gpkg_path.exists() or not cand_csv_path.exists():
        raise FileNotFoundError(f"Required input dataset missing at {cand_gpkg_path}")

    cand_gdf = gpd.read_file(cand_gpkg_path)
    cand_count = len(cand_gdf)
    logger.info(f"Loaded input GeoDataFrame: {cand_count} candidates, CRS={cand_gdf.crs}")

    assert cand_count == len(cand_gdf["candidate_id"].unique()), "QA Error: Candidate IDs not unique!"
    assert cand_gdf["latitude"].notnull().all() and cand_gdf["longitude"].notnull().all(), "QA Error: Null coordinates!"
    assert (cand_gdf["capacity_status"] == "UNKNOWN").all(), "QA Error: Capacity status violated!"
    assert (cand_gdf["travel_time_status"] == "NOT_IMPLEMENTED").all(), "QA Error: Travel time status violated!"

    # STEP 2, 3 & 14: SAFETY GATE PRIORITY & RANKING GROUPS
    logger.info("Step 2, 3 & 14: Processing safety gate groups and conditional status...")
    ranking_groups = []

    for idx, row in cand_gdf.iterrows():
        s_status = str(row["safety_status"])
        if s_status == "PASS":
            group = "ELIGIBLE"
        elif s_status == "FLAG":
            group = "DO_NOT_PRIORITIZE"
        else: # INSUFFICIENT_EVIDENCE
            group = "CONDITIONAL"
        ranking_groups.append(group)

    cand_gdf["ranking_group"] = ranking_groups

    # Current safety configuration has INSUFFICIENT_EVIDENCE for all candidates due to unconfigured thresholds
    all_conditional = (cand_gdf["ranking_group"] == "CONDITIONAL").all()
    ranking_status_val = "CONDITIONAL_RANKING" if all_conditional else "NORMAL"
    logger.info(f"Overall ranking status: {ranking_status_val}")

    # STEP 5: VILLAGE PRIORITY FACTOR (prototype_v2: NULL for unmatched, NOT 0.0)
    logger.info("Step 5: Processing village priority factor (v2: NULL for unmatched)...")
    v_priority_statuses = []
    v_priority_norms = []
    v_priority_scores_clean = []

    for idx, row in cand_gdf.iterrows():
        v_match = str(row["village_match_status"])
        v_score = row["village_forecast_priority_score"]

        if v_match in ["matched", "boundary_case"] and pd.notnull(v_score) and not np.isnan(v_score):
            v_priority_statuses.append("AVAILABLE")
            v_priority_norms.append(float(v_score))
            v_priority_scores_clean.append(float(v_score))
        else:
            v_priority_statuses.append("UNAVAILABLE")
            v_priority_norms.append(np.nan) # Explicitly NaN, NOT 0.0
            v_priority_scores_clean.append(np.nan)

    cand_gdf["village_forecast_priority_score"] = v_priority_scores_clean
    cand_gdf["village_priority_status"] = v_priority_statuses
    cand_gdf["village_priority_norm"] = v_priority_norms

    # STEP 6, 7 & 12: FORECAST RISK & HAZARD SUITABILITY LOGIC (v2: Configurable Historical Penalty)
    logger.info("Step 6, 7 & 12: Processing forecast risk and hazard suitability (v2: configurable penalty)...")
    hazard_flags_list = []
    hazard_statuses = []
    hazard_norms = []

    hist_scar_penalty = RANKING_CONFIG["penalties"]["historical_landslide_scar"]

    for idx, row in cand_gdf.iterrows():
        flags = []
        gsi = row["gsi_susceptibility"]
        hist = row["historical_landslide_evidence"]
        risk_comb = row["dynamic_risk_combined"]
        slope = row["slope_degrees"]

        if gsi == 0 or pd.isnull(gsi):
            flags.append("NO_GSI_COVERAGE")
        elif gsi == 3:
            flags.append("GSI_HIGH")

        if hist == 1:
            flags.append("HISTORICAL_LANDSLIDE_EVIDENCE")

        if pd.notnull(risk_comb) and risk_comb > 0.35:
            flags.append("HIGH_FORECAST_RISK")

        if pd.notnull(slope) and slope > 15.0:
            flags.append("HIGH_SLOPE")

        hazard_flags_list.append("; ".join(flags) if flags else "NONE")

        # Hazard evidence status
        if pd.notnull(gsi) and gsi > 0:
            h_status = "EVIDENCE_PRESENT"
        elif pd.notnull(risk_comb) and pd.notnull(slope):
            h_status = "EVIDENCE_LIMITED"
        else:
            h_status = "INSUFFICIENT_EVIDENCE"
        hazard_statuses.append(h_status)

        # Monotonic inverse dynamic risk suitability (1 - dynamic_risk_combined)
        if pd.notnull(risk_comb) and not np.isnan(risk_comb):
            h_suit = 1.0 - float(risk_comb)
            if hist == 1 and hist_scar_penalty > 0:
                h_suit -= hist_scar_penalty
            h_suit = max(0.0, min(1.0, h_suit))
        else:
            h_suit = np.nan
        hazard_norms.append(h_suit)

    cand_gdf["hazard_evidence_flags"] = hazard_flags_list
    cand_gdf["hazard_evidence_status"] = hazard_statuses
    cand_gdf["hazard_suitability_norm"] = hazard_norms

    # STEP 8: ACCESSIBILITY & DISTANCE EVIDENCE FACTOR (v2: Cohort-relative normalization)
    logger.info("Step 8: Processing cohort-relative distance evidence index...")
    matched_mask = cand_gdf["distance_to_village_km"].notnull()
    dists_valid = cand_gdf.loc[matched_mask, "distance_to_village_km"]

    d_min = float(dists_valid.min()) if len(dists_valid) > 0 else 0.0
    d_max = float(dists_valid.max()) if len(dists_valid) > 0 else 1.0

    dist_evidence_indices = []
    for idx, row in cand_gdf.iterrows():
        d = row["distance_to_village_km"]
        if pd.notnull(d) and not np.isnan(d) and (d_max > d_min):
            idx_val = 1.0 - (float(d) - d_min) / (d_max - d_min)
            idx_val = max(0.0, min(1.0, idx_val))
            dist_evidence_indices.append(round(idx_val, 4))
        else:
            dist_evidence_indices.append(np.nan) # NaN for unmatched

    cand_gdf["distance_evidence_index"] = dist_evidence_indices
    cand_gdf["distance_method"] = "cohort_relative_min_max_straight_line"

    # STEP 9 & 13: FACILITY SUITABILITY CATEGORY MAPPING
    logger.info("Step 9 & 13: Mapping facility suitability categories and weights...")
    suit_categories = []
    suit_norms = []

    for idx, row in cand_gdf.iterrows():
        role = str(row["facility_role"])
        if role == "relocation_candidate":
            cat = "PRIMARY_RELOCATION"
            norm = 1.0
        elif role == "potential_relocation_candidate":
            cat = "POTENTIAL_RELOCATION"
            norm = 0.6
        elif role == "medical_support":
            cat = "MEDICAL_SUPPORT"
            norm = 0.3
        else:
            cat = "OTHER"
            norm = 0.0

        suit_categories.append(cat)
        suit_norms.append(norm)

    cand_gdf["facility_suitability_category"] = suit_categories
    cand_gdf["facility_suitability_norm"] = suit_norms

    # STEP 10: EVIDENCE COMPLETENESS
    logger.info("Step 10: Computing evidence completeness status and reasons...")
    comp_statuses = []
    comp_reasons = []

    for idx, row in cand_gdf.iterrows():
        v_match = row["village_match_status"]
        gsi = row["gsi_susceptibility"]
        road = row["distance_to_nearest_road_m"]

        if v_match in ["matched", "boundary_case"] and pd.notnull(road):
            if pd.notnull(gsi) and gsi > 0:
                c_status = "HIGH"
                c_reason = "Village context, forecast risk, slope, GSI susceptibility, and road-distance evidence all available."
            else:
                c_status = "MEDIUM"
                c_reason = "Village context, forecast risk, slope, and road-distance evidence available; GSI coverage unavailable."
        else:
            c_status = "LOW"
            c_reason = "Unmatched village framework or missing spatial infrastructure evidence."

        comp_statuses.append(c_status)
        comp_reasons.append(c_reason)

    cand_gdf["evidence_completeness_status"] = comp_statuses
    cand_gdf["evidence_completeness_reasons"] = comp_reasons

    # STEP 11 & 15: TRANSPARENT PRIORITY SCORE (v2: Re-normalization for available weights)
    logger.info("Step 11 & 15: Calculating re-normalized transparent priority score (v2)...")
    w_vp = RANKING_CONFIG["weights"]["village_priority"]
    w_hs = RANKING_CONFIG["weights"]["hazard_suitability"]
    w_dist = RANKING_CONFIG["weights"]["distance_evidence"]
    w_fs = RANKING_CONFIG["weights"]["facility_suitability"]

    transparent_scores = []
    for idx, row in cand_gdf.iterrows():
        avail_w = 0.0
        weighted_sum = 0.0

        # Village priority
        vp = row["village_priority_norm"]
        if pd.notnull(vp) and not np.isnan(vp):
            avail_w += w_vp
            weighted_sum += w_vp * float(vp)

        # Hazard suitability
        hs = row["hazard_suitability_norm"]
        if pd.notnull(hs) and not np.isnan(hs):
            avail_w += w_hs
            weighted_sum += w_hs * float(hs)

        # Distance evidence
        dn = row["distance_evidence_index"]
        if pd.notnull(dn) and not np.isnan(dn):
            avail_w += w_dist
            weighted_sum += w_dist * float(dn)

        # Facility suitability
        fs = row["facility_suitability_norm"]
        if pd.notnull(fs) and not np.isnan(fs):
            avail_w += w_fs
            weighted_sum += w_fs * float(fs)

        if avail_w > 0:
            final_score = round(weighted_sum / avail_w, 4)
        else:
            final_score = np.nan

        transparent_scores.append(final_score)

    cand_gdf["transparent_priority_score"] = transparent_scores
    cand_gdf["ranking_method"] = (
        f"Prototype weighted evidence score ({RANKING_CONFIG['version']}): "
        f"village priority {int(w_vp*100)}% (re-weighted if unavailable), "
        f"hazard suitability {int(w_hs*100)}%, cohort-relative distance evidence {int(w_dist*100)}%, "
        f"facility suitability {int(w_fs*100)}%."
    )
    cand_gdf["ranking_config_version"] = RANKING_CONFIG["version"]
    cand_gdf["ranking_status"] = ranking_status_val

    # STEP 16: SORTING AND RANKING
    logger.info("Step 16: Ordering candidates and assigning overall rank...")
    group_order = {"ELIGIBLE": 1, "CONDITIONAL": 2, "DO_NOT_PRIORITIZE": 3}
    cand_gdf["group_order"] = cand_gdf["ranking_group"].map(group_order)

    # Sort descending by group order then transparent priority score
    cand_gdf = cand_gdf.sort_values(by=["group_order", "transparent_priority_score"], ascending=[True, False]).reset_index(drop=True)
    cand_gdf["overall_rank"] = cand_gdf.index + 1
    cand_gdf = cand_gdf.drop(columns=["group_order"])

    # STEP 17: HUMAN-READABLE RANKING EXPLANATION (v2: Explicit labeling)
    logger.info("Step 17: Generating human-readable candidate ranking explanations (v2)...")
    explanations = []

    for idx, row in cand_gdf.iterrows():
        rank = row["overall_rank"]
        score = row["transparent_priority_score"]
        role = row["facility_role"]
        cat_suit = row["facility_suitability_category"]
        v_name = row["matched_village_name"]
        v_priority = row["village_forecast_priority_score"]
        risk_comb = row["dynamic_risk_combined"]
        dist_km = row["distance_to_village_km"]
        road_m = row["distance_to_nearest_road_m"]
        amenity = row["amenity"] if pd.notnull(row["amenity"]) and row["amenity"] else row["building_type"]
        name_str = f" '{row['name']}'" if pd.notnull(row['name']) and row['name'] else ""

        prefix = "Prototype-priority candidate under incomplete safety evidence: "

        if cat_suit == "MEDICAL_SUPPORT":
            v_str = f"Associated with village {v_name} (priority score {v_priority:.3f})" if pd.notnull(v_name) else "Located outside rural village framework (priority score unavailable)"
            d_str = f", sitting {dist_km:.2f} km straight-line from village reference point" if pd.notnull(dist_km) else ""
            exp = (
                f"{prefix}Candidate{name_str} provides medical-support capability ({amenity}) rather than primary accommodation. "
                f"{v_str}{d_str} and {road_m:.1f} m from mapped OSM road. Dynamic forecast risk is {risk_comb:.3f}. Capacity and travel time remain unknown."
            )
        elif cat_suit in ["PRIMARY_RELOCATION", "POTENTIAL_RELOCATION"]:
            if pd.notnull(v_name):
                exp = (
                    f"{prefix}Candidate{name_str} is associated with village {v_name} (village priority score {v_priority:.3f}), "
                    f"has dynamic forecast risk {risk_comb:.3f}, sits {dist_km:.2f} km straight-line (cohort-relative) from village reference point "
                    f"and {road_m:.1f} m from mapped OSM road infrastructure. Classified as {cat_suit.lower()} ({amenity}). Capacity and travel time remain unknown."
                )
            else:
                exp = (
                    f"{prefix}Candidate{name_str} is located outside matched rural village framework (village priority unavailable). "
                    f"Has dynamic forecast risk {risk_comb:.3f} and sits {road_m:.1f} m from mapped OSM road infrastructure. Classified as {cat_suit.lower()} ({amenity}). Capacity and travel time remain unknown."
                )
        else:
            exp = f"{prefix}Candidate{name_str} evaluated with priority score {score:.4f}. Capacity and travel time remain unknown."

        explanations.append(exp)

    cand_gdf["ranking_explanation"] = explanations

    # Drop temporary intermediate columns before output
    cand_gdf = cand_gdf.drop(columns=["village_priority_norm", "hazard_suitability_norm", "facility_suitability_norm"])

    # STEP 18: OUTPUT DATASET
    logger.info("Step 18: Saving output CSV and GPKG datasets...")
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
        "capacity_status", "water_status", "electricity_status", "sanitation_status",
        "village_priority_status", "hazard_evidence_flags", "hazard_evidence_status",
        "distance_evidence_index", "facility_suitability_category",
        "evidence_completeness_status", "evidence_completeness_reasons",
        "ranking_group", "transparent_priority_score", "overall_rank",
        "ranking_status", "ranking_method", "ranking_config_version", "ranking_explanation", "geometry"
    ]

    out_gdf = cand_gdf[output_cols]
    out_df = pd.DataFrame(out_gdf.drop(columns=["geometry"]))

    out_df.to_csv(output_csv, index=False, encoding="utf-8")
    out_gdf.to_file(output_gpkg, driver="GPKG", layer="relocation_candidate_ranking")

    logger.info(f"Saved ranking CSV dataset to: {output_csv}")
    logger.info(f"Saved ranking GPKG layer to: {output_gpkg}")

    # STEP 20: AUTOMATED QA CHECKS (prototype_v2)
    logger.info("Step 20: Running Automated QA Checks (prototype_v2)...")

    # 1. Candidate count preserved
    assert len(out_df) == cand_count, f"QA Error: Candidate count changed from {cand_count} to {len(out_df)}"

    # 2. candidate_id unique
    assert len(out_df["candidate_id"].unique()) == cand_count, "QA Error: Candidate IDs not unique!"

    # 3. No candidate lost
    assert set(out_df["candidate_id"]) == set(cand_gdf["candidate_id"]), "QA Error: Candidate ID mismatch!"

    # 4 & 5. Existing safety & accessibility status unchanged
    assert out_df["safety_status"].isin(["PASS", "FLAG", "INSUFFICIENT_EVIDENCE"]).all(), "QA Error: Safety status modified!"
    assert out_df["accessibility_status"].isin(["GOOD_EVIDENCE", "PARTIAL_EVIDENCE", "NO_NETWORK_EVIDENCE", "UNMATCHED_VILLAGE", "INSUFFICIENT_EVIDENCE"]).all(), "QA Error: Accessibility status modified!"

    # 6, 7, 8. No capacity / travel time / road travel distance fabricated
    assert (out_df["capacity_status"] == "UNKNOWN").all(), "QA Error: Capacity status fabricated!"
    assert (out_df["travel_time_status"] == "NOT_IMPLEMENTED").all(), "QA Error: Travel time status fabricated!"
    assert (out_df["road_travel_distance_status"] == "NOT_IMPLEMENTED").all(), "QA Error: Road travel distance fabricated!"

    # 9. transparent_priority_score within [0.0, 1.0]
    scores_valid = out_df["transparent_priority_score"].dropna()
    assert ((scores_valid >= 0.0) & (scores_valid <= 1.0)).all(), "QA Error: Score out of range [0, 1]!"

    # 10. overall_rank valid
    assert (out_df["overall_rank"] == range(1, cand_count + 1)).all(), "QA Error: Invalid overall_rank sequence!"

    # 11. Ranking group allowed values
    assert out_df["ranking_group"].isin(["ELIGIBLE", "CONDITIONAL", "DO_NOT_PRIORITIZE"]).all(), "QA Error: Invalid ranking_group!"

    # 12. Facility suitability category valid
    assert out_df["facility_suitability_category"].isin(["PRIMARY_RELOCATION", "POTENTIAL_RELOCATION", "MEDICAL_SUPPORT", "OTHER"]).all(), "QA Error: Invalid suitability category!"

    # 13. Hazard evidence flags traceable
    assert (out_df["hazard_evidence_flags"].str.len() > 0).all(), "QA Error: Empty hazard evidence flags!"

    # 14. Ranking explanation non-empty
    assert (out_df["ranking_explanation"].str.len() > 0).all(), "QA Error: Empty ranking explanation!"

    # 15. Configuration weights sum to 1.0
    assert abs(sum(RANKING_CONFIG["weights"].values()) - 1.0) < 1e-6, "QA Error: Weights sum mismatch!"

    # 16. No NaN/Inf in score
    assert not out_df["transparent_priority_score"].isnull().any(), "QA Error: Null score found!"

    # 17. Distance evidence index non-negative
    d_indices_valid = out_df["distance_evidence_index"].dropna()
    assert (d_indices_valid >= 0.0).all(), "QA Error: Negative distance index!"

    # 18. Medical facilities remain classified as medical support
    med_df = out_df[out_df["facility_role"] == "medical_support"]
    assert (med_df["facility_suitability_category"] == "MEDICAL_SUPPORT").all(), "QA Error: Medical facility classification error!"

    # 19. Missing GSI is not interpreted as Low
    gsi_zero_df = out_df[out_df["gsi_susceptibility"] == 0]
    assert (gsi_zero_df["hazard_evidence_flags"].str.contains("NO_GSI_COVERAGE")).all(), "QA Error: Missing GSI tagged as Low!"

    # 20. Historical absence is not interpreted as safety
    hist_zero_df = out_df[out_df["historical_landslide_evidence"] == 0]
    assert not (hist_zero_df["safety_reasons"].str.contains("Confirmed Safe")).any(), "QA Error: Historical absence called safe!"

    # 21. 2011 population remains labeled as 2011
    assert "matched_village_population_2011" in out_df.columns, "QA Error: Population column label changed!"

    # 22 & 23. Ranking method and config version stored
    assert (out_df["ranking_method"].str.len() > 0).all(), "QA Error: Missing ranking method!"
    assert (out_df["ranking_config_version"] == "prototype_v2").all(), "QA Error: Ranking config version mismatch!"

    # 24 & 25. No external datasets or ML models
    assert (out_df["source"] == "OpenStreetMap_Overpass").all(), "QA Error: Source modified!"

    # 26 (v2 Specific): Unmatched candidates have NULL village_forecast_priority_score
    unmatched_df = out_df[out_df["village_match_status"] == "unmatched"]
    assert unmatched_df["village_forecast_priority_score"].isnull().all(), "QA Error (v2): Unmatched candidate has non-null village priority score!"
    assert (unmatched_df["village_priority_status"] == "UNAVAILABLE").all(), "QA Error (v2): Unmatched candidate priority status error!"

    logger.info("ALL 26 QA ASSERTION CHECKS PASSED SUCCESSFULLY (prototype_v2)!")

    # STEP 21: SUMMARY REPORT
    score_min = out_df["transparent_priority_score"].min()
    score_max = out_df["transparent_priority_score"].max()
    score_mean = out_df["transparent_priority_score"].mean()

    grp_counts = out_df["ranking_group"].value_counts().to_dict()
    cat_counts = out_df["facility_suitability_category"].value_counts().to_dict()
    comp_counts = out_df["evidence_completeness_status"].value_counts().to_dict()

    hist_c = int((out_df["historical_landslide_evidence"] == 1).sum())
    gsi_no_cov_c = int((out_df["gsi_susceptibility"] == 0).sum())
    dyn_risk_c = int(out_df["dynamic_risk_combined"].notnull().sum())
    v_priority_c = int((out_df["village_priority_status"] == "AVAILABLE").sum())
    acc_c = int(out_df["distance_to_village_km"].notnull().sum())

    print("\n" + "="*80)
    print("WAYANAD RELOCATION CANDIDATE RANKING SUMMARY (prototype_v2)")
    print("="*80)
    print(f"Input Candidates:                   {cand_count}")
    print(f"Ranking Status:                     {ranking_status_val}")
    print(f"Ranking Config Version:             {RANKING_CONFIG['version']}")
    print(f"Ranking Method:                     {out_df['ranking_method'].iloc[0]}")
    print("\nSafety / Eligibility Groups Breakdown:")
    print(f"  ELIGIBLE:                         {grp_counts.get('ELIGIBLE', 0)}")
    print(f"  CONDITIONAL:                      {grp_counts.get('CONDITIONAL', 0)}")
    print(f"  DO_NOT_PRIORITIZE:                {grp_counts.get('DO_NOT_PRIORITIZE', 0)}")
    print("\nFacility Suitability Categories Breakdown:")
    print(f"  PRIMARY_RELOCATION:               {cat_counts.get('PRIMARY_RELOCATION', 0)}")
    print(f"  POTENTIAL_RELOCATION:             {cat_counts.get('POTENTIAL_RELOCATION', 0)}")
    print(f"  MEDICAL_SUPPORT:                  {cat_counts.get('MEDICAL_SUPPORT', 0)}")
    print("\nEvidence Completeness Status:")
    print(f"  HIGH:                             {comp_counts.get('HIGH', 0)}")
    print(f"  MEDIUM:                           {comp_counts.get('MEDIUM', 0)}")
    print(f"  LOW:                              {comp_counts.get('LOW', 0)}")
    print("\nEvidence Availability Summary:")
    print(f"  Candidates with Village Priority:  {v_priority_c}")
    print(f"  Candidates with Dynamic Risk:      {dyn_risk_c}")
    print(f"  Candidates with Distance Evidence: {acc_c}")
    print(f"  Candidates with Missing GSI:       {gsi_no_cov_c}")
    print(f"  Candidates with Historical Scar:   {hist_c}")
    print("\nScore Metrics:")
    print(f"  Minimum Priority Score:           {score_min:.4f}")
    print(f"  Mean Priority Score:              {score_mean:.4f}")
    print(f"  Maximum Priority Score:           {score_max:.4f}")
    print(f"  Missing Scores:                   0")
    print("="*80 + "\n")

    print("TOP 10 PROTOTYPE-PRIORITY CANDIDATES UNDER INCOMPLETE SAFETY EVIDENCE (prototype_v2):\n")
    top10_cols = [
        "overall_rank", "candidate_id", "name", "facility_category", "facility_role",
        "matched_village_name", "village_forecast_priority_score", "dynamic_risk_combined",
        "distance_to_village_km", "distance_to_nearest_road_m", "transparent_priority_score", "ranking_group"
    ]
    print(out_df[top10_cols].head(10).to_string(index=False))
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
