---
phase: 03-navigation-system
reviewed: 2026-05-09T03:57:04Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - src/secnotepad/model/page_list_model.py
  - src/secnotepad/model/tree_model.py
  - src/secnotepad/ui/main_window.py
  - tests/model/test_page_list_model.py
  - tests/ui/test_main_window.py
  - tests/ui/test_navigation.py
findings:
  critical: 1
  warning: 3
  info: 0
  total: 4
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-09T03:57:04Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

本次按 standard 深度复核了 Phase 03 navigation-system 的 6 个指定文件，并重点追踪上一轮 findings 的修复状态：

- Ctrl+N 的重复注册问题已从“菜单 QAction + 页面 QShortcut 双重抢占”改成单一 `QShortcut` 分发，但当前 shortcut 只在导航初始化后创建，欢迎页/未打开笔记本状态下 `Ctrl+N` 不再可用，仍不满足“其他焦点下新建笔记本”的完整行为。
- Delete/F2 的实现已设置 `Qt.WidgetWithChildrenShortcut`，从代码路径看不会再拦截右侧 `QTextEdit`；但测试未覆盖该回归场景。
- 分区/页面重命名相同标题已通过 `setData()` 返回 `False` 避免置脏。
- placeholder 路径已屏蔽 `QTextEdit.clear()` 信号，不会清空当前 `note.content`。
- 页面右键菜单已从非阻塞 `popup()` 改成阻塞 `exec()`，修复了“局部菜单提前销毁/闪退”的主要生命周期问题；但仍使用 `QMenu(self)` 且未释放，会在重复打开菜单时累积 QObject 子对象。
- 测试覆盖了部分重点行为，但仍缺少 `Ctrl+N` 非页面列表/欢迎页分发，以及 `QTextEdit` 中 Delete/F2 不被吞掉的负向测试。

## Critical Issues

### CR-01: BLOCKER — Ctrl+N 分发器只在导航初始化后注册，欢迎页/未打开笔记本时快捷键失效

**File:** `src/secnotepad/ui/main_window.py:86-87, 533-558, 849-873`

**Issue:** `_act_new` 已移除 `Ctrl+N` 快捷键，这是避免重复 shortcut 的正确方向；但唯一的 `QShortcut(QKeySequence("Ctrl+N"), self)` 只在 `_setup_navigation_shortcuts()` 中创建，而该方法仅由 `_setup_navigation()` 调用。也就是说，在应用启动后的欢迎页（尚未新建/打开任何笔记本）没有任何 `Ctrl+N` 绑定，用户按 `Ctrl+N` 不会新建笔记本。这违反了本轮重点复核要求中“页面列表焦点下新建页面、其他焦点下新建笔记本”的行为：未进入导航系统时也属于“其他焦点/无页面列表焦点”，应走新建笔记本分支。

**Fix:** 将单一 Ctrl+N dispatcher 的生命周期提升到窗口生命周期，只创建一次，不随 `_setup_navigation()` / `_teardown_navigation()` 重建或删除。`_on_ctrl_n()` 已能在 `_navigation_initialized == False` 时落到 `_on_new_notebook()`，因此可以直接复用。

```python
# __init__ 中在 _setup_central_area() 之后、_connect_actions() 之前/之后均可
self._shortcut_ctrl_n = QShortcut(QKeySequence("Ctrl+N"), self)
self._shortcut_ctrl_n.setContext(Qt.WindowShortcut)
self._shortcut_ctrl_n.activated.connect(self._on_ctrl_n)

# _setup_navigation_shortcuts() 不再创建 Ctrl+N，只保留 Delete/F2
# _teardown_navigation() 不要 deleteLater() 这个窗口级 Ctrl+N dispatcher
```

同时增加回归测试：新建任何笔记本前在欢迎页按 `Ctrl+N` 应调用 `_on_new_notebook()` 并切换到三栏布局；导航已初始化但焦点在编辑器/树/窗口其它区域时按 `Ctrl+N` 应新建笔记本；页面列表焦点下仍只新建页面。

