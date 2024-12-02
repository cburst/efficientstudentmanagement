import os
import sys
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor

def main():
    if len(sys.argv) != 2:
        print("Error: No directory name provided.")
        sys.exit(1)
    
    d = sys.argv[1]
    base_dir = os.getcwd()

    # Define the path to the input-files directory
    input_files_dir = os.path.join(base_dir, "input-files")
    tsv_file = os.path.join(input_files_dir, f"{d}raw.tsv")
    if not os.path.isfile(tsv_file):
        print(f"Error: TSV file '{tsv_file}' not found in {input_files_dir}.")
        sys.exit(1)

    generate_prompt_files(tsv_file, d, input_files_dir)

    # Run additional Python scripts in parallel
    with ThreadPoolExecutor() as executor:
        executor.submit(run_script, "GPT.py", f"{d}-gen")
        executor.submit(run_script, "GPT2.py", f"{d}-get")
        executor.submit(run_script, "L2SCA.py", f"{d}")

def generate_prompt_files(tsv_file, d, input_files_dir):
    genprompts_file = os.path.join(input_files_dir, f"{d}-genprompts.tsv")
    getprompts_file = os.path.join(input_files_dir, f"{d}-getprompts.tsv")

    with open(tsv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        header = next(reader)

        with open(genprompts_file, 'w', newline='', encoding='utf-8') as gen_file, \
             open(getprompts_file, 'w', newline='', encoding='utf-8') as get_file:

            gen_writer = csv.writer(gen_file, delimiter='\t')
            get_writer = csv.writer(get_file, delimiter='\t')

            gen_writer.writerow(header)
            get_writer.writerow(header)

            for row in reader:
                gen_row = row[:]
                gen_row[1] = "Can you check the following paragraph, located after the colon, for grammar mistakes, count the number of mistakes, place the number of grammar mistakes between TWO @ symbols even if the number is zero, explain each of the mistakes, and provide a revised paragraph: " + gen_row[1]
                gen_writer.writerow(gen_row)
                
                get_row = row[:]
                get_row[1] = "I want to count the total number of grammar errors in a paragraph by summing errors detected according to error type for the following types of errors: Preposition errors, Morphology errors, Determiner errors, Tense/Aspect errors, Agreement errors, Syntax errors, Punctuation errors, Spelling errors, Unidiomatic errors, Multiple errors, and Miscellaneous errors. The sum total number of errors should use @ as the delimiter, even if the number of errors is 0 (for example @0@, @1@, @2@, etc.). The number of Preposition errors should use ! as the delimiter, even if the number of errors is 0 (for example !0!, !1!, !2!, etc.). The number of Morphology errors should use # as the delimiter, even if the number of errors is 0 (for example #0#, #1#, #2#, etc.). The number of Determiner errors should use $ as the delimiter, even if the number of errors is 0 (for example $0$, $1$, $2$, etc.). The number of Tense/Aspect errors should use % as the delimiter, even if the number of errors is 0 (for example %0%, %1%, %2%, etc.). The number of Agreement errors should use ^ as the delimiter, even if the number of errors is 0 (for example ^0^, ^1^, ^2^, etc.). The number of Syntax errors should use & as the delimiter, even if the number of errors is 0 (for example &0&, &1&, &2&, etc.). The number of Punctuation errors should use * as the delimiter, even if the number of errors is 0 (for example *0*, *1*, *2*, etc.). The number of Spelling errors should use ~ as the delimiter, even if the number of errors is 0 (for example ~0~, ~1~, ~2~, etc.). The number of Unidiomatic errors should use + as the delimiter, even if the number of errors is 0 (for example +0+, +1+, +2+, etc.). The number of Multiple errors should use = as the delimiter, even if the number of errors is 0 (for example =0=, =1=, =2=, etc.). The number of Miscellaneous errors should use ₩ as the delimiter, even if the number of errors is 0 (for example ₩0₩, ₩1₩, ₩2₩, etc.). Make sure that the sum total number matches the sum of the individual error types. Start your answer with all error numbers in their delimiters each separated by a space on the first line. Next, explain each of the errors, and provide a revised paragraph.  The text I would like you to check follows this colon: " + get_row[1]
                get_writer.writerow(get_row)

def run_script(script_name, suffix):
    command = [sys.executable, script_name, suffix]
    subprocess.run(command, check=True)

if __name__ == "__main__":
    main()