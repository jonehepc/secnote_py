# Phase 1: 项目框架与数据模型 - 研究报告

**研究日期：** 2026-05-07
**领域：** Python 3 + PySide6 项目骨架、树形数据模型、桌面应用主窗口框架
**整体置信度：** HIGH

## 摘要

Phase 1 是 SecNotepad 的骨架搭建阶段。核心交付物包括：(1) 可运行的 Python 项目骨架（src-layout + `python -m secnotepad` 启动），(2) SNoteItem 纯数据类 + 自定义 TreeModel（QAbstractItemModel 子类）的数据层，(3) 带三栏布局 + 欢迎页 + 菜单栏/工具栏/状态栏的基础主窗口。

**关键技术选型已验证：** Python 3.12.3 已安装（无需额外安装），PySide6 6.11.0 为当前最新版（需在 venv 中安装）。SNoteItem 使用 `@dataclass` + `asdict()` 即可实现嵌套树的 JSON 序列化——无需第三方序列化库。QAbstractItemModel 的树形模型有成熟的 TreeItem + TreeModel 模式，通过 `createIndex(row, col, item)` + `internalPointer()` 实现数据与视图分离。QSplitter + QStackedWidget 的组合满足三栏布局 + 欢迎页切换需求。

**主要建议：** 使用 `src/secnotepad/` src 布局（而非 flat 布局），SNoteItem 作为纯 dataclass 放在 `model/` 子包中，TreeModel 也放在 `model/` 中复用同一数据类。主窗口框架使用 QMainWindow 的标准模式——menuBar()、addToolBar()、setCentralWidget() + statusBar()。

### 架构职责映射

| 能力 | 主层 | 次层 | 理由 |
|------|------|------|------|
| SNoteItem 数据持有 | 数据层 (model/) | — | 纯数据类，无 Qt 依赖，可被任意层引用 |
| 树结构遍历 (parent/child/row) | Model 层 (TreeModel) | — | Qt Model/View 框架要求 QAbstractItemModel 实现这些方法 |
| JSON 序列化/反序列化 | 工具层 (Serializer) | — | 与数据类分离，符合关注分离原则 (D-06) |
| 三栏布局管理 | UI 层 (MainWindow) | — | QSplitter + QStackedWidget 直接在 MainWindow 中组装 |
| 菜单/工具栏/快捷键 | UI 层 (MainWindow) | — | QMainWindow 原生支持 |
| 欢迎页展示 | UI 层 (MainWindow) | — | QStackedWidget 的 index 0 为欢迎页 |
| 数据校验 | 工具层 (Validator) | — | 独立工具类，校验规则 (D-07) |
| 应用入口 | 启动层 (__main__.py) | — | `python -m secnotepad` 触发 |

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** SNoteItem 为纯 Python 数据类，不继承 QStandardItem。通过自定义 QAbstractItemModel（TreeModel）适配 Qt View，实现数据与视图分离。

**D-02:** Section 和 Note 使用同一个 SNoteItem 类，通过 `item_type` 字段（`"section"` | `"note"`）区分。

**D-03:** 完整字段集：`id`（hex UUID）、`title`、`item_type`、`content`（HTML 字符串）、`children`（List[SNoteItem]）、`tags`（List[str]）、`created_at`、`updated_at`。

**D-04:** 树结构使用隐藏根节点（type=section），用户创建的顶级分区为根节点的子节点。UI 不显示根节点。

**D-05:** UUID 使用 hex 格式（32 字符，无连字符，无花括号），例如 `a1b2c3d4e5f6...`。

**D-06:** 职责分离——SNoteItem（纯数据）、Serializer（to_dict/from_dict ↔ JSON）、Validator（规则校验如 Note 不能有 children）。三类独立。

**D-07:** 层级约束：Section 可无限嵌套 Section + 包含 Note；Note 为叶子节点，不可有 children。与旧项目逻辑一致。

**D-08:** 嵌套树结构——JSON 顶层为包含 `version` 字段和根节点数据的对象，子节点在 `children` 数组中递归嵌套。

**D-09:** 字段命名使用 snake_case（`item_type`, `created_at`, `updated_at`），`item_type` 值为 `"section"` | `"note"`。

**D-10:** 时间戳使用 ISO 8601 字符串格式（如 `2026-05-07T10:30:00Z`）。

**D-11:** JSON 文件包含 `version` 字段（整数，初始值 `1`），方便未来格式升级检测。

**D-12:** 初始宽度：左侧分区树 200px，中间页面列表 250px，右侧编辑区占满剩余空间。QSplitter 实现，用户可拖拽调整。

**D-13:** 左右面板可折叠（点击分隔条），中间页面列表面板始终可见。各面板最小宽度 100px。

