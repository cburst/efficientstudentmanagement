import os
import shutil
import sys
import subprocess
from pathlib import Path
import csv  # for CSV appending later
import pandas as pd  # for loading the output CSV into a DataFrame

def cleanup_backup_directory(backup_dir):
    """Remove files from the backup directory that do not contain 'DeepFilterNet3' in their filename."""
    for item in os.listdir(backup_dir):
        item_path = os.path.join(backup_dir, item)
        if "DeepFilterNet3" not in item:
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"Error deleting '{item_path}': {e}")

def cleanup_analysis_directory(analysis_dir):
    """Delete the analysis directory."""
    try:
        if os.path.exists(analysis_dir):
            shutil.rmtree(analysis_dir)
    except Exception as e:
        print(f"Error deleting analysis directory '{analysis_dir}': {e}")

def is_nontrivial_csv(csv_file):
    """
    Return True if the CSV file has more than just a header line.
    """
    if not os.path.exists(csv_file):
        return False

    with open(csv_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip() != ""]
    return len(lines) > 1

def process_source_directory(parent_dir, source_dir):
    """
    Process a single source directory under parent_dir, replicating the original logic.
    """
    base_dir = os.path.join(parent_dir, source_dir)
    master_path = "folders/my-voice-analysis-master"
    analysis_path = os.path.join(master_path, source_dir)
    if not os.path.exists(analysis_path):
        os.makedirs(analysis_path)

    shutil.copytree(base_dir, analysis_path, dirs_exist_ok=True)
    backup_dir = f"{source_dir}-backup"
    backup_path = os.path.join(master_path, backup_dir)
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    else:
        for item in os.listdir(backup_path):
            item_path = os.path.join(backup_path, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.unlink(item_path)

    for item in os.listdir(analysis_path):
        src_path = os.path.join(analysis_path, item)
        dst_path = os.path.join(backup_path, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

    print(f"Contents of {base_dir} moved to {backup_dir}")

    # NEW: Load the existing output CSV into a DataFrame and build a set of processed filenames.
    output_csv = f"output-files/{source_dir}-PRAAT-processed.csv"
    processed_files = set()
    if os.path.exists(output_csv):
        try:
            df = pd.read_csv(output_csv)
            # Assuming the first column holds the processed filename.
            processed_files = set(df.iloc[:, 0].str.strip().str.lower())
        except Exception as e:
            print(f"Warning: unable to load {output_csv} as a DataFrame: {e}")

    # Recursively scan analysis_path for WAV files.
    for root, dirs, files in os.walk(analysis_path):
        for file in files:
            if file.lower().endswith(".wav"):
                full_path = os.path.join(root, file)
                # Remove any leftover files that already start with "skipped_"
                if file.lower().startswith("skipped_"):
                    os.remove(full_path)
                    print(f"Removing leftover skipped file: {full_path}")
                    continue
                # Determine the expected processed filename:
                # If the file already ends with _DeepFilterNet3.wav, use its name directly.
                if file.lower().endswith("_deepfilternet3.wav"):
                    expected = file.lower()
                else:
                    base, ext = os.path.splitext(file)
                    expected = f"{base}_DeepFilterNet3.wav".lower()
                if expected in processed_files:
                    os.remove(full_path)
                    print(f"Skipping processing of redundant file: {full_path}")

    # Run the processing script
    current_dir = Path.cwd()
    os.chdir(master_path)  # Change directory to where proc.py is located
    try:
        subprocess.run([sys.executable, "proc.py", source_dir])
    finally:
        os.chdir(current_dir)

    # Handle the CSV output from proc.py.
    csv_path = os.path.join(master_path, f"{source_dir}.csv")
    if is_nontrivial_csv(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as new_file:
            new_reader = csv.reader(new_file)
            new_header = next(new_reader)
            new_rows = list(new_reader)
        if os.path.exists(output_csv):
            with open(output_csv, 'r', encoding='utf-8') as existing_file:
                existing_reader = csv.reader(existing_file)
                existing_header = next(existing_reader)
                existing_processed = {row[0].strip().lower() for row in existing_reader}
            rows_to_append = [row for row in new_rows if row[0].strip().lower() not in existing_processed]
            if rows_to_append:
                with open(output_csv, 'a', newline='', encoding='utf-8') as out_file:
                    writer = csv.writer(out_file)
                    writer.writerows(rows_to_append)
                print(f"Appended {len(rows_to_append)} new rows to {output_csv}")
            else:
                print("No new rows to append.")
        else:
            with open(output_csv, 'w', newline='', encoding='utf-8') as out_file:
                writer = csv.writer(out_file)
                writer.writerow(new_header)
                writer.writerows(new_rows)
            print(f"Created new output CSV {output_csv} with {len(new_rows)} rows")
    else:
        print(f"Skipping CSV copy for {csv_path} (empty or header-only)")

    # Move processed items back to backup.
    for item in os.listdir(analysis_path):
        src_item_path = os.path.join(analysis_path, item)
        dst_item_path = os.path.join(backup_path, item)
        shutil.move(src_item_path, dst_item_path)

    cleanup_backup_directory(backup_path)
    cleanup_analysis_directory(analysis_path)

def main():
    """
    Scans parent folders (folders/tcs, folders/ipe, folders/capstone) and processes each subdirectory.
    """
    parent_dirs = [
        "folders/tcs",
        "folders/ipe",
        "folders/capstone"
    ]
    for parent_dir in parent_dirs:
        if not os.path.isdir(parent_dir):
            continue
        for source_dir in os.listdir(parent_dir):
            subdir_path = os.path.join(parent_dir, source_dir)
            if os.path.isdir(subdir_path):
                print(f"\nProcessing: {subdir_path}")
                try:
                    process_source_directory(parent_dir, source_dir)
                except Exception as e:
                    print(f"Error while processing '{subdir_path}': {e}")

if __name__ == "__main__":
    main()