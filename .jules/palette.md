## 2024-03-04 - Prefer native list elements
**Learning:** Native `<ul>` and `<li>` elements provide list semantics without redundant ARIA roles, and their default bullets, margin, and padding can be reset with CSS when the visual design requires it.
**Action:** Use native list elements for lists and adjust their presentation with CSS instead of applying list or group roles to generic containers.

## 2024-03-05 - Complex region landmarks need explicit names
**Learning:** HTML5 `<section>` elements do not automatically act as semantic `region` landmarks for screen readers. In complex layouts (like cards or dashboards), they should be explicitly defined by linking them to their visible headers using `aria-labelledby` and `aria-describedby` to provide rich structural context.
**Action:** Always upgrade `<section>` and complex structural containers into properly labeled region landmarks by referencing existing visible headers (`<h2>`, `<p>`) using ARIA attributes instead of relying on standalone `aria-label`s.
