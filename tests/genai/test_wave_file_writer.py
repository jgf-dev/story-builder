import os
import pathlib
import wave
import tempfile

from storybuilder.genai.client import wave_file_writer

def test_wave_file_writer_creates_valid_wave_file():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = pathlib.Path(temp_dir) / "test.wav"
        test_pcm = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        channels = 1
        rate = 24000
        sample_width = 2

        wave_file_writer(str(temp_file), test_pcm, channels, rate, sample_width)

        assert temp_file.exists()

        with wave.open(str(temp_file), "rb") as wf:
            assert wf.getnchannels() == channels
            assert wf.getsampwidth() == sample_width
            assert wf.getframerate() == rate
            assert wf.readframes(wf.getnframes()) == test_pcm

def test_wave_file_writer_default_params():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = pathlib.Path(temp_dir) / "test_default.wav"
        test_pcm = b'\x00\x00\x00\x00\x00\x00\x00\x00'

        wave_file_writer(str(temp_file), test_pcm)

        assert temp_file.exists()

        with wave.open(str(temp_file), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 24000
            assert wf.readframes(wf.getnframes()) == test_pcm
