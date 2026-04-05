# ============================================================================
# Zaytoon VDB Map — Production Dockerfile
#
# Uses rocker/geospatial which pre-installs:
#   - R 4.4.x
#   - GDAL, GEOS, PROJ system libs  
#   - sf, terra, sp, ggplot2, dplyr, tmap (all pre-compiled, no build time)
#
# Only needs to add: python3, gunicorn, bangladesh R package
# ============================================================================
FROM rocker/geospatial:4.4.1

# Install Python3 + pip (rocker images are Debian-based)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install remaining R packages not bundled in rocker/geospatial
# IMPORTANT: Pin tmap to v3 — our R script uses tmap v3 API
# (tmap v4 has breaking changes: col->fill, component.autoscale removed, etc.)
#
# NOTE: The R code is kept in install_packages.R to avoid shell-escaping issues
# that occur when comments (#) and backslash continuations are mixed inside
# a Rscript -e "..." one-liner.
COPY install_packages.R /tmp/install_packages.R
RUN Rscript /tmp/install_packages.R

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (Docker layer cache)
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . /app

# Ensure output/geojson directories exist and are writable
RUN mkdir -p /app/outputs /app/geojson && \
    chmod -R 777 /app/outputs /app/geojson

# Backup original CSV if not already backed up
RUN if [ -f /app/region_swapped_data.csv ] && [ ! -f /app/region_swapped_data_original.csv ]; then \
      cp /app/region_swapped_data.csv /app/region_swapped_data_original.csv; \
    fi

# Pre-generate GeoJSON from CSV so the interactive map works on first load
RUN python3 /app/geojson_generator.py && echo "[OK] Initial GeoJSON generated" \
    || echo "[WARN] GeoJSON pre-generation skipped"

# Render uses port 10000 for Docker services
EXPOSE 10000

# Gunicorn: 1 worker (free tier limit), 180s timeout for R map generation
CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:10000", \
     "--workers", "1", \
     "--timeout", "180", \
     "--log-level", "info", \
     "--access-logfile", "-"]
