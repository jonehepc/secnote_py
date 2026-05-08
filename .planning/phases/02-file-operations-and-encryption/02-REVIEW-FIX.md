---
phase: 02-file-operations-and-encryption
fixed_at: 2026-05-08T10:00:00Z
review_path: /home/jone/projects/secnotepad/.planning/phases/02-file-operations-and-encryption/02-REVIEW.md
iteration: 1
findings_in_scope: 14
fixed: 14
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-05-08T10:00:00Z
**Source review:** .planning/phases/02-file-operations-and-encryption/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 14 (8 Warnings + 6 Info)
- Fixed: 14
- Skipped: 0

## Fixed Issues

### WR-01: `_on_new_notebook` silently discards unsaved data

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** 193ac9e
**Applied fix:** Replaced stub `pass` block with a full dirty-check confirmation dialog (Save/Discard/Cancel) before overwriting the current notebook, matching the pattern used in `closeEvent()`.

### WR-02: `_on_open_notebook` and `_on_open_recent` silently discard unsaved data

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** 317be23
**Applied fix:** Added `_confirm_discard_changes()` helper method that shows a confirmation dialog when `_is_dirty` is true. Called from both `_on_open_notebook()` (before file dialog) and `_on_open_recent()` (after file existence check).

### WR-03: `assert` in `Header.build()` bypassed under `python -O`

**Files modified:** `src/secnotepad/crypto/header.py`
**Commit:** 23b097d
**Applied fix:** Replaced `assert len(...)` statements with explicit `if len(...) != N: raise HeaderError(...)` guards that execute regardless of optimization flags.

### WR-04: Non-ASCII password crashes `PasswordDialog` instead of showing error

**Files modified:** `src/secnotepad/ui/password_dialog.py`
**Commit:** 0233eb1
**Applied fix:** Added `pwd_text.isascii()` check at the start of `_on_confirm()` that shows an inline error message and returns early instead of letting `encode('ascii')` raise `UnicodeEncodeError`.

### WR-05: `FileService.decrypt()` missing `isascii()` guard present in `encrypt()`

**Files modified:** `src/secnotepad/crypto/file_service.py`
**Commit:** 5b2547f
**Applied fix:** Added `if not password.isascii(): raise ValueError(...)` to `decrypt()`, matching the existing guard in `encrypt()`.

### WR-06: `PasswordGenerator._on_accept` returns a different password than displayed

**Files modified:** `src/secnotepad/ui/password_generator.py`
**Commit:** 882a3d5
**Applied fix:** Removed the `self._generate()` call from `_on_accept()` so the dialog returns the password already displayed in the preview, not a newly generated one.

### WR-07: `_on_save_as` updates application state before confirming I/O success

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** 7045673
**Applied fix:** Wrapped `FileService.save_as()` and `FileService.save()` in try/except blocks for `(OSError, IOError)`. State (`_current_path`, `_current_password`, `_is_dirty`) is only updated after successful I/O. Same fix applied to `_on_save()` which had the same pattern.

### WR-08: `QSettings.value()` single-string degradation on single-element list

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** 01b06f8
**Applied fix:** Added `if isinstance(paths, str): paths = [paths]` guard after each `QSettings.value()` call in `_load_recent_files()`, `_add_recent_file()`, and `_remove_recent_file()` to prevent silent data loss when the settings backend degrades single-element lists to scalars.

### IN-01: Deprecated CFB cipher mode from `cryptography.hazmat.decrepit`

**Files modified:** `src/secnotepad/crypto/header.py`, `src/secnotepad/crypto/file_service.py`
**Commit:** 980bc65
**Applied fix:** Migrated from AES-256-CFB (from `cryptography.hazmat.decrepit`) to AES-256-GCM. Removed separate HMAC computation since GCM provides authenticated encryption. Simplified key derivation to a single PBKDF2 key. Updated header format to version 2: salt (16B) + nonce (12B) + GCM tag (16B) = 49B header.

### IN-02: Eye toggle uses checkmark icon instead of eye icon

**Files modified:** `src/secnotepad/ui/password_dialog.py`
**Commit:** 6e18365
**Applied fix:** Changed icon from `QStyle.SP_DialogApplyButton` (checkmark) to `QStyle.SP_FileDialogContentsView` (view icon), since Qt has no standard eye icon. Added docstring noting that a custom QRC resource would be ideal.

### IN-03: `_clear_session` does not clear `_root_item`

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** 6ca6ed6
**Applied fix:** Added `self._root_item = None` and `self._tree_model = None` to `_clear_session()`, consistent with the secure clearing done for the password.

### IN-04: TODO left in production code

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** (fixed as part of WR-01, commit 193ac9e)
**Applied fix:** The `# Phase 3 TODO` comment was removed as part of WR-01's dirty-check confirmation implementation, replacing the stub `pass` block.

### IN-05: Duplicate password retry logic across `_on_open_notebook` and `_on_open_recent`

**Files modified:** `src/secnotepad/ui/main_window.py`
**Commit:** b80bfe7
**Applied fix:** Extracted the duplicated password retry loop into `_open_with_password_retry(path)` helper method. Both `_on_open_notebook` and `_on_open_recent` now call the shared helper, reducing 34 duplicated lines.

### IN-06: Password generator does not guarantee characters from each selected charset

**Files modified:** `src/secnotepad/ui/password_generator.py`
**Commit:** 479be4a
**Applied fix:** `_generate()` now picks at least one character from each enabled charset before filling remaining positions from the combined pool. The result is shuffled to avoid predictable prefix patterns. Edge case where length < number of charsets is handled by random subset selection.

---

_Fixed: 2026-05-08T10:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
