---
phase: 02-file-operations-and-encryption
verified: 2026-05-07T16:00:00Z
status: passed
score: 31/31 must-haves verified
overrides_applied: 1
overrides:
  - must_have: "file_service.py imports/model/serializer.py via Serializer.from_json"
    reason: "By design — FileService is a pure crypto layer operating on plain JSON strings. Serializer integration happens at the MainWindow layer (main_window.py imports Serializer). Plan 03 context explicitly documents this decoupling."
    accepted_by: "design (D-21~D-28, documented in CONTEXT.md)"
    accepted_at: "2026-05-07T16:00:00Z"
gaps: []
deferred: []
human_verification: []
---

# Phase 2: File Operations and Encryption — Verification Report

**Phase Goal:** 实现文件加密存储和密码管理功能，包括加密文件头、密码对话框、文件服务和主窗口集成
**Verified:** 2026-05-07T16:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### ROADMAP Success Criteria

| # | Success Criterion | Status | Evidence |
|---|-------------------|--------|----------|
| 1 | 用户新建笔记本后可输入内容、保存为 `.secnote` 文件（需输入密码） | VERIFIED | `_on_new_notebook()` creates in-memory notebook. `_on_save()`/`_on_save_as()` triggers PasswordDialog(SET_PASSWORD) then FileService.save(). Test `test_save_enabled_after_new` confirms save button enabled. |
| 2 | 打开已有 `.secnote` 文件时，输入正确密码可解密加载，错误密码显示错误提示 | VERIFIED | `_on_open_notebook()` uses QFileDialog + PasswordDialog(ENTER_PASSWORD) with while-loop retry. `dialog.set_error_message()` shows "密码错误，请重试" on ValueError. FileService.open() + Serializer.from_json() loads data. Test password dialog tests verify. |
| 3 | 文件内容使用 PBKDF2-SHA256(密码) + AES-256-CFB + HMAC-SHA256 加密存储，无法直接明文读取 | VERIFIED | FileService.encrypt() uses PBKDF2-SHA256 600k iterations (D-21), AES-256-CFB, HMAC-SHA256. `test_encrypt_output_not_readable` confirms plaintext not in ciphertext. `test_tampered_ciphertext`/`test_tampered_hmac` verify integrity protection. |
| 4 | 另存为功能可用，支持更改路径和密码 | VERIFIED | `_on_save_as()` uses PasswordDialog(CHANGE_PASSWORD) with optional password change. FileService.save_as() generates new salt+IV per D-28. TestSaveAs tests confirm new password functionality. |
| 5 | 关闭时若有未保存更改，弹出保存提示 | VERIFIED | `closeEvent()` creates QMessageBox with save/discard/cancel three buttons (D-48). `_is_dirty` flag managed via mark_dirty()/mark_clean(). D-47: empty new notebook skips prompt. |

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 文件头可以正确组装为 69 字节的二进制数据 | VERIFIED | `Header.build()` at `header.py:37-40`. `test_build_header_length` passes: 18/18 header tests pass. |
| 2 | 文件头可以从二进制数据正确解析回各字段 | VERIFIED | `Header.parse()` at `header.py:43-70`. `test_parse_header_roundtrip` confirms all fields preserved. |
| 3 | 无效魔数被检测并拒绝 | VERIFIED | `test_parse_header_invalid_magic` raises HeaderError with "魔数" message. |
| 4 | build + parse 往返测试保留所有字段 | VERIFIED | `test_parse_header_roundtrip`, `test_parse_header_roundtrip_version` confirm. |
| 5 | 新建笔记本时可以输入密码（含确认字段） | VERIFIED | PasswordDialog SET_PASSWORD mode has two QLineEdit fields. `test_two_password_fields` confirms. |
| 6 | 打开笔记本时可以输入密码解密 | VERIFIED | PasswordDialog ENTER_PASSWORD mode with single QLineEdit + "请输入文件加密密码" label. |
| 7 | 另存为时可以更换密码或沿用现有密码 | VERIFIED | PasswordDialog CHANGE_PASSWORD mode with QCheckBox "更换密码". `test_checkbox_exists` confirms. |
| 8 | 密码支持显示/隐藏切换（眼睛图标） | VERIFIED | `_add_eye_toggle()` at `password_dialog.py:220-229` adds QAction toggle for EchoMode switching. |
| 9 | 密码强度实时显示（弱/中/强） | VERIFIED | `_evaluate_strength()` at `password_dialog.py:188-218` with QProgressBar color coding. `test_strength_bar_exists` confirms. |
| 10 | 密码错误时在对话框内提示重新输入 | VERIFIED | `set_error_message()` at `password_dialog.py:158-166`. Test `test_set_error_message_shows_label` confirms. MainWindow while-loop retry pattern. |
| 11 | 可以生成随机密码，可选长度和字符集 | VERIFIED | PasswordGenerator with QSpinBox (8-128), 4 charsets, secrets module. `test_generator_creates_password` confirms. |
| 12 | 两次输入的密码不一致时确认按钮禁用 | VERIFIED | `_on_password_changed()` shows mismatch_warning. `_update_confirm_button()` disables when pwd != confirm. |
| 13 | 密码最短 8 字符 | VERIFIED | `_update_confirm_button()` checks `len(pwd) >= 8`. `test_min_length_8` confirms. |
| 14 | 明文 JSON 加密后无法直接读取 | VERIFIED | `test_encrypt_output_not_readable` passes — `assert plaintext_bytes not in encrypted`. |
| 15 | 加密后的数据可以用同一密码解密还原 | VERIFIED | `test_encrypt_decrypt_roundtrip` passes. FileService roundtrip confirmed. |
| 16 | 不同密码解密时抛出 ValueError | VERIFIED | `test_decrypt_wrong_password` passes with match="密码错误". |
| 17 | 加密文件保存到磁盘后可重新打开 | VERIFIED | `test_save_and_open_roundtrip` passes — save + open roundtrip. |
| 18 | 另存为功能可修改密码 | VERIFIED | `test_save_as_new_password` passes — old password fails, new password succeeds. |
| 19 | 密码在内存使用后显式清零 | VERIFIED | `clear_password()` at `password_dialog.py:179-184` uses bytearray in-place zeroing. `test_clear_password_zeros_bytearray` passes. |
| 20 | 打开 .secnote 文件时弹出文件选择对话框 | VERIFIED | `_on_open_notebook()` calls `QFileDialog.getOpenFileName()` with .secnote filter. Source: `main_window.py:293-296`. |
| 21 | 选择文件后弹出密码输入对话框 | VERIFIED | `PasswordDialog(mode=PasswordMode.ENTER_PASSWORD)` created immediately after file selection. |
| 22 | 输入正确密码后文件被解密并加载到编辑界面 | VERIFIED | `FileService.open(path, password) -> json_str` then `Serializer.from_json(json_str)` builds TreeModel. Stack switches to index 1. |
| 23 | 输入错误密码时在对话框内显示错误提示，可重试 | VERIFIED | `while dialog.exec() == QDialog.Accepted` loop with `dialog.set_error_message("密码错误，请重试")`. |
| 24 | 点击保存时直接加密保存到当前文件（无需重复输入密码） | VERIFIED | `_on_save()` uses `self._current_path` and `self._current_password` directly. |
| 25 | 点击另存为时可选择新路径和新密码 | VERIFIED | `_on_save_as()` calls QFileDialog.getSaveFileName + CHANGE_PASSWORD dialog. |
| 26 | 关闭窗口时若有未保存更改，弹出保存/不保存/取消确认框 | VERIFIED | `closeEvent()` at `main_window.py:176-208` with 3-button QMessageBox. |
| 27 | 空的未保存新建笔记本关闭时不弹出提示 | VERIFIED | `if self._is_dirty and self._root_item is not None` — new notebook has `_is_dirty=False`, skips prompt. `test_new_notebook_not_dirty` confirms. |
| 28 | 欢迎页显示最近打开的文件列表（最多 5 条） | VERIFIED | WelcomeWidget has QListWidget. `set_recent_files()` method. `MAX_RECENT_FILES = 5`. `test_recent_files_max_items` confirms. |
| 29 | 单击最近文件直接触发打开流程 | VERIFIED | `recent_file_clicked` Signal(str) → `_on_open_recent(path)` → PasswordDialog retry loop. |
| 30 | 文件路径不存在的条目被静默移除 | VERIFIED | `_load_recent_files()` at `main_window.py:411-423` filters by `os.path.isfile(p)`. |
| 31 | 窗口标题显示当前文件名，有未保存更改时带 * 标记 | VERIFIED | `_update_window_title()` at `main_window.py:232-242`. `test_dirty_marker_appears` confirms. |

