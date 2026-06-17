# XAI TTS API Skill

## Summary

Create `.agent/skills/xai-tts-api/SKILL.md` as a repo-aware skill for using xAI Text-to-Speech. The skill will combine current xAI API facts from Context7 with this repo’s existing story annotation resources and helper scripts.
Default validation will avoid paid API calls. Optional live API tests will be included for users who explicitly opt in and have XAI_API_KEY configured.

## Key Changes

Add YAML frontmatter:name: xai-tts-api
Strong trigger description for xAI TTS, Grok voice/audio generation, story-to-speech, voice listing, custom voices, audio formats, and repo story annotation workflows.

Add required rules:Use current docs for xAI API details before inventing endpoints or fields.
Read `XAI_API_KEY` from environment; never hardcode or print secrets.
Use `<https://api.x.ai/v1/tts>` for TTS, `GET /v1/tts/voices` for voices, and `/v1/custom-voices` for custom voice creation.
Respect the documented 15,000 character text limit and chunk longer story text.

Add implementation guidance:Prefer requests for TTS because current Context7 TTS examples are REST-based.
Use `xai-sdk` for chat-based annotation workflows where the repo helper scripts already use `Client().chat.create(...)`.
Reference `.agent/skills/xai-tts-api/resources/annotate.md` when annotating stories for expressive speech tags.
Mention the existing helper scripts under `.agent/skills/xai-tts-api/scripts/` and require import/path verification before using them.

Add compact examples:List voices.
Generate `hello.mp3` using built-in `voice_id: "eve"`.
Generate other supported formats such as WAV/PCM after verifying the current docs.
Create and use a custom voice from a reference clip.

## Evaluation Plan

Create `evals/evals.json` for the skill and run the full skill-creator loop:
Eval 1: Ask for Python code that lists xAI TTS voices and generates a short MP3 without exposing the API key.
Eval 2: Ask for a repo-specific workflow to annotate a story and synthesize chunked audio from it.
Eval 3: Ask how to create a custom voice from a WAV reference and then use it for TTS.
Add optional live API test cases, clearly marked as opt-in:
Live API 1: With `XAI_API_KEY` set, call `GET /v1/tts/voices` and verify the response is JSON with available voice data.
Live API 2: Generate a very short MP3 from "Hello from the xAI TTS smoke test.", save it under a temp/test output directory, and verify nonzero bytes plus an MP3-like response/content type when available.
Live API 3: Generate a short WAV output if the current docs confirm the exact format field, then verify nonzero bytes and file extension.
Live API guardrails:Skip automatically when `XAI_API_KEY` is missing.
Never use story content or long transcripts in live smoke tests.
Keep generated text under 100 characters to minimize cost.
Do not create custom voices in automated live tests unless explicitly requested, because that requires user-provided reference audio and may have account/storage implications.

Run each non-live eval with and without the new skill, save outputs under `.agent/skills/xai-tts-api-workspace/iteration-1/`, draft objective assertions, grade outputs, aggregate benchmark results, and generate a static review page with eval-viewer/generate_review.py.

## Assumptions

The first implementation pass updates SKILL.md and eval artifacts only.
Live API tests are optional and gated behind explicit opt-in plus XAI_API_KEY.
If helper-script execution becomes part of the evals, first fix or account for the current storybuilder.xaiapi.client import mismatch in .agent/skills/xai-tts-api/scripts/annotate.py.

XAI TTS API Skill Implementation

# TODO

- [ ] Test the benchmark properly using the `benchmark.py` script using the provided evals and sub-agents.
- [ ] Update the review.html to display the results properly. If not good , go back to LLM and ask it to fix it.
