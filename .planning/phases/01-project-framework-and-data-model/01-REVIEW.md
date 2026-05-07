---
phase: 01-project-framework-and-data-model
reviewed: 2026-05-07T12:00:00Z
depth: standard
files_reviewed: 22
files_reviewed_list:
  - .gitignore
  - pyproject.toml
  - src/secnotepad/__init__.py
  - src/secnotepad/__main__.py
  - src/secnotepad/app.py
  - src/secnotepad/model/__init__.py
  - src/secnotepad/model/serializer.py
  - src/secnotepad/model/snote_item.py
  - src/secnotepad/model/tree_model.py
  - src/secnotepad/model/validator.py
  - src/secnotepad/ui/__init__.py
  - src/secnotepad/ui/main_window.py
  - src/secnotepad/ui/welcome_widget.py
  - tests/__init__.py
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
  warning: 5
  info: 8
  total: 13
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-07T12:00:00Z
**Depth:** standard
**Files Reviewed:** 22
**Status:** issues_found

## Summary

Reviewed 22 files in the SecNotebook Phase 1 implementation. The codebase is generally
well-structured with clean separation of concerns (SNoteItem dataclass, Serializer,
Validator, TreeModel, UI shell) and thorough test coverage. No critical security
vulnerabilities or data corruption bugs were found. Five warnings and eight info-level
items are reported.

Key concerns:
1. **TreeModel.add_item() does not enforce D-07 domain invariant** -- Notes can
   illegally gain children through the mutation API.
2. **No dirty-check guard in _on_new_notebook()** -- current work is silently discarded.
3. **Serializer.from_json() lacks input validation** -- crashes with opaque errors on
   malformed data.
4. **TreeModel.remove_item() uses value equality (list.index) instead of identity (is)**
   -- inconsistent with _child_row and _find_parent.
5. **Validator's unusual return-value pattern for an exception class.**

---

## Warnings

### WR-01: TreeModel.add_item() does not enforce D-07 invariant (Note is leaf)

**File:** `/home/jone/projects/secnotepad/src/secnotepad/model/tree_model.py:147-158`
**Issue:** `add_item()` unconditionally appends a child to the parent's children list
without checking the parent's `item_type`. Domain rule D-07 mandates that Notes must be
leaf nodes with empty children. A caller can invoke `add_item(note_index, some_child)`
and a Note will illegally gain children, silently corrupting the model invariant.
This API will be wired to UI actions in Phase 3, making this a latent bug.

**Fix:** Add a guard at the top of `add_item()`:

```python
def add_item(self, parent_index: QModelIndex, item: SNoteItem):
    parent_item = (parent_index.internalPointer()
                   if parent_index.isValid() else self._root_item)
    if parent_item.item_type == "note":
        raise ValueError("Cannot add children to a Note (leaf node)")
    row = len(parent_item.children)
    self.beginInsertRows(parent_index, row, row)
    parent_item.children.append(item)
    self.endInsertRows()
```

---

### WR-02: TreeModel.remove_item() uses value equality while rest of code uses identity

**File:** `/home/jone/projects/secnotepad/src/secnotepad/model/tree_model.py:173`
**Issue:** `parent_item.children.index(item)` uses `list.index()` which relies on
Python's `__eq__` (value comparison). The rest of the file -- `_find_parent` (line 126),
`_child_row` (line 141), and `parent()` (line 66) -- consistently uses `is` (reference
comparison). Because `SNoteItem` is a dataclass with auto-generated `__eq__`, two
distinct instances with identical field values would be considered equal by `list.index()`,
potentially returning the wrong item's index. In the worst case this causes silent
removal of the wrong child node.

**Fix:** Use the existing `_child_row` static method which performs `is` comparison:

```python
row = self._child_row(parent_item, item)
if row == -1:
    return False
```

---

### WR-03: _on_new_notebook() silently discards current work

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:175-181`
**Issue:** When `_on_new_notebook()` is called while a notebook is already open
(`_root_item` is not None), all in-memory state is silently discarded with no
confirmation dialog. Any unsaved changes are lost. A user pressing `Ctrl+N`
accidentally or clicking the toolbar button twice loses their work.

**Fix:** Add a guard before overwriting state:

```python
def _on_new_notebook(self):
    if self._root_item is not None:
        # Phase 3 TODO: check dirty flag and show confirmation dialog
        pass
    self._root_item = SNoteItem.new_section("根分区")
    ...
```

Additionally, clean up the old model to prevent resource accumulation (existing
WR-05 from prior review):

```python
    if self._tree_model is not None:
        self._tree_model.deleteLater()
```

---

### WR-04: Serializer.from_json() bare key access crashes on malformed input

**File:** `/home/jone/projects/secnotepad/src/secnotepad/model/serializer.py:42,49-51`
**Issue:** `document["data"]` at line 42 uses bare subscript access. If the parsed JSON
is valid but lacks `"data"` (e.g., corrupted file or format mismatch), a `KeyError` is
raised with no context. Inside `_from_dict`, `d["id"]`, `d["title"]`, and `d["item_type"]`
(lines 49-52) are also accessed without `.get()` fallback, crashing on missing required
fields. Additionally, `json.loads()` at line 40 has no `try`/`except` guard, so a
malformed JSON string raises `json.JSONDecodeError` with no context wrapping.

**Fix:** Add input validation with descriptive errors:

```python
@staticmethod
def from_json(json_str: str) -> SNoteItem:
    try:
        document = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
    if not isinstance(document, dict):
        raise ValueError("JSON root must be an object")
    if "data" not in document:
        raise ValueError("Missing required 'data' field")
    data = document["data"]
    for key in ("id", "title", "item_type"):
        if key not in data:
            raise ValueError(f"Missing required field '{key}' in SNoteItem data")
    return Serializer._from_dict(data)
