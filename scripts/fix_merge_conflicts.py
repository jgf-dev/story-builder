#!/usr/bin/env python3
"""Auto-resolve git merge conflict markers by keeping the HEAD side."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_PARTS = {".git", "venv", ".venv", "__pycache__", ".ruff_cache", "stories"}


def resolve_file(path: Path) -> bool:
	try:
		text = path.read_text(encoding="utf-8")
	except (UnicodeDecodeError, OSError):
		return False
<<<<<<< HEAD
=======
	if "<<<<<<<" not in text:
>>>>>>> origin/main
		return False

	out_lines: list[str] = []
	lines = text.splitlines()
	i = 0
	n = len(lines)
	changed = False
	while i < n:
		line = lines[i]
		if "<<<<<<<" in line:
			i += 1
			head_lines: list[str] = []
			while i < n and not lines[i].startswith("======="):
				head_lines.append(lines[i])
				i += 1
			if i < n and lines[i].startswith("======="):
				i += 1
			while i < n and ">>>>>>>" not in lines[i]:
				i += 1
			if i < n and ">>>>>>>" in lines[i]:
				i += 1
			out_lines.extend(head_lines)
			changed = True
		else:
			out_lines.append(line)
			i += 1

	if changed:
		path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
	return changed


def main() -> None:
	fixed: list[Path] = []
	skipped: list[tuple[Path, str]] = []
	for path in ROOT.rglob("*"):
		if not path.is_file():
			continue
		if any(part in SKIP_PARTS or part.startswith(".git") for part in path.parts):
			continue
		try:
			if resolve_file(path):
				fixed.append(path.relative_to(ROOT))
		except Exception as exc:
			skipped.append((path.relative_to(ROOT), str(exc)))

	print(f"Fixed {len(fixed)} files")
	for p in fixed:
		print(p)
	if skipped:
		print("\nSkipped files with errors:")
		for p, err in skipped:
			print(p, err)


if __name__ == "__main__":
	main()
