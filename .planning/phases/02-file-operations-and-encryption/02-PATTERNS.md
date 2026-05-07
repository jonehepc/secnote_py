# Phase 02: File Operations and Encryption - Pattern Map

**Mapped:** 2026-05-07
**Files analyzed:** 14 (7 new, 3 modify, 4 test)
**Analogs found:** 12 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/secnotepad/crypto/__init__.py` | config | N/A | `src/secnotepad/model/__init__.py` | exact |
| `src/secnotepad/crypto/header.py` | utility | transform | `src/secnotepad/model/validator.py` | role-match |
| `src/secnotepad/crypto/file_service.py` | service | CRUD (file I/O) | `src/secnotepad/model/serializer.py` | role-match |
| `src/secnotepad/ui/password_dialog.py` | component | request-response | `src/secnotepad/ui/welcome_widget.py` | role-match |
| `src/secnotepad/ui/password_generator.py` | component | request-response | `src/secnotepad/ui/welcome_widget.py` | role-match |
| `src/secnotepad/ui/main_window.py` | controller | request-response | (self — extend existing) | self |
| `src/secnotepad/ui/welcome_widget.py` | component | request-response | (self — extend existing) | self |
| `tests/crypto/__init__.py` | test-infra | N/A | `tests/model/__init__.py` | exact |
| `tests/crypto/test_header.py` | test | transform | `tests/model/test_validator.py` | role + data flow |
| `tests/crypto/test_file_service.py` | test | CRUD (file I/O) | `tests/model/test_serializer.py` | role + data flow |
| `tests/ui/test_password_dialog.py` | test | request-response | `tests/ui/test_main_window.py` | role + data flow |
| `tests/conftest.py` | test-infra | N/A | (self — extend existing) | self |

## Pattern Assignments

### `src/secnotepad/crypto/__init__.py` (config, N/A)

**Pattern:** Empty package init file, adding `crypto` module to namespace.

**Analog:** `src/secnotepad/model/__init__.py`

Contents (line 1):
```python
# empty file
```

---

### `src/secnotepad/crypto/header.py` (utility, transform)

**Analog:** `src/secnotepad/model/validator.py`

This file follows the same pattern as `Validator` — a stateless utility class with static methods, and a custom exception class for validation errors.

**Imports pattern** (from `validator.py` lines 1-15):
```python
from typing import Optional

from .snote_item import SNoteItem


class ValidationError(Exception):
    """SNoteItem 校验失败时抛出的异常。"""
    pass


class Validator:
    """SNoteItem 规则校验器。

    所有方法为静态方法，不维护状态。
    """
```

**Core pattern — static methods with assertions/guards** (from `validator.py` lines 30-50):
```python
@staticmethod
def validate(item: SNoteItem) -> Optional[ValidationError]:
    if item.item_type == "note" and item.children:
        return ValidationError(
            f"Note '{item.title}' cannot have children"
        )
    if item.item_type == "section":
        for child in item.children:
            err = Validator.validate(child)
            if err:
                return err
    return None
```

**Pattern to use for `header.py`:**
- Define `HeaderError(Exception)` for parsing failures (analogous to `ValidationError`)
- Class `Header` (or module-level functions) with `@staticmethod` methods `build_header(salt, iv, hmac_tag) -> bytes` and `parse_header(data) -> dict`
- Use `assert` guards for preconditions (matching `validator.py` style)
- Raise `HeaderError` for invalid magic bytes or version mismatch

---

### `src/secnotepad/crypto/file_service.py` (service, CRUD file I/O)

**Analog:** `src/secnotepad/model/serializer.py`

This file follows the same pattern as `Serializer` — a class with static methods serving as the orchestration layer between data and persistence.

**Imports pattern** (from `serializer.py` lines 1-12):
```python
"""Serializer - SNoteItem 树 ↔ JSON 双向转换工具 (D-06)。"""

import json
from dataclasses import asdict

