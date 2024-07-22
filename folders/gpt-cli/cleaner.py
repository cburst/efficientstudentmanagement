import re
import csv
import sys
import os

def filter_csv(file_path):
    # Pattern to match a string with one, two, or three digits between @ symbols (either @1@, @@1@@, @999@, or @@999@@) and no other @ symbols
    pattern = re.compile(r'^([^@]*@{1,2}(\d{1,3})@{1,2}[^@]*)$')
    
    # String to be removed from each line
    removal_string = "the number of mistakes between @@ symbols"
    
    # Open the file with utf-8 encoding to handle Unicode characters consistently across platforms
    with open(file_path, mode='r', encoding='utf-8', newline='') as file:
        reader = csv.reader(file)
        
        # Process and filter rows
        lines = []
        for row in reader:
            # Remove the specified string from each cell in the row
            cleaned_row = [cell.replace(removal_string, '') for cell in row]
            # Filter rows that match the regex pattern
            if any(pattern.match(cell) for cell in cleaned_row):
                lines.append(row)
    
    # Write the filtered rows back to the file with utf-8 encoding
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lines)
    
    # Print the complete path of the CSV file and a completion message
    print(f"Cleaning completed for: {os.path.abspath(file_path)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py file.csv")
    else:
        file_path = sys.argv[1]
        filter_csv(file_path)