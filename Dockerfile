# ============================================================================
# Zaytoon VDB Map — Production Dockerfile
# Uses r-base so R + system GIS libraries (GDAL, GEOS, PROJ) are pre-installed
# ============================================================================
FROM r-base:4.3.3

# Install system dependencies required for R spatial packages + Python + gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libudunits2-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    libtiff-dev \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps first (layer cache)
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Install R packages — cached as a separate layer before copying project files
# Using pak for faster parallel installs
RUN Rscript -e "\
  options(repos = c(CRAN = 'https://cloud.r-project.org/')); \
  pkgs <- c('sf', 'tmap', 'dplyr', 'jsonlite'); \
  install.packages(pkgs, dependencies = TRUE, quiet = TRUE); \
  cat('R packages installed:', paste(pkgs, collapse=', '), '\n') \
"

# Install the 'bangladesh' package from its source (CRAN or GitHub)
RUN Rscript -e "\
  options(repos = c(CRAN = 'https://cloud.r-project.org/')); \
  tryCatch({ \
    install.packages('bangladesh', dependencies = TRUE, quiet = TRUE); \
    cat('bangladesh package installed from CRAN\n') \
  }, error = function(e) { \
    if (!requireNamespace('remotes', quietly = TRUE)) install.packages('remotes'); \
    remotes::install_github('ranindu/bangladesh', quiet = TRUE); \
    cat('bangladesh package installed from GitHub\n') \
  }) \
"

# Copy all project files
COPY . /app

# Create output directories and set permissions
RUN mkdir -p /app/outputs /app/geojson && \
    chmod -R 777 /app/outputs /app/geojson

# Create backup of original CSV
RUN if [ -f /app/region_swapped_data.csv ] && [ ! -f /app/region_swapped_data_original.csv ]; then \
    cp /app/region_swapped_data.csv /app/region_swapped_data_original.csv; \
    fi

# Generate initial GeoJSON files using Python generator
RUN python3 geojson_generator.py && echo "Initial GeoJSON generated" || echo "GeoJSON generation skipped"

# Expose the port Render uses
EXPOSE 10000

# Start with gunicorn — 1 worker (free tier), 120s timeout for R map generation
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "180", "--log-level", "info"]
