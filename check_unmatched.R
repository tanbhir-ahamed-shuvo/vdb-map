library(dplyr)

# Read files
mapping <- read.csv('District_Thana_Mapping.csv', stringsAsFactors=FALSE)
region_data <- read.csv('region.csv', header=FALSE, sep='\t', col.names=c('Region', 'District', 'Thana'))

# Show structure
cat('Columns in mapping:\n')
print(colnames(mapping))
cat('\n')

# Show unmatched
unmatched <- mapping[is.na(mapping$Region), ]
cat('Number of unmatched entries:', nrow(unmatched), '\n\n')

if(nrow(unmatched) > 0) {
  cat('Unmatched entries (first 10):\n')
  col_names <- colnames(mapping)[3:4]
  print(head(unmatched[, col_names], 10))
  
  cat('\nUnique unmatched districts and thanas:\n')
  uniq_unmatched <- unique(unmatched[, col_names])
  print(uniq_unmatched)
}