**Score:** 31/31 truths verified

### Required Artifacts

| Artifact | Expected | Actual Lines | Status | Details |
|----------|----------|-------------|--------|---------|
| `src/secnotepad/crypto/header.py` | >= 60 | 70 | VERIFIED | Header.build(), Header.parse(), HeaderError, constants |
| `tests/crypto/test_header.py` | >= 80 | 155 | VERIFIED | 18 tests covering constants, build, parse, errors |
| `src/secnotepad/ui/password_dialog.py` | >= 200 | 329 | VERIFIED | PasswordDialog with 3 modes, eye toggle, strength bar, bytearray security |
| `src/secnotepad/ui/password_generator.py` | >= 100 | 107 | VERIFIED | PasswordGenerator with length/charset controls, secrets module |
| `tests/ui/test_password_dialog.py` | >= 80 | 203 | VERIFIED | 19 tests across 5 test classes |
| `src/secnotepad/crypto/file_service.py` | >= 150 | 202 | VERIFIED | FileService.encrypt/decrypt/save/open/save_as, PBKDF2+AES+HMAC |
| `tests/crypto/test_file_service.py` | >= 100 | 145 | VERIFIED | 16 tests covering roundtrip, wrong pw, tampering, file I/O |
| `src/secnotepad/ui/main_window.py` | >= 270 | 505 | VERIFIED | Dirty flag, closeEvent, file handlers, recent files, full lifecycle |
| `src/secnotepad/ui/welcome_widget.py` | >= 100 | 114 | VERIFIED | Recent file QListWidget, Signal(str), set_recent_files |
| `tests/ui/test_main_window.py` | >= 220 | 371 | VERIFIED | 53 tests including TestDirtyFlag, TestSaveActions, TestWindowTitle, TestRecentFiles |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `crypto/header.py` | `crypto/file_service.py` | import | VERIFIED | `file_service.py:24` — `from .header import Header, HeaderError` |
| `ui/password_dialog.py` | `ui/main_window.py` | import | VERIFIED | `main_window.py:17` — `from .password_dialog import PasswordDialog, PasswordMode` |
| `ui/password_generator.py` | `ui/password_dialog.py` | import | VERIFIED | `password_dialog.py:301` — `from .password_generator import PasswordGenerator` |
| `crypto/file_service.py` | `crypto/header.py` | import Header | VERIFIED | `file_service.py:24` — imports Header for build/parse |
| `crypto/file_service.py` | `model/serializer.py` | design flow | PASSED (override) | FileService operates on JSON strings; Serializer integration is at MainWindow layer (`main_window.py:16` imports Serializer). Documented design per CONTEXT.md. |
| `ui/main_window.py` | `crypto/file_service.py` | import FileService | VERIFIED | `main_window.py:15` — `from ..crypto.file_service import FileService` |
| `ui/main_window.py` | `ui/password_dialog.py` | import PasswordDialog | VERIFIED | `main_window.py:17` — imports both PasswordDialog and PasswordMode |
| `ui/main_window.py` | `ui/welcome_widget.py` | signal connect | VERIFIED | `main_window.py:143` — `self._welcome.recent_file_clicked.connect(self._on_open_recent)` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `header.py` | Return of `build()` | `struct.pack` with real inputs | Yes | FLOWING |
| `header.py` | Return of `parse()` | `struct.unpack` from binary data | Yes | FLOWING |
| `file_service.py` | Ciphertext in `encrypt()` | `os.urandom` salt/IV, PBKDF2 derivation, AES-CFB encryption | Yes | FLOWING |
| `file_service.py` | Plaintext in `decrypt()` | AES-CFB decryption + HMAC verification | Yes | FLOWING |
| `password_dialog.py` | `self._password` | `bytearray(pwd_text.encode('ascii'))` from user input | Yes | FLOWING |
| `main_window.py` | `self._current_password` | From PasswordDialog.password() after exec() | Yes | FLOWING |
| `welcome_widget.py` | `self._recent_list` items | From QSettings via `set_recent_files()` | Yes | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Header tests pass | `python -m pytest tests/crypto/test_header.py -x -q` | 18 passed | PASS |
| File service tests pass | `python -m pytest tests/crypto/test_file_service.py -x -q` | 16 passed | PASS |
| Password dialog tests pass | `python -m pytest tests/ui/test_password_dialog.py -x -q` | 19 passed | PASS |
| Main window tests pass | `python -m pytest tests/ui/test_main_window.py -x -q` | 53 passed | PASS |
| Total: 106 tests | All 4 test suites | 106/106 passed | PASS |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CRYPT-01 | 02, 04 | 新建或另存时输入加密密钥，支持显示/隐藏切换 | SATISFIED | PasswordDialog SET_PASSWORD/CHANGE_PASSWORD modes. Eye toggle via `_add_eye_toggle()`. |
| CRYPT-02 | 02, 04 | 打开时输入密钥解密，错误时显示错误提示 | SATISFIED | PasswordDialog ENTER_PASSWORD mode. `set_error_message()` + while-loop retry. |
| CRYPT-03 | 01, 03 | 保存时加密整体 JSON 写入文件 | SATISFIED | FileService.encrypt() with PBKDF2-SHA256 + AES-256-CFB + HMAC-SHA256. Note: upgraded from REQUIREMENTS.md's "SHA-512" to PBKDF2-SHA256 per design decision D-21 (documented in CONTEXT.md, RESEARCH.md). |
| CRYPT-04 | 02 | 提供密码生成工具 | SATISFIED | PasswordGenerator with secrets module, length 8-128, 4 charsets. |
| FILE-02 | 03, 04 | 打开 .secnote 文件，输入密钥解密加载 | SATISFIED | `_on_open_notebook()` + `_on_open_recent()` with full FileService + PasswordDialog integration. |
| FILE-03 | 03, 04 | 保存笔记本，有路径直接写入，无路径弹出保存对话框 | SATISFIED | `_on_save()` with `_current_path` check, falls through to `_on_save_as()`. |
| FILE-04 | 03, 04 | 另存为新文件，指定新路径和新密钥 | SATISFIED | `_on_save_as()` with CHANGE_PASSWORD dialog. FileService.save_as() generates new salt+IV. |
| FILE-05 | 04 | 关闭时若有未保存更改则提示保存 | SATISFIED | `closeEvent()` with 3-button QMessageBox (save/discard/cancel). |
| UI-03 | — | 富文本格式工具栏 | — | Not a Phase 2 requirement per ROADMAP.md and REQUIREMENTS.md (Phase 6). No plans claim it. |

