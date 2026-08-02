## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.

## 2024-03-12 - Structurally link lists to visible headers
**Learning:** Structurally linking components like lists to their existing visible `<header>` tags (e.g., `<h2>` and `<p>`) using `aria-labelledby` and `aria-describedby` provides richer semantic context for screen reader users than a standalone `aria-label`.
**Action:** When enhancing accessibility for lists or structural regions, use `aria-labelledby` and `aria-describedby` to reference existing headers and description elements.

## 2024-07-29 - Upgrade generic `<section>` elements to semantic `region` landmarks
**Learning:** HTML5 `<section>` elements do not inherently act as semantic `region` landmarks for screen reader navigation unless they are provided with an accessible name. Relying solely on `<section>` without ARIA attributes can leave complex interactive regions difficult to parse for users of assistive technologies.
**Action:** Always verify if complex structural areas like stats groups or form editors use `<section>`. If they do, structurally link them to their visible `<header>` tags (e.g., `<h2>` and `<p>`) using `aria-labelledby` and `aria-describedby` to upgrade them to accessible landmarks, providing much richer context than standalone ARIA labels.
