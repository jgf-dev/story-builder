# xAI TTS voices and MP3 example

This is a dry-run example. It reads `XAI_API_KEY` from the environment and does not run unless you execute it yourself.

```python
import json
import os

import requests

api_key = os.environ["XAI_API_KEY"]
headers = {"Authorization": f"Bearer {api_key}"}

voices = requests.get(
    "https://api.x.ai/v1/tts/voices",
    headers=headers,
    timeout=60,
)
voices.raise_for_status()
print(json.dumps(voices.json(), indent=2))

speech = requests.post(
    "https://api.x.ai/v1/tts",
    headers={
        **headers,
        "Content-Type": "application/json",
    },
    json={
        "text": "Hello! Welcome to the xAI Text to Speech API.",
        "voice_id": "eve",
        "language": "en",
    },
    timeout=120,
)
speech.raise_for_status()

with open("hello.mp3", "wb") as f:
    f.write(speech.content)
```

Do not print or commit the API key. For live testing, keep the text short and write audio to a temp or test output directory.
