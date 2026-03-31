#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=== Starting build process ==="

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Checking for gunicorn..."
if python -c "import gunicorn" 2>/dev/null; then
    echo "[OK] gunicorn is installed"
else
    echo "Installing gunicorn..."
    pip install gunicorn>=21.2.0
fi

echo "Creating necessary directories..."
mkdir -p outputs
mkdir -p geojson
chmod -R 777 outputs 2>/dev/null || true
chmod -R 777 geojson 2>/dev/null || true

echo "Checking required CSV files..."
if [ -f "region_swapped_data.csv" ]; then
    echo "[OK] region_swapped_data.csv exists ($(wc -l < region_swapped_data.csv) lines)"
else
    echo "[WARN] region_swapped_data.csv missing!"
fi

if [ -f "region_swapped_data.csv" ] && [ ! -f "region_swapped_data_original.csv" ]; then
    cp region_swapped_data.csv region_swapped_data_original.csv
    echo "[OK] Created backup file region_swapped_data_original.csv"
fi

echo "Checking if R is available..."
if command -v Rscript &> /dev/null; then
    echo "[OK] R is available - installing packages..."
    Rscript -e "install.packages(c('sf', 'tmap', 'dplyr', 'bangladesh'), repos='https://cloud.r-project.org/', dependencies=TRUE)" || echo "[WARN] R package installation failed"
    echo "Generating initial GeoJSON files..."
    if [ -f "generate_geojson.R" ]; then
        Rscript generate_geojson.R || echo "[WARN] GeoJSON generation will happen on first run"
    fi
else
    echo "[WARN] R not available in this environment - map generation via R disabled"
    echo "Interactive manager, CSV export, and view features will still work"
fi

echo "=== Build completed successfully! ==="
