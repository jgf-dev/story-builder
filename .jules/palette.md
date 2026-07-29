## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.
## 2024-10-27 - Enhance section regions with aria attributes
**Learning:** HTML5 `<section>` elements do not act as semantic `region` landmarks for screen reader navigation by default. Adding `aria-labelledby` and `aria-describedby` structurally links them to their existing visible `<header>` tags (`<h2>` and `<p>`), providing richer semantic context than a standalone `aria-label`.
**Action:** Upgrade `<section>` elements (and other complex structural regions) by using `aria-labelledby` and `aria-describedby` to link them to their visible headers, enabling them as properly described landmarks for screen reader users.
