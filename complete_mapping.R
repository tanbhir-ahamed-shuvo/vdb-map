library(dplyr)

# Read all necessary data
region_data <- read.csv('region.csv', header=FALSE, sep='\t', col.names=c('Region', 'District', 'Thana'))
region_data$Region <- trimws(region_data$Region)
region_data$District <- trimws(region_data$District)
region_data$Thana <- trimws(region_data$Thana)

# Read the existing District_Thana_Mapping
existing_mapping <- read.csv('District_Thana_Mapping.csv', stringsAsFactors=FALSE)

# Clean column names
colnames(existing_mapping) <- c('District_Code', 'Thana_Code', 'District_CSV', 'Thana_CSV', 'Region')

# Remove trailing spaces
existing_mapping$District_Code <- trimws(existing_mapping$District_Code)
existing_mapping$Thana_Code <- trimws(existing_mapping$Thana_Code)
existing_mapping$District_CSV <- trimws(existing_mapping$District_CSV)
existing_mapping$Thana_CSV <- trimws(existing_mapping$Thana_CSV)
existing_mapping$Region <- trimws(existing_mapping$Region)

# Normalization functions
normalize_name <- function(x) {
  x <- tolower(trimws(x))
  x <- gsub('\\s+', '', x)
  x <- gsub('[^a-z0-9]', '', x)
  x
}

normalize_district <- function(x) {
  x <- normalize_name(x)
  x <- gsub('brahamanbaria', 'brahmanbaria', x)
  x <- gsub('brahmanbari', 'brahmanbaria', x)
  x <- gsub('jhalokati', 'jhalakati', x)
  x <- gsub('nawabganj', 'chapainawabganj', x)
  x <- gsub('narshingdi', 'narsingdi', x)
  x <- gsub('netrakona', 'netrokona', x)
  x <- gsub('khagrachari', 'khagrachhari', x)
  x <- gsub('barishal', 'barisal', x)
  x
}

# Normalize columns
existing_mapping$District_Code_norm <- normalize_district(existing_mapping$District_Code)
existing_mapping$Thana_Code_norm <- normalize_name(existing_mapping$Thana_Code)
existing_mapping$District_CSV_norm <- normalize_district(existing_mapping$District_CSV)
existing_mapping$Thana_CSV_norm <- normalize_name(existing_mapping$Thana_CSV)

region_data$District_norm <- normalize_district(region_data$District)
region_data$Thana_norm <- normalize_name(region_data$Thana)

# Create lookup tables
region_lookup_district_thana <- region_data %>%
  select(Region, District_norm, Thana_norm) %>%
  distinct()

thana_lookup <- region_data %>%
  select(Thana_norm, Region) %>%
  distinct()

district_lookup <- region_data %>%
  select(District_norm, Region) %>%
  distinct()

# Initialize Region column
existing_mapping$Region_final <- NA_character_

# Strategy 1: Match using District_Code + Thana_Code (from map)
for(i in 1:nrow(existing_mapping)) {
  match_idx <- which(
    region_lookup_district_thana$District_norm == existing_mapping$District_Code_norm[i] &
    region_lookup_district_thana$Thana_norm == existing_mapping$Thana_Code_norm[i]
  )
  if(length(match_idx) > 0) {
    existing_mapping$Region_final[i] <- region_lookup_district_thana$Region[match_idx[1]]
  }
}

# Fallback 1: Match by Thana_Code only (thana names are authoritative)
for(i in 1:nrow(existing_mapping)) {
  if(is.na(existing_mapping$Region_final[i])) {
    match_idx <- which(thana_lookup$Thana_norm == existing_mapping$Thana_Code_norm[i])
    if(length(match_idx) > 0) {
      existing_mapping$Region_final[i] <- thana_lookup$Region[match_idx[1]]
    }
  }
}

# Fallback 2: Match by District_Code (authoritative from map)
for(i in 1:nrow(existing_mapping)) {
  if(is.na(existing_mapping$Region_final[i])) {
    match_idx <- which(district_lookup$District_norm == existing_mapping$District_Code_norm[i])
    if(length(match_idx) > 0) {
      existing_mapping$Region_final[i] <- district_lookup$Region[match_idx[1]]
    }
  }
}

# Fallback 3: Manual mapping for districts that don't exist in region.csv
# Barisal district has thanas that belong to multiple districts in the region.csv
# Map these Barisal thanas based on their actual district code equivalents
barisal_thana_mapping <- data.frame(
  Thana_norm = c(
    normalize_name('Agailjhara'),
    normalize_name('Babuganj'),
    normalize_name('Bakerganj'),
    normalize_name('Banari Para'),
    normalize_name('Barisal Sadar (Kotwali)'),
    normalize_name('Gaurnadi'),
    normalize_name('Hizla'),
    normalize_name('Mehendiganj'),
    normalize_name('Muladi'),
    normalize_name('Wazirpur')
  ),
  Region = rep('Barisal', 10),
  stringsAsFactors = FALSE
)

for(i in 1:nrow(existing_mapping)) {
  if(is.na(existing_mapping$Region_final[i]) && 
     existing_mapping$District_Code_norm[i] == 'barisal') {
    match_idx <- which(barisal_thana_mapping$Thana_norm == existing_mapping$Thana_Code_norm[i])
    if(length(match_idx) > 0) {
      existing_mapping$Region_final[i] <- barisal_thana_mapping$Region[match_idx[1]]
    }
  }
}

# Create final output with original column names
final_mapping <- existing_mapping %>%
  select(
    `District (IN CODE)` = District_Code,
    `Thana (IN CODE)` = Thana_Code,
    `District (IN CSV)` = District_CSV,
    `Upazila / Thana (IN CSV)` = Thana_CSV,
    Region = Region_final
  ) %>%
  # Filter out empty rows
  filter(!(`District (IN CODE)` == '' | is.na(`District (IN CODE)`))) %>%
  arrange(`District (IN CODE)`, `Thana (IN CODE)`)

# Write output
write.csv(final_mapping, 'District_Thana_Mapping.csv', row.names=FALSE)

# Report
cat('✓ District_Thana_Mapping.csv completed with Region information\n')
cat('Total rows:', nrow(final_mapping), '\n')
cat('Matched rows:', sum(!is.na(final_mapping$Region)), '\n')
cat('Unmatched rows:', sum(is.na(final_mapping$Region)), '\n')

# Show any remaining unmatched
unmatched <- final_mapping[is.na(final_mapping$Region), ]
if(nrow(unmatched) > 0) {
  cat('\nRemaining unmatched entries:\n')
  print(unique(unmatched[, c(1, 2)]))
}
