---
phase: 02-file-operations-and-encryption
reviewed: 2026-05-08T10:00:00Z
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
  critical: 0
  warning: 8
  info: 6
  total: 14
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-08T10:00:00Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Reviewed 13 files covering the crypto layer (file_service, header), UI layer (main_window, password_dialog, password_generator, welcome_widget), and their tests. The architecture follows a sound Encrypt-and-MAC pattern with PBKDF2 key derivation, constant-time HMAC comparison, and `bytearray`-based password clearing. However, there are significant issues: two data-loss paths where `_on_new_notebook` and `_on_open_notebook` silently discard unsaved changes; the `Header.build()` uses `assert` for validation which is stripped under `python -O`; `PasswordDialog` crashes on non-ASCII input instead of rejecting it gracefully; `FileService.decrypt()` is missing an `isascii()` guard that `encrypt()` has; `PasswordGenerator` returns a different password than displayed; `save_as` updates state before confirming I/O succeeded; and the `QSettings` recent-files list handles single-entry lists incorrectly, which silently loses the list on the first open. No critical security vulnerabilities were found.

## Warnings

### WR-01: `_on_new_notebook` silently discards unsaved data

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:261-265`
**Issue:** `_on_new_notebook()` has a stub block that checks `if self._root_item is not None` but executes only `pass`, then unconditionally overwrites `self._root_item` on line 268. If the user has an open notebook with unsaved changes and clicks "New", the existing `_root_item` reference is dropped and all unsaved data is silently discarded. The `# Phase 3 TODO` comment acknowledges this gap but the code is shipping with active data loss.

```python
def _on_new_notebook(self):
    if self._root_item is not None:
        # Phase 3 TODO: check dirty flag and show confirmation dialog
        pass          # does nothing -- data silently lost
    if self._tree_model is not None:
        self._tree_model.deleteLater()
    self._root_item = SNoteItem.new_section("根分区")  # overwrites
```

**Fix:** Implement dirty-check confirmation before overwriting, following the same pattern as `closeEvent()`:

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
                return
        elif clicked == btn_cancel:
            return
    # ... proceed with creation ...
```

---

### WR-02: `_on_open_notebook` and `_on_open_recent` silently discard unsaved data

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:288` and `:459`
**Issue:** Same data-loss pattern as WR-01. Both `_on_open_notebook()` and `_on_open_recent()` overwrite `self._root_item` (lines 324 and 489) without checking `self._is_dirty`. If the user has unsaved changes and opens a different file, the changes are lost without warning. The password retry loop (lines 301-318 and 470-484) completes successfully, then the new data replaces the old unconditionally.

**Fix:** Insert a dirty-check guard at the start of both methods, before opening the file dialog or password dialog:

```python
def _on_open_notebook(self):
    if self._root_item is not None and self._is_dirty:
        # Show confirmation dialog (same pattern as WR-01)
        if not self._confirm_discard_changes():
            return
    path, _ = QFileDialog.getOpenFileName(...)
    ...
```

---

### WR-03: `assert` in `Header.build()` bypassed under `python -O`

**File:** `/home/jone/projects/secnotepad/src/secnotepad/crypto/header.py:34-36`
**Issue:** `assert` statements are stripped when Python runs with `-O` (optimized flag). In optimized builds, these length checks vanish. Any future refactoring that produces wrong-length salt, IV, or HMAC tag would pass through silently and produce a corrupt file header (or a confusing `struct.error`).

```python
assert len(salt) == 16, "salt must be 16 bytes"
assert len(iv) == 16, "IV must be 16 bytes"
assert len(hmac_tag) == 32, "HMAC tag must be 32 bytes"
```

**Fix:** Replace `assert` with explicit `ValueError` or `HeaderError` guards:

```python
if len(salt) != 16:
    raise HeaderError(f"salt must be 16 bytes, got {len(salt)}")
if len(iv) != 16:
    raise HeaderError(f"IV must be 16 bytes, got {len(iv)}")
if len(hmac_tag) != 32:
    raise HeaderError(f"HMAC tag must be 32 bytes, got {len(hmac_tag)}")
```

---

