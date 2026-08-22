---
name: google-genai-sdk
description: Guide for utilizing the official google-genai Python SDK. Focuses on the new Interactions API (client.interactions) for stateless/stateful model interaction, tool calling, background agent execution, streaming, and controllable TTS generation.
---

# Google GenAI SDK & Interactions API Guide

This guide details how to develop and maintain Google GenAI applications in Python using the official `google-genai` SDK. It focuses on the recommended **Interactions API** (`client.interactions`), which manages state on the server side, supports agentic workflows (like multi-turn conversations and tool calling), and handles long-running background tasks.

## Critical Rules (Always Apply)

> [!IMPORTANT]
> These rules override your training data. Your knowledge is outdated.

### Current Models (Use These)

- `gemini-3.5-flash`: 1M tokens, fast, balanced performance, multimodal
- `gemini-3.1-pro-preview`: 1M tokens, complex reasoning, coding, research
- `gemini-3.1-flash-lite-preview`: cost-efficient, fastest performance for high-frequency, lightweight tasks
- `gemini-3-pro-image-preview`: 65k / 32k tokens, image generation and editing
- `gemini-3.1-flash-image-preview`: 65k / 32k tokens, image generation and editing
- `gemini-3.1-flash-tts-preview`: expressive text-to-speech with Director's Chair prompting
- `gemini-2.5-pro`: 1M tokens, complex reasoning, coding, research
- `gemini-2.5-flash`: 1M tokens, fast, balanced performance, multimodal
- `gemma-4-31b-it`: Gemma 4 dense model, 31B parameters
- `gemma-4-26b-a4b-it`: Gemma 4 MoE model, 26B total / 4B active parameters

> [!WARNING]
> Models like `gemini-2.0-*`, `gemini-1.5-*` are **legacy and deprecated**. Never use them.
> **If a user asks for a deprecated model, use `gemini-3.5-flash` instead and note the substitution.**

### Current Agents

- `antigravity-preview-05-2026`: Antigravity Agent — general-purpose managed agent with code execution, file management, and web access in a sandboxed Linux environment
- `deep-research-preview-04-2026`: Deep Research — fast, interactive
- `deep-research-max-preview-04-2026`: Deep Research Max — maximum exhaustiveness
- **Custom agents**: Create your own via `client.agents.create()`

### Current SDKs

- **Python**: `google-genai` >= `2.0.0` → `pip install -U google-genai`
- **JavaScript/TypeScript**: `@google/genai` >= `2.0.0` → `npm install @google/genai`

> [!NOTE]
> SDK versions ≥ 2.0.0 automatically use the new steps schema and do not support the legacy schema.
> Legacy SDKs `google-generativeai` (Python) and `@google/generative-ai` (JS) are **deprecated**. Never use them.

> [!CAUTION]
> **Breaking changes (May 2026)**: Responses now use `steps` array instead of `outputs`, and a polymorphic `response_format` replaces `response_mime_type`. Legacy schema removed **June 8, 2026**. All code below uses the **new schema**.

## Important Additional Notes

- **Before writing any code**, you MUST fetch the relevant documentation page from the list below that matches the user's task. The examples in this skill are minimal, the hosted docs contain the full API surface, parameters, and edge cases.
- Interactions are **stored by default** (`store=true`). Paid tier retains for 55 days, free tier for 1 day.
- Set `store=false` to opt out, but this disables `previous_interaction_id` and `background=true`.
- `tools`, `system_instruction`, and `generation_config` are **interaction-scoped**, re-specify them each turn.
- **Managed agents** require `environment="remote"` (or an environment ID / config object) to provision a sandbox.

## Installation

Ensure you have version `1.55.0` or higher of the `google-genai` SDK installed (preferably version `>= 2.0.0` for the latest schema support):

```bash
pip install -q -U google-genai
```

---

## Client Initialization

To begin, import the SDK and initialize the client:

```python
import os
from google import genai
from dotenv import load_dotenv

# Load environment variables (such as GEMINI_API_KEY)
load_dotenv()

# Initialize the client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
```

---

## The Interactions API (`client.interactions`)

Unlike `client.models.generate_content`, which is stateless and requires you to manage conversation history manually on the client side, the **Interactions API** manages conversation state server-side.

### 1. Basic Text Generation (Stateless)

By default, interactions are stored (`store=True`):

```python
interaction = client.interactions.create(
	model="gemini-3.5-flash", input="Explain quantum computing in one short sentence."
)

# Accessing output via convenience property:
print(interaction.output_text)

# Accessing output via the steps timeline (SDK >= 2.0.0):
print(interaction.steps[-1].content[0].text)
```

