# Phase 05: 标签与搜索 - Research

**Researched:** 2026-05-11  
**Domain:** PySide6/Qt6 桌面应用中的页面级标签管理、HTML 纯文本搜索、搜索结果跳转  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
## Implementation Decisions

### 标签入口与展示
- **D-81:** 标签编辑入口固定放在右侧编辑区顶部，位于当前页面编辑区域内；不要把标签编辑放到中间页面列表或主工具栏。
- **D-82:** 标签使用横向 chip 行展示，每个标签 chip 可单独移除，末尾提供添加标签入口。添加、移除标签后必须更新当前页面 `SNoteItem.tags` 并调用 `mark_dirty()`。
- **D-83:** 页面列表暂不显示标签，继续保持当前单列标题列表模式。搜索结果可以显示路径和片段，但中间页面列表不需要多行标签 delegate。
- **D-84:** 未选中页面时，标签区域随编辑器状态禁用或隐藏为不可编辑状态；行为应与现有格式工具栏未选页面时禁用的模式一致。

### 标签命名规则
- **D-85:** 新增标签时对输入做首尾 trim；保存和展示时保留用户输入的大小写、中文、空格和符号原样。
- **D-86:** 同一页面内重复标签判断忽略大小写；如果用户已添加 `Python`，再次添加 `python` 应被视为重复，不再新增第二个标签。显示形式保留首次添加的文本。
- **D-87:** 添加标签时提供当前笔记本已有标签的下拉补全，帮助复用已有标签；仍允许输入新标签。
- **D-88:** 标签采用轻量限制：空标签拒绝，超长标签限制在合理长度（建议 32 字符）；不做严格 slug 化，不限制中文、空格或常见符号。

### 搜索入口与范围
- **D-89:** 搜索入口使用菜单弹窗，而不是常驻中间栏搜索框或主工具栏搜索框。弹窗由菜单项触发，规划时可考虑常见快捷键，但不是必须由讨论锁定。
- **D-90:** 搜索在弹窗中通过回车或“搜索”按钮触发；不要默认实时搜索或 debounce 每次输入。
- **D-91:** 搜索默认覆盖当前打开笔记本内的全部页面，而不是仅当前分区。搜索服务需要遍历整棵 SNoteItem 树并记录页面所属分区路径。
- **D-92:** 搜索弹窗提供字段筛选，允许用户选择搜索标题、正文和标签。默认选择应覆盖标题与正文以满足 SRCH-01；标签字段可作为可选搜索范围。

### 结果片段与跳转
- **D-93:** 搜索结果列表显示页面标题、所在分区路径和匹配片段。路径用于区分同名页面。
- **D-94:** 正文匹配片段从 HTML 内容提取纯文本后生成，围绕第一个命中词截取短片段，并高亮关键词。不要尝试在结果片段中保留富文本 HTML 格式。
- **D-95:** 点击搜索结果后，在主界面展开/选中对应分区与页面，并加载该页面到右侧编辑器；Phase 5 不要求把 QTextEdit 光标定位到正文匹配位置。
- **D-96:** 点击结果跳转后搜索弹窗保持打开，用户可以连续点击多个结果查看。

### Claude's Discretion
无。所有本次讨论的灰区均由用户选择了明确方向。

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

None — discussion stayed within phase scope.
</user_constraints>

## Summary

Phase 05 应在既有 Python 3.13 + PySide6 6.11.0 + Qt6 桌面架构上实现，不需要引入新的第三方库；当前项目已在 `pyproject.toml` 中声明 `PySide6>=6.11.0`、`cryptography>=48.0.0`，并在项目虚拟环境中安装了 PySide6 6.11.0、cryptography 48.0.0、pytest 9.0.3。[VERIFIED: /home/jone/projects/secnotepad/pyproject.toml][VERIFIED: project .venv import/version probe][VERIFIED: PyPI JSON]

标签数据层已经具备落点：`SNoteItem.tags` 是 `list[str]` 字段，`Serializer.to_json()` 通过 `asdict()` 写出标签，`Serializer.from_json()` 对缺失 `tags` 使用 `[]` 默认值，因此 Phase 05 主要是 UI、校验、搜索服务和导航跳转集成，而不是数据格式迁移。[VERIFIED: /home/jone/projects/secnotepad/src/secnotepad/model/snote_item.py][VERIFIED: /home/jone/projects/secnotepad/src/secnotepad/model/serializer.py]

搜索应作为内存内、当前已解密笔记本范围的同步服务实现：遍历 `SNoteItem` 树，提取标题、标签和正文纯文本，生成安全片段，再由 `SearchDialog` 显示结果并向 `MainWindow` 发出跳转请求；不要建立外部索引、数据库、跨文件搜索或后台服务。[VERIFIED: /home/jone/projects/secnotepad/.planning/phases/05-tags-and-search/05-CONTEXT.md][VERIFIED: /home/jone/projects/secnotepad/.planning/PROJECT.md]

**Primary recommendation:** 新增 `TagBarWidget`、`SearchDialog` 和纯 Python `SearchService`，在 `MainWindow._setup_editor_area()`、`_show_note_in_editor()`、`_show_editor_placeholder()`、菜单动作和导航选择 API 中集成；保持数据写入 `SNoteItem.tags` 与 `SNoteItem.content` 分离。[VERIFIED: /home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py][VERIFIED: /home/jone/projects/secnotepad/.planning/phases/05-tags-and-search/05-CONTEXT.md]

## Project Constraints (from CLAUDE.md)

