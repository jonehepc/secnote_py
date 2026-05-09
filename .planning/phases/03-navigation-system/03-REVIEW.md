---
phase: 03-navigation-system
reviewed: 2026-05-09T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/secnotepad/model/page_list_model.py
  - src/secnotepad/ui/main_window.py
  - tests/model/test_page_list_model.py
  - tests/ui/test_main_window.py
  - tests/ui/test_navigation.py
findings:
  critical: 1
  warning: 4
  info: 1
  total: 6
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-05-09T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

本次按 standard 深度审查了导航系统相关的 5 个文件，重点检查 PySide6 signal/shortcut 生命周期、`_setup_navigation()` 重复初始化、页面列表 `Ctrl+N` 与主窗口 `Ctrl+N` 冲突、rename 脏状态，以及测试是否真实覆盖交互行为。

当前实现仍存在一个必须修复的快捷键冲突：页面列表新增页面的 `Ctrl+N` 与主窗口“新建笔记本”的 `Ctrl+N` 同时处于活动范围，Qt 可能将该快捷键判为 ambiguous，或触发错误的新建笔记本动作。另有 Delete/F2 shortcut 作用域过大、无变化 rename 仍置脏、placeholder 清空编辑器信号未屏蔽、页面右键菜单生命周期，以及测试覆盖不足等问题。

## Critical Issues

### CR-01: BLOCKER — 页面列表 Ctrl+N 与主窗口 Ctrl+N 同时生效，可能 ambiguous 或触发错误动作

**File:** `src/secnotepad/ui/main_window.py:86-88, 550-553`

**Issue:** 主窗口 `_act_new` 使用 `Ctrl+N` 作为“新建笔记本”快捷键；导航初始化又在 `_list_view` 上创建同样为 `Ctrl+N` 的 `QShortcut` 用于“新建页面”。`Qt.WidgetShortcut` 只限制页面快捷键的生效范围，但不会自动禁用窗口级 QAction 的 `Ctrl+N`；当焦点在页面列表中时，页面 `QShortcut` 和主窗口 QAction 都可能匹配同一按键。Qt 对重复快捷键可能发出 ambiguous shortcut，导致页面无法创建；也可能触发“新建笔记本”，在当前笔记本干净时直接替换会话，行为与用户在页面列表中按 `Ctrl+N` 的意图相反。

**Fix:** 不要注册两个相同 key sequence。保留菜单/工具栏点击行为，改用单一键盘 shortcut 做上下文分发；或为“新建页面”改用不冲突快捷键。示例修复：

```python
# _setup_menu_bar: 不把 Ctrl+N 直接挂在“新建笔记本” QAction 上，避免与页面快捷键重复
self._act_new = QAction("新建(&N)", self)
file_menu.addAction(self._act_new)

# __init__ 或 _setup_navigation_shortcuts 中只创建一个窗口级 Ctrl+N shortcut
self._shortcut_ctrl_n = QShortcut(QKeySequence("Ctrl+N"), self)
self._shortcut_ctrl_n.setContext(Qt.WindowShortcut)
self._shortcut_ctrl_n.activated.connect(self._on_ctrl_n)

def _on_ctrl_n(self):
    focused = self.focusWidget()
    if (
        self._navigation_initialized
        and (focused is self._list_view or self._list_view.isAncestorOf(focused))
        and self._page_list_model is not None
        and self._page_list_model._section is not None
    ):
        self._on_new_page()
    else:
        self._on_new_notebook()
```

同时增加测试：在页面列表聚焦时监听 `_act_new.triggered` 不应触发，并验证没有 `activatedAmbiguously`；在非页面列表聚焦时 `Ctrl+N` 仍执行新建笔记本。

## Warnings

### WR-01: WARNING — Delete/F2 QAction 默认 WindowShortcut 会拦截编辑器按键，且焦点判断过窄

**File:** `src/secnotepad/ui/main_window.py:536-548, 696-710`

**Issue:** `_act_delete` 和 `_act_rename` 被添加到 tree/list view，但未设置 shortcut context；QAction 默认是 `Qt.WindowShortcut`，因此只要主窗口激活，Delete/F2 都可能被 QAction shortcut map 捕获。焦点在右侧 `QTextEdit` 时按 Delete 可能先触发 `_on_delete_selected()`，该方法因 `focusWidget()` 不是 `_list_view`/`_tree_view` 而 no-op，但按键已被 shortcut 消费，文本编辑器无法正常删除字符。此外，QAbstractItemView 的实际焦点有时在 viewport/子控件上，`focused is self._list_view` 的精确比较也可能让列表/树中 Delete/F2 不生效。

**Fix:** 将导航快捷键限制在对应视图及其子控件，或为 tree/list 分别创建 QAction；dispatch 时使用 `hasFocus()` / `isAncestorOf()` 判断。示例：

```python
self._act_delete.setShortcutContext(Qt.WidgetWithChildrenShortcut)
self._act_rename.setShortcutContext(Qt.WidgetWithChildrenShortcut)

def _focus_in(self, widget):
    focused = self.focusWidget()
    return focused is widget or widget.isAncestorOf(focused)

def _on_delete_selected(self):
    if self._focus_in(self._list_view):
        self._on_delete_page()
    elif self._focus_in(self._tree_view):
        self._on_delete_section()
```

