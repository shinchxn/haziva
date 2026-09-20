"""
HAZIVA Relocation Data Preparation & Initialization Script

This script checks for the presence of full raw GeoTIFF GIS rasters:
- If raw rasters are locally present (developer GIS environment), it executes full candidate extraction & ranking re-processing scripts.
- If raw rasters are absent (fresh clone environment), it verifies that the committed lightweight (~5 MB) runtime data bundle is present and ready for database seeding.
"""

import sys
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("prepare_relocation_data")


ROOT = Path(__file__).resolve().parent.parent

# Required GIS Rasters for full offline re-generation
RASTER_FILES = [
    ROOT / "data" / "processed" / "terrain" / "wayanad_copernicus_slope_degrees.tif",
    ROOT / "data" / "processed" / "landslide" / "susceptibility" / "wayanad_gsi_susceptibility_copernicus_30m.tif",
    ROOT / "data" / "processed" / "landslide" / "inventory" / "wayanad_historical_landslide_presence_copernicus_30m.tif",
]

# Pipeline scripts
PIPELINE_SCRIPTS = [
    "build_relocation_candidate_facilities.py",
    "build_relocation_candidate_safety.py",
    "build_relocation_candidate_accessibility.py",
    "build_relocation_candidate_ranking.py",
]

# Committed runtime CSV dataset
RUNTIME_RANKING_CSV = ROOT / "data" / "processed" / "exposure" / "relocation" / "wayanad_relocation_candidate_ranking.csv"


def main():
    logger.info("=" * 70)
    logger.info("HAZIVA RELOCATION DATA PIPELINE PREPARATION & AUDIT")
    logger.info("=" * 70)

    # Check raster availability
    missing_rasters = [p for p in RASTER_FILES if not p.exists()]

    if not missing_rasters:
        logger.info("All required GIS rasters present. Executing full canonical GIS candidate processing pipeline...")
        for script_name in PIPELINE_SCRIPTS:
            script_path = ROOT / "scripts" / script_name
            logger.info(f"Running pipeline step: {script_name}...")
            res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
            if res.returncode != 0:
                logger.error(f"Error executing {script_name}:\n{res.stderr}")
                sys.exit(1)
            logger.info(f"Step {script_name} completed successfully.")
        logger.info("Full GIS candidate processing pipeline completed successfully.")
    else:
        logger.info("Large GeoTIFF GIS rasters are excluded from Git repository to keep checkout lightweight.")
        if RUNTIME_RANKING_CSV.exists():
            logger.info(f"[OK] Committed runtime bundle dataset present at:\n     {RUNTIME_RANKING_CSV}")
            logger.info("Database seeding can proceed directly using the committed runtime bundle.")
            logger.info("Run `python scripts/validate_relocation_data.py` to verify integrity.")
        else:
            logger.error("[FAIL] Runtime candidate ranking dataset is missing!")
            logger.error("Missing rasters required for full re-generation:")
            for p in missing_rasters:
                logger.error(f"  - {p.relative_to(ROOT)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
