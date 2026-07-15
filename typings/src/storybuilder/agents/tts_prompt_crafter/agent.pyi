import logging
import os
import pathlib
import warnings
from enum import Enum, StrEnum
from functools import cached_property
from storybuilder.utils.env import load_env
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
from storybuilder.utils.env import load_env
from storybuilder.utils.logging_config import configure_logging, get_logger
from .prompts import get_prompt
from .tools import list_stories
from .tools import read_story
from .tools import split_scene_files
from .tools import write_scene_file

logger: Logger
safety_settings: list[SafetySetting]


class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client: ...


class CharacterName(BaseModel):
    name: str


class CharacterSchema(BaseModel):
    name: CharacterName
    role: str
    voice: str
    voice_archetype: str
    recommended_voice: str
    vocal_qualities: str
    personality_in_brief: str
    emotional_range: str


class StorySchema(BaseModel):
    title: str
    story: str


class IntimacyLevel(StrEnum):
    NONE: Literal['none'] = "none"
    MILD: Literal['mild'] = "mild"
    MODERATE: Literal['moderate'] = "moderate"
    HIGH: Literal['high'] = "high"

    def has_explicit_content(self) -> bool: ...


class PacingNotes(StrEnum):
    SLOW: Literal['slow'] = "slow"
    MEASURED: Literal['measured'] = "measured"
    CONVERSATIONAL: Literal['conversational'] = "conversational"
    FAST: Literal['fast'] = "fast"
    URGENT: Literal['urgent'] = "urgent"


class SceneSchema(BaseModel):
    scene_number: NonNegativeInt
    scene_title: str
    location: str
    characters_present: list[CharacterName]
    emotional_tone: str
    intimacy_level: IntimacyLevel
    key_events: list[str]
    pacing_notes: PacingNotes
    start_marker: str
    end_marker: str


class VoiceInteractionNotesSchema(BaseModel):
    dialogue_heavy_scenes: list[str]
    narrator_heavy_scenes: list[str]
    emotional_transitions: list[str]


class SceneAnalysisSchema(BaseModel):
    scenes: list[SceneSchema]
    voice_interaction_notes: VoiceInteractionNotesSchema


class Genre(str, Enum):
    M4M_ROMANCE: Literal['M4M Romance'] = "M4M Romance"
    M4M_EROTICA: Literal['M4M Erotica'] = "M4M Erotica"
    M4M_EROTIC_ROMANCE: Literal['M4M Erotic Romance'] = "M4M Erotic Romance"
    YA_COMING_OF_AGE: Literal['YA Coming-of-Age'] = "YA Coming-of-Age"
    ADULT_FRIENDS: Literal['Adult Friends'] = "Adult Friends"
    ADULT_YOUTH: Literal['Adult Youth'] = "Adult Youth"
    ATHLETICS: Literal['Athletics'] = "Athletics"
    AUTHORITARIAN: Literal['Authoritarian'] = "Authoritarian"
    BEGINNINGS: Literal['Beginnings'] = "Beginnings"
    CAMPING: Literal['Camping'] = "Camping"
    CELEBRITY: Literal['Celebrity'] = "Celebrity"
    COLLEGE: Literal['College'] = "College"
    ENCOUNTERS: Literal['Encounters'] = "Encounters"
    FIRST_TIME: Literal['First Time'] = "First Time"
    HIGH_SCHOOL: Literal['High School'] = "High School"
    HISTORICAL: Literal['Historical'] = "Historical"
    INCEST: Literal['Incest'] = "Incest"
    INTERRACIAL: Literal['Interracial'] = "Interracial"
    MASTURBATION: Literal['Masturbation'] = "Masturbation"
    MILITARY: Literal['Military'] = "Military"
    NO_SEX: Literal['No Sex'] = "No Sex"
    NON_ENGLISH: Literal['Non-English'] = "Non-English"
    RELATIONSHIPS: Literal['Relationships'] = "Relationships"
    RURAL: Literal['Rural'] = "Rural"
    SCIENCE_FICTION_OR_FANTASY: Literal['Science Fiction or Fantasy'] = "Science Fiction or Fantasy"
    URINATION: Literal['Urination'] = "Urination"
    YOUNG_FRIENDS: Literal['Young Friends'] = "Young Friends"
    POLYAMORY: Literal['Polyamory'] = "Polyamory"
    POLYANDRY: Literal['Polyandry'] = "Polyandry"
    BISEXUAL: Literal['Bisexual'] = "Bisexual"
    GAY: Literal['Gay'] = "Gay"
    OTHER: Literal['Other'] = "Other"


class StoryAnalysisSchema(BaseModel):
    title: str
    genre_tone: list[Genre]
    setting: str
    narrative_voice: str
    emotional_arc: str
    characters: list[CharacterSchema]
    scene_analysis: SceneAnalysisSchema


story_analyzer: LlmAgent


class ScenePromptWriterInputSchema(BaseModel):
    story_analysis: StoryAnalysisSchema
    raw_story: str


class PromptFileSchema(BaseModel):
    file_name: str
    content: str


class PromptFilesOutputSchema(BaseModel):
    prompt_files: list[PromptFileSchema]


scene_writer: LlmAgent
root_agent: LlmAgent
memory_service: VertexAiMemoryBankService
db_url: Literal['sqlite+aiosqlite:///./stories/db/tts_prompt_crafter.db'] = "sqlite+aiosqlite:///./stories/db/tts_prompt_crafter.db"
session_service: DatabaseSessionService
artifact_service: InMemoryArtifactService
APP_NAME: Literal['tts_prompt_crafter'] = "tts_prompt_crafter"
USER_ID: Literal['user_1'] = "user_1"
SESSION_ID: Literal['session_001'] = "session_001"
runner: Runner
