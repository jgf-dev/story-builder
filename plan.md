1. **Understand the target**: `dashboard.html` is a standalone editor for `TASKS.md`.
2. **Identify UX issue**: Users naturally press `Ctrl+S` / `Cmd+S` when using a text editor. Currently, this triggers the browser's native "Save Page As..." dialog, which is frustrating and interrupts the workflow.
3. **Select enhancement**: Implement `Ctrl+S` / `Cmd+S` keyboard shortcut intercept to trigger the custom `saveBtn` click instead. Add `aria-keyshortcuts` and `title` to the Save button to provide visual and screen-reader hints.
4. **Implement**:
   - Update `<button id="saveBtn">` with `title` and `aria-keyshortcuts`.
   - Add `keydown` event listener in `<script>` to intercept `Ctrl+S`/`Cmd+S` and trigger the save button.
5. **Verify**: Ensure the changes are syntactically correct and `< 50 lines`.
6. **Pre-commit**: Run tests/linters.
7. **Submit**: Create PR.
