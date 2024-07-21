import os
import shutil
import sys
import subprocess
import csv
import time

def main():
    if len(sys.argv) != 2:
        print("Error: No directory name provided.")
        sys.exit(1)
    
    d = sys.argv[1]
    base_dir = os.getcwd()

    # Define the path to the input-files directory
    input_files_dir = os.path.join(base_dir, "input-files")

    tsv_file = os.path.join(input_files_dir, f"{d}raw.tsv")
    if not os.path.isfile(tsv_file):
        print(f"Error: TSV file '{tsv_file}' not found in {input_files_dir}.")
        sys.exit(1)

    destination_folder = os.path.join(base_dir, "folders", "L2SCA-2023-08-15")
    os.makedirs(destination_folder, exist_ok=True)

    destination_file = os.path.join(destination_folder, os.path.basename(tsv_file))
    shutil.copy(tsv_file, destination_file)
    print(f"Copied '{tsv_file}' to '{destination_file}'.")

    subdirectory_path = os.path.join(destination_folder, d)
    os.makedirs(subdirectory_path, exist_ok=True)

    subfolder_destination_file = os.path.join(subdirectory_path, os.path.basename(tsv_file))
    shutil.copy(destination_file, subfolder_destination_file)
    print(f"Copied to subfolder: '{subfolder_destination_file}'.")

    process_tsv_with_python(subfolder_destination_file)

    if os.path.exists("Student Number.txt"):
        os.remove("Student Number.txt")
    os.remove(subfolder_destination_file)
    
    # Run Python analysis script
    analyzefolder_path = os.path.join(destination_folder, "analyzefolder.py")
    command = [sys.executable, analyzefolder_path, d, f"{d}.csv"]
    subprocess.run(command, cwd=destination_folder, check=True)

    # Check if the CSV file exists and is not empty
    final_csv_source = os.path.join(destination_folder, f"{d}.csv")
    if not os.path.isfile(final_csv_source) or os.path.getsize(final_csv_source) == 0:
        print(f"Error: CSV file '{final_csv_source}' not found or is empty.")
        sys.exit(1)

    # Optional: Wait briefly to ensure file I/O operations have settled - can adjust based on need
    time.sleep(1)

    # Copy the final CSV to the 'output-files' directory
    final_csv_destination = os.path.join(base_dir, "output-files", f"{d}-L2SCA-processed.csv")
    os.makedirs(os.path.dirname(final_csv_destination), exist_ok=True)
    shutil.copy(final_csv_source, final_csv_destination)
    print(f"Final CSV copied to '{final_csv_destination}'.")

    # Cleanup: delete the {d} directory and the TSV file from the L2SCA folder
    cleanup(subdirectory_path, destination_file)

def process_tsv_with_python(tsv_file):
    base_dir = os.getcwd()  # Ensure base directory is set
    destination_folder = os.path.join(base_dir, "folders", "L2SCA-2023-08-15")
    subdirectory_path = os.path.join(destination_folder, os.path.basename(tsv_file).replace("raw.tsv", ""))  # Assuming tsv_file naming follows a specific pattern
    os.makedirs(subdirectory_path, exist_ok=True)  # Make sure the subdirectory exists

    with open(tsv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        output_files = {}
        try:
            for row in reader:
                if row[0] == "Student Number":
                    continue  # Skip unwanted header or specific row
                file_name = os.path.join(subdirectory_path, f"{row[0]}.txt")
                if file_name not in output_files:
                    output_files[file_name] = open(file_name, 'w', encoding='utf-8')
                output_files[file_name].write(row[1] + '\n')
        finally:
            for f in output_files.values():
                f.close()

def cleanup(directory, tsv_file):
    """Delete the specified directory and TSV file."""
    try:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        if os.path.exists(tsv_file):
            os.remove(tsv_file)
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    main()
