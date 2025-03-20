import os
import sys
import csv
import subprocess
from PyPDF2 import PdfMerger

def map_score_to_color(score):
    """Map the prosody score to a color."""
    try:
        s = float(score)
    except Exception:
        s = 0.0
    if s > 85:
        return "green"
    elif s > 80:
        return "yellow"
    elif s > 75:
        return "orange"
    else:
        return "red"

def escape_latex(s):
    """Escape LaTeX special characters."""
    return s.replace('\\', r'\textbackslash{}')\
            .replace('&', r'\&')\
            .replace('%', r'\%')\
            .replace('$', r'\$')\
            .replace('#', r'\#')\
            .replace('_', ' ')\
            .replace('{', r'\{')\
            .replace('}', r'\}')\
            .replace('~', r'\textasciitilde{}')\
            .replace('^', r'\^{}')

def generate_heatmap_pdf(folder, rows):
    """Generate the heatmap PDF with user‑adjustable LaTeX formatting."""
    # Create the highlighted sentences as one LaTeX line.
    highlighted_sentences = ""
    for idx, row in enumerate(rows):
        sentence = row.get("recognized_text", "").strip()
        score = row.get("prosody_score", "0").strip()
        color = map_score_to_color(score)
        color_name = f"tempcolor{idx}"
        # Build each highlighted sentence.
        highlighted_sentences += r"{\definecolor{" + color_name + r"}{named}{" + color + r"}" \
                                 + r"\sethlcolor{" + color_name + r"}\hl{" + escape_latex(sentence) + r"}} "
    
    # Write out the LaTeX document as a single multi-line string.
    latex_content = rf"""\documentclass{{article}}
\usepackage{{soul}}
\usepackage{{xcolor}}
\usepackage[margin=1in]{{geometry}}
\begin{{document}}
\large

\indent\indent\textbf{{Analysis notes:}}\newline
\indent\indent This PDF file contains your text color-coded according to speech quality as measured by the Azure Speech Assessment API. Try to improve your intonation, emphasis, and pronunciation to achieve higher levels of speech quality.\newline\newline
\indent\indent \textbf{{Contact info:}}\newline
\indent\indent \begin{{color}}{{teal}} richard.rose@hufs.ac.kr \end{{color}} \newline
\indent\indent \begin{{color}}{{teal}} richard.rose@yonsei.ac.kr \end{{color}}\newline\newline
\indent\indent \noindent\textbf{{Speech Quality and Color Scoring System:}}\newline
\indent\indent {{\definecolor{{keygreen}}{{named}}{{green}}\sethlcolor{{keygreen}}\hl{{~~~~}}}} Score between 85 and 100 \newline
\indent\indent {{\definecolor{{keyyellow}}{{named}}{{yellow}}\sethlcolor{{keyyellow}}\hl{{~~~~}}}} Score between 80 and 85 \newline
\indent\indent {{\definecolor{{keyorange}}{{named}}{{orange}}\sethlcolor{{keyorange}}\hl{{~~~~}}}} Score between 75 and 80 \newline
\indent\indent {{\definecolor{{keyred}}{{named}}{{red}}\sethlcolor{{keyred}}\hl{{~~~~}}}} Score below 75 \newline \newline
\indent\indent \textbf{{Your text:}}

\indent\indent {highlighted_sentences}

\end{{document}}
"""
    # Write the LaTeX content to a file.
    tex_filename = "heatmap.tex"
    tex_path = os.path.join(folder, tex_filename)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)
    
    # Compile the document twice.
    for i in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], cwd=folder)

def create_sentences_pdf(folder, rows):
    """Generate the sentence-level PDF."""
    latex_lines = [
        r"\documentclass{article}",
        r"\usepackage{longtable}",
        r"\usepackage{array}",
        r"\usepackage{pdflscape}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{makecell}",
        r"\pagestyle{empty}",
        r"\renewcommand{\arraystretch}{1.3}",
        r"\begin{document}",
        r"\begin{landscape}",
        r"\section*{Sentence Level Data}",
        r"\footnotesize"
    ]

    headers = list(rows[0].keys())
    column_widths = ['p{1.5cm}', 'p{5cm}', 'p{5cm}', 'p{1.5cm}', 'p{1.5cm}', 'p{2.5cm}', 'p{2.5cm}', 'p{1.5cm}']
    formatted_headers = [r"\textbf{" + escape_latex(h) + "}" for h in headers]

    latex_lines.append(r"\begin{longtable}{" + "|".join(column_widths) + r"|}")
    latex_lines.append(r"\hline")
    latex_lines.append(" & ".join(formatted_headers) + r" \\ \hline")
    latex_lines.append(r"\endfirsthead")
    latex_lines.append(r"\hline " + " & ".join(formatted_headers) + r" \\ \hline")
    latex_lines.append(r"\endhead")

    for row in rows:
        row_data = [escape_latex(str(row.get(h, ""))) for h in headers]
        latex_lines.append(" & ".join(row_data) + r" \\ \hline")

    latex_lines += [
        r"\end{longtable}",
        r"\end{landscape}",
        r"\end{document}"
    ]

    tex_filename = "sentences.tex"
    tex_path = os.path.join(folder, tex_filename)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_lines))

    for i in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], cwd=folder)

