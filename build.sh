#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📊 Installing R and system dependencies..."
apt-get update
apt-get install -y r-base libgdal-dev libgeos-dev libproj-dev libudunits2-dev

echo "📈 Installing R packages..."
Rscript -e "install.packages(c('sf', 'tmap', 'dplyr', 'bangladesh'), repos='https://cloud.r-project.org/')"

echo "✅ Build completed successfully!"
