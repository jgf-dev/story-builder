# pyrefly: ignore [missing-import]
import os

import braintrust

braintrust.auto_instrument()

from dotenv import load_dotenv

from storybuilder.genai import client

load_dotenv()


if __name__ == "__main__":
	braintrust.init_logger(project="storybuilder")
	client.process_directory(os.getenv("STORIES_TEXT"))