- 与用户沟通使用中文；供人类阅读的 `PLAN.md`、`SPEC.md`、`RESEARCH.md` 等文档需使用中文撰写。[VERIFIED: /home/jone/projects/secnotepad/CLAUDE.md]
- 代码注释可使用英文或中文，以清晰为准；GSD 内部指令、配置文件、代码标识符可使用英文。[VERIFIED: /home/jone/projects/secnotepad/CLAUDE.md]
- 新 phase 分支由 GSD 配置的 `branching_strategy: phase` 自动处理，分支命名格式为 `gsd/phase-{N}-{name}`。[VERIFIED: /home/jone/projects/secnotepad/CLAUDE.md][VERIFIED: /home/jone/projects/secnotepad/.planning/config.json]
- 项目核心是本地加密笔记本：分区树 + 页面列表的层级笔记管理，笔记内容以加密文件形式保存在本地。[VERIFIED: /home/jone/projects/secnotepad/CLAUDE.md]
- 技术栈约束未在 CLAUDE.md 的 stack 区块展开，但 PROJECT.md 明确约束 Python 3 + PySide6 + Qt6、cryptography、QTextEdit 原生富文本、不使用 QWebEngine、目标平台 Windows + Linux。[VERIFIED: /home/jone/projects/secnotepad/CLAUDE.md][VERIFIED: /home/jone/projects/secnotepad/.planning/PROJECT.md]
- 修改文件前应通过 GSD 工作流入口保持规划产物和执行上下文同步；本次研究由 GSD 研究目标触发，满足该约束。[VERIFIED: /home/jone/projects/secnotepad/CLAUDE.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| 页面标签持久化 | 数据模型 / 本地存储 | UI | `SNoteItem.tags` 是页面数据字段，序列化随整体 JSON 进入加密 `.secnote`；UI 只负责编辑和展示。[VERIFIED: snote_item.py][VERIFIED: serializer.py][VERIFIED: 05-CONTEXT.md] |
| 标签 chip 行 | 桌面客户端 UI | 数据模型 | 决策要求标签入口位于右侧编辑区顶部并操作当前页面 tags。[VERIFIED: 05-CONTEXT.md] |
| 标签补全 | 桌面客户端 UI | 搜索/遍历服务 | `QCompleter` 可为 `QLineEdit` 提供补全；补全集合应从当前笔记本标签遍历得到。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html][VERIFIED: 05-CONTEXT.md] |
| 全文搜索 | 应用服务层 / 内存业务逻辑 | UI | 搜索范围是当前已打开笔记本的内存 `SNoteItem` 树，UI 弹窗只提交条件和显示结果。[VERIFIED: 05-CONTEXT.md][VERIFIED: snote_item.py] |
| HTML 正文转纯文本 | 应用服务层 | Qt 文档工具 | `QTextDocument` 提供 `toPlainText()`，`QTextDocumentFragment` 支持从 HTML 构造并获取纯文本；片段不应保留富文本 HTML。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocumentFragment.html][VERIFIED: 05-CONTEXT.md] |
| 搜索结果跳转 | MainWindow 导航集成 | 搜索弹窗 | 现有导航由 `QTreeView`/`QListView` 的 selection model 驱动；结果点击应由弹窗发信号给 MainWindow 执行选中分区和页面。[VERIFIED: main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QItemSelectionModel.html] |
| 保存与 dirty 标记 | MainWindow / 文件服务 | UI | 现有 `mark_dirty()` 控制窗口标题和保存提示；只有标签变更应置脏，搜索和跳转不应置脏。[VERIFIED: main_window.py][VERIFIED: 05-CONTEXT.md] |

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TAG-01 | 用户可以为一个页面添加多个标签 | 使用 `TagBarWidget` 编辑当前 `SNoteItem.tags`，同一页面允许多个字符串标签。[VERIFIED: REQUIREMENTS.md][VERIFIED: snote_item.py] |
| TAG-02 | 用户可以移除页面的标签 | chip 行每个标签提供移除入口，移除后更新 `SNoteItem.tags` 并调用 `mark_dirty()`。[VERIFIED: REQUIREMENTS.md][VERIFIED: 05-CONTEXT.md] |
| TAG-03 | 标签在页面列表或页面上可见展示 | 用户决策要求页面列表不显示标签，标签在右侧当前页面编辑区顶部可见展示。[VERIFIED: REQUIREMENTS.md][VERIFIED: 05-CONTEXT.md] |
| SRCH-01 | 用户可以通过关键词搜索页面标题和内容 | `SearchService` 遍历整棵树并默认搜索标题与正文纯文本；标签字段为可选范围。[VERIFIED: REQUIREMENTS.md][VERIFIED: 05-CONTEXT.md] |
| SRCH-02 | 搜索结果以列表展示，包含标题和高亮匹配片段 | `SearchDialog` 显示标题、分区路径和围绕首个命中的纯文本片段；高亮只用于片段展示。[VERIFIED: REQUIREMENTS.md][VERIFIED: 05-CONTEXT.md] |
| SRCH-03 | 点击搜索结果可跳转到对应页面 | 结果项携带 note id / 对象引用和分区路径，MainWindow 展开并选中分区与页面。[VERIFIED: REQUIREMENTS.md][VERIFIED: main_window.py] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.12 declared; 3.13.5 installed in `.venv` | 应用运行时、数据模型、搜索服务 | 项目声明 `requires-python >=3.12`，当前 `.venv` 为 Python 3.13.5。[VERIFIED: pyproject.toml][VERIFIED: .venv version probe] |
| PySide6 / Qt for Python | 6.11.0 installed; 6.11.0 current on PyPI, uploaded 2026-03-23 | Qt6 Widgets UI、QDialog、QCompleter、QTextDocument、Model/View | 项目依赖已声明并安装；官方 Qt for Python 文档覆盖相关 widgets 和 model/view API。[VERIFIED: pyproject.toml][VERIFIED: PyPI JSON][CITED: https://doc.qt.io/qtforpython-6/] |
| Qt Widgets | bundled with PySide6 6.11.0 | `QWidget`、`QDialog`、`QLineEdit`、`QCompleter`、`QListWidget`/`QListView`、`QToolButton` | 现有 MainWindow、RichTextEditorWidget 和测试均使用 Qt Widgets；Phase 05 UI 应沿用同一组件体系。[VERIFIED: main_window.py][VERIFIED: rich_text_editor.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDialog.html] |
| QTextDocument / QTextDocumentFragment | Qt 6 API via PySide6 | 从 HTML 提取纯文本、正文搜索和片段生成 | 官方文档说明 `QTextDocument` 提供 `toPlainText()`/`toHtml()`，`QTextDocumentFragment` 可由 HTML 创建并输出纯文本。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocumentFragment.html] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 installed; 9.0.3 current on PyPI, uploaded 2026-04-07 | 单元测试、UI 行为测试 | Phase 05 应新增服务层、标签控件、搜索弹窗和 MainWindow 集成测试。[VERIFIED: requirements.txt][VERIFIED: PyPI JSON][VERIFIED: tests/conftest.py] |
| cryptography | 48.0.0 installed; 48.0.0 current on PyPI, uploaded 2026-05-04 | 已有 `.secnote` 文件加密保存 | Phase 05 不直接新增加密逻辑，但标签持久化会随现有 Serializer + FileService 进入加密文件。[VERIFIED: pyproject.toml][VERIFIED: PyPI JSON][VERIFIED: crypto/file_service.py] |
| html / re 标准库 | Python stdlib | 片段高亮转义、关键词匹配 | 搜索结果片段若用 rich text label 展示，应先 HTML 转义用户内容再插入 `<mark>`/span，避免把笔记内容当 UI HTML 执行。[ASSUMED] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| 内存遍历 `SNoteItem` 树 | SQLite FTS / Whoosh / Tantivy | 当前锁定范围是当前打开笔记本内搜索且不需要索引服务；外部索引会增加加密数据落盘风险和迁移复杂度。[VERIFIED: 05-CONTEXT.md][ASSUMED] |
| Qt Widgets `QDialog` 搜索弹窗 | 常驻搜索栏 / dock widget | 用户已锁定菜单弹窗入口，不应探索常驻 UI。[VERIFIED: 05-CONTEXT.md] |
| `QCompleter` + `QStringListModel` | 自定义补全弹窗 | 官方 `QCompleter` 已支持 `QLineEdit` 补全并可设大小写敏感性；自定义弹窗会重复实现键盘导航和匹配逻辑。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html] |
| QTextDocument 纯文本提取 | 正则剥离 HTML 标签 | Qt 文档对象理解 QTextEdit 生成的 HTML，正则剥离容易误处理实体、段落和嵌套标签。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html][ASSUMED] |

