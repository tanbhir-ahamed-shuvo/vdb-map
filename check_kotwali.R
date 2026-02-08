library(bangladesh)
upazila_map <- get_map('upazila')

# Find Jessore entries
jessore_entries <- upazila_map[upazila_map$District == "Jessore", ]
cat("\n=== All Jessore upazilas in shapefile ===\n")
for(i in 1:nrow(jessore_entries)) {
  cat(sprintf("%s\n", jessore_entries$Upazila[i]))
}

# Find Chittagong entries
chittagong_entries <- upazila_map[upazila_map$District == "Chittagong", ]
cat("\n=== All Chittagong upazilas in shapefile ===\n")
for(i in 1:nrow(chittagong_entries)) {
  cat(sprintf("%s\n", chittagong_entries$Upazila[i]))
}
