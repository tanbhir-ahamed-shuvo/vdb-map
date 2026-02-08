#!/usr/bin/env Rscript

# ============================================================================
# Generate Regional Maps from Swapped Data
# EXACT COPY of logic from create_regional_map.R that works
# ============================================================================

library(tmap)
library(sf)
library(dplyr)
library(bangladesh)

# Read the swapped region mapping CSV
region_data <- read.csv("region_swapped_data.csv", 
                        header = TRUE,
                        stringsAsFactors = FALSE)

# Clean whitespace
region_data$Region <- trimws(region_data$Region)
region_data$District <- trimws(region_data$District)
region_data$Thana <- trimws(region_data$Thana)

# Normalize names for matching (remove spaces/punctuation, lowercase)
normalize_name <- function(x) {
  x <- tolower(trimws(x))
  x <- gsub("\\s+", "", x)
  x <- gsub("[^a-z0-9]", "", x)
  x
}

# Normalize district names with common corrections
normalize_district <- function(x) {
  x <- normalize_name(x)
  x <- ifelse(x == "brahamanbaria", "brahamanbaria", x)
  x <- ifelse(x == "brahmanbari", "brahamanbaria", x)
  x <- ifelse(x == "brahmanbaria", "brahamanbaria", x)
  x <- ifelse(x == "jhalokati", "jhalokati", x)
  x <- ifelse(x == "jhalakati", "jhalokati", x)
  x <- ifelse(x == "nawabganj", "nawabganj", x)
  x <- ifelse(x == "chapainawabganj", "nawabganj", x)
  x <- ifelse(x == "narshingdi", "narsingdi", x)
  x <- ifelse(x == "netrakona", "netrakona", x)
  x <- ifelse(x == "netrokona", "netrakona", x)
  x <- ifelse(x == "khagrachari", "khagrachhari", x)
  x <- ifelse(x == "khagrachhari", "khagrachhari", x)
  x <- ifelse(x == "barishal", "barisal", x)
  x
}

# Ensure output directory
if (!dir.exists("outputs")) {
    dir.create("outputs", recursive = TRUE, showWarnings = FALSE)
}

# Get the upazila (thana) level map
upazila_map <- get_map("upazila")

# Create a mapping table for matching
upazila_map$Upazila_clean <- trimws(upazila_map$Upazila)
upazila_map$District_clean <- trimws(upazila_map$District)

region_data$Thana_clean <- trimws(region_data$Thana)
region_data$District_clean <- trimws(region_data$District)

upazila_map$Upazila_norm <- normalize_name(upazila_map$Upazila_clean)
upazila_map$District_norm <- normalize_district(upazila_map$District_clean)
region_data$Thana_norm <- normalize_name(region_data$Thana_clean)
region_data$Thana_norm <- ifelse(region_data$Thana_norm == "manohard", "manohardi", region_data$Thana_norm)
region_data$District_norm <- normalize_district(region_data$District_clean)

# Build district -> region lookup for fallback
district_region_lookup <- region_data %>%
  select(District_norm, Region) %>%
  distinct()

# Match by thana + district first
map_with_regions <- upazila_map %>%
  left_join(
    region_data %>%
      select(Region, District_norm, Thana_norm) %>%
      distinct(),
    by = c("District_norm" = "District_norm", "Upazila_norm" = "Thana_norm")
  )

# Fallback: match by thana only
if (sum(is.na(map_with_regions$Region)) > 0) {
  thana_lookup <- region_data %>%
    select(Thana_norm, Region) %>%
    distinct()
  map_with_regions$Region <- ifelse(
    is.na(map_with_regions$Region),
    thana_lookup$Region[match(map_with_regions$Upazila_norm, thana_lookup$Thana_norm)],
    map_with_regions$Region
  )
}

# Fallback: assign region by district when thana match is missing
map_with_regions$Region <- ifelse(
  is.na(map_with_regions$Region),
  district_region_lookup$Region[match(map_with_regions$District_norm,
                                      district_region_lookup$District_norm)],
  map_with_regions$Region
)

