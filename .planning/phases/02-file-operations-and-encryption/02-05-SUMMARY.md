---
phase: 02-file-operations-and-encryption
plan: 05
type: gap_closure
subsystem: ui
tags: [recent-files, QSettings, welcome-page, gap-closure]
requires:
  - 02-04 (MainWindow file lifecycle, WelcomeWidget recent file interaction, QSettings persistence)
provides:
  - Welcome page recent files list populated on startup
  - Recent files list updated after save to existing path
affects:
  - src/secnotepad/ui/main_window.py
  - tests/ui/test_main_window.py
tech-stack:
  added: []
  patterns:
    - _load_recent_files() called in __init__ to populate welcome page on startup
    - _add_recent_file() called in _on_save() existing-path branch to keep recent list current
key-files:
  created: []
  modified:
    - src/secnotepad/ui/main_window.py (+4 lines, in __init__ and _on_save)
    - tests/ui/test_main_window.py (+44 lines, 2 new tests)
decisions:
  - __init__ 末尾调用 _load_recent_files() 后传入 WelcomeWidget.set_recent_files() —— 与 _on_new_notebook() 末尾的模式一致
  - _on_save() 已有路径分支末尾调用 _add_recent_file() —— 与 _on_save_as() 和 _on_open_notebook() 的模式一致
requirements-completed: [FILE-03, FILE-05]
metrics:
  duration_minutes: null
  completed: 2026-05-08
  test_count: 201 (all passing, +2 new tests)
---

# Phase 02 Plan 05: 修复欢迎页最近文件列表为空

## One-liner

修复启动时未从 QSettings 加载最近文件和保存到已有路径时不更新列表两个缺失，欢迎页最近文件列表现在正确显示历史文件。

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-08
- **Completed:** 2026-05-08
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- `MainWindow.__init__()` 末尾调用 `_load_recent_files()` 并将结果通过 `set_recent_files()` 传入欢迎页
- `_on_save()` 已有路径分支末尾调用 `_add_recent_file()` 更新最近文件列表
- 新增 2 个测试覆盖两个修复场景

## Task Commits

1. **Task 1: 修复 __init__() 和 _on_save() 中最近文件加载缺失** - `31f57e1` (fix)

## Files Created/Modified
- `src/secnotepad/ui/main_window.py` - __init__ 末尾加载最近文件；_on_save 已有路径分支更新列表
- `tests/ui/test_main_window.py` - test_init_loads_recent_files + test_on_save_adds_recent_file

## Decisions Made
None - 严格遵循诊断结果和计划指定的修复方案

## Deviations from Plan

None - 计划执行完全符合预期

## Issues Encountered
None

## Next Phase Readiness
- 欢迎页最近文件列表 gap 已关闭，Phase 2 文件操作功能完整
- 201 个测试全部通过，无回归

---
*Phase: 02-file-operations-and-encryption*
*Plan: 05 - gap closure*
*Completed: 2026-05-08*
