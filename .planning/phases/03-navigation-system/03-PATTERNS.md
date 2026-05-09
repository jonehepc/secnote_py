# Phase 03: 导航系统 - Pattern Map

**Mapped:** 2026-05-08
**Files analyzed:** 10 (6 new, 4 modified)
**Analogs found:** 10 / 10

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/secnotepad/model/section_filter_proxy.py` | model (proxy) | transform (filter) | `src/secnotepad/model/tree_model.py` | role-match |
| `src/secnotepad/model/page_list_model.py` | model (list) | crud | `src/secnotepad/model/tree_model.py` | role-match |
| `src/secnotepad/model/tree_model.py` (modify) | model (tree) | crud | itself — add setData() | exact |
| `src/secnotepad/ui/main_window.py` (modify) | controller | event-driven | itself — add CRUD + signals | exact |
| `tests/model/test_section_filter_proxy.py` | test | assertions | `tests/model/test_tree_model.py` | exact |
| `tests/model/test_page_list_model.py` | test | assertions | `tests/model/test_tree_model.py` | exact |
| `tests/ui/test_navigation.py` | test | integration | `tests/ui/test_main_window.py` | exact |
| `tests/model/test_tree_model.py` (modify) | test | assertions | itself — add setData test class | exact |
| `tests/conftest.py` (modify) | config | n/a | itself — add fixture | exact |

---

## Pattern Assignments

### 1. `src/secnotepad/model/section_filter_proxy.py` (model/proxy, transform/filter)

**Analog:** `src/secnotepad/model/tree_model.py` (for imports, docstring, code organization style)

**Imports pattern** (lines 1-10):
```python
"""SectionFilterProxy - QSortFilterProxyModel 子类，过滤分区树仅显示 section 节点 (D-49)。

使用 Qt6 的 setRecursiveFilteringEnabled(True) 实现递归过滤，
配合 setAutoAcceptChildRows(False) 确保 note 子节点不显示。
"""

from PySide6.QtCore import QSortFilterProxyModel, QModelIndex

from .snote_item import SNoteItem
```

**Code organization pattern** (lines 13-104 of tree_model.py):
```python
# 类继承自 Qt 基类，使用 super().__init__(parent)
class SectionFilterProxy(QSortFilterProxyModel):
    """类级别 docstring 说明用途和引用决策编号。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化设置
```

**Core pattern** (from RESEARCH.md Pattern 1):
```python
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        source = self.sourceModel()
        # 防御性检查：sourceModel 可能为 None
        if source is None:
            return False
        index = source.index(source_row, 0, source_parent)
        if not index.isValid():
            return False
        item = index.internalPointer()
        return item.item_type == "section"
```

---

### 2. `src/secnotepad/model/page_list_model.py` (model/list, crud)

**Analog:** `src/secnotepad/model/tree_model.py` (imports, docstring, method organization, Qt signal patterns)

**Imports pattern** (lines 1-10 of tree_model.py):
```python
"""PageListModel - QAbstractListModel 子类，平铺展示分区下的页面列表 (D-50, D-54)。

