import os
import pathlib
import re
import subprocess


def run_git_cmd(args):
    return subprocess.run(args, capture_output=True, text=True)


def find_files_with_conflict_markers():
    # Scan files in src/, scripts/, tests/, evals/, tasks/, etc. or use grep
    res = subprocess.run(["grep", "-rl", "^<<<<<<< ", "."], capture_output=True, text=True)
    files = res.stdout.strip().split("\n")
    valid_files = []
    for f in files:
        if not f:
            continue
        # clean file path (remove leading './')
        f = f.removeprefix("./")
        if f.startswith(".venv/") or f.startswith(".git/"):
            continue
        valid_files.append(f)
    return valid_files


def resolve_file(filepath):
    print(f"Resolving conflicts in: {filepath}")
    content = pathlib.Path(filepath).read_text(encoding="utf-8")

    # Highly robust pattern to find conflict blocks matching <<<<<<< ... ======= ... >>>>>>> without crossing boundaries
    pattern = re.compile(
        r"<<<<<<< [^\n]+\n((?:(?!<<<<<<<|=======|>>>>>>>).)*?)=======\n((?:(?!<<<<<<<|=======|>>>>>>>).)*?)>>>>>>> [^\n]+",
        re.DOTALL,
    )

    basename = os.path.basename(filepath)

    def replacer(match):
        ours = match.group(1)
        theirs = match.group(2)

        # Rule 1: .gitignore
        if basename == ".gitignore":
            our_lines = ours.split("\n")
            their_lines = theirs.split("\n")
            combined = sorted(list(set(our_lines + their_lines)))
            combined = [l.strip() for l in combined if l.strip()]
            return "\n".join(combined) + "\n"

        # Rule 2: launch.json
        if basename == "launch.json":
            return theirs.rstrip("\r\n") + "\n"

        # Rule 3: AGENTS.md
        if basename == "AGENTS.md":
            return ours.rstrip("\r\n") + "\n"

        # Rule 4: evals/ files
        if filepath.startswith("evals/"):
            return ours.rstrip("\r\n") + "\n"

        # Rule 5: pyproject.toml
        if basename == "pyproject.toml":
            lines = []
            for line in ours.split("\n"):
                if "sqlmodel" in line:
                    lines.append(line.strip())
            for line in theirs.split("\n"):
                if "streamlit" in line or "tqdm" in line:
                    lines.append(line.strip())
            lines = [l for l in lines if l]
            formatted_lines = [f'    "{l.strip(' ",')}",' for l in lines]
            return "\n".join(formatted_lines) + "\n"

        # Rule 6: Database/Scraper related files
        if filepath in [
            "src/storybuilder/downloader/db.py",
            "src/storybuilder/downloader/storage.py",
            "src/storybuilder/downloader/scraper.py",
            "src/storybuilder/downloader/network.py",
            "src/storybuilder/downloader/cache.py",
            "tests/downloader/test_database.py",
            "tests/downloader/test_dashboard.py",
            "scripts/story_db.py",
        ]:
            return ours.rstrip("\r\n") + "\n"

        # Rule 7: dashboard files
        if filepath.startswith("src/storybuilder/dashboard/"):
            return ours.rstrip("\r\n") + "\n"

        # Rule 8: scripts/dashboard.py
        if basename == "dashboard.py":
            return ours.rstrip("\r\n") + "\n"

        # Rule 9: test_tts_pipeline.py
        if basename == "test_tts_pipeline.py":
            if "Path(md_file).stem" in theirs:
                return theirs.rstrip("\r\n") + "\n"
            return ours.rstrip("\r\n") + "\n"

        # Default fallback: keep ours
        return ours.rstrip("\r\n") + "\n"

    # Run sub in a loop to ensure we replace nested/multiple conflicts iteratively if needed
    old_content = ""
    while old_content != content:
        old_content = content
        content = pattern.sub(replacer, content)

    pathlib.Path(filepath).write_text(content, encoding="utf-8")


def main():
    files = find_files_with_conflict_markers()
    print(f"Found {len(files)} files with conflict markers: {files}")
    for f in files:
        if f:
            resolve_file(f)
            run_git_cmd(["git", "add", f])


if __name__ == "__main__":
    main()
