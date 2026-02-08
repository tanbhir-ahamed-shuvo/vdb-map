FROM r-base:4.3.3

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libudunits2-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install R packages
RUN Rscript -e "install.packages(c('sf', 'tmap', 'dplyr', 'bangladesh'), repos='https://cloud.r-project.org/', dependencies=TRUE)"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start the app
CMD ["python3", "app.py"]