接收 SNoteItem(section) 为数据源，仅显示 item_type=="note" 的子节点。
支持单列标题显示、原地重命名 (EditRole)、添加/删除笔记。
"""

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from .snote_item import SNoteItem
```

**Docstring and section comment style** (lines 1-10, 102-115 of tree_model.py):
```python
    # ── QAbstractListModel 必需契约方法 ──
    # ── 数据变更接口（供 Phase 3 调用） ──
```

**Core pattern — data() & flags()** (lines 88-106 of tree_model.py):
```python
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """返回索引处的数据显示。"""
        if not index.isValid():
            return None
        note = self._notes[index.row()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return note.title
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
```

**Core pattern — setData()** (to be added, pattern from RESEARCH.md Pattern 2):
```python
    def setData(self, index: QModelIndex, value: str,
                role: int = Qt.EditRole) -> bool:
        """重命名标题 (D-60: 拒绝空名称)。"""
        if not index.isValid() or role != Qt.EditRole:
            return False
        if not isinstance(value, str) or value.strip() == "":
            # D-60: empty name rejection
            return False
        note = self._notes[index.row()]
        note.title = value.strip()
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True
```

**Core pattern — add/remove with begin/end signals** (from RESEARCH.md Pattern 2, patterned after tree_model.py lines 147-183):
```python
    # Uses beginResetModel/endResetModel for set_section()
    # Uses beginInsertRows/endInsertRows for add_note()
    # Uses beginRemoveRows/endRemoveRows for remove_note()
```

**beginResetModel pattern** (new — not in tree_model.py):
```python
    def set_section(self, section: SNoteItem | None):
        self.beginResetModel()
        self._section = section
        if section is not None:
            self._notes = [c for c in section.children if c.item_type == "note"]
        else:
            self._notes = []
        self.endResetModel()
```

---

### 3. `src/secnotepad/model/tree_model.py` — MODIFY: add setData()

**Analog:** self — same file, add new method following existing method patterns

**Existing method style to match** (lines 145-183 of tree_model.py):
```python
    # ── 数据变更接口（供 Phase 3 调用） ──
    # Add setData here, between add_item/remove_item block

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        """重命名分区标题 (D-59, D-60: 拒绝空名称)。

        Phase 3 添加，支持原地编辑 (EditRole)。
        """
        if role != Qt.EditRole:
            return False
        if not index.isValid():
            return False
        # D-60: reject empty names
        if not isinstance(value, str) or value.strip() == "":
            return False
        item: SNoteItem = index.internalPointer()
        item.title = value.strip()
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True
```

**Additionally:** Update `flags()` (line 103-105) to include `Qt.ItemIsEditable`:
```python
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
```

---

### 4. `src/secnotepad/ui/main_window.py` — MODIFY: integrate navigation

**Analog:** self — same file, add new methods and modify existing ones

**Existing import pattern** (lines 1-17 of main_window.py):
```python
# Add these new imports alongside existing ones
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QMainWindow, QWidget, QSplitter,
                                QTreeView, QListView, QStackedWidget,
                                QStyle, QVBoxLayout, QMessageBox,
                                QFileDialog, QDialog,
                                QMenu, QTextEdit, QLabel, QAbstractItemView)  # NEW for Phase 3
from PySide6.QtGui import QAction, QKeySequence, QCloseEvent

from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
from ..model.section_filter_proxy import SectionFilterProxy  # NEW
from ..model.page_list_model import PageListModel            # NEW
from .welcome_widget import WelcomeWidget
from ..crypto.file_service import FileService
from ..model.serializer import Serializer
from .password_dialog import PasswordDialog, PasswordMode
```

**New instance variables pattern** (lines 28-35 of main_window.py):
```python
        # ── 导航系统状态 (Phase 3) ──
        self._section_filter: SectionFilterProxy = None
        self._page_list_model: PageListModel = None
        self._editor_preview: QTextEdit = None
        self._editor_stack: QStackedWidget = None
        self._editor_placeholder_label: QLabel = None
```

**Modify _setup_central_area:** Replace `_editor_placeholder` QWidget with editor stack:
```python
        # Replace:
        self._editor_placeholder = QWidget()
        splitter.addWidget(self._editor_placeholder)
        # With:
        self._setup_editor_area()  # New method that creates QStackedWidget
        splitter.addWidget(self._editor_stack)
```

**New method: _setup_editor_area** (follows `_setup_central_area` pattern at line 134):
```python
    def _setup_editor_area(self):
        """创建右侧编辑区: 只读预览 + placeholder 堆叠 (D-62, D-63)。"""
        self._editor_preview = QTextEdit()
        self._editor_preview.setReadOnly(True)

        self._editor_placeholder_label = QLabel("请在页面列表中选择一个页面")
        self._editor_placeholder_label.setAlignment(Qt.AlignCenter)
        self._editor_placeholder_label.setStyleSheet("color: #888; font-size: 14px;")

        self._editor_stack = QStackedWidget()
        self._editor_stack.addWidget(self._editor_preview)        # index 0
        self._editor_stack.addWidget(self._editor_placeholder_label)  # index 1
        self._editor_stack.setCurrentIndex(1)                     # default placeholder
```

**Modify _on_new_notebook** (lines 292-331): After setting TreeModel on _tree_view, add navigation setup:
```python
    def _on_new_notebook(self):
        # ... existing code up to _tree_view.setModel ...
        # After line 315 (_tree_view.setModel):
        self._setup_navigation()  # NEW: Phase 3 navigation setup
```

**Modify _on_open_notebook** (lines 333-376): After `_tree_view.setModel` on line 359 and similarly in `_on_open_recent` (line 557):
```python
        self._setup_navigation()  # NEW: Phase 3 navigation setup
```

**New method: _setup_navigation** (signal-driven architecture pattern from lines 277-290; method naming follows `_setup_central_area` at line 134):
```python
    def _setup_navigation(self):
        """Phase 3: 设置导航系统 — Proxy 模型、页面列表、信号连接 (D-49~D-64)。"""
        # --- SectionFilterProxy: 过滤分区树仅显示 section (D-49) ---
        self._section_filter = SectionFilterProxy(self)
        self._section_filter.setSourceModel(self._tree_model)
        self._tree_view.setModel(self._section_filter)

        # D-59: 原地编辑 (必须在 setModel 之后设置)
        from PySide6.QtWidgets import QAbstractItemView
        self._tree_view.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )

        # --- PageListModel: 平铺显示当前分区的页面 (D-50, D-54) ---
        self._page_list_model = PageListModel(self)
        self._list_view.setModel(self._page_list_model)

        # D-59: 原地编辑
        self._list_view.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )

        # --- 选择信号连接 (D-51, D-62) ---
        self._tree_selection = self._tree_view.selectionModel()
        self._tree_selection.currentChanged.connect(self._on_tree_current_changed)

        self._page_selection = self._list_view.selectionModel()
        self._page_selection.currentChanged.connect(self._on_page_current_changed)

        # --- 右键菜单 (D-56) ---
        self._setup_tree_context_menu()
        self._setup_page_context_menu()

        # --- 键盘快捷键 (D-57) ---
        self._setup_navigation_shortcuts()

        # --- 初始状态 (D-52, D-53) ---
        self._initialize_navigation_state()
```

**New method: _on_tree_current_changed** (follows handler naming pattern `_on_*` from lines 277-291):
```python
    def _on_tree_current_changed(self, current: QModelIndex, previous: QModelIndex):
        """分区选择变化 → 更新页面列表 (D-51)。"""
        source_index = self._section_filter.mapToSource(current)
        if source_index.isValid():
            section_item: SNoteItem = source_index.internalPointer()
            self._page_list_model.set_section(section_item)
        else:
            self._page_list_model.set_section(None)
        self._show_editor_placeholder()
```

**New method: _on_page_current_changed:**
```python
    def _on_page_current_changed(self, current: QModelIndex, previous: QModelIndex):
        """页面选择变化 → 显示只读预览 (D-62, D-63)。"""
        note = self._page_list_model.note_at(current)
        if note is not None:
            self._editor_preview.setHtml(note.content or "")
            self._editor_stack.setCurrentIndex(0)
        else:
            self._show_editor_placeholder()
```

**New method: _show_editor_placeholder:**
```python
    def _show_editor_placeholder(self):
        """显示 placeholder 提示文字 (D-63)。"""
        self._editor_preview.clear()
        self._editor_stack.setCurrentIndex(1)
```

**New method: _setup_tree_context_menu** (follows _setup_menu_bar pattern, lines 58-110):
```python
    def _setup_tree_context_menu(self):
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(self._on_tree_context_menu)

    def _on_tree_context_menu(self, pos):
        """分区树右键菜单 (D-56)。"""
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        proxy_index = self._tree_view.indexAt(pos)

        if proxy_index.isValid():
            source_index = self._section_filter.mapToSource(proxy_index)
            item: SNoteItem = source_index.internalPointer()
            menu.addAction("新建子分区", self._on_new_child_section)
            menu.addAction("新建页面", self._on_new_page_in_section)
            menu.addSeparator()
            menu.addAction("重命名分区", self._on_rename_section)
            menu.addAction("删除分区", self._on_delete_section)
        else:
            menu.addAction("新建分区", self._on_new_root_section)

        menu.exec(self._tree_view.viewport().mapToGlobal(pos))
```

**New method: _setup_page_context_menu:**
```python
    def _setup_page_context_menu(self):
        self._list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_view.customContextMenuRequested.connect(self._on_page_context_menu)

    def _on_page_context_menu(self, pos):
        """页面列表右键菜单 (D-56)。"""
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        proxy_index = self._list_view.indexAt(pos)

        if proxy_index.isValid():
            menu.addAction("重命名页面", self._on_rename_page)
            menu.addAction("删除页面", self._on_delete_page)
        else:
            menu.addAction("新建页面", self._on_new_page)

        menu.exec(self._list_view.viewport().mapToGlobal(pos))
```

**New method: _setup_navigation_shortcuts** (follows QAction with QKeySequence pattern from lines 62-111):
```python
    def _setup_navigation_shortcuts(self):
        """键盘快捷键 (D-57): Delete 删除、F2 重命名、Ctrl+N 新建页面。"""
        # Delete key — context-sensitive based on focused view
        self._act_delete = QAction("删除", self)
        self._act_delete.setShortcut(QKeySequence.StandardKey.Delete)
        self._tree_view.addAction(self._act_delete)
        self._list_view.addAction(self._act_delete)
        self._act_delete.triggered.connect(self._on_delete_selected)

        # F2 for rename — handled by EditTriggers, also add as action
        self._act_rename = QAction("重命名", self)
        self._act_rename.setShortcut(QKeySequence("F2"))
        self._tree_view.addAction(self._act_rename)
        self._list_view.addAction(self._act_rename)
        self._act_rename.triggered.connect(self._on_rename_selected)

        # Ctrl+N for new page (only applies when page list is focused)
        self._act_new_page = QAction("新建页面", self)
        self._act_new_page.setShortcut(QKeySequence("Ctrl+N"))
        self._list_view.addAction(self._act_new_page)
        self._act_new_page.triggered.connect(self._on_new_page)
```

**New method: _initialize_navigation_state** (D-52, D-53):
```python
    def _initialize_navigation_state(self):
        """打开笔记本后自动选中第一个子分区并展开第一层 (D-52, D-53)。"""
        # D-53: Expand first level of proxy model
        proxy = self._section_filter
        for row in range(proxy.rowCount()):
            index = proxy.index(row, 0, QModelIndex())
            self._tree_view.expand(index)

        # D-52: Auto-select first child section
        root_index = proxy.index(0, 0, QModelIndex())
        if root_index.isValid():
            self._tree_view.setCurrentIndex(root_index)
```

**New method: _on_new_root_section** (CRUD handlers follow mark_dirty pattern, D-61):
```python
    def _on_new_root_section(self):
        """创建顶级分区。"""
        section = SNoteItem.new_section("新分区")
        self._tree_model.add_item(QModelIndex(), section)
        self.mark_dirty()
```

**New method: _on_new_child_section:**
```python
    def _on_new_child_section(self):
        """在选中的分区下创建子分区。"""
        current = self._tree_view.currentIndex()
        if not current.isValid():
            return
        source_index = self._section_filter.mapToSource(current)
        parent_item: SNoteItem = source_index.internalPointer()
        section = SNoteItem.new_section("新分区")
        self._tree_model.add_item(source_index, section)
        self.mark_dirty()
```

**New method: _on_new_page / _on_new_page_in_section / on_rename_* / _on_delete_*:** All follow the same pattern:
```python
    def _on_*** (self):
        # 1. Get current selection from appropriate view
        # 2. Map proxy index to source if needed
        # 3. Perform CRUD on model
        # 4. Call self.mark_dirty() (D-61)
```

**Status bar messages pattern** (from lines 327 and 372):
```python
        self.statusBar().showMessage("就绪")              # line 176
        self.statusBar().showMessage("新建笔记本 - 未保存")  # line 327
        self.statusBar().showMessage("笔记本已保存")        # line 394
```

---

### 5. `tests/model/test_section_filter_proxy.py` (test, assertions)

**Analog:** `tests/model/test_tree_model.py` (test file structure, fixtures, class organization)

**Imports pattern** (lines 1-10 of test_tree_model.py):
```python
"""Tests for SectionFilterProxy - QSortFilterProxyModel 分区过滤。

