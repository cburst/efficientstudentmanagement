#!/bin/bash

# Check if exactly one argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <textfile>"
    exit 1
fi

filename="$1"

# Check if the file exists and is not a directory
if [ ! -f "$filename" ]; then
    echo "Error: File does not exist or is a directory."
    exit 1
fi

# Optional: Check the file extension
if [[ ! $filename == *.txt ]]; then
    echo "Error: File is not a .txt file."
    exit 1
fi

# Optional: Check MIME type for a text file
# Requires 'file' command, available on most Unix systems
file_type=$(file --mime-type -b "$filename") # gets the MIME type
if [[ ! $file_type == text/* ]]; then
    echo "Error: File is not a text file."
    exit 1
fi

# Continue with the rest of the script
echo "Processing text file: $filename"


# filename processing begins
text=$(cat "$1")
append_text="_process"
length=$((${#filename} - 4))


# Remove the last four characters (.txt) and then append the text and .txt
filenameproc="${filename:0:length}${append_text}.txt"

        
# Save the text to the generated filename
echo "$text" > "$filenameproc"
tr '\n' ' ' < "$filenameproc" > temp.txt && mv temp.txt "$filenameproc"
sed 's/[^ -~]//g' "$filenameproc" > intermediate.txt
sed 's/[&%]//g' intermediate.txt > intermediate2.txt
sed 's/^"\(.*\)"$/\1/' intermediate2.txt > "$filenameproc"
rm intermediate.txt
rm intermediate2.txt
echo "Text extracted and saved to" "$filenameproc"

input_file="$filenameproc"

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
    
    # Check the 8th cell of the second line of the CSV file
    eighth_cell=$(awk -F ',' 'NR==2 {print $8}' "$output_csv")
    
    if [ "$eighth_cell" -gt 0 ]; then
        new_sentence_filename="${sentence_file%.*}-C.${sentence_file##*.}"
    elif [ "$eighth_cell" = "0" ]; then
        new_sentence_filename="${sentence_file%.*}-S.${sentence_file##*.}"
    else
        new_sentence_filename="$sentence_file"
    fi
    
    if [ "$new_sentence_filename" != "$sentence_file" ]; then
        mv "$sentence_file" "$new_sentence_filename"
    fi
done

# Analyze original text
python3 analyzeText.py "$input_file" "$output_dir/analysis.csv"

# Input and output file names
inputcsv_file="$output_dir/analysis.csv"
tempcsv_file="$output_dir/tempcsv_file.csv"
outputcsv_file="$output_dir/analysis_transposed.csv"

# Check if the input file exists
if [ ! -f "$inputcsv_file" ]; then
  echo "Input file not found: $inputcsv_file"
  exit 1
fi

# Use awk to transpose the data
awk -F',' '{
  for (i = 2; i <= NF; i++) {
    if (NR == 1) {
      headers[i] = $i
    } else {
      data[i, NR-1] = $i
    }
  }
} END {
  for (i = 2; i <= NF; i++) {
    printf "%s", headers[i]
    for (j = 1; j <= NR-1; j++) {
      printf ",%s", data[i, j]
    }
    printf "\n"
  }
}' "$inputcsv_file" > "$tempcsv_file"
echo "Measurement","Data" > "$outputcsv_file"
cat "$tempcsv_file" >> "$outputcsv_file"

# echo "File $outputcsv_file created."

# Find and sort the files in ascending order based on the 3-digit part
files_to_combine=($(find "$output_dir" -type f -name "*[0-9][0-9][0-9]-[CS].txt" | sort -t- -k2,2n))

# Create a temporary LaTeX document for the combined text
latex_file="${output_dir}/combined_sentences.tex"

# Initialize LaTeX document
cat << EOF > "$latex_file"
\documentclass{article}
\usepackage{xcolor}
\usepackage{csvsimple}
\usepackage{booktabs} % Required for better table styling
\begin{document}
\indent \textbf{Analysis notes:} \newline
\indent This PDF file contains your text color-coded according to L2SCA analysis of syntactic complexity.
\begin{color}{orange}Syntactically complex sentences have been highlighted in \textbf{orange}, so that you may write more sentences like these in the future. \end{color}
Try to combine sentences that are not highlighted to make them more syntactically complex. \newline
\newline
\indent \textbf{Use the following words to combine your sentences:} \newline 
\begin{color}{teal} \indent after, although, as, because, before, despite, even if, how, if, since, so that \newline
\indent though, unless, until, when, whenever, where, whereas, wherever, and while. \end{color} \newline
\newline
\indent \textbf{Contact info:} \newline
\indent \begin{color}{teal} richard.rose@yonsei.ac.kr \end{color} \newline
\newline
\newline
\indent \textbf{Your text:} \newline
\indent 
EOF

# Add each file's content to the LaTeX document with or without highlighting
for file in "${files_to_combine[@]}"; do
    content=$(cat "$file")
    if [[ $file == *"-C.txt" ]]; then
        echo "\\textcolor{orange}{${content}} " >> "$latex_file"
    else
        echo "${content} " >> "$latex_file"
    fi
done

text_with_line_breaks="\newpage 
\textbf{L2SCA Analysis}\newline \newline 
\csvautobooktabular{$outputcsv_file}"

echo "$text_with_line_breaks" >> "$latex_file"
echo "\end{document}" >> "$latex_file"

# Generate the PDF using pdflatex
if command -v pdflatex &>/dev/null; then
    pdflatex -output-directory="$output_dir" "$latex_file" > /dev/null
    append_text2="_analysis"
    filenameproc2="${filename:0:length}${append_text2}.pdf"
    mv "${output_dir}/combined_sentences.pdf" "$filenameproc2"
    echo "PDF generated."
else
    echo "pdflatex not found. Please install TeX Live or MacTeX to generate the PDF."
fi


# clean up the rest
rm -r "$output_dir"
rm "$filenameproc"
echo "File analyzed."
