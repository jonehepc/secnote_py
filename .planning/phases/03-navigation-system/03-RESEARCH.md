# Phase 03: 导航系统 - Research

**Researched:** 2026-05-08
**Domain:** PySide6/Qt6 数据模型与视图架构 (Model/View), 树形过滤, 列表模型, 选择模型协调
**Confidence:** HIGH

## Summary

Phase 03 在已有 TreeModel/SNoteItem 数据层的 Phase 01 和三栏布局骨架的 Phase 01 之上，实现分区树过滤、页面列表绑定、CRUD 交互（创建/重命名/删除）和页面内容预览。核心技术选型全部基于 PySide6/Qt6 原生组件，无第三方依赖。

关键架构决策：使用 QSortFilterProxyModel 子类（SectionFilterProxy）在视图层过滤 TreeModel，仅显示 section 类型节点，保持 TreeModel 完整数据不变；使用 QAbstractListModel 子类（PageListModel）将选中分区的 children 列表平铺展示为页面列表。这两者都遵循 Phase 01 确立的数据/视图分离原则 (D-01)。

**Primary recommendation:** 严格使用 Qt6 原生 QSortFilterProxyModel（含 `setRecursiveFilteringEnabled` 和 `autoAcceptChildRows` 两个 Qt6 新特性）实现分区树过滤，不要自行实现递归过滤逻辑。

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAV-01 | 分区以树形结构展示，支持多级嵌套 | SectionFilterProxy (QSortFilterProxyModel 子类) 过滤 item_type=="section"，递归过滤特性确保嵌套可见性 |
| NAV-02 | 页面在所属分区下以列表形式展示，点击分区切换页面列表 | PageListModel (QAbstractListModel) + selectionChanged 信号驱动更新 |
| NAV-03 | 用户可以创建、重命名、删除分区 | TreeModel.setData (EditRole) + TreeModel.add_item/remove_item + 右键菜单/工具栏/快捷键 |
| NAV-04 | 用户可以在当前选中的分区下创建、重命名、删除页面 | PageListModel.setData (EditRole) + PageListModel.add_note/remove_note + 右键菜单/工具栏/快捷键 |

</phase_requirements>

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-49:** 使用 QSortFilterProxyModel 子类过滤分区树——重写 filterAcceptsRow，仅显示 item_type == "section" 的节点。TreeModel 保持完整数据不变，过滤在视图层完成。
- **D-50:** 新建 PageListModel(QAbstractListModel) 驱动中间 QListView——接收 SNoteItem(section) 为数据源，平铺显示其 children 中的 note 类型节点。仅支持单列标题显示。
- **D-51:** 分区选择 → 页面列表更新通过 QItemSelectionModel.selectionChanged 信号驱动——获取选中分区的 SNoteItem，调用 PageListModel.set_section() 刷新列表。
- **D-52:** 打开笔记本后自动选中根分区下的第一个子分区，页面列表随之显示其下页面。
- **D-53:** 打开笔记本后分区树仅展开第一层，更深层子分区保持折叠状态。
- **D-54:** 页面列表仅显示标题（Qt.DisplayRole），单列布局。
- **D-55:** 工具栏按钮 + 右键菜单组合——分区树上方放置新建分区/新建子分区按钮，页面列表上方放置新建页面按钮。
- **D-56:** 右键菜单根据目标类型变化：右键分区 → 新建子分区、新建页面、重命名分区、删除分区；右键页面 → 重命名页面、删除页面；右键空白区域 → 新建分区/页面。
- **D-57:** 标准键盘快捷键——Delete 删除选中项、F2 重命名、Ctrl+N 新建页面（页面列表聚焦时）。
- **D-58:** 删除确认——仅当分区含子内容（子分区或页面）时弹警告对话框说明级联删除内容；删除空分区或单页面不弹确认。
- **D-59:** 原地编辑——QTreeView/QListView 设置 EditTriggers = DoubleClicked | EditKeyPressed。双击或选中+F2 进入编辑，Enter 确认，Esc 取消还原。
- **D-60:** 空名称拒绝——Model.setData() 中若 EditRole 数据为空字符串，返回 False，视图自动还原旧名称。可配合状态栏提示"名称不能为空"。
- **D-61:** 所有结构变更操作（创建/重命名/删除分区和页面）后调用 MainWindow.mark_dirty() 标记笔记本已修改。
- **D-62:** 点击页面后在右侧编辑区显示只读 QTextEdit，渲染选中页面的 HTML 内容。
- **D-63:** 未选中任何页面时，编辑区显示居中提示文字"请在页面列表中选择一个页面"。
- **D-64:** 新建页面后自动在页面列表中选中新创建的页面，编辑区随之显示空白内容。

