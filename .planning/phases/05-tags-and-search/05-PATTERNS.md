# Phase 05: 标签与搜索 - Pattern Map

**Mapped:** 2026-05-11  
**Files analyzed:** 9  
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/secnotepad/model/search_service.py` | service / utility | batch + transform | `src/secnotepad/model/tree_model.py` + `src/secnotepad/model/serializer.py` | partial |
| `src/secnotepad/ui/tag_bar_widget.py` | component | event-driven | `src/secnotepad/ui/rich_text_editor.py` | exact |
| `src/secnotepad/ui/search_dialog.py` | component / dialog | request-response + event-driven | `src/secnotepad/ui/password_dialog.py` | role-match |
| `src/secnotepad/ui/main_window.py` | controller / provider | event-driven + request-response | `src/secnotepad/ui/main_window.py` | exact |
| `tests/model/test_search_service.py` | test | batch + transform | `tests/model/test_tree_model.py` + `tests/model/test_page_list_model.py` | role-match |
| `tests/ui/test_tag_bar_widget.py` | test | event-driven | `tests/ui/test_rich_text_editor.py` | exact |
| `tests/ui/test_search_dialog.py` | test | request-response + event-driven | `tests/ui/test_password_dialog.py` | role-match |
| `tests/ui/test_main_window_tags.py` | test | event-driven | `tests/ui/test_navigation.py` | exact |
| `tests/ui/test_main_window_search.py` | test | event-driven + request-response | `tests/ui/test_navigation.py` | exact |

## Pattern Assignments

### `src/secnotepad/model/search_service.py` (service / utility, batch + transform)

**Analog:** `src/secnotepad/model/tree_model.py` + `src/secnotepad/model/serializer.py`

**Imports pattern** — 纯模型层仅依赖 QtCore 或 dataclass/标准库，避免 UI widget 依赖；若需要 HTML 转纯文本，可只引入 `PySide6.QtGui.QTextDocumentFragment`。

Source: `src/secnotepad/model/tree_model.py` lines 7-10:
```python
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt

from .snote_item import SNoteItem
```

Source: `src/secnotepad/model/serializer.py` lines 8-11:
```python
import json
from dataclasses import asdict

from .snote_item import SNoteItem
```

**树遍历 pattern** — 搜索服务遍历整棵 `SNoteItem` 树时复制递归 helper 的引用比较和递归写法；结果中保留 note 对象或 note id，并记录父分区路径。

Source: `src/secnotepad/model/tree_model.py` lines 116-130:
```python
@staticmethod
def _find_parent(root: SNoteItem, target: SNoteItem):
    """在树中递归查找 target 的父节点。

    使用引用比较（is），而非值比较。
    对于少量节点（< 10000）性能可接受。
    返回父节点 SNoteItem，未找到时返回 None。
    """
    for child in root.children:
        if child is target:
            return root
        found = TreeModel._find_parent(child, target)
        if found:
            return found
    return None
```

**纯转换 / 错误处理 pattern** — 服务方法应像 serializer 一样：输入无效时显式返回空结果或抛出明确异常；不要弹窗、不要修改 UI。

Source: `src/secnotepad/model/serializer.py` lines 37-61:
```python
@staticmethod
def from_json(json_str: str) -> SNoteItem:
    """JSON 字符串 → SNoteItem 树。

    Raises:
        ValueError: 如果 JSON 格式无效、缺少必填字段或版本不兼容。
    """
    try:
        document = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e
    if not isinstance(document, dict):
        raise ValueError("JSON root must be an object")
    version = document.get("version", 1)
    if version > Serializer.FORMAT_VERSION:
        raise ValueError(
            f"Unsupported format version {version}; "
            f"expected <= {Serializer.FORMAT_VERSION}"
        )
    if "data" not in document:
        raise ValueError("Missing required 'data' field")
    data = document["data"]
    for key in ("id", "title", "item_type"):
        if key not in data:
            raise ValueError(f"Missing required field '{key}' in SNoteItem data")
    return Serializer._from_dict(data)
```

**数据边界 pattern** — `tags` 已在 `SNoteItem` 中，搜索服务直接读字段，不新增数据库、索引或外部文件。

Source: `src/secnotepad/model/snote_item.py` lines 28-35:
```python
id: str = ""
title: str = ""
item_type: str = "note"  # "section" | "note"
content: str = ""
children: List["SNoteItem"] = field(default_factory=list)
tags: List[str] = field(default_factory=list)
created_at: str = ""
updated_at: str = ""
```

---

### `src/secnotepad/ui/tag_bar_widget.py` (component, event-driven)

**Analog:** `src/secnotepad/ui/rich_text_editor.py`

**Imports pattern** — UI component 使用 `Signal` 声明事件，Qt Widgets 在同一 import block 内分组。

Source: `src/secnotepad/ui/rich_text_editor.py` lines 5-11:
```python
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont,
                            QTextBlockFormat, QTextCharFormat, QTextCursor,
                            QTextDocumentFragment, QTextListFormat)
