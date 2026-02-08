library(bangladesh)
upazila_map <- get_map('upazila')

# Find all Nawabganj entries
nawab_entries <- upazila_map[grepl('awab', upazila_map$Upazila, ignore.case=TRUE), ]
cat("\n=== All Nawabganj entries in shapefile ===\n")
for(i in 1:nrow(nawab_entries)) {
  cat(sprintf("District: %-20s Upazila: %s\n", 
              nawab_entries$District[i], 
              nawab_entries$Upazila[i]))
}

# Also check Dinajpur district specifically
dinajpur_upazilas <- upazila_map[upazila_map$District == "Dinajpur", ]
cat("\n=== All Dinajpur upazilas ===\n")
for(i in 1:nrow(dinajpur_upazilas)) {
  cat(sprintf("%s\n", dinajpur_upazilas$Upazila[i]))
}
