import os
import csv
import argparse

def read_text_files_in_folder(folder_path):
    text_files = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    text = f.read()
                    text_files[file] = text
    return text_files

def find_identical_strings(text_files1, text_files2):
    results = []

    for file1, text1 in text_files1.items():
        for file2, text2 in text_files2.items():
            identical_strings = [""] * 5  # Initialize with empty strings for 4 to 8 words

            for word_length in range(4, 9):
                words1 = text1.split()
                for i in range(len(words1) - word_length + 1):
                    word_sequence = " ".join(words1[i:i + word_length])
                    if word_sequence in text2:
                        identical_strings[word_length - 4] += f"{word_sequence}\r"

            if any(identical_strings):
                results.append([file1, file2] + identical_strings)

    return results

def main(folder1, folder2, output_csv):
    text_files1 = read_text_files_in_folder(folder1)
    text_files2 = read_text_files_in_folder(folder2)

    results = find_identical_strings(text_files1, text_files2)

    with open(output_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        headers = ["filename1", "filename2", "4-string", "5-string", "6-string", "7-string", "8-string"]
        csv_writer.writerow(headers)
        for row in results:
            csv_writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find identical strings in two folders of text files.")
    parser.add_argument("folder1", help="Path to the first folder of text files.")
    parser.add_argument("folder2", help="Path to the second folder of text files.")
    parser.add_argument("output_csv", help="Output CSV file name.")

    args = parser.parse_args()

    main(args.folder1, args.folder2, args.output_csv)