**Cross-reference note:** UI-03 is assigned to Phase 6 in REQUIREMENTS.md. The user query lists it as a Phase 2 requirement, which appears to be a discrepancy with the canonical REQUIREMENTS.md and ROADMAP.md — neither maps UI-03 to Phase 2.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| None | — | — | No TODO/FIXME/placeholder/stub patterns found in any source file. |

### Human Verification Required

None — all checks are programmatically verifiable.

### Design Notes

1. **SHA-512 vs PBKDF2-SHA256 (CRYPT-03):** REQUIREMENTS.md literal text specifies "SHA-512 派生密钥". The CONTEXT.md D-21 decision explicitly upgrades this to PBKDF2-SHA256 with 600,000 iterations ("超越 CRYPT-03 的纯 SHA-512 要求，增强暴力破解防护"). This is a documented design improvement, not an implementation failure. The RESEARCH.md requirement mapping also documents this upgrade. REQUIREMENTS.md should be updated to reflect this decision.

2. **file_service.py → serializer.py key link:** Plan 03 frontmatter lists this key link, but FileService intentionally does not import Serializer — it operates on plain JSON strings. The Serializer ↔ FileService connection happens through MainWindow (both imported separately). This is documented in Plan 03's context ("FileService 作为纯数据层") and is the correct decoupling.

### Gaps Summary

No gaps found. All 31 truths verified. All 106 tests pass. All 5 ROADMAP success criteria met. All 8 Phase 2 requirements satisfied.

---

_Verified: 2026-05-07T16:00:00Z_
_Verifier: Claude (gsd-verifier)_
