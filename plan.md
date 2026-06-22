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
