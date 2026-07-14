"""Tools for the TTS Prompt Crafter ADK agent.

Provides file I/O and prompt splitting as callable functions
that ADK can expose to the LLM as tools.
"""

import glob
import os
import pathlib
import sys


# Add the project root so we can import split_prompts
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."),
)
_STORIES_DIR = os.path.join(_PROJECT_ROOT, "stories", "text")
_SPLIT_SCRIPT_DIR = os.path.join(
    _PROJECT_ROOT,
    ".agent",
    "skills",
    "tts-prompt-crafter",
    "scripts",
)
if _SPLIT_SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SPLIT_SCRIPT_DIR)


def _resolve_absolute_story_path(story_path_or_name: str) -> str | None:
    candidates = [story_path_or_name]
    if not story_path_or_name.endswith(".md"):
        candidates.append(f"{story_path_or_name}.md")
    for candidate in candidates:
        if pathlib.Path(candidate).exists():
            return candidate
    return None


def _resolve_story_path(story_path_or_name: str) -> str | None:
    """Resolve a story name or path to an existing markdown file."""
    if not story_path_or_name:
        return None

    if pathlib.Path(story_path_or_name).is_absolute():
        return _resolve_absolute_story_path(story_path_or_name)

    # Keep explicit relative paths rejected so callers do not accidentally
    # depend on the current working directory.
    if os.path.sep in story_path_or_name or (os.path.altsep and os.path.altsep in story_path_or_name):
        return None

    candidates = [story_path_or_name]
    if not story_path_or_name.endswith(".md"):
        candidates.insert(0, f"{story_path_or_name}.md")

    for candidate in candidates:
        resolved = os.path.join(_STORIES_DIR, candidate)
        if pathlib.Path(resolved).exists():
            return resolved
    return None


def _resolve_output_dir(story_path_or_dir: str) -> str | None:
    """Resolve either a story path or an output directory."""
    if not story_path_or_dir:
        return None

    if pathlib.Path(story_path_or_dir).is_dir():
        return story_path_or_dir

    if pathlib.Path(story_path_or_dir).is_absolute():
        if pathlib.Path(story_path_or_dir).is_file():
            return os.path.join(os.path.dirname(story_path_or_dir), "output")
        if story_path_or_dir.endswith(".md"):
            return None
        return story_path_or_dir

    if os.path.sep in story_path_or_dir or (os.path.altsep and os.path.altsep in story_path_or_dir):
        return None

    story_path = _resolve_story_path(story_path_or_dir)
    if story_path:
        return os.path.join(os.path.dirname(story_path), "output")
    return None


def read_story(story_path: str) -> str:
    """Read a story from disk by absolute path or story name.

    Args:
        story_path: The absolute path to the story markdown file or a
            story name that exists under ``stories/text``.

    Returns:
        The full text content of the story file.
    """
    resolved = _resolve_story_path(story_path)
    if not resolved:
        if pathlib.Path(story_path).is_absolute():
            return f"Error: Story file not found at {story_path}"
        if os.path.sep in story_path or (os.path.altsep and os.path.altsep in story_path):
            return f"Error: story_path must be an absolute path. Got: {story_path}"
        return f"Error: Story file not found for name '{story_path}' in {_STORIES_DIR}"

    if not pathlib.Path(resolved).exists():
        return f"Error: Story file not found at {story_path}"
    with pathlib.Path(resolved).open() as f:
        return f.read()


def list_stories(directory: str | None = None) -> str:
    """List available story markdown files in a directory.

    Args:
        directory: The absolute path to the directory containing story files.
            If omitted, defaults to ``stories/text``.

    Returns:
        A newline-separated list of story file paths found in the directory.
    """
    if directory is None:
        directory = _STORIES_DIR
    if not pathlib.Path(directory).is_absolute():
        return f"Error: directory must be an absolute path. Got: {directory}"
    if not pathlib.Path(directory).is_dir():
        return f"Error: Directory not found at {directory}"
    files = sorted(glob.glob(os.path.join(directory, "*.md")))
    if not files:
        return f"No .md files found in {directory}"
    return "\n".join(files)


def _get_validated_output_dir(story_path: str) -> tuple[str | None, str | None]:
    """Validate story_path and return (output_dir, error_message)."""
    output_dir = _resolve_output_dir(story_path)
    if not output_dir:
        if os.path.sep in story_path or (os.path.altsep and os.path.altsep in story_path):
            return (
                None,
                f"Error: story_path must be an absolute path. Got: {story_path}",
            )
        return None, f"Error: Could not resolve output directory for {story_path}"
    return output_dir, None


def _format_split_results(output_dir: str) -> str:
    """Format the results of split_prompts for the ADK agent."""
    part_files = sorted(glob.glob(os.path.join(output_dir, "*-part.md")))
    archived = sorted(glob.glob(os.path.join(output_dir, "archive", "*-scene*.md")))

    result_lines = [
        f"Split complete. Generated {len(part_files)} part file(s):",
    ]
    for pf in part_files:
        result_lines.append(f"  - {os.path.basename(pf)}")
    if archived:
        result_lines.append(
            f"Archived {len(archived)} original scene file(s) to output/archive/",
        )

    return "\n".join(result_lines)


def write_scene_file(story_path: str, filename: str, content: str) -> str:
    """Write a TTS scene prompt file to the resolved output directory.

    The first argument can be either a story path or an existing output
    directory. When a story path is provided, the output directory is created
    as a sibling ``output`` subdirectory next to the story file.

    Args:
        story_path: The absolute path to the original story file or an
            output directory path.
        filename: The scene filename to create (e.g. '01-scene1.md').
            Must match the glob pattern '*-scene*.md'.
        content: The full markdown content of the scene prompt file.

    Returns:
        A confirmation message with the path of the written file.
    """
    output_dir, error = _get_validated_output_dir(story_path)
    if error:
        return error

    pathlib.Path(output_dir).mkdir(exist_ok=True, parents=True)

    # Validate filename pattern
    if "-scene" not in filename or not filename.endswith(".md"):
        return f"Error: filename must match '*-scene*.md' pattern. Got: {filename}"

    filepath = os.path.join(output_dir, filename)
    pathlib.Path(filepath).write_text(content)
    return f"Successfully wrote scene file to {filepath}"


def split_scene_files(story_path: str) -> str:
    """Split TTS scene prompt files to respect the 2-voice limit.

    Runs the split_prompts processor on the resolved output directory.
    This chunks scene files by speaker count (max 2) and character length
    (max 1800), producing sequentially numbered '*-part.md' files.

    Args:
        story_path: The absolute path to the original story file or an
            existing output directory path.

    Returns:
        A status message listing the resulting part files.
    """
    output_dir, error = _get_validated_output_dir(story_path)
    if error:
        return error

    if not pathlib.Path(output_dir).is_dir():
        return f"Error: Output directory not found at {output_dir}"

    scene_files = glob.glob(os.path.join(output_dir, "*-scene*.md"))
    if not scene_files:
        return f"Error: No *-scene*.md files found in {output_dir}"

    try:
        from split_prompts import process_files  # pylint: disable=import-error

        process_files(output_dir)
    except Exception as e:
        return f"Error running splitter: {e}"

    return _format_split_results(output_dir)
