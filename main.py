# pyrefly: ignore [missing-import]
import os
from pathlib import Path

import braintrust

from storybuilder.utils.env import load_env


braintrust.auto_instrument()

# Load the project's .env file regardless of the working directory so imports
# that touch environment variables below see the expected configuration.
load_env(Path(__file__).with_name(".env"))

if __name__ == "__main__":
    from storybuilder.genai import client

    braintrust.init_logger(project="storybuilder")
    client.process_directory(os.getenv("STORIES_TEXT"))