测试递归过滤、section/note 混合树过滤、autoAcceptChildRows 行为 (NAV-01)。
"""

import pytest
from PySide6.QtCore import QModelIndex, Qt

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.tree_model import TreeModel
from src.secnotepad.model.section_filter_proxy import SectionFilterProxy
```

**Fixtures pattern** (lines 16-47 of test_tree_model.py):
```python
@pytest.fixture
def sample_tree():
    """创建混合 section + note 树供过滤测试。

    根分区 (section, hidden)
    └── 工作 (section)
        ├── 周报 (note)
        └── 项目A (section)
            ├── 需求文档 (note)
            └── 子分区 (section)
                └── 子笔记 (note)
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    report = SNoteItem.new_note("周报")
    project = SNoteItem.new_section("项目A")
    doc = SNoteItem.new_note("需求文档")
    sub_section = SNoteItem.new_section("子分区")
    sub_note = SNoteItem.new_note("子笔记")
    sub_section.children.append(sub_note)
    project.children.append(doc)
    project.children.append(sub_section)
    work.children.append(report)
    work.children.append(project)
    root.children.append(work)
    return root


@pytest.fixture
def proxy(sample_tree):
    """创建 SectionFilterProxy + TreeModel 组合。"""
    model = TreeModel(sample_tree)
    proxy = SectionFilterProxy()
    proxy.setSourceModel(model)
    return proxy