**Installation:**
```bash
# 已安装在项目虚拟环境；如需重建环境：
/home/jone/projects/secnotepad/.venv/bin/pip install -r /home/jone/projects/secnotepad/requirements.txt
```

**Version verification:** 本项目是 Python 项目，不使用 `npm view`；版本通过 `.venv` import/version probe、`pip index versions` 和 PyPI JSON 验证。[VERIFIED: command output]

## Architecture Patterns

### System Architecture Diagram

```text
用户输入标签 / 点击移除
        │
        ▼
TagBarWidget（右侧编辑区顶部）
        │ trim / 长度 / 当前页面内大小写去重
        ▼
MainWindow 当前页面解析 ───────────────┐
        │                              │
        ▼                              │
SNoteItem.tags 更新                    │
        │                              │
        ▼                              │
mark_dirty() → Serializer.to_json() → FileService.save() → 加密 .secnote

用户打开菜单“搜索”
        │
        ▼
SearchDialog（关键词 + 字段筛选 + 搜索按钮/回车）
        │
        ▼
SearchService.search(root, query, fields)
        │
        ├─ 遍历 SNoteItem 树，维护分区路径
        ├─ 标题匹配
        ├─ HTML content → QTextDocument/Fragment → 纯文本匹配
        └─ tags 匹配（可选字段）
        │
        ▼
SearchResult(title, section_path, snippet, note_id/object)
        │
        ▼
SearchDialog 结果列表展示高亮片段
        │ result activated
        ▼
MainWindow.select_note_by_id()/object
        │
        ├─ 展开并选中目标分区（QTreeView + SectionFilterProxy）
        ├─ PageListModel 绑定目标分区
        └─ 选中目标页面 → _show_note_in_editor()
```

该数据流匹配用户锁定的标签位置、搜索弹窗、全树搜索、纯文本片段和点击跳转要求。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py]

### Recommended Project Structure

