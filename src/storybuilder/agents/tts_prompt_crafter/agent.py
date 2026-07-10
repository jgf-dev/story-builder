"""TTS Prompt Crafter — ADK Multi-Agent System.

Converts raw story files into production-ready TTS prompt files
using a three-agent pipeline:

  1. Story Analyzer  — character profiling + scene breakdown
  2. Scene Writer    — canonical TTS prompt generation
  3. Root Orchestrator — coordinates the pipeline, manages file I/O
"""

import logging
import os
import warnings
from enum import Enum
from functools import cached_property

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import Client
from google.genai import types
from opentelemetry import _logs
from opentelemetry import metrics
from opentelemetry import trace
from opentelemetry._logs._internal import ProxyLoggerProvider
from pydantic import BaseModel
from pydantic import Field
from pydantic.types import NonNegativeInt

from .prompts import get_prompt
from .tools import list_stories
from .tools import read_story
from .tools import split_scene_files
from .tools import write_scene_file




dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))
load_dotenv(dotenv_path)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

os.environ["OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"] = "http://localhost:4318/v1/logs"
os.environ["OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"] = "http://localhost:4318/v1/metrics"
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
os.environ["OTEL_SERVICE_NAME"] = "story-builder"


def _otel_providers_are_default() -> bool:
    """Avoid re-registering providers when another integration already did."""

    return (
        isinstance(trace.get_tracer_provider(), trace.ProxyTracerProvider)
        and isinstance(metrics.get_meter_provider(), metrics._internal._ProxyMeterProvider)
        and isinstance(_logs.get_logger_provider(), ProxyLoggerProvider)
    )


if _otel_providers_are_default():
    maybe_set_otel_providers()

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
# Custom Gemini model using Vertex AI
# ---------------------------------------------------------------------------
class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client:
        return Client(vertexai=True, project="storage-499607", location="global")


# ---------------------------------------------------------------------------
# Sub-Agent 1: Story Analyzer
# ---------------------------------------------------------------------------


class CharacterName(BaseModel):
    name: str


class CharacterSchema(BaseModel):
    """Schema for a character in the story."""

    name: CharacterName
    role: str = Field(default="", description="The role of the character.")
    voice: str = Field(default="", description="The voice to use for the character.")
    voice_archetype: str = Field(default="", description="The voice archetype of the character.")
    recommended_voice: str = Field(default="", description="The recommended voice for the character.")
    vocal_qualities: str = Field(default="", description="The vocal qualities of the character.")
    personality_in_brief: str = Field(default="", description="The personality of the character in brief.")
    emotional_range: str = Field(default="", description="The emotional range of the character.")


class StorySchema(BaseModel):
    """Schema for story analysis."""

    title: str = Field(default="", description="The title of the story.")
    story: str = Field(default="", description="The story text.")


class IntimacyLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"

    def has_explicit_content(self) -> bool:
        return self in (self.MODERATE, self.HIGH)


class PacingNotes(str, Enum):
    SLOW = "slow"
    MEASURED = "measured"
    CONVERSATIONAL = "conversational"
    FAST = "fast"
    URGENT = "urgent"


class SceneSchema(BaseModel):
    """Schema for a scene in the story."""

    scene_number: NonNegativeInt = Field(default=0, description="The scene number.")
    scene_title: str = Field(description="The title of the scene.")
    location: str = Field(description="The location of the scene.")
    characters_present: list[CharacterName] = Field(min_items=1, description="The characters present in the scene.")
    emotional_tone: str = Field(description="The emotional tone of the scene.")
    intimacy_level: IntimacyLevel = Field(default=IntimacyLevel.NONE, description="The intimacy level of the scene.")
    key_events: list[str] = Field(min_items=1, description="The key events of the scene.")
    pacing_notes: PacingNotes = Field(
        default=PacingNotes.CONVERSATIONAL,
        description="The pacing notes for the scene.",
    )
    start_marker: str = Field(description="The start marker for the scene.")
    end_marker: str = Field(description="The end marker for the scene.")


class VoiceInteractionNotesSchema(BaseModel):
    """Schema for voice interaction notes."""

    dialogue_heavy_scenes: list[str] = Field(default=[], description="The dialogue-heavy scenes.")
    narrator_heavy_scenes: list[str] = Field(default=[], description="The narrator-heavy scenes.")
    emotional_transitions: list[str] = Field(default=[], description="The emotional transitions.")


class SceneAnalysisSchema(BaseModel):
    """Schema for scene analysis output."""

    scenes: list[SceneSchema] = Field(min_items=1, description="The scenes in the story.")
    voice_interaction_notes: VoiceInteractionNotesSchema = Field(description="The voice interaction notes.")


