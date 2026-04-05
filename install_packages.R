options(repos = c(CRAN = "https://cloud.r-project.org/"))

installed <- rownames(installed.packages())

# Downgrade tmap to v3 if v4 is present (rocker/geospatial ships v4)
# tmap v4 has breaking changes: col->fill, component.autoscale removed, etc.
tmap_ver <- if ("tmap" %in% installed) as.character(packageVersion("tmap")) else "0"

if (startsWith(tmap_ver, "4") || tmap_ver == "0") {
  cat("Installing tmap v3...\n")
  if (!requireNamespace("remotes", quietly = TRUE)) {
    install.packages("remotes")
  }
  remotes::install_version(
    "tmap",
    version  = "3.3-4",
    repos    = "https://cloud.r-project.org/",
    upgrade  = "never"
  )
} else {
  cat("tmap v3 already present:", tmap_ver, "\n")
}

# Install any other missing packages
pkgs_needed <- c("jsonlite", "bangladesh")
to_install  <- pkgs_needed[!pkgs_needed %in% rownames(installed.packages())]

if (length(to_install) > 0) {
  cat("Installing:", paste(to_install, collapse = ", "), "\n")
  install.packages(to_install, dependencies = TRUE, quiet = FALSE)
} else {
  cat("All required packages already installed.\n")
}
