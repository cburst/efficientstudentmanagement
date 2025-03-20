#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def process_tsv_file(tsv_file, script_dir, input_dir):
    print(f"\nProcessing file: {tsv_file}")
    
    # Validate TSV file: must have a header and at least one non-empty row.
    try:
        with open(tsv_file, 'r', newline='') as f:
            header = f.readline()
            if not header:
                print(f"{tsv_file} is empty. Skipping.")
                return
            # Check for at least one data row.
            has_data = any(line.strip() for line in f)
            if not has_data:
                print(f"{tsv_file} has no data rows after the header. Skipping.")
                return
    except Exception as e:
        print(f"Error reading {tsv_file}: {e}")
        return

    # Copy the TSV file into the 'input-files' directory.
    dest_file = os.path.join(input_dir, os.path.basename(tsv_file))
    try:
        shutil.copy(tsv_file, dest_file)
        print(f"Copied {tsv_file} to {dest_file}")
    except Exception as e:
        print(f"Error copying {tsv_file}: {e}")
        return

    # Extract the portion of the filename preceding 'raw'.
    base_name = os.path.basename(tsv_file)
    name_without_ext, _ = os.path.splitext(base_name)
    if 'raw' in name_without_ext:
        arg_value = name_without_ext.split('raw')[0]
    else:
        print(f"Filename '{base_name}' does not contain 'raw'. Skipping.")
        return

    # Construct expected output file path (in output-files folder)
    output_filename = f"{arg_value}-L2SCA-processed.csv"
    output_filepath = os.path.join(script_dir, 'output-files', output_filename)

    # If the output file exists, compare row counts.
    if os.path.exists(output_filepath):
        try:
            with open(tsv_file, 'r', newline='') as f:
                tsv_lines = [line for line in f if line.strip()]
            tsv_row_count = len(tsv_lines)
        except Exception as e:
            print(f"Error counting rows in {tsv_file}: {e}")
            tsv_row_count = -1  # Force processing if error

        try:
            with open(output_filepath, 'r', newline='') as f:
                output_lines = [line for line in f if line.strip()]
            output_row_count = len(output_lines)
        except Exception as e:
            print(f"Error counting rows in {output_filepath}: {e}")
            output_row_count = -1

        if tsv_row_count == output_row_count and tsv_row_count != -1:
            # The following line is commented out to avoid printing skipped file messages.
            # print(f"Skipping processing for {tsv_file}: row count ({tsv_row_count}) matches output file.")
            return
        else:
            print(f"Row count mismatch (TSV: {tsv_row_count} vs Output: {output_row_count}), proceeding with processing.")

    # Build the paths to GPTmulti.py and L2SCA.py (assumed to be in the same directory as this script).
    gpt_script = os.path.join(script_dir, 'GPTmulti.py')
    l2sca_script = os.path.join(script_dir, 'L2SCA.py')

    # Execute L2SCA.py first with the extracted argument.
    try:
        subprocess.run([sys.executable, l2sca_script, arg_value], check=True)
        print(f"Executed {l2sca_script} with argument '{arg_value}'")
    except subprocess.CalledProcessError as e:
        print(f"Error running {l2sca_script} for {tsv_file}: {e}")
        return

    # Execute GPTmulti.py next with the extracted argument.
    try:
        subprocess.run([sys.executable, gpt_script, arg_value], check=True)
        print(f"Executed {gpt_script} with argument '{arg_value}'")
    except subprocess.CalledProcessError as e:
        print(f"Error running {gpt_script} for {tsv_file}: {e}")
        return

def main():
    # Get the directory where this script is located and change the working directory to it.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Create the 'input-files' and 'output-files' directories if they do not exist.
    input_dir = os.path.join(script_dir, 'input-files')
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Created directory: {input_dir}")
    
    output_dir = os.path.join(script_dir, 'output-files')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Define the base folder that contains your specific subfolders with TSV files.
    base_folder = os.path.join(script_dir, 'folders')
    if not os.path.exists(base_folder):
        print(f"Base folder '{base_folder}' does not exist. Exiting.")
        sys.exit(1)

    # List of allowed subfolder names
    allowed_dirs = ["tcw", "tcs", "ipe", "capstone", "AIDT"]

    # Loop through each allowed subfolder.
    for subfolder in allowed_dirs:
        current_folder = os.path.join(base_folder, subfolder)
        if not os.path.exists(current_folder):
            print(f"Subfolder '{current_folder}' does not exist. Skipping.")
            continue
        # Process all TSV files within the current allowed subfolder (including any nested folders).
        for root, dirs, files in os.walk(current_folder):
            for file in files:
                if file.endswith('.tsv'):
                    tsv_file = os.path.join(root, file)
                    process_tsv_file(tsv_file, script_dir, input_dir)

if __name__ == '__main__':
    main()