from PySide6.QtWidgets import (QApplication, QColorDialog, QComboBox,
                                QFontComboBox, QStyle, QTextEdit, QToolBar,
                                QVBoxLayout, QWidget)
```

**Signal pattern** — `TagBarWidget` 应声明 `tag_added = Signal(str)` / `tag_removed = Signal(str)`，只发出意图，不直接调用 `MainWindow.mark_dirty()`。

Source: `src/secnotepad/ui/rich_text_editor.py` lines 58-67:
```python
class RichTextEditorWidget(QWidget):
    """Composite rich text editor with local formatting toolbar."""

    content_changed = Signal(str)
    paste_sanitized = Signal()
    status_message_requested = Signal(str)
    undo_available_changed = Signal(bool)
    redo_available_changed = Signal(bool)
    copy_available_changed = Signal(bool)
```

**布局 pattern** — 组件内部创建 layout，设置 margin/spacing，然后添加控件；标签 chip 行应沿用该风格。

Source: `src/secnotepad/ui/rich_text_editor.py` lines 70-89:
```python
def __init__(self, parent=None):
    super().__init__(parent)
    self._status_callback: Callable[[str], None] | None = None
    self._syncing_toolbar = False
    self._zoom_steps = 0

    layout = QVBoxLayout(self)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)

    self._format_toolbar = QToolBar("格式工具栏", self)
    self._format_toolbar.setMovable(False)
    layout.addWidget(self._format_toolbar)

    self._editor = SafeRichTextEdit(self)
    self._editor.setReadOnly(False)
    layout.addWidget(self._editor)

    self._setup_toolbar()
    self._connect_editor_signals()
```

**启用/禁用 pattern** — 未选中页面时标签栏应像富文本工具栏一样整体禁用；不要让 widget 自己猜测当前页面状态。

Source: `src/secnotepad/ui/rich_text_editor.py` lines 99-103:
```python
def set_editor_enabled(self, enabled: bool) -> None:
    """Enable or disable both the toolbar and text editor."""
    self._format_toolbar.setEnabled(enabled)
    self._editor.setEnabled(enabled)
```

**事件连接 pattern** — 将 UI 信号集中在 `_connect_*_signals()` 中，便于测试和避免重复连接。

Source: `src/secnotepad/ui/rich_text_editor.py` lines 261-273:
```python
def _connect_editor_signals(self) -> None:
    self._editor.textChanged.connect(self._emit_content_changed)
    self._editor.currentCharFormatChanged.connect(self._sync_char_format)
    self._editor.cursorPositionChanged.connect(self._sync_block_format)
    self._editor.document().undoAvailable.connect(self.undo_available_changed)
    self._editor.document().undoAvailable.connect(self.action_undo.setEnabled)
    self._editor.document().redoAvailable.connect(self.redo_available_changed)
    self._editor.document().redoAvailable.connect(self.action_redo.setEnabled)
    self._editor.copyAvailable.connect(self.copy_available_changed)
    self._editor.copyAvailable.connect(self.action_cut.setEnabled)
    self._editor.copyAvailable.connect(self.action_copy.setEnabled)
    self._editor.paste_sanitized.connect(self._on_paste_sanitized)
```

---

### `src/secnotepad/ui/search_dialog.py` (component / dialog, request-response + event-driven)

**Analog:** `src/secnotepad/ui/password_dialog.py`

**Imports pattern** — 对话框文件独立导入 Qt widget；保持对话框 UI 与 MainWindow 解耦。

Source: `src/secnotepad/ui/password_dialog.py` lines 5-9:
```python
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                QLabel, QLineEdit, QPushButton,
                                QCheckBox, QProgressBar, QStyle)
```

**Dialog 初始化 pattern** — `SearchDialog` 应继承 `QDialog`，在 `__init__` 中设置标题、主布局、输入控件、按钮区和信号连接。

Source: `src/secnotepad/ui/password_dialog.py` lines 25-41:
```python
def __init__(self, mode: PasswordMode, parent=None):
    super().__init__(parent)
    self._mode = mode
    self._password = bytearray()

    self.setModal(True)

    # --- 窗口标题 ---
    titles = {
        PasswordMode.SET_PASSWORD: "设置加密密码",
        PasswordMode.ENTER_PASSWORD: "输入密码",
        PasswordMode.CHANGE_PASSWORD: "更换密码",
    }
    self.setWindowTitle(titles[mode])

    # --- 主布局 ---
    layout = QVBoxLayout(self)
