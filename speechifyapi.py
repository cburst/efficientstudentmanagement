import requests
import base64
from datetime import datetime
import os
import sys

# Option 1: Get the API key from the environment variable
api_key = os.getenv("SPEECHIFY_API_KEY")

# Option 2: If the environment variable is not set, use the hardcoded API key
if not api_key:
    api_key = "your_api_key_here"

# Default text to be read
default_text = "Hello, this is a test using your selected voice."

# Check if text is provided via command line arguments
if len(sys.argv) > 1:
    input_text = sys.argv[1].strip('"')  # Take the first argument and strip quotation marks
else:
    input_text = default_text

# Endpoint to get the list of voices
url = "https://api.sws.speechify.com/v1/voices"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    voices = response.json()
    
    simba_english_voices = []
    seen_combinations = set()

    for voice in voices:
        for model in voice['models']:
            if model['name'] == 'simba-english':
                for lang in model['languages']:
                    voice_name = voice['display_name']
                    gender = 'M' if voice['gender'] == 'male' else 'F'
                    region = lang['locale']
                    combination = (voice_name, gender, region)

                    if combination not in seen_combinations:
                        seen_combinations.add(combination)
                        simba_english_voices.append({
                            "name": voice_name,
                            "gender": gender,
                            "region": region,
                            "id": voice['id']
                        })

    if not simba_english_voices:
        print("No Simba English voices found.")
    else:
        print("Available English Voices:")
        for i, voice in enumerate(simba_english_voices):
            print(f"{i + 1}: {voice['name']} - {voice['gender']} - {voice['region']}")

        choice = int(input("\nEnter the number of the voice you want to use: ")) - 1
        selected_voice = simba_english_voices[choice]['id']
        selected_voice_name = simba_english_voices[choice]['name']

        print(f"\nYou selected: {selected_voice_name} - {simba_english_voices[choice]['gender']} - {simba_english_voices[choice]['region']}")

        data = {
            "input": f"<speak>{input_text}</speak>",
            "voice_id": selected_voice,
            "engine": "simba-english",
            "format": "mp3"
        }

        tts_response = requests.post("https://api.sws.speechify.com/v1/audio/speech", json=data, headers=headers)

        if tts_response.status_code == 200:
            audio_data = tts_response.json().get('audio_data')
            if audio_data:
                timestamp = datetime.now().strftime("%m%d%y-%H%M")
                filename = f"speechify-{timestamp}-{selected_voice_name}.mp3"

                with open(filename, "wb") as file:
                    file.write(base64.b64decode(audio_data))
                print(f"Audio saved as {filename}")
            else:
                print("No audio data found in the response.")
        else:
            print(f"Failed to get response: {tts_response.status_code}, {tts_response.text}")
else:
    print(f"Failed to retrieve voices: {response.status_code}, {response.text}")