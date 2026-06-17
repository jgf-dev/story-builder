# Story audio workflow

Use an LLM to add pauses and emotion tags to the story, split it into pieces, then send each piece to xAI. Save each returned audio file as an MP3.

Example steps:

1. Read the story.
2. Ask Grok to improve it for narration.
3. Split every few thousand words.
4. Send each chunk to a TTS endpoint.
5. Merge the MP3 files.

Check the scripts folder for anything useful.
