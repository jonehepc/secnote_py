---
phase: 03-navigation-system
plan: 06
subsystem: ui
tags: [pyside6, navigation, idempotency, dirty-state]
requires:
  - phase: 03-navigation-system
    provides: 03-05 page-list Ctrl+N shortcut
provides:
  - 幂等的导航重复初始化清理
  - 分区和页面原地重命名置脏
  - 新建子分区后自动选中新子分区
affects: [navigation, ui-signals, dirty-state]
tech-stack:
  added: []
  patterns: [navigation teardown before setup, model dataChanged to dirty-state]
key-files:
  created:
    - .planning/phases/03-navigation-system/03-06-SUMMARY.md
  modified:
    - src/secnotepad/ui/main_window.py
    - tests/ui/test_navigation.py
key-decisions:
  - "重复 `_setup_navigation()` 时先执行 `_teardown_navigation()`，集中清理 selection、按钮、右键菜单、action、QShortcut 和 dataChanged 绑定。"
  - "将 TreeModel/PageListModel 的 dataChanged 接到 `_on_structure_data_changed()`，覆盖原地编辑路径的 dirty 状态。"
patterns-established:
  - "Qt 模型重命名造成的数据变更由 MainWindow 统一监听 dataChanged 并调用 mark_dirty。"
requirements-completed: [NAV-03, NAV-04]
duration: unknown
completed: 2026-05-09
---

# Phase 03: Navigation System Plan 06 Summary

**导航重复初始化、原地重命名置脏和新建子分区自动选中缺口已集中关闭。**

## Performance

- **Duration:** unknown
- **Started:** 2026-05-09
- **Completed:** 2026-05-09
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- [main_window.py](../../../src/secnotepad/ui/main_window.py) 的 `_setup_navigation()` 已在重复初始化前调用 `_teardown_navigation()`。
- `_teardown_navigation()` 清理选择模型、按钮、右键菜单、Delete/F2 action、页面 Ctrl+N shortcut 和模型 dataChanged 连接。
- `TreeModel.dataChanged` 与 `PageListModel.dataChanged` 接入 `_on_structure_data_changed()`，原地重命名后调用 `mark_dirty()`。
- 新建子分区后通过 proxy parent 定位新增 child index，并调用 `setCurrentIndex()` / `scrollTo()`。
- [test_navigation.py](../../../tests/ui/test_navigation.py) 覆盖重复初始化、重命名置脏、新建子分区自动选中以及 Ctrl+N 快捷键回归。

## Task Commits

执行器提交将在本 SUMMARY 与实现一起提交。

## Files Created/Modified

- [main_window.py](../../../src/secnotepad/ui/main_window.py) - 导航 teardown、dataChanged dirty wiring、子分区选中、Ctrl+N 清理。
- [test_navigation.py](../../../tests/ui/test_navigation.py) - gap closure 回归测试。

## Decisions Made

- 保持已有 CRUD handler 结构，只补齐信号生命周期和 dirty-state 接线，避免重写导航系统。

## Deviations from Plan

- 测试环境缺少 pytest，无法执行计划中的 pytest 命令；已执行 `python3 -m compileall src tests` 验证语法。
- 当前工作树在开始执行前已有 page list model 和相关测试改动，本计划未回滚这些用户/前序未提交改动。

## Issues Encountered

- `python` 命令不存在，`python3` 与两个虚拟环境均缺少 pytest 模块。

## User Setup Required

- 安装测试依赖后运行：`QT_QPA_PLATFORM=offscreen python -m pytest tests/ui/test_navigation.py tests/model/test_tree_model.py tests/model/test_page_list_model.py -x --timeout=30`。

## Next Phase Readiness

- Phase 03 可进入代码审查和 verifier 复核；若环境补齐 pytest，应先运行完整测试套件。

---
*Phase: 03-navigation-system*
*Completed: 2026-05-09*
