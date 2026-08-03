1. Use `run_in_bash_session` to create `tests/utils/__init__.py` with `touch tests/utils/__init__.py` to satisfy Ruff's `implicit-namespace-package` rule.
2. Use `run_in_bash_session` to create `tests/utils/test_logging_config.py` with test cases for `get_logger` (testing both basic logger creation and creation with a specific level) using `cat << 'EOF' > tests/utils/test_logging_config.py...EOF`.
3. Use `run_in_bash_session` to execute `uv run pytest tests/utils/test_logging_config.py` to verify the tests pass.
4. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
5. Use the `submit` tool to create a pull request with the title "🧪 [testing improvement] Add tests for get_logger utility" and the required description format.
