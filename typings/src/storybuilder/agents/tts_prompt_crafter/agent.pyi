from _typeshed import Incomplete

import logging
import os
import warnings
from enum import Enum, StrEnum
from functools import cached_property
from google.adk.agents import Agent
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import Client, types
from opentelemetry import _logs, metrics, trace
from opentelemetry._logs._internal import ProxyLoggerProvider
from pydantic import BaseModel, Field
from pydantic.types import NonNegativeInt
from storybuilder.utils.env import load_env
from storybuilder.utils.logging_config import configure_logging, get_logger
from .prompts import get_prompt
from .tools import list_stories, read_story, split_scene_files, write_scene_file

logger: Logger
safety_settings: list[SafetySetting]


class GlobalGemini(Gemini):
    @cached_property
    def api_client(self) -> Client: ...

    def __init__(self, *, model: bytearray | bytes | str = ..., client_kwargs: Mapping[str, Any] | None = ..., base_url: bytearray | bytes | str | None = ..., speech_config: Any | None = ..., use_interactions_api: Decimal | bool | float | int | str = ..., retry_options: Any | None = ..., **kwargs: Incomplete) -> None: ...


class CharacterName(BaseModel):
    name: str

    def __init__(self, *, name: bytearray | bytes | str, **kwargs: Incomplete) -> None: ...


class CharacterSchema(BaseModel):
    name: CharacterName
    role: str
    voice: str
    voice_archetype: str
    recommended_voice: str
    vocal_qualities: str
    personality_in_brief: str
    emotional_range: str

    def __init__(self, *, name: Incomplete, role: bytearray | bytes | str = ..., voice: bytearray | bytes | str = ..., voice_archetype: bytearray | bytes | str = ..., recommended_voice: bytearray | bytes | str = ..., vocal_qualities: bytearray | bytes | str = ..., personality_in_brief: bytearray | bytes | str = ..., emotional_range: bytearray | bytes | str = ..., **kwargs: Incomplete) -> None: ...


class StorySchema(BaseModel):
    title: str
    story: str

    def __init__(self, *, title: bytearray | bytes | str = ..., story: bytearray | bytes | str = ..., **kwargs: Incomplete) -> None: ...


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

    def __init__(self, *, scene_number: Decimal | bool | bytes | float | int | str = ..., scene_title: bytearray | bytes | str, location: bytearray | bytes | str, characters_present: Iterable[Any], emotional_tone: bytearray | bytes | str, intimacy_level: Incomplete = ..., key_events: Iterable[LaxStr], pacing_notes: Incomplete = ..., start_marker: bytearray | bytes | str, end_marker: bytearray | bytes | str, **kwargs: Incomplete) -> None: ...


class VoiceInteractionNotesSchema(BaseModel):
    dialogue_heavy_scenes: list[str]
    narrator_heavy_scenes: list[str]
    emotional_transitions: list[str]

    def __init__(self, *, dialogue_heavy_scenes: Iterable[LaxStr] = ..., narrator_heavy_scenes: Iterable[LaxStr] = ..., emotional_transitions: Iterable[LaxStr] = ..., **kwargs: Incomplete) -> None: ...


class SceneAnalysisSchema(BaseModel):
    scenes: list[SceneSchema]
    voice_interaction_notes: VoiceInteractionNotesSchema

    def __init__(self, *, scenes: Iterable[Any], voice_interaction_notes: Incomplete, **kwargs: Incomplete) -> None: ...


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

    def __init__(self, *, title: bytearray | bytes | str, genre_tone: Iterable[Any], setting: bytearray | bytes | str, narrative_voice: bytearray | bytes | str, emotional_arc: bytearray | bytes | str, characters: Iterable[Any], scene_analysis: Incomplete, **kwargs: Incomplete) -> None: ...


story_analyzer: LlmAgent


class ScenePromptWriterInputSchema(BaseModel):
    story_analysis: StoryAnalysisSchema
    raw_story: str

    def __init__(self, *, story_analysis: Incomplete, raw_story: bytearray | bytes | str, **kwargs: Incomplete) -> None: ...


class PromptFileSchema(BaseModel):
    file_name: str
    content: str

    def __init__(self, *, file_name: bytearray | bytes | str, content: bytearray | bytes | str, **kwargs: Incomplete) -> None: ...


class PromptFilesOutputSchema(BaseModel):
    prompt_files: list[PromptFileSchema]

    def __init__(self, *, prompt_files: Iterable[Any], **kwargs: Incomplete) -> None: ...


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