from .snote_item import SNoteItem
```

**Core pattern — static methods with docstrings** (from `serializer.py` lines 15-36):
```python
class Serializer:
    """SNoteItem 树 ↔ JSON 字符串的双向转换。"""

    FORMAT_VERSION = 1

    @staticmethod
    def to_json(root: SNoteItem) -> str:
        """SNoteItem 树 → JSON 字符串。

        JSON 顶层格式 (D-08, D-11):
        { ... }
        """
        data = asdict(root)
        document = {
            "version": Serializer.FORMAT_VERSION,
            "data": data,
        }
        return json.dumps(document, ensure_ascii=False, indent=2)
```

**Error handling pattern — try/except with ValueError** (from `serializer.py` lines 37-62):
```python
    @staticmethod
    def from_json(json_str: str) -> SNoteItem:
        """JSON 字符串 → SNoteItem 树。

        Raises:
            ValueError: 如果 JSON 格式无效、缺少必填字段或版本不兼容。
        """
        try:
            document = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
        if not isinstance(document, dict):
            raise ValueError("JSON root must be an object")
        version = document.get("version", 1)
        if version > Serializer.FORMAT_VERSION:
            raise ValueError(
                f"Unsupported format version {version}; "
                f"expected <= {Serializer.FORMAT_VERSION}"
            )
        if "data" not in document:
            raise ValueError("Missing required 'data' field")
