#!/bin/bash

# Desired volume threshold (in dB)
desired_volume_threshold=-20.0

# Directory containing the *.wav files
if [ $# -ne 1 ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

directory="$1"

if [ ! -d "$directory" ]; then
    echo "Error: $directory is not a directory"
    exit 1
fi

# Temporary directories
temp_dir="temp_wav_files"
mkdir -p "$temp_dir"

temp2_dir="temp2_wav_files"
mkdir -p "$temp2_dir"

# Loop through each file in the input directory
for file in "$directory"/*; do
    # Check if it's a regular file (not a directory)
    if [ -f "$file" ]; then
        newname=$(echo "$file" | tr -d ' ,')
        mv "$file" "$newname"

        # Analyze the audio volume
        volume_info=$(ffmpeg -i "$newname" -filter:a volumedetect -f null /dev/null 2>&1)

        # Extract the mean volume using awk
        mean_volume=$(echo "$volume_info" | awk '/mean_volume/ {print $5}' | sed 's/dB//')

        # Calculate the required volume increase
        required_increase=$(echo "$desired_volume_threshold - $mean_volume" | bc -l)

        # Check if an increase is necessary
        if [ $(echo "$required_increase > 0" | bc -l) -eq 1 ]; then
            # Volume increase is required
            echo "Increasing volume of $newname by $required_increase dB"
            ffmpeg -i "$newname" -filter:a "volume=${required_increase}dB" "$temp2_dir/$(basename "$newname")"
        else
            # Volume is already above the threshold
            echo "Volume of $newname is already above the threshold."
            cp "$newname" "$temp2_dir/$(basename "$newname")"
        fi

        # Convert to WAV with specified sample rate
        ffmpeg -i "$temp2_dir/$(basename "$newname")" -ar 48000 "$temp_dir/$(basename "${newname%.*}").wav"



		# deep filter step
    	deepFilter "$temp_dir/$(basename "${newname%.*}").wav" -o "$directory"
    	
		# directory copy step    	
    	cp "$directory/$(basename "${newname%.*}")_DeepFilterNet3.wav" "speakingsamples/$(basename "${newname%.*}")_DeepFilterNet3.wav"
	fi
done

mv "$temp2_dir"/* "$1"
rm -r "$temp_dir"
rm -r "$temp2_dir"

# The string you want to start the CSV file with
starting_string='filename,number_of_syllables,number_of_pauses,rate_of_speech (syllables/sec original duration),articulation_rate (syllables/sec speaking duration),speaking_duration (only speaking duration without pauses),original_duration (total speaking duration with pauses),balance_ratio (speaking duration)/(original duration),f0 mean,f0 stddev,f0 median,f0 min,f0 max,f0quantile25,f0quantile75,pronunciation_posteriori_probability_score_percentage'

# Name of the CSV file
csv_file="$1.csv"

# Create or overwrite or append the CSV file with the starting string
echo "$starting_string" >> "$csv_file"

# Loop through each *_DeepFilterNet3.wav file in the directory
for wav_file in "$directory"/*_DeepFilterNet3.wav; do
    python3 test3.py "$wav_file" > yourfile.txt
    grep -oE '(= |:)[0-9]+(\.[0-9]+)?' yourfile.txt | grep -oE '[0-9]+(\.[0-9]+)?' | tr '\n' ',' | sed 's/,$/\n/' > outputfile.txt
    { echo -n "$wav_file,"; cat outputfile.txt; } > tmpfile && mv tmpfile outputfile.txt
    cat outputfile.txt >> "$csv_file"
    rm outputfile.txt
    rm yourfile.txt
done
