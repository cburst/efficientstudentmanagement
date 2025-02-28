import os
import csv
import sys
import subprocess
import shutil


def main():
    if len(sys.argv) != 2:
        print("Error: No directory name provided.")
        sys.exit(1)

    working_dir = os.getcwd()
    input_dir = os.path.join(working_dir, "input-files")
    output_dir = os.path.join(working_dir, "output-files")
    folder_dir = os.path.join(working_dir, "folders", "L2SCA-2023-08-15")
    os.makedirs(folder_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    tsv_file = os.path.join(input_dir, f"{sys.argv[1]}raw.tsv")
    if not os.path.isfile(tsv_file):
        print(f"Error: TSV file '{tsv_file}' not found.")
        sys.exit(1)

    # Create the working directory inside folders/L2SCA-2023-08-15
    individual_files_dir = os.path.join(folder_dir, sys.argv[1])
    os.makedirs(individual_files_dir, exist_ok=True)

    # Expand TSV into individual text files
    total_files_created = expand_tsv(tsv_file, individual_files_dir)
    print(f"Total files created from TSV: {total_files_created}")

    # Process individual files
    final_csv_path = os.path.join(output_dir, f"{sys.argv[1]}-L2SCA-processed.csv")
    total_files_processed = process_individual_files(individual_files_dir, folder_dir, final_csv_path)

    # Confirm the number of processed files
    print(f"Total files processed successfully: {total_files_processed}")

    # Delete the working directory
    delete_directory(individual_files_dir)

    print(f"Processing complete. Final CSV saved to {final_csv_path}")


def expand_tsv(tsv_file, output_dir):
    """Expand TSV into individual text files."""
    file_count = 0
    with open(tsv_file, newline='', encoding='utf-8') as tsv:
        reader = csv.reader(tsv, delimiter='\t')
        for row in reader:
            if len(row) < 2 or not row[0].strip() or not row[1].strip():
                print(f"Skipping invalid or empty row: {row}")
                continue
            filename = os.path.join(output_dir, f"{row[0].strip()}.txt")
            with open(filename, "w", encoding="utf-8") as txt_file:
                txt_file.write(row[1].strip())
                file_count += 1
    print(f"TSV expanded into individual text files in {output_dir}.")
    return file_count


def process_individual_files(working_dir, folder_dir, final_csv_path):
    """Process each individual file."""
    csv_writer = None
    processed_count = 0

    for filename in os.listdir(working_dir):
        file_path = os.path.join(working_dir, filename)

        # Skip "Student Number.txt" and files smaller than 20B
        if filename == "Student Number.txt" or os.path.getsize(file_path) < 20:
            print(f"Skipping unnecessary file: {filename}")
            continue

        if not filename.endswith(".txt"):
            continue

        # Copy individual text file to L2SCA-2023-08-15
        folder_text_file = os.path.join(folder_dir, filename)
        shutil.copy(file_path, folder_text_file)

        # Run analyzeText.py on the copied file
        folder_csv_file = folder_text_file.replace(".txt", ".csv")
        try:
            # Change working directory to folder_dir and use relative paths
            command = [
                sys.executable,
                "analyzeText.py",
                filename,  # Pass only the filename, not the full path
                filename.replace(".txt", ".csv"),
            ]
            subprocess.run(command, cwd=folder_dir, check=True)

            # Verify the output CSV exists
            if os.path.isfile(folder_csv_file):
                # Add content of individual CSV to final CSV
                with open(folder_csv_file, "r", newline="", encoding="utf-8") as csv_file:
                    reader = csv.reader(csv_file)
                    if csv_writer is None:
                        with open(final_csv_path, "w", newline="", encoding="utf-8") as final_csv:
                            csv_writer = csv.writer(final_csv)
                            csv_writer.writerow(next(reader))  # Write header
                    else:
                        next(reader)  # Skip header
                    with open(final_csv_path, "a", newline="", encoding="utf-8") as final_csv:
                        csv_writer = csv.writer(final_csv)
                        csv_writer.writerows(reader)
                processed_count += 1
            else:
                print(f"Error: Expected CSV output not found for {filename}")

        except subprocess.CalledProcessError as e:
            print(f"Error processing {filename}: {e}")
        except FileNotFoundError as e:
            print(f"File not found error: {e}")

        # Clean up individual text and CSV files
        if os.path.exists(folder_text_file):
            os.remove(folder_text_file)
        if os.path.exists(folder_csv_file):
            os.remove(folder_csv_file)
        print(f"Processed and cleaned up {filename}.")

    print(f"All files processed. Final CSV is at {final_csv_path}.")
    return processed_count


def delete_directory(directory_path):
    """Delete the specified directory."""
    try:
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            print(f"Deleted working directory: {directory_path}")
        else:
            print(f"Directory does not exist: {directory_path}")
    except Exception as e:
        print(f"Error deleting directory {directory_path}: {e}")


if __name__ == "__main__":
    main()