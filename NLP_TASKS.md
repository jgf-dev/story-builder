# NLP Tasks

## Tasks Annotation and review

Tasks are workflows that preprocess and queue up data for annotation or review and start the annotation server. You can view and create them in the UI via Tasks or using the CLI commands under ellf tasks.

## Named Entity Recognition

Annotate labeled text spans representing real-world objects like names, persons, countries or products.

### ner

**Span Categorization**
Annotate potentially overlapping and nested spans in the data.

### spans

**Text Classification**
Assign categories to whole documents or sentences.

### textcat

## Relation Extraction

Annotate relations between tokens and spans. Also supports joint span and relation annotation.

### relations

**Coreference Resolution**
Annotate coreference, i.e. links of ambiguous mentions like "her" or "the woman" back to an antecedent providing more context about the entity in question

### coref

**Dependency Parsing**
Annotate syntactic dependencies.

### dep

**Part of Speech tagging recipe**
Annotate word types.

### pos

**Terminology List**
Bootstrap a terminology list from word vectors. Terminology lists can be converted into patterns to help pre-select entity spans during annotation.

### terms

**Image Annotation & Classification**
Annotate bounding boxes and segments, or assign categories to images.

### image

**Annotate Audio**
Annotate regions, assign categories to audio content or transcribe audio files.

### audio

**Annotate Video**
Annotate regions, assign categories to video content or transcribe video files.

### video

**Curate and Explore**
View what's in your data and accept or reject examples

### curate

## Review Annotations

Review existing annotations created by multiple annotators and resolve potential conflicts by creating one final annotation.

### review

**Sentence Segmentation**
Create gold data for sentence boundaries by correcting a model's predictions

### sent

**Actions Training, evaluation and more**
Actions are workflows that execute any logic and exit, similar to jobs running in a CI system. You can view and create them in the UI via Actions or using the CLI commands under ellf actions.

## Dataset operations

Merge, copy and export annotated data

### db_actions

**Migrate dataset to structured**
Convert an unstructured dataset to the structured format

### migrate_to_structured

**Hello world**
Print 'hello world'

### hello_world

**Print dataset or file length**
Print the number of records in a dataset or lines in an input file.

### print_dataset_or_file_length

**Download spaCy models**
Download and install one or more spaCy models to shared storage so they can be loaded with spacy.load()

### download_spacy_models

**Train a spaCy pipeline**
Train a spaCy model with one or more components on annotated data

### train

**Textcat LLM fetch**
Gather text categorization predictions from an LLM

### llm_fetch_textcat

**Agents Auto-annotation and automation**
Agents are autonomous workers and annotators that can be assigned to tasks. They’re typically powered by LLMs and can use models running on the cluster or via APIs. You can view and create them in the UI via Agents or using the CLI commands under ellf agents.

## Gemini Annotation Agent

Autonomous annotation agent powered by Google Gemini

### gemini_agent

**spaCy Agent**
Deterministic local annotation agent for tests and development

### spacy_test_agent
