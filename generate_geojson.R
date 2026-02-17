suppressPackageStartupMessages({
  library(sf)
  library(dplyr)
  library(readr)
  library(stringr)
})

base_dir <- getwd()
data_dir <- file.path(base_dir, "bangladesh", "data")
output_dir <- file.path(base_dir, "geojson")

dir.create(output_dir, showWarnings = FALSE, recursive = TRUE)

load(file.path(data_dir, "map_district.rda"))
load(file.path(data_dir, "map_upazila.rda"))

# Load CURRENT mapping (user modifications)
mapping_current <- read_csv(file.path(base_dir, "region_swapped_data.csv"), show_col_types = FALSE) %>%
  transmute(
    region = Region,
    district = District,
    thana = Thana,
    thana_norm = str_to_lower(str_squish(Thana))
  )

mapping_raw <- read_csv(file.path(base_dir, "District_Thana_Mapping.csv"), show_col_types = FALSE)

mapping_csv <- mapping_raw %>%
  transmute(
    region = Region,
    district = `District (IN CSV)`,
    thana = `Upazila / Thana (IN CSV)`,
    thana_norm = str_to_lower(str_squish(`Upazila / Thana (IN CSV)`))
  )

mapping_code <- mapping_raw %>%
  transmute(
    region = Region,
    district = `District (IN CODE)`,
    thana = `Thana (IN CODE)`,
    thana_norm = str_to_lower(str_squish(`Thana (IN CODE)`))
  )

# Combine: prioritize current, then csv, then code - deduplicate by district+thana combination
mapping <- bind_rows(mapping_current, mapping_csv, mapping_code) %>%
  mutate(
    district = str_squish(as.character(district)),
    thana = str_squish(as.character(thana)),
    district_norm = str_to_lower(district)
  ) %>%
  distinct(district_norm, thana_norm, .keep_all = TRUE)  # Keep unique district+thana combinations

# District-level mapping: ONLY from current CSV to ensure user changes take priority
district_region_mapping <- mapping_current %>%
  mutate(
    district = str_squish(as.character(district)),
    district_norm = str_to_lower(district)
  ) %>%
  distinct(district_norm, region, district)

# Districts with region assignment
map_district <- map_district %>%
  mutate(
    District = as.character(District),
    district_norm = str_to_lower(str_squish(District)),
    # Fix spelling mismatches between .rda file and CSV
    district_norm = case_when(
      district_norm == "brahamanbaria" ~ "brahmanbaria",
      district_norm == "jhalokati" ~ "jhalakati",
      district_norm == "khagrachhari" ~ "khagrachari",
      district_norm == "nawabganj" ~ "chapainawabganj",
      district_norm == "netrakona" ~ "netrokona",
      TRUE ~ district_norm
    )
  ) %>%
  left_join(
    district_region_mapping,
    by = "district_norm"
  ) %>%
  mutate(
    region = if_else(is.na(region), "Unknown", region),
    district = if_else(is.na(district), District, district)
  ) %>%
  select(region, district, geometry)

# Regions dissolved from districts
regions <- map_district %>%
  group_by(region) %>%
  summarize(geometry = st_union(geometry), .groups = "drop")

# Thanas (upazilas) with region + district assignment
district_lookup <- mapping %>%
  distinct(district_norm, region, district)

map_upazila <- map_upazila %>%
  mutate(
    District = as.character(District),
    Upazila = as.character(Upazila),
    district_norm = str_to_lower(str_squish(District)),
    thana_norm = str_to_lower(str_squish(Upazila)),
    # Fix spelling mismatches between .rda file and CSV
    district_norm = case_when(
      district_norm == "brahamanbaria" ~ "brahmanbaria",
      district_norm == "jhalokati" ~ "jhalakati",
      district_norm == "khagrachhari" ~ "khagrachari",
      district_norm == "nawabganj" ~ "chapainawabganj",
      district_norm == "netrakona" ~ "netrokona",
      TRUE ~ district_norm
    )
  ) %>%
  left_join(
    mapping %>% distinct(district_norm, thana_norm, region, district, thana),
    by = c("district_norm", "thana_norm")
  ) %>%
  left_join(
    district_lookup,
    by = "district_norm",
    suffix = c("", "_district")
  ) %>%
  mutate(
    region = if_else(is.na(region), region_district, region),
    district = if_else(is.na(district), district_district, district),
    region = if_else(is.na(region), "Unknown", region),
    district = if_else(is.na(district), District, district),
    thana = if_else(is.na(thana), Upazila, thana)
  ) %>%
  select(region, district, thana, geometry)

st_write(regions, file.path(output_dir, "regions.geojson"), delete_dsn = TRUE, quiet = TRUE)
st_write(map_district, file.path(output_dir, "districts.geojson"), delete_dsn = TRUE, quiet = TRUE)
st_write(map_upazila, file.path(output_dir, "thanas.geojson"), delete_dsn = TRUE, quiet = TRUE)

cat("GeoJSON generated in", output_dir, "\n")
