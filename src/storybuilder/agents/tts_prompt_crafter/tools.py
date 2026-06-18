"""Tools for the TTS Prompt Crafter ADK agent.

Provides file I/O and prompt splitting as callable functions
that ADK can expose to the LLM as tools.
"""

import glob
import os
import sys

# Add the project root so we can import split_prompts
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
_SPLIT_SCRIPT_DIR = os.path.join(
    _PROJECT_ROOT, ".agent", "skills", "tts-prompt-crafter", "scripts"
)
if _SPLIT_SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SPLIT_SCRIPT_DIR)


def read_story(story_path: str) -> str:
    """Read a story file from disk given its full absolute path.

    Args:
        story_path: The absolute path to the story markdown file
            (e.g. '/home/user/stories/text/my_story.md').

    Returns:
        The full text content of the story file.
    """
    if not os.path.isabs(story_path):
        return f"Error: story_path must be an absolute path. Got: {story_path}"
    if not os.path.exists(story_path):
        return f"Error: Story file not found at {story_path}"
    with open(story_path, "r") as f:
        return f.read()


def list_stories(directory: str) -> str:
    """List available story markdown files in a directory.

    Args:
        directory: The absolute path to the directory containing story files.

    Returns:
        A newline-separated list of story file paths found in the directory.
    """
    if not os.path.isabs(directory):
        return f"Error: directory must be an absolute path. Got: {directory}"
    if not os.path.isdir(directory):
        return f"Error: Directory not found at {directory}"
    files = sorted(glob.glob(os.path.join(directory, "*.md")))
    if not files:
        return f"No .md files found in {directory}"
    return "\n".join(files)


def write_scene_file(story_path: str, filename: str, content: str) -> str:
    """Write a TTS scene prompt file to an 'output' subdirectory next to the story.

    The output directory is created as a sibling 'output' subdirectory
    within the same directory as the source story file.

    Args:
        story_path: The absolute path to the original story file. Used to
            determine the output directory location.
        filename: The scene filename to create (e.g. '01-scene1.md').
            Must match the glob pattern '*-scene*.md'.
        content: The full markdown content of the scene prompt file.

    Returns:
        A confirmation message with the path of the written file.
    """
    if not os.path.isabs(story_path):
        return f"Error: story_path must be an absolute path. Got: {story_path}"

    # Derive the output directory: same parent as story, in an 'output' subdir
    story_dir = os.path.dirname(story_path)
    output_dir = os.path.join(story_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Validate filename pattern
    if "-scene" not in filename or not filename.endswith(".md"):
        return (
            f"Error: filename must match '*-scene*.md' pattern. "
            f"Got: {filename}"
        )

    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return f"Successfully wrote scene file to {filepath}"


def split_scene_files(story_path: str) -> str:
    """Split TTS scene prompt files to respect the 2-voice limit.

    Runs the split_prompts processor on the 'output' subdirectory
    next to the given story file. This chunks scene files by speaker
    count (max 2) and character length (max 1800), producing
    sequentially numbered '*-part.md' files.

    Args:
        story_path: The absolute path to the original story file. Used to
            determine the output directory containing scene files.

    Returns:
        A status message listing the resulting part files.
    """
    if not os.path.isabs(story_path):
        return f"Error: story_path must be an absolute path. Got: {story_path}"

    story_dir = os.path.dirname(story_path)
    output_dir = os.path.join(story_dir, "output")

    if not os.path.isdir(output_dir):
        return f"Error: Output directory not found at {output_dir}"

    scene_files = glob.glob(os.path.join(output_dir, "*-scene*.md"))
    if not scene_files:
        return f"Error: No *-scene*.md files found in {output_dir}"

    try:
        from split_prompts import process_files

        process_files(output_dir)
    except Exception as e:
        return f"Error running splitter: {e}"

    # Report results
    part_files = sorted(glob.glob(os.path.join(output_dir, "*-part.md")))
    archived = sorted(
        glob.glob(os.path.join(output_dir, "archive", "*-scene*.md"))
    )

    result_lines = [
        f"Split complete. Generated {len(part_files)} part file(s):",
    ]
    for pf in part_files:
        result_lines.append(f"  - {os.path.basename(pf)}")
    if archived:
        result_lines.append(
            f"Archived {len(archived)} original scene file(s) to output/archive/"
        )

    return "\n".join(result_lines)