### WR-04: Non-ASCII password crashes `PasswordDialog` instead of showing error

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/password_dialog.py:289-296`
**Issue:** `_on_confirm()` calls `pwd_text.encode('ascii')` without validation. If a user types non-ASCII characters (e.g., CJK, accented Latin, emoji), Python raises `UnicodeEncodeError` inside the Qt slot. In PySide6, this exception is printed to stderr and the slot returns without calling `self.accept()`. The dialog does not close, the user receives no feedback, and the confirm button appears to do nothing. The same failure exists in `password()` (line 177: `str(self._password, encoding='ascii')`).

The ASCII-only constraint is documented (D-29) but the UI does not enforce it before encoding.

```python
def _on_confirm(self):
    pwd_text = self._pwd_input.text()
    ...
    self._password = bytearray(pwd_text.encode('ascii'))  # UnicodeEncodeError
    self.accept()
```

**Fix:** Validate ASCII before encoding and show an inline error message:

```python
def _on_confirm(self):
    pwd_text = self._pwd_input.text()
    if pwd_text and not pwd_text.isascii():
        error_label = getattr(self, '_error_label', None) or self._mismatch_warning
        error_label.setText("密码仅支持 ASCII 字符")
        error_label.setVisible(True)
        return
    # ... proceed with encoding ...
```

---

### WR-05: `FileService.decrypt()` missing `isascii()` guard present in `encrypt()`

**File:** `/home/jone/projects/secnotepad/src/secnotepad/crypto/file_service.py:133-139`
**Issue:** `encrypt()` (line 96-97) validates `password.isascii()` and raises a clear `ValueError`. `decrypt()` only checks `if not password` (line 133) but does NOT check `isascii()`. If any future code path calls `decrypt()` with a non-ASCII password (e.g., bypassing `PasswordDialog`), the call crashes with `UnicodeEncodeError` from `_derive_keys` (line 50) instead of a meaningful error message.

```python
# encrypt() has:
if not password.isascii():
    raise ValueError("密码仅支持 ASCII 字符 (D-29)")

# decrypt() is missing this guard -- only checks:
if not password:
    raise ValueError("密码不能为空")
```

**Fix:** Add the same `isascii()` guard to `decrypt()`:

```python
@staticmethod
def decrypt(file_data: bytes, password: str) -> str:
    if not password:
        raise ValueError("密码不能为空")
    if not password.isascii():
        raise ValueError("密码仅支持 ASCII 字符 (D-29)")
    ...
```

---

### WR-06: `PasswordGenerator._on_accept` returns a different password than displayed

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/password_generator.py:100-103`
**Issue:** `_on_accept()` calls `self._generate()` and then `self.accept()`. This generates a NEW password at accept time, different from the one the user saw in the preview. The button is labeled "生成并使用" (Generate and Use) which implies the displayed password will be used. The user may have read or copied the preview password, only to receive a different one.

```python
def _on_accept(self):
    """确认生成并关闭。"""
    self._generate()  # regenerates a different password
    self.accept()
```

**Fix:** Either (a) use the current preview password without regenerating, or (b) rename the button to "重新生成并使用" and rework the flow so users expect a fresh password on accept:

```python
def _on_accept(self):
    """使用当前显示的密码并关闭。"""
    # Don't regenerate -- use what's already in self._password and _preview
    self.accept()
```

---

### WR-07: `_on_save_as` updates application state before confirming I/O success

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:393-401`
**Issue:** After calling `FileService.save_as(json_str, path, new_password)` on line 394, the method immediately updates `_current_path`, `_current_password`, and sets `_is_dirty = False`. If the actual I/O operation fails (disk full, permissions, file locked, etc.), the application state reflects a successful save while the file was never written. The dirty flag is cleared, so the user cannot retry. This causes silent data loss.

```python
FileService.save_as(json_str, path, new_password)  # may raise IOError

# These execute even if save_as failed:
self._current_path = path
self._current_password = new_password
self._is_dirty = False
```

**Fix:** Only update state after successful I/O. Catch exceptions and propagate or handle them before touching state:

```python
try:
    FileService.save_as(json_str, path, new_password)
except (OSError, IOError) as e:
    QMessageBox.critical(self, "保存失败", f"无法保存文件:\n{e}")
    return