```

**按钮与信号 pattern** — 搜索按钮和回车应触发同一个 `_on_search()`；结果激活时发出信号给 MainWindow，而不是在 dialog 内直接操作主窗口状态。

Source: `src/secnotepad/ui/password_dialog.py` lines 136-150:
```python
# --- 确认 / 取消按钮 ---
btn_layout = QHBoxLayout()
self._btn_confirm = QPushButton("确认")
self._btn_confirm.clicked.connect(self._on_confirm)
btn_layout.addStretch()
btn_layout.addWidget(self._btn_confirm)
cancel_btn = QPushButton("取消")
cancel_btn.clicked.connect(self.reject)
btn_layout.addWidget(cancel_btn)
layout.addLayout(btn_layout)

# --- 信号连接 ---
self._pwd_input.textChanged.connect(self._on_password_changed)
self._confirm_input.textChanged.connect(self._on_password_changed)
self.rejected.connect(self.clear_password)
```

**输入校验 pattern** — 对话框本地校验输入，并通过按钮 enabled/error label 反馈；搜索 query 为空时应禁用搜索或显示空结果。

Source: `src/secnotepad/ui/password_dialog.py` lines 269-288:
```python
def _update_confirm_button(self):
    """根据当前模式更新确认按钮启用状态。"""
    if self._mode == PasswordMode.SET_PASSWORD:
        pwd = self._pwd_input.text()
        confirm = self._confirm_input.text()
        valid = len(pwd) >= 8 and pwd == confirm
        self._btn_confirm.setEnabled(valid)

    elif self._mode == PasswordMode.ENTER_PASSWORD:
        pwd = self._pwd_input.text()
        self._btn_confirm.setEnabled(len(pwd) > 0)

    elif self._mode == PasswordMode.CHANGE_PASSWORD:
        if self._cb_change and not self._cb_change.isChecked():
            self._btn_confirm.setEnabled(True)
        else:
            pwd = self._pwd_input.text()
            confirm = self._confirm_input.text()
            valid = len(pwd) >= 8 and pwd == confirm
            self._btn_confirm.setEnabled(valid)
```

---

### `src/secnotepad/ui/main_window.py` (controller / provider, event-driven + request-response)

**Analog:** `src/secnotepad/ui/main_window.py`

**Imports pattern** — 新增 `TagBarWidget` / `SearchDialog` / `SearchService` 时按现有相对导入风格追加到 import block。

Source: `src/secnotepad/ui/main_window.py` lines 13-21:
```python
from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
from ..model.section_filter_proxy import SectionFilterProxy
from ..model.page_list_model import PageListModel
from .welcome_widget import WelcomeWidget
from ..crypto.file_service import FileService
from ..model.serializer import Serializer
from .password_dialog import PasswordDialog, PasswordMode
from .rich_text_editor import RichTextEditorWidget
```

**菜单 action pattern** — 搜索入口应加到 `编辑(&E)` 菜单，和现有 QAction / shortcut / enabled 模式一致。

Source: `src/secnotepad/ui/main_window.py` lines 119-143:
```python
# ── 编辑菜单 ──
self._edit_menu = QMenu("编辑(&E)", self)
mb.addMenu(self._edit_menu)
edit_menu = self._edit_menu
self._act_undo = QAction("撤销(&U)", self)
self._act_undo.setShortcut(QKeySequence.StandardKey.Undo)
self._act_redo = QAction("重做(&R)", self)
self._act_redo.setShortcut(QKeySequence("Ctrl+Y"))
self._act_cut = QAction("剪切(&T)", self)
self._act_cut.setShortcut(QKeySequence.StandardKey.Cut)
self._act_copy = QAction("复制(&C)", self)
self._act_copy.setShortcut(QKeySequence.StandardKey.Copy)
self._act_paste = QAction("粘贴(&P)", self)
self._act_paste.setShortcut(QKeySequence.StandardKey.Paste)
self._edit_actions = [
    self._act_undo,
    self._act_redo,
    self._act_cut,
    self._act_copy,
    self._act_paste,
]
for act in self._edit_actions:
    act.setEnabled(False)
    edit_menu.addAction(act)
```

**右侧编辑区集成 pattern** — 标签栏必须在 `_setup_editor_area()` 内加入编辑区顶部；顺序应是标签栏、格式工具栏、编辑器 stack（或按 UI 规划将标签栏置于当前页面编辑区域顶部），不要加入中间页面列表。

Source: `src/secnotepad/ui/main_window.py` lines 275-306:
```python
self._editor_container = QWidget()
editor_layout = QVBoxLayout(self._editor_container)
editor_layout.setContentsMargins(0, 0, 0, 0)
editor_layout.setSpacing(8)

