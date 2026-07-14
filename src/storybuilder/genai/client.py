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


def wave_file_writer(filename, pcm, channels=1, rate=24000, sample_width=2) -> None:
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def _parse_voice_mappings(markdown_content):
    """Parses the markdown content to extract speaker to voice mappings and the transcript."""
    speaker_to_voice = {}
    speakers = []

    parts = markdown_content.split("#### TRANSCRIPT")
    if len(parts) == 2:
        preamble, transcript = parts[0], parts[1]
    else:
        preamble = markdown_content
        transcript = ""
    for line in preamble.split("\n"):
        line = line.strip()
        if line.startswith(("*", "-")):
            match = re.search(r"[\*\-]\s*([A-Za-z0-9_-]+)\s*\(Voice:\s*([A-Za-z0-9_-]+)\)", line)
            if match:
                speaker = match.group(1)
                voice = match.group(2)
                speaker_to_voice[speaker] = voice
                if speaker not in speakers:
                    speakers.append(speaker)
    transcript_text = transcript.strip() if isinstance(transcript, str) else ""
    return speaker_to_voice, speakers, transcript_text


def _extract_active_speakers(transcript):
    """Extracts active speakers actually speaking in the transcript in order of appearance."""
    active_speakers = []
    if transcript is None:
        return active_speakers
    if isinstance(transcript, list):
        return transcript
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
            speech_config.append({"speaker": sp, "voice": "Kore"})
        if len(speech_config) == 2:
            break

    if not speech_config:
        for sp, vc in list(speaker_to_voice.items())[:2]:
            speech_config.append({"speaker": sp, "voice": vc})

    if not speech_config:
        speech_config.append({"voice": "Kore"})
    elif len(speech_config) == 1:
        speech_config.append({"speaker": "Dummy", "voice": "Puck"})

    return speech_config


def parse_speech_config(markdown_content):
    """Parses the markdown content to extract speakers and voices, dynamically matching active speakers in the transcript."""
    speaker_to_voice, _, transcript = _parse_voice_mappings(markdown_content)
    active_speakers = _extract_active_speakers(transcript)
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


def _classify_error(error_msg: str) -> tuple[bool, bool, bool, bool]:
    error_lower = error_msg.lower()
    is_invalid_key = (
        "api key not valid" in error_lower
        or "api_key_invalid" in error_lower
        or "modality" in error_lower
        or "400" in error_msg
    )
    is_quota = "429" in error_msg or "too_many_requests" in error_lower or "quota" in error_lower
    is_session_not_found = (
        "404" in error_msg or "not_found" in error_lower or "requested entity was not found" in error_lower
    )
    is_unauthorized = "unauthorized" in error_lower or "401" in error_msg
    return is_invalid_key, is_quota, is_session_not_found, is_unauthorized


def _handle_exception(e, api_state, previous_id, attempt, md_file):
    is_invalid_key, is_quota, is_session_not_found, is_unauthorized = _classify_error(str(e))
    md_name = pathlib.Path(md_file).name

    if is_session_not_found and previous_id is not None:
        print(f"  Session ID {previous_id} not found or expired.")
        return _prompt_key_rotation(api_state, previous_id, md_file)

    if is_invalid_key or is_unauthorized:
        print(f"  Invalid/unauthorized key error for {md_name}: {e}")
        return _prompt_key_rotation(api_state, previous_id, md_file)

    if is_quota:
        if attempt < 4:
            wait_time = 15 * (2 ** attempt)
            print(f"  Quota hit on {md_name}. Retrying with backoff in {wait_time}s... (Attempt {attempt + 1}/5)")
            time.sleep(wait_time)
            return previous_id, attempt + 1, True
        else:
            print(f"  Quota still hit after {attempt + 1} retries. Exhausted retries for now.")
            return previous_id, attempt, False

    print(f"  Error processing {md_name}: {e}")
    return previous_id, attempt, False


def _prompt_key_rotation(api_state, previous_id, md_file):
    """Ask user if they want to rotate keys after session expiration (voice mismatch risk)."""
    md_name = pathlib.Path(md_file).name
    print(f"  Session expired for {md_name}. Continuing with a new key will cause voice mismatch.")
    print("  Options:")
    print("    [S] Skip this file and continue (preserves session for next file)")
    print("    [Q] Quit and let user restart from this file with fresh session")
    print("    [K] Rotate to next key and continue (voice mismatch likely)")
    print("    [A] Rotate to next key and restart session from this file")

    while True:
        try:
            choice = input("  Choose [S/Q/K/A]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n  Quitting...")
            return previous_id, 0, False

        if choice == "s":
            return previous_id, 0, True
        elif choice == "q":
            print("  Quitting. Run again with the same input to resume from this file.")
            return previous_id, 0, False
        elif choice == "k":
            return _rotate_key(api_state, previous_id, md_file, restart_session=False)
        elif choice == "a":
            return _rotate_key(api_state, previous_id, md_file, restart_session=True)
        else:
            print("  Invalid choice. Please enter S, Q, K, or A.")