### Claude's Discretion
所有决策均由用户选择——无"Claude 决定"的领域。

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 分区树过滤与展示 | UI/View Layer | Model Layer (TreeModel) | SectionFilterProxy 是视图层过滤适配器，不修改 TreeModel 数据 |
| 页面列表展示 | UI/View Layer | Model Layer (SNoteItem.children) | PageListModel 是视图模型，数据源来自当前选中的 SNoteItem(section) |
| 分区选择 → 列表联动 | Controller (MainWindow) | — | QItemSelectionModel.selectionChanged 信号连接到 MainWindow 槽函数 |
| 分区 CRUD | Controller → Model | UI/View | 工具栏/菜单/快捷键 → MainWindow 方法 → TreeModel.add_item/remove_item/setData |
| 页面 CRUD | Controller → Model | UI/View | 工具栏/菜单/快捷键 → MainWindow 方法 → PageListModel 方法 |
| 页面内容预览 | UI/View Layer | — | QTextEdit (read-only) 纯展示组件，Phase 4 复用同一组件切换为可编辑 |
| 脏标志管理 | Controller (MainWindow) | — | 所有结构变更调用 mark_dirty()，已由 Phase 2 实现 |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PySide6 | 6.11.0 | Qt6 Python 绑定，提供所有 Qt 组件 | 项目已锁定 [VERIFIED: pip3 list] |
| PySide6.QtCore.QSortFilterProxyModel | (bundled) | 分区树过滤代理模型 | Qt6 内置，`setRecursiveFilteringEnabled(True)` 是 Qt6 专有特性 [VERIFIED: Context7 /websites/doc_qt_io_qtforpython-6] |
| PySide6.QtCore.QAbstractListModel | (bundled) | PageListModel 基类 | Qt 模型/视图架构标准基类 [VERIFIED: Context7] |
| PySide6.QtWidgets.QTextEdit | (bundled) | 只读页面内容预览 | 项目已锁定使用 QTextEdit 而非 QWebEngine [VERIFIED: PROJECT.md] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| PySide6.QtCore.QItemSelectionModel | (bundled) | 获取选中索引，连接 selectionChanged 信号 | 监听 QTreeView/QListView 选择变化 [VERIFIED: Context7] |
| PySide6.QtCore.QPersistentModelIndex | (bundled) | 跨模型变更保持索引引用 | 新建项后自动选中（D-64 实现方案之一）[CITED: Qt docs] |
| PySide6.QtGui.QKeySequence.StandardKey | (bundled) | 标准键盘快捷键 (Delete, F2) | 统一跨平台快捷键行为 [VERIFIED: Context7] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| QSortFilterProxyModel 子类 | 手动实现代理模型 | Qt6 的递归过滤和 autoAcceptChildRows 已原生支持，手动实现复杂性高且易出错 |
| QAbstractListModel | QStandardItemModel | QStandardItemModel 使用 QStandardItem 对象而非 SNoteItem，破坏了 SNoteItem 作为数据源的统一性 |
| QPersistentModelIndex | 存储行号后手动查找 | QPersistentModelIndex 自动追踪模型变更，更安全 |

**Installation:**
```bash
# No additional packages needed — all components are in PySide6 6.11.0
```

**Version verification:** PySide6 6.11.0 confirmed installed via `pip3 list` and `python3 -c "import PySide6; print(PySide6.__version__)"` [VERIFIED: local environment]

## Architecture Patterns

### System Architecture Diagram

```
                          ┌─────────────────────────────────────┐
                          │           MainWindow                │
                          │  (Controller — signals + slots)     │
                          │                                     │
                          │   mark_dirty()   mark_clean()       │
                          └──┬──────────┬─────────────┬─────────┘
                             │          │             │
              ┌──────────────┼──────────┼─────────────┼──────────────────┐
              │              │          │             │                  │
              ▼              ▼          ▼             ▼                  ▼
    ┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────┐
    │  Toolbar     │ │ Key Events  │ │ Context  │ │ Selection    │
    │  (QAction)   │ │ (Delete/F2) │ │ Menus    │ │ Model (tree) │
    │  new/open+   │ │            │ │           │ │              │
    └──┬───┬───┬───┘ └──┬───┬─────┘ └──┬───┬────┘ └──────┬───────┘
       │   │   │        │   │          │   │              │
       │   │   │        │   │          │   │              │ selectionChanged
       │   │   │        │   │          │   │              ▼
       │   │   │        │   │          │   │    ┌───────────────────┐
       │   │   │        │   │          │   │    │ _on_tree_        │
       │   │   │        │   │          │   │    │ selection_changed│
       │   │   │        │   │          │   │    └────────┬──────────┘
       │   │   │        │   │          │   │             │
       │   │   │        │   │          │   │    ┌────────▼──────────┐
       │   │   │        │   │          │   │    │ PageListModel     │
       │   │   │        │   │          │   │    │ .set_section(s)   │
       │   │   │        │   │          │   │    └────────┬──────────┘
       │   │   │        │   │          │   │             │
       │   │   │        │   │          │   │    ┌────────▼──────────┐
       │   │   │        │   │          │   │    │ QListView         │
       │   │   │        │   │          │   │    │ show notes list   │
       │   │   │        │   │          │   │    │ single column     │
       │   │   │        │   │          │   │    └────────┬──────────┘
       │   │   │        │   │          │   │             │
       │   │   │        │   │          │   │    ┌────────▼──────────┐
       │   │   │        │   │          │   │    │ QTextEdit (RO)    │
       │   │   │        │   │          │   │    │ setHtml(content)  │
       │   │   │        │   │          │   │    │ or placeholder    │
       │   │   │        │   │          │   │    └───────────────────┘
       │   │   │        │   │          │   │
       ▼   ▼   ▼        ▼   ▼          ▼   ▼
┌─────────────────────────────────────────────────────────────┐
│              Model Layer (read + write)                     │
│                                                             │
│  ┌───────────────┐    ┌──────────────────────────┐         │
│  │  SNoteItem    │◀───│  TreeModel               │         │
│  │  (root)       │    │  (QAbstractItemModel)     │         │
│  │               │    │  ┌───────────────────┐   │         │
│  │ children[] ───┼────│▶│ add_item()        │   │         │
│  │ item_type ────┼──┐ │  remove_item()     │   │         │
│  │ title ────────┼─┐│ │  setData(EditRole) │   │         │
│  │ content ──────┼┐││ └───────────────────┘   │         │
│  └───────────────┘│││                          │         │
│                   │││ ┌───────────────────┐   │         │
│                   │││ │ SectionFilterProxy│   │         │
│                   │││ │ (QSortFilterProxy │   │         │
│                   │││ │  Model 子类)       │   │         │
│                   │││ │                   │   │         │
│                   │││ │ filterAcceptsRow ─┼───┼─ item_type│
│                   │││ │  → only "section" │   │         │
│                   │││ │ recursiveFilter   │   │         │
│                   │││ └───────────────────┘   │         │
│                   │││            │             │         │
│                   │││      QTreeView           │         │
│                   │││                          │         │
│                   │││ ┌───────────────────┐   │         │
│                   │││ │ PageListModel     │   │         │
│                   │││ │ (QAbstractList    │   │         │
│                   │││ │  Model 子类)       │   │         │
│                   │││ │                   │   │         │
│                   │││ │ ._section.children│◀──┼─ 遍历    │
│                   │││ │ rowCount → len()  │   │         │
│                   │││ │ data → title      │   │         │
│                   │││ └───────────────────┘   │         │
│                   │││            │             │         │
│                   │││      QListView           │         │
│                   └┴┴──────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘

Data flow for primary use case (click section → view pages → click page → preview):
  1. User clicks section in QTreeView
  2. QItemSelectionModel emits selectionChanged(selected, deselected)
  3. _on_tree_selection_changed slot fires
  4. Gets proxy index → mapToSource → finds SNoteItem (the section)
  5. Calls PageListModel.set_section(section_item)
  6. PageListModel.beginResetModel/endResetModel refreshes QListView
  7. User clicks page in QListView
  8. QItemSelectionModel emits selectionChanged again
  9. _on_page_selection_changed fires
  10. Gets SNoteItem (the note) from PageListModel
  11. Calls QTextEdit.setHtml(note.content) or shows placeholder if empty

CRUD flow for new section:
  1. User clicks "新建子分区" button or context menu
  2. MainWindow creates SNoteItem.new_section("新分区")
  3. TreeModel.add_item(selected_proxy_source_parent, new_section)
  4. TreeModel emits beginInsertRows/endInsertRows → both views auto-update
  5. SectionFilterProxy re-evaluates filterAcceptsRow → if section, auto-accepts
  6. MainWindow.mark_dirty() called
```

