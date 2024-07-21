import pandas as pd
from Levenshtein import ratio

# Load your TSV file
file_path = 'disc.tsv'
df = pd.read_csv(file_path, sep='\t')

# Keep only the first seven columns
df = df.iloc[:, :7]

# Extract the columns of interest
column_data_6 = df.iloc[:, 5].astype(str)
column_data_7 = df.iloc[:, 6].astype(str)

# Combine the two columns into one for processing
combined_data = pd.concat([column_data_6, column_data_7], ignore_index=True)

# Initialize new columns
df['R'] = ''
df['R_Matches'] = ''
df['R_match_pct'] = ''
df['S'] = ''
df['S_Matches'] = ''
df['S_match_pct'] = ''

# Function to update similarity columns
def update_similarity_columns(index, R_matches, R_match_pct, S_matches, S_match_pct):
    if R_matches:
        df.at[index, 'R'] = 'R'
        df.at[index, 'R_Matches'] = ','.join(R_matches)
        df.at[index, 'R_match_pct'] = ','.join(R_match_pct)
    if S_matches:
        df.at[index, 'S'] = 'S'
        df.at[index, 'S_Matches'] = ','.join(S_matches)
        df.at[index, 'S_match_pct'] = ','.join(S_match_pct)

# Populate new columns based on Levenshtein similarity
num_rows = len(df)
total_rows = len(combined_data)
for i in range(num_rows):
    R_matches = []
    R_match_pct = []
    S_matches = []
    S_match_pct = []

    # Check similarity for column 6 against all
    for j in range(total_rows):
        if j < num_rows and i == j:  # Ignore the same row for column 6
            continue
        similarity = ratio(column_data_6[i], combined_data[j])
        similarity_pct = f"{similarity * 100:.2f}"
        if similarity >= 0.90:
            R_matches.append(str(j % num_rows + 1))  # 1-based index
            R_match_pct.append(similarity_pct)
        elif 0.70 <= similarity < 0.90:
            S_matches.append(str(j % num_rows + 1))  # 1-based index
            S_match_pct.append(similarity_pct)

    # Check similarity for column 7 against all
    for j in range(total_rows):
        if j >= num_rows and i == j - num_rows:  # Ignore the same row for column 7
            continue
        similarity = ratio(column_data_7[i], combined_data[j])
        similarity_pct = f"{similarity * 100:.2f}"
        if similarity >= 0.90:
            R_matches.append(str(j % num_rows + 1))  # 1-based index
            R_match_pct.append(similarity_pct)
        elif 0.70 <= similarity < 0.90:
            S_matches.append(str(j % num_rows + 1))  # 1-based index
            S_match_pct.append(similarity_pct)

    update_similarity_columns(i, R_matches, R_match_pct, S_matches, S_match_pct)

# Clear the new columns for rows where column six has fewer than 10 characters
for i in range(len(df)):
    if len(column_data_6[i].strip()) < 10:
        df.at[i, 'R'] = ''
        df.at[i, 'R_Matches'] = ''
        df.at[i, 'R_match_pct'] = ''
        df.at[i, 'S'] = ''
        df.at[i, 'S_Matches'] = ''
        df.at[i, 'S_match_pct'] = ''

# Save the updated dataframe to a new TSV file
output_file_path = 'disc_updated.tsv'
df.to_csv(output_file_path, sep='\t', index=False)

print(f"Updated file saved to {output_file_path}")