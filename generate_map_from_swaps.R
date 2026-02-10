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

# Define consistent colors for regions (matching full map)
region_colors <- c(
  'Barisal' = '#FF6B6B',
  'Chittagong' = '#4ECDC4',
  'Cumilla' = '#45B7D1',
  'Dhaka' = '#96CEB4',
  'Faridpur' = '#FFEAA7',
  'Khulna' = '#DDA15E',
  'Mymensingh' = '#BC6C25',
  'Rajshahi' = '#C9ADA7',
  'Rangpur' = '#9A8C98',
  'Sylhet' = '#F4A261'
)

# Add color column to map_with_regions
map_with_regions$RegionColor <- region_colors[map_with_regions$Region]

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

# Add color column to district_map
district_map$RegionColor <- region_colors[district_map$Region]

map_districts <- tm_shape(district_map) +
  tm_polygons(col = "Region",
              palette = region_colors,
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
            title.size = 1.3,
            legend.outside = TRUE,
            legend.outside.position = "right",
            legend.text.size = 0.9,
            component.autoscale = FALSE,
            frame = FALSE,
            inner.margins = c(0, 0, 0.22, 0),
            outer.margins = 0)

tmap_save(map_districts, "outputs/bangladesh_districts_updated_from_swaps.png", width = 4200, height = 3000, dpi = 300)
cat("✓ District PNG saved\n")

# Create PDF version with smaller labels and better layout
map_districts_pdf <- tm_shape(district_map) +
  tm_polygons(col = "Region",
              palette = region_colors,
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
            title.size = 0.8,
            legend.outside = TRUE,
            legend.outside.position = "right",
            legend.outside.size = 0.15,
            legend.text.size = 0.6,
            legend.title.size = 0.8,
            inner.margins = c(0.02, 0.02, 0.22, 0.02),
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
  tm_polygons(col = "Region",
              palette = region_colors,
              border.col = "white",
              lwd = 0.3,
              title = "Regions") +
  tm_shape(district_map) +
  tm_borders(col = "black", lwd = 1.5) +
  # Other district labels - bigger
  tm_shape(district_other) +
  tm_text("District_label",
      size = 0.7,
          col = "darkblue",
          fontface = "bold",
      bg.color = "white",
      bg.alpha = 0.6,
      remove.overlap = TRUE,
      auto.placement = TRUE) +
  # Dhaka district label - same size
  tm_shape(district_dhaka) +
  tm_text("District_label",
      size = 0.5,
          col = "darkblue",
          fontface = "bold",
      bg.color = "white",
      bg.alpha = 0.6,
      remove.overlap = TRUE,
      auto.placement = TRUE) +
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
      size = 0.18,
          col = "black",
          fontface = "plain",
          remove.overlap = TRUE,
          auto.placement = TRUE) +
  tm_layout(title = "Bangladesh - Districts and Thanas/Upazilas by Region",
            title.position = c("center", "top"),
            title.size = 2.2,
            legend.outside = TRUE,
            legend.outside.position = "right",
            legend.outside.size = 0.25,
            legend.text.size = 1.8,
            legend.title.size = 2.2,
            inner.margins = c(0.05, 0.02, 0.24, 0.02),
            outer.margins = 0,
            frame = FALSE)

tmap_save(map_thanas_labeled, "outputs/bangladesh_thanas_updated_from_swaps.pdf", width = 50, height = 36, dpi = 600)
cat("✓ Thana PDF saved (42×30\" @ 600 DPI)\n")

tmap_save(map_thanas_labeled, "outputs/bangladesh_thanas_updated_from_swaps.png", width = 5400, height = 3800, dpi = 300)
cat("✓ Thana PNG saved (5400×3800 px @ 300 DPI)\n")

# Create individual PDFs for each of the 10 regions
cat("\nCreating region-wise maps (10 files, one per region)...\n")
region_list <- sort(unique(map_with_regions$Region))

