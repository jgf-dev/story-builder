# Markr AI Config Health

Workspace: **story-builder**
Generated: 6/19/2026, 4:24:00 AM

## Readiness Score

**78/100** · 3 config files · ~5.4K tok across AI context docs

| Check | Status |
| --- | --- |
| Primary instructions | Ready |
| Commands documented | Needs attention |
| Testing guidance | Needs attention |
| Safety guidance | Needs attention |
| MCP config | Needs attention |
| Env example | Needs attention |

## Priority Fixes

- **Medium: Env file exists without an example**. Agents need variable names, not private values. Fix: Add .env.example with safe placeholders.
- **Info: No MCP config detected**. This is fine if the workspace does not use MCP tools yet. Fix: Add .vscode/mcp.json or mcp.json when the project needs tool servers.

## Config Inventory

| File | Kind | Size | Notes |
| --- | --- | ---: | --- |
| `.env` | ENV | 311 tok | 14 env keys |
| `AGENTS.md` | Agent | ~5.1K tok | 12 headings, commands documented, verification guidance |
| `src/storybuilder/agents/tts_prompt_crafter/.env` | AI Doc | 25 tok | 3 env keys |

## Recommended Next Moves

1. Fix Critical and High findings first, especially secrets and missing verification commands.
2. Keep one primary instruction file as the source of truth, then link tool-specific files to it.
3. Use Context Bridge when a session crosses 65% context, and hand off before 85%.
4. Use Mermaid/Gantt diagrams for plans, but keep the source copyable so another tool can continue the diagram.
