library(dplyr)
mapping <- read.csv('District_Thana_Mapping.csv', stringsAsFactors=FALSE)

# Show summary by region
cat('SUMMARY BY REGION:\n')
region_summary <- mapping %>% 
  group_by(Region) %>% 
  summarise(Count = n(), .groups = 'drop') %>% 
  arrange(desc(Count))
print(region_summary)

cat('\n========================================\n')
cat('✓ COMPLETE DISTRICT-THANA-REGION MAPPING\n')
cat('========================================\n')
cat('Total mapped entries:', nrow(mapping), '\n')
cat('Total unique districts:', n_distinct(mapping[[1]]), '\n')
cat('Total unique thanas:', n_distinct(mapping[[2]]), '\n')
cat('Total regions:', n_distinct(mapping[[5]]), '\n')
