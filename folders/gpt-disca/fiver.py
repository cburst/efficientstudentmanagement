import os
import shutil
import time
import csv
import subprocess
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def main():
    # Check if the directory argument is provided
    if len(sys.argv) != 2:
        print(Fore.RED + "Usage: python script.py directory_path")
        sys.exit(1)

    file_directory = sys.argv[1]
    csv_file = f"{file_directory}.csv"
    working_directory = os.path.join(file_directory, "workingdirectory")

    # Create working directory if it doesn't exist
    os.makedirs(working_directory, exist_ok=True)

    # Create CSV file if it doesn't exist
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Filename", "Prompt1_Output", "Prompt2_Output", "Prompt3_Output"])

    while True:
        all_files_met_condition = True
        total_missing_references = 0

        # Loop through each file in the directory
        for file in os.listdir(file_directory):
            file_path = os.path.join(file_directory, file)
            if os.path.isfile(file_path) and get_file_size(file_path) > 10:
                filename = os.path.basename(file_path)
                count = count_occurrences(filename, csv_file)

                print(Fore.BLUE + f"File: {filename}, Count: {count}")  # Debugging line

                if count < 5:
                    all_files_met_condition = False
                    total_missing_references += (5 - count)
                    # Copy file to working directory if not already there
                    if not os.path.exists(os.path.join(working_directory, filename)):
                        shutil.copy(file_path, working_directory)
                else:
                    # Delete file from working directory if it's there
                    if os.path.exists(os.path.join(working_directory, filename)):
                        os.remove(os.path.join(working_directory, filename))

        print(Fore.GREEN + f"Total number of remaining missing references: {total_missing_references}")

        # Run the file processing only if any file needs processing
        if not all_files_met_condition:
            process_files(working_directory, csv_file)

        # Check if the condition is met for all files
        if all_files_met_condition:
            print(Fore.BLUE + "All files have appeared 5 times in the CSV.")
            break

        # Optional: Add a delay to avoid rapid, continuous execution
        time.sleep(5)

def count_occurrences(filename, csv_file):
    count = 0
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0] == filename:
                count += 1
    return count


def get_file_size(file):
    return os.stat(file).st_size


def process_files(working_directory, csv_file):
    print(Fore.CYAN + f"Starting to process files in {working_directory}")

    for i in os.listdir(working_directory):
        i_path = os.path.join(working_directory, i)
        if os.path.isfile(i_path) and get_file_size(i_path) > 25:
            print(Fore.CYAN + f"Processing file: {i}")

            try:
                with open(i_path, 'r', encoding="utf-8", errors="ignore") as file:
                    content = file.read().replace('\x00', '')  # Remove null bytes

                # Remove all line breaks (Windows: \r\n, Unix/Linux: \n, macOS: \r)
                content = content.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")

                print(Fore.BLUE + f"Read and cleaned content from {i}")
                timestamp_input = datetime.now().strftime('%m-%d %H:%M:%S')
                print(Fore.BLUE + f"[{timestamp_input}] (input size: {len(content)} characters)")
            except UnicodeDecodeError:
                print(Fore.RED + f"Error decoding file: {i_path}")
                continue

            # Run the `gpt` command with three prompts
            outputs = run_gpt_command(content)
            if not outputs:
                print(Fore.RED + f"Skipped logging output for file: {i}")
                continue

            # Write the outputs to the CSV file
            with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([os.path.basename(i), *outputs])
                print(Fore.BLUE + f"Logged output to CSV for {i}")

    print(Fore.CYAN + f"Finished processing all eligible files in {working_directory}")


def run_gpt_command(content):
    # Construct prompts
    prompts = [
        f"Can you perform sentiment analysis on the following paragraph, referred to as 'the sample text' in subsequent queries, by replying with any and all words contained in the sample text with POSITIVE connotations, each separated by commas, no other text whatsoever (especially no introduction or conclusion sentences, as these will disrupt the analysis process). Please end your answer with a triple colon (:::) to separate this response from subsequent responses. Here is the paragraph: {content}",
        "Can you perform sentiment analysis on 'the sample text', by replying with any and all words contained in the sample text with NEGATIVE connotations, each separated by commas, no other text whatsoever (especially no introduction or conclusion sentences, as these will disrupt the analysis process). Please end your answer with a triple colon (:::) to separate this response from subsequent responses.",
        "On a scale from -1 to +1, with -1 being completely negative and +1 being completely positive, how would you rate the sample text. reply with only numerals, a single decimal point, and a plus or minus symbol, no other characters whatsoever (especially no introduction or conclusion sentences, as these will disrupt the analysis process)."
    ]

    # Build the `gpt` command
    command = ["gpt", "--model", "gpt-4o", "Disca", "--no_stream"]
    for prompt in prompts:
        # Add each prompt to the command
        command.extend(["--prompt", prompt])

    try:
        # Run the `gpt` command with a 30-second timeout
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(Fore.RED + f"Error running gpt command: {result.stderr}")
            return None

        # Split the output by `:::`
        outputs = result.stdout.split(":::")
        return [output.strip() for output in outputs if output.strip()]

    except subprocess.TimeoutExpired:
        print(Fore.RED + f"GPT command timed out after 30 seconds.")
        return None

    except Exception as e:
        print(Fore.RED + f"Error occurred while running gpt command: {e}")
        return None


if __name__ == "__main__":
    main()