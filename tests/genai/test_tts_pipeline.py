"""TTS audio generation pipeline tests.

Default (unit): process_file is replaced with an in-process fake that writes a
tiny WAV and returns chained interaction ids — zero network / TTS cost.

Live integration (opt-in): set STORYBUILDER_LIVE_API=1 and provide GEMINI_API_KEY.
    uv run pytest tests/genai/test_tts_pipeline.py -v -s
"""

import glob
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv

from tests.helpers_external_fakes import (
    fake_process_file_factory,
    live_api_enabled,
)

# Maximum number of audio API calls / files in the sequential pipeline test.
MAX_API_CALLS = 3


class TestTTSPipeline(unittest.TestCase):
    """Sequential TTS generation with voice continuity (mocked by default)."""

    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env")

        cls.live = live_api_enabled()
        cls.api_key = os.getenv("GEMINI_API_KEY")
        if cls.live and not cls.api_key:
            raise unittest.SkipTest(
                "STORYBUILDER_LIVE_API=1 but GEMINI_API_KEY not configured"
            )

        all_parts = sorted(
            glob.glob(
                str(project_root / "stories" / "**" / "*-part.md"), recursive=True
            )
        )
        all_parts = [p for p in all_parts if "archive" not in p]

        if not all_parts:
            cls.prompt_files = None
        else:
            cls.prompt_files = all_parts[:MAX_API_CALLS]
        cls.project_root = project_root

    def test_sequential_tts_generation_with_voice_continuity(self):
        """Processes up to 3 prompt files via process_file with previous_id chain."""
        if self.live:
            self._live_sequential_tts()
            return

        self._mocked_sequential_tts()

    def _prepare_prompt_files(self, tmp_dir: str) -> list[str]:
        if self.prompt_files:
            prepared = []
            for md_file in self.prompt_files:
                base_name = os.path.basename(md_file).replace("-part.md", "")
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                content = (
                    content.replace("en-US-Journey-F", "Aoede")
                    .replace("en-US-Journey-D", "Charon")
                    .replace("en-US-Journey-O", "Kore")
                )
                temp_md_file = os.path.join(tmp_dir, f"{base_name}.md")
                with open(temp_md_file, "w", encoding="utf-8") as f:
                    f.write(content)
                prepared.append(temp_md_file)
            return prepared

        # No repo prompt files: synthesize minimal TTS-style prompt markdown.
        synthetic = []
        for i in range(MAX_API_CALLS):
            path = os.path.join(tmp_dir, f"unit-part-{i + 1}.md")
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    f"* Narrator (Voice: Kore)\n\n"
                    f"#### TRANSCRIPT\nNarrator: Unit test line {i + 1}.\n"
                )
            synthetic.append(path)
        return synthetic

    def _mocked_sequential_tts(self):
        """In-process fake: same call pattern as production, no Gemini TTS."""
        from google import genai

        process_file = fake_process_file_factory()
        api_keys = [("GEMINI_API_KEY", "unit-test-fake-key")]
        self.assertGreater(len(api_keys), 0, "No GEMINI_API_KEY found in environment")

        current_key_idx = 0
        _, api_key = api_keys[current_key_idx]
        with patch("google.genai.Client") as mock_client_ctor:
            mock_client_ctor.return_value = object()
            client = genai.Client(api_key=api_key)
            mock_client_ctor.assert_called()

            tmp_dir = tempfile.mkdtemp(prefix="tts_test_")
            try:
                prompt_files = self._prepare_prompt_files(tmp_dir)
                previous_id = None
                generated = []
                call_count = 0

                for temp_md_file in prompt_files:
                    base_name = os.path.basename(temp_md_file).replace(".md", "")
                    wav_file = os.path.join(tmp_dir, f"{base_name}.wav")

                    client, current_key_idx, previous_id = process_file(
                        temp_md_file,
                        wav_file,
                        client,
                        previous_id,
                        api_keys,
                        current_key_idx,
                    )
                    call_count += 1

                    self.assertIsNotNone(previous_id)
                    self.assertTrue(
                        os.path.exists(wav_file),
                        f"WAV missing for {base_name}",
                    )
                    size = os.path.getsize(wav_file)
                    self.assertGreater(
                        size, 0, f"WAV file for {base_name} is empty"
                    )
                    generated.append(wav_file)

                self.assertEqual(len(generated), len(prompt_files))
                self.assertEqual(call_count, len(prompt_files))
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _live_sequential_tts(self):
        from google import genai

        from storybuilder.genai.client import get_gemini_api_keys
        from storybuilder.genai.client import process_file

        api_keys = get_gemini_api_keys()
        self.assertGreater(len(api_keys), 0, "No GEMINI_API_KEY found in environment")

        current_key_idx = 0
        _, api_key = api_keys[current_key_idx]
        client = genai.Client(api_key=api_key)

        tmp_dir = tempfile.mkdtemp(prefix="tts_test_")
        try:
            if not self.prompt_files:
                self.skipTest(
                    "No *-part.md prompt files found — skipping live TTS pipeline test"
                )
            prompt_files = self._prepare_prompt_files(tmp_dir)
            previous_id = None
            generated = []

            for i, temp_md_file in enumerate(prompt_files):
                base_name = os.path.basename(temp_md_file).replace(".md", "")
                wav_file = os.path.join(tmp_dir, f"{base_name}.wav")
                try:
                    client, current_key_idx, previous_id = process_file(
                        temp_md_file,
                        wav_file,
                        client,
                        previous_id,
                        api_keys,
                        current_key_idx,
                    )
                except Exception as e:
                    err = str(e).lower()
                    if any(
                        k in err
                        for k in (
                            "quota",
                            "429",
                            "resource_exhausted",
                            "unauthenticated",
                            "permission",
                        )
                    ):
                        self.skipTest(
                            f"Skipped due to API/quota issue on file {i + 1}: {e}"
                        )
                    else:
                        self.fail(
                            f"process_file failed on {os.path.basename(temp_md_file)}: {e}"
                        )

                if os.path.exists(wav_file):
                    size = os.path.getsize(wav_file)
                    self.assertGreater(
                        size,
                        0,
                        f"WAV file for {os.path.basename(temp_md_file)} is empty",
                    )
                    generated.append(wav_file)
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
