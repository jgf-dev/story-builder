## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.

## 2024-03-12 - Structurally link lists to visible headers
**Learning:** Structurally linking components like lists to their existing visible `<header>` tags (e.g., `<h2>` and `<p>`) using `aria-labelledby` and `aria-describedby` provides richer semantic context for screen reader users than a standalone `aria-label`.
**Action:** When enhancing accessibility for lists or structural regions, use `aria-labelledby` and `aria-describedby` to reference existing headers and description elements.

## 2024-05-18 - Card Component Region Landmarks
**Learning:** In this application's design system, `<section class="card">` elements lack implicit ARIA region landmark roles for screen readers.
**Action:** Always upgrade `.card` sections by binding them to their internal `<header class="hd">` elements using `aria-labelledby` (pointing to the `<h2>`) and `aria-describedby` (pointing to the `<p class="sub">`) to provide rich, structural semantic context.