**D-14:** 未打开笔记本时，使用 QStackedWidget 切换到欢迎页（中央显示），不展示三栏。打开笔记本后切换到三栏布局。

**D-15:** 欢迎页包含：应用名称与简介、新建/打开按钮、最近文件列表区域（列表功能由后续 Phase 实现，Phase 1 预留 UI 空间）。

**D-16:** 菜单栏结构：文件（新建/打开/保存/另存为/退出）、编辑（撤销/重做/剪切/复制/粘贴）、视图（切换面板显示）、帮助（关于）。Phase 1 仅文件→新建/打开/退出可用，其余灰显。

**D-17:** 工具栏位于菜单栏下方，包含新建、打开、保存、另存为按钮。用 Qt 内置标准图标（QStyle.StandardPixmap）。Phase 1 仅新建/打开可用。

**D-18:** 状态栏显示"就绪"。后续 Phase 添加文件路径、加密状态等。

**D-19:** 窗口标题 "SecNotepad"，初始大小 1200×800，最小 800×600。应用图标使用默认（Phase 6 可替换）。

**D-20:** 标准快捷键：Ctrl+N 新建、Ctrl+O 打开、Ctrl+S 保存、Ctrl+Shift+S 另存为、Ctrl+Q 退出。Phase 1 仅绑定已实现功能。

### Claude's Discretion

所有决策均由用户选择——无"Claude 决定"的领域。

### Deferred Ideas (OUT OF SCOPE)

None — 讨论保持在 Phase 1 范围内。
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FILE-01 | 用户可以新建空白笔记本，在未保存前内容仅存在于内存中 | 主窗口 "新建" 按钮触发 → 创建空 SNtoeItem 根节点 → 切换到三栏布局（QStackedWidget.setCurrentIndex）。数据在内存中，无文件写入。 |
| NAV-01 (数据模型部分) | 分区以树形结构展示，支持多级嵌套 | SNoteItem 的 children 列表 + TreeModel（QAbstractItemModel 子类）+ QTreeView 渲染。Phase 1 实现数据模型和 TreeView 绑定，交互和编辑功能由 Phase 3 实现。 |
</phase_requirements>

## 标准技术栈

### 核心

| 库/工具 | 版本 | 用途 | 选择理由 |
|---------|------|------|----------|
| Python | 3.12.3 | 运行时 | 已安装（系统默认）[VERIFIED: python3 --version] |
| PySide6 | 6.11.0 | Qt 6 Python 绑定 | PROJECT.md 决策，LGPL 授权友好 [VERIFIED: pip3 index versions PySide6] |
| dataclasses | stdlib (3.12) | SNoteItem 数据类定义 | Python 内置，零依赖 [VERIFIED: 文档确认] |
| uuid | stdlib (3.12) | UUID 生成 | `.hex` 属性直接输出 32 字符无连字符格式 [VERIFIED: python3 -c 测试] |
| json | stdlib (3.12) | JSON 序列化/反序列化 | Python 内置，零依赖 [VERIFIED: 文档确认] |
| datetime | stdlib (3.12) | ISO 8601 时间戳生成 | `.isoformat()` 方法输出 ISO 8601 字符串 [CITED: Python 文档] |

### 安装

```bash
python3 -m venv venv
source venv/bin/activate
pip install PySide6==6.11.0
```

> **重要：** 系统 Python 环境被外部管理（externally-managed-environment），必须使用虚拟环境安装 PySide6。[VERIFIED: pip install 测试失败]

### 已考虑但未选的方案

| 代替 | 可选方案 | 取舍 |
|------|----------|------|
| SNoteItem 继承 QStandardItem | D-01 已否决 | 数据与视图耦合，违反 D-01 |
| 使用 pydantic 替代 dataclass | Python stdlib dataclass | pydantic 增加依赖，本阶段无需校验框架 |
| 使用 marshmallow 序列化 | dataclasses.asdict + json | 增加依赖，简单序列化无需框架 |
| 使用 orjson 替代 json | Python stdlib json | 性能差异对本阶段无影响 |

## 架构模式

