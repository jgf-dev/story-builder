## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.

## 2024-03-04 - Section elements require accessible names to become region landmarks
**Learning:** By default, HTML5 `<section>` elements do not act as semantic `region` landmarks for screen reader navigation unless they have an accessible name.
**Action:** Use `aria-labelledby` linking to a visible heading within the section to upgrade it into a useful navigational region for assistive technology.
