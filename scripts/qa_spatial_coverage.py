import sys
import logging
from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.crs import CRS
from shapely.geometry import box, shape

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("spatial_qa")

def main():
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    boundary_path = data_dir / "raw" / "boundaries" / "wayanad_boundary.geojson"
    dem_path = data_dir / "raw" / "dem" / "wayanad_srtm_gl1_30m.tif"
    slope_path = data_dir / "processed" / "terrain" / "wayanad_slope_degrees.tif"
    gsi_path = data_dir / "processed" / "landslide" / "inventory" / "wayanad_gsi_event_table.csv"
    gsi_raster_path = data_dir / "processed" / "landslide" / "inventory" / "wayanad_historical_landslide_presence_30m.tif"
    static_grid_path = data_dir / "processed" / "features" / "wayanad_static_features.parquet"

    # Input existence check
    for p, name in [
        (boundary_path, "Wayanad boundary"),
        (dem_path, "DEM"),
        (slope_path, "Slope raster"),
        (gsi_path, "GSI event table"),
        (gsi_raster_path, "GSI raster"),
        (static_grid_path, "Static feature grid")
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Missing required file for QA: {p} ({name})")

    # 1. Wayanad Boundary
    logger.info("Reading Wayanad boundary...")
    boundary_gdf = gpd.read_file(boundary_path)
    boundary_crs = boundary_gdf.crs
    boundary_bounds = boundary_gdf.total_bounds # minx, miny, maxx, maxy
    boundary_geom = boundary_gdf.geometry.unary_union
    
    # Calculate area in sq km (projected to UTM 43N EPSG:32643 for accuracy)
    boundary_gdf_utm = boundary_gdf.to_crs(epsg=32643)
    boundary_area_sqkm = boundary_gdf_utm.geometry.area.sum() / 1e6

    report = {}
    report["1_wayanad_boundary"] = {
        "path": str(boundary_path.relative_to(base_dir)),
        "crs": str(boundary_crs),
        "bounds": [float(x) for x in boundary_bounds],
        "area_sqkm": float(boundary_area_sqkm),
        "num_features": len(boundary_gdf)
    }

    # Helper function for raster QA
    def inspect_raster(path, name):
        with rasterio.open(path) as src:
            data = src.read(1)
            nodata = src.nodata
            bounds = [float(x) for x in src.bounds]
            res = [float(src.res[0]), float(src.res[1])]
            dims = [int(src.height), int(src.width)]
            crs = str(src.crs)
            total_cells = dims[0] * dims[1]
            
            if nodata is None or np.isnan(nodata):
                nodata_mask = np.isnan(data)
            else:
                nodata_mask = (data == nodata) | np.isnan(data)
            
            valid_cells = int((~nodata_mask).sum())
            nodata_cells = int(nodata_mask.sum())
            nodata_pct = float(nodata_cells / total_cells * 100.0)

            # Raster bounding box geometry
            rbound_geom = box(*src.bounds)
            rbound_gdf = gpd.GeoDataFrame(geometry=[rbound_geom], crs=src.crs).to_crs(boundary_crs)
            
            # Intersection area with Wayanad boundary
            intersection_geom = rbound_gdf.geometry.unary_union.intersection(boundary_geom)
            if not intersection_geom.is_empty:
                inter_gdf = gpd.GeoDataFrame(geometry=[intersection_geom], crs=boundary_crs).to_crs(epsg=32643)
                covered_area_sqkm = inter_gdf.geometry.area.sum() / 1e6
            else:
                covered_area_sqkm = 0.0

            pct_wayanad_covered = float(covered_area_sqkm / boundary_area_sqkm * 100.0)

            # Also check actual valid pixels coverage vs Wayanad boundary
            return {
                "path": str(path.relative_to(base_dir)),
                "crs": crs,
                "bounds": bounds,
                "dimensions": dims,
                "resolution": res,
                "total_cells": total_cells,
                "valid_cells": valid_cells,
                "nodata_cells": nodata_cells,
                "nodata_pct": nodata_pct,
                "bbox_area_sqkm": float(gpd.GeoDataFrame(geometry=[rbound_geom], crs=src.crs).to_crs(epsg=32643).geometry.area.sum() / 1e6),
                "pct_wayanad_covered_by_bbox": pct_wayanad_covered
            }

    # 2. DEM QA
    logger.info("Inspecting DEM...")
    report["2_dem"] = inspect_raster(dem_path, "DEM")

    # 3. Slope Raster QA
    logger.info("Inspecting Slope Raster...")
    report["3_slope_raster"] = inspect_raster(slope_path, "Slope raster")

    # 4. GSI Dated Event Points QA
    logger.info("Inspecting GSI Dated Event Points...")
    gsi_df = pd.read_csv(gsi_path)
    # Check lat/lon columns
    lat_col = [c for c in gsi_df.columns if "lat" in c.lower() or "y" in c.lower()][0]
    lon_col = [c for c in gsi_df.columns if "lon" in c.lower() or "x" in c.lower()][0]

    gsi_gdf = gpd.GeoDataFrame(
        gsi_df,
        geometry=gpd.points_from_xy(gsi_df[lon_col], gsi_df[lat_col]),
        crs="EPSG:4326"
    )
    
    # Points inside Wayanad boundary
    gsi_in_boundary = gsi_gdf[gsi_gdf.geometry.within(boundary_geom)]
    gsi_out_boundary = gsi_gdf[~gsi_gdf.geometry.within(boundary_geom)]

    # Points inside DEM raster bbox and valid cells
    with rasterio.open(dem_path) as src:
        dem_crs = src.crs
        gsi_dem_crs = gsi_gdf.to_crs(dem_crs)
        coords = [(x, y) for x, y in zip(gsi_dem_crs.geometry.x, gsi_dem_crs.geometry.y)]
        dem_values = [val[0] for val in src.sample(coords)]
        dem_nodata = src.nodata
        if dem_nodata is None or np.isnan(dem_nodata):
            pts_in_dem_valid = [v for v in dem_values if not np.isnan(v)]
        else:
            pts_in_dem_valid = [v for v in dem_values if v != dem_nodata and not np.isnan(v)]

    # Points inside Slope raster
    with rasterio.open(slope_path) as src:
        slope_crs = src.crs
        gsi_slope_crs = gsi_gdf.to_crs(slope_crs)
        coords = [(x, y) for x, y in zip(gsi_slope_crs.geometry.x, gsi_slope_crs.geometry.y)]
        slope_values = [val[0] for val in src.sample(coords)]
        slope_nodata = src.nodata
        if slope_nodata is None or np.isnan(slope_nodata):
            pts_in_slope_valid = [v for v in slope_values if not np.isnan(v)]
        else:
            pts_in_slope_valid = [v for v in slope_values if v != slope_nodata and not np.isnan(v)]

    report["4_gsi_events"] = {
        "path": str(gsi_path.relative_to(base_dir)),
        "total_records": len(gsi_df),
        "num_inside_wayanad": len(gsi_in_boundary),
        "num_outside_wayanad": len(gsi_out_boundary),
        "outside_records_labels": gsi_out_boundary["location_name"].tolist() if "location_name" in gsi_out_boundary.columns else (gsi_out_boundary["location"].tolist() if "location" in gsi_out_boundary.columns else list(gsi_out_boundary.index)),
        "num_falling_in_valid_dem_cells": len(pts_in_dem_valid),
        "num_falling_in_valid_slope_cells": len(pts_in_slope_valid)
    }

    # 5. GSI Historical Landslide Presence Raster QA
    logger.info("Inspecting GSI Historical Landslide Presence Raster...")
    report["5_gsi_presence_raster"] = inspect_raster(gsi_raster_path, "GSI Presence Raster")

    # 6. Static Feature Grid QA
    logger.info("Inspecting Static Feature Grid...")
    grid_df = pd.read_parquet(static_grid_path)
    report["6_static_feature_grid"] = {
        "path": str(static_grid_path.relative_to(base_dir)),
        "total_rows": len(grid_df),
        "columns": list(grid_df.columns),
        "min_x": float(grid_df["x"].min()) if "x" in grid_df else None,
        "max_x": float(grid_df["x"].max()) if "x" in grid_df else None,
        "min_y": float(grid_df["y"].min()) if "y" in grid_df else None,
        "max_y": float(grid_df["y"].max()) if "y" in grid_df else None,
        "null_counts": {col: int(grid_df[col].isnull().sum()) for col in grid_df.columns}
    }

    # Save output report
    report_file = base_dir / "data" / "processed" / "spatial_coverage_qa_report.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Spatial QA Report successfully generated at: {report_file}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
