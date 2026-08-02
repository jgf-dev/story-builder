## 2026-07-30 - Dashboard Section Landmarks
**Learning:** HTML5 `<section>` elements do not inherently act as `region` landmarks for assistive technologies like screen readers unless they are provided an accessible name. Relying on default semantic behavior leaves these complex structural areas un-navigable.
**Action:** When using `<section>` tags to group major content areas, always provide an accessible name, preferably by using `aria-labelledby` (and optionally `aria-describedby`) to structurally link the section to its existing visible heading and description elements.