def _rotate_key(api_state, previous_id, md_file, restart_session=False):
    """Rotate to next API key, optionally restarting the session."""
    current_key_idx = api_state["current_key_idx"]
    api_keys = api_state["api_keys"]

    if len(api_keys) == 1:
        print(f"  Only one key available. Cannot rotate.")
        return previous_id, 0, False

    next_idx = (current_key_idx + 1) % len(api_keys)
    new_key_name, api_key = api_keys[next_idx]
    print(f"  Rotating to key '{new_key_name}'...")
    api_state["current_key_idx"] = next_idx
    api_state["client"] = genai.Client(api_key=api_key)

    if restart_session:
        print("  Restarting session from this file (voice mismatch expected).")
        return None, 0, True
    else:
        print("  Continuing without session history (voice mismatch possible).")
        return None, 0, True


def _save_audio_from_interaction(interaction, wav_file, md_file) -> None:
    if not (interaction.output_audio and interaction.output_audio.data):
        print(f"  Warning: No audio output for {pathlib.Path(md_file).name}")
        return

    audio_bytes = base64.b64decode(interaction.output_audio.data)
    sample_rate = 24000

    mime_type = getattr(interaction.output_audio, "mime_type", None)
    if mime_type:
        rate_match = re.search(r"rate=(\d+)", mime_type)
        if rate_match:
            sample_rate = int(rate_match.group(1))
            print(f"  Extracted sample rate from mime_type: {sample_rate}Hz")

    wave_file(wav_file, audio_bytes, rate=sample_rate)
    print(f"  Saved audio to {pathlib.Path(wav_file).name}")


def process_file(md_file, wav_file, previous_id, api_state):
    client = api_state["client"]
    api_keys = api_state["api_keys"]
    current_key_idx = api_state["current_key_idx"]
    api_keys[current_key_idx][0]

    print(f"Processing {pathlib.Path(md_file).name}...")
    content = pathlib.Path(md_file).read_text(encoding="utf-8")

    speech_config = parse_speech_config(content)
    print(f"  Speech config: {speech_config}")

    max_retries = 5
    attempt = 0
    while attempt < max_retries:
        try:
            interaction = client.interactions.create(
                model="gemini-3.1-flash-tts-preview",
                input=content,
                response_modalities=["audio"],
                generation_config={"speech_config": speech_config},
                previous_interaction_id=previous_id,
            )
        except Exception as e:
            previous_id, attempt, should_continue = _handle_exception(
                e,
                api_state,
                previous_id,
                attempt,
                md_file,
            )
            if should_continue:
                client = api_state["client"]
                continue
            raise
        else:
            _save_audio_from_interaction(interaction, wav_file, md_file)
            previous_id = interaction.id
            break
    else:
        print(
            f"  Failed to process {pathlib.Path(md_file).name} after {max_retries} attempts.",
        )

    return previous_id


def process_directory(directory) -> None:
    api_keys = get_gemini_api_keys()
    if not api_keys:
        print("Error: No GEMINI_API_KEY or GEMINI_API_KEY_X found in environment.")
        return

    current_key_idx = 0
    _, api_key = api_keys[current_key_idx]
    client = genai.Client(api_key=api_key)

    # Find all *-part.md prompt files in the directory
    files = sorted(glob.glob(os.path.join(directory, "*-part.md")))
    if not files:
        print(f"No prompt files found in {directory}")
        return

    print(f"Found {len(files)} prompt files to process in {directory}.")

    api_state = {
        "client": client,
        "api_keys": api_keys,
        "current_key_idx": current_key_idx,
    }
    previous_id = None
    for md_file in files:
        base_name = os.path.splitext(pathlib.Path(md_file).name)[0]
        wav_file = os.path.join(directory, f"{base_name}.wav")

        if pathlib.Path(wav_file).exists():
            print(f"Skipping {pathlib.Path(md_file).name}, {pathlib.Path(wav_file).name} already exists.")
            continue

        previous_id = process_file(
            md_file,
            wav_file,
            previous_id,
            api_state,
        )

        # Slight delay to respect rate limits
        time.sleep(2)


def main() -> None:
    """Parse CLI arguments and generate TTS audio from prompt files in a directory.

    This is the entrypoint for the ``genai-tts`` console script installed by
    ``pyproject.toml``.  Equivalent to running
    ``python -m storybuilder.genai.client --dir <directory>``.
    """
    parser = argparse.ArgumentParser(description="Process TTS prompt files to generate audio.")
    parser.add_argument(
        "--dir",
        default="stories/the_secret_vacation",
        help="Directory containing the *-part.md prompt files",
    )
    args = parser.parse_args()

    dir_path = pathlib.Path(args.dir)
    if not dir_path.exists():
        parser.error(f"Path '{args.dir}' does not exist.")
    if not dir_path.is_dir():
        parser.error(f"Path '{args.dir}' is not a directory.")

    if not get_gemini_api_keys():
        parser.exit(1, "Error: No GEMINI_API_KEY or GEMINI_API_KEY_X found in environment.\n")

    md_files = sorted(glob.glob(os.path.join(args.dir, "*-part.md")))
    if not md_files:
        parser.exit(1, f"Error: No prompt files found in {args.dir}\n")

    process_directory(args.dir)


if __name__ == "__main__":
    main()