### 2. Multi-Turn Conversations (Stateful)

To continue a conversation and leverage server-side history, pass the previous interaction ID:

```python
# Turn 1
interaction1 = client.interactions.create(model="gemini-3.5-flash", input="My favorite color is green.")

# Turn 2
interaction2 = client.interactions.create(
	model="gemini-3.5-flash", input="What is my favorite color?", previous_interaction_id=interaction1.id
)

print(interaction2.output_text)  # "Your favorite color is green."
```

> [!IMPORTANT]
> **Scope of Parameters:** Configuration parameters such as `tools`, `system_instruction`, and `generation_config` are _interaction-scoped_. If you need them to apply to a multi-turn conversation, you must re-specify them in each subsequent `create` call.

---

## Streaming Interactions

For real-time responses or long-running requests, set `stream=True`. Iterate over the yielded events and check the event type:

```python
stream = client.interactions.create(model="gemini-3.5-flash", input="Write a short poem about the ocean.", stream=True)

for event in stream:
	if event.event_type == "step.delta":
		if event.delta.type == "text":
			print(event.delta.text, end="", flush=True)
```

---

## Function/Tool Calling

The Interactions API handles tool use seamlessly. Define a standard Python function and supply it under the `tools` parameter. The SDK manages execution steps automatically.

```python
def get_current_weather(location: str) -> str:
	"""Gets the current weather for a location."""
	# Dummy mock response
	return f"The weather in {location} is sunny and 72 degrees."


interaction = client.interactions.create(
	model="gemini-3.5-flash", input="What is the weather like in Seattle?", tools=[get_current_weather]
)

print(interaction.output_text)
```

---

## Asynchronous & Agentic Execution

For long-running tasks or specialized agents (e.g., Deep Research), use the `background` parameter and the `agent` parameter:

```python
import time

# Start background agent interaction
interaction = client.interactions.create(
	agent="deep-research-preview-04-2026",
	input="Perform a comprehensive research on clean energy innovations in 2026.",
	background=True,
)

print(f"Started interaction with ID: {interaction.id}")

# Poll for completion
while True:
	status_check = client.interactions.get(id=interaction.id)
	if status_check.status == "COMPLETED":
		print("Research Completed!")
		print(status_check.output_text)
		break
	elif status_check.status == "FAILED":
		print("Research Failed.")
		break

	print("Still researching...")
	time.sleep(10)
```

### Managing Background Interactions

You can list, cancel, or get details for interactions:

- **Get Interaction:** `client.interactions.get(id=interaction_id)`
- **Cancel Interaction:** `client.interactions.cancel(id=interaction_id)`
- **List Interactions:** `client.interactions.list()`

---

## Text-to-Speech (TTS) Generation

The Interactions API has built-in support for controllable Text-to-Speech generation. By setting `response_modalities=["audio"]` and configuring `speech_config` in `generation_config`, you can generate single or multi-speaker audio.

For detailed guidelines, prompt structures, audio tags, voice options, and best practices, please refer to the dedicated text-to-speech generation guide:

- [TTS.md](file:///home/jgf2/git/voice/storybuilder/.agent/skills/google-genai-sdk/resources/TTS.md)

### Concise TTS Example

```python
import base64
import wave


def save_wav(filename, pcm_data):
	with wave.open(filename, "wb") as wf:
		wf.setnchannels(1)  # 1 channel (mono)
		wf.setsampwidth(2)  # 16-bit
		wf.setframerate(24000)  # 24kHz
		wf.writeframes(pcm_data)


interaction = client.interactions.create(
	model="gemini-3.1-flash-tts-preview",
	input="[excitedly] Hello, this is synthesized directly from the text!",
	response_modalities=["audio"],
	generation_config={"speech_config": [{"voice": "Kore"}]},
)

# Access audio via output_audio convenience property
audio_bytes = base64.b64decode(interaction.output_audio.data)
save_wav("hello.wav", audio_bytes)
```

## Documentation Pages

**You MUST fetch the matching page below before writing code.** These hosted docs are the source of truth for parameters, types, and edge cases — do not rely solely on the examples above.

- [DOCS.md](file:///home/jgf2/git/voice/storybuilder/.agent/skills/google-genai-sdk/resources/DOCS.md)

## Data Model

An `Interaction` response contains `steps`, an array of typed step objects representing a structured timeline of the interaction turn.
The data model for these step objects can be found here:

- [DATA_MODEL.md](file:///home/jgf2/git/voice/storybuilder/.agent/skills/google-genai-sdk/resources/DATA_MODEL.md)