def create_words_pdf(folder, word_csv_path):
    """Generate the word-level PDF."""
    temp_csv_path = os.path.join(folder, "word_level_results_temp.csv")
    
    with open(word_csv_path, 'r', encoding='utf-8') as infile, open(temp_csv_path, 'w', encoding='utf-8', newline='') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            new_row = [cell.replace('_', ' ') for cell in row]
            writer.writerow(new_row)

    rows = []
    with open(temp_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    latex_lines = [
        r"\documentclass{article}",
        r"\usepackage{longtable}",
        r"\usepackage{array}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{makecell}",
        r"\pagestyle{empty}",
        r"\renewcommand{\arraystretch}{1.3}",
        r"\begin{document}",
        r"\section*{Word Level Data}",
        r"\normalsize"
    ]

    headers = list(rows[0].keys())
    column_widths = ['p{2cm}' if idx in [0, 1, 3] else 'p{3.3cm}' if idx == 4 else 'p{2.5cm}' for idx in range(len(headers))]
    formatted_headers = [r"\textbf{" + escape_latex(h) + "}" for h in headers]

    latex_lines.append(r"\begin{longtable}{" + "|".join(column_widths) + r"|}")
    latex_lines.append(r"\hline")
    latex_lines.append(" & ".join(formatted_headers) + r" \\ \hline")
    latex_lines.append(r"\endfirsthead")
    latex_lines.append(r"\hline " + " & ".join(formatted_headers) + r" \\ \hline")
    latex_lines.append(r"\endhead")

    for row in rows:
        row_data = [escape_latex(str(row.get(h, ""))) for h in headers]
        latex_lines.append(" & ".join(row_data) + r" \\ \hline")

    latex_lines += [
        r"\end{longtable}",
        r"\end{document}"
    ]

    tex_filename = "words.tex"
    tex_path = os.path.join(folder, tex_filename)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("\n".join(latex_lines))

    for i in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", tex_filename], cwd=folder)

def merge_pdfs(folder):
    """Merge the three generated PDFs into one."""
    merger = PdfMerger()
    pdf_files = ["heatmap.pdf", "sentences.pdf", "words.pdf"]

    for pdf in pdf_files:
        pdf_path = os.path.join(folder, pdf)
        if os.path.isfile(pdf_path):
            merger.append(pdf_path)
        else:
            print(f"Warning: {pdf} not found, skipping.")

    output_path = os.path.join(folder, "heatmap-and-tables.pdf")
    merger.write(output_path)
    merger.close()
    print(f"Combined PDF created at {output_path}")
    
    # Rename the merged PDF to analysis.pdf for the email attachment
    analysis_pdf = os.path.join(folder, "analysis.pdf")
    os.replace(output_path, analysis_pdf)
    print(f"Renamed merged PDF to {analysis_pdf}")

def send_email_with_applescript(folder_path):
    """
    Generates and runs an AppleScript that sends an email using email.txt, name.txt, and analysis.pdf 
    in the given folder path.
    """
    applescript_code = f'''
    -- Use the folder path directly since it's already in POSIX format
    set targetFolder to "{folder_path}"
    
    -- Build the file paths by adding a slash if needed
    set emailFilePath to targetFolder & "/email.txt"
    set nameFilePath to targetFolder & "/name.txt"
    set analysisPDFPath to targetFolder & "/analysis.pdf"
    
    -- Attempt to read the email address from email.txt
    try
        set emailaddy to do shell script "cat " & quoted form of emailFilePath
    on error errMsg
        display dialog "Error reading email.txt: " & errMsg buttons {{"OK"}} default button "OK"
        return
    end try

    if emailaddy is "" then
        display dialog "email.txt is empty. Please enter a valid email address." buttons {{"OK"}} default button "OK"
        return
    end if

    -- Read the name from name.txt
    try
        set nameFileContent to do shell script "cat " & quoted form of nameFilePath
    on error
        set nameFileContent to "Name not found"
    end try

    set greeting to "Hi " & nameFileContent & ","
    set currentDate to current date
    set formattedDate to (currentDate as string)
    
    tell application "Mail"
        set newMessage to make new outgoing message with properties {{subject:"Speech Quality Analysis - " & formattedDate, content:greeting & return & return & "Thank you for sending your recorded audio and document information for analysis." & return & "The audio and document analysis file is attached for your consideration." & return & "Please let me know if you have any further questions." & return & return & "Best regards," & return & "Dr. Rose", visible:true}}
        
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:emailaddy}}
            try
                -- Convert the PDF path to an alias and attach it to the message content
                set attachmentFile to POSIX file analysisPDFPath as alias
                tell content
                    make new attachment with properties {{file name:attachmentFile}} at after last paragraph
                end tell
            on error errMsg
                display dialog "Error attaching analysis.pdf: " & errMsg buttons {{"OK"}} default button "OK"
            end try
        end tell
        
        activate
        send newMessage
    end tell
    '''
    
    script_path = os.path.join(folder_path, "send_email.applescript")
    with open(script_path, "w") as script_file:
        script_file.write(applescript_code)
    
    try:
        subprocess.run(["osascript", script_path], check=True)
        print(f"Executed AppleScript to send email from {folder_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error running AppleScript: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python combined_script.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        sys.exit(1)

    # Load sentence-level CSV
    sentence_csv = os.path.join(folder, "sentence_level_results.csv")
    word_csv = os.path.join(folder, "word_level_results.csv")
    
    if not os.path.isfile(sentence_csv):
        print(f"Error: {sentence_csv} not found.")
        sys.exit(1)

    with open(sentence_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    # Generate PDFs
    generate_heatmap_pdf(folder, rows)
    create_sentences_pdf(folder, rows)

    if os.path.isfile(word_csv):
        create_words_pdf(folder, word_csv)
    else:
        print(f"Warning: {word_csv} not found, skipping word-level PDF.")

    # Merge PDFs and rename merged file to analysis.pdf for email attachment
    merge_pdfs(folder)

    # Send the email using the AppleScript
    # send_email_with_applescript(folder)

if __name__ == "__main__":
    main()