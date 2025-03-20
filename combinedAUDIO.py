import os
import argparse
import pandas as pd

##############################
# Data Collection Functions  #
##############################

def process_subfolder(subfolder):
    """
    Processes a single subfolder in an oneliners folder.
    Reads studentnumber.txt, computes averages (columns 4-8) from sentence_level_results.csv,
    and does the same for the modelaudio subfolder (if available).
    Returns a row with:
      [student_number, student_accuracy, student_prosody, student_pronunciation, student_completeness, student_fluency,
       model_accuracy, model_prosody, model_pronunciation, model_completeness, model_fluency]
    """
    student_number_file = os.path.join(subfolder, 'studentnumber.txt')
    student_csv_file = os.path.join(subfolder, 'sentence_level_results.csv')
    model_csv_file = os.path.join(subfolder, 'modelaudio', 'sentence_level_results.csv')
    
    # Check essential student files
    if not os.path.exists(student_number_file):
        print(f"Warning: {student_number_file} does not exist. Skipping {subfolder}")
        return None
    if not os.path.exists(student_csv_file):
        print(f"Warning: {student_csv_file} does not exist. Skipping {subfolder}")
        return None
    
    with open(student_number_file, 'r') as f:
        student_number = f.read().strip()
    
    # Compute student averages (columns 4-8; zero-indexed 3:8)
    try:
        df_student = pd.read_csv(student_csv_file)
        student_means = df_student.iloc[:, 3:8].mean()
    except Exception as e:
        print(f"Error processing {student_csv_file}: {e}")
        return None
    
    # Process model CSV if available; otherwise, leave as blanks
    if os.path.exists(model_csv_file):
        try:
            df_model = pd.read_csv(model_csv_file)
            model_means = df_model.iloc[:, 3:8].mean()
        except Exception as e:
            print(f"Error processing {model_csv_file}: {e}")
            model_means = [None] * 5
    else:
        print(f"Warning: {model_csv_file} does not exist. Leaving model values blank for {subfolder}")
        model_means = [None] * 5
    
    row = [student_number]
    row.extend(student_means.tolist())
    row.extend(model_means.tolist() if not isinstance(model_means, list) else model_means)
    return row

def process_oneliners_folder(oneliners_folder):
    """
    Processes all valid subfolders inside an oneliners folder.
    Returns a list of rows for which data could be collected.
    """
    rows = []
    for item in os.listdir(oneliners_folder):
        candidate = os.path.join(oneliners_folder, item)
        if os.path.isdir(candidate):
            row = process_subfolder(candidate)
            if row is not None:
                rows.append(row)
    return rows

#####################################
# PRAAT Combination Helper Functions#
#####################################

def extract_student_number(filename, is_model=False):
    """
    Extracts the student number from the given filename.
    For a filename like "2024311294_DeepFilterNet3.wav", returns "2024311294".
    For a model filename like "model2025313057_DeepFilterNet3.wav", returns "2025313057".
    """
    base = os.path.basename(filename)
    key = base.split('_')[0]
    if is_model and key.startswith("model"):
        return key[len("model"):]
    return key

def process_praat_file(praat_csv_path):
    """
    Processes the PRAAT-processed CSV.
    Assumes the first column is a filename. Renames it to 'filename' if needed.
    Splits the DataFrame into two: one for student rows and one for model rows,
    extracting a 'student_number' from the filename.
    Then, renames the remaining columns by prepending "student_" or "model_".
    Returns two DataFrames: (df_praat_student, df_praat_model)
    """
    df = pd.read_csv(praat_csv_path)
    first_col = df.columns[0]
    if first_col != "filename":
        df = df.rename(columns={first_col: "filename"})
    
    # Split rows based on whether filename starts with "model"
    df_student = df[~df['filename'].str.startswith("model")].copy()
    df_model = df[df['filename'].str.startswith("model")].copy()
    
    # Extract student_number
    df_student['student_number'] = df_student['filename'].apply(lambda x: extract_student_number(x, is_model=False))
    df_model['student_number'] = df_model['filename'].apply(lambda x: extract_student_number(x, is_model=True))
    
    # Drop the original filename column
    df_student.drop(columns=['filename'], inplace=True)
    df_model.drop(columns=['filename'], inplace=True)
    
    # Rename columns (except 'student_number') by appending a prefix
    df_student = df_student.rename(columns=lambda col: f"student_{col}" if col != "student_number" else col)
    df_model = df_model.rename(columns=lambda col: f"model_{col}" if col != "student_number" else col)
    
    return df_student, df_model

