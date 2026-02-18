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
from functools import wraps

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory, Response, session, redirect, url_for, render_template_string

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
LOG_FILE = BASE_DIR / "app_debug.log"
PROGRESS_FILE = BASE_DIR / ".progress"

# Global state for progress tracking
current_progress = {"regions": 0, "districts": 0, "total_regions": 10, "total_districts": 64, "status": "idle"}

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
app.secret_key = 'zaytoon-map-secret-key-change-in-production'  # Change this in production!

# Simple user credentials (in production, use a database with hashed passwords)
USERS = {
    'admin': 'zaytoon123',  # username: password
    'manager': 'map2024',
}

def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({'success': False, 'message': 'Authentication required', 'redirect': '/login'}), 401
        return f(*args, **kwargs)
    return decorated_function


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
    """Main dashboard - requires login."""
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_from_directory(BASE_DIR, "region-manager-interactive.html")


@app.route("/login", methods=["GET", "POST"])
def login() -> Any:
    """Login page."""
    log_debug(f"Login route called. Method: {request.method}")
    if request.method == "POST":
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    
    # GET request - show login page
    return send_from_directory(BASE_DIR, "login.html")


@app.route("/logout")
def logout() -> Any:
    """Logout route."""
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route("/check_auth")
def check_auth() -> Any:
    """Check if user is authenticated."""
    if 'username' in session:
        return jsonify({'authenticated': True, 'username': session['username']})
    return jsonify({'authenticated': False}), 401


@app.route("/districts")
def districts_viewer() -> Any:
    return send_from_directory(BASE_DIR, "district-viewer.html")


@app.route("/map")
def interactive_map() -> Any:
    return send_from_directory(BASE_DIR, "interactive-map.html")


@app.route("/map/fullscreen")
def interactive_map_fullscreen() -> Any:
    return send_from_directory(BASE_DIR, "interactive-map-fullscreen.html")


@app.route("/geojson/<path:filename>")
def geojson_files(filename: str) -> Any:
    return send_from_directory(BASE_DIR / "geojson", filename)


@app.route("/progress")
def get_progress() -> Any:
    """Return current map generation progress."""
    try:
        if PROGRESS_FILE.exists():
            # Try multiple times in case file is being written
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            return jsonify(data)
                    break  # Success, exit the loop
                except (IOError, json.JSONDecodeError) as e:
                    if attempt < max_attempts - 1:
                        import time
                        time.sleep(0.05)  # Brief wait before retry
                        continue
                    else:
                        log_debug(f"Progress file read error after {max_attempts} attempts: {e}")
                        raise
    except Exception as e:
        log_debug(f"Error reading progress file: {e}")
    return jsonify(current_progress)