```

**Pattern to use for `file_service.py`:**
- Class `FileService` with `@staticmethod` methods: `encrypt`, `decrypt`, `save`, `open`
- Methods raise `ValueError` for invalid inputs (matching `serializer.py` style)
- Docstrings follow the same `Args:` / `Returns:` / `Raises:` format
- Internal helper methods prefixed with underscore (`_derive_keys`, `_build_header`)

---

### `src/secnotepad/ui/password_dialog.py` (component, request-response)

**Analog:** `src/secnotepad/ui/welcome_widget.py`

The `PasswordDialog` follows the same widget pattern as `WelcomeWidget` — a `QDialog` subclass (vs `QWidget`) with layout setup and signal declarations.

**Imports pattern** (from `welcome_widget.py` lines 1-5):
```python
"""欢迎页组件 (D-15)"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                                QPushButton)
```

**Signal declaration pattern** (from `welcome_widget.py` lines 15-16):
```python
class WelcomeWidget(QWidget):
    new_notebook_clicked = Signal()
    open_notebook_clicked = Signal()
```

**Layout setup pattern** (from `welcome_widget.py` lines 18-58):
```python
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        layout.addStretch()

        title_label = QLabel("SecNotepad")
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        # ... more layout setup ...

        layout.addStretch()
```

**Property accessor pattern** (from `welcome_widget.py` lines 60-68):
```python
    @property
    def new_button(self) -> QPushButton:
        """新建笔记本按钮"""
        return self._btn_new
```

**Pattern to use for `password_dialog.py`:**
- Add enum/mode class `PasswordMode(SET_PASSWORD, ENTER_PASSWORD, CHANGE_PASSWORD)` at module level
- Class `PasswordDialog(QDialog)` with mode parameter in `__init__`
- Use `QDialog.accept()` / `QDialog.reject()` for dialog result
- Provide `password()` getter that returns `bytearray` (D-39), with `clear_password()` method
- Use mode switching with `if self._mode == PasswordMode.ENTER_PASSWORD` pattern internally

**Qt standard icon pattern** (from `main_window.py` lines 103-108 — for eye toggle icon):
```python
style = self.style()
icon = style.standardIcon(QStyle.SP_FileIcon)
```

---

### `src/secnotepad/ui/password_generator.py` (component, request-response)

**Analog:** `src/secnotepad/ui/welcome_widget.py`

Same widget pattern as `WelcomeWidget`. Also draws from `main_window.py`'s layout and action pattern.

**Pattern to use for `password_generator.py`:**
- Class `PasswordGenerator(QDialog)` — sub-dialog
- `__init__` takes optional length and character set parameters with defaults
- Layout with spin box (length), checkboxes (character sets), generate button
- Return the generated password via `password()` getter
- Use `secrets` module for CSPRNG generation

---

### `src/secnotepad/ui/main_window.py` (modification, controller, request-response)

**Analog:** Self — extending existing pattern. Key existing patterns to preserve and extend.

**Existing action setup pattern** (from `main_window.py` lines 50-66):
```python
self._act_save = QAction("保存(&S)", self)
self._act_save.setShortcut(QKeySequence("Ctrl+S"))
self._act_save.setEnabled(False)           # D-16: 灰显
file_menu.addAction(self._act_save)
```

**Existing signal connection pattern** (from `main_window.py` lines 169-173):
```python
self._act_new.triggered.connect(self._on_new_notebook)
self._tb_new.triggered.connect(self._on_new_notebook)
self._act_open.triggered.connect(self._on_open_notebook)
self._tb_open.triggered.connect(self._on_open_notebook)
```

**Existing `_on_new_notebook` handler pattern** (from `main_window.py` lines 175-186):
```python
def _on_new_notebook(self):
    """新建空白笔记本 (D-14)"""
    if self._root_item is not None:
        # Phase 3 TODO: check dirty flag and show confirmation dialog
        pass
    if self._tree_model is not None:
        self._tree_model.deleteLater()
    self._root_item = SNoteItem.new_section("根分区")
    self._tree_model = TreeModel(self._root_item, self)
    self._tree_view.setModel(self._tree_model)
    self._stack.setCurrentIndex(1)               # 切换到三栏布局
    self.statusBar().showMessage("新建笔记本 - 未保存")
```

**Pattern to add:**
- `_is_dirty: bool = False` instance variable in `__init__`
- `mark_dirty()` / `mark_clean()` public methods (for Phase 3/4 consumers)
- `closeEvent(self, event: QCloseEvent)` override with dirty check dialog
- Replace `_on_open_notebook()` stub with full flow: QFileDialog -> PasswordDialog -> FileService.open -> Serializer.from_json
- Add `_on_save()`, `_on_save_as()` handlers
- Enable save/save-as actions after notebook loaded
- `QMessageBox` three-button pattern for unsaved changes

---

### `src/secnotepad/ui/welcome_widget.py` (modification, component, request-response)

**Analog:** Self — extending with recent files list widget.

**Existing placeholder to replace** (from `welcome_widget.py` line 56):
```python
# 最近文件列表占位区域（后续 Phase 实现）
layout.addWidget(QLabel("最近文件（功能待实现）"))
```

**Pattern to use:**
- Replace `QLabel` with `QListWidget`
- Emit new signal `recent_file_clicked(str)` when an item is clicked
- Add `set_recent_files(paths: list[str])` method to populate the list
- Style the list widget to fit the welcome page aesthetic

---

### `tests/crypto/__init__.py` (test-infra, N/A)

**Pattern:** Empty package init file.

**Analog:** `tests/model/__init__.py`

Contents:
```python
# empty file
```

---

### `tests/crypto/test_header.py` (test, transform)

**Analog:** `tests/model/test_validator.py`

Tests for a stateless utility class with static methods.

**Test class organization pattern** (from `test_validator.py` lines 1-148):
```python
"""Tests for Validator - SNoteItem 层级约束校验 (D-06, D-07)."""

import pytest

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.validator import ValidationError, Validator


class TestValidatorSection:
    """Section 节点校验."""

    def test_empty_section_valid(self):
        """空 section（无 children）校验通过."""
        section = SNoteItem.new_section("空分区")
        assert Validator.validate(section) is None
```

**Pattern to use for `test_header.py`:**
- Import from `src.secnotepad.crypto.header`
- Test classes: `TestHeaderBuild`, `TestHeaderParse`, `TestHeaderErrors`
- Test roundtrip: build -> parse -> verify fields match
- Test error cases: invalid magic, wrong length, version mismatch
- Use `pytest.raises` for error tests

---

### `tests/crypto/test_file_service.py` (test, CRUD file I/O)

**Analog:** `tests/model/test_serializer.py`

Integration tests for a roundtrip service with encryption/decryption.

**Test class organization pattern** (from `test_serializer.py` lines 37-109):
```python
class TestSerializerToJson:
    """Serializer.to_json() 测试."""

    def test_returns_string(self, sample_tree):
        """to_json() 返回字符串."""
        result = Serializer.to_json(sample_tree)
        assert isinstance(result, str)
```

**Roundtrip test pattern** (from `test_serializer.py` lines 133-145):
```python
def test_nested_tree_roundtrip(self, sample_tree):
    """Round-trip: tree → JSON → tree' 结构一致."""
    json_str = Serializer.to_json(sample_tree)
    restored = Serializer.from_json(json_str)

    assert restored.title == sample_tree.title
    assert restored.item_type == sample_tree.item_type
    assert len(restored.children) == len(sample_tree.children)
    assert restored.children[0].title == "工作"