self._rich_text_editor = RichTextEditorWidget(self._editor_container)
self._rich_text_editor.set_status_callback(
    lambda message: self.statusBar().showMessage(message)
)
self._rich_text_editor.content_changed.connect(
    self._on_editor_content_changed
)
self._editor_preview = self._rich_text_editor.editor()
self._format_toolbar = self._rich_text_editor.format_toolbar()
self._format_toolbar.setParent(self._editor_container)
editor_layout.addWidget(self._format_toolbar)
self._rich_text_editor.layout().removeWidget(self._format_toolbar)
self._rich_text_editor.set_editor_enabled(False)

self._editor_placeholder_label = QLabel(
    "请在页面列表中选择一个页面"
)
self._editor_placeholder_label.setAlignment(Qt.AlignCenter)
self._editor_placeholder_label.setStyleSheet(
    "color: #888; font-size: 14px;"
)

self._editor_stack = QStackedWidget(self._editor_container)
self._editor_stack.addWidget(self._rich_text_editor.editor())  # index 0
self._editor_stack.addWidget(self._editor_placeholder_label)  # index 1
self._editor_stack.setCurrentIndex(1)  # 默认显示 placeholder
editor_layout.addWidget(self._editor_stack)
```

**页面加载 / placeholder pattern** — 标签栏刷新应插入这两个方法：选中页面时 `set_tags(note.tags)` 并启用；无页面时清空并禁用。保持 `load_html()` 不触发脏标记的边界。

Source: `src/secnotepad/ui/main_window.py` lines 493-523:
```python
def _show_editor_placeholder(self):
    """显示 placeholder 提示文字 (D-63)，不写回当前页面。"""
    self._editor_stack.setCurrentIndex(1)
    self._rich_text_editor.load_html("")
    self._rich_text_editor.set_editor_enabled(False)
    self._update_edit_action_states()

...

def _show_note_in_editor(self, note: SNoteItem):
    """显示页面内容到右侧编辑器，避免触发无意义脏标记。"""
    self._rich_text_editor.load_html(note.content or "")
    self._editor_stack.setCurrentIndex(0)
    self._rich_text_editor.set_editor_enabled(True)
    self._update_edit_action_states()
```

**dirty pattern** — 标签 add/remove handler 修改 `note.tags` 后调用 `mark_dirty()`；搜索、结果展示和跳转不得调用 `mark_dirty()`。

Source: `src/secnotepad/ui/main_window.py` lines 504-516:
```python
def _on_editor_content_changed(self, html: str):
    """编辑器内容变化时同步回当前页面并标记脏状态。"""
    if self._editor_stack.currentIndex() != 0:
        return
    if self._page_list_model is None:
        return
    current = self._list_view.currentIndex()
    note = self._page_list_model.note_at(current)
    if note is None:
        return
    if note.content != html:
        note.content = html
        self.mark_dirty()
```

Source: `src/secnotepad/ui/main_window.py` lines 883-887:
```python
def mark_dirty(self):
    """标记笔记本已修改。Phase 3（结构编辑）和 Phase 4（文本编辑）调用此方法。"""
    if not self._is_dirty and self._root_item is not None:
        self._is_dirty = True
        self._update_window_title()
```

**导航选择 pattern** — 搜索结果跳转应复用 selection model / `setCurrentIndex()` 流程，让既有 `_on_tree_current_changed()` 和 `_on_page_current_changed()` 驱动页面列表和编辑器刷新。

Source: `src/secnotepad/ui/main_window.py` lines 341-350:
```python
# --- 3. 选择信号连接 (D-51, D-62, Pitfall 3) ---
self._tree_selection = self._tree_view.selectionModel()
self._tree_selection.currentChanged.connect(
    self._on_tree_current_changed
)

self._page_selection = self._list_view.selectionModel()
self._page_selection.currentChanged.connect(
    self._on_page_current_changed
)
```

Source: `src/secnotepad/ui/main_window.py` lines 464-491:
```python
def _on_tree_current_changed(self, current: QModelIndex,
                             previous: QModelIndex):
    """分区选择变化 → 更新页面列表 (D-51)。

    从 proxy 索引映射回源模型索引，获取 SNoteItem(section)，
    调用 PageListModel.set_section() 刷新列表。
    每次分区切换时重置编辑区为 placeholder (D-63)。
    """
    source_index = self._section_filter.mapToSource(current)
    if source_index.isValid():
        section_item = source_index.internalPointer()
        self._page_list_model.set_section(section_item)
    else:
        self._page_list_model.set_section(None)
    self._show_editor_placeholder()

