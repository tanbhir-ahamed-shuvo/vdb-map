from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import io
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory, Response

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_FILE = BASE_DIR / "app_debug.log"

# Set up logging
def log_debug(message: str) -> None:
    """Log debug message to both console and file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg, file=sys.stderr)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")
    except:
        pass

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
        log_debug("=" * 70)
        log_debug("GENERATE ENDPOINT CALLED")
        
        payload: List[Dict[str, str]] = request.get_json(force=True)
        if not isinstance(payload, list) or len(payload) == 0:
            log_debug("ERROR: No data provided")
            return jsonify({"success": False, "message": "No data provided"}), 400

        log_debug(f"Received {len(payload)} records from client")
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
            log_debug(f"Loaded {len(existing_data)} existing records from CSV")
        except FileNotFoundError:
            log_debug("WARNING: CSV file not found, starting fresh")

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
        
        log_debug(f"Prepared {len(output_rows)} records for CSV")
        
        # Write CSV maintaining header
        try:
            with csv_path.open("w", encoding="utf-8", newline="") as f:
                f.write("Region,District,Thana\n")
                for region, district, thana in output_rows:
                    f.write(f"{region},{district},{thana}\n")
            log_debug(f"✓ CSV written successfully to {csv_path}")
            
            # Verify CSV was written
            with csv_path.open("r", encoding="utf-8") as f:
                csv_content = f.read()
                line_count = len(csv_content.split("\n")) - 1
            log_debug(f"✓ CSV verification: {line_count} records (including header)")
            
        except Exception as e:
            log_debug(f"ERROR writing CSV: {str(e)}")
            return jsonify({"success": False, "message": f"CSV write error: {str(e)}"}), 500

        # Call R script
        log_debug("Calling R script: generate_map_from_swaps.R")
        cmd = ["Rscript", "generate_map_from_swaps.R"]
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
        
        log_debug(f"R script return code: {result.returncode}")
        if result.stdout:
            log_debug(f"R stdout (first 500 chars): {result.stdout[:500]}")
        if result.stderr:
            log_debug(f"R stderr (first 500 chars): {result.stderr[:500]}")

        district_png = OUTPUT_DIR / "bangladesh_districts_updated_from_swaps.png"
        thana_png = OUTPUT_DIR / "bangladesh_thanas_updated_from_swaps.png"
        district_pdf = OUTPUT_DIR / "bangladesh_districts_updated_from_swaps.pdf"
        thana_pdf = OUTPUT_DIR / "bangladesh_thanas_updated_from_swaps.pdf"

        outputs_exist = all(p.exists() for p in [district_png, thana_png, district_pdf, thana_pdf])
        log_debug(f"Map files exist: PNG={district_png.exists() and thana_png.exists()}, PDF={district_pdf.exists() and thana_pdf.exists()}")

        if result.returncode != 0 and not outputs_exist:
            log_debug(f"ERROR: R script failed and no output files exist")
            return jsonify(
                {
                    "success": False,
                    "message": "Map generation failed",
                    "stdout": result.stdout[:1000],
                    "stderr": result.stderr[:1000],
                }
            ), 500

        # Add logos to generated maps - CRITICAL for branding
        log_debug("Starting logo addition process")
        logo_output = ""
        logo_success = False
        
        try:
            python_exe = sys.executable
            log_debug(f"Using Python: {python_exe}")
            
            # Add logos to PDFs
            pdf_script = BASE_DIR / "add_logo_to_pdfs.py"
            log_debug("Calling add_logo_to_pdfs.py")
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
            log_debug(f"PDF logo return code: {pdf_result.returncode}")
            
            # Add logos to PNGs
            png_script = BASE_DIR / "add_logo_to_pngs.py"
            log_debug("Calling add_logo_to_pngs.py")
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
            log_debug(f"PNG logo return code: {png_result.returncode}")
            
            logo_success = pdf_result.returncode == 0 and png_result.returncode == 0
            log_debug(f"✓ Logo addition complete - success: {logo_success}")
            
        except subprocess.TimeoutExpired:
            log_debug("ERROR: Logo addition timed out")
            logo_output += "\n⚠ Logo addition timed out\n"
        except Exception as e:
            log_debug(f"ERROR in logo addition: {str(e)}")
            logo_output += f"\n⚠ Logo addition error: {str(e)}\n"
            import traceback
            logo_output += traceback.format_exc()

        log_debug(f"\nGeneration complete. Logo success: {logo_success}")
        log_debug("=" * 70)
        
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
                "stdout": result.stdout[-2000:] if result.stdout else "",  # Last 2000 chars
                "stderr": result.stderr[-2000:] if result.stderr else "",
            }
        )
    except Exception as exc:  # noqa: BLE001
        log_debug(f"EXCEPTION in generate: {str(exc)}")
        import traceback
        log_debug(traceback.format_exc())
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


@app.route("/debug/csv")
def debug_csv() -> Any:
    """View current CSV content for debugging"""
    try:
        csv_path = BASE_DIR / "region_swapped_data.csv"
        if not csv_path.exists():
            return jsonify({"error": "CSV file not found"}), 404
        
        with csv_path.open("r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        return jsonify({
            "file": str(csv_path),
            "total_lines": len([l for l in lines if l.strip()]),
            "content": content,
            "preview": lines[:10]  # First 10 lines
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/debug/logs")
def debug_logs() -> Any:
    """View debug logs for troubleshooting"""
    try:
        if not LOG_FILE.exists():
            return jsonify({"message": "No logs yet"}), 200
        
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        return jsonify({
            "file": str(LOG_FILE),
            "total_lines": len([l for l in lines if l.strip()]),
            "last_50_lines": lines[-50:],  # Last 50 lines
            "full_content_length": len(content)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/debug/clear")
def debug_clear() -> Any:
    """Clear debug logs"""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            return jsonify({"message": "Logs cleared"})
        else:
            return jsonify({"message": "No logs to clear"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/<path:filename>")
def static_files(filename: str) -> Any:
    return send_from_directory(BASE_DIR, filename)


@app.route("/favicon.ico")
def favicon() -> Response:
    return Response(status=204)


@app.route("/health")
def health_check() -> Any:
    """Health check endpoint for deployment diagnostics"""
    return jsonify({
        "status": "healthy",
        "service": "VDB MAP 2.1",
        "timestamp": str(Path(__file__).stat().st_mtime)
    })


@app.route("/diagnostics")
def diagnostics() -> Any:
    """Diagnostic endpoint to check system configuration"""
    import sys
    import platform
    
    diagnostics_info = {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "base_dir": str(BASE_DIR),
        "output_dir": str(OUTPUT_DIR),
        "output_dir_exists": OUTPUT_DIR.exists(),
        "output_dir_writable": os.access(OUTPUT_DIR, os.W_OK),
    }
    
    # Check for required files
    diagnostics_info["required_files"] = {
        "region_swapped_data.csv": (BASE_DIR / "region_swapped_data.csv").exists(),
        "region_swapped_data_original.csv": (BASE_DIR / "region_swapped_data_original.csv").exists(),
        "generate_map_from_swaps.R": (BASE_DIR / "generate_map_from_swaps.R").exists(),
        "zaytoon-logo.png": (BASE_DIR / "zaytoon-logo.png").exists(),
        "add_logo_to_pdfs.py": (BASE_DIR / "add_logo_to_pdfs.py").exists(),
        "add_logo_to_pngs.py": (BASE_DIR / "add_logo_to_pngs.py").exists(),
    }
    
    # Check R installation
    try:
        r_check = subprocess.run(
            ["Rscript", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        diagnostics_info["r_installed"] = r_check.returncode == 0
        diagnostics_info["r_version"] = r_check.stderr.strip() if r_check.returncode == 0 else "Not installed"
    except Exception as e:
        diagnostics_info["r_installed"] = False
        diagnostics_info["r_error"] = str(e)
    
    # Check Python packages
    try:
        from pypdf import PdfReader
        diagnostics_info["pypdf_installed"] = True
    except ImportError:
        diagnostics_info["pypdf_installed"] = False
    
    try:
        from PIL import Image
        diagnostics_info["pillow_installed"] = True
    except ImportError:
        diagnostics_info["pillow_installed"] = False
    
    try:
        from reportlab.pdfgen import canvas
        diagnostics_info["reportlab_installed"] = True
    except ImportError:
        diagnostics_info["reportlab_installed"] = False
    
    # Check output files
    output_files = list(OUTPUT_DIR.glob("*.pdf")) + list(OUTPUT_DIR.glob("*.png"))
    diagnostics_info["output_files_count"] = len(output_files)
    diagnostics_info["output_files"] = [f.name for f in output_files[:10]]  # First 10
    
    return jsonify(diagnostics_info)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
