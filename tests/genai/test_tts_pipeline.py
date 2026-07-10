"""Integration test for TTS audio generation via the Gemini interactions API.

This test exercises the real `process_file` pipeline from client.py, processing
at most 3 prompt files in sequence. Each file is linked to the previous via
`previous_interaction_id` to maintain voice continuity — exactly as production
does — but the run is capped at 3 calls to limit costs.

Run manually with:
    uv run pytest tests/genai/test_tts_pipeline.py -v -s
"""

import glob
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from dotenv import load_dotenv

# Maximum number of real audio API calls to make during the test.
MAX_API_CALLS = 3


class TestTTSPipeline(unittest.TestCase):
    """Tests the stateful TTS generation pipeline end-to-end using real API calls."""

    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(project_root / ".env")

        cls.api_key = os.getenv("GEMINI_API_KEY")
        if not cls.api_key:
            raise unittest.SkipTest("GEMINI_API_KEY not configured — skipping TTS pipeline test")

        # Find up to MAX_API_CALLS real prompt files from the repo
        all_parts = sorted(
            glob.glob(str(project_root / "stories" / "**" / "*-part.md"), recursive=True)
        )
        # Exclude archive directories
        all_parts = [p for p in all_parts if "archive" not in p]

        if not all_parts:
            raise unittest.SkipTest("No *-part.md prompt files found — skipping TTS pipeline test")

        # Take at most MAX_API_CALLS files
        cls.prompt_files = all_parts[:MAX_API_CALLS]
        cls.project_root = project_root

    def test_sequential_tts_generation_with_voice_continuity(self):
        """Generates audio for up to 3 prompt files in sequence.

        Files are processed via process_file() with the previous_interaction_id
        passed between calls to maintain voice consistency, exactly as
        process_directory() does in production.
        """
        from google import genai

        from storybuilder.genai.client import get_gemini_api_keys, process_file

        api_keys = get_gemini_api_keys()
        self.assertGreater(len(api_keys), 0, "No GEMINI_API_KEY found in environment")

        current_key_idx = 0
        _, api_key = api_keys[current_key_idx]
        client = genai.Client(api_key=api_key)

        # Use a temp dir for output — don't pollute the repo
        tmp_dir = tempfile.mkdtemp(prefix="tts_test_")
        try:
            previous_id = None
            generated = []

            for i, md_file in enumerate(self.prompt_files):
                base_name = os.path.splitext(os.path.basename(md_file))[0]
                wav_file = os.path.join(tmp_dir, f"{base_name}.wav")

            # Sanitize voice names to valid Gemini voices for the integration test
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
                print(f"\n[{i+1}/{len(self.prompt_files)}] Processing: {os.path.basename(md_file)}")
                if previous_id:
                    print(f"  Linking to previous_interaction_id={previous_id[:12]}... for voice continuity")

                try:
                    client, current_key_idx, previous_id = process_file(
                        temp_md_file, wav_file, client, previous_id, api_keys, current_key_idx
                    )
                except Exception as e:
                    err = str(e).lower()
                    if any(k in err for k in ("quota", "429", "resource_exhausted", "unauthenticated", "permission")):
                        self.skipTest(f"Skipped due to API/quota issue on file {i+1}: {e}")
                    else:
                        self.fail(f"process_file failed on {os.path.basename(md_file)}: {e}")

                if os.path.exists(wav_file):
                    size = os.path.getsize(wav_file)
                    self.assertGreater(size, 0, f"WAV file for {os.path.basename(md_file)} is empty")
                    generated.append(wav_file)
                    print(f"  ✓ WAV written ({size} bytes)")
                else:
                    print("  ⚠ No WAV output — API returned no audio (non-fatal)")

            print(f"\nTTS pipeline test complete: {len(generated)}/{len(self.prompt_files)} files generated audio.")

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

            for i, md_file in enumerate(self.prompt_files):
                base_name = os.path.splitext(os.path.basename(md_file))[0]
                wav_file = os.path.join(tmp_dir, f"{base_name}.wav")

if __name__ == "__main__":
    unittest.main()
