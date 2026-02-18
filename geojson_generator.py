"""
Python-based GeoJSON generator for Render deployment (no R dependency)
Generates districts.geojson, thanas.geojson, and regions.geojson from CSV data
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any


def load_geojson_template(output_dir: Path, filename: str) -> Dict[str, Any]:
    """Load existing GeoJSON template to preserve geometry"""
    filepath = output_dir / filename
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {filename}: {e}")
    return {"type": "FeatureCollection", "features": []}


def update_geojson_properties(geojson_template: Dict, csv_data: Dict) -> Dict:
    """Update properties in GeoJSON features based on current CSV mappings"""
    
    if "features" not in geojson_template:
        return geojson_template
    
    for feature in geojson_template["features"]:
        if "properties" not in feature:
            feature["properties"] = {}
        
        props = feature["properties"]
        
        # For district-level features
        if "District" in props:
            district_name = props.get("District", "")
            if district_name in csv_data["district_to_region"]:
                props["Region"] = csv_data["district_to_region"][district_name]
        
        # For thana-level features
        if "Upazila" in props and "District" in props:
            thana_key = (props.get("District", ""), props.get("Upazila", ""))
            if thana_key in csv_data["thana_to_region"]:
                props["Region"] = csv_data["thana_to_region"][thana_key][0]
                props["District"] = csv_data["thana_to_region"][thana_key][1]
    
    return geojson_template


def generate_geojson_from_csv(base_dir: Path) -> bool:
    """
    Generate/update GeoJSON files based on current CSV data
    Returns True if successful, False if R script should be tried
    """
    
    try:
        output_dir = base_dir / "geojson"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        csv_file = base_dir / "region_swapped_data.csv"
        if not csv_file.exists():
            print(f"CSV file not found: {csv_file}")
            return False
        
        # Load current mappings from CSV
        district_to_region: Dict[str, str] = {}
        thana_to_region: Dict[tuple, tuple] = {}  # (district, thana) -> (region, district, thana)
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                region = row.get("Region", "").strip()
                district = row.get("District", "").strip()
                thana = row.get("Thana", "").strip()
                
                if district:
                    district_to_region[district] = region
                
                if district and thana:
                    thana_to_region[(district, thana)] = (region, district, thana)
        
        print(f"Loaded {len(district_to_region)} districts and {len(thana_to_region)} thanas from CSV")
        
        csv_data = {
            "district_to_region": district_to_region,
            "thana_to_region": thana_to_region
        }
        
        # Update existing GeoJSON files
        geojson_files = ["districts.geojson", "thanas.geojson", "regions.geojson"]
        
        for filename in geojson_files:
            template = load_geojson_template(output_dir, filename)
            updated = update_geojson_properties(template, csv_data)
            
            filepath = output_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(updated, f)
            print(f"✓ Updated {filename}")
        
        print("✓ GeoJSON update complete")
        return True
        
    except Exception as e:
        print(f"Error updating GeoJSON: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    success = generate_geojson_from_csv(base_dir)
    exit(0 if success else 1)