```text
src/secnotepad/
├── model/
│   ├── snote_item.py              # 已有：SNoteItem.tags 字段
│   ├── serializer.py              # 已有：tags 序列化/旧数据兼容
│   └── search_service.py          # 新增：纯 Python/Qt 文档辅助的搜索与片段生成
├── ui/
│   ├── tag_bar_widget.py          # 新增：页面标签 chip 行 + 添加入口 + QCompleter
│   ├── search_dialog.py           # 新增：关键词、字段筛选、结果列表和 result_activated 信号
│   ├── rich_text_editor.py        # 已有：富文本编辑器，不把 tags 写入 content
│   └── main_window.py             # 集成标签栏、搜索菜单和跳转
└── tests/
    ├── model/test_search_service.py
    └── ui/test_tag_bar_widget.py / test_search_dialog.py / test_main_window_search.py
```

上述结构保持现有“数据类/模型/视图分离”和 MainWindow 集成模式。[VERIFIED: tree_model.py][VERIFIED: page_list_model.py][VERIFIED: main_window.py]

### Pattern 1: 标签栏作为页面元数据控件，不进入 HTML

**What:** `TagBarWidget` 接收当前页面 `tags` 和补全候选集合，发出 `tag_added(str)` / `tag_removed(str)` 信号；MainWindow 在 handler 中修改当前 `SNoteItem.tags` 并调用 `mark_dirty()`。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py]

**When to use:** 当前页面被选中时启用；无页面或 placeholder 状态时禁用/隐藏为不可编辑状态。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py]

**Example:**
```python
# Source: Qt for Python QCompleter docs + project MainWindow signal pattern
# [CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html]
from PySide6.QtCore import QStringListModel, Qt, Signal
from PySide6.QtWidgets import QCompleter, QLineEdit, QWidget

class TagBarWidget(QWidget):
    tag_added = Signal(str)
    tag_removed = Signal(str)

    def set_available_tags(self, tags: list[str]) -> None:
        model = QStringListModel(sorted(tags, key=str.casefold), self)
        completer = QCompleter(model, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._line_edit.setCompleter(completer)
```

### Pattern 2: 搜索服务返回不可变结果对象，UI 不直接遍历树

**What:** `SearchService` 负责树遍历、字段匹配、HTML 转纯文本和片段生成；`SearchDialog` 只调用服务并展示结果。[VERIFIED: 05-CONTEXT.md][VERIFIED: snote_item.py]

**When to use:** 搜索按钮或回车触发搜索时使用；不要在每次输入变化时实时运行搜索。[VERIFIED: 05-CONTEXT.md]

**Example:**
```python
# Source: Qt for Python QTextDocumentFragment docs
# [CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocumentFragment.html]
from PySide6.QtGui import QTextDocumentFragment

def html_to_plain_text(html: str) -> str:
    return QTextDocumentFragment.fromHtml(html or "").toPlainText()
```

### Pattern 3: 跳转通过 MainWindow 统一执行选择状态变更

**What:** SearchDialog 的 result activated 信号携带目标 note id 或目标 note 对象；MainWindow 查找父分区，设置树当前索引，等待/触发 `PageListModel.set_section()` 后设置列表当前页。[VERIFIED: main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QItemSelectionModel.html]

**When to use:** 点击或双击搜索结果时使用；弹窗保持打开，跳转不调用 `mark_dirty()`。[VERIFIED: 05-CONTEXT.md]

**Example:**
```python
# Source: Qt model/view selection docs
# [CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_tutorials_modelview.html]
selection_model = tree_view.selectionModel()
selection_model.selectionChanged.connect(selection_changed_slot)
```

### Anti-Patterns to Avoid

- **把标签写进 `SNoteItem.content` HTML:** 标签已有 `SNoteItem.tags` 字段；写进 HTML 会污染正文搜索、富文本编辑和序列化语义。[VERIFIED: snote_item.py][VERIFIED: 05-CONTEXT.md]
- **在页面列表显示标签:** 用户明确要求页面列表保持单列标题模式，本阶段不做多行 delegate。[VERIFIED: 05-CONTEXT.md]
- **实时搜索/debounce:** 用户明确要求回车或“搜索”按钮触发，不要默认每次输入触发。[VERIFIED: 05-CONTEXT.md]
- **把片段高亮当作正文定位:** Phase 05 不要求把 QTextEdit 光标定位到正文匹配位置，只需跳转页面。[VERIFIED: 05-CONTEXT.md]
- **外部索引落盘:** 项目核心价值是磁盘上只保存加密笔记内容；外部搜索索引可能引入明文副本风险。[VERIFIED: PROJECT.md][ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 标签输入补全 | 自定义下拉浮层和键盘选择 | `QCompleter` + `QStringListModel` | 官方组件已支持 `QLineEdit` 补全和大小写敏感性设置。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QStringListModel.html] |
| HTML 转纯文本 | 正则删除 `<...>` | `QTextDocumentFragment.fromHtml(...).toPlainText()` 或 `QTextDocument.toPlainText()` | Qt 文档 API 能处理 QTextEdit 生成的 HTML 文档片段。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocumentFragment.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html] |
| 搜索弹窗生命周期 | 手写顶层窗口状态机 | `QDialog` / modeless dialog + Qt signals | `QDialog` 是 Qt 对话框基类，MainWindow 现有架构已使用 Qt signal/slot。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDialog.html][VERIFIED: password_dialog.py][VERIFIED: main_window.py] |
| 导航选择传播 | 直接手动调用多个 UI 更新函数并绕过 selection model | `QTreeView.setCurrentIndex()` / `QListView.setCurrentIndex()` + 现有 selection handlers | 现有页面加载由 selection currentChanged handler 驱动；绕过会导致列表、编辑器和状态不同步。[VERIFIED: main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QItemSelectionModel.html] |
| 加密保存标签 | 单独保存 tags 文件或设置 | 复用 `Serializer.to_json()` + `FileService.save()` | `tags` 已在 SNoteItem JSON 中，整体文件保存已加密。[VERIFIED: serializer.py][VERIFIED: crypto/file_service.py] |

