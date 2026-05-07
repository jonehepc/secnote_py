---
phase: 02-file-operations-and-encryption
plan: 02
subsystem: ui
tags: [password-dialog, password-generator, bytearray-cleanup, ui-testing]
provides: [CRYPT-01, CRYPT-02, CRYPT-04]
affects: [main_window.py, welcome_widget.py]
tech-stack:
  added:
    - "secrets (CSPRNG for password generation)"
    - "PySide6.QLineEdit.addAction for eye toggle"
  patterns:
    - "bytearray secure zeroing (D-27)"
    - "PasswordMode enum for three-mode dialog"
key-files:
  created:
    - src/secnotepad/ui/password_dialog.py (329 lines)
    - src/secnotepad/ui/password_generator.py (100+ lines)
  modified:
    - tests/conftest.py (added test_password, sample_json_str fixtures)
  created:
    - tests/ui/test_password_dialog.py (203 lines, 19 tests)
decisions:
  - "Eye toggle uses QStyle.SP_DialogApplyButton as icon (Qt built-in)"
  - "Password strength uses simple entropy calculation (no zxcvbn)"
  - "PasswordGenerator uses secrets module (not random)"
metrics:
  duration: "~2 minutes"
  completed: "2026-05-07"
  files_created: 3
  tests_passed: 19
---

# Phase 02 Plan 02: Password Dialog and Generator

Implement unified PasswordDialog (SET_PASSWORD / ENTER_PASSWORD / CHANGE_PASSWORD modes) and PasswordGenerator sub-dialog, with test fixtures and bytearray secure cleanup.

## Tasks

### Task 1: Extend test fixtures and create PasswordGenerator

- Added `test_password` fixture (returns "TestP@ss123") and `sample_json_str` fixture (valid JSON payload) to tests/conftest.py
- Created `src/secnotepad/ui/password_generator.py` with `PasswordGenerator(QDialog)` class
- PasswordGenerator uses `secrets` module for CSPRNG, length range 8-128 (default 16), four character sets (uppercase/lowercase/digits/symbols), read-only preview field, "生成并使用" button
- At least one character set must remain checked (prevents all-uncheck state)

### Task 2: Implement PasswordDialog (3 modes, bytearray secure cleanup)

- Created `src/secnotepad/ui/password_dialog.py` with `PasswordMode` enum and `PasswordDialog(QDialog)` class
- **SET_PASSWORD mode (D-31, D-32, D-34):** Two QLineEdit fields (password + confirm) with eye toggle, mismatch warning label ("两次输入的密码不一致"), real-time strength indicator (QProgressBar with red/orange/green styling + "弱"/"中"/"强" label), "生成密码" button opens PasswordGenerator, confirm button disabled when < 8 chars or mismatch
- **ENTER_PASSWORD mode (D-35):** Single QLineEdit with eye toggle, "请输入文件加密密码" label, `_error_label` hidden initially (red "密码错误，请重试"), `set_error_message()` public API for external error display, confirm enabled when non-empty, unlimited retry
- **CHANGE_PASSWORD mode (D-38):** QCheckBox "更换密码" (default unchecked), when checked shows SET_PASSWORD-style password fields; when unchecked confirm always enabled
- **Security:** Password stored as `bytearray` (D-27, D-39), `clear_password()` zeros in-place via `self._password[:] = b'\x00' * len(self._password)`, `rejected` signal connected to `clear_password()`, `password()` returns `str` (decoded from bytearray)
- **Eye toggle (D-37):** `_add_eye_toggle()` adds QAction with QStyle.SP_DialogApplyButton icon, switches EchoMode between Password and Normal
- **Strength evaluation:** Simple entropy = length * log2(charset_size), mapped to 0-100% (red 0-33, orange 34-66, green 67-100)

### Task 3: Create dialog tests (19 test cases)

- 5 test classes: `TestSetPasswordMode`, `TestEnterPasswordMode`, `TestChangePasswordMode`, `TestSecureClear`, `TestPasswordGenerator`
- Tests use `qapp` fixture, fixture pattern from test_main_window.py
- **D-27 bytearray tests:** verify `_password` is bytearray, `clear_password()` zeros all bytes in-place, `password()` returns str
- **D-35 test:** `set_error_message()` shows the error label
- **D-33 generator tests:** default length 16, spinbox changes length, uses `secrets` not `random`

## Threat Model Compliance

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-02-04 (Info Disclosure - bytearray) | mitigate | Implemented: bytearray storage + clear_password() zeroing |
| T-02-05 (Info Disclosure - eye toggle) | mitigate | Implemented: default EchoMode=Password, toggle on demand |
| T-02-06 (Spoofing - strength indicator) | accept | Implemented as UX-only, not security mechanism |
| T-02-07 (Info Disclosure - generator preview) | accept | Preview in local dialog only, no logging |

## Verification Results

- `python -c "from src.secnotepad.ui.password_dialog import PasswordDialog, PasswordMode"` -- PASSED
- `python -c "from src.secnotepad.ui.password_generator import PasswordGenerator"` -- PASSED
- `python -m pytest tests/ui/test_password_dialog.py -x -q` -- 19 passed in 0.11s

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all features fully wired.

## Threat Flags

None - all security surface matches the plan's threat model.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `8c065fe` | feat(02-02): add test fixtures and PasswordGenerator dialog |
| 2 | `0d87e4b` | feat(02-02): implement PasswordDialog with three modes |
| 3 | `897bb42` | test(02-02): add password dialog and generator tests |

## Self-Check: PASSED

- [x] `src/secnotepad/ui/password_dialog.py` exists (verify: FOUND)
- [x] `src/secnotepad/ui/password_generator.py` exists (verify: FOUND)
- [x] `tests/ui/test_password_dialog.py` exists (verify: FOUND)
- [x] `tests/conftest.py` has test_password fixture (verify: FOUND)
- [x] Commit 8c065fe exists (verify: FOUND)
- [x] Commit 0d87e4b exists (verify: FOUND)
- [x] Commit 897bb42 exists (verify: FOUND)
- [x] All 19 tests pass (verify: 19 passed)
