import os

from google import genai


def main() -> None:
	api_key = os.getenv("GEMINI_API_KEY")
	client = genai.Client(api_key=api_key)

	speech_config = [
		{"speaker": "Narrator", "voice": "Zubenelgenubi"},
		{"speaker": "Levi", "voice": "Zubenelgenubi"},
		{"speaker": "Jace", "voice": "Algenib"},
	]

	try:
		client.interactions.create(
			model="gemini-3.1-flash-tts-preview",
			input="Narrator: The sun set over the mountains.\nLevi: Hey Jace.\nJace: Hey Levi.",
			response_modalities=["audio"],
			generation_config={"speech_config": speech_config},
		)
		print("Success!")
	except Exception as e:
		print(f"Error: {e}")


if __name__ == "__main__":
	main()