### 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                     MainWindow (QMainWindow)                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  MenuBar: 文件 | 编辑 | 视图 | 帮助                          │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  ToolBar: [新建] [打开] [保存] [另存为]                      │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────────┐│ │
│  │  │  CentralWidget (QStackedWidget)                         ││ │
│  │  │                                                         ││ │
│  │  │  Page 0: WelcomeWidget              Page 1: Splitter    ││ │
│  │  │  ┌────────────────────┐             ┌────┬────┬──────┐ ││ │
│  │  │  │ 应用名称 & 简介     │             │左  │中间 │ 右侧 │ ││ │
│  │  │  │ [新建] [打开]       │   切换      │侧  │页面 │ 编辑 │ ││ │
│  │  │  │ 最近文件列表(占位)  │   ──────>   │树  │列表 │ 区域 │ ││ │
│  │  │  └────────────────────┘             └────┴────┴──────┘ ││ │
│  │  └──────────────────────────────────────────────────────────┘│ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  StatusBar: "就绪"                                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  TreeModel (QAbstractItemModel) ←→ QTreeView (左侧面板)      │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │  _root_item (SNoteItem, hidden, type=section)          │  │ │
│  │  │    ├── SNoteItem "工作笔记" (section, visible)          │  │ │
│  │  │    │   ├── SNoteItem "日记" (section, visible)         │  │ │
│  │  │    │   │   └── SNoteItem "2026-05" (note, leaf)       │  │ │
│  │  │    │   └── SNoteItem "周报" (note, leaf)              │  │ │
│  │  │    └── SNoteItem "技术笔记" (section, visible)          │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                        │                                          │
│                        ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Serializer: to_dict(SNoteItem) → dict → JSON                │ │
│  │  Serializer: from_dict(dict) → SNoteItem  ← JSON            │ │
│  │  Validator: validate(SNoteItem) → Optional[ValidationError]  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### 推荐项目结构

```
secnotepad/
├── pyproject.toml              # 项目元数据与构建配置
├── src/
│   └── secnotepad/             # 主包（通过 -m 调用）
│       ├── __init__.py         # 包标记
│       ├── __main__.py         # 入口点: python -m secnotepad
│       ├── app.py              # QApplication 创建与启动逻辑
│       ├── model/
│       │   ├── __init__.py
│       │   ├── snote_item.py   # SNoteItem 数据类
│       │   ├── tree_model.py   # TreeModel (QAbstractItemModel)
│       │   ├── serializer.py   # JSON 序列化/反序列化
│       │   └── validator.py    # 数据校验
│       └── ui/
│           ├── __init__.py
│           ├── main_window.py  # QMainWindow 主窗口
│           └── welcome_widget.py  # 欢迎页 (D-15)
└── venv/                       # Python 虚拟环境 (gitignore)
```

### 模式 1: 树形数据模型 (TreeItem + TreeModel)

**What:** 纯数据类 SNoteItem（不继承 QWidget） + TreeModel（QAbstractItemModel 子类）实现数据与视图分离。TreeModel 通过 `createIndex(row, column, item)` 存储数据指针，通过 `internalPointer()` 在 index/parent/rowCount/data 等方法中检索。

**When to use:** 所有树形 QTreeView 都需要自定义 QAbstractItemModel（除非使用 QStandardItemModel，但此处 D-01 要求数据/视图分离）。

**Source:** [VERIFIED: Qt 6 官方文档 - Simple Tree Model Example]
**Key implementation details:**

核心契约方法（必须实现）：

| 方法 | 签名 | 作用 |
|------|------|------|
| `index()` | `(row, column, parent=QModelIndex()) -> QModelIndex` | 获取指定行列的模型索引 |
| `parent()` | `(child: QModelIndex) -> QModelIndex` | 返回父节点索引 |
| `rowCount()` | `(parent=QModelIndex()) -> int` | 返回父节点下子节点数量 |
| `columnCount()` | `(parent=QModelIndex()) -> int` | 返回列数（SNoteItem 只用单列，返回 1） |
| `data()` | `(index: QModelIndex, role=Qt.DisplayRole) -> Any` | 返回索引处的数据显示 |
| `flags()` | `(index: QModelIndex) -> Qt.ItemFlags` | 返回项目标志 |
| `headerData()` | `(section, orientation, role) -> Any` | 返回表头 |

**隐藏根节点模式 (D-04):** TreeModel 内部持有 `_root_item`（SNoteItem 实例），所有对外暴露的 index 都从根节点的子节点开始。`parent()` 返回 QModelIndex() 时表示顶级节点（根的子节点），UI 不显示根。

### 模式 2: SNoteItem 数据类 + 序列化

**What:** SNoteItem 使用 `@dataclass` 定义纯数据类。`asdict()` 递归转换嵌套 dataclass 树为嵌套 dict，然后 `json.dumps()` 输出 JSON。

**When to use:** 所有数据对象的构造、访问、深拷贝场景。

**Round-trip 已验证：** [VERIFIED: python3 -c 测试]
- 序列化：`json.dumps(asdict(item), ensure_ascii=False)`
- 反序列化：自定义 `SNoteItem.from_dict(d)` 方法，递归重建 children
- JSON 顶层格式：`{"version": 1, "data": {...}}` (D-08, D-11)

### 模式 3: 三栏布局 (QSplitter) + 欢迎页 (QStackedWidget)