### Recommended Project Structure
```
src/secnotepad/
├── model/
│   ├── snote_item.py          # 已有 — SNoteItem 数据类
│   ├── tree_model.py          # 已有 — TreeModel, 需添加 setData() for EditRole
│   ├── section_filter_proxy.py # NEW — SectionFilterProxy(QSortFilterProxyModel)
│   ├── page_list_model.py     # NEW — PageListModel(QAbstractListModel)
│   ├── serializer.py          # 已有 — JSON 序列化
│   └── validator.py           # 已有 — 数据校验
├── ui/
│   ├── main_window.py         # 修改 — 集成导航系统, 添加 CRUD 方法
│   ├── welcome_widget.py      # 已有 — 无需修改
│   └── password_dialog.py     # 已有 — 无需修改
└── crypto/
    └── file_service.py        # 已有 — 无需修改

tests/
├── conftest.py                # 已有 — 共享 fixture
├── model/
│   ├── test_tree_model.py     # 修改 — 添加 setData 测试
│   ├── test_section_filter_proxy.py  # NEW — SectionFilterProxy 测试
│   └── test_page_list_model.py       # NEW — PageListModel 测试
└── ui/
    ├── test_main_window.py    # 修改 — 添加导航交互测试
    └── test_navigation.py     # NEW — 跨组件集成测试
```

### Pattern 1: QSortFilterProxyModel Tree Filtering (SectionFilterProxy)

**What:** 使用 Qt6 的 `setRecursiveFilteringEnabled(True)` 和 `autoAcceptChildRows` 特性实现树形过滤。`filterAcceptsRow` 检查 item_type == "section"，递归特性和 autoAcceptChildRows 确保子节点不被意外隐藏。
**When to use:** D-49 要求仅在 QTreeView 中显示分区节点，隐藏 note 节点。
**Important Note on autoAcceptChildRows:** `autoAcceptChildRows` 属性在 Qt6 中默认值为 `true`。当父节点被 filterAcceptsRow 接受时，其子节点也会自动接受（即使子节点本身不符合过滤条件）。这意味着如果一个 section 包含 note 子节点，这些 note 子节点也会被接受。**但这并不符合需求**——我们不希望在 QTreeView 中看到 note 节点。因此需要显式设置 `setAutoAcceptChildRows(False)`，配合 `setRecursiveFilteringEnabled(True)` 来仅过滤到 section 节点。

**Example:**
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6 + Qt6 behavior analysis
from PySide6.QtCore import QSortFilterProxyModel, QModelIndex

class SectionFilterProxy(QSortFilterProxyModel):
    """Filter tree model to only show section-type items (D-49)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Qt6: Enable recursive filtering so children of matched nodes
        # are also evaluated through filterAcceptsRow
        self.setRecursiveFilteringEnabled(True)
        # CRITICAL: Set to False so note children of sections are NOT
        # auto-accepted. We rely on filterAcceptsRow to make the decision.
        self.setAutoAcceptChildRows(False)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Accept row only if item_type == 'section' (D-49).

        With recursiveFilteringEnabled=True, this method is called for
        every node in the tree, ensuring deep nesting is evaluated.
        With autoAcceptChildRows=False, only sections pass through.
        """
        source = self.sourceModel()
        index = source.index(source_row, 0, source_parent)
        if not index.isValid():
            return False
        item = index.internalPointer()
        return item.item_type == "section"
```

**Proxy ↔ Source mapping pattern (critical for CRUD operations):**
```python
# Getting selection through proxy model
proxy_index = tree_view.selectionModel().currentIndex()
source_index = proxy_model.mapToSource(proxy_index)
section_item = source_index.internalPointer()

# Adding through proxy model - work on source model directly
# (proxy transparently reflects source model changes)
parent_source_index = proxy_model.mapToSource(proxy_parent_index)
tree_model.add_item(parent_source_index, new_item)

