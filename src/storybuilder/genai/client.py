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
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def parse_speech_config(markdown_content):
    """Parses the markdown content to extract speakers and voices, dynamically matching active speakers in the transcript."""
    # 1. Parse all voice mappings defined in the preamble
    speaker_to_voice = {}
    preamble = ""
    transcript = ""
    
    parts = markdown_content.split('#### TRANSCRIPT')
    if len(parts) == 2:
        preamble, transcript = parts[0], parts[1]
    else:
        preamble = markdown_content
        transcript = ""
        
    for line in preamble.split('\n'):
        line = line.strip()
        if line.startswith('*') or line.startswith('-'):
            match = re.search(r'[\*\-]\s*([A-Za-z0-9_-]+)\s*\(Voice:\s*([A-Za-z0-9_-]+)\)', line)
            if match:
                speaker = match.group(1)
                voice = match.group(2)
                speaker_to_voice[speaker] = voice

    # 2. Extract active speakers actually speaking in the transcript (in order of appearance)
    active_speakers = []
    for line in transcript.split('\n'):
        line = line.strip()
        match = re.match(r'^([A-Za-z0-9_-]+):', line)
        if match:
            sp = match.group(1)
            if sp not in active_speakers:
                active_speakers.append(sp)

    # 3. Build speech_config using the active speakers
    speech_config = []
    for sp in active_speakers:
        if sp in speaker_to_voice:
            speech_config.append({"speaker": sp, "voice": speaker_to_voice[sp]})
        else:
            # Fallback if an active speaker has no voice defined
            speech_config.append({"speaker": sp, "voice": "Kore"})
        if len(speech_config) == 2:
            break

    # If the transcript doesn't have active speakers, fallback to the preamble's first defined speakers
    if not speech_config:
        for sp, vc in list(speaker_to_voice.items())[:2]:
            speech_config.append({"speaker": sp, "voice": vc})

    # Final validation/padding
    if not speech_config:
        speech_config.append({"voice": "Kore"})
    elif len(speech_config) == 1:
        # Force multi-speaker mode by padding with a dummy speaker to prevent 400 Invalid Input errors
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
        with open(md_file, 'r') as f:
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
                    
                    # Dynamically extract sample rate from mime_type if available
                    sample_rate = 24000
                    if hasattr(interaction.output_audio, "mime_type") and interaction.output_audio.mime_type:
                        rate_match = re.search(r"rate=(\d+)", interaction.output_audio.mime_type)
                        if rate_match:
                            sample_rate = int(rate_match.group(1))
                            print(f"  Extracted sample rate from mime_type: {sample_rate}Hz")
                            
                    wave_file(wav_file, audio_bytes, rate=sample_rate)
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