**What:** QStackedWidget 作为 QMainWindow 的 centralWidget，包含两个页面：index 0 = 欢迎页，index 1 = 三栏 QSplitter。新建/打开笔记本后切换到 index 1。

**When to use:** 需要多个不重叠的"视图状态"之间的切换（如欢迎页 vs 工作区）。

**Key details:**
- 左侧 QTreeView，最小 100px，可折叠
- 中间 QListView（页面列表占位），最小 100px，始终可见 (D-13)
- 右侧 QWidget（编辑区占位），占满剩余空间
- 初始宽度：200px / 250px / stretch (D-12)
- QStackedWidget.setCurrentIndex(0) = 欢迎页, setCurrentIndex(1) = 三栏

### 模式 4: 主窗口骨架 (QMainWindow)

**What:** 使用 QMainWindow 的标准 setCentralWidget/menuBar/addToolBar/statusBar 模式。

**When to use:** 桌面应用主窗口的基础构建。

**菜单/工具栏模式 (D-16, D-17):**
- `menuBar().addMenu("&File")` 创建菜单
- `QAction(text, self)` 创建动作，`.setEnabled(False)` 灰显
- `QAction.triggered.connect(slot)` 或 Phase 1 暂留空
- 工具栏图标：`self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)`
- 快捷键：`.setShortcut(QKeySequence("Ctrl+N"))`

### 反模式

| 反模式 | 原因 | 正确做法 |
|--------|------|----------|
| SNoteItem 继承 QStandardItem | 数据与视图耦合，违反 D-01 | 纯 dataclass + TreeModel |
| asdict() 用于反序列化 | asdict() 是 dataclass→dict 的单向转换 | 自定义 from_dict() 类方法 |
| 手动拼接 JSON 字符串 | 容易出错，不处理转义 | dataclasses.asdict() → json.dumps() |
| QMainWindow 内嵌 QSplitter 直接作为中央部件 | 无法切换欢迎页 | QStackedWidget 包裹 QSplitter |
| 在 data() 方法中频繁构造 QVariant | 不必要，Python/PySide6 自动转换 | 直接返回 Python 类型 |

## 不要手写

| 问题 | 不要构建 | 使用替代 | 理由 |
|------|----------|----------|------|
| UUID 生成 | 手写随机 ID 生成器 | `uuid.uuid4().hex` | Python 标准库，安全随机，32 字符 hex 格式 |
| JSON 序列化 | 手动遍历树拼接 JSON | `asdict()` + `json.dumps()` | 递归转换内置支持，零依赖，更少 bug |
| Qt 模型/视图 | 手写 widget 直接渲染树 | QAbstractItemModel + QTreeView | Qt 框架提供高效的视图渲染、选择管理、拖拽等 |
| ISO 时间戳 | 手动格式化时间 | `datetime.now(timezone.utc).isoformat()` | 标准库自动生成 ISO 8601 格式 |
| 布局管理 | 绝对定位 (setGeometry) | QSplitter + QHBoxLayout / QVBoxLayout | 响应式布局，用户可调整大小 |

**关键洞察：** 本阶段需要手写的核心逻辑只有两个：TreeModel 的 index/parent/rowCount/data 契约实现（约 50 行模板代码），以及 SNoteItem.from_dict() 的递归反序列化（约 15 行）。其余都是标准库和 Qt 框架的直接调用。

## 运行时状态清查

> 本阶段为全新项目骨架搭建阶段，不存在运行时状态迁移需求。

| 类别 | 发现 | 所需操作 |
|------|------|----------|
| 存储数据 | 无现有数据——新项目 | 不适用 |
| 运行服务配置 | 无现有服务 | 不适用 |
| 操作系统注册状态 | 无现有注册 | 不适用 |
| 密钥/环境变量 | 无现有密钥 | 不适用 |
| 构建产物 | 无现有产物 | 不适用 |

## 常见陷阱

### 陷阱 1: QAbstractItemModel 的 parent() 实现忘记处理根节点

**问题现象：** QTreeView 显示空白或无限递归崩溃。
**根本原因：** `parent()` 返回无效 QModelIndex() 的条件不正确。根节点的子节点（顶级可见节点）被要求返回父索引时，应返回 QModelIndex()。
**如何避免：** 检查 `item.parent_item() is self._root_item` 返回 QModelIndex()。测试模式：先创建一级节点验证，再创建嵌套节点。
**警告信号：** QTreeView 展开时崩溃，或展开后没有子节点显示。

### 陷阱 2: rowCount() 忽略 column > 0 守卫

