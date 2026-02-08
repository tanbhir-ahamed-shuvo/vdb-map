library(bangladesh)

# Get district map to see exact spellings
district_map <- get_map("district")

# Check the exact spellings of the problem districts
problem_districts <- c("Nawabganj", "Netrakona", "Netrokona", "Brahamanbaria", "Brahmanbaria", "Barisal")

cat("Exact district names in the map:\n")
for(dist in district_map$District) {
  if(grepl("Nawa|Netro|Netrak|Brahman|Barisal", dist, ignore.case=TRUE)) {
    cat("  '", dist, "'\n", sep="")
  }
}
