import argparse
import glob
import os
import pathlib
import re
import time
import wave

import requests
from dotenv import load_dotenv


load_dotenv()

# Map common Gemini/custom voice names to official Cartesia Emotive voice IDs
VOICE_MAP = {
    "algenib": "6776173b-fd72-460d-89b3-d85812ee518d",  # Jace (Masculine, deep)
    "leo": "0834f3df-e650-4766-a20c-5a93a43aa6e3",  # Leo (Masculine)
    "gavin": "f4a3a8e4-694c-4c45-9ca0-27caf97901b5",  # Gavin (Masculine)
    "kyle": "c961b81c-a935-4c17-bfb3-ba2239de8c2f",  # Kyle (Masculine)
    "puck": "f4a3a8e4-694c-4c45-9ca0-27caf97901b5",  # Gavin as Puck
    "enceladus": "c961b81c-a935-4c17-bfb3-ba2239de8c2f",  # Kyle as Enceladus
    "kore": "cbaf8084-f009-4838-a096-07ee2e6612b1",  # Maya as Kore (Feminine)
    "tessa": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Tessa (Feminine)
    "dana": "cc00e582-ed66-4004-8336-0175b85c85f6",  # Dana (Feminine)
    "marian": "26403c37-80c1-4a1a-8692-540551ca2ae5",  # Marian (Feminine)
    "zubenelgenubi": "c961b81c-a935-4c17-bfb3-ba2239de8c2f",  # Kyle as Zubenelgenubi
    "narrator": "cbaf8084-f009-4838-a096-07ee2e6612b1",  # Maya as Narrator
}

