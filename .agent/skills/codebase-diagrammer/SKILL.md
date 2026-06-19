---
name: codebase-diagrammer
title: "Codebase Diagrammer"
description: |
  Create a visual representation of a codebase's files, scripts, module dependencies,
  classes, functions, database connections, and user interfaces using structured Mermaid diagrams in a markdown file.
---

# Codebase Diagrammer

The Codebase Diagrammer skill reviews a repository structure and code logic to produce a Markdown document containing visual diagrams of the codebase. It relies on a Python script (`scripts/generate_diagrams.py`) to parse directories, Python AST trees, databases, and UI components, compiling them into a set of standard Mermaid diagrams.

## Workflow

To create architecture diagrams for a codebase:

1. **Run the Generator Script**:
   Execute the analyzer from the root of the repository:
   ```bash
   python .agent/skills/codebase-diagrammer/scripts/generate_diagrams.py --root-dir <path-to-codebase> --output-file <output-markdown-file>
   ```
   *Example:*
   ```bash
   python .agent/skills/codebase-diagrammer/scripts/generate_diagrams.py --root-dir . --output-file architecture.md
   ```

2. **Verify Diagram Correctness**:
   Open the generated markdown file and ensure the Mermaid syntax is correct. Note that:
   - Node IDs should contain only alphanumeric characters and underscores (`[a-zA-Z0-9_]`).
   - Labels containing special characters (like brackets, parenthesis, quotes) must be safely escaped or quoted (e.g. `node["label (info)"]`).
   - The script handles clean ID generation and label escaping, but custom modifications should maintain these conventions.

3. **Interpret the Output Diagrams**:
   The output contains five standard sections:
   - **Directory & Component Structure**: A nesting flowchart mapping directory hierarchies.
   - **Module & File Dependencies**: Dependency relationships showing imports between scripts.
   - **Key Classes & Functions**: Class method listings and module-level functions.
   - **Data Storage & API Flows**: Databases (SQLite, ChromaDB, S3) and local file storage.
   - **UI & Presentation Layers**: Streamlit dashboards, HTML templates, or visualization pages.

## Mermaid Design Guidelines

When adding custom diagrams or editing existing ones:
- **Keep lines short**: Wrap long connection descriptions to avoid visual clutter.
- **Direction**: Use `TD` (top-down) for directory structures, `RL` (right-to-left) or `LR` (left-to-right) for data and dependency flow to keep diagrams readable.
- **Subgraphs**: Group related modules into labeled subgraphs (e.g. `subgraph database [DB Layer]`).
- **Styles**: Use standard shapes to demarcate node types:
  - Database: `node_id[(\"DatabaseName\")]`
  - UI Screen/Route: `node_id{\"UI Screen/Route\"}`
  - Standard Script/Class: `node_id[\"ScriptName\"]`
