# pyrefly: ignore [missing-import]
import os
from pathlib import Path

from storybuilder.utils.env import load_env

# Load the project's .env file before any third-party instrumentation reads
# environment variables such as Braintrust API keys or project config.
load_env(Path(__file__).with_name(".env"))

import braintrust  # noqa: E402

braintrust.auto_instrument()

if __name__ == "__main__":
	from storybuilder.genai import client

	braintrust.init_logger(project="storybuilder")
	stories_text_dir = os.getenv("STORIES_TEXT", "stories/text")
	client.process_directory(stories_text_dir)
