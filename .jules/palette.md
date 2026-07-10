## 2026-06-22 - File Input Accessibility
**Learning:** Using `display: none` on native file inputs completely removes them from the accessibility tree and tab order, preventing keyboard users from accessing them, even if there's an associated `<label>` styled as a button.
**Action:** Use a `.sr-only` visually-hidden class for the `<input type="file">` instead, and place it immediately before its associated `<label>`. This allows using the adjacent sibling combinator (`input[type="file"]:focus-visible + .file-label`) to style the label when the hidden input receives keyboard focus, restoring full keyboard accessibility.
## 2026-06-23 - Keyboard Shortcuts in Web Editors
**Learning:** Users instinctively press Ctrl+S/Cmd+S to save work in web-based text editors. Failing to intercept this triggers the browser's native "Save Page As" dialog, which breaks the UX flow.
**Action:** When building web-based editors or forms where users spend significant time typing, always intercept standard save shortcuts (Ctrl+S/Cmd+S), prevent default behavior, and trigger the application's save function. Add `aria-keyshortcuts` to the corresponding button for screen reader visibility.
## 2024-06-29 - Save Button UX States
**Learning:** Users lack confidence when a save button is always enabled or when clicking it doesn't provide immediate feedback during a slow, asynchronous operation like writing to a local file system.
**Action:** When implementing save functionality, disable the save button visually (e.g., opacity, cursor) and functionally (prevent click/keyboard shortcuts) when there are no unsaved changes. Provide explicit loading states (e.g., "Saving...", wait cursor) during asynchronous operations to improve UX feedback.
## 2026-06-28 - Save Button Interactive UX
**Learning:** Leaving save buttons constantly enabled without providing feedback on dirty states or active operations can lead to user confusion. When users press "Save", they need immediate visual feedback that the application is processing the request, and when they have no unsaved changes, the button should communicate that saving is unnecessary.
**Action:** When implementing save functionality in web interfaces (like dashboard.html), disable the save button visually (e.g., opacity, cursor) and functionally (prevent click/keyboard shortcuts) when there are no unsaved changes (`isDirty`), and provide explicit loading states (e.g., 'Saving...', wait cursor) during asynchronous operations to improve UX feedback.
## 2024-06-29 - Save Button UX States
**Learning:** Users lack confidence when a save button is always enabled or when clicking it doesn't provide immediate feedback during a slow, asynchronous operation like writing to a local file system.
**Action:** When implementing save functionality, disable the save button visually (e.g., opacity, cursor) and functionally (prevent click/keyboard shortcuts) when there are no unsaved changes. Provide explicit loading states (e.g., "Saving...", wait cursor) during asynchronous operations to improve UX feedback.

## 2024-05-20 - Ensure single unique ID for file inputs when using visually-hidden labels
**Learning:** When styling file inputs using an associated `<label>`, ensuring only a single `<input>` has the targeted `id` is critical. Duplicate IDs cause unpredictable `label for="..."` association, screen reader confusion, and duplicate rendering of native file inputs alongside the custom UI.
**Action:** When inspecting visually styled `<input type="file">` elements, verify there is only a single input per ID, typically hidden with `.sr-only` right before the `<label>`, and remove any duplicate visible inputs.