```

**Pattern to use for `test_file_service.py`:**
- Conftest fixtures: `temp_dir`, `test_password`, `sample_json_str`
- `TestEncryptDecrypt` — roundtrip: `encrypt(plaintext)` -> `decrypt(ciphertext)` == `plaintext`
- `TestFileSaveOpen` — roundtrip: `save(path, data)` -> `open(path, password)` == data
- `TestWrongPassword` — HMAC rejection: save with password A, open with password B raises ValueError
- `TestSaveAs` — save same data to new path with new password
- Use `tmp_path` fixture from pytest for temp files

---

### `tests/ui/test_password_dialog.py` (test, request-response)

**Analog:** `tests/ui/test_main_window.py`

UI test for a Qt widget using `qapp` fixture.

**Fixture pattern** (from `test_main_window.py` lines 14-21):
```python
@pytest.fixture
def window(qapp):
    """创建 MainWindow 实例，测试结束后自动清理。"""
    w = MainWindow()
    w.show()
    yield w
    w.close()
    w.deleteLater()
```

**Test class organization pattern** (from `test_main_window.py` lines 26-42):
```python
class TestWindowSetup:
    """D-19: 窗口标题、大小"""

    def test_window_title(self, window):
        """窗口标题为 'SecNotepad'"""
        assert window.windowTitle() == "SecNotepad"
```

**Pattern to use for `test_password_dialog.py`:**
- Fixture `dialog(qapp)` creates `PasswordDialog(mode=SET_PASSWORD)`, yields, then deletes
- Test classes: `TestSetPasswordMode`, `TestEnterPasswordMode`, `TestChangePasswordMode`
- Test password field echo mode toggle
- Test confirm password mismatch disables accept
- Test password generator sub-dialog integration
- Test `password()` getter returns `bytearray`

---

### `tests/conftest.py` (modification, test-infra, N/A)

**Analog:** Self — extend existing fixture file.

**Existing fixture pattern** (from `conftest.py` lines 22-57):
```python
@pytest.fixture
def sample_tree() -> SNoteItem:
    """创建 3 层示例 SNoteItem 树。"""
    root = SNoteItem.new_section("根分区")
    # ...
    return root
```

**Pattern to add:**
- `tmp_path` is from pytest built-in, no fixture needed
- Add `test_password -> bytearray` fixture (returns `b"TestP@ss123"`)
- Add `sample_json_str -> str` fixture (a valid JSON string for encryption)
- Add `temp_dir -> Path` fixture using pytest's `tmp_path`

## Shared Patterns

### Error Handling
**Source:** `src/secnotepad/model/serializer.py` lines 37-62
**Apply to:** `crypto/file_service.py`, `crypto/header.py`

```python
# try/except wrapping external library calls, re-raising as ValueError
try:
    document = json.loads(json_str)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON: {e}") from e

# Guard checks with descriptive messages
if not isinstance(document, dict):
    raise ValueError("JSON root must be an object")
