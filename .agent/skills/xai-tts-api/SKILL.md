---
name: xai-tts-api
description: Use this skill whenever the user asks about xAI Text-to-Speech, Grok voice or audio generation, listing xAI TTS voices, creating custom voices, generating MP3/WAV/PCM audio, adding speech tags for xAI TTS, or turning repository stories into narrated audio. This skill is especially relevant for StoryBuilder workflows that mention xAI, XAI_API_KEY, Grok, TTS, voice_id, /v1/tts, story annotation, or expressive speech tags, even if the user does not explicitly say "use the xAI TTS skill."
---

# xAI TTS API Skill

Use this skill to help a developer integrate xAI Text-to-Speech into StoryBuilder or a nearby Python project. Keep two jobs in view:

- API integration: call the current xAI TTS REST endpoints safely and correctly.
- Story workflow: prepare narrative text with expressive tags, chunk it when needed, and generate audio files without changing the story's words unless the user asks for annotation.

## Current Documentation Rule

Before giving endpoint, field, model, voice, or SDK details, fetch current documentation. In this repo, follow the project rule:

```bash
npx ctx7@latest library xAI "<the user's full question>"
npx ctx7@latest docs <selected-library-id> "<the user's full question>"
```

Prefer `/websites/x_ai_developers` for REST TTS endpoint details and `/xai-org/xai-sdk-python` for Python SDK client/chat details. If Context7 fails with quota, DNS, or network errors, report that clearly instead of guessing.

## Required API Facts

These facts were confirmed from Context7 on 2026-06-13, but still re-check docs before implementing user-facing code:

- Base URL: `https://api.x.ai`
- Generate TTS audio: `POST https://api.x.ai/v1/tts`
- List TTS voices: `GET https://api.x.ai/v1/tts/voices`
- Create custom voice: `POST https://api.x.ai/v1/custom-voices`
- Authentication: `Authorization: Bearer <XAI_API_KEY>`
- Default built-in voice shown in docs: `voice_id: "eve"`
- Required request shape for basic TTS includes `text`, `voice_id`, and `language`.
- Text limit: 15,000 characters per TTS request.
- Documented output formats include MP3, WAV, PCM, MULAW, and ALAW.
- xAI TTS supports inline speech tags and wrapping delivery tags for expressive output.

## Safety and Cost Guardrails

- Read `XAI_API_KEY` from the environment. Do not hardcode it, print it, check it into files, or include it in eval prompts.
- Do not run live TTS calls unless the user explicitly opts in. Treat live calls as paid/account-affecting.
- Keep smoke-test text under 100 characters.
- Do not send long story text, private drafts, or erotic content to live API tests unless the user explicitly asks.
- Do not create custom voices in automated tests. Creating custom voices requires user-provided reference audio and may have account/storage implications.
- When writing examples, call `response.raise_for_status()` and save binary audio with `open(..., "wb")`.

## Choosing REST vs SDK

Prefer REST with `requests` for TTS because the current xAI docs expose TTS examples through HTTP endpoints. Use `xai-sdk` for chat-based story annotation workflows when that is the user's goal.

The existing helper scripts are:

- `.agent/skills/xai-tts-api/scripts/client.py`: initializes `xai_sdk.Client` with `XAI_API_KEY`, optional `XAI_MANAGEMENT_API_KEY`, and a long timeout.
- `.agent/skills/xai-tts-api/scripts/annotate.py`: uses chat to annotate a story with speech tags.
- `.agent/skills/xai-tts-api/resources/annotate.md`: the annotation prompt and tag reference.

Before running the helper scripts, verify imports in the current checkout. At the time this skill was written, `annotate.py` imports `storybuilder.xaiapi.client`, but the client file lives under this skill's `scripts/` directory. Fix or work around that import path before executing it.

## Basic Examples

### List Voices

```python
import json
import os

import requests

response = requests.get(
	"https://api.x.ai/v1/tts/voices",
	headers={"Authorization": f"Bearer {os.environ['XAI_API_KEY']}"},
	timeout=60,
)
response.raise_for_status()
print(json.dumps(response.json(), indent=2))
```

### Generate a Short MP3

```python
import os

import requests

response = requests.post(
	"https://api.x.ai/v1/tts",
	headers={
		"Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
		"Content-Type": "application/json",
	},
	json={
		"text": "Hello! Welcome to the xAI Text to Speech API.",
		"voice_id": "eve",
		"language": "en",
	},
	timeout=120,
)
response.raise_for_status()

with open("hello.mp3", "wb") as f:
	f.write(response.content)
```

### Create a Custom Voice, Then Use It

```python
import os

import requests

with open("reference.wav", "rb") as f:
	create = requests.post(
		"https://api.x.ai/v1/custom-voices",
		headers={"Authorization": f"Bearer {os.environ['XAI_API_KEY']}"},
		files={"file": ("reference.wav", f, "audio/wav")},
		data={"name": "Friendly Narrator", "language": "en"},
		timeout=300,
	)
create.raise_for_status()
voice_id = create.json()["voice_id"]

speech = requests.post(
	"https://api.x.ai/v1/tts",
	headers={
		"Authorization": f"Bearer {os.environ['XAI_API_KEY']}",
		"Content-Type": "application/json",
	},
	json={
		"text": "Hello! This is my custom voice.",
		"voice_id": voice_id,
		"language": "en",
	},
	timeout=120,
)
speech.raise_for_status()

with open("custom.mp3", "wb") as f:
	f.write(speech.content)
```

For WAV, PCM, MULAW, ALAW, sample rate, or bitrate options, re-check the current xAI REST docs and use the exact documented field names. Do not invent an `output_format` parameter if the docs have changed.

## StoryBuilder Workflow

Use this workflow when the user wants story audio or asks to annotate a story for xAI TTS:

1. Confirm the source text path or story slug.
2. If annotation is requested, read `.agent/skills/xai-tts-api/resources/annotate.md` and preserve the original words. Insert only supported tags.
3. Validate tag shape:
   - Inline tags use `[tag]`.
   - Wrapping tags use `<tag>text</tag>`.
   - Wrapping tags must close in reverse order.
   - Avoid overlapping or broken tags.
4. Chunk final text before live API calls:
   - Hard limit: less than 15,000 characters per request.
   - Prefer smaller chunks at paragraph boundaries for reviewability and stable retries.
5. Generate numbered audio files such as `001.mp3`, `002.mp3`, and keep a manifest with source chunk, voice ID, language, format, and output path.
6. Skip existing audio files unless the user asks to overwrite.

## Optional Live API Smoke Tests

Only run these after the user explicitly opts in and `XAI_API_KEY` is present:

1. Voices: call `GET /v1/tts/voices` and verify the response parses as JSON.
2. MP3: generate `"Hello from the xAI TTS smoke test."`, save it under a temp or test output directory, and verify the file has nonzero bytes.
3. WAV: only after re-checking the current docs for the exact format field, generate a short WAV and verify nonzero bytes plus the expected extension.

Do not include live tests in default CI. They are integration checks, not unit tests.

## Output Style

When answering users:

- Explain whether you are giving a dry-run plan, code sample, or live-call workflow.
- Include the minimum complete code needed for the requested path.
- Name any assumptions about voice, language, output format, or chunking.
- If you cannot verify current docs, say so and ask the user to run the Context7 login/API-key step rather than relying on stale API knowledge.
