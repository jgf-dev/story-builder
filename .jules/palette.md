## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.

## 2024-07-28 - HTML5 Section Landmarks
**Learning:** HTML5 `<section>` elements do not act as semantic `region` landmarks for screen reader navigation by default.
**Action:** Upgrade `<section>` elements by using `aria-labelledby` and `aria-describedby` to structurally link them to their existing visible `<header>` tags (e.g., `<h2>` and `<p>`), providing richer semantic context.
