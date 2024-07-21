import re
import sys

def condense_spaces(line):
    # Replace multiple consecutive spaces with a single space
    return re.sub(r'\s+', ' ', line)

def process_line(line, is_answer_line):
    if line:
        words = line.split()
        modified_words = []

        # Check if the line is a numbered line (question)
        if line[0].isdigit():
            # Add a period right after the number
            first_word_end = line.find(' ')
            first_word = line[:first_word_end] + '.'
            rest_of_line = line[first_word_end + 1:]
            modified_words.append(first_word)

            # Process the rest of the line
            for word in rest_of_line.split():
                # Add a colon after 'A' or 'B'
                if word in ['A', 'B']:
                    modified_words.append(word + ':')
                else:
                    modified_words.append(word)
            return ' '.join(modified_words).rstrip()
        else:
            # Process words in answer lines
            for word in words:
                # Add a period after individual letters from 'A' to 'H' (uppercase and lowercase) on answer lines
                if word.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                    modified_words.append('\n' + word.capitalize() + '.')
                else:
                    modified_words.append(word)
            return ' '.join(modified_words).lstrip()

    return line

def modify_file(input_file, output_file):
    with open(input_file, 'r') as file, open(output_file, 'w') as outfile:
        for line in file:
            line = condense_spaces(line.strip())
            # Determine if the line is an answer line (not starting with a number)
            is_answer_line = not line[0].isdigit() if line else False

            # Add two line breaks before numbered lines
            if line and line[0].isdigit():
                outfile.write('\n\n')

            modified_line = process_line(line, is_answer_line)
            outfile.write(modified_line + '\n')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py input_filename.txt")
    else:
        input_file = sys.argv[1]
        output_file = 'modified_' + input_file
        modify_file(input_file, output_file)
