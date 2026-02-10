#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📊 Installing R and system dependencies..."
apt-get update
apt-get install -y r-base libgdal-dev libgeos-dev libproj-dev libudunits2-dev

echo "📈 Installing R packages..."
Rscript -e "install.packages(c('sf', 'tmap', 'dplyr', 'bangladesh'), repos='https://cloud.r-project.org/', dependencies=TRUE)"

echo "🗂️ Creating necessary directories..."
mkdir -p outputs
chmod -R 755 outputs

echo "📋 Ensuring backup file exists..."
if [ -f "region_swapped_data.csv" ] && [ ! -f "region_swapped_data_original.csv" ]; then
    cp region_swapped_data.csv region_swapped_data_original.csv
    echo "✓ Created backup file"
fi

echo "✅ Build completed successfully!"
