library(dplyr)

# Read current region data (as CSV since it was corrupted)
region_data <- read.csv("region.csv", stringsAsFactors=FALSE)
colnames(region_data) <- c("Region", "District", "Thana")

# Add missing district entries for districts with spelling variants
missing_entries <- data.frame(
  Region = c('Barisal', 'Cumilla', 'Barisal', 'Chittagong', 'Dhaka', 'Rajshahi', 'Sylhet'),
  District = c('Barisal', 'Brahmanbaria', 'Jhalokati', 'Khagrachhari', 'Narsingdi', 'Nawabganj', 'Netrakona'),
  Thana = c('Barisal Sadar', 'Brahmanbaria Sadar', 'Jhalakati Sadar', 'Khagrachhari Sadar', 'Narsingdi Sadar', 'Nawabganj Sadar', 'Netrakona Sadar'),
  stringsAsFactors = FALSE
)

# Combine
full_data <- rbind(region_data, missing_entries)

# Write as TSV (tab-separated)
write.table(full_data, file="region.csv", sep="\t", quote=FALSE, row.names=FALSE, col.names=FALSE)

cat("✓ Updated region.csv with proper TSV format\n")
cat("✓ Added 7 missing district mappings\n")
cat("Total entries:", nrow(full_data), "\n")