# Print matching statistics
matched <- sum(!is.na(map_with_regions$Region))
total <- nrow(map_with_regions)
cat(sprintf("\nMatching Results: %d/%d thanas matched (%.1f%%)\n", 
            matched, total, (matched/total)*100))

# Create district-level map with region colors
district_map <- get_map("district")
district_map$District_clean <- trimws(district_map$District)
district_map$District_norm <- normalize_name(district_map$District_clean)

# Adjust district labels to match Excel spellings
district_map$District_label <- district_map$District_clean
district_map$District_label <- gsub("Nawabganj", "Chapainawabganj", district_map$District_label)
district_map$District_label <- gsub("Netrakona", "Netrokona", district_map$District_label)
district_map$District_label <- gsub("Brahamanbaria", "Brahmanbari", district_map$District_label)
district_map$District_label <- gsub("Khagrachhari", "Khagrachari", district_map$District_label)
district_map$District_label <- gsub("Jhalokati", "Jhalakati", district_map$District_label)

# Labels that must always appear
highlight_labels <- c("Chapainawabganj", "Netrokona", "Barisal", "Jhalakati", "Brahmanbari")

# Create manual label points for highlighted districts
label_points <- subset(district_map, District_label %in% highlight_labels)
label_points$label <- label_points$District_label

# Compute centroids and apply small offsets to avoid overlaps
label_centroids <- sf::st_centroid(label_points)
coords <- sf::st_coordinates(label_centroids)

offsets <- data.frame(
  label = highlight_labels,
  dx = c(0.15, 0.15, 0.15, 0.15, 0.2),
  dy = c(0.15, 0.2, -0.25, -0.2, 0.25),
  stringsAsFactors = FALSE
)

offsets <- offsets[match(label_centroids$label, offsets$label), ]
new_coords <- cbind(coords[, 1] + offsets$dx, coords[, 2] + offsets$dy)

label_centroids$geometry <- sf::st_sfc(
  lapply(seq_len(nrow(new_coords)), function(i) sf::st_point(new_coords[i, ])),
  crs = sf::st_crs(label_centroids)
)

# Aggregate regions to district level
district_regions <- region_data %>%
  select(Region, District_norm) %>%
  distinct()

district_map <- left_join(district_map, district_regions, by = "District_norm")

map_districts <- tm_shape(district_map) +
  tm_polygons("Region",
              palette = "Set3",
              border.col = "black",
              lwd = 1.5,
              title = "Regions") +
  tm_shape(subset(district_map, !(District_label %in% highlight_labels))) +
  tm_text("District_label",
    size = 0.8,
    col = "black",
    fontface = "bold",
    remove.overlap = FALSE,
    shadow = TRUE) +
  tm_shape(label_centroids) +
  tm_text("label",
    size = 0.95,
    col = "black",
    fontface = "bold",
    remove.overlap = FALSE,
    shadow = TRUE) +
  tm_layout(title = "Bangladesh - 64 Districts in 10 Regions",
            title.position = c("center", "top"),
            title.size = 1.5,
            legend.outside = TRUE,
            legend.outside.position = "right",
            legend.text.size = 0.9,
            component.autoscale = FALSE,
            frame = FALSE)

tmap_save(map_districts, "outputs/bangladesh_districts_updated_from_swaps.png", width = 4200, height = 3000, dpi = 300)
cat("✓ District PNG saved\n")

# Create PDF version with smaller labels and better layout
map_districts_pdf <- tm_shape(district_map) +
  tm_polygons("Region",
              palette = "Set3",
              border.col = "black",
              lwd = 1,
              title = "Regions") +
  tm_shape(subset(district_map, !(District_label %in% highlight_labels))) +
  tm_text("District_label",
    size = 0.45,
    col = "black",
    fontface = "bold",
    remove.overlap = FALSE) +
  tm_shape(label_centroids) +
  tm_text("label",
    size = 0.5,
    col = "black",
    fontface = "bold",
    remove.overlap = FALSE) +
  tm_layout(title = "Bangladesh - 64 Districts in 10 Regions",
            title.position = c("left", "top"),
            title.size = 0.9,
            legend.outside = TRUE,
            legend.outside.position = "right",
            legend.outside.size = 0.15,
            legend.text.size = 0.6,
            legend.title.size = 0.8,
            inner.margins = c(0.02, 0.02, 0.15, 0.02),
            outer.margins = 0,
            frame = FALSE)

