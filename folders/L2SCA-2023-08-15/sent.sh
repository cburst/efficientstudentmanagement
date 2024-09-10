#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <input_directory>"
    exit 1
fi

input_directory="$1"

# Check if the input directory exists
if [ ! -d "$input_directory" ]; then
    echo "Input directory not found: $input_directory"
    exit 1
fi

# Create a temporary directory to store modified TXT files
temp_dir="/tmp/temp_txt_files"
mkdir -p "$temp_dir"

# Add a space to the end of each TXT file and copy them to the temporary directory
for txt_file in "$input_directory"/*.txt; do
    output_file="$temp_dir/$(basename "$txt_file")"
    echo "$(cat "$txt_file") " > "$output_file"
done

# Create a temporary combined text file from the modified TXT files
combined_text_file="/tmp/combined_sentences.txt"
cat "$temp_dir"/*.txt | sort -t- -k2 -n > "$combined_text_file"

# Generate a PDF file from the combined text using pdflatex
pdf_output="${input_directory%/}_combined.pdf"

# Check if pdflatex is available
if command -v pdflatex &>/dev/null; then
    # Create a temporary LaTeX document with the combined text
    (
        echo "\\documentclass{article}"
        echo "\\begin{document}"
        cat "$combined_text_file"
        echo "\\end{document}"
    ) > "/tmp/combined_sentences.tex"
    
    # Compile the LaTeX document
    pdflatex "/tmp/combined_sentences.tex" > /dev/null
    
    # Clean up temporary files and directories
    rm -r "$temp_dir" "$combined_text_file" "/tmp/combined_sentences.tex"
    
    echo "PDF generated: $pdf_output"
else
    echo "pdflatex not found. Please install TeX Live or MacTeX to generate the PDF."
fi
