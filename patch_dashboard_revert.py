with open("scripts/dashboard.py", "r") as f:
    content = f.read()

import re

# Adding back the unused import storybuilder_db which might be dynamically used or monkey patched in a way SonarCloud complains about differently. Wait, SonarCloud complained about Duplicate Code 3.6%.
# The annotations from the user for the second failure are:
# Failed Check Run 1: SonarCloud Code Analysis
# [3.6% Duplication on New Code]
# File: scripts/dashboard.py, Line: 176
# File: tests/genai/test_split_prompts.py, Line: 32
# File: tests/genai/test_tts_pipeline.py, Line: 66
# File: scripts/dashboard.py, Line: 144
# File: scripts/dashboard.py, Line: 410
# File: scripts/dashboard.py, Lines: 238-250

# It's a duplication issue! SonarCloud detected duplicated code!