tmap_save(map_districts_pdf, "outputs/bangladesh_districts_updated_from_swaps.pdf", width = 10, height = 8)
cat("✓ District PDF saved\n")

# Create high-resolution PDF map with all thana names labeled
cat("\nCreating thana-level map with labels...\n")

# Split data - Dhaka district vs other districts
map_dhaka <- map_with_regions %>% filter(District == "Dhaka")
map_other <- map_with_regions %>% filter(District != "Dhaka")
district_dhaka <- district_map %>% filter(District_label == "Dhaka")
district_other <- district_map %>% filter(District_label != "Dhaka")

map_thanas_labeled <- tm_shape(map_with_regions) +
  tm_polygons("Region",
              palette = "Set3",
              border.col = "white",
              lwd = 0.3,
              title = "Regions") +
  tm_shape(district_map) +
  tm_borders(col = "black", lwd = 1.5) +
  # Other district labels - bigger
  tm_shape(district_other) +
  tm_text("District_label",
          size = 0.85,
          col = "darkblue",
          fontface = "bold",
          remove.overlap = FALSE,
          auto.placement = FALSE) +
  # Dhaka district label - same size
  tm_shape(district_dhaka) +
  tm_text("District_label",
          size = 0.6,
          col = "darkblue",
          fontface = "bold",
          remove.overlap = FALSE,
          auto.placement = FALSE) +
  # Other thanas - bigger
  tm_shape(map_other) +
  tm_text("Upazila",
          size = 0.35,
          col = "black",
          fontface = "plain",
          remove.overlap = TRUE,
          auto.placement = TRUE) +
  # Dhaka thanas - smaller with more aggressive overlap removal
  tm_shape(map_dhaka) +
  tm_text("Upazila",
          size = 0.12,
          col = "black",
          fontface = "plain",
          remove.overlap = TRUE,
          auto.placement = TRUE) +
  tm_layout(title = "Bangladesh - Districts and Thanas/Upazilas by Region",
            title.position = c("center", "top"),
            title.size = 2.5,
            legend.outside = TRUE,
            legend.outside.position = "right",
            legend.outside.size = 0.25,
            legend.text.size = 1.8,
            legend.title.size = 2.2,
            inner.margins = c(0.05, 0.02, 0.18, 0.02),
            outer.margins = c(0.02, 0, 0, 0),
            frame = FALSE)

tmap_save(map_thanas_labeled, "outputs/bangladesh_thanas_updated_from_swaps.pdf", width = 42, height = 30, dpi = 600)
cat("✓ Thana PDF saved (42×30\" @ 600 DPI)\n")

tmap_save(map_thanas_labeled, "outputs/bangladesh_thanas_updated_from_swaps.png", width = 5400, height = 3800, dpi = 300)
cat("✓ Thana PNG saved (5400×3800 px @ 300 DPI)\n")

# Print summary statistics
cat("\n=== Summary Statistics ===\n")
summary_table <- region_data %>%
  group_by(Region) %>%
  summarise(
    Districts = n_distinct(District),
    Thanas = n_distinct(Thana)
  ) %>%
  arrange(Region)

print(summary_table)

cat("\n✓ Maps created successfully!\n")
cat("  - outputs/bangladesh_districts_updated_from_swaps.png\n")
cat("  - outputs/bangladesh_districts_updated_from_swaps.pdf\n")
cat("  - outputs/bangladesh_thanas_updated_from_swaps.png\n")
cat("  - outputs/bangladesh_thanas_updated_from_swaps.pdf\n")
