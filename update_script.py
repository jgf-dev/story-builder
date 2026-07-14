import re

files_to_update_env = [
    "src/storybuilder/agents/tts_prompt_crafter/agent.py",
    "src/storybuilder/genai/fix_prompts2.py",
    "src/storybuilder/genai/cartesia_client.py",
    "src/storybuilder/genai/client.py",
    "src/storybuilder/genai/fix_prompts.py",
    "src/storybuilder/utils/storage.py",
]

def update_file(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Replace import
    content = re.sub(r'from dotenv import load_dotenv\n?', 'from storybuilder.utils.env import load_env\n', content)

    # Replace calls
    if filepath == "src/storybuilder/agents/tts_prompt_crafter/agent.py":
        content = re.sub(r'dotenv_path = pathlib\.Path\(os\.path\.join\(pathlib\.Path\(__file__\)\.parent, "\.\.", "\.\.", "\.\.", "\.\.", "\.env"\)\)\.resolve\(\)\n\s*load_dotenv\(dotenv_path\)\n', 'load_env()\n', content)
        content = re.sub(r'logging\.basicConfig\(\s*level=logging\.INFO,\s*format="%\(asctime\)s - %\(levelname\)s - %\(name\)s - %\(message\)s",\s*\)\n', 'from storybuilder.utils.logging_config import configure_logging\nconfigure_logging()\n', content)
    elif filepath == "src/storybuilder/utils/storage.py":
        content = re.sub(r'logging\.basicConfig\(format="%\(message\)s", level=logging\.INFO\)\n', 'from storybuilder.utils.logging_config import configure_logging\nconfigure_logging()\n', content)
        content = re.sub(r'\s*load_dotenv\(\)\s*# Load environment variables from \.env file', '\n    load_env()\n', content)
        content = re.sub(r'# Load environment variables from \.env file\n', '', content)
    else:
        content = re.sub(r'load_dotenv\(\)', 'load_env()', content)

    with open(filepath, "w") as f:
        f.write(content)

for filepath in files_to_update_env:
    update_file(filepath)
