## 2026-06-22 - File Input Accessibility
**Learning:** Using `display: none` on native file inputs completely removes them from the accessibility tree and tab order, preventing keyboard users from accessing them, even if there's an associated `<label>` styled as a button.
**Action:** Use a `.sr-only` visually-hidden class for the `<input type="file">` instead, and place it immediately before its associated `<label>`. This allows using the adjacent sibling combinator (`input[type="file"]:focus-visible + .file-label`) to style the label when the hidden input receives keyboard focus, restoring full keyboard accessibility.
## 2026-06-23 - Keyboard Shortcuts in Web Editors
**Learning:** Users instinctively press Ctrl+S/Cmd+S to save work in web-based text editors. Failing to intercept this triggers the browser's native "Save Page As" dialog, which breaks the UX flow.
**Action:** When building web-based editors or forms where users spend significant time typing, always intercept standard save shortcuts (Ctrl+S/Cmd+S), prevent default behavior, and trigger the application's save function. Add `aria-keyshortcuts` to the corresponding button for screen reader visibility.
## 2026-06-24 - Unsaved Changes Protection in Editors
**Learning:** Web-based text editors can lose data if the user accidentally closes the tab, navigates away, or refreshes the page. Without visual indicators or warnings, this can result in significant frustration and poor UX.
**Action:** When building web-based editors or forms where users spend significant time typing, implement a `beforeunload` event listener to intercept page navigation if there are unsaved changes. Also, update the document title and UI to visually indicate the "dirty" state (e.g., adding an asterisk `*` to the title).
