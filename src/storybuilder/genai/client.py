import argparse
import base64
import glob
import os
import re
import time
import wave

from dotenv import load_dotenv
from google import genai

load_dotenv()

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def parse_speech_config(markdown_content):
    """Parses the markdown content to extract speakers and voices."""
    speech_config = []
    
    for line in markdown_content.split('\n'):
        line = line.strip()
        # Look for bullet points with the voice definition
        if line.startswith('*') or line.startswith('-'):
            match = re.search(r'[\*\-]\s*([A-Za-z0-9_-]+)\s*\(Voice:\s*([A-Za-z0-9_-]+)\)', line)
            if match:
                speaker = match.group(1)
                voice = match.group(2)
                # The API allows a maximum of 2 voices
                if len(speech_config) < 2:
                    speech_config.append({"speaker": speaker, "voice": voice})
                    
    if not speech_config:
        # Fallback if no voice config is found
        speech_config.append({"voice": "Kore"})
    elif len(speech_config) == 1:
        # Force multi-speaker mode by padding with a dummy speaker
        # This prevents 400 Invalid Input errors when a chunk happens to only have one speaker
        speech_config.append({"speaker": "Dummy", "voice": "Puck"})
        
    return speech_config

def process_directory(directory):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        return
        
    client = genai.Client(api_key=api_key)
    
    # Find all *-part.md files in the directory
    files = sorted(glob.glob(os.path.join(directory, "*-part.md")))
    if not files:
        print(f"No prompt files found in {directory}")
        return
        
    print(f"Found {len(files)} prompt files to process in {directory}.")
    
    previous_id = None
    for md_file in files:
        base_name = os.path.splitext(os.path.basename(md_file))[0]
        wav_file = os.path.join(directory, f"{base_name}.wav")
        
        if os.path.exists(wav_file):
            print(f"Skipping {os.path.basename(md_file)}, {os.path.basename(wav_file)} already exists.")
            continue
            
        print(f"Processing {os.path.basename(md_file)}...")
        with open(md_file, "r") as f:
            content = f.read()
            
        speech_config = parse_speech_config(content)
        print(f"  Speech config: {speech_config}")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                interaction = client.interactions.create(
                    model="gemini-3.1-flash-tts-preview",
                    input=content,
                    response_modalities=["audio"],
                    generation_config={"speech_config": speech_config},
                    previous_interaction_id=previous_id
                )
                
                if interaction.output_audio and interaction.output_audio.data:
                    audio_bytes = base64.b64decode(interaction.output_audio.data)
                    wave_file(wav_file, audio_bytes)
                    print(f"  Saved audio to {os.path.basename(wav_file)}")
                else:
                    print(f"  Warning: No audio output for {os.path.basename(md_file)}")
                    
                previous_id = interaction.id
                break
                    
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'too_many_requests' in error_msg.lower() or 'quota' in error_msg.lower():
                    wait_time = 15 * (attempt + 1)
                    print(f"  Rate limit hit (429/Quota). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"  Error processing {os.path.basename(md_file)}: {e}")
                    break
        else:
            print(f"  Failed to process {os.path.basename(md_file)} after {max_retries} attempts.")
            
        # Slight delay to respect rate limits
        time.sleep(2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process TTS prompt files to generate audio.")
    parser.add_argument("--dir", default="stories/the_secret_vacation", help="Directory containing the *-part.md files")
    args = parser.parse_args()
    
    if os.path.isdir(args.dir):
        process_directory(args.dir)
    else:
        print(f"Error: Directory '{args.dir}' does not exist.")