class Genre(str, Enum):
    M4M_ROMANCE = "M4M Romance"
    M4M_EROTICA = "M4M Erotica"
    M4M_EROTIC_ROMANCE = "M4M Erotic Romance"
    YA_COMING_OF_AGE = "YA Coming-of-Age"
    ADULT_FRIENDS = "Adult Friends"
    ADULT_YOUTH = "Adult Youth"
    ATHLETICS = "Athletics"
    AUTHORITARIAN = "Authoritarian"
    BEGINNINGS = "Beginnings"
    CAMPING = "Camping"
    CELEBRITY = "Celebrity"
    COLLEGE = "College"
    ENCOUNTERS = "Encounters"
    FIRST_TIME = "First Time"
    HIGH_SCHOOL = "High School"
    HISTORICAL = "Historical"
    INCEST = "Incest"
    INTERRACIAL = "Interracial"
    MASTURBATION = "Masturbation"
    MILITARY = "Military"
    NO_SEX = "No Sex"
    NON_ENGLISH = "Non-English"
    RELATIONSHIPS = "Relationships"
    RURAL = "Rural"
    SCIENCE_FICTION_OR_FANTASY = "Science Fiction or Fantasy"
    URINATION = "Urination"
    YOUNG_FRIENDS = "Young Friends"
    POLYAMORY = "Polyamory"
    POLYANDRY = "Polyandry"
    BISEXUAL = "Bisexual"
    GAY = "Gay"
    OTHER = "Other"


class StoryAnalysisSchema(BaseModel):
    """Schema for story analysis output."""

    title: str = Field(description="The title of the story.")
    genre_tone: list[Genre] = Field(
        min_items=1,
        description="The genres and tones of the story. Use as many as appropriate.",
    )
    setting: str = Field(description="The setting of the story.")
    narrative_voice: str = Field(description="The narrative voice of the story.")
    emotional_arc: str = Field(description="The emotional arc of the story.")
    characters: list[CharacterSchema] = Field(min_items=1, description="The characters in the story.")
    scene_analysis: SceneAnalysisSchema = Field(description="The scene analysis.")


story_analyzer = LlmAgent(
    name="story_analyzer",
    model=GlobalGemini(model="gemini-3.5-flash"),
    description=(
        "Analyzes a raw story text to identify characters, assign Gemini "
        "TTS voices, break the text into logical scenes, and map emotional "
        "arcs and intimacy levels. Returns structured analysis for the "
        "scene writer."
    ),
    instruction=get_prompt("story-analyzer"),
    generate_content_config=types.GenerateContentConfig(safety_settings=safety_settings),
    mode="single_turn",
    output_key="story-analysis",
    input_schema=StorySchema,
    output_schema=StoryAnalysisSchema,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)


class ScenePromptWriterInputSchema(BaseModel):
    """Schema for scene prompt writer input."""

    story_analysis: StoryAnalysisSchema = Field(description="The story analysis.")
    raw_story: str = Field(description="The raw story text.")


class PromptFileSchema(BaseModel):
    """Schema for a prompt file."""

    file_name: str = Field(description="The name of the file.")
    content: str = Field(description="The content of the file.")


class PromptFilesOutputSchema(BaseModel):
    """Schema for scene prompt files output."""

    prompt_files: list[PromptFileSchema] = Field(min_items=1, description="The prompt files.")


# ---------------------------------------------------------------------------
# Sub-Agent 2: Scene Prompt Writer
# ---------------------------------------------------------------------------
scene_writer = LlmAgent(
    name="scene_writer",
    model=GlobalGemini(model="gemini-3.5-flash"),
    description=(
        "Converts a story analysis and raw story text into structured TTS "
        "scene prompt files following the canonical schema with SYSTEM "
        "PREAMBLE, AUDIO PROFILE, THE SCENE, DIRECTOR'S NOTES, and "
        "TRANSCRIPT sections. Outputs delimited scene file blocks."
    ),
    instruction=get_prompt("scene-writer"),
    generate_content_config=types.GenerateContentConfig(safety_settings=safety_settings),
    mode="single_turn",
    output_key="scene-prompts",
    input_schema=ScenePromptWriterInputSchema,
    output_schema=PromptFilesOutputSchema,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

# ---------------------------------------------------------------------------
# Root Orchestrator Agent
# ---------------------------------------------------------------------------
root_agent = LlmAgent(
    name="tts_prompt_crafter",
    model=GlobalGemini(model="gemini-3.5-flash"),
    description="Root orchestrator for the TTS prompt crafter pipeline.",
    instruction=get_prompt("tts-prompt-crafter"),
    generate_content_config=types.GenerateContentConfig(safety_settings=safety_settings),
    sub_agents=[story_analyzer, scene_writer],
    tools=[read_story, list_stories, write_scene_file, split_scene_files],
)

# ---------------------------------------------------------------------------
# Session & Runner
# ---------------------------------------------------------------------------


memory_service = VertexAiMemoryBankService(
    project="storage-499607",
    location="global",
    agent_engine_id="8434441657599918080",
)

db_url = "sqlite+aiosqlite:///./stories/db/tts_prompt_crafter.db"
session_service = DatabaseSessionService(db_url=db_url)

artifact_service = InMemoryArtifactService()

APP_NAME = "tts_prompt_crafter"
USER_ID = "user_1"
SESSION_ID = "session_001"
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
    memory_service=memory_service,
    artifact_service=artifact_service,
)

logging.getLogger(__name__).info(f"Runner created for agent '{runner.agent.name}'.")


logging.getLogger(__name__).info(
    f"  Sub-agents: {story_analyzer.name}, {scene_writer.name}",
)
logging.getLogger(__name__).info(
    f"  Function tools: {read_story.__name__}, {list_stories.__name__}, {write_scene_file.__name__}, {split_scene_files.__name__}",
)
