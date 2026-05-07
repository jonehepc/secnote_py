---
phase: 01-project-framework-and-data-model
fixed_at: 2026-05-07T12:00:00Z
review_path: .planning/phases/01-project-framework-and-data-model/01-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-05-07
**Source review:** `.planning/phases/01-project-framework-and-data-model/01-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (all Warnings)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: TreeModel.add_item() does not enforce D-07 invariant (Note is leaf)

**Files modified:** `src/secnotepad/model/tree_model.py`
**Commit:** `1a9ea6d`
**Applied fix:** Added guard in `add_item()` that raises `ValueError` when caller attempts to add children to a Note-type parent item. This enforces domain rule D-07 that Notes must be leaf nodes with empty children.

### WR-02: TreeModel.remove_item() uses value equality while rest of code uses identity

**Files modified:** `src/secnotepad/model/tree_model.py`
**Commit:** `b7d897e`
**Applied fix:** Replaced `parent_item.children.index(item)` (value equality via `__eq__`) with `self._child_row(parent_item, item)` (identity comparison via `is`), consistent with the rest of the file. Returns `False` when `_child_row` returns -1.

### WR-03: _on_new_notebook() silently discards current work

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** `b91ac70`
**Applied fix:** Added guard checking `self._root_item is not None` before overwriting state, with Phase 3 TODO comment for dirty-flag confirmation dialog. Added `self._tree_model.deleteLater()` cleanup when an old model exists.

### WR-04: Serializer.from_json() bare key access crashes on malformed input

**Files modified:** `src/secnotepad/model/serializer.py`
**Commit:** `9f39e05`
**Applied fix:** Wrapped `json.loads()` in try/except with descriptive ValueError. Added type check (must be dict), required "data" field check, and required key checks ("id", "title", "item_type") in the data payload. All failures raise ValueError with context.

### WR-05: Serializer stores version field but never validates it

**Files modified:** `src/secnotepad/model/serializer.py`
**Commit:** `9abd031`
**Applied fix:** Added version validation in `from_json()`: reads `version` from envelope (default 1), raises ValueError if version exceeds `Serializer.FORMAT_VERSION`. Prevents silent deserialization of future format versions.

---

_Fixed: 2026-05-07_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
