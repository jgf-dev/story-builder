#!/usr/bin/env python3
"""
Simple utility to auto-resolve git merge conflict markers by keeping the
Use with caution and review changes before committing.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def resolve_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "<<<<<<<" not in text:
        return False
    out_lines = []
    i = 0
    lines = text.splitlines()
    n = len(lines)
    changed = False
    while i < n:
        line = lines[i]
        # detect markers anywhere in the line (allow leading/trailing spaces)
        if "<<<<<<<" in line:
            # collect HEAD side
            i += 1
            head_lines = []
            while i < n and ">>>>>>>" not in lines[i]:
                i += 1
            # skip the >>>>>>> marker
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


def main():
    files = list(ROOT.rglob("*"))
    skipped = []
    fixed = []
    for f in files:
        if not f.is_file():
            continue
        # skip virtual envs, git dir, .venv, .git
        if any(part.startswith(".git") or part in ("venv", ".venv", "__pycache__") for part in f.parts):
            continue
        try:
            if resolve_file(f):
                fixed.append(f.relative_to(ROOT))
        except Exception as e:
            skipped.append((f.relative_to(ROOT), str(e)))
    print(f"Fixed {len(fixed)} files")
    for p in fixed[:100]:
        print(p)
    if skipped:
        print("\nSkipped files with errors:")
        for p, err in skipped:
            print(p, err)


if __name__ == "__main__":
    main()