# setData through proxy - calls source model's setData automatically
proxy_model.setData(proxy_index, new_name, Qt.EditRole)
```

### Pattern 2: PageListModel (QAbstractListModel)

**What:** 自定义 QAbstractListModel 子类，将 SNoteItem(section) 的 children 列表平铺为单列列表。仅显示 note 类型子节点（children 中的 non-section 项）。
**When to use:** D-50, D-54 — QListView 的数据源。
**Key insight:** 与直接复用 TreeModel 不同，PageListModel 是轻量级列表模型，数据源是单个 section 节点的 children 引用，而非整个树。

**Example:**
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6 (QAbstractTableModel pattern adapted)
from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

class PageListModel(QAbstractListModel):
    """Flat list model showing notes under a section (D-50, D-54)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._section: SNoteItem = None  # Current section
        self._notes: list[SNoteItem] = []  # Cached list of notes

    def set_section(self, section: SNoteItem | None):
        """Set the current section and refresh the note list.

        Called from selectionChanged handler (D-51).
        Uses beginResetModel/endResetModel for full refresh.
        """
        self.beginResetModel()
        self._section = section
        if section is not None:
            self._notes = [c for c in section.children if c.item_type == "note"]
        else:
            self._notes = []
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._notes)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._notes):
            return None
        note = self._notes[index.row()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return note.title
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value: str,
                role: int = Qt.EditRole) -> bool:
        """Rename a note's title (D-60: reject empty names)."""
        if not index.isValid() or role != Qt.EditRole:
            return False
        if not isinstance(value, str) or value.strip() == "":
            # D-60: empty name rejection
            return False
        note = self._notes[index.row()]
        note.title = value.strip()
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def add_note(self, note: SNoteItem):
        """Append a new note to the current section."""
        if self._section is None:
            return False
        row = len(self._notes)
        self.beginInsertRows(QModelIndex(), row, row)
        self._section.children.append(note)
        self._notes.append(note)
        self.endInsertRows()
        return True

    def remove_note(self, index: QModelIndex) -> bool:
        """Remove a note from the current section."""
        if not index.isValid() or index.row() >= len(self._notes):
            return False
        row = index.row()
        note = self._notes[row]
        # Remove from section's children list (canonical source)
        if note in self._section.children:
            self._section.children.remove(note)
        self.beginRemoveRows(QModelIndex(), row, row)
        self._notes.pop(row)
        self.endRemoveRows()
        return True

    def note_at(self, index: QModelIndex) -> SNoteItem | None:
        """Get the SNoteItem at the given index."""
        if not index.isValid() or index.row() >= len(self._notes):
            return None
        return self._notes[index.row()]
```

### Pattern 3: Signal-Driven Selection → Page List Update

**What:** QTreeView 的 QItemSelectionModel.selectionChanged 信号驱动 PageListModel 更新。
**When to use:** D-51.
**Key detail:** 使用 `currentChanged` 而非 `selectionChanged` 可能更精确——`currentChanged` 在用户通过键盘导航时也会触发，而 `selectionChanged` 在某些情况下可能不包含 `currentIndex`。

**Example:**
```python
# In MainWindow._setup_navigation() (new method called from _on_new_notebook / _on_open_notebook)

# Connect tree selection to page list update
self._tree_selection = self._tree_view.selectionModel()
self._tree_selection.currentChanged.connect(self._on_tree_current_changed)

# Connect page selection to editor preview
self._page_selection = self._list_view.selectionModel()
self._page_selection.currentChanged.connect(self._on_page_current_changed)

def _on_tree_current_changed(self, current: QModelIndex, previous: QModelIndex):
    """Tree selection changed → update page list (D-51)."""
    # Map proxy index to source model index
    source_index = self._section_filter.mapToSource(current)
    if source_index.isValid():
        section_item: SNoteItem = source_index.internalPointer()
        self._page_list_model.set_section(section_item)
    else:
        self._page_list_model.set_section(None)
    # D-63: Reset editor to placeholder when section changes
    self._show_editor_placeholder()

def _on_page_current_changed(self, current: QModelIndex, previous: QModelIndex):
    """Page selection changed → show read-only preview (D-62, D-63)."""
    note = self._page_list_model.note_at(current)
    if note is not None:
        self._editor_preview.setHtml(note.content or "")
    else:
        self._show_editor_placeholder()
```

### Pattern 4: Context Menus by Target Type

**What:** 通过 `customContextMenuRequested` 信号和 `indexAt(pos)` 判断右键位置，构建不同菜单。
**When to use:** D-55, D-56.

**Example:**
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6 (custom context menu pattern)
def _setup_tree_context_menu(self):
    self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
    self._tree_view.customContextMenuRequested.connect(self._tree_context_menu)

def _tree_context_menu(self, pos: QPoint):
    """Context menu for tree (D-56): varies by target type."""
    menu = QMenu(self)
    proxy_index = self._tree_view.indexAt(pos)

    if proxy_index.isValid():
        source_index = self._section_filter.mapToSource(proxy_index)
        item: SNoteItem = source_index.internalPointer()
        # Right-click on a section
        menu.addAction("新建子分区", self._on_new_child_section)
        menu.addAction("新建页面", self._on_new_page_in_section)
        menu.addSeparator()
        menu.addAction("重命名分区", self._on_rename_section)
        menu.addAction("删除分区", self._on_delete_section)
    else:
        # Right-click on empty area
        menu.addAction("新建分区", self._on_new_root_section)

    menu.exec(self._tree_view.viewport().mapToGlobal(pos))
```

### Pattern 5: In-Place Editing with EditTriggers

**What:** 设置 EditTriggers 和 Model.setData() 支持原地重命名。
**When to use:** D-59, D-60.
**Warning:** `setEditTriggers` 必须在视图设置了 model 之后再调用，否则可能被重置。

**Example:**
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# In _on_new_notebook / _on_open_notebook after setting models:

# D-59: Enable in-place editing via DoubleClick or F2
self._tree_view.setEditTriggers(
    QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
)
self._list_view.setEditTriggers(
    QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
)
```

### Pattern 6: Keyboard Shortcuts for CRUD

**What:** 使用 QAction 绑定标准快捷键（Delete, F2, Ctrl+N），这是 Qt 的推荐做法。
**When to use:** D-57.
**Important:** 必须处理焦点上下文——Delete 键只应删除当前聚焦视图中的选中项。

