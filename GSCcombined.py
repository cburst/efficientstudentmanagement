import os
import sys
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor

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

    # Run additional Python scripts in parallel
    with ThreadPoolExecutor() as executor:
        executor.submit(run_script, "GPTmulti.py", f"{d}")
        executor.submit(run_script, "L2SCA.py", f"{d}")

def run_script(script_name, suffix):
    command = [sys.executable, script_name, suffix]
    subprocess.run(command, check=True)

if __name__ == "__main__":
    main()