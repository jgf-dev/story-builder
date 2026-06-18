# TODO

## Story Scraper

- [x] Implement story scraper to scrape stories from nifty.org

## Story Database

- [x] Implement SQL database schema and database management module to store stories.
  - [x] Add FTS5 to the database schema.
  - [] Partial FTS Optimization: In partitioned mode, calling optimize_fts() only optimizes active connections currently loaded in_connections. Partitions that haven't been written to during the current run are ignored. Recommendation: Implement a mechanism to scan the partition folder and run the optimize PRAGMA command on all year databases in batch mode.
- [x] Parttion database by year.
  - [] Lack of cross-partition searching: While partitioning keeps file sizes highly manageable, SQLite cannot natively query across multiple closed databases. Recommendation: If using partitioned databases, ensure search clients (such as story_db.py) dynamically attach partition files using ATTACH DATABASE statements when performing global queries.

## Named Entity Recognition

- [x] Implement basic named entity recognition to extract character names, locations, and other entities from stories.
  - [] Refine named entity recognition to extract correct entities, relationships, etc.
- [] Implement a story search function to search stories based on named entities.

## TTS engine

### Prompt composer agent

- [] Implement a prompt composer agent to compose prompts for TTS engine.
- [] The prompt composer agent should be able to generate prompts for different TTS engines.

### GenAI TTS Client

- [] TTS Output Validation is non-existent. Recommendation: Plan a robust validation system to ensure the LLM adheres to all constraints and instructions.
  - [] Check if audio file is generated.
  - [] Check if character voices are correct in the generated audio file.
  - [] Check if the audio file contains all the dialogue in the scene.
  - [] Check if the audio file contains all the sound effects in the scene.
  - [] Check if voice actor performance are correct in the generated audio file and the annotations in the script are followed.

### ElevenLabs TTS Client

- [LATER] Add ElevenLabs TTS Client.

### Cartesia TTS Client

- [] Add Cartesia TTS Client.

## UI

- [] Implement story database viewer. The user needs to be able to search stories based on a prompt or filter stories by date, categories, etc.
- [] Add an export function to export stories to a markdown file.
- [] Add a statistics tab to show the number of stories by date, categories, genre, word count, named entities, etc.

## General Improvement

- [] Clean up single script files in the root directory and move the useful scripts to appropriate submodules.