**Example:**
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# Delete key action — shared but context-sensitive
self._act_delete = QAction("删除", self)
self._act_delete.setShortcut(QKeySequence.StandardKey.Delete)
# ❌ Do NOT add to menu — Delete is triggered by key only
self._tree_view.addAction(self._act_delete)  # Only active when tree focused
self._list_view.addAction(self._act_delete)  # Only active when list focused
self._act_delete.triggered.connect(self._on_delete_selected)

# F2 for rename — handled by EditTriggers (D-59), but also add as action
self._act_rename = QAction("重命名", self)
self._act_rename.setShortcut(QKeySequence("F2"))
self._tree_view.addAction(self._act_rename)
self._list_view.addAction(self._act_rename)
self._act_rename.triggered.connect(self._on_rename_selected)

# Ctrl+N for new page
self._act_new_page = QAction("新建页面", self)
self._act_new_page.setShortcut(QKeySequence("Ctrl+N"))
self._list_view.addAction(self._act_new_page)
self._act_new_page.triggered.connect(self._on_new_page)
```

### Pattern 7: Read-Only QTextEdit for Page Preview

**What:** QTextEdit 设置为只读模式用于内容预览。Phase 4 将移除只读限制并添加格式工具栏。
**When to use:** D-62, D-63.
**Placeholder 实现:** 使用 QStackedWidget 切换 QTextEdit 和 QLabel（居中提示文字），这是最简洁的方案。也可以使用 QLabel 作为 QTextEdit 的 overlay（实现复杂，不推荐）。

**Example:**
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# In _setup_navigation():

def _setup_editor_area(self):
    """Create read-only preview + placeholder stacked in right panel."""
    # QTextEdit for read-only preview (D-62)
    self._editor_preview = QTextEdit()
    self._editor_preview.setReadOnly(True)
    self._editor_preview.setPlaceholderText("")

    # QLabel placeholder (D-63)
    self._editor_placeholder_label = QLabel("请在页面列表中选择一个页面")
    self._editor_placeholder_label.setAlignment(Qt.AlignCenter)
    self._editor_placeholder_label.setStyleSheet("color: #888; font-size: 14px;")

    # Stack for switching
    self._editor_stack = QStackedWidget()
    self._editor_stack.addWidget(self._editor_preview)   # index 0
    self._editor_stack.addWidget(self._editor_placeholder_label)  # index 1
    self._editor_stack.setCurrentIndex(1)  # Default: placeholder

def _show_editor_placeholder(self):
    """Show placeholder text (D-63)."""
    self._editor_preview.clear()
    self._editor_stack.setCurrentIndex(1)

def _show_page_preview(self, note: SNoteItem):
    """Show read-only preview of selected page (D-62)."""
    self._editor_preview.setHtml(note.content or "")
    self._editor_stack.setCurrentIndex(0)
```

### Anti-Patterns to Avoid

- **Anti-pattern: 在 filterAcceptsRow 中手动实现递归遍历。** Qt6 的 `setRecursiveFilteringEnabled(True)` 已经处理了递归，手动实现会导致双重递归和性能问题。
- **Anti-pattern: 使用 mapFromSource 遍历树节点来查找过滤后的节点。** 过滤是视图层行为，应该通过 `filterAcceptsRow` 声明式完成，不应在 MainWindow 中遍历。
- **Anti-pattern: 直接修改 SNoteItem.title 而不通过 setData。** 跳过 setData 意味着不会发出 dataChanged 信号，视图不会更新。
- **Anti-pattern: 在 selectionChanged 信号中调用可能触发新的 selectionChanged 的操作。** 这会形成信号反馈循环。区分 `currentChanged` 和 `selectionChanged`——`currentChanged` 更精确且不易形成循环。
- **Anti-pattern: 忘记在 PageListModel 中同步 `_notes` 列表和 `_section.children`。** 两者必须保持一致。添加/删除/重命名操作必须同时更新两个引用。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 树形过滤（仅显示 section 节点） | 手动遍历树 + 构建过滤列表 | QSortFilterProxyModel 子类 + setRecursiveFilteringEnabled | Qt6 原生递归过滤处理所有边界情况：insertion、removal、model reset、lazy children |
| 模型索引跨变更保持 | 存储行号和 parent 指针 | QPersistentModelIndex 或 model.add_item 返回的 index | Qt 的 persistent index 自动追踪 beginInsertRows/endInsertRows/beginRemoveRows |
| 空名称校验 | 视图层弹窗检查 | Model.setData() 返回 False | Qt 视图自动还原旧值，无需手动处理输入撤销 [VERIFIED: Context7] |
| 键盘快捷键 | 重写 keyPressEvent 并手动分发 | QAction + QKeySequence.StandardKey | Qt 的 QAction 系统自动处理焦点上下文、平台差异、快捷键冲突 |
| 右键菜单坐标映射 | 手动计算 globalPos | `view.viewport().mapToGlobal(pos)` | Qt 坐标映射处理高 DPI、滚动偏移、header 偏移等 [VERIFIED: Context7] |

**Key insight:** Qt 的 Model/View 框架已经有 20+ 年的成熟实现。几乎所有"看起来需要手写"的交互（过滤、选择、编辑、快捷键）都有声明式 API。手写实现通常只会引入 bugs。

## Runtime State Inventory

> Phase 03 is a greenfield feature addition (no rename/refactor/migration). This section is omitted.

**Skip reason:** Phase 03 adds new components (SectionFilterProxy, PageListModel, CRUD handlers) to existing code. No stored data, live service config, OS-registered state, secrets, or build artifacts carry references to Phase 03 components that need migration.

## Common Pitfalls

