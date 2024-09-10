import os
import pandas as pd
import argparse
import subprocess
import shutil
import time

def download_files(input_csv, output_dir):
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_csv)

    # Loop through each row in the DataFrame
    for index, row in df.iterrows():
        student_number = row['number']
        file_link = row['file']

        try:
            # Open the Google Drive file link in Chrome
            subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", file_link])

            # Wait for 10 seconds
            time.sleep(10)

            # Find the most recent file in the Downloads directory
            downloads_dir = os.path.expanduser("~/Downloads")
            files = os.listdir(downloads_dir)
            files = [f for f in files if os.path.isfile(os.path.join(downloads_dir, f))]
            files = sorted(files, key=lambda f: os.path.getmtime(os.path.join(downloads_dir, f)), reverse=True)

            if files:
                most_recent_file = files[0]
                # Construct the destination file path
                destination_file = os.path.join(output_dir, f"{student_number}_{most_recent_file.split('.')[0]}.{most_recent_file.split('.')[-1]}")
                shutil.copy2(os.path.join(downloads_dir, most_recent_file), destination_file)
            else:
                print("No files found in Downloads directory.")

        except Exception as e:
            print(f"Failed to download: {file_link}")
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and rename files from a CSV with Google Drive links")
    parser.add_argument("input_csv", help="Path to the input CSV file")
    parser.add_argument("output_dir", help="Directory to save downloaded files")
    args = parser.parse_args()

    download_files(args.input_csv, args.output_dir)
