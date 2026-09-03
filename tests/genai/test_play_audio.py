import sys
from unittest.mock import patch

from storybuilder.genai.play_audio import get_audio_player
from storybuilder.genai.play_audio import natural_sort_key


def test_get_audio_player_darwin() -> None:
	with patch.object(sys, "platform", "darwin"):
		assert get_audio_player() == ["afplay"]


def test_get_audio_player_win32() -> None:
	with patch.object(sys, "platform", "win32"):
		assert get_audio_player() == [
			"powershell",
			"-c",
			"(New-Object Media.SoundPlayer '{0}').PlaySync();",
		]


def test_get_audio_player_linux() -> None:
	with patch.object(sys, "platform", "linux"):
		assert get_audio_player() == ["aplay", "-q"]


def test_get_audio_player_other() -> None:
	with patch.object(sys, "platform", "freebsd"):
		assert get_audio_player() == ["aplay", "-q"]


def test_natural_sort_key_basic() -> None:
	assert natural_sort_key("apple") == ["apple"]
	assert natural_sort_key("Apple") == ["apple"]


def test_natural_sort_key_numbers() -> None:
	assert natural_sort_key("123") == ["", 123, ""]


def test_natural_sort_key_mixed() -> None:
	assert natural_sort_key("file1.wav") == ["file", 1, ".wav"]
	assert natural_sort_key("file10.wav") == ["file", 10, ".wav"]
	assert natural_sort_key("file2.wav") == ["file", 2, ".wav"]


def test_natural_sort_key_sorting_order() -> None:
	files = ["file10.wav", "file2.wav", "file1.wav"]
	sorted_files = sorted(files, key=natural_sort_key)
	assert sorted_files == ["file1.wav", "file2.wav", "file10.wav"]


def test_natural_sort_key_empty() -> None:
	assert natural_sort_key("") == [""]
