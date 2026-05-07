# Phase 1: 项目框架与数据模型 - Pattern Map

**Mapped:** 2026-05-07
**Files analyzed:** 18
**Analogs found:** 7 / 18 (greenfield project -- analogs from old C++/Qt5 project and RESEARCH.md patterns)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/secnotepad/__init__.py` | config | none | -- | none (std boilerplate) |
| `src/secnotepad/__main__.py` | config | startup | `SafetyNotebook/main.cpp` | role-match |
| `src/secnotepad/app.py` | config | startup | `SafetyNotebook/main.cpp` | role-match |
| `src/secnotepad/model/__init__.py` | config | none | -- | none (std boilerplate) |
| `src/secnotepad/model/snote_item.py` | model | CRUD | `SafetyNotebook/snoteitem.h` + `.cpp` | exact (data model) |
| `src/secnotepad/model/tree_model.py` | model | request-response | RESEARCH.md Qt TreeItem pattern | partial (no direct analog) |
| `src/secnotepad/model/serializer.py` | utility | transform | `SafetyNotebook/snoteitem.cpp` (toJson/fromJson) | exact (serialization) |
| `src/secnotepad/model/validator.py` | utility | request-response | -- | none (new addition) |
| `src/secnotepad/ui/__init__.py` | config | none | -- | none (std boilerplate) |
| `src/secnotepad/ui/main_window.py` | component | event-driven | `SafetyNotebook/mainwindow.h` + `.cpp` | role-match (QMainWindow) |
| `src/secnotepad/ui/welcome_widget.py` | component | event-driven | -- | none (new addition) |
| `pyproject.toml` | config | none | -- | none (new project) |
| `tests/conftest.py` | config | none | -- | none (new addition) |
| `tests/model/test_snote_item.py` | test | CRUD | -- | none (new addition) |
| `tests/model/test_tree_model.py` | test | request-response | -- | none (new addition) |
| `tests/model/test_serializer.py` | test | transform | -- | none (new addition) |
| `tests/model/test_validator.py` | test | request-response | -- | none (new addition) |
| `tests/ui/test_main_window.py` | test | event-driven | -- | none (new addition) |

## Pattern Assignments

### `src/secnotepad/__main__.py` (config, startup)

**Analog:** `/home/jone/projects/SafetyNotebook/SafetyNotebook/main.cpp` lines 1-9

**Core pattern** (lines 4-9):
```cpp
int main(int argc, char *argv[]) {
    QApplication a(argc, argv);
    MainWindow w;
    w.show();
    return a.exec();
}
```

**Translation to Python pattern (from RESEARCH.md lines 744-760):**
```python
import sys
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SecNotepad")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

**Key differences from C++ analog:**
- Python uses `sys.argv` instead of `argc/argv`
- `app.setApplicationName()` replaces C++ project metadata
- `sys.exit(app.exec())` instead of bare `return a.exec()`
- Conditional `if __name__ == "__main__"` guard (Python convention absent in C++)

---

### `src/secnotepad/model/snote_item.py` (model, CRUD)

**Analog:** `/home/jone/projects/SafetyNotebook/SafetyNotebook/snoteitem.h` lines 14-61 + `.cpp` lines 1-137

**Imports pattern** (from RESEARCH.md lines 332-337):
```python
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
```

**Core data class pattern** (from RESEARCH.md lines 339-386):
```python
@dataclass
class SNoteItem:
    id: str = ""
    title: str = ""
    item_type: str = "note"    # "section" | "note"
    content: str = ""
    children: List["SNoteItem"] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def create_id() -> str:
        """生成 32 字符 hex UUID (D-05)"""
        return uuid.uuid4().hex

    @staticmethod
    def now_iso() -> str:
        """生成 ISO 8601 时间戳 (D-10)"""
        return datetime.now(timezone.utc).isoformat()

    @classmethod
    def new_section(cls, title: str) -> "SNoteItem":
        """创建分区"""
        now = cls.now_iso()
        return cls(
            id=cls.create_id(),
            title=title,
            item_type="section",
            children=[],
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def new_note(cls, title: str, content: str = "") -> "SNoteItem":
        """创建笔记叶子节点"""
        now = cls.now_iso()
        return cls(
            id=cls.create_id(),
            title=title,
            item_type="note",
            content=content,
            children=[],
            created_at=now,
            updated_at=now,
        )
```

