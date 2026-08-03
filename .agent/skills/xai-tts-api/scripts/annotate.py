import pathlib

from xai_sdk.chat import system, user

from storybuilder.utils import get_prompt, get_story
from storybuilder.xaiapi.client import create_chat_session


annotate_prompt = get_prompt("annotate")


def annotate_story(story: str) -> str:
	"""Annotates a story with speech tags."""
	story = get_story(story)
	chat_session = create_chat_session("grok-4.3")
	chat_session.append(system(annotate_prompt))
	chat_session.append(user(story))

	response = chat_session.sample()

	return response.content


if __name__ == "__main__":
	ann = annotate_story("cumshort")
	pathlib.Path("../../stories/cumshort.annotated.md").write_text(ann)
