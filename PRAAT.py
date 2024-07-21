import os
import shutil
import sys
import subprocess
from pathlib import Path

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

def main():
    if len(sys.argv) < 2:
        print("Usage: python PRAAT.py <source_directory>")
        sys.exit(1)

    source_dir = sys.argv[1]
    base_dir = f"input-files/{source_dir}"  # Adjusted base directory with source_dir

    # This is the base path where proc.py is located
    master_path = "folders/my-voice-analysis-master"

    # Analysis path is a specific folder under the master path for this source
    analysis_path = os.path.join(master_path, source_dir)
    if not os.path.exists(analysis_path):
        os.makedirs(analysis_path)

    # Copy source directory content, create if doesn't exist
    shutil.copytree(f"{base_dir}/", analysis_path, dirs_exist_ok=True)

    # Create the backup directory with a name based on the source directory
    backup_dir = f"{source_dir}-backup"
    backup_path = os.path.join(master_path, backup_dir)

    # Check if the backup directory already exists, and if not, create it
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    # Ensure backup directory is empty before copying
    for item in os.listdir(backup_path):
        item_path = os.path.join(backup_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.unlink(item_path)

    # Copy contents to backup directory
    for item in os.listdir(analysis_path):
        src_path = os.path.join(analysis_path, item)
        dst_path = os.path.join(backup_path, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)

    print(f"Contents of {source_dir} moved to {backup_dir}")

    # Handle remaining command line arguments (files)
    for file in sys.argv[2:]:
        file_path = os.path.join(base_dir, file)
        if os.path.exists(file_path):
            shutil.move(file_path, analysis_path)
            print(f"Moved {file} to {source_dir}/")
        else:
            print(f"File {file} not found.")

    print(f"Files {' '.join(sys.argv[2:])} moved to {source_dir}")

    # Run the processing Python script
    current_dir = Path.cwd()
    os.chdir(master_path)  # Change directory to where proc.py is located
    try:
        subprocess.run([sys.executable, "proc.py", source_dir])
    finally:
        # Always revert back to the original directory
        os.chdir(current_dir)

    # Move processed CSV and clean up
    shutil.copy(f"{master_path}/{source_dir}.csv", f"output-files/{source_dir}-PRAAT-processed.csv")
    for item in os.listdir(analysis_path):
        src_item_path = os.path.join(analysis_path, item)
        dst_item_path = os.path.join(backup_path, item)
        shutil.move(src_item_path, dst_item_path)

    # Perform cleanup in the backup directory
    cleanup_backup_directory(backup_path)
    
    # Delete the analysis directory
    cleanup_analysis_directory(analysis_path)

if __name__ == "__main__":
    main()