def combine_csv_files(pron_csv_path, praat_csv_path, output_path):
    """
    Combines the pronunciation-processed CSV and the PRAAT-processed CSV.
    It merges on the 'student_number' key. If PRAAT data is available for both student
    and model rows, the columns are renamed with the appropriate prefixes.
    The combined data is then saved to output_path.
    """
    # Load pronunciation CSV (which must contain a 'student_number' column)
    df_pron = pd.read_csv(pron_csv_path)
    if 'student_number' not in df_pron.columns:
        print(f"Error: 'student_number' column not found in {pron_csv_path}")
        return
    
    # Process PRAAT CSV into student and model DataFrames
    try:
        df_praat_student, df_praat_model = process_praat_file(praat_csv_path)
    except Exception as e:
        print(f"Error processing PRAAT file {praat_csv_path}: {e}")
        return

    # Convert student_number columns to string for merging
    df_pron['student_number'] = df_pron['student_number'].astype(str)
    df_praat_student['student_number'] = df_praat_student['student_number'].astype(str)
    df_praat_model['student_number'] = df_praat_model['student_number'].astype(str)
    
    # Merge the PRAAT student data into the pronunciation DataFrame
    df_combined = pd.merge(df_pron, df_praat_student, on='student_number', how='left')
    # Merge the PRAAT model data into the combined DataFrame
    df_combined = pd.merge(df_combined, df_praat_model, on='student_number', how='left')
    
    df_combined.to_csv(output_path, index=False)
    print(f"Combined CSV saved to {output_path}")

##############################
# Main Integration Function  #
##############################

def main():
    parser = argparse.ArgumentParser(
        description="Process oneliners folders and combine with PRAAT data into a single audio-processed CSV per parent folder."
    )
    parser.add_argument('-o', '--output',
                        help='Output directory for CSV files (default: output-files folder in script directory)',
                        default=None)
    args = parser.parse_args()
    
    # Determine the script directory.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Set up the output directory (for both individual and combined CSVs).
    output_dir = args.output if args.output else os.path.join(script_dir, "output-files")
    os.makedirs(output_dir, exist_ok=True)
    
    # Define the fixed parent–parent directories relative to the script.
    parent_parent_dirs = [
        os.path.join(script_dir, "folders", "tcs"),
        os.path.join(script_dir, "folders", "ipe"),
        os.path.join(script_dir, "folders", "capstone")
    ]
    
    # Define column names for the pronunciation-processed CSV.
    pron_columns = [
        'student_number',
        'student_accuracy_score', 'student_prosody_score', 'student_pronunciation_score',
        'student_completeness_score', 'student_fluency_score',
        'model_accuracy_score', 'model_prosody_score', 'model_pronunciation_score',
        'model_completeness_score', 'model_fluency_score'
    ]
    
    # -------------------------
    # PART 1: Data Collection
    # -------------------------
    for parent_parent in parent_parent_dirs:
        if not os.path.exists(parent_parent):
            print(f"Directory {parent_parent} does not exist. Skipping.")
            continue
        
        # Iterate over each parent folder in the current parent–parent directory.
        for parent_folder in os.listdir(parent_parent):
            parent_folder_path = os.path.join(parent_parent, parent_folder)
            if os.path.isdir(parent_folder_path):
                oneliners_folder = os.path.join(parent_folder_path, "oneliners")
                if os.path.isdir(oneliners_folder):
                    print(f"Processing oneliners folder: {oneliners_folder}")
                    rows = process_oneliners_folder(oneliners_folder)
                    if not rows:
                        print(f"No valid data found in {oneliners_folder}.")
                        continue
                    df_pron = pd.DataFrame(rows, columns=pron_columns)
                    
                    # Name the output file using the parent folder's name.
                    pron_output_filename = f"{parent_folder}-pronunciation-processed.csv"
                    pron_output_path = os.path.join(output_dir, pron_output_filename)
                    df_pron.to_csv(pron_output_path, index=False)
                    print(f"Pronunciation processed CSV saved to {pron_output_path}")
                else:
                    print(f"No oneliners folder found in {parent_folder_path}. Skipping.")
    
    # -------------------------
    # PART 2: Combination Step
    # -------------------------
    # For every pronunciation processed CSV in output_dir, look for a corresponding PRAAT CSV.
    for filename in os.listdir(output_dir):
        if filename.endswith("-pronunciation-processed.csv"):
            parent_folder_name = filename.replace("-pronunciation-processed.csv", "")
            pron_csv_path = os.path.join(output_dir, filename)
            praat_filename = f"{parent_folder_name}-PRAAT-processed.csv"
            praat_csv_path = os.path.join(output_dir, praat_filename)
            if not os.path.exists(praat_csv_path):
                print(f"PRAAT file {praat_csv_path} not found for {parent_folder_name}. Skipping combination.")
                continue
            combined_filename = f"{parent_folder_name}-audio-processed.csv"
            combined_output_path = os.path.join(output_dir, combined_filename)
            print(f"Combining pronunciation and PRAAT CSV files for {parent_folder_name}...")
            combine_csv_files(pron_csv_path, praat_csv_path, combined_output_path)

if __name__ == '__main__':
    main()