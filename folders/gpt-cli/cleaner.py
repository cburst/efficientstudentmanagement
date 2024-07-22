import re
import csv
import sys
import os

def filter_csv(file_path):
    # Pattern to match a string with one, two, or three digits between @ symbols (either @1@, @@1@@, @999@, or @@999@@) and no other @ symbols
    at_pattern = re.compile(r'^([^@]*@{1,2}(\d{1,3})@{1,2}[^@]*)$')
    
    # String to be removed from each line
    removal_string = "the number of mistakes between @@ symbols"
    
    # Pattern to match a number between the specified delimiters
    delimiters_pattern = re.compile(r'([!#\$%\^&\*\~\+=₩])(\d{1,3})\1')
    
    # Pattern to find "error" variations
    error_pattern = re.compile(r'error', re.IGNORECASE)
    
    at_violations = 0
    delimiter_violations = 0
    total_lines = 0
    removed_lines = 0

    def check_delimiters_and_error(cell):
        # Find the position of the first occurrence of "error"
        match = error_pattern.search(cell)
        if not match:
            return True  # No "error", so no need to check further
        
        error_pos = match.start()
        before_error = cell[:error_pos]
        
        # Find all matches of delimiters pattern before the first "error" occurrence
        matches = delimiters_pattern.findall(before_error)
        counts = {}
        for match in matches:
            if match in counts:
                counts[match] += 1
            else:
                counts[match] = 1
        
        # Ensure each delimiter pattern appears no more than once before "error"
        return all(count <= 1 for count in counts.values())
    
    # Open the file with utf-8 encoding to handle Unicode characters consistently across platforms
    with open(file_path, mode='r', encoding='utf-8', newline='') as file:
        reader = csv.reader(file)
        
        # Process and filter rows
        lines = []
        for row in reader:
            total_lines += 1
            # Remove the specified string from each cell in the row
            cleaned_row = [cell.replace(removal_string, '') for cell in row]
            
            # Check each cell for delimiter and error conditions
            valid_row = True
            for cell in cleaned_row:
                if not check_delimiters_and_error(cell):
                    valid_row = False
                    delimiter_violations += 1
                    break
            
            # Filter rows that match the regex pattern and pass the delimiters check
            if valid_row and any(at_pattern.match(cell) for cell in cleaned_row):
                lines.append(row)
            else:
                if not valid_row:
                    removed_lines += 1
                elif not any(at_pattern.match(cell) for cell in cleaned_row):
                    at_violations += 1
                    removed_lines += 1
    
    # Write the filtered rows back to the file with utf-8 encoding
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(lines)
    
    # Print the complete path of the CSV file and a completion message
    print(f"Cleaning completed for: {os.path.abspath(file_path)}")
    print(f"Total lines processed: {total_lines}")
    print(f"Total lines removed: {removed_lines}")
    print(f"Percent of lines removed: {removed_lines / total_lines * 100:.2f}%")
    print(f"Main delimiter issues: {at_violations}")
    print(f"Other delimiter issues: {delimiter_violations}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py file.csv")
    else:
        file_path = sys.argv[1]
        filter_csv(file_path)