**Key insight:** Phase 05 的复杂点不是算法库选择，而是状态边界：标签是页面元数据、搜索是只读查询、跳转是导航选择，三者不能污染富文本 HTML 或 dirty 语义。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py]

## Common Pitfalls

### Pitfall 1: `QTextEdit.toHtml()` 生成的完整 HTML 直接用于片段展示
**What goes wrong:** 搜索片段含有 Qt HTML 头、样式或用户内容 HTML，结果列表可能难读或形成 UI 注入风险。[VERIFIED: rich_text_editor.py][ASSUMED]  
**Why it happens:** QTextEdit 内容持久化是 HTML，但搜索结果要求纯文本片段。[VERIFIED: REQUIREMENTS.md][VERIFIED: 05-CONTEXT.md]  
**How to avoid:** 搜索服务先用 Qt 文档 API 提取纯文本，再对展示片段做 HTML 转义和关键词高亮。[CITED: QTextDocumentFragment docs][ASSUMED]  
**Warning signs:** 结果片段出现 `<p>`、`style=`、`<!DOCTYPE>` 或原始 HTML 标签。[VERIFIED: rich_text_editor.py]

### Pitfall 2: 标签变更未调用 `mark_dirty()`
**What goes wrong:** 用户添加/删除标签后关闭或保存流程认为无修改，标签丢失。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py]  
**Why it happens:** 标签变化不经过 `_on_editor_content_changed()`，不会自动触发正文 dirty 逻辑。[VERIFIED: main_window.py]  
**How to avoid:** 标签 add/remove handler 独立比较并更新 `note.tags`，成功变更后调用 `mark_dirty()`。[VERIFIED: 05-CONTEXT.md]  
**Warning signs:** 标签 UI 变化后窗口标题没有 `*`，保存后重新打开标签消失。[VERIFIED: main_window.py]

### Pitfall 3: 标签补全候选没有随笔记本变化刷新
**What goes wrong:** 新增标签后补全列表不包含新标签，或打开另一个笔记本后仍显示旧标签。[VERIFIED: 05-CONTEXT.md][ASSUMED]  
**Why it happens:** 补全集合是从当前笔记本遍历得到的派生状态。[VERIFIED: 05-CONTEXT.md]  
**How to avoid:** 每次打开/新建笔记本、添加/删除标签、显示页面时从 `_root_item` 收集唯一标签并更新 `QStringListModel`。[VERIFIED: snote_item.py][CITED: QStringListModel docs]  
**Warning signs:** 补全建议出现其他文件标签或缺少刚添加的标签。[ASSUMED]

### Pitfall 4: 结果跳转绕过 `SectionFilterProxy` 映射
**What goes wrong:** 树视图无法选中目标分区，页面列表没有绑定到目标分区，点击结果无效或选中错误页面。[VERIFIED: main_window.py]  
**Why it happens:** 左侧视图使用 `SectionFilterProxy`，源模型索引和代理索引不能混用。[VERIFIED: main_window.py][VERIFIED: section_filter_proxy.py]  
**How to avoid:** 查找源 `QModelIndex` 后用 `mapFromSource()` 取得代理索引，再调用 tree view 选择；页面选择使用当前 `PageListModel.index(row, 0)`。[VERIFIED: main_window.py]  
**Warning signs:** 搜索结果点击后右侧仍显示旧页面，或树选中项和页面列表不一致。[ASSUMED]

### Pitfall 5: 搜索操作错误置脏
**What goes wrong:** 用户只是搜索和跳转，窗口标题出现 `*`，关闭时误提示保存。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py]  
**Why it happens:** 跳转过程复用了结构变更路径或误调用 `mark_dirty()`。[VERIFIED: main_window.py]  
**How to avoid:** 搜索、结果展示、结果跳转都不修改 `SNoteItem`；只有标签 add/remove 修改 tags 时置脏。[VERIFIED: 05-CONTEXT.md]  
**Warning signs:** 搜索后 `_is_dirty` 从 False 变 True。[VERIFIED: main_window.py]

### Pitfall 6: 大小写去重破坏用户显示形式
**What goes wrong:** 已有 `Python` 后添加 `python` 导致显示变成小写，违反“保留首次添加文本”。[VERIFIED: 05-CONTEXT.md]  
**Why it happens:** 去重时直接把标签规范化后保存。[ASSUMED]  
**How to avoid:** 比较用 `tag.casefold()` 集合，保存用 trim 后的原字符串；重复时不修改旧标签。[VERIFIED: 05-CONTEXT.md]  
**Warning signs:** 添加重复标签后原 chip 文本大小写改变。[ASSUMED]

## Code Examples

Verified patterns from official sources and existing codebase:

### QCompleter 用于标签补全
```python
# Source: Qt for Python QCompleter docs
# [CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QCompleter.html]
from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import QCompleter, QLineEdit

line_edit = QLineEdit(parent)
model = QStringListModel(["Python", "项目 A", "安全 笔记"])
completer = QCompleter(model, parent)
completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
line_edit.setCompleter(completer)
```

