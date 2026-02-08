library(dplyr)

# Read current region data
region_data <- read.csv("region.csv", header=FALSE, sep='\t', col.names=c('Region', 'District', 'Thana'))

# Add missing district-region mappings for districts with spelling variants
# These districts exist in the map but need to be mapped to regions
missing_mappings <- data.frame(
  Region = c(
    "Barisal",         # Barisal district itself
    "Cumilla",         # Brahamanbaria (old spelling)
    "Barisal",         # Jhalokati (old spelling)
    "Chittagong",      # Khagrachhari (old spelling)
    "Dhaka",           # Narsingdi (old spelling)
    "Rajshahi",        # Nawabganj (old spelling) - but this is Chapainawabganj
    "Sylhet"           # Netrakona (old spelling)
  ),
  District = c(
    "Barisal",
    "Brahamanbaria",
    "Jhalokati",
    "Khagrachhari",
    "Narsingdi",
    "Nawabganj",
    "Netrakona"
  ),
  Thana = c(
    "Barisal Sadar",
    "Brahamanbaria Sadar",
    "Jhalokati Sadar",
    "Khagrachhari Sadar",
    "Narsingdi Sadar",
    "Nawabganj Sadar",
    "Netrakona Sadar"
  ),
  stringsAsFactors = FALSE
)

# Combine
full_data <- rbind(region_data, missing_mappings)

# Write back
write.csv(full_data, "region.csv", sep="\t", quote=FALSE, row.names=FALSE, col.names=FALSE)
cat("✓ Updated region.csv with 7 missing district mappings\n")
