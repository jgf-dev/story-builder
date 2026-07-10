Ran terminal command:  cd /home/jgf2/git/voice/story-builder && uv run python 
User: The code for pages is much too messy and needs to be divided up into logical chunks. Can you come up with a plan for how to divide the code into logical chunks?

---

GitHub Copilot: I'll analyze the dashboard.py file to understand its current structure and propose a logical refactoring plan.


Read [](file:///home/jgf2/git/voice/story-builder/scripts/dashboard.py#466-466), lines 466 to 875

Read [](file:///home/jgf2/git/voice/story-builder/scripts/dashboard.py#1-1), lines 1 to 465

Compacted conversationNow I have a complete picture of the dashboard.py file. Let me create a comprehensive refactoring plan.


Created 2 todos

Based on my thorough analysis of the 875-line dashboard.py, here's my comprehensive refactoring plan:

---

## 📋 Refactoring Plan: dashboard.py Modularization

### Current State Analysis
- **875 lines** in a single file
- **6 major sections**: Imports/CSS/DB (1-465), Sidebar (466-510), 4 Pages (513-875)
- **Mixed concerns**: DB logic, UI rendering, business logic, CSS all intertwined
- **No separation** between data layer, presentation layer, and page components

---

### Target Architecture

```
dashboard/
├── __init__.py
├── main.py                    # Entry point, page routing
├── config.py                  # Constants, CSS, DB paths
├── data/
│   ├── __init__.py
│   ├── connections.py         # DB connection management
│   ├── queries.py             # Search, stats, favorites queries
│   └── models.py              # Dataclasses (StorySearchQuery, Story, Favorite)
├── ui/
│   ├── __init__.py
│   ├── components.py          # Reusable UI components (cards, filters, etc.)
│   ├── sidebar.py             # Sidebar navigation & global filters
│   └── styles.py              # CSS injection
└── pages/
    ├── __init__.py
    ├── search_explorer.py     # Page 1: Search & Explorer
    ├── read_story.py          # Page 2: Read Story
    ├── favorites_tags.py      # Page 3: Favorites & Tags
    └── archive_stats.py       # Page 4: Archive Stats
```

---

### Detailed Migration Plan

| Phase                | Files to Create                                                                                        | Lines Moved | Description                                                                |
| -------------------- | ------------------------------------------------------------------------------------------------------ | ----------- | -------------------------------------------------------------------------- |
| **1. Foundation**    | `config.py`, `data/connections.py`, `data/models.py`                                                   | ~150        | Constants, DB paths, CSS, connection pooling, dataclasses                  |
| **2. Data Layer**    | `data/queries.py`                                                                                      | ~200        | All SQL queries, search logic, stats aggregation, favorites CRUD           |
| **3. UI Components** | `ui/styles.py`, `ui/components.py`, `ui/sidebar.py`                                                    | ~100        | CSS injection, reusable components (story cards, filters, badges), sidebar |
| **4. Pages**         | `pages/search_explorer.py`, `pages/read_story.py`, `pages/favorites_tags.py`, `pages/archive_stats.py` | ~350        | Each page as independent module with `render()` function                   |
| **5. Entry Point**   | main.py                                                                                                | ~20         | Streamlit page config, routing, page dispatch                              |
| **6. Cleanup**       | Delete old dashboard.py                                                                                | -           | Remove monolith after verification                                         |

---

### Key Design Decisions

1. **Data Layer Separation**: All SQL moves to `data/queries.py` with typed functions returning dataclasses
2. **Page Components**: Each page exports a single `render()` function taking shared dependencies
3. **Shared State**: Use `st.session_state` for cross-page state (search params, selected story)
4. **Dependency Injection**: Pages receive DB connections via parameters, not globals
5. **CSS Extraction**: Move 150-line CSS string to `ui/styles.py` with `inject_css()` function
6. **Reusable Components**: Extract story cards, filter panels, stat cards to `ui/components.py`

---

### Migration Order (Dependency-Aware)

```
config.py → data/models.py → data/connections.py → data/queries.py 
    → ui/styles.py → ui/components.py → ui/sidebar.py
    → pages/*.py (4 files, independent)
    → main.py
```

---

### Benefits After Refactor

| Metric        | Before           | After                              |
| ------------- | ---------------- | ---------------------------------- |
| Max file size | 875 lines        | ~200 lines                         |
| Testability   | Hard (monolith)  | Easy (unit test each module)       |
| Reusability   | None             | High (components, queries)         |
| Navigation    | Scroll 875 lines | Jump to `pages/search_explorer.py` |
| Parallel work | Blocked          | Multiple devs on different pages   |

---

### Risk Mitigation

- **Incremental**: Create new structure alongside old file, verify page-by-page
- **Backwards compatible**: Old dashboard.py stays until all pages work
- **Streamlit caching**: Preserve `@st.cache_data` decorators on query functions
- **Session state**: Migrate keys explicitly, document in `config.py`

---

Would you like me to proceed with this refactoring? I'll start with Phase 1 (Foundation) and work through each phase, verifying each page works before moving to the next.
