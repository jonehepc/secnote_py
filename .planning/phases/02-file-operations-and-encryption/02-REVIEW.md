---
phase: 02-file-operations-and-encryption
reviewed: 2026-05-07T14:00:00Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - src/secnotepad/crypto/__init__.py
  - src/secnotepad/crypto/file_service.py
  - src/secnotepad/crypto/header.py
  - src/secnotepad/ui/main_window.py
  - src/secnotepad/ui/password_dialog.py
  - src/secnotepad/ui/password_generator.py
  - src/secnotepad/ui/welcome_widget.py
  - tests/conftest.py
  - tests/crypto/__init__.py
  - tests/crypto/test_file_service.py
  - tests/crypto/test_header.py
  - tests/ui/test_main_window.py
  - tests/ui/test_password_dialog.py
findings:
  critical: 1
  warning: 6
  info: 2
  total: 9
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-07T14:00:00Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed 13 files covering the crypto layer (file_service, header), UI layer (main_window, password_dialog, password_generator, welcome_widget), and their tests. The overall architecture is sound: MAC-then-Encrypt with PBKDF2 key derivation, constant-time HMAC comparison, and `bytearray`-based password clearing. However, there is one critical data-loss bug in the new-notebook flow, several input-validation gaps, and weak test assertions that pass trivially without testing their stated intent.

## Critical Issues

### CR-01: New notebook without dirty-check confirmation silently discards unsaved data

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:261-268`
**Issue:** `_on_new_notebook()` has a placeholder block (lines 263-265) that checks `if self._root_item is not None` but only executes `pass`, then unconditionally overwrites `self._root_item` on line 268. If the user has an open notebook with unsaved changes and clicks "New", the existing `_root_item` reference is dropped and all unsaved data is silently discarded. The promise of "Phase 3 TODO" is not acceptable — this is an active data-loss path in current code.

```python
def _on_new_notebook(self):
    """新建空白笔记本 (D-14)"""
    if self._root_item is not None:
        # Phase 3 TODO: check dirty flag and show confirmation dialog
        pass          # <--- does nothing, data silently lost
    if self._tree_model is not None:
        self._tree_model.deleteLater()
    self._root_item = SNoteItem.new_section("根分区")  # <--- overwrites
```

**Fix:** Implement the dirty-check + confirmation dialog before overwriting, reusing the same pattern as `closeEvent()`:

```python
def _on_new_notebook(self):
    if self._root_item is not None and self._is_dirty:
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("未保存的更改")
        msg_box.setText("当前笔记本有未保存的更改。是否在创建新笔记本前保存？")
        msg_box.setIcon(QMessageBox.Question)
        btn_save = msg_box.addButton("保存", QMessageBox.AcceptRole)
        btn_discard = msg_box.addButton("不保存", QMessageBox.DestructiveRole)
        btn_cancel = msg_box.addButton("取消", QMessageBox.RejectRole)
        msg_box.setDefaultButton(btn_save)
        msg_box.exec()
        clicked = msg_box.clickedButton()
        if clicked == btn_save:
            self._on_save()
            if self._is_dirty:
                return  # save cancelled
        elif clicked == btn_cancel:
            return
    if self._tree_model is not None:
        self._tree_model.deleteLater()
    self._root_item = SNoteItem.new_section("根分区")
    ...
```

## Warnings

### WR-01: `assert` in Header.build() removed under Python -O, bypassing length validation

**File:** `/home/jone/projects/secnotepad/src/secnotepad/crypto/header.py:34-36`
**Issue:** `assert` statements are stripped when Python runs with `-O` (optimized flag). While the current callers (`FileService.encrypt`) always pass correct-length parameters, this defense-in-depth validation vanishes in optimized builds. Any future refactoring that produces wrong-length salt, IV, or HMAC tag would silently pass through to `struct.pack`, which would either throw a confusing `struct.error` or, if the format string happens to accept it, produce a corrupt file header.

```python
assert len(salt) == 16, "salt must be 16 bytes"
assert len(iv) == 16, "IV must be 16 bytes"
assert len(hmac_tag) == 32, "HMAC tag must be 32 bytes"
```

**Fix:** Replace `assert` with explicit guards that raise `ValueError`:

```python
if len(salt) != 16:
    raise ValueError(f"salt must be 16 bytes, got {len(salt)}")
if len(iv) != 16:
    raise ValueError(f"IV must be 16 bytes, got {len(iv)}")
