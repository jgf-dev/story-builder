# Custom voice

Upload a voice sample, then use the voice in a TTS request:

```python
import requests

key = "YOUR_KEY"
voice = requests.post(
	"https://api.x.ai/v1/voices",
	headers={"Authorization": f"Bearer {key}"},
	files={"audio": open("reference.wav", "rb")},
).json()["id"]

audio = requests.post(
	"https://api.x.ai/v1/tts",
	headers={"Authorization": f"Bearer {key}"},
	json={"text": "Hello", "voice": voice},
).content

open("custom.mp3", "wb").write(audio)
```