for (region_name in region_list) {
  region_thanas <- map_with_regions %>% filter(Region == region_name)
  region_districts <- district_map %>%
    filter(District_norm %in% unique(region_thanas$District_norm))

  # Split districts into Dhaka and others
  district_dhaka_region <- region_districts %>% filter(District_label == "Dhaka")
  district_other_region <- region_districts %>% filter(District_label != "Dhaka")

  # Split thanas into Dhaka and others
  thanas_dhaka_region <- region_thanas %>% filter(District == "Dhaka")
  thanas_other_region <- region_thanas %>% filter(District != "Dhaka")

  # Build the region map dynamically based on what's available
  region_map <- tm_shape(region_thanas) +
    tm_polygons(col = "Region",
                palette = region_colors,
                border.col = "white",
                lwd = 0.3,
                title = "Regions")

  # Add district borders
  region_map <- region_map + tm_shape(region_districts) +
    tm_borders(col = "black", lwd = 1.5)

  # Add other districts labels if they exist
  if (nrow(district_other_region) > 0) {
    region_map <- region_map + tm_shape(district_other_region) +
      tm_text("District_label",
              size = 0.65,
              col = "darkblue",
              fontface = "bold",
              bg.color = "white",
              bg.alpha = 0.7,
              remove.overlap = TRUE,
              auto.placement = TRUE)
  }

  # Add Dhaka district label if it exists in this region
  if (nrow(district_dhaka_region) > 0) {
    region_map <- region_map + tm_shape(district_dhaka_region) +
      tm_text("District_label",
              size = 0.5,
              col = "darkblue",
              fontface = "bold",
              bg.color = "white",
              bg.alpha = 0.7,
              remove.overlap = TRUE,
              auto.placement = TRUE)
  }

  # Add other thanas labels
  if (nrow(thanas_other_region) > 0) {
    region_map <- region_map + tm_shape(thanas_other_region) +
      tm_text("Upazila",
              size = 0.28,
              col = "black",
              fontface = "plain",
              remove.overlap = TRUE,
              auto.placement = TRUE)
  }

  # Add Dhaka thanas labels if they exist
  if (nrow(thanas_dhaka_region) > 0) {
    region_map <- region_map + tm_shape(thanas_dhaka_region) +
      tm_text("Upazila",
              size = 0.15,
              col = "black",
              fontface = "plain",
              remove.overlap = TRUE,
              auto.placement = TRUE)
  }

  # Add layout with margins to prevent title overlap and show legend
  region_map <- region_map + tm_layout(title = paste("Region:", region_name),
                                       title.position = c("center", "top"),
                                       title.size = 1.1,
                                       legend.outside = TRUE,
                                       legend.outside.position = "right",
                                       legend.outside.size = 0.15,
                                       legend.text.size = 0.85,
                                       legend.title.size = 1.0,
                                       frame = FALSE,
                                       inner.margins = c(0.05, 0.05, 0.22, 0.05),
                                       outer.margins = 0)

  file_name <- paste0("outputs/region_", tolower(gsub(" ", "_", region_name)), ".pdf")
  tmap_save(region_map, file_name, width = 14, height = 10, dpi = 300)
  cat(paste0("✓ ", region_name, " PDF saved (with district labels)\n"))
}

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
cat("  - outputs/region_*.pdf (10 individual region maps)\n")

# Create a color reference CSV
cat("\nCreating color reference...\n")
color_ref <- data.frame(
  Region = names(region_colors),
  HexColor = unname(region_colors),
  stringsAsFactors = FALSE
)

write.csv(color_ref, "outputs/region_colors.csv", row.names = FALSE)
cat("✓ Color reference saved to outputs/region_colors.csv\n")
cat("\n✓ All maps generated successfully!\n")

# Automatically add Zaytoon logo to all generated maps
cat("\n🎨 Adding Zaytoon logo to maps...\n")

tryCatch({
  # Add logo to PDFs
  system("python add_logo_to_pdfs.py", wait = TRUE)
  
  # Add logo to PNGs
  system("python add_logo_to_pngs.py", wait = TRUE)
  
  cat("✓ Logos added successfully!\n")
}, error = function(e) {
  cat("⚠ Warning: Could not add logos -", e$message, "\n")
  cat("  Maps generated without logo overlay\n")
})
