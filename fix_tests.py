import re
import os

files_to_update = [
    "tests/agents/test_agent_smoke.py",
    "tests/agents/test_subagent.py",
    "tests/genai/test_tts_pipeline.py",
    "tests/misc/test_keys.py",
    "tests/misc/test_storage.py"
]

for filepath in files_to_update:
    with open(filepath, "r") as f:
        content = f.read()

    if filepath == "tests/misc/test_storage.py":
        content = content.replace('patch("storybuilder.utils.storage.load_dotenv")', 'patch("storybuilder.utils.env.load_env")')
    else:
        content = re.sub(r'from dotenv import load_dotenv', 'from storybuilder.utils.env import load_env', content)
        content = re.sub(r'load_dotenv\(project_root / "\.env"\)', 'load_env(project_root / ".env")', content)

    with open(filepath, "w") as f:
        f.write(content)
