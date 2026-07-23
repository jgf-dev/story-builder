## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.
## 2024-03-05 - Enhance semantic regions with aria attributes
**Learning:** HTML5 `<section>` elements do not act as semantic `region` landmarks for screen reader navigation by default unless they have an accessible name.
**Action:** When a `<section>` acts as a complex structural region (like a card or widget), add `aria-labelledby` and `aria-describedby` to structurally link it to its visible heading and description, providing richer semantic context than a standalone `aria-label` or relying on generic containers.
