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
  - All D-12 through D-20 decisions implemented and verified
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
key-files:
  created:
    - src/secnotepad/ui/__init__.py
    - src/secnotepad/ui/welcome_widget.py
    - src/secnotepad/ui/main_window.py
  created (plan):
    - .planning/phases/01-project-framework-and-data-model/01-05-PLAN.md
key-decisions:
  - "QAction imported from PySide6.QtGui (Qt6 change from QtWidgets in Qt5)"
  - "WelcomeWidget uses Qt Signals for button->mainwindow communication"
  - "New notebook creates SNoteItem.new_section('根分区') and wraps in TreeModel"
requirements-completed: []
duration: 25min
completed: 2026-05-07
---

# Phase 01 Plan 05 Summary

**MainWindow UI skeleton with WelcomeWidget, three-panel layout, menu/toolbar/statusbar -- checkpoint at Task 4**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-07T12:50:00Z
- **Completed:** 2026-05-07T13:15:00Z (checkpoint reached)
- **Tasks completed:** 3/5 (stopped at checkpoint: task 4)
- **Files created:** 5

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

### Automated Verification

All UI decisions D-12 through D-20 verified automatically:
- Window title, size, minimum size correct
- QStackedWidget has 2 pages, starts at index 0 (welcome)
- QSplitter has 3 panels with correct collapsible settings
- TreeView and ListView present
- Save/SaveAs/Edit/View/Help actions disabled
- Status bar shows "就绪"
- Ctrl+N and Ctrl+Q shortcuts set
- New notebook flow creates TreeModel, switches to index 1, updates status bar

## Deviations from Plan

### Rule 3 - Blocking fix: QAction import moved to QtGui

**Issue:** In PySide6 (Qt6), `QAction` is no longer in `PySide6.QtWidgets` (moved to `PySide6.QtGui`). The import `from PySide6.QtWidgets import QAction` would fail.

**Fix:** Changed import to `from PySide6.QtGui import QAction, QKeySequence`.

**Files modified:** `src/secnotepad/ui/main_window.py`

### Plan File Creation

**Issue:** Plan file `01-05-PLAN.md` did not exist. Created based on RESEARCH.md, PATTERNS.md, and project requirements.

**Impact:** Enabled execution to proceed.

## Checkpoint Reached

**Type:** human-verify
**Task 4:** UI layout smoke test

### What was built

- **WelcomeWidget** with application name, description, new/open buttons, recent files placeholder
- **MainWindow** with full menu bar (4 menus), toolbar (4 actions), stacked widget (2 pages), three-panel splitter layout, and status bar
- **New notebook flow** -- creates root section, TreeModel, binds to QTreeView, switches to editor layout

### Verification steps (for user)

1. Run `cd /home/jone/projects/secnotepad && source venv/bin/activate && python -m secnotepad`
2. Confirm welcome page appears with application name "SecNotepad" and "安全的本地加密笔记本"
3. Click "新建笔记本" button or use Ctrl+N
4. Confirm three-panel layout appears (left tree, middle list, right empty area)
5. Verify menu bar: 文件, 编辑, 视图, 帮助
6. Verify toolbar icons are visible
7. Check status bar shows appropriate messages

### All automated checks passed

No visual issues expected, but visual confirmation ensures correct layout proportions and appearance.

## Task 5 (deferred after checkpoint)

- Create `tests/ui/__init__.py`
- Create `tests/ui/test_main_window.py` with 10+ tests

## Threat Flags

None -- UI layer introduces no network endpoints, file access, or security surface.

## Next Phase Readiness

- MainWindow ready for Phase 2 (file save/open dialogs)
- WelcomeWidget signals ready for file open dialog binding
- TreeView ready for Phase 3 navigation interactions
- Editor placeholder ready for Phase 4 rich text editor

---

*Phase: 01-project-framework-and-data-model*
*Completed: 2026-05-07 (checkpoint at Task 4)*
