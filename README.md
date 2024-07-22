# efficientstudentmanagement
This is a group of python scripts that can help reduce time required for educators to complete administrative tasks.

1. Add current versions of gpt-cli (https://github.com/kharvd/gpt-cli), my-voice-analysis (https://github.com/Shahabks/my-voice-analysis), and L2SCA (https://www.dropbox.com/scl/fi/kim1jb151ii4e711zb6to/L2SCA-2023-08-15.tgz?rlkey=uqwsr96jpxnr5ucbgta5nwypz&st=blyfw6n0&dl=0) as subfolders in the folder entitled 'folders'

2. Verify that each of those software packages, as well as python 3.11, is installed correctly

3. Copy necessary input files to 'input-files' folders, such as 'w01prompts.tsv' (containing two columns, one with student numbers, the other with the entire prompt include student text for each student number), 'w01raw.tsv' (containing two columns, one with student numbers, the other with the entire text sample for each student number), and a folder containing audio files in any format 'w01' (containing audio files, where each file name begins with a student number).

Here is the syntax for the most important scripts:

python3 GPT.py [prompts file reference in TSV format, such as w01prompts.tsv] w01

python3 L2SCA.py [raw text file reference in TSV format, such as w01raw.tsv] w01

python3 PRAAT.py [audio file folder name reference] w01



Additional scripts

-audio file formatting:

-audiodownloader: takes a CSV file with student numbers in one column and GoogleDrive links in another column, uses Google Chrome (with an extension that automatically downloads Google Drive files), downloads files to ~/Downloads, and prepends student numbers

-checking for plagiarism:

-concat_check: takes a TSV file with three columns, one with student numbers, one with text for comparison (e.g., all previous text written by a particular student), one with text of interest (e.g., a recent assignment).
disc_similarlity_check, hw_similarity_check, and plagiarism_detection_on_two_folders are similar to concat_check (but for different assignment structures, intended as example scripts only)

-formatting text for GetMarked:

-getmarkedformatter: takes text where questions are on one line and answers are on another line of a text file, and formats them so they can be used with GetMarked, where each answer choice is on its own line

-creating tests from question banks:

-shufflequestions: takes two text files containing GetMarked formatted questions, randomly selects 15 questions from each question bank, shuffles them, and adds them to a single formatted text file for use with GetMarked.

-formatting forms:

-AppScript_customgetmarkedscript: paste AppsScript code from GetMarked into this AppsScript template to use with a template form (requires a previously saved template form in Google Drive; you can add details into this form that you want to appear in every form, such as collecting student numbers, email addresses, and other form settings like allowing response editing, showing which responses are incorrect, etc.)

-extracting comment data from Google Docs:

-AppScript_commentharvester: use this AppsScript in Google Sheets to retrieve information associated with Google Docs files, such as author name, comment author name, and comment content (allows for content analysis of Google Docs meta data).