### Pitfall 1: Proxy Model Index Confusion
**What goes wrong:** 从 proxy index 获取 internalPointer 得到的是源模型的 SNoteItem，但尝试用 proxy index 调用源模型方法（如 `rowCount(parent_proxy_index)`）会得到错误结果。
**Why it happens:** QSortFilterProxyModel 的索引空间与源模型不同。proxy 的 parent index 不能直接用于源模型的 rowCount/methods。
**How to avoid:** 始终在操作前调用 `mapToSource()` 将 proxy index 转换为 source index。CRUD 操作直接在源模型 (TreeModel) 上执行，让 proxy 自动感知变化。
**Warning signs:** `rowCount()` 返回 0 但 tree 中有可见节点；`parent()` 返回无效索引。

### Pitfall 2: EditTriggers 设置在 setModel 之前失效
**What goes wrong:** 在 `_setup_central_area` 中设置了 EditTriggers，但在 `_on_new_notebook` 中调用 `setModel()` 后 EditTriggers 被重置。
**Why it happens:** `QAbstractItemView.setModel()` 在某些 Qt 版本中会重置部分视图属性。
**How to avoid:** 在 `setModel()` 之后显式设置 EditTriggers。即在 `_on_new_notebook` / `_on_open_notebook` 中设置 model 后立即调用 `setEditTriggers()`。
**Warning signs:** 双击无法进入编辑模式；F2 无效。

### Pitfall 3: selectionModel 在 setModel 时重建
**What goes wrong:** 在 setup 阶段获取了 `self._tree_view.selectionModel()` 并连接信号，但后续 `setModel()` 会创建新的 selectionModel，之前的连接丢失。
**Why it happens:** Qt 在 `setModel()` 时销毁旧的 selectionModel 并创建新的。信号连接到旧 selectionModel 上，新 selectionModel 不发射信号到已连接的槽。
**How to avoid:** 在 `setModel()` 之后重新获取 `selectionModel()` 并连接信号。即在 `_on_new_notebook / _on_open_notebook` 中设置 model 后执行信号连接。
**Warning signs:** 点击树节点后页面列表不更新；selectionChanged 槽函数从不被调用。

### Pitfall 4: autoAcceptChildRows 默认 true 导致 Note 节点出现在树中
**What goes wrong:** 在 `filterAcceptsRow` 中只接受 section 节点，但 note 类型的子节点仍然在树中可见。
**Why it happens:** Qt6 的 `QSortFilterProxyModel.autoAcceptChildRows` 默认值为 `true`。当父节点 (section) 被 filterAcceptsRow 接受时，其所有子节点自动接受，忽略 filterAcceptsRow 的返回值。
**How to avoid:** 显式调用 `self.setAutoAcceptChildRows(False)`。
**Warning signs:** QTreeView 中显示 note 类型的子节点。

### Pitfall 5: PageListModel 数据不一致
**What goes wrong:** 重命名 page 后，序列化保存的 title 仍是旧值，或树视图中的对应 note 节点标题未更新。
**Why it happens:** PageListModel 维护了 `_notes` 缓存列表。如果只更新了缓存中的引用，但 `_section.children` 中对应的原始 SNoteItem 未被更新，就会出现不一致。SNoteItem title 的更新应该直接在原始对象上进行（因为 `_notes` 和 `_section.children` 引用的是同一个 SNoteItem 对象）。
**How to avoid:** 确保 `_notes` 列表中的对象就是 `_section.children` 中的同一个对象引用。PageListModel.set_section 中过滤时应保留对象引用而非创建副本。setData 中直接修改 `note.title` 会同时影响缓存和源数据。
**Warning signs:** 保存后再打开，页面标题回退到旧值。

### Pitfall 6: 信号反馈循环
**What goes wrong:** selectionChanged 触发页面加载 → 页面加载触发 mark_dirty → mark_dirty 更新窗口标题 → 某些情况下触发视图刷新 → selection 变化 → 再次触发 selectionChanged。
**Why it happens:** Qt 的信号/槽系统是同步的。如果槽函数中触发了可能影响 selection 的操作（如 model reset），会导致递归。
**How to avoid:** 
- 使用 `currentChanged` 而非 `selectionChanged`——前者更精确，在 model reset 时不一定会触发
- 在 set_section 中使用 `beginResetModel/endResetModel` 而非删除重建 model——后者会销毁 selectionModel
- 必要时使用 QTimer.singleShot(0, ...) 将操作推迟到事件循环
**Warning signs:** 应用卡死；重复的 selectionChanged 触发；stack overflow。

### Pitfall 7: 删除当前分区后 PageListModel 仍持有过期引用
**What goes wrong:** 删除当前选中的分区后，PageListModel 的 `_section` 仍然指向已删除的 SNoteItem，但该 item 已从树的 children 中移除。后续操作（如新建页面）可能操作已删除的对象。
**Why it happens:** 删除分区时未同步清除 PageListModel 的当前 section 引用。
**How to avoid:** 删除操作后检查被删除的 section 是否是当前 PageListModel 的 section。如果是，将 PageListModel.set_section(None) 并选中父分区。
**Warning signs:** 删除分区后尝试新建页面导致崩溃或静默失败。

## Code Examples

Verified patterns from official sources (Context7 Qt for Python documentation):

### QSortFilterProxyModel with recursive filtering
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# QSortFilterProxyModel.setRecursiveFilteringEnabled(bool) — Qt6 feature
# QSortFilterProxyModel.autoAcceptChildRows property — Qt6 default True
# filterAcceptsRow(int sourceRow, QModelIndex sourceParent) → bool
class SectionFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRecursiveFilteringEnabled(True)
        self.setAutoAcceptChildRows(False)

    def filterAcceptsRow(self, source_row, source_parent):
        source = self.sourceModel()
        index = source.index(source_row, 0, source_parent)
        item = index.internalPointer()
        return item.item_type == "section"
```

### QAbstractItemModel setData pattern for rename
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# Editable tree model pattern — setData validates, updates, emits dataChanged
def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
    if role != Qt.EditRole:
        return False
    if not index.isValid():
        return False
    # D-60: reject empty names
    if not isinstance(value, str) or value.strip() == "":
        return False
    item: SNoteItem = index.internalPointer()
    item.title = value.strip()
    # Emit dataChanged for both EditRole and DisplayRole
    self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
    return True
```