def _on_page_current_changed(self, current: QModelIndex,
                             previous: QModelIndex):
    """页面选择变化 → 显示只读预览 (D-62, D-63)。

    获取 SNoteItem(note) 后调用 QTextEdit.setHtml() 显示内容。
    无效选择（取消选择）时显示 placeholder。
    """
    note = self._page_list_model.note_at(current)
    if note is not None:
        self._show_note_in_editor(note)
    else:
        self._show_editor_placeholder()
```

**重复初始化防重复绑定 pattern** — 如果新增搜索 dialog 引用、tag bar 信号或 action，需遵守现有 teardown/幂等思路，避免重复 `_setup_navigation()` 后信号多次触发。

Source: `src/secnotepad/ui/main_window.py` lines 319-321:
```python
if self._navigation_initialized:
    self._teardown_navigation()
```

Source: `src/secnotepad/ui/main_window.py` lines 378-433:
```python
def _teardown_navigation(self):
    """断开上一次导航初始化的信号，确保重复初始化幂等。"""
    if self._tree_selection is not None:
        try:
            self._tree_selection.currentChanged.disconnect(
                self._on_tree_current_changed
            )
        except (RuntimeError, TypeError):
            pass
    if self._page_selection is not None:
        try:
            self._page_selection.currentChanged.disconnect(
                self._on_page_current_changed
            )
        except (RuntimeError, TypeError):
            pass
    for button, handler in (
        (self._btn_new_section, self._on_new_root_section),
        (self._btn_new_child_section, self._on_new_child_section),
        (self._btn_new_page, self._on_new_page),
    ):
        if button is None:
            continue
        try:
            button.clicked.disconnect(handler)
        except (RuntimeError, TypeError):
            pass
```

---

### `tests/model/test_search_service.py` (test, batch + transform)

**Analog:** `tests/model/test_tree_model.py` + `tests/model/test_page_list_model.py`

**Imports / fixture pattern** — 模型测试用 pytest fixture 构造 `SNoteItem` 树，直接断言纯 Python/Qt 模型行为。

Source: `tests/model/test_tree_model.py` lines 5-10:
```python
import pytest
from PySide6.QtCore import QModelIndex, Qt

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.tree_model import TreeModel
```

Source: `tests/model/test_tree_model.py` lines 28-46:
```python
@pytest.fixture
def sample_tree():
    """创建 3 层示例树.

    根分区 (hidden)
    └── 工作 (section)
        ├── 周报 (note)
        └── 项目A (section)
            └── 需求文档 (note)
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    report = SNoteItem.new_note("周报")
    project = SNoteItem.new_section("项目A")
    doc = SNoteItem.new_note("需求文档")
    project.children.append(doc)
    work.children.append(report)
    work.children.append(project)
    root.children.append(work)
    return root
```

**测试组织 pattern** — 使用 class 分组场景；搜索服务测试可分为 `TestSearchFields`、`TestSnippet`、`TestPaths`、`TestTags`。

Source: `tests/model/test_page_list_model.py` lines 52-60:
```python
class TestRowCount:
    """rowCount — 平铺展示分区下的 note 子节点列表。"""

    def test_rowcount_counts_only_notes(self, section_with_notes):
        """场景 1: set_section 传入含 2 个 note + 1 个 section 子节点的分区 → rowCount() == 2（只计 note）。"""
        model = PageListModel()
        model.set_section(section_with_notes)
        assert model.rowCount() == 2
```

**引用一致性 pattern** — 搜索结果若携带 `SNoteItem` 对象，应测试对象引用而非值相等。

Source: `tests/model/test_page_list_model.py` lines 283-316:
```python
def test_remove_note_uses_object_identity_not_value_equality(self):
    """字段值相等的不同页面对象删除时不能误删第一个同值对象。"""
    section = SNoteItem.new_section("分区")
    first = SNoteItem(
        id="same-id",
        title="同名页面",
        item_type="note",
        content="same content",
        children=[],
        tags=[],
        created_at="same-time",
        updated_at="same-time",
    )
    second = SNoteItem(
        id="same-id",
        title="同名页面",
        item_type="note",
        content="same content",
        children=[],
        tags=[],
        created_at="same-time",
        updated_at="same-time",
    )
    assert first == second
    assert first is not second
    section.children.extend([first, second])
    model = PageListModel()
    model.set_section(section)

    assert model.remove_note(model.index(1, 0)) is True

    assert section.children == [first]
    assert model.rowCount() == 1
    assert model.note_at(model.index(0, 0)) is first
```

---

### `tests/ui/test_tag_bar_widget.py` (test, event-driven)

**Analog:** `tests/ui/test_rich_text_editor.py`

**Fixture pattern** — UI widget 测试用 `qapp` fixture，show / yield / close / deleteLater。

Source: `tests/ui/test_rich_text_editor.py` lines 11-18:
```python
@pytest.fixture
def editor_widget(qapp):
    """Create the rich text editor widget under test."""
    widget = RichTextEditorWidget()
    widget.show()
    yield widget
    widget.close()
    widget.deleteLater()
```

**信号测试 pattern** — 通过列表收集 signal payload，验证 load/set 状态不应误发变更，用户操作才发信号。

Source: `tests/ui/test_rich_text_editor.py` lines 29-43:
```python
def test_editing_page_updates_note_html_and_dirty(editor_widget):
    changes = []
    editor_widget.content_changed.connect(lambda _html: changes.append("changed"))

    editor_widget.load_html("<p>旧内容</p>")
    assert changes == []
    assert "旧内容" in editor_widget.to_html()

    editor = editor_widget.editor()
    editor.setFocus()
    editor.selectAll()
    editor.insertPlainText("新内容")

    assert changes
    assert "新内容" in editor_widget.to_html()
```

**不误置脏 pattern** — 标签栏 `set_tags()` / `set_available_tags()` 这类刷新方法应测试不发 add/remove 信号；用户点击添加/删除才发信号。

Source: `tests/ui/test_rich_text_editor.py` lines 235-250:
```python
def test_zoom_does_not_mark_content_dirty(editor_widget):
    changes = []
    editor_widget.content_changed.connect(lambda: changes.append("changed"))
    editor_widget.load_html("<p>zoom me</p>")
    before = editor_widget.to_html()

    editor_widget.zoom_in()
    assert editor_widget.zoom_percent == 110
    editor_widget.zoom_out()
    assert editor_widget.zoom_percent == 100
    editor_widget.zoom_in()
    editor_widget.reset_zoom()
    assert editor_widget.zoom_percent == 100

    assert editor_widget.to_html() == before
    assert changes == []
```

---

### `tests/ui/test_search_dialog.py` (test, request-response + event-driven)

**Analog:** `tests/ui/test_password_dialog.py`

**Dialog fixture pattern** — 每种 dialog 状态用单独 fixture，创建后 show，测试结束 close/deleteLater。

Source: `tests/ui/test_password_dialog.py` lines 13-30:
```python
@pytest.fixture
def set_dialog(qapp):
    """SET_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.SET_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()


