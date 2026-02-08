from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory, Response

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder="outputs", static_url_path="/outputs")


@app.after_request
def add_header(response):
    """Add headers to disable caching for map images."""
    if request.path.startswith('/outputs/'):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response


def normalize_thana_name(thana: str) -> str:
    """Preserve correct spellings for known thanas."""
    corrections = {
        "Jessore Sadar": "Kotwali",
        "Dualatpur": "Daulatpur",
        "Nowabganj": "Nawabganj",
    }
    return corrections.get(thana, thana)


@app.route("/")
def index() -> Any:
    return send_from_directory(BASE_DIR, "region-manager-interactive.html")


@app.route("/generate", methods=["POST"])
def generate() -> Any:
    try:
        payload: List[Dict[str, str]] = request.get_json(force=True)
        if not isinstance(payload, list) or len(payload) == 0:
            return jsonify({"success": False, "message": "No data provided"}), 400

        csv_path = BASE_DIR / "region_swapped_data.csv"
        
        # Load existing CSV to preserve spellings and corrections
        existing_data = {}
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        region, district, thana = parts[0], parts[1], parts[2]
                        existing_data[(district.strip(), thana.strip())] = (region.strip(), district.strip(), thana.strip())
        except FileNotFoundError:
            pass

        # Build new data, preserving spellings from existing CSV
        output_rows = []
        for row in payload:
            region = row.get("region", "").strip()
            district = row.get("district", "").strip()
            thana = row.get("thana", "").strip()
            
            # Check if this (district, thana) exists in original - use original spelling
            key = (district, thana)
            if key in existing_data:
                _, _, original_thana = existing_data[key]
                thana = original_thana  # Use original spelling
            else:
                # Apply corrections if not found
                thana = normalize_thana_name(thana)
            
            if region and district and thana:
                output_rows.append((region, district, thana))
        
        # Write CSV maintaining header
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            f.write("Region,District,Thana\n")
            for region, district, thana in output_rows:
                f.write(f"{region},{district},{thana}\n")

        cmd = ["Rscript", "generate_map_from_swaps.R"]
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=False,
        )

        district_png = OUTPUT_DIR / "bangladesh_districts_updated_from_swaps.png"
        thana_png = OUTPUT_DIR / "bangladesh_thanas_updated_from_swaps.png"
        district_pdf = OUTPUT_DIR / "bangladesh_districts_updated_from_swaps.pdf"
        thana_pdf = OUTPUT_DIR / "bangladesh_thanas_updated_from_swaps.pdf"

        outputs_exist = all(p.exists() for p in [district_png, thana_png, district_pdf, thana_pdf])

        if result.returncode != 0 and not outputs_exist:
            return jsonify(
                {
                    "success": False,
                    "message": "Map generation failed",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            ), 500

        return jsonify(
            {
                "success": True,
                "message": "Maps generated",
                "outputs": {
                    "district_png": "/outputs/bangladesh_districts_updated_from_swaps.png",
                    "thana_png": "/outputs/bangladesh_thanas_updated_from_swaps.png",
                    "district_pdf": "/outputs/bangladesh_districts_updated_from_swaps.pdf",
                    "thana_pdf": "/outputs/bangladesh_thanas_updated_from_swaps.pdf",
                },
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "message": str(exc)}), 500



@app.route("/region_swapped_data.csv")
def get_csv() -> Any:
    """Serve the CSV file with no-cache headers to always get the latest version."""
    csv_path = BASE_DIR / "region_swapped_data.csv"
    response = send_from_directory(BASE_DIR, "region_swapped_data.csv")
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


@app.route("/<path:filename>")
def static_files(filename: str) -> Any:
    return send_from_directory(BASE_DIR, filename)


@app.route("/favicon.ico")
def favicon() -> Response:
    return Response(status=204)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
