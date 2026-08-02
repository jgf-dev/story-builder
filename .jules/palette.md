## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.

## 2024-03-12 - Structurally link lists to visible headers
**Learning:** Structurally linking components like lists to their existing visible `<header>` tags (e.g., `<h2>` and `<p>`) using `aria-labelledby` and `aria-describedby` provides richer semantic context for screen reader users than a standalone `aria-label`.
**Action:** When enhancing accessibility for lists or structural regions, use `aria-labelledby` and `aria-describedby` to reference existing headers and description elements.

## 2024-10-27 - Enhance section regions with aria attributes
**Learning:** HTML5 `<section>` elements do not act as semantic `region` landmarks for screen reader navigation by default. Adding `aria-labelledby` and `aria-describedby` structurally links them to their existing visible `<header>` tags (`<h2>` and `<p>`), providing richer semantic context than a standalone `aria-label`.
**Action:** Upgrade `<section>` elements (and other complex structural regions) by using `aria-labelledby` and `aria-describedby` to link them to their visible headers, enabling them as properly described landmarks for screen reader users.

## 2026-07-30 - Dashboard Section Landmarks
**Learning:** HTML5 `<section>` elements do not inherently act as `region` landmarks for assistive technologies like screen readers unless they are provided an accessible name. Relying on default semantic behavior leaves these complex structural areas un-navigable.
**Action:** When using `<section>` tags to group major content areas, always provide an accessible name, preferably by using `aria-labelledby` (and optionally `aria-describedby`) to structurally link the section to its existing visible heading and description elements.