if len(hmac_tag) != 32:
    raise ValueError(f"HMAC tag must be 32 bytes, got {len(hmac_tag)}")
```

### WR-02: `except ValueError` conflates format errors with password errors in main_window password loops

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:307-310` (and duplicated at line 476-478)
**Issue:** Both `_on_open_notebook()` and `_on_open_recent()` catch all `ValueError` from `FileService.open()` and display "密码错误，请重试". But `FileService.open()` raises `ValueError` for two different failure modes: (1) invalid file format (header parsing failure), and (2) wrong password / tampered data (HMAC mismatch). Format errors are misrepresented to the user as password errors. Additionally, `FileNotFoundError` is not caught at all — if the file is deleted between the dialog opening and the actual read, an unhandled exception propagates.

```python
try:
    json_str = FileService.open(path, password)
except ValueError:
    dialog.set_error_message("密码错误，请重试")
    continue
```

**Fix:** Differentiate error types at the `FileService` layer, or at least catch `FileNotFoundError` with a separate message:

```python
try:
    json_str = FileService.open(path, password)
except FileNotFoundError:
    dialog.set_error_message("文件不存在或已被移动")
    continue
except ValueError as e:
    msg = str(e)
    if "无效的文件格式" in msg or "数据过短" in msg:
        dialog.set_error_message("文件格式无效或已损坏")
    else:
        dialog.set_error_message("密码错误，请重试")
    continue
```

### WR-03: PasswordDialog allows non-ASCII input that crashes on `encode('ascii')` during confirm

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/password_dialog.py:289-296`
**Issue:** `_on_confirm()` calls `pwd_text.encode('ascii')` without any validation. If a user types non-ASCII characters (e.g., CJK characters, emoji) into the password field, this raises `UnicodeEncodeError`. In PySide6, this exception is silently printed to stderr, `accept()` is never reached, the dialog stays open, and the user sees no feedback — the confirm button appears to do nothing. The same failure path exists in `password()` at line 177 (`str(self._password, encoding='ascii')`).

The ASCII-only constraint is documented (D-29) but the UI does not enforce it before encoding.

```python
def _on_confirm(self):
    pwd_text = self._pwd_input.text()
    if self._mode == PasswordMode.CHANGE_PASSWORD:
        if self._cb_change and self._cb_change.isChecked():
            self._password = bytearray(pwd_text.encode('ascii'))  # crash here
        else:
            self._password = bytearray()
    else:
        self._password = bytearray(pwd_text.encode('ascii'))  # crash here
    self.accept()
```

**Fix:** Validate ASCII before encoding and show an inline error message:

```python
def _on_confirm(self):
    pwd_text = self._pwd_input.text()
    if pwd_text and not pwd_text.isascii():
        self._mismatch_warning.setText("密码仅支持 ASCII 字符")
        self._mismatch_warning.setVisible(True)
        return
    # ... proceed with encoding ...
```

### WR-04: `FileService.decrypt()` lacks ASCII validation that `encrypt()` has

**File:** `/home/jone/projects/secnotepad/src/secnotepad/crypto/file_service.py:133-139`
**Issue:** `encrypt()` (line 96) validates `password.isascii()` and raises a clear `ValueError`. `decrypt()` only checks `if not password` but does NOT check `isascii()`. If `decrypt()` is called with a non-ASCII password (e.g., through a future API path that bypasses the dialog), it silently raises `UnicodeEncodeError` from `password.encode('ascii')` on line 50 rather than a meaningful error. This is an asymmetry that invites future bugs when new callers assume both methods validate the same way.

```python
# encrypt() has this guard:
if not password.isascii():
    raise ValueError("密码仅支持 ASCII 字符 (D-29)")

# decrypt() does NOT:
if not password:
    raise ValueError("密码不能为空")
# ... missing isascii() check
```

**Fix:** Add the same `isascii()` guard to `decrypt()`:

```python
if not password:
    raise ValueError("密码不能为空")
if not password.isascii():
    raise ValueError("密码仅支持 ASCII 字符 (D-29)")
