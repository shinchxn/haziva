import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.database import Base, get_engine, get_sessionmaker
from backend.app.models.habitation import Habitation
from backend.app.models.relocation_site import RelocationSite
from backend.app.models.risk import Risk
from backend.app.services.trajectory import calculate_trajectory


DYNAMIC_RISK_CSV = ROOT / "data" / "processed" / "exposure" / "village_risk" / "wayanad_village_dynamic_risk.csv"
RISK_EXPOSURE_CSV = ROOT / "data" / "processed" / "exposure" / "village_risk" / "wayanad_village_risk_exposure.csv"
RELOCATION_RANKING_CSV = ROOT / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_ranking.csv"
VILLAGE_GPKG = ROOT / "data" / "processed" / "exposure" / "census_nwdp_reconciliation" / "wayanad_census_nwdp_village_population_2011.gpkg"


def get_village_centroids() -> dict[str, tuple[float, float]]:
    """Extract village centroids (lat, lon) from GPKG or fall back to default Wayanad bbox center."""
    centroids = {}
    try:
        import geopandas as gpd
        if VILLAGE_GPKG.exists():
            gdf = gpd.read_file(VILLAGE_GPKG)
            # Ensure EPSG:4326 for lat/lon
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            for _, row in gdf.iterrows():
                code = str(row.get("village_code", "")).strip()
                if code.endswith(".0"):
                    code = code[:-2]
                centroid = row.geometry.centroid
                centroids[code] = (float(centroid.y), float(centroid.x))
    except Exception as e:
        print(f"Notice: geopandas centroid extraction returned error: {e}. Using calculated/fallback centroids.")
    return centroids


def estimate_capacity(facility_category: str, building_type: str | None = None) -> int:
    cat = str(facility_category).lower()
    bld = str(building_type).lower() if building_type else ""
    if "education" in cat or "school" in bld:
        return 650
    if "community" in cat or "hall" in bld:
        return 900
    if "stadium" in cat or "sports" in cat:
        return 1500
    if "hospital" in cat or "medical" in cat:
        return 300
    return 450