**Fields mapped from old C++ SNoteItem** (`snoteitem.h` lines 56-60, `snoteitem.cpp` lines 85-99):
| C++ Field | C++ Type | Python Field | Python Type | Notes |
|---|---|---|---|---|
| `_id` | `QUuid*` | `id` | `str` (hex) | C++ UUID with braces, Python hex 32-char (D-05) |
| `_title` | `QString` | `title` | `str` | Same |
| `_content` | `QString` | `content` | `str` | Same |
| `_childrens` | `QList<SNoteItem*>` | `children` | `List[SNoteItem]` | C++ raw ptr list, Python list |
| `_type` | `SNoteItemType` | `item_type` | `str` | C++ enum (Partition/Note), Python str ("section"/"note") |
| (none) | -- | `tags` | `List[str]` | New field not in C++ version |
| (none) | -- | `created_at` | `str` (ISO 8601) | New field not in C++ version |
| (none) | -- | `updated_at` | `str` (ISO 8601) | New field not in C++ version |

**Key differences from C++ analog:**
- Python `@dataclass` replaces C++ manual getter/setter boilerplate (`snoteitem.cpp` lines 32-78)
- Migrated from `SNoteItemType` enum (Partition=0 / Note=1) to string `item_type` ("section" / "note")
- `children` uses `field(default_factory=list)` to avoid mutable default trap (RESEARCH.md trap 4, lines 316-319)
- Added `tags`, `created_at`, `updated_at` fields not present in C++ version
- `create_id()` returns `uuid.uuid4().hex` (32-char no-dash) instead of C++ `QUuid::createUuid().toString(WithBraces)`
- Factory methods `new_section()` / `new_note()` replace C++ constructor overloads

---

### `src/secnotepad/model/tree_model.py` (model, request-response)

**Analog:** Qt 6 Simple Tree Model Example (no direct codebase analog -- old project used `QStandardItemModel`)

**Imports pattern** (from RESEARCH.md lines 462-466):
```python
from PySide6.QtCore import (QAbstractItemModel, QModelIndex, Qt)
from .snote_item import SNoteItem
```

**Core QAbstractItemModel pattern -- TreeModel** (from RESEARCH.md lines 468-584):

**Required method contracts** (lines 476-537):
| Method | Signature | Behavior |
|---|---|---|
| `index()` | `(row, column, parent) -> QModelIndex` | `hasIndex` guard, resolve parent item, `createIndex(row, col, child_item)` |
| `parent()` | `(index) -> QModelIndex` | Return `QModelIndex()` if parent is root (hidden root, D-04); `_find_parent()` traversal |
| `rowCount()` | `(parent) -> int` | Guard: `if parent.column() > 0: return 0`; count parent's children |
| `columnCount()` | `(parent) -> int` | Return `1` (single-column tree) |
| `data()` | `(index, role) -> Any` | Return `item.title` for `Qt.DisplayRole` |
| `flags()` | `(index) -> Qt.ItemFlags` | `Qt.ItemIsEnabled \| Qt.ItemIsSelectable` |
| `headerData()` | `(section, orientation, role)` | Return `"笔记分区"` for horizontal header |

**Hidden root pattern** (from RESEARCH.md lines 469, 498-503):
```python
self._root_item = root_item  # type=section, not shown in UI

# In parent():
if parent_item is None or parent_item is self._root_item:
    return QModelIndex()  # root not visible
```

**Tree traversal helpers** (from RESEARCH.md lines 541-558):
```python
@staticmethod
def _find_parent(root: SNoteItem, target: SNoteItem) -> SNoteItem:
    """在树中查找 target 的父节点"""
    for child in root.children:
        if child is target:
            return root
        found = TreeModel._find_parent(child, target)
        if found:
            return found
    return None

@staticmethod
def _child_row(parent: SNoteItem, child: SNoteItem) -> int:
    """返回 child 在 parent.children 中的索引"""
    for i, c in enumerate(parent.children):
        if c is child:
            return i
    return -1
```