@app.route("/generate", methods=["POST"])
@login_required
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
        
        # Initialize progress file
        progress_data = {"regions": 0, "districts": 0, "total_regions": 10, "total_districts": 64, "status": "generating"}
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f)
        
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

        # Regenerate GeoJSON for interactive map
        log_debug("Regenerating GeoJSON for interactive map")
        try:
            geojson_result = subprocess.run(
                ["Rscript", "generate_geojson.R"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            log_debug(f"GeoJSON regeneration return code: {geojson_result.returncode}")
            if geojson_result.stdout:
                log_debug(f"GeoJSON stdout: {geojson_result.stdout[:200]}")
            
            # If R fails, fall back to Python GeoJSON generator
            if geojson_result.returncode != 0:
                log_debug("R GeoJSON generation failed, trying Python fallback")
                try:
                    from geojson_generator import generate_geojson_from_csv
                    if generate_geojson_from_csv(BASE_DIR):
                        log_debug("✓ Python GeoJSON generator successful")
                    else:
                        log_debug("⚠ Python GeoJSON generator also failed")
                except Exception as py_err:
                    log_debug(f"Python GeoJSON error: {str(py_err)}")
                    
        except Exception as e:
            log_debug(f"ERROR regenerating GeoJSON via R: {str(e)}")
            # Try Python fallback
            try:
                from geojson_generator import generate_geojson_from_csv
                if generate_geojson_from_csv(BASE_DIR):
                    log_debug("✓ Python GeoJSON generator successful (fallback)")
                else:
                    log_debug("⚠ Python GeoJSON generator also failed")
            except Exception as py_err:
                log_debug(f"Python GeoJSON fallback error: {str(py_err)}")

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


@app.route("/api/export-csv", methods=["GET"])
@login_required
def export_comparison_csv() -> Any:
    """Export CSV with original vs current mapping comparison."""
    try:
        # Read original mapping
        original_file = BASE_DIR / "District_Thana_Mapping.csv"
        current_file = BASE_DIR / "region_swapped_data.csv"
        
        if not original_file.exists() or not current_file.exists():
            return jsonify({'error': 'Mapping files not found'}), 404
        
        original_df = pd.read_csv(original_file)
        current_df = pd.read_csv(current_file)
        
        # Create comparison list
        comparison_data = []
        
        # Process each original entry
        for _, orig_row in original_df.iterrows():
            # Use correct column names from District_Thana_Mapping.csv
            orig_district = orig_row.get('District (IN CSV)', '')
            orig_thana = orig_row.get('Upazila / Thana (IN CSV)', '')
            orig_region = orig_row.get('Region', '')
            
            # Find current entry in region_swapped_data.csv
            current_matches = current_df[
                (current_df['District'] == orig_district) & 
                (current_df['Thana'] == orig_thana)
            ]
            
            if not current_matches.empty:
                current_row = current_matches.iloc[0]
                current_district = current_row.get('District', orig_district)
                current_region = current_row.get('Region', orig_region)
                status = 'MOVED' if orig_district != current_district else 'UNCHANGED'
            else:
                current_district = orig_district
                current_region = orig_region
                status = 'UNCHANGED'
            
            comparison_data.append({
                'Original_Region': orig_region,
                'Original_District': orig_district,
                'Original_Thana': orig_thana,
                'Current_Region': current_region,
                'Current_District': current_district,
                'Current_Thana': orig_thana,
                'Status': status
            })
        
        # Create dataframe
        export_df = pd.DataFrame(comparison_data)
        
        # Sort by status (MOVED first, then UNCHANGED)
        export_df = export_df.sort_values(['Status', 'Original_District'], ascending=[False, True])
        
        # Generate CSV
        csv_string = export_df.to_csv(index=False)
        
        # Create response
        response = Response(csv_string, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=Bangladesh_Mapping_Original_vs_Current_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
    
    except Exception as e:
        log_debug(f"Export CSV error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route("/reset", methods=["POST"])
@login_required
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
        
        # Regenerate GeoJSON for interactive map
        try:
            geojson_result = subprocess.run(
                ["Rscript", "generate_geojson.R"],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if geojson_result.returncode != 0:
                logo_output += f"\n⚠ GeoJSON regeneration via R failed, trying Python fallback...\n"
                # Fall back to Python GeoJSON generator
                try:
                    from geojson_generator import generate_geojson_from_csv
                    if generate_geojson_from_csv(BASE_DIR):
                        logo_output += "✓ Python GeoJSON generator successful\n"
                    else:
                        logo_output += "⚠ Python GeoJSON generator failed\n"
                except Exception as py_err:
                    logo_output += f"Python GeoJSON error: {str(py_err)}\n"
            else:
                logo_output += "✓ GeoJSON regenerated via R\n"
        except Exception as e:
            logo_output += f"\nGeoJSON regeneration error: {str(e)}\nTrying Python fallback...\n"
            try:
                from geojson_generator import generate_geojson_from_csv
                if generate_geojson_from_csv(BASE_DIR):
                    logo_output += "✓ Python GeoJSON generator successful (fallback)\n"
                else:
                    logo_output += "⚠ Python GeoJSON generator failed\n"
            except Exception as py_err:
                logo_output += f"Python GeoJSON fallback error: {str(py_err)}\n"
        
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


@app.route("/districts/list")
def list_districts() -> Any:
    """List all available district maps"""
    try:
        districts_dir = OUTPUT_DIR / "districts"
        if not districts_dir.exists():
            return jsonify({"districts": [], "count": 0})
        
        district_files = sorted(districts_dir.glob("district_*.pdf"))
        districts = []
        
        for file in district_files:
            # Extract district name from filename: district_dhaka.pdf -> Dhaka
            district_name = file.stem.replace("district_", "").replace("_", " ").title()
            districts.append({
                "name": district_name,
                "filename": file.name,
                "path": f"/outputs/districts/{file.name}",
                "size": file.stat().st_size
            })
        
        return jsonify({
            "districts": districts,
            "count": len(districts)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/outputs/districts/<filename>")
def serve_district_map(filename: str) -> Any:
    """Serve district map files with no-cache headers"""
    districts_dir = OUTPUT_DIR / "districts"
    if not districts_dir.exists():
        return jsonify({"error": "Districts directory not found"}), 404
    
    response = send_from_directory(districts_dir, filename)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


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
    debug_mode = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