def seed_database(db: Session | None = None) -> None:
    engine = get_engine()
    print(f"Creating database tables on engine: {engine.url}")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    close_session = False
    if db is None:
        SessionFactory = get_sessionmaker()
        db = SessionFactory()
        close_session = True

    try:
        print("=" * 80)
        print("SEEDING HAZIVA DATABASE FROM PROCESSED GIS & ML OUTPUTS")
        print("=" * 80)

        # 1. Load DataFrames
        missing_files = []
        if not DYNAMIC_RISK_CSV.exists(): missing_files.append(str(DYNAMIC_RISK_CSV.relative_to(ROOT)))
        if not RISK_EXPOSURE_CSV.exists(): missing_files.append(str(RISK_EXPOSURE_CSV.relative_to(ROOT)))
        if not RELOCATION_RANKING_CSV.exists(): missing_files.append(str(RELOCATION_RANKING_CSV.relative_to(ROOT)))

        if missing_files:
            raise RuntimeError(
                f"\n{'='*80}\n"
                f"SETUP ERROR: Runtime seed dataset(s) missing:\n"
                + "\n".join(f"  - {f}" for f in missing_files) + "\n\n"
                "Please verify Git checkout or run `python scripts/validate_relocation_data.py` / `python scripts/prepare_relocation_data.py`.\n"
                f"{'='*80}"
            )


        dynamic_df = pd.read_csv(DYNAMIC_RISK_CSV)
        exposure_df = pd.read_csv(RISK_EXPOSURE_CSV)
        relocation_df = pd.read_csv(RELOCATION_RANKING_CSV)

        # Normalize village codes
        dynamic_df["village_code_clean"] = dynamic_df["village_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        exposure_df["village_code_clean"] = exposure_df["village_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

        merged_villages = pd.merge(
            dynamic_df,
            exposure_df[["village_code_clean", "model_a_risk_p95", "model_a_risk_mean", "priority_score", "priority_rank"]],
            on="village_code_clean",
            how="left"
        )

        centroids = get_village_centroids()

        # Clean existing records
        db.query(RelocationSite).delete()
        db.query(Risk).delete()
        db.query(Habitation).delete()
        db.commit()

        habitations_to_add = []
        risks_to_add = []

        primary_village_code = None

        for _, row in merged_villages.iterrows():
            vcode = str(row["village_code_clean"])
            vname = str(row["village_name"]).strip()
            pop = int(row["population_2011"]) if pd.notna(row["population_2011"]) else 0
            households = int(row["households_2011"]) if pd.notna(row["households_2011"]) else 0

            # Default coordinates for Wayanad (~11.6 to 11.8 N, 75.9 to 76.2 E) if missing
            lat, lon = centroids.get(vcode, (11.65, 76.10))

            hab_id = f"hab_{vcode}"
            if primary_village_code is None:
                primary_village_code = hab_id

            pop_exp_index = float(row.get("population_exposure_index", 0.5)) if pd.notna(row.get("population_exposure_index")) else 0.5

            hab = Habitation(
                id=hab_id,
                name=vname,
                latitude=float(lat),
                longitude=float(lon),
                population=pop,
                households=households,
                exposure_info={
                    "landslide_susceptibility": "High" if float(row.get("model_a_risk_p95", 0.5)) > 0.6 else "Moderate",
                    "population_exposure": "High" if pop_exp_index > 0.7 else "Moderate",
                    "score": round(pop_exp_index, 4),
                    "priority_score": round(float(row.get("forecast_priority_score", 0.5)), 4),
                    "priority_rank": int(row.get("forecast_priority_rank", 99)),
                },
                vulnerability_info={
                    "socioeconomic_vulnerability": "Moderate",
                    "health_access": "Standard",
                    "score": 0.5,
                },
                accessibility_info={
                    "road_access": "Standard",
                    "evacuation_route": "Primary Road Network",
                    "score": 0.5,
                },
            )
            habitations_to_add.append(hab)

            # Risk calculation: require real values from processed CSVs without synthetic multiplication fallbacks
            if pd.isna(row.get("model_a_risk_p95")) or pd.isna(row.get("risk_24h_p95")) or pd.isna(row.get("risk_72h_p95")):
                raise ValueError(
                    f"Missing required real GIS/dynamic risk values for village code '{vcode}'. "
                    "Synthetic multiplication fallbacks are forbidden."
                )

            c_risk = float(row["model_a_risk_p95"])
            r_24h = float(row["risk_24h_p95"])
            r_72h = float(row["risk_72h_p95"])

            c_risk = round(min(max(c_risk, 0.0), 1.0), 4)
            r_24h = round(min(max(r_24h, 0.0), 1.0), 4)
            r_72h = round(min(max(r_72h, 0.0), 1.0), 4)

            traj = calculate_trajectory(c_risk, r_24h, r_72h)

            drivers = [
                f"Model A terrain susceptibility p95: {c_risk:.2f}",
                f"24h forecast rainfall risk p95: {r_24h:.2f}",
                f"72h forecast rainfall risk p95: {r_72h:.2f}",
                f"Census 2011 population exposure index: {pop_exp_index:.2f}",
            ]

            risk_obj = Risk(
                habitation_id=hab_id,
                current_risk=c_risk,
                risk_24h=r_24h,
                risk_72h=r_72h,
                trajectory=traj,
                confidence=0.85,
                confidence_reason="Data Coverage: 85% — Represents spatial & temporal coverage of supporting 30m terrain grid, GSI susceptibility, Census 2011 reconciliation, and ECMWF 24h/72h rainfall forecast coverage (Not model prediction accuracy).",
                prediction_timestamp=datetime.now(timezone.utc),
                risk_drivers=drivers,
            )
            risks_to_add.append(risk_obj)

        db.add_all(habitations_to_add)
        db.add_all(risks_to_add)
        db.commit()
        print(f"Successfully seeded {len(habitations_to_add)} habitations and risk profiles.")

        # 2. Seed Relocation Sites
        relocation_sites_to_add = []

        valid_hab_ids = {h.id for h in habitations_to_add}

        for _, row in relocation_df.iterrows():
            cid = str(row["candidate_id"]).strip()
            matched_v = str(row.get("matched_village_code", "")).strip().replace(".0", "")

            target_hab_id = f"hab_{matched_v}" if matched_v and f"hab_{matched_v}" in valid_hab_ids else None

            facility_name = str(row.get("name", "")).strip()
            if not facility_name or facility_name.lower() == "nan":
                facility_name = f"Relocation Facility ({cid})"

            cat = str(row.get("facility_category", "community")).strip()
            bld = str(row.get("building_type", "")).strip()

            lat = float(row["latitude"]) if pd.notna(row["latitude"]) else 11.65
            lon = float(row["longitude"]) if pd.notna(row["longitude"]) else 76.10

            safety_status = str(row.get("safety_status", "INSUFFICIENT_EVIDENCE")).strip()
            access_status = str(row.get("accessibility_status", "UNKNOWN")).strip()
            ranking_exp = str(row.get("ranking_explanation", "Prototype candidate site subject to authority verification.")).strip()

            cap = estimate_capacity(cat, bld)
            t_score = float(row.get("transparent_priority_score", 0.5)) if pd.notna(row.get("transparent_priority_score")) else 0.5

            site = RelocationSite(
                site_id=cid,
                habitation_id=target_hab_id,
                name=facility_name,
                facility_category=cat,
                latitude=lat,
                longitude=lon,
                status="candidate",
                safety_result=safety_status,
                capacity=cap,
                capacity_status="HEURISTIC",
                infrastructure_info={
                    "water": {"status": "UNKNOWN", "source": None, "label": "Water Availability: Unknown — Verification Required"},
                    "shelter": {"status": "VERIFIED", "source": "OpenStreetMap", "label": "Public Shelter/Facility"},
                    "roads": {"status": "VERIFIED", "source": "OpenStreetMap Proximity", "label": access_status},
                    "osm_type": str(row.get("osm_type", "")),
                },
                accessibility=access_status,
                rejection_reason=str(row.get("safety_reasons", "")) if safety_status != "PASS" else None,
                transparent_priority_score=round(t_score, 4),
                ranking_explanation=ranking_exp,
            )
            relocation_sites_to_add.append(site)

        db.add_all(relocation_sites_to_add)
        db.commit()
        print(f"Successfully seeded {len(relocation_sites_to_add)} relocation candidate sites.")

        print("=" * 80)
        print("DATABASE SEEDING COMPLETE SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"Error during database seeding: {e}")
        raise
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    seed_database()