```

**Test class organization** (lines 53-403 of test_tree_model.py):
```python
class TestSectionFilterProxy:
    """SectionFilterProxy 过滤行为测试。"""

    def test_filter_only_sections(self, sample_tree, proxy):
        """代理模型 rowCount 只计 section 节点。"""
        # TreeModel root has 1 child ("工作"), but that's a section
        pass

    def test_notes_filtered_out(self, sample_tree, proxy):
        """note 节点被过滤，不在代理模型中显示。"""
        pass

    def test_recursive_filtering_nested(self, sample_tree, proxy):
        """递归过滤确保深层 section 可见 (Qt6 feature)。"""
        pass

    def test_map_to_source(self, sample_tree, proxy):
        """mapToSource 正确映射 proxy index → source index。"""
        pass

    def test_source_model_changes_propagate(self, sample_tree, proxy):
        """源模型添加 section 后代理自动更新。"""
        pass
```

---

### 6. `tests/model/test_page_list_model.py` (test, assertions)

**Analog:** `tests/model/test_tree_model.py` (test structure, fixture patterns)

**Imports and fixtures** (following test_tree_model.py pattern):
```python
"""Tests for PageListModel - QAbstractListModel 页面列表 (NAV-02, NAV-04)。"""

import pytest
from PySide6.QtCore import QModelIndex, Qt

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.page_list_model import PageListModel


