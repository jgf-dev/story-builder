# StoryBuilder xAI TTS workflow

1. Pick a story path or slug and keep the original source file untouched.
2. If expressive annotation is requested, read `.agent/skills/xai-tts-api/resources/annotate.md` and insert only supported speech tags. Preserve the story's original words.
3. Inspect `.agent/skills/xai-tts-api/scripts/client.py` and `.agent/skills/xai-tts-api/scripts/annotate.py` before execution. The current `annotate.py` imports `storybuilder.xaiapi.client`, but the available client lives in the skill's `scripts/` directory, so verify or fix that import path first.
4. Chunk annotated text under the xAI TTS 15,000 character request limit. Prefer paragraph boundaries and smaller chunks for retries.
5. For each chunk, call `POST https://api.x.ai/v1/tts` with `XAI_API_KEY` from the environment, a selected `voice_id`, and `language`.
6. Save outputs as numbered files such as `001.mp3`, `002.mp3`, and write a manifest recording chunk source, voice ID, language, format, and output path.
7. Skip existing audio unless the user asks to overwrite.

Live calls should be opt-in. Default validation should use dry-run code or short smoke-test text, not full story content.
