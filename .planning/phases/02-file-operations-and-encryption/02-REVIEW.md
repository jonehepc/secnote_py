---
phase: 02-file-operations-and-encryption
reviewed: 2026-05-08T00:00:00Z
depth: quick
files_reviewed: 2
files_reviewed_list:
  - src/secnotepad/ui/main_window.py
  - tests/ui/test_main_window.py
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: issues_found
---

# Phase 02: Code Review Report (Quick -- Recent Changes)

**Reviewed:** 2026-05-08
**Depth:** quick (pattern-matching only)
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Targeted quick review of the recent changes (commit 31f57e1) which added: (1) loading recent files from QSettings into WelcomeWidget during `MainWindow.__init__()`, (2) calling `_add_recent_file()` in `_on_save()` after a successful save, and (3) corresponding tests. No critical issues or warnings found. One minor inconsistency in `_load_recent_files()`.

**Pattern-matching scan results:**
- **Hardcoded secrets:** `"testpw"` found in test file line 401 -- benign, test-only fixture value
- **Dangerous functions:** All `exec()` hits are standard PySide6 `QDialog.exec()` / `QMessageBox.exec()` calls, not code-execution `exec()`
- **Debug artifacts:** None found
- **Empty catch blocks:** None found
- **Commented-out code:** None found

## Info

### IN-01: `_load_recent_files()` does not enforce `MAX_RECENT_FILES` limit

**File:** `src/secnotepad/ui/main_window.py:453-468`
**Issue:** `_load_recent_files()` returns all valid (existing) file paths from QSettings without truncating to `MAX_RECENT_FILES = 5`. The companion method `_add_recent_file()` correctly truncates at line 485 (`paths = paths[:self.MAX_RECENT_FILES]`). If QSettings contains more than 5 entries and all referenced files exist on disk, `WelcomeWidget.set_recent_files()` will receive more than 5 items on initialization. While `_add_recent_file()` and `_remove_recent_file()` both truncate and write back, the load side does not guard against pre-existing QSettings data with excess entries (e.g., from a future MAX_RECENT_FILES reduction, manual edits, or a corrupted settings file).

**Fix:** Add a truncation step in `_load_recent_files()` after filtering:
```python
valid = [p for p in paths if isinstance(p, str) and os.path.isfile(p)]
valid = valid[:self.MAX_RECENT_FILES]   # enforce D-40 maximum
if len(valid) < len(paths):
    settings.setValue(self.SETTINGS_KEY, valid)
return valid
```

---

_Reviewed: 2026-05-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
