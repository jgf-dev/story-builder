import argparse
import base64
import glob
import os
import pathlib
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


def _parse_voice_mappings(markdown_content):
    """Parses the markdown content to extract speaker to voice mappings and the transcript."""
    speaker_to_voice = {}

    parts = markdown_content.split("#### TRANSCRIPT")
    if len(parts) == 2:
        preamble, transcript = parts[0], parts[1]
    else:
        preamble = markdown_content
        transcript = ""
    for line in preamble.split("\n"):
        line = line.strip()
        if line.startswith("*") or line.startswith("-"):
            match = re.search(r"[\*\-]\s*([A-Za-z0-9_-]+)\s*\(Voice:\s*([A-Za-z0-9_-]+)\)", line)
            if match:
                speaker = match.group(1)
                voice = match.group(2)
                speaker_to_voice[speaker] = voice

    return speaker_to_voice, transcript


def _extract_active_speakers(transcript):
    """Extracts active speakers actually speaking in the transcript in order of appearance."""
    active_speakers = []
    for line in transcript.split("\n"):
        line = line.strip()
        match = re.match(r"^([A-Za-z0-9_-]+):", line)
        if match:
            sp = match.group(1)
            if sp not in active_speakers:
                active_speakers.append(sp)
    return active_speakers


def _build_speech_config(active_speakers, speaker_to_voice):
    """Builds the final speech config array with fallbacks and padding."""
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


def parse_speech_config(markdown_content):
    """Parses the markdown content to extract speakers and voices, dynamically matching active speakers in the transcript."""
    # 1. Parse all voice mappings defined in the preamble
    speaker_to_voice, transcript = _parse_voice_mappings(markdown_content)

    # 2. Extract active speakers actually speaking in the transcript (in order of appearance)
    active_speakers = _extract_active_speakers(transcript)

    # 3. Build speech_config using the active speakers
    return _build_speech_config(active_speakers, speaker_to_voice)


def get_gemini_api_keys():
    keys = []
    primary = os.getenv("GEMINI_API_KEY")
    if primary:
        keys.append(("GEMINI_API_KEY", primary))
    idx = 1
    while True:
        key = os.getenv(f"GEMINI_API_KEY_{idx}")
        if key:
            keys.append((f"GEMINI_API_KEY_{idx}", key))
            idx += 1
        else:
            break
    return keys


def process_directory(directory):
    api_keys = get_gemini_api_keys()
    if not api_keys:
        print("Error: No GEMINI_API_KEY or GEMINI_API_KEY_X found in environment.")
        return

    current_key_idx = 0
    key_name, api_key = api_keys[current_key_idx]
    client = genai.Client(api_key=api_key)

    # Find all *.md prompt files in the directory
    files = sorted(glob.glob(os.path.join(directory, "*.md")))
    if not files:
        print(f"No prompt files found in {directory}")
        return

    print(f"Found {len(files)} prompt files to process in {directory}.")

    previous_id = None
    for md_file in files:
        base_name = os.path.splitext(os.path.basename(md_file))[0]
        wav_file = os.path.join(directory, f"{base_name}.wav")

        if pathlib.Path(wav_file).exists():
            print(f"Skipping {os.path.basename(md_file)}, {os.path.basename(wav_file)} already exists.")
            continue

        print(f"Processing {os.path.basename(md_file)}...")
        content = pathlib.Path(md_file).read_text()

        speech_config = parse_speech_config(content)
        print(f"  Speech config: {speech_config}")

        max_retries = 5
        keys_tried = 0
        attempt = 0
        while attempt < max_retries:
            try:
                interaction = client.interactions.create(
                    model="gemini-3.1-flash-tts-preview",
                    input=content,
                    response_modalities=["audio"],
                    generation_config={"speech_config": speech_config},
                    previous_interaction_id=previous_id,  # TODO: Check if the interaction API supports previous_interaction_id
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

                previous_id = interaction.id  # TODO: check if key rotation breaks
                break

            except Exception as e:
                error_msg = str(e)
                is_invalid_key = (
                    "api key not valid" in error_msg.lower()
                    or "api_key_invalid" in error_msg.lower()
                    or "modality" in error_msg.lower()
                    or "400" in error_msg
                )
                is_quota = (
                    "429" in error_msg or "too_many_requests" in error_msg.lower() or "quota" in error_msg.lower()
                )
                is_session_not_found = (
                    "404" in error_msg
                    or "not_found" in error_msg.lower()
                    or "requested entity was not found" in error_msg.lower()
                )

                if is_session_not_found and previous_id is not None:
                    print(f"  Session ID {previous_id} not found or expired. Retrying without session history.")
                    previous_id = None
                    continue

                if (is_invalid_key or is_quota) and keys_tried < len(
                    api_keys,
                ) - 1:  # TODO: Move key management out of the function
                    print(f"  Error processing {os.path.basename(md_file)} for {key_name}")
                    keys_tried += 1
                    current_key_idx = (current_key_idx + 1) % len(api_keys)
                    key_name, api_key = api_keys[current_key_idx]
                    print(f"  Switching to key '{key_name}' due to error: {e}")
                    client = genai.Client(api_key=api_key)
                    previous_id = None  # Clear session history on key switch
                    continue

                # TODO: Make sure this doesnt happen, session is too important for audio quality
                # TODO: Also make sure the wait time is not above this the session expiry
                # TODO: Alternatively, find a way to ensure audio consistency across retries with the same key
                if is_quota:
                    wait_time = 15 * (attempt + 1)
                    print(
                        f"  Rate limit/Quota hit on all keys. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})",
                    )
                    time.sleep(wait_time)
                    attempt += 1
                    keys_tried = 0
                else:
                    print(f"  Error processing {os.path.basename(md_file)}: {e}")
                    break
        else:
            print(f"  Failed to process {os.path.basename(md_file)} after {max_retries} attempts.")

        # Slight delay to respect rate limits
        time.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process TTS prompt files to generate audio.")
    parser.add_argument(
        "--dir",
        default="stories/the_secret_vacation",
        help="Directory containing the *-part.md files",
    )
    args = parser.parse_args()

    if pathlib.Path(args.dir).is_dir():
        process_directory(args.dir)
    else:
        print(f"Error: Directory '{args.dir}' does not exist.")
