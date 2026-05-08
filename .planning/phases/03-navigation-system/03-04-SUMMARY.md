---
phase: 03-navigation-system
plan: 04
subsystem: navigation
tags: [navigation, crud, context-menu, keyboard-shortcuts, toolbar]
requires: [03-03]
provides: [NAV-03, NAV-04]
affects: [ui/main_window, ui/test_main_window, ui/test_navigation]
tech-stack:
  added: []
  patterns: [context-menu, keyboard-shortcut-dispatch, dirty-flag-management, crud-with-deletion-confirmation]
key-files:
  created:
    - tests/ui/test_navigation.py
  modified:
    - src/secnotadata/ui/main_window.py
    - tests/ui/test_main_window.py
decisions: []
metrics:
  duration: ~30m
  completed: "2026-05-08T04:35:00Z"
---

# Phase 03 Plan 04: 导航系统 CRUD 交互实现总结

**一行总结：** 在 MainWindow 中实现分区和页面的完整 CRUD 交互——工具栏按钮创建、右键菜单、键盘快捷键分发、含子内容删除确认对话框

## Commits

| 序号 | Hash    | 类型 | 说明                                                 |
|------|---------|------|------------------------------------------------------|
| 1    | 7b4acda | feat | 添加工具栏按钮、上下文菜单、键盘快捷键                  |
| 2    | ed6b4b4 | feat | 实现 CRUD handler、工具栏按钮信号连接、删除确认对话框    |
| 3    | 795f25d | test | 导航 CRUD 集成测试（16 个测试），修复布局变更后的旧测试  |

## 完成的需求 (Must-Haves)

- [x] 用户可通过工具栏按钮创建分区/子分区/页面 (D-55)
- [x] 右键分区树节点显示上下文菜单 (D-56)
- [x] 右键页面列表节点显示上下文菜单 (D-56)
- [x] 右键空白区域显示新建选项 (D-56)
- [x] 按 Delete 键根据焦点视图删除 (D-57)
- [x] 按 F2 键进入重命名模式 (D-57)
- [x] Ctrl+N 新建页面（仅页面列表聚焦时）(D-57)
- [x] 删除含子内容分区时弹出警告对话框 (D-58)
- [x] 删除空分区或单页面时不弹确认 (D-58)
- [x] 所有创建/删除操作后调用 mark_dirty() (D-61)
- [x] 新建页面后自动选中 (D-64)
- [x] 删除当前分区后 PageListModel 清空 (Pitfall 7)
- [x] 集成测试 16 个全部通过
- [x] 全部已有测试 266 个无回归

## 关键实现决策

1. **容器包装方案：** 每个面板（分区树 / 页面列表）用 QWidget 容器包装，QVBoxLayout 布局按钮栏在上、视图在下。按钮栏使用 QFrame+QHBoxLayout 实现水平排列。

2. **上下文感知快捷键分发：** Delete 和 F2 通过 `self.focusWidget()` 判断当前焦点视图，分发给对应的 `_on_delete_section`/`_on_delete_page` 或 `_on_rename_section`/`_on_rename_page`。

3. **删除确认策略：** 仅删除含子内容的分区时弹出 QMessageBox.warning，空分区或单页面直接删除。删除当前选中的分区后主动清空 PageListModel（Pitfall 7）。

4. **脏标志触发点：** `_on_new_root_section`、`_on_new_child_section`、`_on_delete_section`、`_on_new_page`、`_on_delete_page` 中调用 `self.mark_dirty()`。重命名操作通过模型 `setData` 的内联编辑完成，重命名 handler 仅触发编辑模式。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 布局变更导致旧测试失败**
- **发现于：** Task 3 执行前
- **问题：** `_setup_central_area` 中将 QTreeView/QListView 包装进容器 QWidget 后，splitter.widget(0)/widget(1) 不再是 QTreeView/QListView 实例
- **修复：** 更新 `test_tree_view_exists` 和 `test_list_view_exists` 使用 `findChild()` 在容器内查找对应控件
- **修改文件：** `tests/ui/test_main_window.py`
- **提交：** 795f25d

**2. [Rule 1 - Bug] 新笔记本无子分区导致页面 CRUD 测试失败**
- **发现于：** Task 3 执行中
- **问题：** `_on_new_notebook` 创建的根分区无子分区，`_page_list_model._section` 为 None，导致 `_on_new_page` 静默返回
- **修复：** 在 `test_new_page_in_current_section`、`test_new_page_sets_dirty`、`test_delete_page` 中先调用 `_on_new_root_section()` 确保存在选中分区
- **修改文件：** `tests/ui/test_navigation.py`
- **提交：** 795f25d

## 验证结果

- 语法导入: `python -c "from src.secnotepad.ui.main_window import MainWindow"` — 通过
- 导航集成测试: `python -m pytest tests/ui/test_navigation.py -x` — 16/16 通过
- 完整回归测试: `python -m pytest tests/ -x` — 266/266 通过

## 威胁模型审查

| 威胁 ID   | 处置     | 实施状态                           |
|-----------|----------|-----------------------------------|
| T-03-04   | mitigate | `_on_delete_section` 中已实现 Pitfall 7 检查 |
| T-03-05   | accept   | 桌面单用户应用，Qt 单线程事件循环序列化  |
| T-03-06   | accept   | 分区名称在确认对话框中显示——设计意图   |

## Self-Check: PASSED

- [x] `src/secnotepad/ui/main_window.py` — 已修改，存在
- [x] `tests/ui/test_navigation.py` — 已创建，存在
- [x] `tests/ui/test_main_window.py` — 已修改，存在
- [x] Commit 7b4acda: `git log --oneline --all | grep 7b4acda` — 存在
- [x] Commit ed6b4b4: `git log --oneline --all | grep ed6b4b4` — 存在
- [x] Commit 795f25d: `git log --oneline --all | grep 795f25d` — 存在
- [x] 266 tests pass
