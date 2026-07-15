## 2024-03-04 - Use ARIA roles for lists when CSS cannot be changed
**Learning:** Using <div role="list"> and <div role="listitem"> allows exposing list semantics to screen readers without introducing the default user-agent styling (bullets, padding) associated with native <ul> and <li> tags, which is useful when CSS modifications are restricted.
**Action:** Apply list roles to non-semantic container elements when they represent a list of items and CSS changes are out of scope.
