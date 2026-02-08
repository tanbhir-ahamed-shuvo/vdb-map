library(dplyr)

# Read current region data
region_data <- read.delim("region.csv", header=FALSE, stringsAsFactors=FALSE)
colnames(region_data) <- c("Region", "District", "Thana")

# Remove duplicate entries that were added with wrong spellings
region_data <- region_data[!(region_data$District == "Brahmanbaria" & region_data$Thana == "Brahmanbaria Sadar"), ]
region_data <- region_data[!(region_data$District == "Netrakona" & region_data$Thana == "Netrakona Sadar"), ]

# Now add with CORRECT spellings from map
correct_entries <- data.frame(
  Region = c('Cumilla', 'Sylhet'),
  District = c('Brahamanbaria', 'Netrakona'),
  Thana = c('Brahamanbaria Sadar', 'Netrakona Sadar'),
  stringsAsFactors = FALSE
)

# Combine
full_data <- rbind(region_data, correct_entries)

# Remove any remaining duplicates
full_data <- full_data %>% distinct()

# Write as TSV
write.table(full_data, file="region.csv", sep="\t", quote=FALSE, row.names=FALSE, col.names=FALSE)

cat("✓ Updated region.csv with correct spellings from map\n")
cat("✓ Brahamanbaria (with 'ha' not 'hma')\n")
cat("✓ Netrakona (with 'a' not 'o')\n")
cat("Total entries:", nrow(full_data), "\n")