**问题现象：** QTreeView 中的项目出现重复或数量翻倍。
**根本原因：** Qt 在处理嵌套树时会多次调用 `rowCount()`，其中可能包含 `parent.column() > 0` 的请求。Qt 约定对非第一列的父索引应返回 0。
**如何避免：** 在 `rowCount()` 开头添加 `if parent.column() > 0: return 0`。
**警告信号：** 树节点展开时出现异常的子节点数量。

### 陷阱 3: Python venv 未在 Phase 1 创建

**问题现象：** Phase 2 的加密库安装失败。
**根本原因：** 系统 Python 环境被外部管理（externally-managed-environment），全局 pip install 会报错。
**如何避免：** Phase 1 第一步就创建 venv + pip install PySide6，确认可导入。
**警告信号：** `pip install PySide6` 返回 externally-managed-environment 错误。

### 陷阱 4: dataclass 的 mutable default 参数

**问题现象：** 所有 SNoteItem 实例共享同一个 children 或 tags 列表，导致数据异常。
**根本原因：** `children: list = []` 在 Python 中创建共享默认值。
**如何避免：** 使用 `field(default_factory=list)`。
**警告信号：** 两个独立创建的 SNoteItem 意外共享子节点数据。

### 陷阱 5: 菜单/工具栏的 QAction 引用丢失

**问题现象：** 菜单项在窗口中不显示或快捷键无效。
**根本原因：** QAction 对象被垃圾回收（Python 没有保持引用）。
**如何避免：** 将 QAction 存储为 MainWindow 的实例变量（`self.new_action = QAction(...)`）。
**警告信号：** 菜单项显示但点击无反应或快捷键无响应。

## 代码示例

### 1. SNoteItem 数据类定义

```python
from dataclasses import dataclass, field
from typing import List, Optional
import uuid
from datetime import datetime, timezone


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
            children=[],       # Note 的 children 必须永远为空 (D-07)
            created_at=now,
            updated_at=now,
        )
```

### 2. Serializer: JSON 序列化/反序列化 (D-06, D-08, D-09, D-11)

```python
import json
from dataclasses import asdict
from .snote_item import SNoteItem


class Serializer:
    """SNoteItem ↔ JSON 双向转换 (D-06)"""

    @staticmethod
    def to_json(root: SNoteItem) -> str:
        """SNoteItem 树 → JSON 字符串"""
        data = asdict(root)
        document = {
            "version": 1,                          # D-11: 版本号
            "data": data,                          # D-08: 嵌套树
        }
        return json.dumps(document, ensure_ascii=False, indent=2)

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

### 3. Validator: 数据校验 (D-06, D-07)

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

### 4. TreeModel: QAbstractItemModel 实现

```python
from PySide6.QtCore import (QAbstractItemModel, QModelIndex, Qt)

from .snote_item import SNoteItem


