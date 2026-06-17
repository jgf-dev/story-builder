# Google Genai SDK Data Model

## Step Types

**User steps:**

- `user_input`: User input (text, audio, multimodal). Contains `content` array.

**Model/server steps:**

- `model_output`: Final model generation. Contains `content` array with `text`, `image`, `audio`, etc.
- `thought`: Model reasoning/Chain of Thought. Has `signature` field (required) and optional `summary`.
- `function_call`: Tool call request (`id`, `name`, `arguments`).
- `function_result`: Tool result you send back (`call_id`, `name`, `result`).
- `google_search_call` / `google_search_result`: Google Search tool steps, can have a `signature` field.
- `code_execution_call` / `code_execution_result`: Code execution tool steps, can have a `signature` field.
- `url_context_call` / `url_context_result`: URL context tool steps, can have a `signature` field.
- `mcp_server_tool_call` / `mcp_server_tool_result`: Remote MCP tool steps.
- `file_search_call` / `file_search_result`: File search tool steps, can have a `signature` field.

## Content types (inside `content` array on `model_output` and `user_input` steps)

- `text`: Text content (`text` field)
- `image` / `audio` / `document` / `video`: Content with `data`, `mime_type`, or `uri`

## Streaming Event Types

| Event                       | Description                                                             |
| --------------------------- | ----------------------------------------------------------------------- |
| `interaction.created`       | Interaction created; includes metadata.                                 |
| `interaction.status_update` | Interaction-level status change.                                        |
| `step.start`                | A new step begins. Contains step `type` and initial metadata.           |
| `step.delta`                | Incremental data for the current step. Contains a typed `delta` object. |
| `step.stop`                 | The step is complete. Contains `index`.                                 |
| `interaction.complete`      | Interaction finished. Contains final `usage`.                           |

## Delta Types

| Delta Type          | Parent Step    | Description                                |
| ------------------- | -------------- | ------------------------------------------ |
| `text`              | `model_output` | Incremental text token.                    |
| `audio`             | `model_output` | audio chunk (base64).                      |
| `image`             | `model_output` | image chunk (base64).                      |
| `thought_summary`   | `thought`      | thinking summary text.                     |
| `thought_signature` | `thought`      | Opaque signature for thought verification. |

**Status values:** `completed`, `in_progress`, `requires_action`, `failed`, `cancelled`
