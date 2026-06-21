1. **Analyze the Issue:** We need to split the long `main()` function in `src/storybuilder/analysis/visualize_tsne.py` into smaller, focused helper functions to improve code health (readability and maintainability).
2. **Refactor Code:**
   - Extract command-line parsing into `parse_args()`.
   - Extract ChromaDB connection and data fetching into `fetch_embeddings(db_path)`.
   - Extract the t-SNE dimensionality reduction logic into `run_tsne(embeddings, perplexity_arg)`.
   - Extract the label extraction (short names and subcategories) logic into `extract_labels(ids)`.
   - Extract the interactive plot generation and saving logic into `create_and_save_plot(embeddings_2d, ids, short_names, subcategories, output_path)`.
   - Update `main()` to simply coordinate these new helper functions.
3. **Verify Refactoring:**
   - Run `python -m py_compile src/storybuilder/analysis/visualize_tsne.py` to catch any immediate syntax errors.
   - Run `uv run pytest tests/` to ensure no existing functionality was broken.
4. **Pre-commit:**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
5. **Submit:**
   - Commit the changes with a clear and descriptive message using the `submit` tool.
6. **Understand the target**: `dashboard.html` is a standalone editor for `TASKS.md`.
7. **Identify UX issue**: Users naturally press `Ctrl+S` / `Cmd+S` when using a text editor. Currently, this triggers the browser's native "Save Page As..." dialog, which is frustrating and interrupts the workflow.
8. **Select enhancement**: Implement `Ctrl+S` / `Cmd+S` keyboard shortcut intercept to trigger the custom `saveBtn` click instead. Add `aria-keyshortcuts` and `title` to the Save button to provide visual and screen-reader hints.
9. **Implement**:
   - Update `<button id="saveBtn">` with `title` and `aria-keyshortcuts`.
   - Add `keydown` event listener in `<script>` to intercept `Ctrl+S`/`Cmd+S` and trigger the save button.
10. **Verify**: Ensure the changes are syntactically correct and `< 50 lines`.
11. **Pre-commit**: Run tests/linters.
12. **Submit**: Create PR.