@pytest.fixture
def enter_dialog(qapp):
    """ENTER_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()
```

**查找控件 pattern** — 测试通过 `findChildren()` / `findChild()` 验证控件存在、初始状态和 enabled 状态。

Source: `tests/ui/test_password_dialog.py` lines 49-67:
```python
def test_two_password_fields(self, set_dialog):
    """SET_PASSWORD 模式有密码和确认密码两个字段。"""
    line_edits = set_dialog.findChildren(QLineEdit)
    assert len(line_edits) == 2

def test_confirm_disabled_when_empty(self, set_dialog):
    """初始状态确认按钮禁用。"""
    confirm = set_dialog.findChild(QPushButton, "确认")
    assert confirm is None or not confirm.isEnabled()

def test_strength_bar_exists(self, set_dialog):
    """有密码强度指示器。"""
    bar = set_dialog.findChild(QProgressBar)
    assert bar is not None

def test_generate_button_exists(self, set_dialog):
    """有'生成密码'按钮。"""
    buttons = [b for b in set_dialog.findChildren(QPushButton) if '生成' in b.text()]
    assert len(buttons) >= 1
```

**输入校验 pattern** — 搜索 query、字段勾选和搜索按钮 enabled 状态应像密码对话框一样通过直接设置控件文本测试。

Source: `tests/ui/test_password_dialog.py` lines 69-77:
```python
def test_min_length_8(self, set_dialog):
    """密码短于 8 字符时确认按钮禁用。"""
    # 模拟输入 6 字符密码
    line_edits = set_dialog.findChildren(QLineEdit)
    line_edits[0].setText("Abc12")
    line_edits[1].setText("Abc12")
    confirm = [b for b in set_dialog.findChildren(QPushButton) if b.text() == "确认"]
    if confirm:
        assert not confirm[0].isEnabled()
```

---

### `tests/ui/test_main_window_tags.py` (test, event-driven)

**Analog:** `tests/ui/test_navigation.py`

**MainWindow fixture pattern** — 新增标签集成测试复用已打开笔记本 fixture；测试结束前清 dirty，避免 closeEvent 弹保存确认。

Source: `tests/ui/test_navigation.py` lines 11-20:
```python
@pytest.fixture
def window_with_notebook(qapp):
    """创建已打开笔记本的 MainWindow，导航系统已初始化。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()