```

### WR-05: `QSettings.value()` single-string degradation on single-entry lists

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:411-417, 427-438, 447-454`
**Issue:** `QSettings.value()` can return a single `str` instead of `list[str]` when the stored list contains exactly one entry and the settings backend (e.g., INI format) degrades single-element lists to scalars. If this happens, the list comprehension `[p for p in paths if isinstance(p, str) and os.path.isfile(p)]` iterates over individual characters of the path string. The `isinstance(p, str)` check would pass for each character, but `os.path.isfile(p)` would return `False` for single characters, so the list would become empty — effectively losing the recent files list. This degrades silently and confuses users.

This affects `_load_recent_files()`, `_add_recent_file()`, and `_remove_recent_file()`.

**Fix:** Guard against string degradation at the start of each method:

```python
def _load_recent_files(self) -> list[str]:
    from PySide6.QtCore import QSettings
    settings = QSettings()
    paths = settings.value(self.SETTINGS_KEY, [])
    if paths is None:
        return []
    if isinstance(paths, str):
        paths = [paths]
    valid = [p for p in paths if isinstance(p, str) and os.path.isfile(p)]
    ...
```

### WR-06: Test assertions that pass trivially without testing their stated intent

**File:** `/home/jone/projects/secnotepad/tests/ui/test_password_dialog.py:55-58`  
**File:** `/home/jone/projects/secnotepad/tests/ui/test_password_dialog.py:126-131`

**Issue:** Two tests use non-functional assertions that always pass:

1. Lines 55-58, `test_confirm_disabled_when_empty`: Uses `set_dialog.findChild(QPushButton, "确认")` which searches by Qt object *name* (which is empty), not by button *text*. The function almost certainly returns `None`, making `assert confirm is None or not confirm.isEnabled()` trivially pass via the first branch.

2. Lines 127-131, `test_password_fields_hidden_initially`: Contains `assert len(line_edits) >= 0` — a tautology that always evaluates to `True` regardless of actual state. The accompanying comment "至少不报错" acknowledges this is a placeholder.

```python
# test_password_dialog.py:55-58
def test_confirm_disabled_when_empty(self, set_dialog):
    confirm = set_dialog.findChild(QPushButton, "确认")  # finds by objectName, not text
    assert confirm is None or not confirm.isEnabled()     # always passes via None

# test_password_dialog.py:127-131
def test_password_fields_hidden_initially(self, change_dialog):
    line_edits = change_dialog.findChildren(QLineEdit)
    assert len(line_edits) >= 0  # always true, vacuously
```

**Fix:** Replace with meaningful assertions:

```python
# test_password_dialog.py:55-58
def test_confirm_disabled_when_empty(self, set_dialog):
    confirm = [b for b in set_dialog.findChildren(QPushButton) if b.text() == "确认"]
    assert len(confirm) == 1
    assert not confirm[0].isEnabled()

# test_password_dialog.py:127-131
def test_password_fields_hidden_initially(self, change_dialog):
    line_edits = change_dialog.findChildren(QLineEdit)
    for le in line_edits:
        assert le.isHidden(), f"Field '{le.objectName()}' should be hidden"
```

## Info

### IN-01: `_evaluate_strength` declares unused `self` parameter

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/password_dialog.py:188-218`
**Issue:** The method `_evaluate_strength` accepts `self` as its first parameter but never uses it. It is called as `self._evaluate_strength(pwd_text)` but could be a `@staticmethod`. This is a minor inconsistency — no bug, but degrades readability and bypasses the static-method decorator's documentation role.

**Fix:** Decorate with `@staticmethod`:

```python
@staticmethod
def _evaluate_strength(password: str) -> tuple[int, str]:
```

### IN-02: `_on_open_notebook` and `_on_open_recent` are nearly identical

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:288-342` and `:459-505`
**Issue:** The password retry loop + model loading logic in `_on_open_notebook` (lines 301-318) and `_on_open_recent` (lines 470-484) is nearly identical. The only difference is the source of the file path (from `QFileDialog` vs. from the signal parameter). This duplication means any future fix to the password loop (e.g., the error distinction issue in WR-02) must be applied in two places.

**Fix:** Extract a shared helper:

```python
def _open_file_with_password(self, path: str):
    """Shared password retry loop + model load."""
    dialog = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD, parent=self)
    while dialog.exec() == QDialog.Accepted:
        password = dialog.password()
        dialog.clear_password()
        try:
            json_str = FileService.open(path, password)
        except ValueError:
            dialog.set_error_message("密码错误，请重试")
            continue
        password_correct = password
        break
    else:
        return None
    return json_str, password_correct
```

---

_Reviewed: 2026-05-07T14:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
