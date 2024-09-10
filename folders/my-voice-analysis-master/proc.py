import os
import shutil
import subprocess
import sys
import re
from pathlib import Path
import logging

def sanitize_filename(filepath):
    newname = re.sub(r'[ ,]', '', str(filepath))
    shutil.move(str(filepath), newname)
    return Path(newname)

def analyze_volume(file_path):
    # Using platform-independent devnull handling
    devnull = os.devnull
    cmd = ['ffmpeg', '-i', str(file_path), '-filter:a', 'volumedetect', '-f', 'null', devnull]
    result = subprocess.run(cmd, text=True, stderr=subprocess.PIPE)
    mean_volume = re.search(r"mean_volume: ([-\d.]+) dB", result.stderr)
    return float(mean_volume.group(1)) if mean_volume else None

def adjust_volume(filepath, desired_volume_threshold, temp2_dir):
    mean_volume = analyze_volume(filepath)
    if mean_volume is None:
        return None
    required_increase = desired_volume_threshold - mean_volume
    output_file = temp2_dir / Path(filepath).name
    if required_increase > 0:
        print(f"Increasing volume of {filepath} by {required_increase} dB")
        subprocess.run(['ffmpeg', '-i', str(filepath), '-filter:a', f'volume={required_increase}dB', str(output_file)], check=True)
    else:
        print(f"Volume of {filepath} is already above the threshold.")
        shutil.copy(str(filepath), str(output_file))
    return output_file

def process_audio_files(directory, temp_dir, temp2_dir, desired_volume_threshold):
    directory = Path(directory)
    temp_dir = Path(temp_dir)
    temp2_dir = Path(temp2_dir)
    for filename in directory.iterdir():
        if filename.is_file():
            newname = sanitize_filename(filename)
            output_file = adjust_volume(newname, desired_volume_threshold, temp2_dir)
            if output_file:
                final_wav = convert_to_wav(output_file, temp_dir)
                apply_deep_filter(final_wav, directory)

def convert_to_wav(input_file, temp_dir):
    final_wav = temp_dir / f"{input_file.stem}.wav"
    subprocess.run(['ffmpeg', '-i', str(input_file), '-ar', '48000', str(final_wav)], check=True)
    return final_wav

def apply_deep_filter(wav_file, output_dir):
    subprocess.run(['deepFilter', str(wav_file), '-o', str(output_dir)], check=True)
    return wav_file.with_name(wav_file.stem + "_DeepFilterNet3.wav")

def generate_csv(directory):
    directory = Path(directory)
    try:
        script_directory = Path(__file__).parent  # Ensure this is being run as a script
    except NameError:
        script_directory = Path.cwd()  # Fallback if __file__ is not defined, e.g., running in an interpreter

    csv_file = script_directory / f"{directory.name}.csv"
    header = 'filename,number_of_syllables,number_of_pauses,rate_of_speech (syllables/sec original duration),articulation_rate (syllables/sec speaking duration),speaking_duration (only speaking duration without pauses),original_duration (total speaking duration with pauses),balance_ratio (speaking duration)/(original duration),f0 mean,f0 stddev,f0 median,f0 min,f0 max,f0quantile25,f0quantile75,pronunciation_posteriori_probability_score_percentage'
    
    try:
        with open(csv_file, 'w') as f:
            f.write(header + '\n')
    except IOError as e:
        logging.error(f"Unable to write to {csv_file}: {e}")
        return

    # Create 'speakingsamples' directory if it does not exist
    speakingsamples_directory = script_directory / 'speakingsamples'
    speakingsamples_directory.mkdir(exist_ok=True)

    for wav_file in directory.glob("*_DeepFilterNet3.wav"):
        try:
            add_audio_data_to_csv(wav_file.name, directory, csv_file, speakingsamples_directory)
        except Exception as e:
            logging.error(f"Failed to process {wav_file.name}: {e}")

    logging.info(f"CSV generation completed for {directory}")

def add_audio_data_to_csv(wav_file_name, directory, csv_file, speakingsamples_directory):
    csv_file = Path(csv_file)
    wav_file_path = directory / wav_file_name  # Use just the filename to form the path

    # Copy the wav file to 'speakingsamples' directory
    destination_path = speakingsamples_directory / wav_file_name
    shutil.copy(wav_file_path, destination_path)

    # print(f"File copied to {destination_path}")  # Diagnostic print
    print(f"Processing {wav_file_path}")  # Diagnostic print for the original file

    # Use the original wav file path for running the test3.py script
    command = [sys.executable, 'test3.py', str(wav_file_path)]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error processing {wav_file_path}: {result.stderr}")  # Log errors
        return  # Skip this file if there's an error

    # Process the output captured from stdout
    output = result.stdout
    numbers = ','.join(re.findall(r'[=:]\s*([0-9]+(?:\.[0-9]+)?)\s*(?:#.*)?', output))
    
    if not numbers:
        print(f"No data extracted for {wav_file_path}")  # Log if no data is extracted
        return

    # Open CSV file in append mode and write the data
    with open(csv_file, 'a') as f:
        f.write(f"{wav_file_name},{numbers}\n")

    print(f"Data written for {wav_file_name}")  # Confirm data write




def cleanup_temp_directories(*directories):
    for directory in directories:
        shutil.rmtree(directory, ignore_errors=True)  # ignore_errors to avoid exceptions if the directory is already removed or inaccessible

def backup_files(directory, backup_dir):
    directory = Path(directory)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)  # ensures that the backup directory is created if it does not exist

    for file in directory.iterdir():
        target_file = backup_dir / file.name
        if file.is_file():  # Ensure it's a file, not a directory
            shutil.move(str(file), str(target_file))

def main(directory):
    directory = Path(directory)
    if not directory.is_dir():
        print(f"Error: {directory} is not a directory")
        sys.exit(1)
    
    desired_volume_threshold = -20.0
    temp_dir = directory / "temp_wav_files"
    temp2_dir = directory / "temp2_wav_files"
    temp_dir.mkdir(exist_ok=True)
    temp2_dir.mkdir(exist_ok=True)

    process_audio_files(str(directory), str(temp_dir), str(temp2_dir), desired_volume_threshold)
    generate_csv(str(directory))
    cleanup_temp_directories(str(temp_dir), str(temp2_dir))
    backup_files(str(directory), str(directory) + "-backup")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory>")
        sys.exit(1)
    main(sys.argv[1])