@pytest.fixture
def section_with_notes():
    """创建含多个 note 子节点的 section。"""
    section = SNoteItem.new_section("测试分区")
    section.children.append(SNoteItem.new_note("页面1", "内容1"))
    section.children.append(SNoteItem.new_note("页面2", "内容2"))
    empty_section = SNoteItem.new_section("子分区")
    section.children.append(empty_section)  # 不应出现在列表
    return section


@pytest.fixture
def list_model(section_with_notes):
    """创建关联 section 的 PageListModel。"""
    model = PageListModel()
    model.set_section(section_with_notes)
    return model


class TestPageListModel:
    """PageListModel 基本行为测试。"""

    def test_row_count_excludes_sections(self, list_model):
        """rowCount 只计数 note 类型子节点。"""
        assert list_model.rowCount() == 2

    def test_data_returns_title(self, list_model):
        """data(DisplayRole) 返回页面标题。"""
        idx = list_model.index(0, 0)
        assert list_model.data(idx, Qt.DisplayRole) == "页面1"

    def test_set_section_clears_previous(self, list_model):
        """set_section(None) 清空列表。"""
        list_model.set_section(None)
        assert list_model.rowCount() == 0

    def test_setdata_rename(self, list_model):
        """setData(EditRole) 重命名成功。"""
        idx = list_model.index(0, 0)
        assert list_model.setData(idx, "新标题", Qt.EditRole)
        assert list_model.data(idx, Qt.DisplayRole) == "新标题"

    def test_setdata_reject_empty(self, list_model):
        """setData 空字符串返回 False (D-60)。"""
        idx = list_model.index(0, 0)
        assert not list_model.setData(idx, "", Qt.EditRole)
        assert not list_model.setData(idx, "   ", Qt.EditRole)

    def test_add_note(self, list_model):
        """add_note 追加新页面。"""
        note = SNoteItem.new_note("新页面")
        assert list_model.add_note(note)
        assert list_model.rowCount() == 3

    def test_remove_note(self, list_model):
        """remove_note 删除页面。"""
        idx = list_model.index(0, 0)
        assert list_model.remove_note(idx)
        assert list_model.rowCount() == 1

    def test_flags_editable(self, list_model):
        """flags 包含 ItemIsEditable。"""
        idx = list_model.index(0, 0)
        assert list_model.flags(idx) & Qt.ItemIsEditable