```

**页面选择与当前 note pattern** — 标签集成测试应通过 `_on_new_root_section()` + `_on_new_page()` 创建当前页面，再用 `note_at(current)` 取得真实 `SNoteItem` 验证 `tags`。

Source: `tests/ui/test_navigation.py` lines 726-741:
```python
def test_editor_updates_note_content_and_marks_dirty(self, window_with_notebook):
    """编辑右侧文本后同步回当前页面并置脏。"""
    window_with_notebook._on_new_root_section()
    window_with_notebook._on_new_page()

    current = window_with_notebook._list_view.currentIndex()
    note = window_with_notebook._page_list_model.note_at(current)
    assert note is not None

    window_with_notebook._is_dirty = False
    window_with_notebook._editor_preview.setFocus()
    window_with_notebook._editor_preview.clear()
    QTest.keyClicks(window_with_notebook._editor_preview, "hello")

    assert "hello" in note.content
    assert window_with_notebook._is_dirty is True
```

**placeholder 不写回 pattern** — 标签栏在无页面状态清空/禁用不得修改原 note.tags，也不得置脏。

Source: `tests/ui/test_navigation.py` lines 749-762:
```python
def test_show_editor_placeholder_does_not_clear_note_content(self, window_with_notebook):
    """切换到 placeholder 不会把当前页面正文写空。"""
    window_with_notebook._on_new_root_section()
    window_with_notebook._on_new_page()
    note = window_with_notebook._page_list_model.note_at(
        window_with_notebook._list_view.currentIndex()
    )
    note.content = "<p>keep me</p>"
    window_with_notebook._is_dirty = False

    window_with_notebook._show_editor_placeholder()

    assert note.content == "<p>keep me</p>"
    assert window_with_notebook._is_dirty is False
```

---

### `tests/ui/test_main_window_search.py` (test, event-driven + request-response)

**Analog:** `tests/ui/test_navigation.py`

**导航状态测试 pattern** — 搜索跳转测试应断言 tree/list/editor 三者同步；不要只断言某个 handler 被调用。

Source: `tests/ui/test_navigation.py` lines 743-747:
```python
def test_selecting_page_shows_editor(self, window_with_notebook):
    """选中页面后切换到编辑器页，而不是保持 placeholder。"""
    window_with_notebook._on_new_root_section()
    window_with_notebook._on_new_page()
    assert window_with_notebook._editor_stack.currentIndex() == 0
```

**setCurrentIndex / 自动选中 pattern** — 跳转到搜索结果目标页面时，测试应验证当前列表索引有效，并且 `note_at(current)` 是目标页面。

Source: `tests/ui/test_navigation.py` lines 759-770:
```python
def _on_new_page(self):
    """在当前分区下新建页面 (D-55, D-61, D-64)。"""
    if self._page_list_model._section is None:
        return
    note = SNoteItem.new_note("新页面")
    if self._page_list_model.add_note(note):
        self.mark_dirty()
        # D-64: 自动选中新创建的页面
        new_row = self._page_list_model.rowCount() - 1
        new_index = self._page_list_model.index(new_row, 0)
        self._list_view.setCurrentIndex(new_index)
```

**不置脏 pattern** — 搜索、打开 dialog、点击结果跳转都不应修改 `_is_dirty`。

Source: `tests/ui/test_navigation.py` lines 834-859:
```python
def test_switching_pages_clears_undo_stack_and_does_not_mark_dirty(self, window_with_notebook):
    """切换页面后 undo 不恢复上一页明文，且不会误置脏。"""
    window_with_notebook._on_new_root_section()
    window_with_notebook._on_new_page()
    first_index = window_with_notebook._list_view.currentIndex()
    first_note = window_with_notebook._page_list_model.note_at(first_index)
    first_note.content = "<p>第一页保密内容</p>"
    window_with_notebook._show_note_in_editor(first_note)
    editor = window_with_notebook._rich_text_editor.editor()
    editor.setFocus()
    editor.selectAll()
    editor.insertPlainText("第一页已编辑明文")
    assert "第一页已编辑明文" in first_note.content

    window_with_notebook._on_new_page()
    second_index = window_with_notebook._list_view.currentIndex()
    second_note = window_with_notebook._page_list_model.note_at(second_index)
    second_note.content = "<p>第二页内容</p>"
    window_with_notebook._is_dirty = False

    window_with_notebook._show_note_in_editor(second_note)
    window_with_notebook._rich_text_editor.action_undo.trigger()

    assert "第一页已编辑明文" not in window_with_notebook._rich_text_editor.editor().toPlainText()
    assert "第一页已编辑明文" not in second_note.content
    assert window_with_notebook._is_dirty is False