# Fallback voice ID mapping based on lowercase speaker name
NAME_FALLBACK_MAP = {
    "jace": "6776173b-fd72-460d-89b3-d85812ee518d",  # Jace (Masculine, deep)
    "levi": "c961b81c-a935-4c17-bfb3-ba2239de8c2f",  # Kyle as Levi
    "ewan": "f4a3a8e4-694c-4c45-9ca0-27caf97901b5",  # Gavin as Ewan
    "kerry": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Tessa as Kerry
    "narrator": "cbaf8084-f009-4838-a096-07ee2e6612b1",  # Maya as Narrator
    "default": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",  # Tessa as Default
}


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2) -> None:
    """Writes raw PCM s16le bytes to a standard WAV container."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def parse_speech_config_cartesia(markdown_content):
    """
    Parses the markdown content preamble to map speakers to Cartesia voice UUIDs.
    If a character is mapped to a GenAI voice name, resolves it via VOICE_MAP.
    """
    speaker_to_voice_id = {}

    parts = markdown_content.split("#### TRANSCRIPT")
    preamble = parts[0] if len(parts) == 2 else markdown_content

    for line in preamble.split("\n"):
        line = line.strip()
        if line.startswith(("*", "-")):
            match = re.search(r"[\*\-]\s*([A-Za-z0-9_-]+)\s*\(Voice:\s*([A-Za-z0-9_-]+)\)", line)
            if match:
                speaker = match.group(1)
                voice_ref = match.group(2)

                # Check if voice_ref is already a UUID format
                if re.match(
                    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                    voice_ref.lower(),
                ):
                    speaker_to_voice_id[speaker] = voice_ref.lower()
                else:
                    # Resolve common voice names
                    resolved_voice_id = VOICE_MAP.get(voice_ref.lower(), NAME_FALLBACK_MAP["default"])
                    speaker_to_voice_id[speaker] = resolved_voice_id

    return speaker_to_voice_id


def _parse_line_speaker_and_text(line: str) -> tuple[str, str]:
    match = re.match(r"^([A-Za-z0-9_-]+):", line)
    if match:
        speaker = match.group(1)
        text = line[match.end() :].strip()
    else:
        speaker = "Narrator"
        text = line
    return speaker, text.strip("\"'")


def _resolve_voice_id(speaker: str, speaker_to_voice_id: dict, default_voice_id: str) -> str:
    voice_id = speaker_to_voice_id.get(speaker)
    if voice_id:
        return voice_id
    # Try name-based fallback matching
    voice_id = NAME_FALLBACK_MAP.get(speaker.lower())
    if voice_id:
        return voice_id
    # Fallback to the default narrator/first speaker
    return default_voice_id


def parse_transcript_segments(markdown_content, speaker_to_voice_id, default_voice_id):
    """
    Parses the transcript section into contiguous segments spoken by the same voice ID.
    This minimizes API requests by grouping adjacent lines spoken by the same character.
    """
    parts = markdown_content.split("#### TRANSCRIPT")
    transcript = parts[1] if len(parts) == 2 else markdown_content

    segments = []
    current_voice_id = None
    current_lines = []

    for line in transcript.split("\n"):
        speaker, text = _parse_line_speaker_and_text(line.strip())
        if not text:
            continue

        voice_id = _resolve_voice_id(speaker, speaker_to_voice_id, default_voice_id)

        if voice_id == current_voice_id:
            current_lines.append(text)
        else:
            if current_lines:
                segments.append((current_voice_id, " ".join(current_lines)))
            current_voice_id = voice_id
            current_lines = [text]

    if current_lines:
        segments.append((current_voice_id, " ".join(current_lines)))

    return segments


def generate_segment_audio(api_key, text, voice_id, rate=24000):
    """
    Calls Cartesia's REST API endpoint /tts/bytes to synthesize a single speech segment.
    Returns the raw PCM s16le bytes.
    """
    url = "https://api.cartesia.ai/tts/bytes"
    headers = {
        "Cartesia-Version": "2026-03-01",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model_id": "sonic-latest",
        "transcript": text,
        "voice": {"mode": "id", "id": voice_id},
        "output_format": {
            "container": "raw",
            "encoding": "pcm_s16le",
            "sample_rate": rate,
        },
        "language": "en",
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                return response.content
            if response.status_code == 429:
                wait_time = 10 * (attempt + 1)
                print(
                    f"  Cartesia Rate Limit (429). Retrying in {wait_time}s... ({attempt + 1}/{max_retries})",
                )
                time.sleep(wait_time)
            else:
                print(f"  Cartesia error {response.status_code}: {response.text}")
                response.raise_for_status()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = 5 * (attempt + 1)
            print(f"  Request error: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to generate segment after {max_retries} attempts.")


def process_file_cartesia(md_file, wav_file, api_key, rate=24000):
    """Processes a single markdown file and generates matched WAVs using Cartesia."""
    print(f"Processing {os.path.basename(md_file)} with Cartesia...")
    content = pathlib.Path(md_file).read_text()

    # Parse voice mappings
    speaker_to_voice_id = parse_speech_config_cartesia(content)

    # Determine default narrator voice (first defined, or Maya fallback)
    default_voice_id = next(iter(speaker_to_voice_id.values())) if speaker_to_voice_id else NAME_FALLBACK_MAP["narrator"]

    # Parse dialogue segments
    segments = parse_transcript_segments(content, speaker_to_voice_id, default_voice_id)
    print(f"  Parsed {len(segments)} narrative segments.")

    # Sequentially synthesize each segment and accumulate raw PCM data
    accumulated_pcm = b""
    success = True

    for idx, (voice_id, text) in enumerate(segments):
        print(
            f"  Synthesizing segment {idx + 1}/{len(segments)} (Voice ID: {voice_id[:8]}...): {text[:40]}...",
        )
        try:
            segment_pcm = generate_segment_audio(api_key, text, voice_id, rate=rate)
            accumulated_pcm += segment_pcm
            # Short rest between segment API calls to respect rate limits
            time.sleep(0.5)
        except Exception as e:
            print(f"  Failed to synthesize segment {idx + 1}: {e}")
            success = False
            break

    if success and accumulated_pcm:
        # Save accumulated PCM bytes as a unified WAV file
        wave_file(wav_file, accumulated_pcm, rate=rate)
        print(f"  Saved unified audio to {os.path.basename(wav_file)}")
    else:
        print("  Skipped saving WAV due to synthesis failure.")


def process_directory_cartesia(directory, rate=24000):
    """Processes a directory of scene part markdown files and generates matched WAVs using Cartesia."""
    api_key = os.getenv("CARTESIA_API_KEY")
    if not api_key:
        print("Error: CARTESIA_API_KEY not found in environment.")
        return

    # Find all *-part.md files in the directory
    files = sorted(glob.glob(os.path.join(directory, "*-part.md")))
    if not files:
        print(f"No prompt files found in {directory}")
        return

    print(f"Found {len(files)} prompt files to process using Cartesia API.")

    for md_file in files:
        base_name = os.path.splitext(os.path.basename(md_file))[0]
        wav_file = os.path.join(directory, f"{base_name}.wav")

        # Check if already generated
        if pathlib.Path(wav_file).exists():
            print(f"Skipping {os.path.basename(md_file)}, {os.path.basename(wav_file)} already exists.")
            continue

        process_file_cartesia(md_file, wav_file, api_key, rate=rate)
        # Brief sleep between files
        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process TTS prompt files using Cartesia API.")
    parser.add_argument(
        "--dir",
        default="stories/the_secret_vacation",
        help="Directory containing the *-part.md files",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=24000,
        help="Audio output sample rate (default 24000)",
    )
    args = parser.parse_args()

    if pathlib.Path(args.dir).is_dir():
        process_directory_cartesia(args.dir, rate=args.rate)
    else:
        print(f"Error: Directory '{args.dir}' does not exist.")
