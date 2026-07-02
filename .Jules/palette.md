## 2024-03-05 - Duplicate file inputs
**Learning:** When using custom styled labels for file inputs (using `.sr-only` hidden inputs), ensure there is only one input with the target ID, otherwise the `label for=...` attribute behavior will be unpredictable and duplicate native inputs will be rendered visually.
**Action:** Removed duplicate unstyled `<input type="file">`. Double-check HTML to ensure unique IDs.
