## 2024-05-20 - Ensure single unique ID for file inputs when using visually-hidden labels
**Learning:** When styling file inputs using an associated `<label>`, ensuring only a single `<input>` has the targeted `id` is critical. Duplicate IDs cause unpredictable `label for="..."` association, screen reader confusion, and duplicate rendering of native file inputs alongside the custom UI.
**Action:** When inspecting visually styled `<input type="file">` elements, verify there is only a single input per ID, typically hidden with `.sr-only` right before the `<label>`, and remove any duplicate visible inputs.

## 2024-05-20 - Ensure single unique ID for file inputs when using visually-hidden labels
**Learning:** When styling file inputs using an associated `<label>`, ensuring only a single `<input>` has the targeted `id` is critical. Duplicate IDs cause unpredictable `label for="..."` association, screen reader confusion, and duplicate rendering of native file inputs alongside the custom UI.
**Action:** When inspecting visually styled `<input type="file">` elements, verify there is only a single input per ID, typically hidden with `.sr-only` right before the `<label>`, and remove any duplicate visible inputs.