```

### Static Method Service Pattern
**Source:** `src/secnotepad/model/serializer.py` lines 15-36, `src/secnotepad/model/validator.py` lines 24-50
**Apply to:** `crypto/file_service.py`, `crypto/header.py`

```python
class ServiceName:
    """Stateless utility class with static methods."""

    CONSTANT = 1

    @staticmethod
    def method_name(input: Type) -> ReturnType:
        """Description.

        Args:
            input: parameter description

        Returns:
            Return value description

        Raises:
            ValueError: When input is invalid
        """
        # implementation
```

### Qt Widget/Component Pattern
**Source:** `src/secnotepad/ui/welcome_widget.py` lines 1-68
**Apply to:** `ui/password_dialog.py`, `ui/password_generator.py`

```python
class WidgetName(QDialog):
    """Description."""

    signal_name = Signal(str)  # signal declarations

    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. Set up instance state
        # 2. Create layout
        # 3. Add widgets to layout
        # 4. Connect signals

    @property
    def accessor(self) -> ReturnType:
        """Public property accessor."""
        return self._private_attr
```

### Test Class Organization Pattern
**Source:** `tests/model/test_serializer.py`, `tests/model/test_validator.py`, `tests/ui/test_main_window.py`
**Apply to:** All new test files

```python
class TestFeatureCategory:
    """Category description."""

    def test_specific_behavior(self):
        """Test name describes expected behavior."""
        # Arrange
        # Act
        # Assert
```

### Path Import Convention
**Source:** All existing files use relative imports within `src/secnotepad/`, and absolute imports from `src.secnotepad.*` in tests.

```python
# Inside src/secnotepad/ — relative imports
from ..model.snote_item import SNoteItem
from .snote_item import SNoteItem

# In tests/ — absolute imports from package root
from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.crypto.file_service import FileService
```

### Bytearray Secure Cleanup Pattern (for PasswordDialog)
**Source:** RESEARCH.md Traps section (not in existing codebase — new pattern)
**Apply to:** `ui/password_dialog.py`

```python
# Store password as bytearray for explicit zeroing
self._password = bytearray()

def password(self) -> bytearray:
    """Return copy of password bytes."""
    return bytearray(self._password)

def clear_password(self):
    """Explicitly zero out password in memory (D-27)."""
    self._password[:] = b'\x00' * len(self._password)
```

### QSettings Recent Files Pattern
**Source:** RESEARCH.md code examples (new pattern for the project)
**Apply to:** `ui/welcome_widget.py` (or a shared utility), consumed by `main_window.py`

```python
from PySide6.QtCore import QSettings
import os

MAX_RECENT_FILES = 5
SETTINGS_KEY = "recent_files"

def load_recent_files() -> list[str]:
    settings = QSettings()
    paths = settings.value(SETTINGS_KEY, [])
    if paths is None:
        return []
    valid = [p for p in paths if os.path.isfile(p)]
    if len(valid) < len(paths):
        settings.setValue(SETTINGS_KEY, valid)
    return valid

def add_recent_file(path: str):
    settings = QSettings()
    paths = settings.value(SETTINGS_KEY, []) or []
    if path in paths:
        paths.remove(path)
    paths.insert(0, path)
    paths = paths[:MAX_RECENT_FILES]
    settings.setValue(SETTINGS_KEY, paths)
```

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns and the shared patterns above):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/ui/test_password_dialog.py` | test | request-response | Good analog exists (`test_main_window.py`), but needs `pytest-qt` patterns not yet used in project |

Shared patterns above (QSettings, bytearray cleanup, QLineEdit echo toggle) are entirely new to this codebase and have no existing analogs. Use the RESEARCH.md code examples as primary references for these.

## Metadata

**Analog search scope:** `src/secnotepad/` (all .py files), `tests/` (all .py files)
**Files scanned:** 14 existing source files
**Pattern extraction date:** 2026-05-07
