import pandas as pd

def find_identical_strings(col1, col2, length):
    col1_words = str(col1).split()
    col2_words = str(col2).split()
    matches = []
    for i in range(len(col1_words) - length + 1):
        for j in range(len(col2_words) - length + 1):
            if col1_words[i:i+length] == col2_words[j:j+length]:
                matches.append(" ".join(col1_words[i:i+length]))
    return "/".join(matches)

# Load the TSV file
df = pd.read_csv('concat.tsv', sep='\t', header=None)

# Initialize new columns for identical strings of varying lengths
df[3] = df.apply(lambda row: find_identical_strings(row[1], row[2], 6), axis=1)
df[4] = df.apply(lambda row: find_identical_strings(row[1], row[2], 7), axis=1)
df[5] = df.apply(lambda row: find_identical_strings(row[1], row[2], 8), axis=1)
df[6] = df.apply(lambda row: find_identical_strings(row[1], row[2], 9), axis=1)
df[7] = df.apply(lambda row: find_identical_strings(row[1], row[2], 10), axis=1)

# Save the updated dataframe to a new TSV file
df.to_csv('updated_concat.tsv', sep='\t', index=False, header=False)

print("Processing complete. The updated file is saved as 'updated_concat.tsv'.")