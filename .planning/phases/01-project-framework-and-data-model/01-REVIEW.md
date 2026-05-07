---
phase: 01-project-framework-and-data-model
reviewed: 2026-05-07T00:00:00Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - pyproject.toml
  - src/secnotepad/model/__init__.py
  - src/secnotepad/model/serializer.py
  - src/secnotepad/model/snote_item.py
  - src/secnotepad/model/tree_model.py
  - src/secnotepad/model/validator.py
  - src/secnotepad/ui/__init__.py
  - src/secnotepad/ui/main_window.py
  - src/secnotepad/ui/welcome_widget.py
  - tests/conftest.py
  - tests/model/__init__.py
  - tests/model/test_serializer.py
  - tests/model/test_snote_item.py
  - tests/model/test_tree_model.py
  - tests/model/test_validator.py
  - tests/ui/__init__.py
  - tests/ui/test_main_window.py
findings:
  critical: 0
  warning: 7
  info: 9
  total: 16
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-07T00:00:00Z
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Reviewed the Phase 1 implementation of SecNotepad, covering the data model (SNoteItem, TreeModel, Serializer, Validator), UI shell (MainWindow, WelcomeWidget), and corresponding test suites. The overall code quality is good with clear separation of concerns and comprehensive test coverage (no TODOs or debug artifacts found in production code).

Key concerns center on:
1. **Serializer lacks input validation** -- bare dict key access on potentially malformed or malicious JSON causes unhandled `KeyError` crashes.
2. **TreeModel inconsistency** -- `remove_item()` uses value-based `list.index()` while every other comparison in the codebase uses reference equality (`is`), creating a latent bug if two items share field values.
3. **Type annotation errors** in `MainWindow` -- `None` assigned to non-optional fields.
4. **Resource leak** on repeated "New Notebook" calls -- old TreeModel instances are not cleaned up.
5. **Serializer version field is read but never validated** against the declared `FORMAT_VERSION`, making the field purely decorative.

## Warnings

### WR-01: Serializer `from_json` bare key access crashes on missing `data` field

**File:** `src/secnotepad/model/serializer.py:42`
**Issue:** `document["data"]` uses bare subscript access. If the parsed JSON is valid but lacks a `"data"` key (e.g., manual edit, corrupted file, or format version mismatch), a `KeyError` is raised with no context. The same pattern exists at lines 49-55 inside `_from_dict` where `d["id"]`, `d["title"]`, and `d["item_type"]` are accessed without `.get()` fallback.

**Fix:**
```python
data = document.get("data")
if data is None:
    raise ValueError("Missing required 'data' field in document")
```

And in `_from_dict`:
```python
return SNoteItem(
    id=d.get("id", ""),
    title=d.get("title", ""),
    item_type=d.get("item_type", "note"),
    ...
)
```

### WR-02: Serializer `from_json` crashes on malformed JSON input

**File:** `src/secnotepad/model/serializer.py:40`
**Issue:** `json.loads(json_str)` is called without a `try`/`except`. A malformed or corrupted JSON string raises `json.JSONDecodeError`, propagating an unhandled crash. Given this is a local file-storage application, corrupted data is a realistic scenario (incomplete writes, disk errors, manual tampering).

**Fix:**
```python
@staticmethod
def from_json(json_str: str) -> SNoteItem:
    try:
        document = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON document: {e}") from e
    ...
```

### WR-03: TreeModel `remove_item` uses value equality while rest of codebase uses reference equality

**File:** `src/secnotepad/model/tree_model.py:173`
**Issue:** `parent_item.children.index(item)` uses `list.index()` which employs Python's `__eq__` (value comparison). The entire rest of the file -- `_find_parent`, `_child_row`, and `parent()` -- consistently uses `is` (reference comparison). Dataclass auto-generated `__eq__` compares all fields, so two `SNoteItem` instances with identical values (e.g., two default `SNoteItem()` calls with `id=""`) would make `list.index()` find the first matching item by value rather than the exact one pointed to by the QModelIndex. This can cause silent removal of the wrong child node.

**Fix:** Replace with the existing `_child_row` static method which uses `is`:
```python
row = self._child_row(parent_item, item)
if row == -1:
    return False
```

### WR-04: MainWindow type annotations accept `None` for non-optional types