**Data mutation methods (Phase 3 integration)** (from RESEARCH.md lines 560-583):
```python
def add_item(self, parent_index: QModelIndex, item: SNoteItem):
    """添加子节点"""
    parent_item = (parent_index.internalPointer()
                   if parent_index.isValid() else self._root_item)
    row = len(parent_item.children)
    self.beginInsertRows(parent_index, row, row)
    parent_item.children.append(item)
    self.endInsertRows()

def remove_item(self, index: QModelIndex) -> bool:
    """删除节点及其子树"""
    if not index.isValid():
        return False
    item = index.internalPointer()
    parent_idx = self.parent(index)
    parent_item = (parent_idx.internalPointer()
                   if parent_idx.isValid() else self._root_item)
    row = parent_item.children.index(item)
    self.beginRemoveRows(parent_idx, row, row)
    del parent_item.children[row]
    self.endRemoveRows()
    return True
```

**Key differences from old C++ pattern:**
- Old project used `QStandardItemModel` with `SNoteItem` subclassing `QStandardItem` (data+view coupled)
- New model uses `QAbstractItemModel` subclass with pure data class `SNoteItem` + `internalPointer()` (data/view separated per D-01)
- `_find_parent()` is O(n) traversal without parent back-reference (performance acceptable for < 10K nodes)
- `createIndex(row, col, item)` stores the data pointer; `index.internalPointer()` retrieves it

---

### `src/secnotepad/model/serializer.py` (utility, transform)

**Analog:** `/home/jone/projects/SafetyNotebook/SafetyNotebook/snoteitem.cpp` lines 56-133 (toJson/fromJson)

**Imports pattern** (from RESEARCH.md lines 391-393):
```python
import json
from dataclasses import asdict
from .snote_item import SNoteItem
```

**Core serialization pattern -- to_json** (from RESEARCH.md lines 396-407):
```python
@staticmethod
def to_json(root: SNoteItem) -> str:
    """SNoteItem 树 → JSON 字符串"""
    data = asdict(root)
    document = {
        "version": 1,                          # D-11: 版本号
        "data": data,                          # D-08: 嵌套树
    }
    return json.dumps(document, ensure_ascii=False, indent=2)
```

**Core deserialization pattern -- from_json** (from RESEARCH.md lines 409-431):
```python
@staticmethod
def from_json(json_str: str) -> SNoteItem:
    """JSON 字符串 → SNoteItem 树"""
    document = json.loads(json_str)
    version = document.get("version", 1)       # 未来可用于格式升级
    data = document["data"]
    return Serializer._from_dict(data)

@staticmethod
def _from_dict(d: dict) -> SNoteItem:
    """递归反序列化"""
    children = [Serializer._from_dict(c) for c in d.get("children", [])]
    return SNoteItem(
        id=d["id"],
        title=d["title"],
        item_type=d["item_type"],
        content=d.get("content", ""),
        children=children,
        tags=d.get("tags", []),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
    )
```

**JSON format** (from RESEARCH.md, `snoteitem.cpp` lines 85-99):
```json
{
    "version": 1,
    "data": {
        "id": "a1b2c3d4e5f6...",
        "title": "根分区",
        "item_type": "section",
        "content": "",
        "children": [
            {
                "id": "f7g8h9i0...",
                "title": "工作笔记",
                "item_type": "section",
                "content": "",
                "children": [],
                "tags": [],
                "created_at": "2026-05-07T10:30:00Z",
                "updated_at": "2026-05-07T10:30:00Z"
            }
        ],
        "tags": [],
        "created_at": "...",
        "updated_at": "..."
    }
}
```

**Key differences from C++ analog:**
- C++ used `QJsonObject` + manual field-by-field construction (`snoteitem.cpp` lines 85-99); Python uses `dataclasses.asdict()` recursive conversion
- C++ JSON field `"type"` with values `"Partition"/"Note"`; Python uses `"item_type"` with `"section"/"note"` (snake_case, D-09)
- C++ UUID format `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}` (with braces); Python uses bare 32-char hex
- Python adds `"version"` wrapper (D-11), `"tags"`, `"created_at"`, `"updated_at"` fields
- C++ used `QJsonDocument::Compact`; Python uses `indent=2` for readability (non-encrypted phase)

