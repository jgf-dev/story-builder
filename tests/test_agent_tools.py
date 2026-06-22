"""Tests for the TTS Prompt Crafter agent tools."""

import os
import shutil
import tempfile
import unittest


class TestReadStory(unittest.TestCase):
    """Tests for the read_story tool function."""

    def setUp(self):
        import unittest.mock
        self.tmpdir = tempfile.mkdtemp()
        self.story_path = os.path.join(self.tmpdir, "test_story.md")
        with open(self.story_path, "w") as f:
            f.write("# Test Story\n\nOnce upon a time...\n")
        self.patcher = unittest.mock.patch("storybuilder.agents.tts_prompt_crafter.tools._STORIES_DIR", self.tmpdir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.tmpdir)

    def test_read_existing_story(self):
        from storybuilder.agents.tts_prompt_crafter.tools import read_story

        result = read_story(self.story_path)
        self.assertIn("# Test Story", result)
        self.assertIn("Once upon a time", result)

    def test_read_nonexistent_story(self):
        from storybuilder.agents.tts_prompt_crafter.tools import read_story

        result = read_story("/nonexistent/path.md")
        self.assertIn("Error", result)
        self.assertIn("not found", result)

    def test_read_relative_path_rejected(self):
        from storybuilder.agents.tts_prompt_crafter.tools import read_story

        result = read_story("relative/path.md")
        self.assertIn("Error", result)
        self.assertIn("absolute path", result)

    def test_read_story_by_name(self):
        from storybuilder.agents.tts_prompt_crafter.tools import read_story

        result = read_story("test_story")
        self.assertIn("# Test Story", result)


class TestListStories(unittest.TestCase):
    """Tests for the list_stories tool function."""

    def setUp(self):
        import unittest.mock
        self.tmpdir = tempfile.mkdtemp()
        # Create some test .md files
        for name in ["story_a.md", "story_b.md", "not_a_story.txt"]:
            with open(os.path.join(self.tmpdir, name), "w") as f:
                f.write("content")
        self.patcher = unittest.mock.patch("storybuilder.agents.tts_prompt_crafter.tools._STORIES_DIR", self.tmpdir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.tmpdir)

    def test_list_md_files(self):
        from storybuilder.agents.tts_prompt_crafter.tools import list_stories

        result = list_stories(self.tmpdir)
        self.assertIn("story_a.md", result)
        self.assertIn("story_b.md", result)
        self.assertNotIn("not_a_story.txt", result)

    def test_list_empty_directory(self):
        from storybuilder.agents.tts_prompt_crafter.tools import list_stories

        empty_dir = tempfile.mkdtemp()
        try:
            result = list_stories(empty_dir)
            self.assertIn("No .md files", result)
        finally:
            shutil.rmtree(empty_dir)

    def test_list_nonexistent_directory(self):
        from storybuilder.agents.tts_prompt_crafter.tools import list_stories

        result = list_stories("/nonexistent/dir")
        self.assertIn("Error", result)
        self.assertIn("not found", result)

    def test_list_relative_path_rejected(self):
        from storybuilder.agents.tts_prompt_crafter.tools import list_stories

        result = list_stories("relative/dir")
        self.assertIn("Error", result)
        self.assertIn("absolute path", result)

    def test_list_default_directory(self):
        from storybuilder.agents.tts_prompt_crafter.tools import list_stories

        result = list_stories()
        self.assertIn("story_a.md", result)


