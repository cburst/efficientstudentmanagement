import os
import re
import hashlib
import requests
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import subprocess  # For running AppleScript

# Google API Scope
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly"
]
TOKEN_FILE = "token.pickle"  # Stores authentication token to prevent repeated logins

# 🔹 Google Sheets Info (File ID → Folder Name)
SHEETS_INFO = {
    "complexity": "https://docs.google.com/spreadsheets/d/1P0a0swlh9yuTxPKMWtu3Uzitj4o7-hDMucvZTIVDEeU/view",
    "speech-speechify": "https://docs.google.com/spreadsheets/d/1DFPJA7EQKs-Sdt3LKa2Vt_g_Lh0PJRHnhvWTgFvpxbA/view",
    "speech-elevenlabs": "https://docs.google.com/spreadsheets/d/1_ZQwqmGZ8y4-37l7JsedpMcjWC_V6mZ5KAYdtL6xW_s/view",
    "speechquality": "https://docs.google.com/spreadsheets/d/1I6zBSldFFgz8gsAK142butGHgtzW9QwGmSfNl7vr3GE/view",  # New entry for speechquality
}

# 🔹 Output Directories
OUTPUT_DIRS = {
    "complexity": "folders/complexity/",
    "speech-speechify": "folders/speech-speechify/",
    "speech-elevenlabs": "folders/speech-elevenlabs/",
    "speechquality": "folders/speechquality/",  # New folder for speechquality
}

# Ensure folders exist
for folder in OUTPUT_DIRS.values():
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(folder, "oneliners"), exist_ok=True)

# 🔹 Authenticate and Store Credentials
def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret_1046005823792-m8e8jjgv03serb4bmuvsdj1qk0bhptbp.apps.googleusercontent.com.json", SCOPES)
            creds = flow.run_local_server(port=0)  # First-time login will open a browser
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return creds

# 🔹 Extract File ID from Google Sheets URL
def extract_file_id(sheet_url):
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", sheet_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid Google Sheets URL format.")

# 🔹 Hash Functions for Efficient File Comparison
def hash_file(file_path):
    """Generate a hash for an existing file."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def hash_content(content):
    """Generate a hash for raw content (bytes)."""
    return hashlib.md5(content).hexdigest()

def hash_dataframe(df):
    """Generate a hash for a DataFrame."""
    csv_bytes = df.to_csv(index=False, header=False).encode('utf-8')
    return hashlib.md5(csv_bytes).hexdigest()

# 🔹 Send Failure Email Using AppleScript
def send_failure_email(sheet_name, error_details):
    """Sends an email via AppleScript if download fails."""
    subject = f"Google Sheet Download Failed: {sheet_name}"
    body = f"An error occurred while trying to download the Google Sheet '{sheet_name}'.\n\nError Details:\n{error_details}"
    applescript = f'''
    tell application "Mail"
        set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{body}", visible:true}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:"cburst@gmail.com"}}
            send
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])
    print(f"📧 Failure email sent for {sheet_name}")

# 🔹 Download First Sheet as CSV (With Efficiency Check)
def download_google_sheet_as_csv(sheet_id, output_path, service, credentials):
    """Downloads the first sheet as a CSV if contents have changed."""
    try:
        # Get the first sheet name dynamically
        spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        first_sheet_name = spreadsheet["sheets"][0]["properties"]["title"]

        # Read the sheet data
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=first_sheet_name
        ).execute()

        values = result.get('values', [])

        if not values:
            print(f"⚠️ No data found in {first_sheet_name}.")
            return

        # Save the data as CSV
        df = pd.DataFrame(values)
        df.to_csv(output_path, index=False, header=False)
        print(f"✅ Downloaded: {output_path}")

    except Exception as e:
        error_details = str(e)
        print(f"❌ Failed to download: {output_path}\nError: {error_details}")
        send_failure_email(sheet_id, error_details)

# 🔹 Format Timestamp
def format_timestamp(timestamp_str):
    """Convert various timestamp formats to text format: Sep25-2023-091920"""
    date_formats = [
        "%Y-%m-%d %H:%M:%S",  # Expected format (YYYY-MM-DD HH:MM:SS)
        "%m/%d/%Y %H:%M:%S",  # Google Forms format (MM/DD/YYYY HH:MM:SS)
    ]

    for date_format in date_formats:
        try:
            dt = datetime.strptime(timestamp_str, date_format)
            return dt.strftime("%b%d-%Y-%H%M%S")  # Output: Sep25-2023-091920
        except ValueError:
            continue  # Try the next format

    print(f"⚠️ Skipping invalid timestamp: {timestamp_str}")
    return None  # Skip if timestamp is invalid

# 🔹 Process Each CSV and Generate One-Liners (With Efficiency Check)
def process_csv_files():
    """Reads downloaded CSVs and creates one-line CSVs in 'oneliners' subfolder, avoiding duplicates."""
    for folder, base_dir in OUTPUT_DIRS.items():
        csv_path = os.path.join(base_dir, f"{folder}.csv")
        oneliner_folder = os.path.join(base_dir, "oneliners")

        if not os.path.exists(csv_path):
            print(f"❌ No CSV found: {csv_path}, skipping...")
            continue
        
        # Read CSV, forcing all columns to be strings to avoid conversion issues
        df = pd.read_csv(csv_path, dtype=str)
        
        # Ensure student numbers are properly formatted as strings without ".0"
        if "student_number" in df.columns:  # Adjust column name as needed
            df["student_number"] = df["student_number"].astype(str).str.replace(r'\.0$', '', regex=True)

        print(f"📂 Processing {csv_path}...")

        for _, row in df.iterrows():
            timestamp = format_timestamp(row.iloc[0])  # First column (Timestamp)
            email = row.iloc[1].replace("@", "AT")  # Second column (Email)
            name = row.iloc[2]  # Third column (Name)

            if not timestamp:
                print(f"⚠️ Skipping row with invalid timestamp: {row}")
                continue  # Skip rows with bad timestamps

            # Construct filename
            filename = f"{timestamp} - {email} - {name}.csv"
            file_path = os.path.join(oneliner_folder, filename)

            # Prepare DataFrame for this row
            row_df = row.to_frame().T

            # Clean up student numbers and other float-like text columns
            row_df = row_df.apply(lambda col: col.map(lambda x: str(x).replace('.0', '') if isinstance(x, str) else x))

            new_row_hash = hash_dataframe(row_df)

            # If file exists, compare hashes
            if os.path.exists(file_path):
                existing_file_hash = hash_file(file_path)
                if new_row_hash == existing_file_hash:
                    continue

            # Save as a one-line CSV if new or changed
            row_df.to_csv(file_path, index=False, header=False)
            print(f"✅ Created/Updated: {file_path}")

# 🔹 Main Function: Download Sheets & Process One-Liners
if __name__ == "__main__":
    credentials = authenticate()
    sheets_service = build("sheets", "v4", credentials=credentials)

    # Step 1: Download Each Google Sheet (Efficient Download)
    for folder, sheet_url in SHEETS_INFO.items():
        sheet_id = extract_file_id(sheet_url)
        output_file = os.path.join(OUTPUT_DIRS[folder], f"{folder}.csv")
        
        print(f"⬇️ Downloading {folder} from {sheet_url}...")
        download_google_sheet_as_csv(sheet_id, output_file, sheets_service, credentials)

    # Step 2: Process Each CSV & Create One-Liners (Efficient Comparison)
    process_csv_files()