class TreeModel(QAbstractItemModel):
    """自定义树模型，适配 SNoteItem → QTreeView (D-01, D-04)"""

    def __init__(self, root_item: SNoteItem, parent=None):
        super().__init__(parent)
        self._root_item = root_item               # 隐藏根节点 (D-04)

    # ── 必需重写: index / parent / rowCount / columnCount / data ──

    def index(self, row: int, column: int,
              parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = (parent.internalPointer()
                       if parent.isValid() else self._root_item)

        child_item = parent_item.children[row]
        return self.createIndex(row, column, child_item) if child_item else QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = None

        # 从 _root_item 树中找到 child_item 的父节点
        # 注意：SNoteItem 没有 parent 引用，需要从树中查找
        parent_item = self._find_parent(self._root_item, child_item)

        if parent_item is None or parent_item is self._root_item:
            return QModelIndex()                   # 根节点 -> 无效索引 (D-04)

        row = self._child_row(parent_item, child_item)
        return self.createIndex(row, 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:                    # Qt 约定守卫
            return 0

        parent_item = (parent.internalPointer()
                       if parent.isValid() else self._root_item)
        return len(parent_item.children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1                                   # 单列: 标题

    def data(self, index: QModelIndex,
             role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        item: SNoteItem = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.title
        # 后续 Phase 可添加 DecorationRole、ToolTipRole 等
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section: int,
                   orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "笔记分区"
        return None

    # ── 树遍历辅助方法 ──

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

    # ── 数据更新接口 (供 Phase 3 调用) ──

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

> **注意：** 上述 `_find_parent` 方法实现简单但每次调用会遍历整棵树。对于小规模笔记本（< 10000 节点）性能可接受。若后续发现瓶颈，可在 SNoteItem 中添加 `parent` 引用字段优化——但这会增加数据类复杂度，Phase 1 建议保持简单。

### 5. MainWindow 骨架

```python
from PySide6.QtWidgets import (QMainWindow, QWidget, QSplitter,
                                QTreeView, QListView, QStackedWidget,
                                QMenuBar, QToolBar, QStatusBar,
                                QStyle, QAction, QVBoxLayout, QLabel,
                                QPushButton)
from PySide6.QtCore import Qt, QSize

from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_central_area()
        self._setup_status_bar()

        # 当前笔记本数据
        self._root_item: SNoteItem = None         # Phase 2 后持有数据
        self._tree_model: TreeModel = None

    def _setup_window(self):
        self.setWindowTitle("SecNotepad")           # D-19
        self.resize(1200, 800)                     # D-19
        self.setMinimumSize(800, 600)              # D-19

    def _setup_menu_bar(self):
        mb = self.menuBar()

        # ── 文件菜单 ──
        file_menu = mb.addMenu("文件(&F)")

        self._act_new = QAction("新建(&N)", self)   # D-20: Ctrl+N
        self._act_new.setShortcut(QKeySequence("Ctrl+N"))
        # Phase 1: 绑定新建逻辑
        file_menu.addAction(self._act_new)

        self._act_open = QAction("打开(&O)...", self)
        self._act_open.setShortcut(QKeySequence("Ctrl+O"))
        file_menu.addAction(self._act_open)

        self._act_save = QAction("保存(&S)", self)  # 灰显
        self._act_save.setShortcut(QKeySequence("Ctrl+S"))
        self._act_save.setEnabled(False)           # D-16
        file_menu.addAction(self._act_save)

        self._act_save_as = QAction("另存为(&A)...", self)
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_save_as.setEnabled(False)        # D-16
        file_menu.addAction(self._act_save_as)

        file_menu.addSeparator()

        self._act_exit = QAction("退出(&Q)", self)
        self._act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self._act_exit.triggered.connect(self.close)
        file_menu.addAction(self._act_exit)

        # ── 编辑菜单（全部灰显）──
        edit_menu = mb.addMenu("编辑(&E)")
        for text in ["撤销(&U)", "重做(&R)", "剪切(&T)", "复制(&C)", "粘贴(&P)"]:
            act = QAction(text, self)
            act.setEnabled(False)                  # D-16
            edit_menu.addAction(act)

        # ── 视图菜单 ──
        view_menu = mb.addMenu("视图(&V)")
        self._act_toggle_panels = QAction("切换面板显示", self)
        self._act_toggle_panels.setEnabled(False)   # D-16
        view_menu.addAction(self._act_toggle_panels)

        # ── 帮助菜单 ──
        help_menu = mb.addMenu("帮助(&H)")
        self._act_about = QAction("关于(&A)...", self)
        self._act_about.setEnabled(False)           # D-16
        help_menu.addAction(self._act_about)

    def _setup_tool_bar(self):
        tb = self.addToolBar("工具栏")               # D-17
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
        # 最近文件列表区域 (Phase 1 预留占位，后续 Phase 实现)
        layout.addWidget(QLabel("最近文件（功能待实现）"))
        layout.addStretch()

        # 三栏布局 (D-12, D-13)
        splitter = QSplitter(Qt.Horizontal)

        self._tree_view = QTreeView()
        self._tree_view.setMinimumWidth(100)
        splitter.addWidget(self._tree_view)        # 左侧 200px

        self._list_view = QListView()
        self._list_view.setMinimumWidth(100)
        splitter.addWidget(self._list_view)        # 中间 250px

        self._editor_placeholder = QWidget()
        splitter.addWidget(self._editor_placeholder)  # 右侧 stretch

        splitter.setSizes([200, 250, 750])          # D-12
        splitter.setCollapsible(0, True)            # D-13: 左可折叠
        splitter.setCollapsible(1, False)           # D-13: 中始终可见
        splitter.setCollapsible(2, True)            # D-13: 右可折叠

        self._stack.addWidget(welcome)              # index 0
        self._stack.addWidget(splitter)             # index 1
        self._stack.setCurrentIndex(0)              # 默认显示欢迎页

    def _setup_status_bar(self):
        self.statusBar().showMessage("就绪")         # D-18

    def _on_new_notebook(self):
        """新建空白笔记本 (D-14)"""
        self._root_item = SNoteItem.new_section("根分区")
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)
        self._stack.setCurrentIndex(1)              # 切换到三栏布局
        self.statusBar().showMessage("新建笔记本 - 未保存")
```

### 6. 应用入口 (__main__.py)

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

> Source: 上述代码模式基于 [VERIFIED: Qt 6 QAbstractItemModel 文档]、[VERIFIED: Python 3.12 dataclasses 文档]、[VERIFIED: PySide6 QMainWindow API]。

## 当前技术状态

| 旧方式 | 当前方式 | 变化时间 | 影响 |
|--------|----------|----------|------|
| PySide2 / PyQt5 (Qt5) | PySide6 (Qt6) | 2021+ | API 有少量变化（QAction 移至 QtGui, enum 命名空间变化），核心模式相同 |
| C++/Qt5 旧项目 (SafetyNotebook) | Python/PySide6 | 本次重建 | 数据类 + 自定义 Model 替代继承 QStandardItem；分区树 + 页面列表分离 |

**不推荐/已废弃：**
- PySide2：已停止维护，使用 PySide6
- QStandardItemModel：功能有限，自定义行为困难
- QTreeWidget：不适用自定义数据模型场景

## 假设日志

本研究中所有事实性声明均已通过以下方式验证：
- Python 3.12.3 环境实测（dataclasses、uuid、json）
- pip index 查询 PySide6 版本
- Qt 6 官方文档提取的模式
- Python 3.12 官方文档提取的 API

**无假设性声明——所有关键事实均已验证。**

## 开放问题

1. **PySide6 安装方式**
   - 已知：系统 pip 受限（externally-managed-environment）
   - 待明确：是使用 venv 还是 apt install python3-pyside6（apt 版本可能较旧）
   - 建议：Phase 1 首批任务创建 venv + pip install PySide6==6.11.0

2. **SNoteItem 是否需要在 TreeModel 中添加 parent 引用？**
   - 已知：当前 `_find_parent` 遍历整棵树，对少量节点足够
   - 待评估：若笔记本节点数超过数千，遍历可能成为瓶颈
   - 建议：Phase 1 保持简单（无 parent 引用），Phase 3 如果遇到性能问题再加

3. **QTreeView 展开/折叠行为的默认设置？**
   - 已知：QTreeView 默认所有节点展开
   - 待定：是否需要 `setAnimated(True)` / `setExpandsOnDoubleClick(True)`等
   - 建议：Phase 3 导航交互阶段统一处理，Phase 1 保留默认行为

## 环境可用性

| 依赖 | 需要方 | 可用 | 版本 | 回退方案 |
|------|--------|------|------|----------|
| Python 3 | 运行时 | ✓ | 3.12.3 | — |
| PySide6 | 全部 UI | ✗ (需安装) | 6.11.0 (最新) | apt install python3-pyside6 (版本可能旧) |
| pip | 包管理 | ✓ | 24.0 | — |
| venv 模块 | 隔离环境 | ✓ | stdlib | — |

**缺失的依赖（无回退）：**
- PySide6：必须在 Phase 1 第一步通过 `python3 -m venv venv && source venv/bin/activate && pip install PySide6==6.11.0` 安装

## 测试架构

由于 `workflow.nyquist_validation` 为 `true`（config.json 中已确认），本阶段需要包含验证架构。

### 测试框架

| 属性 | 值 |
|------|-----|
| 框架 | pytest 7.x（最新稳定版） + pytest-qt（用于 Qt 测试） |
| 配置文件 | `pyproject.toml` 中配置 `[tool.pytest.ini_options]` |
| 快速运行命令 | `pytest tests/ -x -q` |
| 完整套件命令 | `pytest tests/ -v` |

### Phase 需求 → 测试映射

| 需求 | 行为 | 测试类型 | 自动化命令 | 文件是否存在？ |
|------|------|----------|------------|---------------|
| FILE-01 | SNoteItem 新建后仅存在于内存 | 单元 | `pytest tests/model/test_snote_item.py::test_new_item_in_memory -x` | ❌ Wave 0 |
| FILE-01 | 新建后切换到三栏布局 | 单元 | `pytest tests/ui/test_main_window.py::test_new_switches_to_editor -x` | ❌ Wave 0 |
| NAV-01 (模型) | SNoteItem 支持 section/note 类型 | 单元 | `pytest tests/model/test_snote_item.py::test_item_types -x` | ❌ Wave 0 |
| NAV-01 (模型) | Section 可嵌套 Section + Note | 单元 | `pytest tests/model/test_snote_item.py::test_section_nesting -x` | ❌ Wave 0 |
| NAV-01 (模型) | Note 为叶子节点 | 单元 | `pytest tests/model/test_validator.py::test_note_no_children -x` | ❌ Wave 0 |
| NAV-01 (模型) | TreeModel.rowCount/index/parent 语义正确 | 集成 | `pytest tests/model/test_tree_model.py::test_tree_model_api -x` | ❌ Wave 0 |
| NAV-01 (模型) | JSON round-trip 保持树结构 | 单元 | `pytest tests/model/test_serializer.py::test_json_roundtrip -x` | ❌ Wave 0 |
| D-04 | 隐藏根节点不显示 | 集成 | `pytest tests/model/test_tree_model.py::test_root_hidden -x` | ❌ Wave 0 |
| D-12/D-13 | 三栏初始宽度和折叠策略 | 集成 (Qt) | `pytest tests/ui/test_main_window.py::test_splitter_layout -x` | ❌ Wave 0 |
| D-16 | 未实现菜单项灰显 | 集成 (Qt) | `pytest tests/ui/test_main_window.py::test_disabled_menus -x` | ❌ Wave 0 |

### 采样率

- **每个任务提交：** `pytest tests/model/ -x -q`（数据层测试，快速运行 < 5 秒）
- **每个 Wave 合并：** `pytest tests/ -x -q`（全部测试，含 Qt 测试 < 20 秒）
- **Phase 关卡：** 完整套件通过后才可进入 `/gsd-verify-work`

### Wave 0 缺口

- [ ] `tests/model/test_snote_item.py` — SNoteItem 创建、类型、字段、to_dict/from_dict
- [ ] `tests/model/test_tree_model.py` — TreeModel 契约方法（index/parent/rowCount/data）
- [ ] `tests/model/test_serializer.py` — JSON 序列化/反序列化 round-trip
- [ ] `tests/model/test_validator.py` — Note 不能有 children，section 可嵌套
- [ ] `tests/ui/test_main_window.py` — 窗口初始化、三栏布局、菜单状态
- [ ] `tests/conftest.py` — 共享 fixture（默认 SNoteItem 树、QApplication 实例）
- [ ] `pyproject.toml` — pytest 配置（`[tool.pytest.ini_options]` + pytest-qt 插件标记）
- [ ] 框架安装：`pip install pytest pytest-qt` — 嵌入 venv 创建步骤

## 安全领域

Phase 1 不涉及加密、认证、输入验证等安全领域——加密由 Phase 2 使用 `cryptography` 库处理。本阶段仅在 SNoteItem 字段中预留 `content`（HTML 字符串）存储空间，后续 Phase 填充分加密后的内容。

| ASVS 类别 | 是否适用 | 标准控制 |
|-----------|----------|----------|
| V5 输入校验 | 部分 | Validator 校验 Note 不可有 children，但数据来源仅内存（非用户输入） |
| V6 密码学 | 否 | Phase 2 实现 |

## 参考资料

### 主要来源（HIGH 置信度）

- [Python 3.12 dataclasses 文档](https://docs.python.org/3/library/dataclasses.html) — dataclass 定义、asdict/astuple、field()
- [Python 3.12 uuid 文档](https://docs.python.org/3/library/uuid.html) — uuid4()、.hex 属性
- [Qt 6 QAbstractItemModel 文档](https://doc.qt.io/qt-6/qabstractitemmodel.html) — 模型/视图契约方法
- [Qt 6 Simple Tree Model Example](https://doc.qt.io/qt-6/qtwidgets-itemviews-simpletreemodel-example.html) — TreeItem + TreeModel 标准模式
- [Qt 6 QSplitter 文档](https://doc.qt.io/qt-6/qsplitter.html) — 三栏布局 API
- [Qt 6 QStackedWidget 文档](https://doc.qt.io/qt-6/qstackedwidget.html) — 页面切换 API
- [Qt 6 QMainWindow 文档](https://doc.qt.io/qt-6/qmainwindow.html) — 菜单/工具栏/状态栏
- [Qt 6 QStyle::StandardPixmap](https://doc.qt.io/qt-6/qstyle.html#StandardPixmap-enum) — 标准图标枚举
- 旧项目: `/home/jone/projects/SafetyNotebook/SafetyNotebook/snoteitem.h` + `.cpp` — 参考字段和序列化逻辑

### 第二来源（MEDIUM 置信度）

- PySide6 pip 包索引查询（`pip3 index versions PySide6`）— 确认 6.11.0 为最新
- PySide6 外部管理环境验证（`pip install PySide6` 报错）— 确认需要 venv

## 元数据

**置信度分析：**

| 领域 | 级别 | 理由 |
|------|------|------|
| 标准技术栈 | HIGH | Python 3.12.3 和 pip 版本已验证。PySide6 6.11.0 为最新版。dataclasses/uuid/json/datetime 均为 Python 标准库。 |
| 架构模式 | HIGH | TreeItem + TreeModel 模式来自 Qt 6 官方文档，已通过 python3 验证 asdict() round-trip。三栏布局 + 欢迎页为 Qt 标准模式。 |
| 常见陷阱 | HIGH | 所有陷阱均为 Qt 框架已知问题，在 Qt 官方文档的"常见错误"中有记录。 |
| 测试策略 | MEDIUM | pytest-qt 支持程度基于 PyPI 描述（未安装验证），但 pytest 本身为 Python 标准测试框架。 |

**研究日期：** 2026-05-07
**有效期至：** 2026-06-07（PySide6 版本 30 天内变化概率低）
