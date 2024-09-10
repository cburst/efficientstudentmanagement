#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <input_text_file>"
    exit 1
fi

input_file="$1"

# Check if the input file exists
if [ ! -f "$input_file" ]; then
    echo "Input file not found: $input_file"
    exit 1
fi

# Create a directory to store individual sentence files
output_dir="${input_file%.*}_sentences"
mkdir -p "$output_dir"

# Use Python and NLTK for sentence tokenization
python3 - <<EOF
import os
import nltk.data

# Initialize NLTK sentence tokenizer
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

# Read the input text file
with open("$input_file", 'r') as f:
    text = f.read()

# Tokenize the text into sentences
sentences = tokenizer.tokenize(text)

# Save each sentence as a separate file
for i, sentence in enumerate(sentences, start=1):
    sentence_filename = os.path.join("$output_dir", f"{os.path.splitext(os.path.basename('$input_file'))[0]}-{i:03d}.txt")
    with open(sentence_filename, 'w') as sentence_file:
        sentence_file.write(sentence)

print("Sentences have been separated and saved in the '$output_dir' directory.")
EOF

# Run analyzeText.py for each sentence output file
find "$output_dir" -type f -name "*.txt" | while read -r sentence_file; do
    base_name=$(basename "$sentence_file")
    output_csv="${sentence_file%.*}.csv"
    
    python3 analyzeText.py "$sentence_file" "$output_csv"
    
    echo "Analysis for $sentence_file completed. Result saved in $output_csv"
    
    # Check the 8th cell of the second line of the CSV file
    eighth_cell=$(awk -F ',' 'NR==2 {print $8}' "$output_csv")
    
    if [ "$eighth_cell" = "1" ]; then
        # Append "-C" to the sentence text file name
        new_sentence_filename="${sentence_file%.*}-C.${sentence_file##*.}"
    elif [ "$eighth_cell" = "0" ]; then
        # Append "-S" to the sentence text file name
        new_sentence_filename="${sentence_file%.*}-S.${sentence_file##*.}"
    else
        # Unexpected value, leave the filename unchanged
        new_sentence_filename="$sentence_file"
    fi
    
    # Rename the sentence text file if needed
    if [ "$new_sentence_filename" != "$sentence_file" ]; then
        mv "$sentence_file" "$new_sentence_filename"
        echo "Renamed $sentence_file to $new_sentence_filename"
    fi
done
