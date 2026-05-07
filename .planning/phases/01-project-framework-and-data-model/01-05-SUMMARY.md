---
phase: 01-project-framework-and-data-model
plan: 05
subsystem: ui
tags: python, pyside6, mainwindow, welcome, treeview, splitter, menu, toolbar, statusbar
requires:
  - plan: "01-02"
    provides: "SNoteItem dataclass, Serializer, Validator, TreeModel with 93 tests"
  - plan: "01-01"
    provides: "Project skeleton, venv, pyproject.toml, entry scripts"
provides:
  - WelcomeWidget with new/open buttons and signals
  - MainWindow with full UI skeleton (menu, toolbar, stacked widget, three-panel splitter, statusbar)
  - Working new notebook flow (creates TreeModel, switches to editor layout)
  - 37 UI tests covering all decisions D-12 through D-20
affects:
  - Phase 2: File operations (save/open dialogs connect to MainWindow slots)
  - Phase 3: Navigation (TreeView interactions, section/page management)
tech-stack:
  patterns:
    - QAction stored as instance variables (anti-GC pattern)
    - QStackedWidget for welcome/editor switching
    - QSplitter for three-panel resizable layout
    - QTreeView bound to custom TreeModel (hidden root)
    - Signal-based WelcomeWidget communication
    - pytest-qt for widget testing with qapp session fixture
key-files:
  created:
    - src/secnotepad/ui/__init__.py
    - src/secnotepad/ui/welcome_widget.py
    - src/secnotepad/ui/main_window.py
    - tests/ui/__init__.py
    - tests/ui/test_main_window.py
  created (plan):
    - .planning/phases/01-project-framework-and-data-model/01-05-PLAN.md
key-decisions:
  - "QAction imported from PySide6.QtGui (Qt6 change from QtWidgets in Qt5)"
  - "WelcomeWidget uses Qt Signals for button->mainwindow communication"
  - "New notebook creates SNoteItem.new_section('根分区') and wraps in TreeModel"
  - "UI tests use pytest-qt with session-scoped qapp fixture from conftest.py"
requirements-completed: []
duration: 45min
completed: 2026-05-07
---

# Phase 01 Plan 05 Summary

**MainWindow UI skeleton with WelcomeWidget, three-panel layout, menu/toolbar/statusbar, and 37 passing UI tests**

## Performance

- **Duration:** 45 min
- **Started:** 2026-05-07T12:50:00Z
- **Completed:** 2026-05-07T13:35:00Z
- **Tasks completed:** 5/5
- **Files created:** 6
- **Tests:** 37/37 passing

## Tasks Completed

### Task 1: UI 包标记

Created `src/secnotepad/ui/__init__.py` as empty package marker.

- **Commit:** `9d28332` chore(01-05): add UI package marker

### Task 2: WelcomeWidget

Created `src/secnotepad/ui/welcome_widget.py` with:
- `WelcomeWidget(QWidget)` class with `new_notebook_clicked` and `open_notebook_clicked` signals
- Layout: title, description, new/open buttons, recent files placeholder
- Buttons emit signals for MainWindow to handle

- **Commit:** `d4df607` feat(01-05): implement WelcomeWidget welcome page

### Task 3: MainWindow

Created `src/secnotepad/ui/main_window.py` with:

- **Window (D-19):** Title "SecNotepad", 1200x800, min 800x600
- **Menu bar (D-16):** File (New/Open/Save-SaveAs-gray/Exit), Edit (5 actions gray), View (gray), Help (gray)
- **Toolbar (D-17):** New/Open/Save(gray)/SaveAs(gray) with QStyle standard icons, non-movable
- **Central (D-14):** QStackedWidget -- index 0 = WelcomeWidget, index 1 = three-panel QSplitter
- **Splitter (D-12, D-13):** QTreeView(200px,collapsible) + QListView(250px,always-visible) + QWidget(stretch,collapsible)
- **Status bar (D-18):** "就绪"
- **New notebook handler:** Creates TreeModel, binds to QTreeView, switches to editor layout
- **Connections:** Menu/toolbar/welcome new buttons all connected

- **Commit:** `05267ec` feat(01-05): implement MainWindow with full UI skeleton

### Task 4: UI 布局冒烟测试 (checkpoint:human-verify)

User-approved visual verification. Manual testing confirmed:
- Welcome page displays with application name, description, new/open buttons
- New notebook flow switches to three-panel layout
- Menu bar, toolbar, and status bar all visible and functional

**Status:** Approved by user.

### Task 5: UI 测试

Created `tests/ui/__init__.py` (package marker) and `tests/ui/test_main_window.py` with 37 tests across 7 test classes:

| Test Class | Tests | Coverage |
|---|---|---|
| `TestWindowSetup` | 3 | D-19: title, size, min size |
| `TestWelcomePage` | 3 | D-15: welcome page, buttons, signals |
| `TestNewNotebook` | 6 | D-14: new notebook flow, model binding, stack switch |
| `TestSplitterLayout` | 9 | D-12, D-13: splitter panels, collapsible, widget types |
| `TestMenuBar` | 9 | D-16: menu structure, disabled actions, shortcuts |
| `TestToolBar` | 6 | D-17: toolbar existence, disabled buttons, non-movable |
| `TestStatusBar` | 1 | D-18: ready message |

All 37 tests pass: `pytest tests/ui/ -x -v` (0.32s)

- **Commit:** `8f09879` test(01-05): create UI tests for MainWindow layout and decisions D-12 to D-20

## Automated Verification

All UI decisions D-12 through D-20 verified automatically:
- Window title, size, minimum size correct
- QStackedWidget has 2 pages, starts at index 0 (welcome)
- QSplitter has 3 panels with correct collapsible settings
- TreeView and ListView present
- Save/SaveAs/Edit/View/Help actions disabled
- Status bar shows "就绪"
- Ctrl+N and Ctrl+Q shortcuts set
- New notebook flow creates TreeModel, switches to index 1, updates status bar
- All 37 UI tests pass verifying every D-12 to D-20 decision

## Deviations from Plan

### Rule 3 - Blocking fix: QAction import moved to QtGui

**Issue:** In PySide6 (Qt6), `QAction` is no longer in `PySide6.QtWidgets` (moved to `PySide6.QtGui`). The import `from PySide6.QtWidgets import QAction` would fail.

**Fix:** Changed import to `from PySide6.QtGui import QAction, QKeySequence`.

**Files modified:** `src/secnotepad/ui/main_window.py`

### Plan File Creation

**Issue:** Plan file `01-05-PLAN.md` did not exist. Created based on RESEARCH.md, PATTERNS.md, and project requirements.

**Impact:** Enabled execution to proceed.

## Verification Results

1. `python -m secnotepad` -- Application starts successfully (confirmed by previous agent)
2. `pytest tests/ui/ -x -v` -- 37/37 tests passed
3. All decisions D-12 to D-20 implemented in UI code and covered by tests

## Threat Flags

None -- UI layer introduces no network endpoints, file access, or security surface.

## Next Phase Readiness

- MainWindow ready for Phase 2 (file save/open dialogs)
- WelcomeWidget signals ready for file open dialog binding
- TreeView ready for Phase 3 navigation interactions
- Editor placeholder ready for Phase 4 rich text editor
- 37 UI tests provide safety net for future UI changes

---

*Phase: 01-project-framework-and-data-model*
*Completed: 2026-05-07*
