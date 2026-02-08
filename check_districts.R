library(bangladesh)
library(dplyr)

# Load the district map
district_map <- get_map("district")
cat("Districts in map:\n")
print(sort(unique(district_map$District)))
cat("\nTotal districts in map:", n_distinct(district_map$District), "\n")

# Load region data
region_data <- read.csv("region.csv", header=FALSE, sep='\t', col.names=c('Region', 'District', 'Thana'))
region_data$District <- trimws(region_data$District)
cat("\nDistricts in region.csv:\n")
print(sort(unique(region_data$District)))
cat("\nTotal districts in region.csv:", n_distinct(region_data$District), "\n")

# Find missing
map_dists <- sort(unique(district_map$District))
region_dists <- sort(unique(region_data$District))

missing_in_region <- setdiff(map_dists, region_dists)
cat("\n\nDistricts in map but NOT in region.csv:\n")
print(missing_in_region)
cat("\nCount:", length(missing_in_region), "\n")