---

### `src/secnotepad/model/validator.py` (utility, request-response)

**No direct analog in old C++ project.** The old project had no validation layer -- SNoteItem type checking was implicit.

**Pattern from RESEARCH.md** (lines 435-458):
```python
from typing import Optional
from .snote_item import SNoteItem

class ValidationError(Exception):
    pass

class Validator:
    """SNoteItem 规则校验 (D-06)"""

    @staticmethod
    def validate(item: SNoteItem) -> Optional[ValidationError]:
        """校验 SNoteItem 是否符合层级约束 (D-07)"""
        if item.item_type == "note" and item.children:
            return ValidationError(f"Note '{item.title}' cannot have children")
        if item.item_type == "section":
            for child in item.children:
                err = Validator.validate(child)
                if err:
                    return err
        return None
```

**Pattern:** Static utility class with a single `validate()` method that returns either `None` (valid) or a `ValidationError` (invalid). Recursively traverses children for sections. This is a simple validator pattern -- no framework, no schema, pure Python.

---

### `src/secnotepad/ui/main_window.py` (component, event-driven)

**Analog:** `/home/jone/projects/SafetyNotebook/SafetyNotebook/mainwindow.h` (class declaration) + `mainwindow.cpp` (constructor, initUi, setupFileActions/setupEditActions/setupTextActions, refreshTreeView)

**Imports pattern** (from RESEARCH.md lines 591-599):
```python
from PySide6.QtWidgets import (QMainWindow, QWidget, QSplitter,
                                QTreeView, QListView, QStackedWidget,
                                QMenuBar, QToolBar, QStatusBar,
                                QStyle, QAction, QVBoxLayout, QLabel,
                                QPushButton)
from PySide6.QtCore import Qt, QSize
from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
```

**Class structure pattern** (from RESEARCH.md lines 601-606):
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_central_area()
        self._setup_status_bar()

        # 当前笔记本数据
        self._root_item: SNoteItem = None
        self._tree_model: TreeModel = None
```

**Window setup pattern** (RESEARCH.md lines 615-618):
```python
def _setup_window(self):
    self.setWindowTitle("SecNotepad")           # D-19
    self.resize(1200, 800)                     # D-19
    self.setMinimumSize(800, 600)              # D-19
```

**Menu bar pattern** (from RESEARCH.md lines 620-669):
```python
def _setup_menu_bar(self):
    mb = self.menuBar()

    # 文件菜单
    file_menu = mb.addMenu("文件(&F)")
    self._act_new = QAction("新建(&N)", self)
    self._act_new.setShortcut(QKeySequence("Ctrl+N"))
    file_menu.addAction(self._act_new)

    self._act_save = QAction("保存(&S)", self)
    self._act_save.setShortcut(QKeySequence("Ctrl+S"))
    self._act_save.setEnabled(False)           # 灰显 (D-16)
    file_menu.addAction(self._act_save)

    file_menu.addSeparator()

    self._act_exit = QAction("退出(&Q)", self)
    self._act_exit.setShortcut(QKeySequence("Ctrl+Q"))
    self._act_exit.triggered.connect(self.close)
    file_menu.addAction(self._act_exit)

    # 编辑菜单（全部灰显）
    edit_menu = mb.addMenu("编辑(&E)")
    for text in ["撤销(&U)", "重做(&R)", "剪切(&T)", "复制(&C)", "粘贴(&P)"]:
        act = QAction(text, self)
        act.setEnabled(False)
        edit_menu.addAction(act)
```

**Toolbar pattern** (from RESEARCH.md lines 671-686):
```python
def _setup_tool_bar(self):
    tb = self.addToolBar("工具栏")
    tb.setMovable(False)
    style = self.style()

    new_icon = style.standardIcon(QStyle.SP_FileIcon)
    open_icon = style.standardIcon(QStyle.SP_DialogOpenButton)
    save_icon = style.standardIcon(QStyle.SP_DialogSaveButton)
    saveas_icon = style.standardIcon(QStyle.SP_DialogSaveButton)

    self._tb_new = tb.addAction(new_icon, "新建")
    self._tb_open = tb.addAction(open_icon, "打开")
    self._tb_save = tb.addAction(save_icon, "保存")
    self._tb_save.setEnabled(False)
    self._tb_saveas = tb.addAction(saveas_icon, "另存为")
    self._tb_saveas.setEnabled(False)
