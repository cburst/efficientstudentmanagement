import os
import csv
import sys
import shutil
import subprocess
from datetime import datetime

# Hardcoded working directory
BASE_DIR = os.path.expanduser("~/DropboxM/efficient student management resources")

# Change to the base directory at the start of the script
os.chdir(BASE_DIR)
print(f"Changed working directory to {os.getcwd()}")

def process_csv(csv_filename):
    # Ensure the file exists
    if not os.path.isfile(csv_filename):
        print(f"Error: File '{csv_filename}' not found.")
        return

    # Get the original working directory before changing it
    original_working_dir = os.getcwd()

    # Read the CSV file
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        row = next(reader)  # Read the first (and only) row

    # Extract necessary fields
    timestamp_raw = row[0]  # First column
    email = row[1]  # Second column
    name = row[2]  # Third column
    fifth_column_text = row[5]  # Fifth column

    # Convert timestamp format from "9/26/2023 22:17:30" to "Sep26-2023-221730"
    timestamp_obj = datetime.strptime(timestamp_raw, "%m/%d/%Y %H:%M:%S")
    timestamp_formatted = timestamp_obj.strftime("%b%d-%Y-%H%M%S")

    # Create folder with the same name as the CSV file (without .csv extension)
    folder_name = os.path.splitext(csv_filename)[0]
    os.makedirs(folder_name, exist_ok=True)

    # Paths
    timestamp_file = os.path.join(folder_name, f"{timestamp_formatted}.txt")
    destination_dir = os.path.abspath(os.path.join("folders", "L2SCA-2023-08-15"))
    destination_file = os.path.join(destination_dir, f"{timestamp_formatted}.txt")
    script_path = os.path.join(destination_dir, "distnoclean.py")
    sentences_folder = os.path.join(destination_dir, f"{timestamp_formatted}_sentences")
    target_sentences_folder = os.path.join(original_working_dir, folder_name, f"{timestamp_formatted}_sentences")
    analysis_pdf_source = os.path.join(target_sentences_folder, "analysis.pdf")
    analysis_pdf_target = os.path.join(original_working_dir, folder_name, "analysis.pdf")

    # Function to create text files with content
    def create_text_file(filename, content):
        file_path = os.path.join(folder_name, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure the directory exists
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created text file: {file_path}")

    # Create the required text files
    create_text_file("email.txt", email)
    create_text_file("name.txt", name)
    create_text_file(f"{timestamp_formatted}.txt", fifth_column_text)

    # Copy the timestamp.txt file to folders/L2SCA-2023-08-15
    os.makedirs(destination_dir, exist_ok=True)  # Ensure the destination directory exists
    shutil.copy(timestamp_file, destination_file)
    print(f"Copied {timestamp_file} to {destination_file}")

    # Change directory to folders/L2SCA-2023-08-15
    os.chdir(destination_dir)
    print(f"Changed directory to {os.getcwd()}")

    # Run distnoclean.py using its absolute path and the filename only
    try:
        subprocess.run([sys.executable, script_path, f"{timestamp_formatted}.txt"], check=True)
        print(f"Executed distnoclean.py with {timestamp_formatted}.txt")
    except subprocess.CalledProcessError as e:
        print(f"Error running distnoclean.py: {e}")
    except FileNotFoundError:
        print(f"Error: distnoclean.py not found at {script_path}")
        return  # Stop further processing if script is missing

    # Cleanup: Delete [timestamp].txt from L2SCA-2023-08-15
    try:
        os.remove(destination_file)
        print(f"Deleted {destination_file}")
    except FileNotFoundError:
        print(f"Warning: {destination_file} not found for deletion.")

    # Move [timestamp]_sentences folder back to the original folder
    if os.path.exists(sentences_folder):
        # Ensure the target directory exists
        os.makedirs(os.path.dirname(target_sentences_folder), exist_ok=True)

        if os.path.exists(target_sentences_folder):
            shutil.rmtree(target_sentences_folder)  # Remove existing destination folder to prevent nesting
            print(f"Deleted existing {target_sentences_folder} before moving the new one.")

        shutil.move(sentences_folder, target_sentences_folder)
        print(f"Moved {sentences_folder} to {target_sentences_folder}")
    else:
        print(f"Warning: {sentences_folder} not found. No sentences folder to move.")

    # Move back to the original working directory
    os.chdir(original_working_dir)
    print(f"Returned to original directory: {os.getcwd()}")

    # Copy analysis.pdf back to the original CSV folder
    if os.path.exists(analysis_pdf_source):
        os.makedirs(os.path.dirname(analysis_pdf_target), exist_ok=True)  # Ensure the target directory exists
        shutil.copy(analysis_pdf_source, analysis_pdf_target)
        print(f"Copied {analysis_pdf_source} to {analysis_pdf_target}")
    else:
        print(f"Warning: {analysis_pdf_source} not found. No analysis.pdf to copy.")

    # Run the AppleScript to send an email
    send_email_with_applescript(os.path.join(original_working_dir, folder_name))

def send_email_with_applescript(folder_path):
    """
    Generates and runs an AppleScript that sends an email using the email.txt, name.txt, and analysis.pdf 
    in the given folder path.
    """
    applescript_code = f'''
    set targetFolder to POSIX path of "{folder_path}/"

    -- Check if email.txt exists in the folder
    set emailFilePath to targetFolder & "email.txt"
    if (do shell script "[ -f " & quoted form of POSIX path of emailFilePath & " ] && echo 'true' || echo 'false'") is "true" then
        try
            set emailaddy to do shell script "cat " & quoted form of POSIX path of emailFilePath
        on error
            set emailaddy to "Error: Could not read email.txt"
        end try
    else
        set emailaddy to "Error: email.txt not found in the folder"
    end if

    -- Check if email is valid
    if emailaddy does not contain "Error" then
        -- Read the name from name.txt
        set nameFilePath to targetFolder & "name.txt"
        try
            set nameFileContent to do shell script "cat " & quoted form of POSIX path of nameFilePath
        on error
            set nameFileContent to "Name not found"
        end try

        -- Format the greeting
        set greeting to "Hi " & nameFileContent & ","

        -- Get current date
        set currentDate to current date
        set formattedDate to (currentDate as string)

        -- Path to analysis.pdf (corrected format)
        set analysisPDFPath to POSIX file (targetFolder & "analysis.pdf")

        -- Compose the email
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"Syntactic Complexity Analysis - " & formattedDate, content:greeting & return & return & "Thank you for sending your document for analysis." & return & "The document analysis file is attached for your consideration." & return & "Please let me know if you have any further questions." & return & return & "Best regards," & return & "Dr. Rose" & return, visible:true}}
            
            tell newMessage
                make new to recipient at end of to recipients with properties {{address:emailaddy}}
                
                -- Attach analysis.pdf if it exists
                if (do shell script "[ -f " & quoted form of POSIX path of analysisPDFPath & " ] && echo 'true' || echo 'false'") is "true" then
                    try
                        make new attachment with properties {{file name: analysisPDFPath}} at after last paragraph
                    on error
                        display dialog "Error attaching analysis.pdf"
                    end try
                end if
            end tell
            
            activate
            send newMessage
        end tell
    else
        display dialog "Unable to compose and send an email. Please check the email address." buttons {{"OK"}} default button "OK"
    end if
    '''

    script_path = os.path.join(folder_path, "send_email.applescript")
    with open(script_path, "w") as script_file:
        script_file.write(applescript_code)

    try:
        subprocess.run(["osascript", script_path], check=True)
        print(f"Executed AppleScript to send email from {folder_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running AppleScript: {e}")

    # Cleanup the script file
    os.remove(script_path)

# Check if the script is run with an argument
if len(sys.argv) != 2:
    print("Usage: python script.py <csv_filename>")
else:
    process_csv(sys.argv[1])