### HTML 内容提取纯文本
```python
# Source: Qt for Python QTextDocumentFragment docs
# [CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocumentFragment.html]
from PySide6.QtGui import QTextDocumentFragment

def html_to_plain_text(html: str) -> str:
    return QTextDocumentFragment.fromHtml(html or "").toPlainText()
```

### selection model 驱动视图同步
```python
# Source: Qt for Python model/view tutorial
# [CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_tutorials_modelview.html]
selection_model = tree_view.selectionModel()
selection_model.selectionChanged.connect(selection_changed_slot)
```

### 标签大小写去重但保留首次显示形式
```python
# Source: Phase 05 locked decisions D-85/D-86
# [VERIFIED: /home/jone/projects/secnotepad/.planning/phases/05-tags-and-search/05-CONTEXT.md]
def add_tag_preserving_display(tags: list[str], raw: str, max_len: int = 32) -> bool:
    tag = raw.strip()
    if not tag or len(tag) > max_len:
        return False
    existing = {value.casefold() for value in tags}
    if tag.casefold() in existing:
        return False
    tags.append(tag)
    return True
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 正则剥离 HTML 后搜索 | 用 Qt 文档对象从 QTextEdit HTML 提取纯文本 | Qt 文档 API 当前可用；本项目 Phase 04 采用 QTextEdit HTML 存储 | 片段生成更符合 QTextEdit 文档语义，减少 HTML/实体处理错误。[CITED: QTextDocument docs][VERIFIED: rich_text_editor.py] |
| 外部全文索引 | 当前已解密笔记本内同步遍历 | Phase 05 用户决策锁定当前打开笔记本范围 | 避免外部明文索引和跨文件复杂度。[VERIFIED: 05-CONTEXT.md][VERIFIED: PROJECT.md][ASSUMED] |
| 页面列表中显示标签 | 右侧页面编辑区顶部 chip 行 | Phase 05 D-81/D-83 锁定 | 保持中间列表单列标题模式，降低 delegate/UI 复杂度。[VERIFIED: 05-CONTEXT.md] |
| 实时搜索框 | 菜单触发的搜索弹窗，回车/按钮执行 | Phase 05 D-89/D-90 锁定 | 避免每次输入触发全树搜索和复杂 debounce 状态。[VERIFIED: 05-CONTEXT.md] |

**Deprecated/outdated:**
- 为本阶段引入 QWebEngine 展示/搜索富文本：项目明确不使用 QWebEngine，富文本核心为 QTextEdit 原生组件。[VERIFIED: PROJECT.md]
- 为标签新增全局标签管理页：Phase 05 明确不新增全局标签管理页。[VERIFIED: 05-CONTEXT.md]
- 搜索结果定位到正文命中位置：Phase 05 明确不要求把 QTextEdit 光标定位到正文匹配位置。[VERIFIED: 05-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 使用 Python stdlib `html`/`re` 足以安全生成 UI 高亮片段 | Standard Stack / Common Pitfalls | 如果实现未正确转义，搜索结果片段可能显示错误或形成富文本注入风险。 |
| A2 | 外部索引会增加加密数据落盘风险和复杂度 | Alternatives / Anti-Patterns / State of the Art | 如果后续需求需要大型笔记本性能，可能需要重新评估索引，但 Phase 05 当前范围不需要。 |
| A3 | 补全候选不刷新会造成用户体验问题 | Pitfalls | 如果实现选择每次打开添加弹窗动态计算候选，可能无需独立刷新逻辑。 |
| A4 | 结果跳转错误通常表现为树、列表、编辑器不同步 | Pitfalls | 如果 MainWindow 暴露了更直接的选择 API，症状可能不同，但仍需测试跳转一致性。 |
| A5 | 添加重复标签时若用规范化字符串保存会破坏显示形式 | Pitfalls | 如果实现分离 display/canonical 字段则风险不同；当前数据模型只有 `list[str]`。 |

## Open Questions (RESOLVED)

1. **搜索菜单放在哪个顶层菜单中？ — RESOLVED**
   - Chosen answer: 使用 `编辑(&E) → 搜索(&F)...`，并设置 `Ctrl+F` 快捷键。
   - Reflected by: `05-UI-SPEC.md` 的「搜索入口与弹窗」明确菜单位置和快捷键；`05-05-PLAN.md` 在 MainWindow 编辑菜单中新增 `搜索(&F)...` action。
   - Rationale: 用户锁定菜单弹窗入口（D-89），UI-SPEC 已将该入口落到编辑菜单；这符合桌面编辑器常见查找入口且不新增顶层菜单。

2. **结果列表使用 QListWidget 还是自定义 QAbstractListModel？ — RESOLVED**
   - Chosen answer: 使用 `QListWidget` + 自定义 item widget 或 Qt 等价 Model/View；计划默认按轻量 `QListWidget` 实现，并把原始 `SearchResult` 存入 item `Qt.UserRole`。
   - Reflected by: `05-UI-SPEC.md` Component Inventory 写明 `QListWidget + 自定义 item widget 或等价 Model/View`；`05-04-PLAN.md` Task 2 要求 `QListWidget`（objectName `search_results_list`）并保存 `SearchResult`。
   - Rationale: 搜索结果是弹窗内临时结果集，轻量列表足以展示标题、路径、片段并支持测试；不需要为本阶段引入额外搜索结果模型。

3. **高亮片段使用 QLabel rich text 还是 QListWidget item 文本？ — RESOLVED**
   - Chosen answer: 使用结果项中的自定义 widget / `QLabel` rich text 展示高亮片段；所有用户内容先由 `SearchService` 转义，再插入受控 `<mark>` 或等价高亮标签。
   - Reflected by: `05-UI-SPEC.md` 要求高亮前先 HTML 转义，结果列表可用自定义 item widget；`05-01-PLAN.md` 负责安全 snippet 生成，`05-04-PLAN.md` 只展示 `SearchService.snippet`，不得读取 `result.note.content`。
   - Rationale: 普通 `QListWidgetItem` plain text 不能表达高亮；把高亮限制在已转义 snippet 的 QLabel rich text 中，可满足 SRCH-02 且避免原始笔记 HTML 注入。

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| `/home/jone/projects/secnotepad/.venv/bin/python` | 测试、运行 PySide6 应用 | ✓ | Python 3.13.5 | 无需 fallback；用户记忆要求测试/脚本使用项目 `.venv`。[VERIFIED: .venv version probe][VERIFIED: MEMORY.md] |
| PySide6 | 标签 UI、搜索弹窗、Qt 文档纯文本提取 | ✓ | 6.11.0 | 无 fallback；项目核心依赖。[VERIFIED: .venv import probe][VERIFIED: pyproject.toml] |
| pytest | 自动化测试 | ✓ | 9.0.3 | 无 fallback；已安装。[VERIFIED: .venv import probe][VERIFIED: requirements.txt] |
| cryptography | 保存含 tags 的加密 `.secnote` 文件 | ✓ | 48.0.0 | 无 fallback；Phase 05 复用既有保存链路。[VERIFIED: .venv import probe][VERIFIED: pyproject.toml] |
| pip | 依赖安装/验证 | ✓ | 25.1.1 | 可用系统包管理器重建 venv，但当前不需要。[VERIFIED: .venv pip version probe] |

**Missing dependencies with no fallback:**
- None — Phase 05 所需运行时和测试依赖均在 `.venv` 可用。[VERIFIED: environment probe]

**Missing dependencies with fallback:**
- None。[VERIFIED: environment probe]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + PySide6 Qt Widgets fixtures。[VERIFIED: .venv import probe][VERIFIED: tests/conftest.py] |
| Config file | `/home/jone/projects/secnotepad/pyproject.toml` 的 `[tool.pytest.ini_options] testpaths = ["tests"]`。[VERIFIED: pyproject.toml] |
| Quick run command | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/model/test_search_service.py -x`。[VERIFIED: tests layout][ASSUMED] |
| Full suite command | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests -x`。[VERIFIED: tests layout][VERIFIED: MEMORY.md] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| TAG-01 | 为当前页面添加多个标签，保留大小写/中文/空格/符号，拒绝空标签和超长标签 | unit + UI integration | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/ui/test_tag_bar_widget.py -x` | ❌ Wave 0 |
| TAG-02 | 移除 chip 后更新 `SNoteItem.tags` 并置脏 | UI integration | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/ui/test_main_window_tags.py -x` | ❌ Wave 0 |
| TAG-03 | 标签在右侧页面顶部展示，未选页面禁用/不可编辑，页面列表不显示标签 | UI integration | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/ui/test_main_window_tags.py -x` | ❌ Wave 0 |
| SRCH-01 | 搜索标题和正文纯文本，标签字段可选 | unit | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/model/test_search_service.py -x` | ❌ Wave 0 |
| SRCH-02 | 结果包含标题、分区路径、高亮片段 | unit + UI | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/ui/test_search_dialog.py -x` | ❌ Wave 0 |
| SRCH-03 | 点击结果选中目标分区和页面，弹窗保持打开，不置脏 | UI integration | `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/ui/test_main_window_search.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest <changed test file> -x`。[VERIFIED: existing pytest pattern][VERIFIED: MEMORY.md]
- **Per wave merge:** `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/model /home/jone/projects/secnotepad/tests/ui -x`。[VERIFIED: tests layout]
- **Phase gate:** `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests -x` 全套通过后再进入 `/gsd-verify-work`。[VERIFIED: config nyquist_validation true][VERIFIED: tests layout]