```

**Central area -- QStackedWidget + QSplitter pattern** (from RESEARCH.md lines 688-728):
```python
def _setup_central_area(self):
    """QStackedWidget: index 0 = 欢迎页, index 1 = 三栏布局 (D-14)"""
    self._stack = QStackedWidget()
    self.setCentralWidget(self._stack)

    # 欢迎页 (D-15)
    welcome = QWidget()
    layout = QVBoxLayout(welcome)
    layout.addStretch()
    layout.addWidget(QLabel("SecNotepad"))
    layout.addWidget(QLabel("安全的本地加密笔记本"))
    self._btn_new = QPushButton("新建笔记本")
    self._btn_open = QPushButton("打开笔记本")
    layout.addWidget(self._btn_new)
    layout.addWidget(self._btn_open)
    layout.addWidget(QLabel("最近文件（功能待实现）"))
    layout.addStretch()

    # 三栏布局 (D-12, D-13)
    splitter = QSplitter(Qt.Horizontal)
    self._tree_view = QTreeView()
    self._tree_view.setMinimumWidth(100)
    splitter.addWidget(self._tree_view)

    self._list_view = QListView()
    self._list_view.setMinimumWidth(100)
    splitter.addWidget(self._list_view)

    self._editor_placeholder = QWidget()
    splitter.addWidget(self._editor_placeholder)

    splitter.setSizes([200, 250, 750])          # D-12
    splitter.setCollapsible(0, True)            # D-13: 左可折叠
    splitter.setCollapsible(1, False)           # D-13: 中始终可见
    splitter.setCollapsible(2, True)            # D-13: 右可折叠

    self._stack.addWidget(welcome)              # index 0
    self._stack.addWidget(splitter)             # index 1
    self._stack.setCurrentIndex(0)              # 默认显示欢迎页
```

**New notebook handler pattern** (from RESEARCH.md lines 733-739):
```python
def _on_new_notebook(self):
    """新建空白笔记本 (D-14)"""
    self._root_item = SNoteItem.new_section("根分区")
    self._tree_model = TreeModel(self._root_item, self)
    self._tree_view.setModel(self._tree_model)
    self._stack.setCurrentIndex(1)              # 切换到三栏布局
    self.statusBar().showMessage("新建笔记本 - 未保存")
```

**Status bar pattern** (RESEARCH.md lines 730-731):
```python
def _setup_status_bar(self):
    self.statusBar().showMessage("就绪")         # D-18
```

**Key differences from C++ analog:**
- Old project used Qt Designer `.ui` file (`mainwindow.ui`) + `ui->setupUi()` (`mainwindow.cpp` line 37); new project builds UI programmatically
- Old project setup order: `initUi() -> setupEditActions() -> setupFileActions() -> setupTextActions()`; new project uses `_setup_window() -> _setup_menu_bar() -> _setup_tool_bar() -> _setup_central_area() -> _setup_status_bar()`
- Old project used `QStandardItemModel` for tree (`mainwindow.cpp` line 34, 324); new project uses custom `TreeModel(QAbstractItemModel)`
- Old project used `_model->appendRow(_note)` to add root to tree (`mainwindow.cpp` line 348); new project uses `QTreeView.setModel(tree_model)` with hidden root
- Old project's `initUi()` (`mainwindow.cpp` lines 319-332) also set widget enabled states; new project handles enabled states per-action in menu/toolbar setup

---

### `src/secnotepad/ui/welcome_widget.py` (component, event-driven)

**No direct analog in old C++ project.** The old project opened directly into the editor view without a welcome page.

**Pattern from RESEARCH.md** (welcome page embedded in main_window.py lines 694-704, extract into separate widget):
```python
class WelcomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(QLabel("SecNotepad"))
        layout.addWidget(QLabel("安全的本地加密笔记本"))
        self._btn_new = QPushButton("新建笔记本")
        self._btn_open = QPushButton("打开笔记本")
        layout.addWidget(self._btn_new)
        layout.addWidget(self._btn_open)
        layout.addWidget(QLabel("最近文件（功能待实现）"))
        layout.addStretch()
