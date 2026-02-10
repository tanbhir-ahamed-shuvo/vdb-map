from __future__ import annotations

import json
import os
import shutil
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

        # Add logos to generated maps - CRITICAL for branding
        logo_output = ""
        logo_success = False
        
        try:
            import sys
            python_exe = sys.executable
            
            # Add logos to PDFs
            pdf_script = BASE_DIR / "add_logo_to_pdfs.py"
            pdf_result = subprocess.run(
                [python_exe, str(pdf_script)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            logo_output += "=== PDF Logo Addition ===\n"
            logo_output += pdf_result.stdout + "\n"
            if pdf_result.stderr:
                logo_output += "PDF Errors: " + pdf_result.stderr + "\n"
            
            # Add logos to PNGs
            png_script = BASE_DIR / "add_logo_to_pngs.py"
            png_result = subprocess.run(
                [python_exe, str(png_script)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            logo_output += "\n=== PNG Logo Addition ===\n"
            logo_output += png_result.stdout + "\n"
            if png_result.stderr:
                logo_output += "PNG Errors: " + png_result.stderr + "\n"
            
            logo_success = pdf_result.returncode == 0 and png_result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logo_output += "\n⚠ Logo addition timed out\n"
        except Exception as e:
            logo_output += f"\n⚠ Logo addition error: {str(e)}\n"
            import traceback
            logo_output += traceback.format_exc()

        return jsonify(
            {
                "success": True,
                "message": "Maps generated" + (" with Zaytoon branding" if logo_success else " (logo addition may have failed)"),
                "outputs": {
                    "district_png": "/outputs/bangladesh_districts_updated_from_swaps.png",
                    "thana_png": "/outputs/bangladesh_thanas_updated_from_swaps.png",
                    "district_pdf": "/outputs/bangladesh_districts_updated_from_swaps.pdf",
                    "thana_pdf": "/outputs/bangladesh_thanas_updated_from_swaps.pdf",
                },
                "logo_applied": logo_success,
                "stdout": result.stdout + "\n\n" + logo_output,
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


@app.route("/reset", methods=["POST"])
def reset_to_original() -> Any:
    """Reset to original map state by restoring from backup CSV."""
    try:
        csv_path = BASE_DIR / "region_swapped_data.csv"
        original_csv_path = BASE_DIR / "region_swapped_data_original.csv"
        
        # Check if original backup exists
        if not original_csv_path.exists():
            return jsonify({
                "success": False,
                "message": "Original backup file not found. Please create region_swapped_data_original.csv"
            }), 404
        
        # Copy original to current
        shutil.copy2(original_csv_path, csv_path)
        
        # Regenerate maps from original data
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
        outputs_exist = district_png.exists() and thana_png.exists()
        
        if result.returncode != 0 and not outputs_exist:
            return jsonify({
                "success": False,
                "message": "Reset successful but map regeneration failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }), 500
        
        # Clean up any _with_logo duplicate files
        cleanup_output = ""
        try:
            for pattern in ["*_with_logo.pdf", "*_with_logo.png", "*_temp_logo.pdf", "*_temp_logo.png"]:
                for file in OUTPUT_DIR.glob(pattern):
                    file.unlink()
                    cleanup_output += f"Removed {file.name}\n"
        except Exception as e:
            cleanup_output += f"Cleanup warning: {str(e)}\n"
        
        # Add logos to reset maps
        logo_output = ""
        logo_success = False
        try:
            import sys
            python_exe = sys.executable
            
            pdf_script = BASE_DIR / "add_logo_to_pdfs.py"
            pdf_result = subprocess.run(
                [python_exe, str(pdf_script)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            logo_output += pdf_result.stdout
            
            png_script = BASE_DIR / "add_logo_to_pngs.py"
            png_result = subprocess.run(
                [python_exe, str(png_script)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            logo_output += "\n" + png_result.stdout
            
            logo_success = pdf_result.returncode == 0 and png_result.returncode == 0
            
        except Exception as e:
            logo_output += f"Logo warning: {str(e)}\n"
        
        return jsonify({
            "success": True,
            "message": "Maps reset to original state" + (" with branding" if logo_success else " (check logo status)"),
            "outputs": {
                "district_png": "/outputs/bangladesh_districts_updated_from_swaps.png",
                "thana_png": "/outputs/bangladesh_thanas_updated_from_swaps.png",
            },
            "logo_applied": logo_success,
            "logo_output": logo_output,
        })
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500


@app.route("/<path:filename>")
def static_files(filename: str) -> Any:
    return send_from_directory(BASE_DIR, filename)


@app.route("/favicon.ico")
def favicon() -> Response:
    return Response(status=204)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
