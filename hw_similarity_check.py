import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Levenshtein import ratio

# Load your TSV file
file_path = 'hw.tsv'
df = pd.read_csv(file_path, sep='\t')

# Extract the column of interest
column_data = df.iloc[:, 5].astype(str)

# Calculate TF-IDF vectors and cosine similarity matrix
vectorizer = TfidfVectorizer().fit_transform(column_data)
similarity_matrix = cosine_similarity(vectorizer)

# Initialize new columns
df['R'] = ''
df['R_Matches'] = ''
df['R_match_pct'] = ''
df['S'] = ''
df['S_Matches'] = ''
df['S_match_pct'] = ''

# Populate new columns based on similarity
for i in range(len(df)):
    R_matches = []
    R_match_pct = []
    S_matches = []
    S_match_pct = []
    for j in range(len(df)):
        if i != j:
            # Calculate cosine similarity
            similarity = similarity_matrix[i][j]
            # Calculate Levenshtein similarity percentage
            levenshtein_similarity = ratio(column_data[i], column_data[j]) * 100

            if similarity >= 0.90:
                if levenshtein_similarity >= 90:
                    R_matches.append(str(j + 1))  # 1-based index
                    R_match_pct.append(f"{levenshtein_similarity:.2f}")
                elif 70 <= levenshtein_similarity < 90:
                    S_matches.append(str(j + 1))  # 1-based index
                    S_match_pct.append(f"{levenshtein_similarity:.2f}")
            elif 0.70 <= similarity < 0.90:
                if levenshtein_similarity >= 70:
                    S_matches.append(str(j + 1))  # 1-based index
                    S_match_pct.append(f"{levenshtein_similarity:.2f}")

    # Filter R_matches and R_match_pct to ensure all percentages are above 90
    filtered_R_matches = []
    filtered_R_match_pct = []
    for match, pct in zip(R_matches, R_match_pct):
        if float(pct) >= 90:
            filtered_R_matches.append(match)
            filtered_R_match_pct.append(pct)
        elif 70 <= float(pct) < 90:
            S_matches.append(match)
            S_match_pct.append(pct)

    if filtered_R_matches:
        df.at[i, 'R'] = 'R'
        df.at[i, 'R_Matches'] = ','.join(filtered_R_matches)
        df.at[i, 'R_match_pct'] = ','.join(filtered_R_match_pct)
    if S_matches:
        df.at[i, 'S'] = 'S'
        df.at[i, 'S_Matches'] = ','.join(S_matches)
        df.at[i, 'S_match_pct'] = ','.join(S_match_pct)

# Clear the new columns for rows where column six has fewer than 10 characters
for i in range(len(df)):
    if len(column_data[i].strip()) < 10:
        df.at[i, 'R'] = ''
        df.at[i, 'R_Matches'] = ''
        df.at[i, 'R_match_pct'] = ''
        df.at[i, 'S'] = ''
        df.at[i, 'S_Matches'] = ''
        df.at[i, 'S_match_pct'] = ''

# Save the updated dataframe to a new TSV file
output_file_path = 'hw_updated.tsv'
df.to_csv(output_file_path, sep='\t', index=False)

print(f"Updated file saved to {output_file_path}")