```

## Shared Patterns

### Signal-driven UI 边界

**Source:** `src/secnotepad/ui/rich_text_editor.py`  
**Apply to:** `tag_bar_widget.py`, `search_dialog.py`, `main_window.py`

组件发出信号，MainWindow 负责读取当前状态并修改 `SNoteItem` 或导航选择。

Source lines 61-67:
```python
content_changed = Signal(str)
paste_sanitized = Signal()
status_message_requested = Signal(str)
undo_available_changed = Signal(bool)
redo_available_changed = Signal(bool)
copy_available_changed = Signal(bool)
```

### Dirty 语义

**Source:** `src/secnotepad/ui/main_window.py`  
**Apply to:** 标签 add/remove handler；不应用于搜索和跳转

Source lines 504-516:
```python
if note.content != html:
    note.content = html
    self.mark_dirty()
```

Source lines 883-887:
```python
if not self._is_dirty and self._root_item is not None:
    self._is_dirty = True
    self._update_window_title()
```

### Model/View 与数据源引用

**Source:** `src/secnotepad/model/page_list_model.py`  
**Apply to:** MainWindow 获取当前 note、搜索跳转选中页面、测试断言

Source lines 27-41:
```python
def set_section(self, section: SNoteItem | None):
    """设置当前分区并刷新 note 列表。

    使用 beginResetModel/endResetModel 进行完整模型重置。
    如果 section 为 None，清空列表。

    _notes 缓存中的元素 == _section.children 中的同一对象引用 (Pitfall 5)。
    """
    self.beginResetModel()
    self._section = section
    if section is not None:
        self._notes = [c for c in section.children if c.item_type == "note"]
    else:
        self._notes = []
    self.endResetModel()
```

Source lines 156-163:
```python
def note_at(self, index: QModelIndex) -> SNoteItem | None:
    """通过索引获取对应的 SNoteItem 对象。

    有效索引返回 SNoteItem，无效索引返回 None。
    """
    if not self._is_valid_note_index(index):
        return None
    return self._notes[index.row()]
```

### 搜索/跳转通过现有导航选择传播

**Source:** `src/secnotepad/ui/main_window.py`  
**Apply to:** 搜索结果点击跳转

Source lines 341-350:
```python
self._tree_selection = self._tree_view.selectionModel()
self._tree_selection.currentChanged.connect(
    self._on_tree_current_changed
)

self._page_selection = self._list_view.selectionModel()
self._page_selection.currentChanged.connect(
    self._on_page_current_changed
)
```

Source lines 472-478:
```python
source_index = self._section_filter.mapToSource(current)
if source_index.isValid():
    section_item = source_index.internalPointer()
    self._page_list_model.set_section(section_item)
else:
    self._page_list_model.set_section(None)
self._show_editor_placeholder()
```

### QWidget/QDialog 测试 fixture

**Source:** `tests/ui/test_navigation.py` + `tests/ui/test_rich_text_editor.py`  
**Apply to:** 所有 Phase 05 UI 测试

Source: `tests/ui/test_navigation.py` lines 11-20:
```python
@pytest.fixture
def window_with_notebook(qapp):
    """创建已打开笔记本的 MainWindow，导航系统已初始化。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()
```

Source: `tests/ui/test_rich_text_editor.py` lines 11-18:
```python
@pytest.fixture
def editor_widget(qapp):
    """Create the rich text editor widget under test."""
    widget = RichTextEditorWidget()
    widget.show()
    yield widget
    widget.close()
    widget.deleteLater()
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| None | - | - | 9 个目标文件均有可复用 analog；`search_service.py` 没有同名服务层 analog，但有 `TreeModel` 递归遍历、`Serializer` 纯转换和 `SNoteItem` 数据边界可复用。 |

## Metadata

**Analog search scope:** `/home/jone/projects/secnotepad/src/secnotepad`, `/home/jone/projects/secnotepad/tests`  
**Files scanned:** 43 source/test files listed; 10 primary analog files read  
**Primary analog files:**
- `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py`
- `/home/jone/projects/secnotepad/src/secnotepad/ui/rich_text_editor.py`
- `/home/jone/projects/secnotepad/src/secnotepad/ui/password_dialog.py`
- `/home/jone/projects/secnotepad/src/secnotepad/model/snote_item.py`
- `/home/jone/projects/secnotepad/src/secnotepad/model/serializer.py`
- `/home/jone/projects/secnotepad/src/secnotepad/model/page_list_model.py`
- `/home/jone/projects/secnotepad/src/secnotepad/model/tree_model.py`
- `/home/jone/projects/secnotepad/tests/ui/test_navigation.py`
- `/home/jone/projects/secnotepad/tests/ui/test_rich_text_editor.py`
- `/home/jone/projects/secnotepad/tests/ui/test_password_dialog.py`

**Pattern extraction date:** 2026-05-11
