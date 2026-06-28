# pyrefly: ignore [missing-import]
import os

from dotenv import load_dotenv

from storybuilder.genai import client

load_dotenv()


if __name__ == "__main__":
    client.process_directory(os.getenv("STORIES_TEXT"))