```

---

### 7. `tests/ui/test_navigation.py` (test, integration)

**Analog:** `tests/ui/test_main_window.py` (MainWindow fixture, class organization, assertions on UI state)

**Imports pattern** (lines 1-8 of test_main_window.py):
```python
"""Tests for Navigation System integration (NAV-03, D-62, D-63, D-64)。"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QTextEdit

from src.secnotepad.ui.main_window import MainWindow
```

**Window fixture pattern** (lines 14-21 of test_main_window.py):
```python
@pytest.fixture
def window_with_notebook(qapp):
    """创建已打开笔记本的 MainWindow。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    yield w
    w.close()
    w.deleteLater()
```

**Test class pattern** (lines 27-30 of test_main_window.py):
```python
class TestNavigationSetup:
    """Phase 3: 导航系统初始化 (D-49~D-53)。"""

    def test_section_filter_proxy_set(self, window_with_notebook):
        assert window_with_notebook._section_filter is not None

    def test_tree_view_uses_proxy(self, window_with_notebook):
        assert window_with_notebook._tree_view.model() is window_with_notebook._section_filter

    def test_page_list_model_set(self, window_with_notebook):
        assert window_with_notebook._page_list_model is not None

    def test_list_view_uses_page_model(self, window_with_notebook):
        assert window_with_notebook._list_view.model() is window_with_notebook._page_list_model

    def test_editor_area_created(self, window_with_notebook):
        assert isinstance(window_with_notebook._editor_preview, QTextEdit)
        assert window_with_notebook._editor_preview.isReadOnly()
```

---

### 8. `tests/model/test_tree_model.py` — MODIFY: add setData tests

**Analog:** self — extensible test class following existing pattern

**Add new test class** (following mutation test pattern lines 317-375 of test_tree_model.py):
```python
# ── setData tests (Phase 3: EditRole rename) ──


class TestTreeModelSetData:
    """TreeModel.setData() EditRole 重命名测试 (NAV-03)。"""

    def test_setdata_rename_section(self, sample_tree):
        """setData(EditRole) 重命名 section 标题。"""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        assert model.setData(work, "工作区", Qt.EditRole)
        assert model.data(work, Qt.DisplayRole) == "工作区"
        assert sample_tree.children[0].title == "工作区"  # source data updated

    def test_setdata_reject_empty(self, sample_tree):
        """setData 空字符串返回 False (D-60)。"""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        assert not model.setData(work, "", Qt.EditRole)
        assert not model.setData(work, "   ", Qt.EditRole)

    def test_setdata_wrong_role(self, sample_tree):
        """非 EditRole 的 setData 返回 False。"""
        model = TreeModel(sample_tree)
        work = model.index(0, 0, QModelIndex())
        assert not model.setData(work, "test", Qt.DisplayRole)

    def test_setdata_invalid_index(self, sample_tree):
        """无效索引 setData 返回 False。"""
        model = TreeModel(sample_tree)
        assert not model.setData(QModelIndex(), "test", Qt.EditRole)