class TestWriteSceneFile(unittest.TestCase):
    """Tests for the write_scene_file tool function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.story_path = os.path.join(self.tmpdir, "test_story.md")
        with open(self.story_path, "w") as f:
            f.write("# Test Story\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_write_creates_output_dir_and_file(self):
        from storybuilder.agents.tts_prompt_crafter.tools import write_scene_file

        content = "# SYSTEM PREAMBLE: ...\n\n#### TRANSCRIPT\nJace: Hello."
        result = write_scene_file(self.story_path, "01-scene1.md", content)

        self.assertIn("Successfully", result)
        output_dir = os.path.join(self.tmpdir, "output")
        self.assertTrue(os.path.isdir(output_dir))

        filepath = os.path.join(output_dir, "01-scene1.md")
        self.assertTrue(os.path.exists(filepath))
        with open(filepath) as f:
            self.assertEqual(f.read(), content)

    def test_write_rejects_invalid_filename(self):
        from storybuilder.agents.tts_prompt_crafter.tools import write_scene_file

        result = write_scene_file(self.story_path, "bad_name.md", "content")
        self.assertIn("Error", result)
        self.assertIn("*-scene*.md", result)

    def test_write_rejects_non_md_filename(self):
        from storybuilder.agents.tts_prompt_crafter.tools import write_scene_file

        result = write_scene_file(self.story_path, "01-scene1.txt", "content")
        self.assertIn("Error", result)

    def test_write_rejects_relative_path(self):
        from storybuilder.agents.tts_prompt_crafter.tools import write_scene_file

        result = write_scene_file("relative/story.md", "01-scene1.md", "c")
        self.assertIn("Error", result)
        self.assertIn("absolute path", result)

    def test_write_accepts_output_directory(self):
        from storybuilder.agents.tts_prompt_crafter.tools import write_scene_file

        output_dir = os.path.join(self.tmpdir, "manual-output")
        os.makedirs(output_dir)
        result = write_scene_file(output_dir, "01-scene1.md", "content")
        self.assertIn("Successfully", result)
        self.assertTrue(os.path.exists(os.path.join(output_dir, "01-scene1.md")))


class TestSplitSceneFiles(unittest.TestCase):
    """Tests for the split_scene_files tool function."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.story_path = os.path.join(self.tmpdir, "test_story.md")
        with open(self.story_path, "w") as f:
            f.write("# Test Story\n")
        self.output_dir = os.path.join(self.tmpdir, "output")
        os.makedirs(self.output_dir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_split_produces_parts(self):
        from storybuilder.agents.tts_prompt_crafter.tools import split_scene_files

        # Create a scene file with 3 speakers (forces a split)
        scene_content = (
            "# SYSTEM PREAMBLE: Synthesize speech ONLY...\n\n"
            "# AUDIO PROFILE: Test\n\n"
            "### DIRECTOR'S NOTES\n\n"
            "Style:\n\n"
            "- Alice (Voice: Kore): Test\n"
            "- Bob (Voice: Puck): Test\n"
            "- Charlie (Voice: Enceladus): Test\n\n"
            "#### TRANSCRIPT\n"
            "Alice: Hello there.\n"
            "Bob: Hi Alice!\n"
            "Charlie: Hey everyone.\n"
        )
        scene_path = os.path.join(self.output_dir, "01-scene1.md")
        with open(scene_path, "w") as f:
            f.write(scene_content)

        result = split_scene_files(self.story_path)
        self.assertIn("Split complete", result)
        self.assertIn("part", result)

        # Verify scene file was archived
        archived = os.path.join(self.output_dir, "archive", "01-scene1.md")
        self.assertTrue(os.path.exists(archived))

    def test_split_no_output_dir(self):
        from storybuilder.agents.tts_prompt_crafter.tools import split_scene_files

        # Remove the output dir
        shutil.rmtree(self.output_dir)
        result = split_scene_files(self.story_path)
        self.assertIn("Error", result)
        self.assertIn("not found", result)

    def test_split_no_scene_files(self):
        from storybuilder.agents.tts_prompt_crafter.tools import split_scene_files

        # output dir exists but is empty
        result = split_scene_files(self.story_path)
        self.assertIn("Error", result)
        self.assertIn("No *-scene*.md", result)

    def test_split_rejects_relative_path(self):
        from storybuilder.agents.tts_prompt_crafter.tools import split_scene_files

        result = split_scene_files("relative/story.md")
        self.assertIn("Error", result)
        self.assertIn("absolute path", result)

    def test_split_accepts_output_directory(self):
        from storybuilder.agents.tts_prompt_crafter.tools import split_scene_files

        scene_content = (
            "# SYSTEM PREAMBLE: Synthesize speech ONLY...\n\n"
            "# AUDIO PROFILE: Test\n\n"
            "### DIRECTOR'S NOTES\n\n"
            "Style:\n\n"
            "- Alice (Voice: Kore): Test\n"
            "- Bob (Voice: Puck): Test\n\n"
            "#### TRANSCRIPT\n"
            "Alice: Hello there.\n"
            "Bob: Hi Alice!\n"
        )
        scene_path = os.path.join(self.output_dir, "02-scene1.md")
        with open(scene_path, "w") as f:
            f.write(scene_content)

        result = split_scene_files(self.output_dir)
        self.assertIn("Split complete", result)


if __name__ == "__main__":
    unittest.main()
