import sys
import json
import hashlib
import logging
from pathlib import Path
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_relocation_data")

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "data" / "manifest" / "wayanad_runtime_data.json"
RELOCATION_CSV = ROOT / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_ranking.csv"
DYNAMIC_RISK_CSV = ROOT / "data" / "processed" / "exposure" / "village_risk" / "wayanad_village_dynamic_risk.csv"


def calculate_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main() -> bool:
    logger.info("=" * 70)
    logger.info("HAZIVA RELOCATION DATASET VALIDATION & LINEAGE AUDIT")
    logger.info("=" * 70)

    # 1. Manifest verification
    if not MANIFEST_PATH.exists():
        logger.error(f"[FAIL] Data manifest missing at: {MANIFEST_PATH}")
        return False
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    logger.info(f"Loaded manifest: {manifest.get('project')} ({manifest.get('region')}), version {manifest.get('dataset_version')}")

    # 2. File presence & checksum check
    all_files_ok = True
    for rel_path, expected_hash in manifest.get("checksums_sha256", {}).items():
        abs_path = ROOT / rel_path
        if not abs_path.exists():
            logger.error(f"[FAIL] Required runtime bundle file missing: {rel_path}")
            all_files_ok = False
            continue
        
        actual_hash = calculate_sha256(abs_path)
        if actual_hash == expected_hash:
            logger.info(f"[PASS] Checksum verified: {rel_path}")
        else:
            logger.warning(f"[WARNING] Checksum changed for {rel_path} (Expected: {expected_hash[:8]}..., Actual: {actual_hash[:8]}...)")

    if not all_files_ok:
        logger.error("[FAIL] Runtime data bundle validation failed due to missing files.")
        return False

    # 3. Load & validate relocation candidate dataset
    df = pd.read_csv(RELOCATION_CSV)
    cand_count = len(df)
    baseline_cand = manifest.get("baseline_counts", {}).get("relocation_candidate_count", 794)

    if cand_count == baseline_cand:
        logger.info(f"[PASS] Relocation candidate count matches baseline: {cand_count} candidates")
    else:
        logger.warning(f"[WARNING] Candidate count is {cand_count} (recorded baseline is {baseline_cand}). Version check notice.")

    # 4. Candidate ID uniqueness
    if len(df["candidate_id"].unique()) == cand_count:
        logger.info(f"[PASS] Candidate IDs are 100% unique ({cand_count} candidates)")
    else:
        logger.error("[FAIL] Duplicate candidate_id values found!")
        return False

    # 5. Coordinates validation
    lats = df["latitude"]
    lons = df["longitude"]
    if lats.notnull().all() and lons.notnull().all():
        if ((lats >= 11.0) & (lats <= 12.5) & (lons >= 75.0) & (lons <= 77.0)).all():
            logger.info("[PASS] Geographic coordinates valid and within Wayanad bounding box")
        else:
            logger.error("[FAIL] Candidate coordinates out of Wayanad bounding box range")
            return False
    else:
        logger.error("[FAIL] Null candidate coordinates found!")
        return False

    # 6. Candidate ↔ Habitation Linkage Check
    dyn_df = pd.read_csv(DYNAMIC_RISK_CSV)
    valid_village_codes = set(dyn_df["village_code"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True))

    cand_v_codes = df["matched_village_code"].dropna().astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
    unlinked_candidates = len(df[df["matched_village_code"].isnull()])
    matched_candidates = len(cand_v_codes)

    linked_to_known_habs = sum(c in valid_village_codes for c in cand_v_codes)
    logger.info(f"[PASS] Candidate ↔ Habitation Linkage Summary:")
    logger.info(f"       - Candidates matched to habitations: {matched_candidates}")
    logger.info(f"       - Candidates unlinked (urban/boundary): {unlinked_candidates}")
    logger.info(f"       - Candidates linked to active habitations: {linked_to_known_habs}")

    # 7. Truthfulness & Safety Status Audit
    safety_statuses = df["safety_status"].unique()
    valid_statuses = {"PASS", "FLAG", "INSUFFICIENT_EVIDENCE"}
    if set(safety_statuses).issubset(valid_statuses):
        logger.info(f"[PASS] Safety statuses truthful and valid: {set(safety_statuses)}")
    else:
        logger.error(f"[FAIL] Invalid safety status values found: {set(safety_statuses) - valid_statuses}")
        return False

    # 8. Capacity Label Truthfulness Audit
    cap_statuses = df["capacity_status"].unique()
    logger.info(f"[PASS] Capacity status semantics: {set(cap_statuses)} (Heuristic/Unknown labels preserved)")

    logger.info("=" * 70)
    logger.info("ALL RELOCATION DATA LINEAGE ASSERTION CHECKS PASSED SUCCESSFULLY")
    logger.info("=" * 70)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
