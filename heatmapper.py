import os
import sys
import csv
import subprocess
from weasyprint import HTML
from PyPDF2 import PdfMerger

def map_score_to_color(score):
    try:
        s = float(score)
    except Exception:
        s = 0.0
    if s > 85:
        return "#7CFC00"  # Bright green
    elif s > 80:
        return "#FAFA33"  # Bright yellow
    elif s > 75:
        return "#FF7518"  # Bright orange
    else:
        return "#FF0000"  # Bright red

def escape_html(s):
    return (s.replace("&", "&amp;")
              .replace("<", "&lt;")
              .replace(">", "&gt;")
              .replace('"', "&quot;")
              .replace("'", "&#39;"))

def generate_heatmap_pdf(folder, rows):
    # Build sentences block with manual control — you can insert &nbsp; and <br> into this if needed
    sentences_html = ""
    for idx, row in enumerate(rows):
        sentence = escape_html(row.get("recognized_text", "").strip())
        score = row.get("prosody_score", "0").strip()
        color = map_score_to_color(score)

        if idx > 0:
            sentences_html += " "  # Space between sentences (but you can add <br> here if you want line breaks)
        sentences_html += f'<span style="background-color: {color};">{sentence}</span>'

    # Completely flush-left HTML, but with bold section headers
    html_content = f"""
    <html>
    <head>
        <style>
            @page {{
                size: A4 portrait;
                margin: 1in;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 14pt;
                line-height: 1.3;
            }}
            .color-box {{
                display: inline-block;
                width: 30px;
                height: 15px;
                margin-right: 5px;
            }}
            .bold {{
                font-weight: bold;
            }}
        </style>
    </head>
    <body>

    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="bold">Analysis notes:</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;This PDF contains your text color-coded according to speech quality as measured by the Azure Speech Assessment API. Try to improve your intonation, emphasis, and pronunciation to achieve higher levels of speech quality.<br><br>

    <span class="bold">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Contact info:</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;richard.rose@hufs.ac.kr<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;richard.rose@yonsei.ac.kr<br><br>

    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="bold">Speech Quality and Color Scoring System:</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="color-box" style="background-color: #7CFC00;"></span> Score between 85 and 100<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="color-box" style="background-color: #FAFA33;"></span> Score between 80 and 85<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="color-box" style="background-color: #FF7518;"></span> Score between 75 and 80<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="color-box" style="background-color: #FF0000;"></span> Score below 75<br><br>

    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="bold">Your text:</span><br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{sentences_html}

    </body>
    </html>
    """

    pdf_path = os.path.join(folder, "heatmap.pdf")
    HTML(string=html_content).write_pdf(pdf_path)
    print(f"Generated heatmap PDF at {pdf_path}")

def generate_table_pdf(folder, rows, section_title, filename, landscape=False, wide_columns=None):
    headers = rows[0].keys()

    page_size = "A4 landscape" if landscape else "A4 portrait"

    processed_headers = [h.replace("_", " ") for h in headers]

    col_widths = []
    for idx, h in enumerate(headers):
        if wide_columns and idx in wide_columns:
            col_widths.append("width: 30%;")
        else:
            col_widths.append("width: auto;")

    table_rows = ""
    for row in rows:
        table_rows += "<tr>" + "".join(
            f'<td style="{col_widths[idx]}">{escape_html(str(row.get(h, "")))}</td>'
            for idx, h in enumerate(headers)
        ) + "</tr>"

    html_content = f"""
    <html>
    <head>
        <style>
            @page {{
                size: {page_size};
                margin: 1in;
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 10pt;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                page-break-inside: avoid;
            }}
            th, td {{
                border: 1px solid black;
                padding: 5px;
                text-align: left;
                vertical-align: top;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            thead {{
                display: table-header-group;
            }}
            tr {{
                page-break-inside: avoid;
            }}
            .section-title-header {{
                font-weight: bold;
                font-size: 12pt;
                background-color: #e0e0e0;
                text-align: left;
                padding: 5px;
            }}
        </style>
    </head>
    <body>
        <table>
            <thead>
                <tr><th colspan="{len(headers)}" class="section-title-header">{section_title}</th></tr>
                <tr>{''.join(f'<th>{escape_html(h)}</th>' for h in processed_headers)}</tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </body>
    </html>
    """

    pdf_path = os.path.join(folder, filename)
    HTML(string=html_content).write_pdf(pdf_path)
    print(f"Generated {filename} at {pdf_path}")

def merge_pdfs(folder):
    merger = PdfMerger()
    pdf_files = ["heatmap.pdf", "sentences.pdf", "words.pdf"]

    for pdf in pdf_files:
        pdf_path = os.path.join(folder, pdf)
        if os.path.isfile(pdf_path):
            merger.append(pdf_path)

    combined_path = os.path.join(folder, "analysis.pdf")
    merger.write(combined_path)
    merger.close()
    print(f"Created combined PDF at {combined_path}")

def send_email_with_applescript(folder):
    applescript_code = f'''
    set folderPath to "{folder}"
    set emailFilePath to folderPath & "/email.txt"
    set nameFilePath to folderPath & "/name.txt"
    set pdfPath to folderPath & "/analysis.pdf"

    set emailaddy to do shell script "cat " & quoted form of emailFilePath
    set nameFileContent to do shell script "cat " & quoted form of nameFilePath

    tell application "Mail"
        set newMessage to make new outgoing message with properties {{subject:"Speech Quality Analysis", content:"Hi " & nameFileContent & ",\\n\\nPlease find your speech quality analysis attached.", visible:true}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:emailaddy}}
            make new attachment with properties {{file name:(POSIX file pdfPath as alias)}} at after last paragraph
        end tell
        send newMessage
    end tell
    '''

    script_path = os.path.join(folder, "send_email.applescript")
    with open(script_path, "w") as script_file:
        script_file.write(applescript_code)

    subprocess.run(["osascript", script_path])

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]
    sentence_csv = os.path.join(folder, "sentence_level_results.csv")
    word_csv = os.path.join(folder, "word_level_results.csv")

    with open(sentence_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    generate_heatmap_pdf(folder, rows)
    generate_table_pdf(folder, rows, "Sentence Level Data", "sentences.pdf", landscape=True, wide_columns=[1, 2])

    if os.path.isfile(word_csv):
        with open(word_csv, newline="", encoding="utf-8") as f:
            word_rows = list(csv.DictReader(f))
        generate_table_pdf(folder, word_rows, "Word Level Data", "words.pdf")

    merge_pdfs(folder)
    send_email_with_applescript(folder)

if __name__ == "__main__":
    main()