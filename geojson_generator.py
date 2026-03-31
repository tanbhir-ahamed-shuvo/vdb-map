"""
Python-based GeoJSON generator for Render deployment (no R dependency).
Updates districts.geojson, thanas.geojson, and regions.geojson from CSV data.

GeoJSON property names used in this project:
  districts.geojson -> {'region': ..., 'district': ...}  (all lowercase)
  thanas.geojson    -> {'region': ..., 'district': ..., 'thana': ...}  (all lowercase)
  regions.geojson   -> {'region': ...}  (all lowercase)
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any


def load_geojson(filepath: Path) -> Dict[str, Any]:
    """Load GeoJSON file, return empty FeatureCollection if missing/corrupt."""
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {filepath.name}: {e}")
    return {"type": "FeatureCollection", "features": []}


def save_geojson(filepath: Path, data: Dict[str, Any]) -> bool:
    """Save GeoJSON file compactly (no indent for smaller file size)."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filepath.name}: {e}")
        return False


def load_csv_mappings(csv_path: Path):
    """
    Load region/district/thana mappings from the CSV file.
    Returns:
        district_to_region: {district_name -> region_name}
        thana_to_info:      {(district_name, thana_name) -> region_name}
    """
    district_to_region: Dict[str, str] = {}
    thana_to_info: Dict[tuple, str] = {}

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row.get("Region", "").strip()
            district = row.get("District", "").strip()
            thana = row.get("Thana", "").strip()

            if region and district:
                # Last assignment wins if a district spans multiple rows (it shouldn't, but just in case)
                district_to_region[district] = region

            if region and district and thana:
                thana_to_info[(district, thana)] = region

    print(f"  CSV: {len(district_to_region)} districts, {len(thana_to_info)} thanas loaded")
    return district_to_region, thana_to_info


def update_districts_geojson(geojson: Dict, district_to_region: Dict[str, str]) -> int:
    """
    Update the 'region' property in each district feature.
    Returns number of features updated.
    """
    updated = 0
    not_found = []

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})

        # Property name is 'district' (LOWERCASE) in this project
        district_name = props.get("district", "")

        if district_name in district_to_region:
            new_region = district_to_region[district_name]
            if props.get("region") != new_region:
                props["region"] = new_region
                updated += 1
            else:
                updated += 1  # Count it as processed even if unchanged
        else:
            not_found.append(district_name)

    if not_found:
        print(f"  Warning: {len(not_found)} districts in GeoJSON not found in CSV: {not_found[:5]}")

    return updated


def update_thanas_geojson(geojson: Dict, thana_to_info: Dict[tuple, str],
                          district_to_region: Dict[str, str]) -> int:
    """
    Update the 'region' property in each thana feature.
    Fallback: if thana not found by (district, thana), use district_to_region.
    Returns number of features updated.
    """
    updated = 0

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})

        # Property names are 'district' and 'thana' (LOWERCASE)
        district_name = props.get("district", "")
        thana_name = props.get("thana", "")

        key = (district_name, thana_name)
        if key in thana_to_info:
            props["region"] = thana_to_info[key]
            updated += 1
        elif district_name in district_to_region:
            # Fallback: use the district's region
            props["region"] = district_to_region[district_name]
            updated += 1

    return updated


def rebuild_regions_geojson(geojson: Dict, district_to_region: Dict[str, str]) -> Dict:
    """
    Rebuild regions.geojson by grouping district features under their new regions.
    Instead of dissolving polygons (needs shapely/geopandas), we create one
    MultiPolygon feature per region from the district geometries.
    This works without any external dependencies.
    """
    from collections import defaultdict

    # Group district geometries by region
    region_geometries: Dict[str, List] = defaultdict(list)

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        district_name = props.get("district", "")
        geom = feature.get("geometry", {})

        region = district_to_region.get(district_name, props.get("region", ""))
        if region and geom:
            region_geometries[region].append(geom)

    if not region_geometries:
        return geojson  # Nothing to rebuild

    new_features = []
    for region, geometries in sorted(region_geometries.items()):
        # Collect all polygon rings into one MultiPolygon
        all_polygons = []
        for geom in geometries:
            geom_type = geom.get("type", "")
            coords = geom.get("coordinates", [])
            if geom_type == "Polygon":
                all_polygons.append(coords)
            elif geom_type == "MultiPolygon":
                all_polygons.extend(coords)

        if all_polygons:
            new_features.append({
                "type": "Feature",
                "properties": {"region": region},
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": all_polygons
                }
            })

    return {
        "type": "FeatureCollection",
        "features": new_features
    }


def generate_geojson_from_csv(base_dir: Path) -> bool:
    """
    Update all GeoJSON files based on current CSV data.
    This is the main entry point called from app.py.
    Returns True if successful.
    """
    try:
        geojson_dir = base_dir / "geojson"
        geojson_dir.mkdir(exist_ok=True, parents=True)

        csv_file = base_dir / "region_swapped_data.csv"
        if not csv_file.exists():
            print(f"ERROR: CSV file not found: {csv_file}")
            return False

        print("Loading CSV mappings...")
        district_to_region, thana_to_info = load_csv_mappings(csv_file)

        # ── 1. Update districts.geojson ──────────────────────────────────────
        districts_path = geojson_dir / "districts.geojson"
        districts_geo = load_geojson(districts_path)

        if districts_geo["features"]:
            n = update_districts_geojson(districts_geo, district_to_region)
            if save_geojson(districts_path, districts_geo):
                print(f"[OK] districts.geojson updated ({n} features)")
            else:
                print("[WARN] Could not save districts.geojson")
        else:
            print("[WARN] districts.geojson is empty or missing — cannot update")

        # ── 2. Update thanas.geojson ─────────────────────────────────────────
        thanas_path = geojson_dir / "thanas.geojson"
        thanas_geo = load_geojson(thanas_path)

        if thanas_geo["features"]:
            n = update_thanas_geojson(thanas_geo, thana_to_info, district_to_region)
            if save_geojson(thanas_path, thanas_geo):
                print(f"[OK] thanas.geojson updated ({n} features)")
            else:
                print("[WARN] Could not save thanas.geojson")
        else:
            print("[WARN] thanas.geojson is empty or missing — cannot update")

        # ── 3. Rebuild regions.geojson from updated districts ────────────────
        regions_path = geojson_dir / "regions.geojson"
        if districts_geo["features"]:
            regions_geo = rebuild_regions_geojson(districts_geo, district_to_region)
            if save_geojson(regions_path, regions_geo):
                print(f"[OK] regions.geojson rebuilt ({len(regions_geo['features'])} regions)")
            else:
                print("[WARN] Could not save regions.geojson")
        else:
            print("[WARN] Skipping regions.geojson rebuild — no district data")

        print("[OK] GeoJSON update complete!")
        return True

    except Exception as e:
        print(f"ERROR in generate_geojson_from_csv: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    print(f"Running GeoJSON generator from: {base_dir}")
    success = generate_geojson_from_csv(base_dir)
    exit(0 if success else 1)
