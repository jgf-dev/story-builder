import sys
from unittest.mock import patch

from storybuilder.genai.play_audio import get_audio_player


def test_get_audio_player_darwin() -> None:
    with patch.object(sys, "platform", "darwin"):
        assert get_audio_player() == ["afplay"]  # ruff: ignore[assert]


def test_get_audio_player_win32() -> None:
    with patch.object(sys, "platform", "win32"):
        assert get_audio_player() == [  # ruff: ignore[assert]
            "powershell",
            "-c",
            "(New-Object Media.SoundPlayer '{0}').PlaySync();",
        ]


def test_get_audio_player_linux() -> None:
    with patch.object(sys, "platform", "linux"):
        assert get_audio_player() == ["aplay", "-q"]  # ruff: ignore[assert]


def test_get_audio_player_other() -> None:
    with patch.object(sys, "platform", "freebsd"):
        assert get_audio_player() == ["aplay", "-q"]  # ruff: ignore[assert]
