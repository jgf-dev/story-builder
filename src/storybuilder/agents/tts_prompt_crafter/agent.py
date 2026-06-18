"""TTS Prompt Crafter — ADK Multi-Agent System.

Converts raw story files into production-ready TTS prompt files
using a three-agent pipeline:

  1. Story Analyzer  — character profiling + scene breakdown
  2. Scene Writer    — canonical TTS prompt generation
  3. Root Orchestrator — coordinates the pipeline, manages file I/O
"""

import logging
import warnings
from functools import cached_property

from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import agent_tool
from google.genai import Client, types

from .prompts import get_prompt
from .tools import list_stories, read_story, split_scene_files, write_scene_file

# Suppress noisy warnings for cleaner agent output
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)

# ---------------------------------------------------------------------------
# Safety Settings — all categories set to OFF for explicit content support
# ---------------------------------------------------------------------------
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_UNSPECIFIED,
        threshold=types.HarmBlockThreshold.OFF,
    ),
]


# ---------------------------------------------------------------------------
# Custom Gemini model with Vertex AI (global endpoint)
# ---------------------------------------------------------------------------
class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, location="global")


# ---------------------------------------------------------------------------
# Sub-Agent 1: Story Analyzer
# ---------------------------------------------------------------------------
story_analyzer = LlmAgent(
    name="story_analyzer",
    model=GlobalGemini(model="gemini-2.5-flash"),
    description=(
        "Analyzes a raw story text to identify characters, assign Gemini "
        "TTS voices, break the text into logical scenes, and map emotional "
        "arcs and intimacy levels. Returns structured analysis for the "
        "scene writer."
    ),
    instruction=get_prompt("story-analyzer"),
    generate_content_config={"safety_settings": safety_settings},
    include_contents="none",
)

# ---------------------------------------------------------------------------
# Sub-Agent 2: Scene Prompt Writer
# ---------------------------------------------------------------------------
scene_writer = LlmAgent(
    name="scene_writer",
    model=GlobalGemini(model="gemini-2.5-flash"),
    description=(
        "Converts a story analysis and raw story text into structured TTS "
        "scene prompt files following the canonical schema with SYSTEM "
        "PREAMBLE, AUDIO PROFILE, THE SCENE, DIRECTOR'S NOTES, and "
        "TRANSCRIPT sections. Outputs delimited scene file blocks."
    ),
    instruction=get_prompt("scene-writer"),
    generate_content_config={"safety_settings": safety_settings},
    include_contents="none",
)

# ---------------------------------------------------------------------------
# Root Orchestrator Agent
# ---------------------------------------------------------------------------
root_agent = LlmAgent(
    name="tts_prompt_crafter",
    model=GlobalGemini(model="gemini-2.5-flash"),
    description="Root orchestrator for the TTS prompt crafter pipeline.",
    instruction=get_prompt("tts-prompt-crafter"),
    generate_content_config={"safety_settings": safety_settings},
    sub_agents=[],
    tools=[
        # File I/O tools
        read_story,
        list_stories,
        write_scene_file,
        split_scene_files,
        # Sub-agent delegation tools
        agent_tool.AgentTool(agent=story_analyzer),
        agent_tool.AgentTool(agent=scene_writer),
    ],
)

# ---------------------------------------------------------------------------
# Session & Runner
# ---------------------------------------------------------------------------
session_service = InMemorySessionService()

APP_NAME = "tts_prompt_crafter"
USER_ID = "user_1"
SESSION_ID = "session_001"

runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

print(f"Runner created for agent '{runner.agent.name}'.")
print(f"  Sub-agent tools: story_analyzer, scene_writer")
print(f"  Function tools: read_story, list_stories, write_scene_file, split_scene_files")