self._current_path = path
self._current_password = new_password
self._is_dirty = False
```

---

### WR-08: `QSettings.value()` single-string degradation on single-element list

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:413-419` (and `_add_recent_file` at 431, `_remove_recent_file` at 449)
**Issue:** `QSettings.value()` can return a plain `str` instead of `list[str]` when the stored list has exactly one entry and the settings backend (e.g., INI on Linux) degrades single-element lists to scalars. The list comprehension in `_load_recent_files()` (line 419) iterates over individual characters of the path string. `isinstance(p, str)` passes for each character, but `os.path.isfile(p)` returns `False` for single characters, effectively emptying the recent files list silently. This affects all three QSettings methods.

```python
def _load_recent_files(self) -> list[str]:
    settings = QSettings()
    paths = settings.value(self.SETTINGS_KEY, [])
    if paths is None:
        return []
    # If paths is a single string, iterating yields characters
    valid = [p for p in paths if isinstance(p, str) and os.path.isfile(p)]
```

**Fix:** Guard against string degradation in all three methods:

```python
def _load_recent_files(self) -> list[str]:
    settings = QSettings()
    paths = settings.value(self.SETTINGS_KEY, [])
    if paths is None:
        return []
    if isinstance(paths, str):
        paths = [paths]
    valid = [p for p in paths if isinstance(p, str) and os.path.isfile(p)]
    ...
```

## Info

### IN-01: Deprecated CFB cipher mode used from `cryptography.hazmat.decrepit`

**File:** `/home/jone/projects/secnotepad/src/secnotepad/crypto/file_service.py:19`
**Issue:** CFB mode is imported from `cryptography.hazmat.decrepit.ciphers.modes`, which is a deprecated module. Future versions of the `cryptography` library may remove it entirely. Consider migrating to AES-GCM (authenticated encryption, no separate HMAC required) or AES-CTR with the existing HMAC.

---

### IN-02: Eye toggle uses checkmark icon instead of eye icon

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/password_dialog.py:224-225`
**Issue:** The `_add_eye_toggle()` method sets an icon using `QStyle.SP_DialogApplyButton` which is a checkmark, not an eye. The function name implies it should show/hide password visibility with an eye icon, but users see a checkmark toggle. PySide6 has no standard eye icon; a custom resource icon would be needed.

```python
action.setIcon(icon)  # SP_DialogApplyButton is a checkmark, not an eye
```

---

### IN-03: `_clear_session` does not clear `_root_item`

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:210-214`
**Issue:** `_clear_session()` clears `_current_password`, `_is_dirty`, and `_current_path`, but does not clear `_root_item` or `_tree_model`. When called during close (discard path), the root item containing all loaded note data remains referenced. For a security-focused app concerned with sensitive data in memory (D-27, D-39), retaining the full decrypted note tree after close is inconsistent with the secure-clearing done for the password.

---

### IN-04: TODO left in production code

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:264`
**Issue:** A `# Phase 3 TODO` comment acknowledges the missing dirty-check but leaves the code path broken. TODOs in production code should reference a tracking system rather than serve as placeholder for unimplemented behavior.

---

### IN-05: Duplicate password retry logic across `_on_open_notebook` and `_on_open_recent`

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py:301-318` and `:470-484`
**Issue:** The entire password retry loop (dialog creation, while loop, error handling, break/else) is duplicated verbatim between `_on_open_notebook` and `_on_open_recent`. The only difference is the file path source. Any future fix (e.g., WR-07's error-handling improvement) must be applied to both copies.

**Fix:** Extract a shared helper:

```python
def _open_with_password_retry(self, path: str):
    dialog = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD, parent=self)
    while dialog.exec() == QDialog.Accepted:
        password = dialog.password()
        dialog.clear_password()
        try:
            json_str = FileService.open(path, password)
        except ValueError:
            dialog.set_error_message("密码错误，请重试")
            continue
        return json_str, password
    return None, None
```

---

### IN-06: Password generator does not guarantee characters from each selected charset

**File:** `/home/jone/projects/secnotepad/src/secnotepad/ui/password_generator.py:88-98`
**Issue:** `_generate()` concatenates all selected charsets and picks each character independently from the combined pool. A generated password may contain only lowercase letters even if "symbols" and "digits" are checked, because no per-charset minimum is enforced. This contradicts user expectations -- if a user enables "symbols", they expect at least one symbol character.

---

_Reviewed: 2026-05-08T10:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