**File:** `src/secnotepad/ui/main_window.py:23-24`
**Issue:** `_root_item: SNoteItem = None` and `_tree_model: TreeModel = None` assign `None` to fields typed as non-optional (no `Optional[...]` wrapper). This produces type-checker warnings and defeats downstream type narrowing. The field is semantically optional (it's `None` until a notebook is created/opened).

**Fix:**
```python
from typing import Optional
...
self._root_item: Optional[SNoteItem] = None
self._tree_model: Optional[TreeModel] = None
```

### WR-05: Repeated `_on_new_notebook` leaks old TreeModel instances

**File:** `src/secnotepad/ui/main_window.py:177-179`
**Issue:** Each call to `_on_new_notebook` creates a new `TreeModel` and calls `setModel()`. The old `TreeModel` (also parented to `self`) is not deleted -- Qt's `setModel()` does not take ownership of the prior model. On repeated calls, orphaned `TreeModel` and `SNoteItem` tree objects accumulate until the MainWindow is destroyed. While not a large leak per call, the accumulation is unbounded.

**Fix:**
```python
def _on_new_notebook(self):
    # Clean up old model
    if self._tree_model is not None:
        self._tree_model.deleteLater()
    self._root_item = SNoteItem.new_section("根分区")
    self._tree_model = TreeModel(self._root_item, self)
    self._tree_view.setModel(self._tree_model)
    self._stack.setCurrentIndex(1)
    self.statusBar().showMessage("新建笔记本 - 未保存")
```

### WR-06: Serializer reads `version` field but never validates it

**File:** `src/secnotepad/model/serializer.py:41-42`
**Issue:** The comment on line 41 states `"version 字段保留，未来可用于格式升级检测"`, but the `version` field is only read and never checked against `FORMAT_VERSION`. If a future version changes the format (e.g., `version=2` with a different schema), `from_json` would silently attempt to parse it with the current schema, likely producing corrupted data or an opaque crash.

**Fix:** Add a version guard:
```python
version = document.get("version", 1)
if version != Serializer.FORMAT_VERSION:
    raise ValueError(f"Unsupported format version {version}, expected {Serializer.FORMAT_VERSION}")
```

### WR-07: Validator silently accepts invalid `item_type` values

**File:** `src/secnotepad/model/validator.py:41-48`
**Issue:** The `validate` method only checks `item_type == "note"` and assumes `item_type == "section"` in the `else` branch. Any unexpected `item_type` value (e.g., `"attachment"`, `"tag"`, or a typo like `"sectin"`) would pass validation silently, as `item_type` not being `"note"` causes the code to treat it as a section and recurse through `children`. This means erroneous item types are not caught.

**Fix:**
```python
valid_types = {"section", "note"}
if item.item_type not in valid_types:
    return ValidationError(f"Invalid item_type '{item.item_type}'; expected one of {valid_types}")
if item.item_type == "note" and item.children:
    return ValidationError(...)
if item.item_type == "section":
    for child in item.children:
        err = Validator.validate(child)
        if err:
            return err
```

## Info

### IN-01: Unused import `QVBoxLayout` in `main_window.py`

**File:** `src/secnotepad/ui/main_window.py:6`
**Issue:** `QVBoxLayout` is imported from `QWidgets` but never referenced in the file. This is a dead import.

**Fix:** Remove `QVBoxLayout` from the import line.

### IN-02: Dead code in test -- redundant assignment

**File:** `tests/model/test_serializer.py:149-151`
**Issue:** `item.tags` is assigned `["重要", "工作"]` on line 150, then immediately overwritten with `["工作", "紧急"]` on line 151. The first assignment has no effect.

**Fix:** Remove line 150 (`item.tags = ["重要", "工作"]`).

### IN-03: Test name/body mismatch -- "默认为 1" not asserted

**File:** `tests/model/test_serializer.py:157` (test: `test_from_json_missing_version`)
**Issue:** The test name asserts version defaults to 1 (`"缺少 version 字段时默认为 1"`), but the test body only checks `item.title`. No assertion on version behavior is performed. This is misleading for future maintainers.

**Fix:** Either add a version assertion or rename the test to match what it actually tests.

### IN-04: Weak assertions on minimum width checks

**File:** `tests/ui/test_main_window.py:137-144`
**Issue:** `assert widget.minimumWidth() <= 100` passes trivially (a minimumWidth of 0 or 50 would also pass). The intention is to verify the minimum width was set to 100px.

**Fix:** Change to `assert widget.minimumWidth() == 100` for both assertions.

### IN-05: Missing project metadata in `pyproject.toml`

**File:** `pyproject.toml:1-2`
**Issue:** The config only contains pytest options. No project metadata (name, version, dependencies, Python version requirement) is declared. This means `pip install -e .` would not work for local development, and there is no record of required dependencies.

**Fix:** Add `[project]` section with name, version, and dependencies (at minimum `PySide6`, `pytest`).

### IN-06: Validator returns exception instance instead of raising it -- unconventional API

**File:** `src/secnotepad/model/validator.py:31-50`
**Issue:** `validate()` returns `Optional[ValidationError]`, returning either `None` (pass) or a `ValidationError` instance (failure). Since `ValidationError` extends `Exception`, an instance is always truthy -- but callers must use `if result:` checks rather than the more natural `try/except` pattern. This is an unconventional and fragile contract. A future developer might reasonably wrap the call in `try:` and expect it to raise, which it won't.

**Fix (pick one):**
- Option A: Raise `ValidationError` instead of returning it, and change return type to `None`
- Option B: Keep the current pattern but remove `Exception` from the base class (use a plain dataclass or namedtuple for the error)

### IN-07: `_on_open_notebook` is a stub

**File:** `src/secnotepad/ui/main_window.py:183-185`
**Issue:** The open-notebook handler is a placeholder that only sets a status bar message. This is acceptable for Phase 1 scope, but the stub's minimal nature should be tracked for Phase 2 delivery.

**Fix:** No change needed now; flag for Phase 2 implementation.

### IN-08: `test_none_item` documents crash behavior rather than graceful handling

**File:** `tests/model/test_validator.py:131-133`
**Issue:** The test explicitly expects `AttributeError` when `validate(None)` is called. This codifies crash-on-None behavior instead of requiring the validator to check for `None` and return a clear `ValidationError`.

**Fix:** Add a `None` guard to `Validator.validate()` and update the test to expect `ValidationError` instead.

### IN-09: Test toolbar detection uses fragile parent-based lookup

**File:** `tests/ui/test_main_window.py:219-228`
**Issue:** `window.findChild(type(window._tb_new.parent()))` relies on the runtime class of `_tb_new.parent()`, which is `QToolBar`. The same lookup is used for the movable check. This is fragile -- any refactoring of toolbar setup could silently break the test without a clear error message.

**Fix:** Store a reference to the toolbar in MainWindow (e.g., `self._toolbar`) and test against it directly.

---

_Reviewed: 2026-05-07T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