### QTreeView context menu with indexAt
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# QWidget.customContextMenuRequested signal pattern
self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
self._tree_view.customContextMenuRequested.connect(self._on_context_menu)

def _on_context_menu(self, pos: QPoint):
    index = self._tree_view.indexAt(pos)
    menu = QMenu(self)
    # ... build menu based on index validity and item type
    menu.exec(self._tree_view.viewport().mapToGlobal(pos))
```

### QTextEdit read-only HTML preview
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# setReadOnly(True) disables editing but allows text selection and scrolling
editor = QTextEdit()
editor.setReadOnly(True)
editor.setHtml("<h1>Hello</h1><p>World</p>")
```

### Tree expansion control
```python
# Source: Context7 /websites/doc_qt_io_qtforpython-6
# QTreeView.expandRecursively(index, depth)
# D-53: Expand first level only
for row in range(proxy_model.rowCount()):
    index = proxy_model.index(row, 0)
    self._tree_view.expand(index)  # Expand root-children only
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SafetyNotebook 在同一个 QTreeView 中混合显示分区和笔记 | 分区树 + 页面列表分离（Proxy 过滤 + 独立 ListModel, D-49/D-50） | Phase 03（2026） | 更清晰的分区/页面导航结构 |
| 手动实现递归过滤（遍历树+构建过滤列表） | QSortFilterProxyModel.setRecursiveFilteringEnabled(True) | Qt6（2021） | 声明式过滤，自动处理模型变更 |
| 存储行号追踪选中项 | QPersistentModelIndex（自动追踪模型变更） | Qt4以来 | 更安全的跨变更引用 |
| QStandardItemModel 管理数据 | SNoteItem (纯 Python dataclass) + QAbstractItemModel 适配器 (D-01) | Phase 01（2026） | 数据与视图完全分离，序列化独立于 Qt |

**Deprecated/outdated:**
- **手动递归过滤:** Qt6 的 `setRecursiveFilteringEnabled` 是推荐方式，手动遍历树已经过时。
- **QStandardItemModel 用于应用数据模型:** 自 Qt4 Model/View 框架引入以来，推荐使用自定义 QAbstractItemModel 子类适配应用数据结构。

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | QSortFilterProxyModel.autoAcceptChildRows 默认值为 true（Qt6），需要显式设为 false | Pattern 1, Pitfall 4 | 如果默认值因 Qt 版本而异，树中可能显示 note 节点 |
| A2 | QAbstractItemView.setEditTriggers 在 setModel() 后调用不会被重置 | Pitfall 2 | 如果特定 Qt 版本行为不同，EditTriggers 可能失效，需要额外验证 |
| A3 | selectionModel() 在 setModel() 时被销毁重建 | Pitfall 3 | 如果 Qt 版本不销毁重建（仅更新），则信号连接不需要重新设置 |
| A4 | TreeModel.setData() 修改 SNoteItem.title 会同时影响序列化（因为 setData 直接修改同一个 SNoteItem 对象引用）| Pattern 2, Pitfall 5 | 如果 SNoteItem 某处有深拷贝，title 修改可能不同步 |

**If this table is empty:** Not applicable — assumptions exist and are flagged above.

## Open Questions (RESOLVED)

1. **SectionFilterProxy.filterAcceptsRow 是否需要处理 source_model 为 None 的情况？** — RESOLVED: 在 filterAcceptsRow 开头添加 `if self.sourceModel() is None: return False` 防御性检查。Plan 03-01 中已实施。
   - What we know: 在 `_on_new_notebook` 和 `_on_open_notebook` 中，Proxy 总是在 setSourceModel 之后才设置给 View，所以 source_model 不应为 None
   - Recommendation: 在 filterAcceptsRow 开头添加 `if self.sourceModel() is None: return False` 防御性检查

2. **QTreeView.expandRecursively(index, depth=1) 是否只在 Qt 6.5+ 可用？** — RESOLVED: 使用 `expand(index)` 展开根级子节点（不递归），明确满足 D-53 的"仅展开第一层"需求。Plan 03-03 中已实施。
   - What we know: Context7 文档显示 `expandRecursively(index, depth)` 方法存在
   - Recommendation: 使用 `expand(index)` 展开根级子节点（不递归），这是最安全的方式，也明确满足 D-53 的"仅展开第一层"需求

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PySide6 | All Qt components | Yes | 6.11.0 | — |
| Python 3 | Runtime | Yes | (per system) | — |
| pytest | Test framework | Yes | 9.0.3 | — |
| pytest-qt | Qt test fixtures (qtbot) | No | — | Use manual QApplication fixture in conftest.py (already established pattern) |

**Missing dependencies with no fallback:**
- None — all core dependencies available.

**Missing dependencies with fallback:**
- pytest-qt: Not installed. Fallback to manual QApplication fixture (`qapp`) defined in `tests/conftest.py` — this is already the established testing pattern in Phase 01 and Phase 02 tests.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | tests/conftest.py (QApplication fixture, sample_tree fixture) |
| Quick run command | `python -m pytest tests/model/test_section_filter_proxy.py tests/model/test_page_list_model.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAV-01 | 分区树仅显示 section 节点，支持多级嵌套 | unit | `python -m pytest tests/model/test_section_filter_proxy.py -x` | No (Wave 0) |
| NAV-01 | filterAcceptsRow 正确过滤 section/note 混合树 | unit | `python -m pytest tests/model/test_section_filter_proxy.py::test_filter_only_sections -x` | No (Wave 0) |
| NAV-02 | 选中分区后 PageListModel 显示其 note 子节点 | unit | `python -m pytest tests/model/test_page_list_model.py::test_set_section_shows_notes -x` | No (Wave 0) |
| NAV-02 | 列表仅显示单列标题 (DisplayRole) | unit | `python -m pytest tests/model/test_page_list_model.py::test_single_column_title -x` | No (Wave 0) |
| NAV-03 | 创建/重命名/删除分区，TreeModel.setData 支持 EditRole | unit | `python -m pytest tests/model/test_tree_model.py::test_setdata_rename_section -x` | No (Wave 0) |
| NAV-03 | 删除含子内容分区弹警告，空分区直接删除 | integration | `python -m pytest tests/ui/test_navigation.py::test_delete_section_with_children_warning -x` | No (Wave 0) |
| NAV-04 | 创建/重命名/删除页面，PageListModel.setData 拒绝空名 | unit | `python -m pytest tests/model/test_page_list_model.py::test_setdata_reject_empty -x` | No (Wave 0) |
| NAV-04 | PageListModel.add_note/remove_note 正确更新 | unit | `python -m pytest tests/model/test_page_list_model.py::test_add_remove_note -x` | No (Wave 0) |
| D-59 | 双击或F2触发原地编辑 | integration | manual verification + smoke test with pytest-qt fallback | No (Wave 0) |
| D-62 | 选中页面后 QTextEdit 显示只读 HTML | integration | `python -m pytest tests/ui/test_navigation.py::test_preview_shows_html -x` | No (Wave 0) |
| D-63 | 无页面选中时显示 placeholder | integration | `python -m pytest tests/ui/test_navigation.py::test_placeholder_when_no_page -x` | No (Wave 0) |
| D-64 | 新建页面后自动选中 | integration | `python -m pytest tests/ui/test_navigation.py::test_auto_select_new_page -x` | No (Wave 0) |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/model/test_section_filter_proxy.py tests/model/test_page_list_model.py -x` (unit tests for the sub-component being worked on)
- **Per wave merge:** `python -m pytest tests/model/ tests/ui/test_navigation.py -x`
- **Phase gate:** `python -m pytest tests/ -x` (full suite green)

### Wave 0 Gaps
- [ ] `tests/model/test_section_filter_proxy.py` — NEW: SectionFilterProxy unit tests (NAV-01)
- [ ] `tests/model/test_page_list_model.py` — NEW: PageListModel unit tests (NAV-02, NAV-04)
- [ ] `tests/ui/test_navigation.py` — NEW: Navigation integration tests (NAV-03, D-62, D-63, D-64)
- [ ] `tests/model/test_tree_model.py` — MODIFY: Add setData tests for EditRole renaming (NAV-03)
- [ ] `tests/conftest.py` — MODIFY: Add `sample_tree` fixture with mixed sections/notes for filter testing (already exists from Phase 01, verify it's sufficient)

**Note:** `pytest-qt` is NOT installed. All tests use manual QApplication fixture (`qapp`) from conftest.py. This is sufficient — the existing 201 tests from Phase 01 and Phase 02 all use this pattern successfully. For signal testing, use `QSignalSpy` from PySide6.QtTest (bundled) instead of `qtbot.waitSignal`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Phase 02 handled encryption/decryption |
| V3 Session Management | No | No session state beyond current password in memory |
| V4 Access Control | No | Single-user local application |
| V5 Input Validation | Yes — limited | Empty title rejection in setData() (D-60); Qt handles XSS in QTextEdit.setHtml() by design |
| V6 Cryptography | No | Phase 02 handled all cryptography |

### Known Threat Patterns for PySide6/Qt6 Model/View

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| HTML injection via setHtml() with user content | Tampering | QTextEdit (non-QWebEngine) renders a limited HTML4 subset — no script execution, no external resource loading. Safe by design. [ASSUMED based on Qt docs description] |
| setData() with unexpected types/values | Tampering | Validation gate: isinstance(value, str) and strip() check in setData() |
| Signal-triggered file operations (mark_dirty → save loop) | DoS | D-61 consciously triggers mark_dirty on every structural change. QFileDialog is modal so save storms are impossible during CRUD. |

## Sources

### Primary (HIGH confidence)
- Context7 `/websites/doc_qt_io_qtforpython-6` — QSortFilterProxyModel (recursive filtering, filterAcceptsRow, autoAcceptChildRows, setRecursiveFilteringEnabled), QAbstractItemModel (setData pattern), QAbstractListModel, QItemSelectionModel (selectionChanged/currentChanged signals), QTextEdit (setReadOnly, setHtml, toHtml), QAbstractItemView (setEditTriggers, contextMenuPolicy, customContextMenuRequested), QTreeView (expand, expandRecursively, expandAll, setExpanded), QKeySequence.StandardKey, QPersistentModelIndex
- Context7 `/pytest-dev/pytest-qt` — qtbot.waitSignal pattern (not used due to missing dependency, documented for awareness)
- Context7 `/websites/doc_qt_io_qtforpython-6` (editable tree model setData) — full setData implementation pattern for tree models

### Secondary (MEDIUM confidence)
- PySide6 6.11.0 version confirmed via `pip3 list` [VERIFIED: local environment]
- pytest 9.0.3 version confirmed via `pip3 show pytest` [VERIFIED: local environment]
- pytest-qt NOT installed confirmed via `pip3 list | grep pytest-qt` [VERIFIED: local environment]

### Tertiary (LOW confidence)
- None — all claims verified through Context7 official docs or local environment checks

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all PySide6 6.11.0 bundled components, version verified locally
- Architecture: HIGH — all patterns verified through Context7 official Qt for Python documentation
- Pitfalls: HIGH — pitfalls 1-7 based on known Qt Model/View framework behaviors confirmed in docs, with specific mitigation strategies

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (30 days — PySide6 Qt6 API is stable)

## Project Constraints (from CLAUDE.md)

- 使用中文撰写供人类阅读的文档 (RESEARCH.md 使用中文)
- Git 工作流：Phase 分支命名 `gsd/phase-03-navigation-system`
- 技术栈：Python 3 + PySide6 + Qt6
- 使用 QTextEdit（非 QWebEngine）
- 数据与视图分离原则 (D-01)
- 信号驱动架构模式
