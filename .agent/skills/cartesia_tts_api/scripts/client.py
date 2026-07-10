import os

from cartesia import Cartesia
from cartesia.types import VoiceSpecifierParam
from cartesia.types import WAVOutputFormatParam
from dotenv import load_dotenv


load_dotenv()

client: Cartesia = Cartesia(api_key=os.getenv("CARTESIA_API_KEY"))


def generate_speech(text: str, voice: str):
    response = client.tts.generate(
        model_id="sonic-latest",
        transcript=text,
        voice=VoiceSpecifierParam(id=voice, mode="id"),
<<<<<<< Updated upstream
        output_format=WAVOutputFormatParam(
            sample_rate=48000,
            encoding="pcm_f32le",
            container="wav",
        ),
=======
        output_format=WAVOutputFormatParam(sample_rate=48000, encoding="pcm_f32le", container="wav"),
>>>>>>> Stashed changes
        language="en",
    )
    response.write_to_file("output.wav")


if __name__ == "__main__":
    generate_speech("Hello, world!", "6ccbfb76-1fc6-48f7-b71d-91ac6298247b")
