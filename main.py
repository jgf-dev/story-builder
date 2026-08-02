# pyrefly: ignore [missing-import]
import os

import braintrust


braintrust.auto_instrument()

from storybuilder.utils.env import load_env

from storybuilder.genai import client


load_env()


if __name__ == "__main__":
    braintrust.init_logger(project="storybuilder")
    client.process_directory(os.getenv("STORIES_TEXT"))