```

**Pattern:** Simple QWidget subclass with QVBoxLayout. Signals `_btn_new.clicked` and `_btn_open.clicked` are connected by MainWindow. This is a stateless presentation component -- it emits signals, MainWindow handles logic.

---

### `pyproject.toml` (config, none)

**No direct analog** in old C++ project (used `CMakeLists.txt`).

**Pattern (standard Python src-layout):**
```toml
[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "secnotepad"
version = "0.1.0"
description = "A local encrypted notebook application"
requires-python = ">=3.12"
dependencies = [
    "PySide6>=6.11.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Mapping from old C++ CMakeLists.txt** (`/home/jone/projects/SafetyNotebook/SafetyNotebook/CMakeLists.txt`):
| C++ (CMakeLists.txt) | Python (pyproject.toml) |
|---|---|
| `cmake_minimum_required(VERSION 3.10)` | `[build-system] requires = ["setuptools>=64"]` |
| `project(SafetyNotebook)` | `[project] name = "secnotepad"` |
| `find_package(Qt5 REQUIRED)` | `dependencies = ["PySide6>=6.11.0"]` |
| `add_executable(...)` | (not needed -- `python -m` entry point) |

### Test Files (test, various data flows)

**No direct analogs in old C++ project** (no automated tests existed).

**pytest pattern for model tests:**
```python
# tests/conftest.py
import pytest
from src.secnotepad.model.snote_item import SNoteItem

@pytest.fixture
def sample_tree():
    """创建示例树用于测试"""
    root = SNoteItem.new_section("根分区")
    section = SNoteItem.new_section("工作")
    note = SNoteItem.new_note("笔记1", "内容")
    section.children.append(note)
    root.children.append(section)
    return root
```

**pytest-qt pattern for UI tests** (from RESEARCH.md):
```python
# tests/ui/test_main_window.py
import pytest
from PySide6.QtCore import Qt
from src.secnotepad.ui.main_window import MainWindow

@pytest.fixture
def window(qtbot):
    w = MainWindow()
    qtbot.addWidget(w)
    return w

def test_window_title(window):
    assert window.windowTitle() == "SecNotepad"
```

## Shared Patterns

### QAction Instance Variable Pattern

**Source:** RESEARCH.md lines 322-326 (Trap 5)
**Apply to:** `main_window.py` -- all QAction objects

**Pattern:** Store all QAction objects as instance variables (`self._act_new`, `self._act_save`, etc.) to prevent garbage collection. Do NOT create QAction as local variables that go out of scope.

**From RESEARCH.md trap 5 (lines 322-326):**
> QAction 对象被垃圾回收（Python 没有保持引用）。
> 将 QAction 存储为 MainWindow 的实例变量（`self.new_action = QAction(...)`）。

### Hidden Root Pattern

**Source:** RESEARCH.md lines 217-218, 498-503
**Apply to:** `tree_model.py` -- TreeModel

**Pattern:** TreeModel holds `self._root_item` (SNoteItem, type=section) as hidden root. All public index operations skip the root. `parent()` returns `QModelIndex()` when the parent is `_root_item`. UI never renders the root.

### Qt Convention: rowCount Column Guard

**Source:** RESEARCH.md lines 301-304 (Trap 2)
**Apply to:** `tree_model.py` -- `rowCount()`

**Pattern:** In `rowCount()`, always guard with `if parent.column() > 0: return 0` before any logic. Qt may request rowCount for non-zero columns during tree operations. Without this guard, tree nodes appear duplicated.

### dataclass Mutable Default Value Pattern

**Source:** RESEARCH.md lines 315-319 (Trap 4)
**Apply to:** `snote_item.py` -- `children` and `tags` fields

**Pattern:** Use `field(default_factory=list)` instead of `list = []` for mutable default values:
```python
children: List["SNoteItem"] = field(default_factory=list)
tags: List[str] = field(default_factory=list)
```

### Static Factory Method Pattern for SNoteItem Construction

**Source:** RESEARCH.md lines 361-385
**Apply to:** `snote_item.py`

**Pattern:** Use `@classmethod` factory methods (`new_section()`, `new_note()`) instead of constructor overloads. Each factory sets `item_type`, auto-generates `id`, and sets `created_at`/`updated_at` to current time. The raw constructor remains available for deserialization.

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/secnotepad/model/validator.py` | utility | request-response | Old project had no validation layer |
| `src/secnotepad/ui/welcome_widget.py` | component | event-driven | Old project had no welcome page |
| `pyproject.toml` | config | none | Old project used CMakeLists.txt |
| `tests/conftest.py` | config | none | Old project had no tests |
| `tests/model/test_snote_item.py` | test | CRUD | Old project had no tests |
| `tests/model/test_tree_model.py` | test | request-response | Old project had no tests |
| `tests/model/test_serializer.py` | test | transform | Old project had no tests |
| `tests/model/test_validator.py` | test | request-response | Old project had no tests |
| `tests/ui/test_main_window.py` | test | event-driven | Old project had no tests |
| `src/secnotepad/__init__.py` | config | none | Standard boilerplate |
| `src/secnotepad/model/__init__.py` | config | none | Standard boilerplate |
| `src/secnotepad/ui/__init__.py` | config | none | Standard boilerplate |
| `src/secnotepad/app.py` | config | startup | Thin wrapper around main; RESEARCH.md examples inline in __main__ |

For these files, the planner should use the code examples directly from RESEARCH.md sections 1-6 (lines 330-760) as the primary implementation reference.

## Project Structure Map

```
secnotepad/
├── pyproject.toml                      # Project metadata, pytest config
├── src/
│   └── secnotepad/
│       ├── __init__.py                 # Package marker
│       ├── __main__.py                 # Entry: python -m secnotepad
│       ├── app.py                      # QApplication setup (RESEARCH.md lines 744-760)
│       ├── model/
│       │   ├── __init__.py             # Package marker
│       │   ├── snote_item.py           # SNoteItem dataclass (RESEARCH.md lines 330-386)
│       │   ├── tree_model.py           # TreeModel QAbstractItemModel (RESEARCH.md lines 460-584)
│       │   ├── serializer.py           # JSON serializer (RESEARCH.md lines 388-431)
│       │   └── validator.py            # Validator utility (RESEARCH.md lines 433-458)
│       └── ui/
│           ├── __init__.py             # Package marker
│           ├── main_window.py          # QMainWindow (RESEARCH.md lines 588-740)
│           └── welcome_widget.py       # Welcome page widget (RESEARCH.md lines 694-704)
└── tests/
    ├── conftest.py                     # Shared fixtures
    ├── model/
    │   ├── test_snote_item.py          # SNoteItem unit tests
    │   ├── test_tree_model.py          # TreeModel integration tests
    │   ├── test_serializer.py          # JSON round-trip tests
    │   └── test_validator.py           # Validation rule tests
    └── ui/
        └── test_main_window.py         # MainWindow Qt integration tests
```

## Metadata

**Analog search scope:**
- `/home/jone/projects/SafetyNotebook/SafetyNotebook/snoteitem.h` -- SNoteItem data model (C++/Qt5)
- `/home/jone/projects/SafetyNotebook/SafetyNotebook/snoteitem.cpp` -- SNoteItem implementation + JSON serialization
- `/home/jone/projects/SafetyNotebook/SafetyNotebook/mainwindow.h` -- MainWindow class declaration
- `/home/jone/projects/SafetyNotebook/SafetyNotebook/mainwindow.cpp` -- MainWindow implementation (constructor, initUi, tree view, actions)
- `/home/jone/projects/SafetyNotebook/SafetyNotebook/main.cpp` -- Application entry point
- `/home/jone/projects/SafetyNotebook/SafetyNotebook/CMakeLists.txt` -- Build configuration
- RESEARCH.md code examples (sections 1-6) -- Reference Python implementation patterns
- UI-SPEC.md -- UI design contract (widget inventory, copywriting, sizes)

**Files scanned:** 6 (from old C++ project)
**Pattern extraction date:** 2026-05-07
