import os
import time
import shutil
import re
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import gspread
from gspread_dataframe import get_as_dataframe
import pickle

# --------------------------- Google API Config ---------------------------- #
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
TOKEN_FILE = "token.pickle"

# ✅ Google Sheet URLs
SHEET_URLS = {
    "tcs": "https://docs.google.com/spreadsheets/d/195UvQwRf-h0GkNTmcNHdBMgh183d-8Q-zuS0UXzcCo8/view",
    "tcw": "https://docs.google.com/spreadsheets/d/1xralKSIVO78KzvidvNRJUdGrOz84D6cheFDUrvHldFM/view",
    "capstone": "https://docs.google.com/spreadsheets/d/1E9vFafUcwhuvBzwnMZVZ2gDG8yLDjz_Txc4YW0nTF6s/view",
    "ipe": "https://docs.google.com/spreadsheets/d/1nYStUiwAzqrvHfGRZQ5OquEZ3_8g-LFe02TPmSbHNL4/view"
}

# ---------------------- Google API Authentication ----------------------- #
def authenticate():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return creds

# ------------------------- Utility Functions ---------------------------- #
def dataframes_equal(df1, df2):
    """Compare two DataFrames after normalizing them."""
    # Normalize data: fill NaNs, convert all values to string, and reset index
    df1_normalized = df1.fillna('').astype(str).reset_index(drop=True)
    df2_normalized = df2.fillna('').astype(str).reset_index(drop=True)
    
    # Ensure all column names are strings to avoid mixed-type comparisons
    df1_normalized.columns = df1_normalized.columns.astype(str)
    df2_normalized.columns = df2_normalized.columns.astype(str)
    
    # Sort columns alphabetically using their string representation
    df1_sorted = df1_normalized.reindex(sorted(df1_normalized.columns), axis=1)
    df2_sorted = df2_normalized.reindex(sorted(df2_normalized.columns), axis=1)
    
    return df1_sorted.equals(df2_sorted)

# ----------------------- Download & Process Sheets ---------------------- #


def download_google_sheets():
    creds = authenticate()
    gc = gspread.authorize(creds)

    for class_name, sheet_url in SHEET_URLS.items():
        print(f"📋 Processing class: {class_name}")

        output_dir = f"folders/{class_name}/"
        os.makedirs(output_dir, exist_ok=True)

        temp_dir = os.path.join(output_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            spreadsheet = gc.open_by_url(sheet_url)
        except Exception as e:
            print(f"❌ Error accessing Google Sheet for {class_name}: {e}")
            continue

        download_count = 0

        for worksheet in spreadsheet.worksheets():
            if worksheet.title.lower().endswith("raw"):
                time.sleep(1.5)  # Delay to prevent hitting API rate limits

                try:
                    df = get_as_dataframe(worksheet, evaluate_formulas=True)
                    df.dropna(how='all', inplace=True)

                    # 🛠️ Normalize data: Convert all columns to strings
                    df_output = df.astype(str)  # Convert all values to string
                    df_output = df_output.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))  # Strip whitespace
                    df_output.replace(r'\.0$', '', regex=True, inplace=True)  # Remove trailing ".0"

                    second_col = df_output.iloc[:, 1].fillna("").astype(str).str.strip()
                    df_output = df_output[(second_col != "") & (second_col.str.lower() != "nan")]

                    tsv_name = f"{class_name}-{worksheet.title}.tsv"
                    tsv_path = os.path.join(output_dir, tsv_name)
                    temp_tsv_path = os.path.join(temp_dir, f"temp_{tsv_name}")

                    if os.path.exists(tsv_path):
                        existing_df = pd.read_csv(tsv_path, sep="\t", dtype=str)
                        if dataframes_equal(df_output, existing_df):
                            print(f"⚡ Skipped (No Changes): {tsv_name}")
                            continue

                    df_output.to_csv(temp_tsv_path, sep="\t", index=False)
                    os.replace(temp_tsv_path, tsv_path)

                    download_count += 1
                    print(f"⬇️ Downloaded (Overwritten): {tsv_path}")

                except Exception as e:
                    print(f"❌ Error processing worksheet '{worksheet.title}' for {class_name}: {e}")

        if download_count == 0:
            print(f"⚠️ No new 'raw' sheets downloaded for {class_name}.")
        else:
            print(f"🎉 Successfully downloaded {download_count} updated 'raw' sheets for {class_name}.")

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🗑️ Temporary folder '{temp_dir}' deleted.")

# ---------------------------- Run the Script ---------------------------- #
if __name__ == "__main__":
    download_google_sheets()