import sys
from pathlib import Path

# Add project root to sys.path and remove the script's directory to avoid module shadowing
if __name__ == "__main__":
    script_dir = str(Path(__file__).resolve().parent)
    if script_dir in sys.path:
        sys.path.remove(script_dir)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from storybuilder.downloader.cli import main

if __name__ == "__main__":
    main()
