import argparse
import pathlib
import re
import subprocess  # noqa: S404
import sys






def natural_sort_key(s: str) -> list[object]:
    """Sort strings containing numbers naturally."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


def get_audio_player() -> list[str]:
    if sys.platform == "darwin":
        return ["afplay"]
    if sys.platform == "win32":
        return ["powershell", "-c", "(New-Object Media.SoundPlayer '{0}').PlaySync();"]
    # Assuming linux
    return ["aplay", "-q"]


def play_sequence(directory: str) -> None:
    dir_path = pathlib.Path(directory)
    files = sorted(
        [str(p) for p in dir_path.glob("*-part.wav")],
        key=natural_sort_key,
    )




    if not files:
        print(f"No audio files found in {directory}")
        return

    print(f"Found {len(files)} audio files. Playing sequentially...")

    player_cmd = get_audio_player()

    for i, wav_file in enumerate(files, 1):
        wav_path = pathlib.Path(wav_file)
        print(f"Playing [{i}/{len(files)}]: {wav_path.name}")

        if sys.platform == "win32":
            cmd = [player_cmd[0], player_cmd[1], player_cmd[2].format(wav_file)]
        else:
            cmd = [*player_cmd, wav_file]

        try:
            subprocess.run(cmd, check=True)  # noqa: S603
        except subprocess.CalledProcessError as e:
            print(f"Error playing {wav_path.name}: {e}")
        except KeyboardInterrupt:
            print("\nPlayback stopped by user.")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play a sequence of TTS audio files.")
    parser.add_argument(
        "--dir",
        default="stories/the_secret_vacation",
        help="Directory containing the *-part.wav files",
    )
    args = parser.parse_args()

    if pathlib.Path(args.dir).is_dir():
        play_sequence(args.dir)
    else:
        print(f"Error: Directory '{args.dir}' does not exist.")