```

---

### 9. `tests/conftest.py` — MODIFY: ensure sample_tree fixture sufficient

**Analog:** self — verify existing fixture covers Phase 3 needs

**Current fixture** (lines 26-44 of conftest.py):
```python
@pytest.fixture
def sample_tree() -> SNoteItem:
    """创建 3 层示例 SNoteItem 树。

    根分区 (section, hidden in TreeModel)
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

**Assessment:** This fixture already has mixed section/note nodes, making it suitable for SectionFilterProxy filtering tests. However, the `test_tree_model.py` local fixture IS different (note the test file has its own `sample_tree` fixture that shadows the conftest one). The conftest fixture is used by other test files. Both are structurally similar and both are adequate for Phase 3 testing.

**No modification needed** -- the existing `sample_tree` fixture in conftest.py is sufficient for Phase 3.

**Note for test_section_filter_proxy.py:** Can reuse `conftest.py::sample_tree` or define its own with deeper nesting.

---

## Shared Patterns

### Implementation

**Imports convention** (all model files):
```python
from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from .snote_item import SNoteItem
```

**Imports convention** (all UI files):
```python
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QMainWindow, ...)
from PySide6.QtGui import QAction, QKeySequence
from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
```

**Section comment convention** (all files):
```python
    # ── 段落标题 ──
```

**Qt signal connection pattern:**
```python
    self._tree_selection = self._tree_view.selectionModel()
    self._tree_selection.currentChanged.connect(self._on_tree_current_changed)
```

**Dirty flag pattern (D-61):**
```python
    self.mark_dirty()  # Called after every structural change
```

**Test imports pattern:**
```python
import pytest
from PySide6.QtCore import QModelIndex, Qt
from src.secnotepad.model.snote_item import SNoteItem
```

**Test fixture pattern:**
```python
@pytest.fixture
def window(qapp):
    w = MainWindow()
    w.show()
    yield w
    w.close()
    w.deleteLater()
```

### Critical Pitfall Mitigations (extracted from RESEARCH.md)

**Pitfall 1: Proxy Model Index Confusion**
Always call `mapToSource()` before working with source model indices:
```python
source_index = self._section_filter.mapToSource(proxy_index)
```

**Pitfall 2: EditTriggers After setModel**
Always set `EditTriggers` AFTER `setModel()`:
```python
self._tree_view.setModel(self._section_filter)  # First
self._tree_view.setEditTriggers(...)             # Then
```

**Pitfall 3: selectionModel Rebuilt by setModel**
Always reconnect signals AFTER `setModel()`:
```python
self._tree_view.setModel(self._section_filter)  # First
self._tree_selection = self._tree_view.selectionModel()  # Then
self._tree_selection.currentChanged.connect(...)          # Then
```

**Pitfall 4: autoAcceptChildRows Must Be False**
```python
self.setAutoAcceptChildRows(False)  # Critical in SectionFilterProxy.__init__
```

**Pitfall 5: Object Reference Consistency**
PageListModel._notes must reference SAME objects as _section.children (no copies).

**Pitfall 6: Signal Feedback Loop**
Use `currentChanged` instead of `selectionChanged` for view selection monitoring.

**Pitfall 7: Clear PageListModel After Section Deletion**
When deleting the currently selected section, reset PageListModel.set_section(None).

---

## No Analog Found

No files lack analogs. All new files have clear role-matching or exact-matching analogs in the existing codebase.

---

## Metadata

**Analog search scope:** `src/secnotepad/model/`, `src/secnotepad/ui/`, `tests/`
**Files scanned:** 8 existing source files (tree_model.py, snote_item.py, main_window.py, password_dialog.py, welcome_widget.py, test_tree_model.py, test_main_window.py, conftest.py)
**Pattern extraction date:** 2026-05-08
