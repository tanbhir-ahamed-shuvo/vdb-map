#!/usr/bin/env python3
import sys
import os

# Print diagnostics
print("=" * 60)
print("STARTING FLASK SERVER WITH DIAGNOSTICS")
print("=" * 60)

# Check Python version
print(f"✓ Python Version: {sys.version}")

# Check Flask
try:
    import flask
    print(f"✓ Flask installed: {flask.__version__}")
except ImportError:
    print("✗ Flask NOT installed. Run: pip install flask")
    sys.exit(1)

# Check R
try:
    result = os.system("Rscript --version >nul 2>&1")
    if result == 0:
        print("✓ R is installed")
    else:
        print("✗ R NOT found in PATH")
except Exception as e:
    print(f"✗ R check failed: {e}")

# Check required files
from pathlib import Path
base_dir = Path(__file__).resolve().parent
required_files = [
    "app.py",
    "generate_map_from_swaps.R",
    "region-manager-interactive.html",
    "region.csv"
]

print("\nChecking files:")
for file in required_files:
    file_path = base_dir / file
    if file_path.exists():
        print(f"✓ {file}")
    else:
        print(f"✗ {file} - MISSING!")

print("\n" + "=" * 60)
print("LAUNCHING SERVER ON http://0.0.0.0:5000")
print("Access from this computer: http://localhost:5000")
print("Access from network: http://192.168.1.35:5000")
print("Press Ctrl+C to stop")
print("=" * 60 + "\n")

# Import and run app
from app import app
app.run(host="0.0.0.0", port=5000, debug=True)