更稳妥的做法是为 tree view 和 list view 创建独立 QAction，避免同一个 QAction 同时挂在两个 widget 上造成上下文难以推断。

### WR-02: WARNING — 页面重命名为相同标题也会发出 dataChanged 并置脏

**File:** `src/secnotepad/model/page_list_model.py:102-104`

**Issue:** `PageListModel.setData()` 只校验非空字符串，然后无条件执行 `note.title = value.strip()` 并发出 `dataChanged`。当用户进入原地重命名后未修改标题直接提交，模型没有真实变化，但仍发出 `dataChanged`。`MainWindow._setup_navigation()` 将 `_page_list_model.dataChanged` 连接到 `_on_structure_data_changed()`，因此无变化 rename 也会把笔记本标记为 dirty，导致不必要的保存提示和文件重写。

**Fix:** 在 setData 内比较规范化后的新旧标题，只有真实变化时才修改模型和发信号。分区标题的 `TreeModel.setData()` 也应采用相同规则，否则分区原地重命名仍会误置脏。

```python
new_title = value.strip()
if note.title == new_title:
    return False

note.title = new_title
self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
return True
```

并补充测试：`setData(idx, 当前标题, Qt.EditRole)` 应返回 `False`、不发 `dataChanged`、窗口不进入 dirty 状态。

### WR-03: WARNING — placeholder 清空编辑器时未屏蔽 textChanged，存在误写当前页面内容的风险

**File:** `src/secnotepad/ui/main_window.py:447-450`

**Issue:** `_show_editor_placeholder()` 调用 `self._editor_preview.clear()` 后才切换 stack 到 placeholder。`QTextEdit.clear()` 会发出 `textChanged`；如果调用该方法时编辑器仍处于 index 0 且页面列表 current index 仍有效，`_on_editor_text_changed()` 会把当前页面 `note.content` 写成空 HTML 并标记 dirty。`_show_note_in_editor()` 已经通过 `blockSignals(True)` 处理程序化内容加载，但 placeholder 路径没有同样保护，后续任何从“有页面选中”状态切到 placeholder 的路径都可能引入正文清空风险。

**Fix:** 程序化清空编辑器时屏蔽信号，并先切换到 placeholder 状态或显式清除页面选择，确保 `_on_editor_text_changed()` 不会把 UI 清空同步回模型。

```python
def _show_editor_placeholder(self):
    self._editor_stack.setCurrentIndex(1)
    self._editor_preview.blockSignals(True)
    try:
        self._editor_preview.clear()
    finally:
        self._editor_preview.blockSignals(False)
```

同时增加回归测试：选中含正文页面后调用会进入 placeholder 的真实交互路径，断言 `note.content` 保持不变且不会仅因 placeholder 切换而置脏。

### WR-04: WARNING — 页面右键菜单使用局部 QMenu.popup()，菜单生命周期和测试覆盖都不可靠

**File:** `src/secnotepad/ui/main_window.py:517-529`

**Issue:** `_on_page_context_menu()` 创建局部 `QMenu(self)` 后调用非阻塞 `menu.popup(...)` 并立即返回。PySide 中非阻塞 popup 需要确保菜单对象在用户点击前仍然存活；局部 Python wrapper 在函数返回后可能被回收，导致菜单闪退或 action 不可触发。树右键菜单使用阻塞的 `menu.exec(...)`，不存在同样生命周期问题。现有测试只 monkeypatch `QMenu.popup` 读取 action 文本，并没有验证真实菜单可见、可点击或 action 能执行，因此无法覆盖该生命周期缺陷。

**Fix:** 与树菜单保持一致使用 `exec()`，或把菜单保存到实例属性直到 `aboutToHide` 后释放。

```python
self._page_context_menu = QMenu(self)
menu = self._page_context_menu
# add actions...
menu.exec(self._list_view.viewport().mapToGlobal(pos))
```

若继续使用 `popup()`，应连接 `aboutToHide` 清理实例引用，并增加能触发 action 的测试，而不仅检查 action 文本。

## Info

### IN-01: INFO — 幂等性和脏状态测试多为状态快照，未验证 signal 次数和 ambiguous shortcut

**File:** `tests/ui/test_navigation.py:118-141, 251-273, 269-273`

**Issue:** 多个测试名声称验证“不会重复绑定”或“只标记一次”，但断言只检查最终 rowCount 或 `_is_dirty is True`。`mark_dirty()` 本身是幂等的，重复 dataChanged 连接也会得到同样最终布尔值，因此这些测试不能证明 signal 只连接一次。`test_ctrl_n_shortcut_is_scoped_to_page_list()` 也只检查 QShortcut parent/context，没有监听主窗口 `_act_new` 是否同时触发，也没有检查 `activatedAmbiguously`。

**Fix:** 使用 `QSignalSpy` 或临时计数器验证 handler 调用次数；对 Ctrl+N 增加负向断言（页面列表聚焦时 `_act_new.triggered` 次数为 0，页面 QShortcut 不发 `activatedAmbiguously`），并覆盖“重命名为相同标题不置脏”的场景。

---

_Reviewed: 2026-05-09T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
