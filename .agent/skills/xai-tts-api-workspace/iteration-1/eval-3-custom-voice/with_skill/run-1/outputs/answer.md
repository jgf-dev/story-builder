# Opt-in custom voice example

Run this only after you explicitly approve a live API call and have a reference clip you are allowed to use. Custom voice creation is not part of automated smoke tests.

```python
import os

import requests

headers = {"Authorization": f"Bearer {os.environ['XAI_API_KEY']}"}

with open("reference.wav", "rb") as f:
	create = requests.post(
		"https://api.x.ai/v1/custom-voices",
		headers=headers,
		files={"file": ("reference.wav", f, "audio/wav")},
		data={"name": "Friendly Narrator", "language": "en"},
		timeout=300,
	)
create.raise_for_status()
voice_id = create.json()["voice_id"]

speech = requests.post(
	"https://api.x.ai/v1/tts",
	headers={**headers, "Content-Type": "application/json"},
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

Keep reference audio private, do not commit generated voice IDs if they are sensitive, and avoid custom voice creation in default CI.
