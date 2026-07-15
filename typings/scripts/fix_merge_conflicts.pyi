from pathlib import Path

ROOT: Path
SKIP_PARTS: set[str]


def resolve_file(path: Path) -> bool: ...


def main() -> None: ...
