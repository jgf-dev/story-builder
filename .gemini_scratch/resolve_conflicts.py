#!/usr/bin/env python3
"""Resolve 2-way merge conflicts favoring HEAD for code, merging both for additive content.

Strategy:
- For Python/TOML files: Keep HEAD's version of each conflict (it's the newer codebase)
- For docs/config: Keep both sides where possible
"""

import re
import sys
from pathlib import Path


def resolve_keep_head(filepath: str) -> bool:
    """Resolve conflicts by keeping HEAD's version."""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8", errors="replace")

    if "<<<<<<< HEAD" not in content:
        return False

    pattern = re.compile(r"<<<<<<<\s+HEAD\n(.*?)=======\n(.*?)>>>>>>>\s+[^\n]+\n", re.DOTALL)

    def keep_head(match: re.Match) -> str:
        return match.group(1)  # Keep HEAD content only

    resolved = pattern.sub(keep_head, content)
    path.write_text(resolved, encoding="utf-8")
    return True


def resolve_keep_both(filepath: str) -> bool:
    """Resolve conflicts by keeping both HEAD and incoming."""
    path = Path(filepath)
    content = path.read_text(encoding="utf-8", errors="replace")

    if "<<<<<<< HEAD" not in content:
        return False

    pattern = re.compile(r"<<<<<<<\s+HEAD\n(.*?)=======\n(.*?)>>>>>>>\s+[^\n]+\n", re.DOTALL)

    def keep_both(match: re.Match) -> str:
        head = match.group(1)
        incoming = match.group(2)
        head_stripped = head.strip()
        incoming_stripped = incoming.strip()

        if not head_stripped and not incoming_stripped:
            return ""
        if not head_stripped:
            return incoming
        if not incoming_stripped:
            return head
        return head + incoming

    resolved = pattern.sub(keep_both, content)
    path.write_text(resolved, encoding="utf-8")
    return True


if __name__ == "__main__":
    mode = sys.argv[1]  # "head" or "both"
    func = resolve_keep_head if mode == "head" else resolve_keep_both

    for filepath in sys.argv[2:]:
        try:
            if func(filepath):
                print(f"  ✓ {mode}: {filepath}")
            else:
                print(f"  - No conflicts: {filepath}")
        except Exception as e:
            print(f"  ✗ Error: {filepath}: {e}")
