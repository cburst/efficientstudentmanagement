#!/bin/bash

cd ~/Downloads/L2SCA-2023-08-15/

# Download CSV file
open -a "Google Chrome" "https://docs.google.com/spreadsheets/d/1P0a0swlh9yuTxPKMWtu3Uzitj4o7-hDMucvZTIVDEeU/gviz/tq?tqx=out:csv&sheet=FormResponses1"
sleep 3
current_time=$(date +%s)
lastdig=${current_time: -6}
echo "Last 6 digits of current UNIX timestamp: $lastdig"

# Replace 'yourfile.csv' with the actual path to your CSV file
emailcsv_file="$lastdig".csv
mv ~/Downloads/data.csv "$lastdig".csv

# Check if the file exists
if [ -e "$emailcsv_file" ]; then
    # Use tail to get the last line of the CSV file
    last_line=$(tail -n 1 "$emailcsv_file" | tr -d '\n')
    echo $last_line > "$lastdig".txt
    
    # Use awk to process the last line and remove double quotes
    timestamp=$(awk -F',' '{gsub(/[^0-9]/, "", $1); print $1}' "$lastdig".txt)
    name=$(awk -F, '{ gsub(/"/, "", $3); gsub(/ /, "", $3); print $3 }' "$lastdig".txt)
	
	# Extract all text after the fifth comma
    text=$(cat "$lastdig".txt | cut -d ',' -f 6- )
	
    
    if [ -n "$timestamp" ] && [ -n "$name" ] && [ -n "$text" ]; then
        # Create a filename based on timestamp and name
        filename="$timestamp"_"$lastdig.txt"
        
        # Save the text to the generated filename
        echo "$text" > "$filename"
        sed -i '' '1s/^"//; $s/"$//' "$filename"

        echo "Text extracted and saved to $filename"
    else
        echo "No valid timestamp or text found in the CSV file."
    fi
else
    echo "CSV file not found: $emailcsv_file"
fi

input_file="$filename"

# Create a directory to store individual sentence files
output_dir="${input_file%.*}_sentences"

# run python script on filename
python3 distnoclean.py "$filename"


# Use tail to get the last line of the CSV file
    last_line=$(tail -n 2 "$emailcsv_file")
    
    # Use awk to process the last line and remove double quotes
    email=$(awk -F, '{gsub(/"/, "", $2); print $2}' "$lastdig".txt)


    if [ -n "$email" ]; then
        echo "$email" > "$output_dir"/email.txt
        # echo "Email extracted and saved to email.txt"
    else
        echo "No email found in the CSV file."
    fi
	name2=$(cat "$lastdig".txt | awk -F ',' '{gsub(/"/, "", $3); print $3}')
    
    if [ -n "$timestamp" ] && [ -n "$name" ] && [ -n "$text" ]; then
        echo "$name2" > "$output_dir"/"name.txt"
        # echo "Name saved to name.txt"
    else
        echo "No valid timestamp, name, or text found in the CSV file."
    fi

mv "$filename" "$output_dir"/"$filename"
mv "$lastdig".csv "$output_dir"/"$lastdig".csv
mv "$lastdig".txt "$output_dir"/"$lastdig".txt
echo "$timestamp","$lastdig","$email","$name2","$text" >> ~/DropboxM/confirmation.csv
mv "$output_dir" processed/"$output_dir"_processed

echo Files processed.
