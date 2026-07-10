import pathlib


<<<<<<< HEAD
def save_prompts(prompts: List[str], file_path: str = "tts_prompts.txt") -> str:
=======
def save_prompts(prompts: list[str], file_path: str = "tts_prompts.txt") -> str:
>>>>>>> palette-fix-duplicate-file-input-1065389564287363483
    """Saves a list of TTS prompts to a specified text file.

    Args:
        prompts: A list of strings, where each string is a TTS prompt.
        file_path: The name of the file to save the prompts to. Defaults to 'tts_prompts.txt'.

    Returns:
        A string confirming that the file was saved.
    """
    try:
        with pathlib.Path(file_path).open("w") as f:
            f.writelines(prompt + "\n" for prompt in prompts)
        return f"Successfully saved {len(prompts)} prompts to {file_path}"
    except Exception as e:
        return f"Error saving prompts to {file_path}: {e}"