```

---

### WR-05: Serializer stores version field but never validates it

**File:** `/home/jone/projects/secnotepad/src/secnotepad/model/serializer.py:41-42`
**Issue:** `to_json()` writes `"version": 1` into the JSON envelope, but `from_json()`
never reads or validates the version before deserializing. If a future format version
(>=2) is loaded, it will be silently parsed with the current schema, producing corrupted
data or opaque crashes. The test `test_from_json_missing_version` misleadingly claims
"默认为 1" but no default version behavior exists -- the field is simply ignored.

**Fix:** Add a version guard:

```python
document = json.loads(json_str)
version = document.get("version", 1)
if version > Serializer.FORMAT_VERSION:
    raise ValueError(f"Unsupported format version {version}; expected <= {Serializer.FORMAT_VERSION}")
```

---

## Info

### IN-01: MainWindow type hints accept None for non-optional types

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:23-24`
**Issue:** `self._root_item: SNoteItem = None` and `self._tree_model: TreeModel = None`
assign `None` to fields typed as non-optional. This triggers type checker warnings and
defeats downstream type narrowing.

**Fix:**
```python
from typing import Optional
self._root_item: Optional[SNoteItem] = None
self._tree_model: Optional[TreeModel] = None
```

---

### IN-02: Unnecessary `# noqa: F811` comment

**File:** `/home/jone/projects/secnotepad/src/secnotepad/__main__.py:12`
**Issue:** The `# noqa: F811` is placed on `from .ui.main_window import MainWindow`
inside `main()`. Since `MainWindow` has not been imported at module scope, no
redefinition (F811) can occur. The suppression comment is misleading.

**Fix:** Remove `# noqa: F811`.

---

### IN-03: Signal-to-signal connection with argument count mismatch in WelcomeWidget

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/welcome_widget.py:44,50`
**Issue:** `QPushButton.clicked` is `Signal(bool)` (emits check state), connected
directly to `self.new_notebook_clicked.emit` / `self.open_notebook_clicked.emit`,
both of which are `Signal()` (no arguments). PySide6 silently discards the extra
bool argument at runtime, but this pattern is fragile and diverges from standard
practice.

**Fix:**
```python
self._btn_new.clicked.connect(lambda: self.new_notebook_clicked.emit())
self._btn_open.clicked.connect(lambda: self.open_notebook_clicked.emit())
```

---

### IN-04: Duplicate sample_tree fixture in conftest.py and test_serializer.py

**File:** `/home/jone/projects/secnotepad/tests/conftest.py:26-44` and
`/home/jone/projects/secnotepad/tests/model/test_serializer.py:14-34`
**Issue:** The `sample_tree` fixture is defined identically in both files. The local
definition in `test_serializer.py` shadows the shared one from `conftest.py`, adding
duplication and maintenance burden.

**Fix:** Remove the redundant fixture from `test_serializer.py`.

---

### IN-05: Dead code -- redundant assignment in test

**File:** `/home/jone/projects/secnotepad/tests/model/test_serializer.py:150`
**Issue:** `item.tags = ["重要", "工作"]` on line 150 is immediately overwritten by
`item.tags = ["工作", "紧急"]` on line 151. The first assignment has no effect.

**Fix:** Remove line 150.

---

### IN-06: validator.py returns exception instance instead of raising it

**File:** `/home/jone/projects/secnotepad/src/secnotepad/model/validator.py:31-50`
**Issue:** `validate()` returns `Optional[ValidationError]` -- either `None` (pass)
or a `ValidationError` instance (failure). Since `ValidationError` inherits from
`Exception`, callers must use `if result is not None:` checks. This is an
unconventional contract; a future developer might reasonably wrap the call in
`try/except` and expect it to raise, which it won't. Additionally, the Validator
does not validate that `item_type` is one of the two allowed values (only checking
`"note"` vs non-`"note"`), so a typo like `"sectin"` would silently pass.

**Fix (pick one):**
- Option A: Raise `ValidationError` instead of returning it; change return type to `None`.
- Option B: Keep current pattern but use a simple result class (not inheriting from `Exception`).

```python
# Option A: raise on error
@staticmethod
def validate(item: SNoteItem) -> None:
    valid_types = {"section", "note"}
    if item.item_type not in valid_types:
        raise ValidationError(f"Invalid item_type '{item.item_type}'")
    if item.item_type == "note" and item.children:
        raise ValidationError(f"Note '{item.title}' cannot have children")
    if item.item_type == "section":
        for child in item.children:
            Validator.validate(child)
```

---

### IN-07: Weak assertions on minimum width in tests

**File:** `/home/jone/projects/secnotepad/tests/ui/test_main_window.py:137-144`
**Issue:** `assert widget.minimumWidth() <= 100` passes for any value <= 100 (including
0 or 50). The intent is to verify the minimum width was explicitly set to 100px.

**Fix:**
```python
assert widget.minimumWidth() == 100
```

---

### IN-08: Validator.test_none_item codifies crash-on-None

**File:** `/home/jone/projects/secnotepad/tests/model/test_validator.py:131-133`
**Issue:** The test explicitly expects `AttributeError` when `validate(None)` is called.
This codifies the crash behavior instead of requiring the Validator to check for `None`
and return a clear error.

**Fix:** Add a `None` guard to `Validator.validate()` and update the test:

```python
@staticmethod
def validate(item: SNoteItem) -> Optional[ValidationError]:
    if item is None:
        return ValidationError("Item cannot be None")
    ...
```

---

_Reviewed: 2026-05-07T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
