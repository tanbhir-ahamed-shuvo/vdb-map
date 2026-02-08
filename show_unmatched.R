library(dplyr)

# Read files
mapping <- read.csv('District_Thana_Mapping.csv', stringsAsFactors=FALSE)

# Get unmatched rows
unmatched <- mapping[is.na(mapping$Region), ]
cat('Unmatched entries:\n')
print(unmatched[, 1:4])
