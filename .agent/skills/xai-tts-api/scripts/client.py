import os

from dotenv import load_dotenv
from xai_sdk import Client
from xai_sdk.sync.chat import Chat

load_dotenv()

client:Client = Client(
    api_key=os.getenv("XAI_API_KEY"),
    management_api_key=os.getenv("XAI_MANAGEMENT_API_KEY"),
    timeout=3600,
)


def create_chat_session(model: str) -> Chat:
    """Creates a chat session."""
    return client.chat.create(model=model)


if __name__ == "__main__":
    print(create_chat_session("grok-4.3").id)