### Wave 0 Gaps
- [ ] `/home/jone/projects/secnotepad/tests/model/test_search_service.py` — 覆盖 SRCH-01/SRCH-02 的树遍历、HTML 转纯文本、字段筛选、路径和片段生成。[VERIFIED: tests directory exists][ASSUMED]
- [ ] `/home/jone/projects/secnotepad/tests/ui/test_tag_bar_widget.py` — 覆盖 TAG-01/TAG-02 的 add/remove、trim、casefold 去重、长度限制、补全候选。[VERIFIED: tests directory exists][ASSUMED]
- [ ] `/home/jone/projects/secnotepad/tests/ui/test_search_dialog.py` — 覆盖搜索弹窗输入、字段勾选、回车/按钮触发、结果展示。[VERIFIED: tests directory exists][ASSUMED]
- [ ] `/home/jone/projects/secnotepad/tests/ui/test_main_window_tags.py` — 覆盖右侧标签区域集成、页面切换刷新、dirty 语义。[VERIFIED: tests directory exists][ASSUMED]
- [ ] `/home/jone/projects/secnotepad/tests/ui/test_main_window_search.py` — 覆盖菜单动作、搜索结果跳转、弹窗保持打开、不置脏。[VERIFIED: tests directory exists][ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Phase 05 不新增认证；打开笔记本密码流程已在前序文件操作中实现。[VERIFIED: PROJECT.md][VERIFIED: main_window.py] |
| V3 Session Management | yes | 搜索仅在当前已打开、已解密的内存笔记本中执行；关闭会话时现有 `_clear_session()` 清理 root/password 状态。[VERIFIED: PROJECT.md][VERIFIED: main_window.py] |
| V4 Access Control | no | 单用户本地桌面应用，Phase 05 不新增多用户或权限模型。[VERIFIED: REQUIREMENTS.md][VERIFIED: PROJECT.md] |
| V5 Input Validation | yes | 标签输入 trim、拒绝空值、长度限制、casefold 去重；搜索 query 作为纯字符串处理，片段展示前转义。[VERIFIED: 05-CONTEXT.md][ASSUMED] |
| V6 Cryptography | yes | 不手写加密；标签随既有 JSON 通过 `FileService` 和 cryptography 进入加密 `.secnote` 文件。[VERIFIED: pyproject.toml][VERIFIED: serializer.py][VERIFIED: crypto/file_service.py] |

### Known Threat Patterns for PySide6 local encrypted notes

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| 搜索片段富文本注入 | Tampering / Information Disclosure | 正文 HTML 转纯文本后生成片段；任何 rich text 高亮展示前先 HTML 转义用户内容。[VERIFIED: 05-CONTEXT.md][ASSUMED] |
| 明文搜索索引落盘 | Information Disclosure | 不建立外部索引、数据库或缓存文件；仅搜索当前内存树。[VERIFIED: 05-CONTEXT.md][VERIFIED: PROJECT.md][ASSUMED] |
| 标签字段绕过保存保护 | Tampering | 标签 add/remove 成功后调用 `mark_dirty()`，通过既有保存/关闭提示保护数据。[VERIFIED: 05-CONTEXT.md][VERIFIED: main_window.py] |
| 过长标签造成 UI 退化 | Denial of Service | 添加标签时限制合理长度，用户决策建议 32 字符。[VERIFIED: 05-CONTEXT.md] |
| 搜索导致敏感内容暴露在日志 | Information Disclosure | 不记录 query、片段或正文到日志/调试输出；当前代码未显示日志框架，规划中不应新增敏感日志。[VERIFIED: source tree listing][ASSUMED] |

## Sources

### Primary (HIGH confidence)
- `/home/jone/projects/secnotepad/.planning/phases/05-tags-and-search/05-CONTEXT.md` — Phase 05 用户锁定决策 D-81~D-96、范围、现有集成点。
- `/home/jone/projects/secnotepad/.planning/REQUIREMENTS.md` — TAG-01~03、SRCH-01~03 需求定义与阶段映射。
- `/home/jone/projects/secnotepad/.planning/ROADMAP.md` — Phase 05 目标、成功标准与 Phase 04 完成状态。
- `/home/jone/projects/secnotepad/.planning/PROJECT.md` — 技术栈、范围、加密核心价值、QTextEdit/QWebEngine 决策。
- `/home/jone/projects/secnotepad/CLAUDE.md` — 中文文档、GSD、分支和项目约束。
- `/home/jone/projects/secnotepad/src/secnotepad/model/snote_item.py` — `SNoteItem.tags` 字段。
- `/home/jone/projects/secnotepad/src/secnotepad/model/serializer.py` — tags 序列化和旧数据默认空列表。
- `/home/jone/projects/secnotepad/src/secnotepad/ui/main_window.py` — 右侧编辑区、导航选择、dirty、菜单和保存集成。
- `/home/jone/projects/secnotepad/src/secnotepad/ui/rich_text_editor.py` — QTextEdit HTML、格式工具栏和安全粘贴边界。
- `/home/jone/projects/secnotepad/tests/conftest.py` 和 `/home/jone/projects/secnotepad/pyproject.toml` — pytest + qapp 测试基础设施。
- Context7 `/websites/doc_qt_io_qtforpython-6` — `QCompleter`、`QStringListModel`、`QTextDocumentFragment`、`QTextDocument`、`QDialog`、`QItemSelectionModel` topics fetched。
- PyPI JSON / `.venv` probe — PySide6 6.11.0、cryptography 48.0.0、pytest 9.0.3 版本与发布时间。

### Secondary (MEDIUM confidence)
- Existing Phase 03/04 CONTEXT docs — 导航和富文本编辑器决策与模式，已由当前源码验证。

### Tertiary (LOW confidence)
- Assumptions Log 中 A1~A5 — 需要 planner 在具体控件实现和测试中确认。

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — 依赖版本由 `pyproject.toml`、`.venv` probe、PyPI JSON 和 Qt 官方文档验证。[VERIFIED]
- Architecture: HIGH — Phase 05 决策锁定，且关键数据/UI 集成点已由当前源码验证。[VERIFIED]
- Pitfalls: MEDIUM — dirty、proxy mapping、HTML 纯文本边界由源码和决策支持；片段高亮安全实现细节仍依赖 planner/implementer 选择具体控件。[VERIFIED][ASSUMED]
- Validation: HIGH — pytest 配置、qapp fixture 和现有 UI 测试模式已存在；Phase 05 具体测试文件尚需 Wave 0 新增。[VERIFIED]
- Security: MEDIUM — 加密保存和本地范围已验证；ASVS 映射和 UI 高亮注入控制需要实现期测试确认。[VERIFIED][ASSUMED]

**Research date:** 2026-05-11  
**Valid until:** 2026-06-10（核心栈稳定；若 PySide6/Qt API 或 Phase 05 决策变化，应提前刷新）
