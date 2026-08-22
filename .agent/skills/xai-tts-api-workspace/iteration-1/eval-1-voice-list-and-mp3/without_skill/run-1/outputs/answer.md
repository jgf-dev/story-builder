# xAI TTS sample

```python
import requests

API_KEY = "put-your-key-here"

response = requests.post(
	"https://api.x.ai/v1/audio/speech",
	headers={"Authorization": f"Bearer {API_KEY}"},
	json={"model": "grok-tts", "input": "Hello", "voice": "eve"},
)

open("hello.mp3", "wb").write(response.content)
```

You can add another request to find voices if needed.
