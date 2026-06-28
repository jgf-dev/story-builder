import unittest
import sys
import tempfile
import shutil
from pathlib import Path

# Add the script directory to Python path
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]