## Warnings

### WR-01: WARNING — 测试未覆盖 Delete/F2 不拦截 QTextEdit，也未覆盖 Ctrl+N 的非页面列表分支

**File:** `tests/ui/test_navigation.py:183-199, 285-290`

**Issue:** 现有测试只验证“页面列表聚焦时 Ctrl+N 新建页面”和“存在窗口级 Ctrl+N shortcut”，没有验证欢迎页/编辑器/树等其它焦点下 `Ctrl+N` 会新建笔记本，也没有验证右侧 `QTextEdit` 中 Delete/F2 不会被导航 QAction 消费。上一轮 review 的关键风险正是 shortcut 作用域和焦点分发；缺少这些负向测试会让当前 CR-01 这类回归继续漏检，也无法证明 Delete/F2 对正文编辑器安全。

**Fix:** 增加面向真实按键的测试，而不仅检查 shortcut 属性。例如：

```python
def test_ctrl_n_creates_notebook_before_navigation(window):
    QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)
    assert window._stack.currentIndex() == 1
    assert window._root_item is not None


def test_delete_key_edits_textedit_not_navigation(window_with_notebook):
    window_with_notebook._on_new_root_section()
    window_with_notebook._on_new_page()
    editor = window_with_notebook._editor_preview
    editor.setPlainText("abc")
    editor.setFocus()
    cursor = editor.textCursor()
    cursor.setPosition(1)
    editor.setTextCursor(cursor)

    QTest.keyClick(editor, Qt.Key_Delete)

    assert editor.toPlainText() == "ac"
    assert window_with_notebook._page_list_model.rowCount() == 1
```

### WR-02: WARNING — PageListModel.rowCount 对有效 parent 仍返回顶层数量，违反扁平 list model 契约

**File:** `src/secnotepad/model/page_list_model.py:45-50`

**Issue:** `PageListModel` 是扁平 `QAbstractListModel`，当 Qt 以某个有效 item index 作为 `parent` 查询子行数时应返回 `0`。当前实现无条件返回 `len(self._notes)`，会让模型声称每个列表项下面还有同样数量的子项，违反 Qt model contract。虽然 `QListView` 通常只展示顶层行，但代理模型、测试工具或后续复用该 model 的视图可能依赖该契约，导致错误的层级结构判断。

**Fix:** 按 Qt 约定对有效 parent 返回 0，并补充测试覆盖。

```python
def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
    if parent.isValid():
        return 0
    return len(self._notes)
```

### WR-03: WARNING — 页面右键菜单使用 MainWindow 作为 parent 且未释放，重复打开会累积 QMenu 子对象

**File:** `src/secnotepad/ui/main_window.py:519-531`

**Issue:** 页面右键菜单已经改为 `menu.exec(...)`，修复了上一轮指出的非阻塞 `popup()` 生命周期问题；但 `QMenu(self)` 会把每次创建的菜单挂到 `MainWindow` 的 QObject 子树上，函数返回后并不会自动从 parent 下移除。用户多次打开页面右键菜单会累积菜单和 action 对象，属于仍未收口的菜单生命周期缺陷。树菜单也有相同模式，但本轮重点要求复核页面右键菜单生命周期，因此这里针对页面菜单给出修复。

**Fix:** 使用无 parent 的局部菜单，或在 `exec()` 返回后显式释放；如果需要 parent 管理，则保存单例菜单并复用/清空 action。

```python
def _on_page_context_menu(self, pos):
    from PySide6.QtWidgets import QMenu
    menu = QMenu()
    try:
        index = self._list_view.indexAt(pos)
        if index.isValid():
            self._list_view.setCurrentIndex(index)
            menu.addAction("重命名页面", self._on_rename_page)
            menu.addAction("删除页面", self._on_delete_page)
        else:
            menu.addAction("新建页面", self._on_new_page)
        menu.exec(self._list_view.viewport().mapToGlobal(pos))
    finally:
        menu.deleteLater()
```

---

_Reviewed: 2026-05-09T03:57:04Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
