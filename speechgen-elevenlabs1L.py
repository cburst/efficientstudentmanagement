import os
import csv
import sys
import subprocess
import requests
import re
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the ElevenLabs API key from environment variables
api_key = "YOUR KEY HERE"
if not api_key:
    print("API key not found. Please set the ELEVENLABS_API_KEY environment variable.")
    sys.exit(1)

# Hardcoded working directory
BASE_DIR = os.path.expanduser("~/DropboxM/efficient student management resources")

# Change to the base directory at the start of the script
os.chdir(BASE_DIR)
print(f"Changed working directory to {os.getcwd()}")

def extract_voice_number(voice_field):
    """Extracts the numerical digits before the first colon in the voice field."""
    match = re.match(r"(\d+):", voice_field)
    if match:
        return int(match.group(1))  # Convert to an integer
    return None

def fetch_elevenlabs_voices():
    """Retrieve available ElevenLabs voices via API."""
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"Accept": "application/json", "xi-api-key": api_key}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        voices_data = response.json()
        return voices_data.get("voices", [])
    else:
        print(f"Failed to retrieve voices: {response.status_code}, {response.text}")
        return None

def get_voice_id_from_number(voice_number, voices):
    """Match a numerical voice number to an available ElevenLabs voice."""
    if 1 <= voice_number <= len(voices):
        return voices[voice_number - 1]  # Convert 1-based index to 0-based
    return None

def process_csv(csv_filename):
    if not os.path.isfile(csv_filename):
        print(f"Error: File '{csv_filename}' not found.")
        return

    original_working_dir = os.getcwd()

    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        row = next(reader)  # Read the first (and only) row

    timestamp_raw = row[0]
    email = row[1]
    name = row[2]
    text_to_speak = row[5]  # Extract text from field 6
    voice_field = row[6].strip()  # Extract voice field from field 7

    # Extract the numerical voice ID
    voice_number = extract_voice_number(voice_field)
    if voice_number is None:
        print(f"Error: Could not extract a valid voice number from '{voice_field}'")
        return

    # Fetch ElevenLabs voices and map the number to an ID
    available_voices = fetch_elevenlabs_voices()
    if not available_voices:
        print("Error: No voices retrieved from ElevenLabs API.")
        return

    voice_data = get_voice_id_from_number(voice_number, available_voices)
    if not voice_data:
        print(f"Error: Voice number {voice_number} is out of range. Available voices: {len(available_voices)}")
        return

    elevenlabs_voice_id = voice_data["voice_id"]
    voice_name = voice_data["name"]

    # Debugging: Save and print the matched voice ID
    print(f"Mapped voice number {voice_number} to ElevenLabs voice ID: {elevenlabs_voice_id} ({voice_name})")

    try:
        timestamp_obj = datetime.strptime(timestamp_raw, "%m/%d/%Y %H:%M:%S")
        timestamp_formatted = timestamp_obj.strftime("%Y%m%d-%H%M%S")  # Match original ElevenLabs format
    except ValueError:
        print(f"Error: Invalid timestamp format in {csv_filename}")
        return

    folder_name = os.path.splitext(csv_filename)[0]
    os.makedirs(folder_name, exist_ok=True)

    # Save metadata
    def create_text_file(filename, content):
        with open(os.path.join(folder_name, filename), "w", encoding="utf-8") as f:
            f.write(content)

    create_text_file("email.txt", email)
    create_text_file("name.txt", name)
    create_text_file(f"{timestamp_formatted}.txt", text_to_speak)
    create_text_file("voice.txt", str(voice_number))  # Save the extracted voice number

    # Run ElevenLabs API with the extracted voice ID
    audio_filename = generate_speech(text_to_speak, elevenlabs_voice_id, voice_name, timestamp_formatted, folder_name)
    if audio_filename:
        print(f"Generated speech file: {audio_filename}")

    os.chdir(original_working_dir)
    print(f"Returned to original directory: {os.getcwd()}")

    # Send email with the generated MP3 file
    send_email_with_applescript(os.path.join(original_working_dir, folder_name), audio_filename)

def generate_speech(text, voice_id, voice_name, timestamp, folder):
    """Generate speech using ElevenLabs API and save using original naming format."""
    import os

    # Construct filename and path
    filename = os.path.join(folder, f"elevenlabs-{timestamp}-{voice_name}.mp3")

    # ✅ Ensure the directory exists before writing
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"Accept": "audio/mpeg", "xi-api-key": api_key}
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        try:
            with open(filename, "wb") as file:
                file.write(response.content)
            print(f"✅ Audio saved as {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error saving MP3 file: {e}")
            return None
    else:
        print(f"❌ Failed to generate speech: {response.status_code}, {response.text}")
        return None

def send_email_with_applescript(folder_path, audio_filename):
    """Sends an email with the MP3 file as an attachment."""
    applescript_code = f'''
    set targetFolder to POSIX path of "{folder_path}/"
    set emailFilePath to targetFolder & "email.txt"
    
    if (do shell script "[ -f " & quoted form of POSIX path of emailFilePath & " ] && echo 'true' || echo 'false'") is "true" then
        try
            set emailaddy to do shell script "cat " & quoted form of POSIX path of emailFilePath
        on error
            set emailaddy to "Error: Could not read email.txt"
        end try
    else
        set emailaddy to "Error: email.txt not found in the folder"
    end if

    if emailaddy does not contain "Error" then
        set nameFilePath to targetFolder & "name.txt"
        try
            set nameFileContent to do shell script "cat " & quoted form of POSIX path of nameFilePath
        on error
            set nameFileContent to "Name not found"
        end try

        set greeting to "Hi " & nameFileContent & ","
        set currentDate to current date
        set formattedDate to (currentDate as string)

        set audioFile to POSIX file (targetFolder & "{os.path.basename(audio_filename)}")

        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"ElevenLabs Output - " & formattedDate, content:greeting & return & return & "Here is the speech file generated from your text input." & return & "Please review and let me know if any changes are needed." & return & return & "Best regards," & return & "Dr. Rose", visible:true}}
            tell newMessage
                make new to recipient at end of to recipients with properties {{address:emailaddy}}
                make new attachment with properties {{file name: audioFile}} at after last paragraph
            end tell
            activate
            send newMessage
        end tell
    end if
    '''

    script_path = os.path.join(folder_path, "send_email.applescript")
    with open(script_path, "w") as script_file:
        script_file.write(applescript_code)

    subprocess.run(["osascript", script_path], check=True)
    os.remove(script_path)

# Run script if given a CSV filename
if len(sys.argv) != 2:
    print("Usage: python script.py <csv_filename>")
else:
    process_csv(sys.argv[1])