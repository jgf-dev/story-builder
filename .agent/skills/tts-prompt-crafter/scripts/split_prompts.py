import argparse
import glob
import os
import pathlib
import re
import shutil


def split_line_to_sentences(line, speaker):
    """Safely splits an excessively long line into sentences while preserving the speaker prefix."""
    # Find where the prefix ends (handling potential spaces after colon)
    prefix_match = re.match(rf"^{speaker}:\s*", line)
    if not prefix_match:
        return [line]
    prefix_len = prefix_match.end()
    dialogue_content = line[prefix_len:]

    # Split by sentence boundaries, avoiding splitting inside bracketed tags
    # This guarantees the string only splits after a punctuation mark, provided it is not currently inside an open [ bracket.
    sentences = re.split(r"(?<=[.!?])\s+(?![^\[]*\])", dialogue_content)

    result = []
    for s in sentences:
        s = s.strip()
        if s:
            result.append(f"{speaker}: {s}")
    return result


def filter_preamble_speakers(preamble, active_speakers):
    """Filters the Style bullet points in the preamble to include only active speakers."""
    lines = preamble.split("\n")
    new_lines = []
    for line in lines:
        # Match lines like: - Jace (Voice: Algenib): Intimate, deep.
        match = re.search(
            r"^\s*[\*\-]\s*([A-Za-z0-9_-]+)\s*\(Voice:\s*([A-Za-z0-9_-]+)\)", line,
        )
        if match:
            speaker = match.group(1)
            if speaker in active_speakers:
                new_lines.append(line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def process_files(input_dir):
    files = sorted(glob.glob(os.path.join(input_dir, "*-scene*.md")))
    if not files:
        print(f"No scene files found in {input_dir}")
        return

    file_counter = 1

    # Ensure archive directory exists
    archive_dir = os.path.join(input_dir, "archive")
    pathlib.Path(archive_dir).mkdir(exist_ok=True, parents=True)

    for filepath in files:
        content = pathlib.Path(filepath).read_text()

        parts = re.split(r"^#### TRANSCRIPT\s*$", content, flags=re.MULTILINE)
        if len(parts) != 2:
            print(f"Skipping {filepath} - no TRANSCRIPT section found.")
            continue

        preamble = parts[0]
        transcript_text = parts[1].strip()

        # Split transcript into blocks of max 2 speakers AND max 1800 characters
        lines = re.split(r"[\r\n]+", transcript_text)
        chunks = []
        current_chunk = []
        current_speakers = set()
        current_len = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Validate brackets symmetry to prevent orphaned brackets
            if line.count("[") != line.count("]"):
                raise ValueError(f"Orphaned bracket detected in line: {line}")

            # Warn about adjacent tags (e.g., [sighs][whispers]) which cause TTS API parsing errors
            adjacent_tags = re.findall(r"\]\[", line)
            if adjacent_tags:
                print(
                    f"WARNING: Adjacent tags detected (will cause TTS API error). "
                    f"Separate with space or punctuation: {line}",
                )

            # Extract speaker prefix
            match = re.match(r"^([A-Za-z0-9_-]+):", line)
            if not match:
                # Malformed line or no speaker, treat as no speaker
                speaker = None
            else:
                speaker = match.group(1)

            # If the line exceeds 1800 characters, split it safely by sentence boundaries
            sub_lines = []
            if speaker and len(line) > 1800:
                sub_lines = split_line_to_sentences(line, speaker)
            else:
                sub_lines = [line]

            for sub_line in sub_lines:
                sub_match = re.match(r"^([A-Za-z0-9_-]+):", sub_line)
                sub_speaker = sub_match.group(1) if sub_match else None

                # Validate 2-Speaker Limit
                if sub_speaker and sub_speaker not in current_speakers:
                    if len(current_speakers) == 2:
                        chunks.append((current_speakers.copy(), current_chunk.copy()))
                        current_chunk = []
                        current_speakers = set()
                        current_len = 0
                    current_speakers.add(sub_speaker)

                # Validate length limit
                if current_len + len(sub_line) > 1800 and current_chunk:
                    chunks.append((current_speakers.copy(), current_chunk.copy()))
                    current_chunk = []
                    current_speakers = set()
                    current_len = 0
                    if sub_speaker:
                        current_speakers.add(sub_speaker)

                current_chunk.append(sub_line)
                current_len += len(sub_line) + 1  # +1 for newline

        if current_chunk:
            chunks.append((current_speakers.copy(), current_chunk.copy()))

        # Write out chunks
        for speakers, t_lines in chunks:
            out_filename = os.path.join(input_dir, f"{file_counter:02d}-part.md")
            file_counter += 1

            # Reconstruct preamble filtering only active speakers
            new_preamble = filter_preamble_speakers(preamble, speakers)

            with pathlib.Path(out_filename).open("w") as f:
                f.write(new_preamble)
                f.write("#### TRANSCRIPT\n")
                f.write("\n".join(t_lines) + "\n")

        # Move the old scene file to archive instead of removing it
        archive_filepath = os.path.join(archive_dir, os.path.basename(filepath))
        shutil.move(filepath, archive_filepath)
        print(f"Processed and archived {filepath} to {archive_filepath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Split TTS scene prompts to respect the 2-voice limit and output length constraints.",
    )
    parser.add_argument("input_dir", help="Directory containing the *-scene*.md files")
    args = parser.parse_args()
    process_files(args.input_dir)
