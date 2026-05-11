# Phase 04：富文本编辑器 - Research

**Researched:** 2026-05-09  
**Domain:** PySide6 / Qt QTextEdit 富文本编辑、格式工具栏、加密本地笔记 HTML 持久化  
**Confidence:** HIGH（Qt/PySide6 API 与现有代码集成点已验证；待办复选框与粘贴净化的实现细节需在执行中用测试锁定）

## User Constraints

### Locked Decisions

- `.planning/phases/04-rich-text-editor/04-CONTEXT.md` 已锁定 Phase 04 边界：右侧页面编辑区实现完整 `QTextEdit` 富文本编辑，内容以 HTML 同步到当前 `SNoteItem`，编辑区上方提供独立格式工具栏，并支持 EDIT-01~EDIT-11 的格式、列表、编辑和缩放能力。[VERIFIED: Read .planning/phases/04-rich-text-editor/04-CONTEXT.md]
- 格式工具栏必须固定在右侧编辑区上方，未选中页面时整体禁用，选中页面后可用；格式动作状态必须跟随光标当前位置更新。[VERIFIED: Read .planning/phases/04-rich-text-editor/04-CONTEXT.md]
- 待办列表采用轻量“☐ ”可编辑文本符号方案，不实现 HTML checkbox、鼠标点击复选框交互或待办完成状态切换。[VERIFIED: Read .planning/phases/04-rich-text-editor/04-CONTEXT.md]
- 缩放是会话级显示偏好，只放在“视图”菜单，不写入页面 HTML、不写入 `.secnote`、不新增 `SNoteItem` 字段。[VERIFIED: Read .planning/phases/04-rich-text-editor/04-CONTEXT.md]

### Claude's Discretion

- `04-CONTEXT.md` 明确记录“无”Claude's Discretion；规划必须覆盖 D-65~D-80，不能用研究建议覆盖用户锁定决策。[VERIFIED: Read .planning/phases/04-rich-text-editor/04-CONTEXT.md]

### Deferred Ideas (OUT OF SCOPE)

- v1 排除 Markdown 编辑模式、手写/绘图、云同步、多用户协作、移动端、第三方登录和插件系统；v2 才考虑插入图片与表格编辑。[VERIFIED: Read .planning/REQUIREMENTS.md]

## Project Constraints (from CLAUDE.md)

- 与用户沟通必须使用中文；RESEARCH.md、PLAN.md、SPEC.md 等供人阅读的文档必须使用中文。[VERIFIED: Read CLAUDE.md]
- 代码注释可使用英文或中文，以清晰为准；GSD 内部指令、配置文件、代码标识符可使用英文。[VERIFIED: Read CLAUDE.md]
- Phase 分支命名格式为 `gsd/phase-{N}-{name}`，且当前工作分支为 `gsd/phase-04-rich-text-editor`。[VERIFIED: Read CLAUDE.md][VERIFIED: initial gitStatus]
- 不应在 GSD 工作流之外直接修改仓库源代码；本研究只写规划产物，不修改源代码。[VERIFIED: Read CLAUDE.md]
- 项目说明将 SecNotepad 定义为本地加密笔记本，内容以加密文件形式存储，用户通过密钥打开；富文本编辑、标签和搜索是核心编辑功能。[VERIFIED: Read CLAUDE.md]
- 项目内未发现 `.claude/skills/` 或 `.agents/skills/` 技能目录；`CLAUDE.md` 也记录为无项目技能。[VERIFIED: Bash ls .claude/.agents][VERIFIED: Read CLAUDE.md]

## Summary

Phase 04 应在现有 `MainWindow` 的右侧 `QTextEdit` 基础上演进为完整富文本编辑器，而不是引入新的编辑引擎。[VERIFIED: Read src/secnotepad/ui/main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html] 当前代码已经创建 `_editor_preview = QTextEdit()`，设置为可编辑，并在 `textChanged` 时通过 `toHtml()` 写回当前 `SNoteItem.content` 且调用 `mark_dirty()`；这为 EDIT-01 的 HTML 存储和脏标志链路提供了直接集成点。[VERIFIED: Read src/secnotepad/ui/main_window.py][VERIFIED: Read src/secnotepad/model/snote_item.py]

首选架构是抽出一个 `RichTextEditorWidget` 或同等私有组件，封装 `QTextEdit`、格式工具栏、格式动作和光标状态同步，然后由 `MainWindow` 只负责页面选择、加载/保存 HTML、脏标志和菜单动作路由。[ASSUMED] 这样做符合既有“纯数据模型 + Qt Model/View + MainWindow 连接信号”的分层模式，并能避免把所有格式动作继续塞进已经很大的 `MainWindow`。[VERIFIED: Read src/secnotepad/model/snote_item.py][VERIFIED: Read src/secnotepad/model/tree_model.py][VERIFIED: Read src/secnotepad/model/page_list_model.py][VERIFIED: Read src/secnotepad/ui/main_window.py]

安全上，本阶段不应扩大明文落盘面：HTML 仍应只存在于 `SNoteItem.content` 内存对象中，保存时沿用已有整体 JSON 加密写入流程；不要引入自动保存明文缓存、外部资源引用或未加密临时文件。[VERIFIED: Read src/secnotepad/crypto/file_service.py][VERIFIED: Read src/secnotepad/model/serializer.py][VERIFIED: Read .planning/REQUIREMENTS.md] 粘贴行为需要特别计划：Qt `QTextEdit` 默认支持插入 plain text、HTML 和 rich text；由于 v2 才支持图片，本阶段应禁止或净化图片/外部资源粘贴，并接受 Qt 支持的 HTML 子集而非完整 HTML。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html][VERIFIED: Read .planning/REQUIREMENTS.md]

**Primary recommendation:** 使用 PySide6 官方 `QTextEdit` + `QTextCursor`/`QTextCharFormat`/`QTextBlockFormat`/`QTextListFormat` 实现格式化，新增独立富文本编辑组件，保持 `SNoteItem.content` 为 HTML 字符串并通过现有加密保存链路持久化。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html][VERIFIED: Read src/secnotepad/model/snote_item.py][VERIFIED: Read src/secnotepad/ui/main_window.py]

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EDIT-01 | 页面内容使用 QTextEdit 富文本编辑，内容以 HTML 格式存储。 | 现有 `_editor_preview` 已是 `QTextEdit`，`toHtml()` 已同步到 `note.content`；应将其正式封装为富文本编辑器。[VERIFIED: Read src/secnotepad/ui/main_window.py][VERIFIED: Read .planning/REQUIREMENTS.md] |
| EDIT-02 | 支持加粗、斜体、下划线、删除线。 | `QTextEdit`/`QTextCharFormat` 支持字体 weight、italic、underline，`QTextCharFormat` 支持 strike-out。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextCharFormat.html] |
| EDIT-03 | 支持字体选择和字号调整。 | 官方示例使用 `QFontComboBox` 和字号 `QComboBox` 放入工具栏，并将选择连接到文本格式槽。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFontComboBox.html] |
| EDIT-04 | 支持文字颜色和背景颜色。 | `QTextEdit` 提供文本颜色相关 API，`QTextCharFormat` 可设置前景/背景格式。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextCharFormat.html] |
| EDIT-05 | 支持左/中/右/两端对齐。 | `QTextEdit.setAlignment()` 可设置当前段落对齐；互斥对齐按钮应用 `QActionGroup` 管理。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QActionGroup.html] |
| EDIT-06 | 支持无序列表、有序列表和待办事项复选框。 | `QTextListFormat` 支持列表样式；官方富文本示例用 `QTextBlockFormat.MarkerType.Checked/Unchecked` 表达清单状态。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html][CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| EDIT-07 | 支持 H1-H6 标题样式。 | 官方富文本示例对当前 block 设置 `headingLevel` 并配合字符格式调整字号/粗细。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextBlockFormat.html] |
| EDIT-08 | 支持增加/减少缩进。 | `QTextBlockFormat` 与 `QTextListFormat` 均包含缩进相关设置；实现应作用于当前段落或当前列表。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextBlockFormat.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html] |
| EDIT-09 | 支持撤销和重做。 | `QTextEdit`/`QTextDocument` 支持 undo/redo，且 `QTextDocument` 提供 undo/redo 可用性信号。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html] |
| EDIT-10 | 支持剪切、复制、粘贴。 | 官方示例将标准 Cut/Copy/Paste `QAction` 连接到 `QTextEdit.cut/copy/paste`，并使用标准快捷键。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| EDIT-11 | 支持页面缩放。 | `QTextEdit` 提供 zoom in / zoom out 方法改变显示大小。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html] |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 富文本编辑 UI 与格式工具栏 | Browser / Client（桌面 Qt 客户端） | — | SecNotepad 是本地桌面 Qt 应用，格式操作由 `QTextEdit` 和 Qt action/toolbar 在客户端内完成。[VERIFIED: Read src/secnotepad/ui/main_window.py][CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| 当前页面 HTML 内容同步 | Browser / Client（桌面 Qt 客户端） | Database / Storage（加密文件保存时） | 编辑时更新内存中的 `SNoteItem.content`，保存时由既有 Serializer/FileService 加密写入 `.secnote`。[VERIFIED: Read src/secnotepad/ui/main_window.py][VERIFIED: Read src/secnotepad/model/serializer.py][VERIFIED: Read src/secnotepad/crypto/file_service.py] |
| 撤销/重做、剪切/复制/粘贴 | Browser / Client（桌面 Qt 客户端） | OS Clipboard | `QTextEdit` 提供 undo/redo/cut/copy/paste；粘贴数据来源是系统剪贴板 MIME 数据。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html] |
| HTML 持久化格式 | Database / Storage（加密 JSON 文件） | Browser / Client | `SNoteItem.content` 是 HTML 字符串字段，Serializer 将整棵树放入 JSON，FileService 再加密写入文件。[VERIFIED: Read src/secnotepad/model/snote_item.py][VERIFIED: Read src/secnotepad/model/serializer.py][VERIFIED: Read src/secnotepad/crypto/file_service.py] |
| 粘贴安全与外部资源限制 | Browser / Client（桌面 Qt 客户端） | Security | `QTextEdit` 默认可插入 HTML/rich text，v1 不支持图片；因此应在编辑器组件层限制图片和外部资源进入文档。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][VERIFIED: Read .planning/REQUIREMENTS.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | `>=3.12`（系统 Python 为 3.13.5） | 应用运行时。 | `pyproject.toml` 声明 `requires-python = ">=3.12"`，当前系统 `python3 --version` 返回 3.13.5。[VERIFIED: Read pyproject.toml][VERIFIED: Bash python3 --version] |
| PySide6 | 6.11.0（PyPI 可见最新） | Qt6 桌面 UI、`QTextEdit`、工具栏、Action、富文本格式对象。 | 项目依赖声明 `PySide6>=6.11.0`，PyPI 查询显示 6.11.0 可用，Qt 官方文档提供 `QTextEdit` 富文本示例。[VERIFIED: Read pyproject.toml][VERIFIED: pip index versions PySide6][CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| Qt QTextEdit / QTextDocument | 随 PySide6 6.11.0 | 富文本编辑、HTML 导入导出、撤销重做、剪贴板操作、缩放。 | `QTextEdit` 是 Qt 官方高级富文本编辑控件；官方示例直接以它实现富文本编辑器。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| `SNoteItem.content` | 内部数据模型字段 | 保存页面 HTML 内容。 | `SNoteItem` 定义 `content: str`，注释说明为 HTML 格式内容。[VERIFIED: Read src/secnotepad/model/snote_item.py] |
| Serializer + FileService | 内部模块 | 将 SNoteItem 树序列化为 JSON 并加密保存。 | `Serializer.to_json()` 将 root 放入 `version/data` JSON，`MainWindow._on_save()` 调用 `FileService.save()` 保存 JSON 字符串。[VERIFIED: Read src/secnotepad/model/serializer.py][VERIFIED: Read src/secnotepad/ui/main_window.py] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cryptography | 48.0.0（PyPI 可见最新） | 既有 `.secnote` 加密保存/打开链路。 | 本阶段不改加密算法，但富文本内容保存必须继续走现有 FileService。[VERIFIED: Read pyproject.toml][VERIFIED: pip index versions cryptography][VERIFIED: Read src/secnotepad/crypto/file_service.py] |
| pytest | 9.0.3（PyPI 可见最新） | 单元/集成测试运行器。 | 现有测试目录使用 pytest fixture 和断言风格。[VERIFIED: pip index versions pytest][VERIFIED: Read tests/conftest.py] |
| pytest-qt | 4.5.0（PyPI 可见最新） | Qt UI 测试辅助。 | 现有测试手写 `QApplication` fixture，若计划需要 `qtbot` 可引入；否则可继续不用新增依赖。[VERIFIED: pip index versions pytest-qt][VERIFIED: Read tests/conftest.py][ASSUMED] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `QTextEdit` | 自定义 HTML 编辑器 / WebEngine 编辑器 | 不符合 EDIT-01 指定的 `QTextEdit`，还会扩大依赖面和安全面。[VERIFIED: Read .planning/REQUIREMENTS.md][ASSUMED] |
| Qt 原生富文本格式对象 | 手写 HTML 字符串拼接 | 手写 HTML 容易破坏光标选择、撤销栈和 Qt 支持的 HTML 子集；应通过 `QTextCursor` 与 format 对象修改文档。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html][CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html] |
| 现有 `MainWindow` 继续内联所有格式代码 | `RichTextEditorWidget` / `RichTextEditorPanel` | 独立组件更容易测试和复用；内联实现更快但会继续放大 `MainWindow`。[VERIFIED: Read src/secnotepad/ui/main_window.py][ASSUMED] |
| 允许完整 HTML 粘贴 | 限制为 Qt 支持 HTML 子集并拒绝图片/外部资源 | 完整 HTML 不是 Qt 文档保证的持久格式；v1 图片明确推迟到 v2。[CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html][VERIFIED: Read .planning/REQUIREMENTS.md] |

**Installation:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e . pytest
# 如果采用 qtbot 测试：
.venv/bin/python -m pip install pytest-qt
```

**Version verification:** PyPI 查询显示 PySide6 6.11.0、cryptography 48.0.0、pytest 9.0.3、pytest-qt 4.5.0 可用；项目当前 `pyproject.toml` 已声明 PySide6 与 cryptography，但未声明 pytest/pytest-qt。[VERIFIED: pip index versions PySide6][VERIFIED: pip index versions cryptography][VERIFIED: pip index versions pytest][VERIFIED: pip index versions pytest-qt][VERIFIED: Read pyproject.toml]

## Architecture Patterns

### System Architecture Diagram

```text
用户选择页面
  ↓
QListView currentIndex
  ↓
PageListModel.note_at(index) ──无页面──→ placeholder
  ↓ 有页面
SNoteItem(note).content HTML
  ↓ setHtml()（blockSignals 防止加载即置脏）
RichTextEditorWidget / QTextEdit
  ↓ 用户输入或点击格式工具栏
QTextCursor + QTextCharFormat / QTextBlockFormat / QTextListFormat
  ↓ textChanged
QTextEdit.toHtml()
  ↓
SNoteItem(note).content 更新 + MainWindow.mark_dirty()
  ↓ 用户保存
Serializer.to_json(root)
  ↓
FileService.save/save_as 加密写入 .secnote
```

该数据流与当前 `_show_note_in_editor()`、`_on_editor_text_changed()`、`Serializer.to_json()` 和 `FileService.save()` 的调用关系一致，只是将格式工具栏和编辑器行为封装为富文本组件。[VERIFIED: Read src/secnotepad/ui/main_window.py][VERIFIED: Read src/secnotepad/model/serializer.py][VERIFIED: Read src/secnotepad/crypto/file_service.py][ASSUMED]

### Recommended Project Structure

```text
src/secnotepad/
├── ui/
│   ├── main_window.py              # 页面选择、文件保存、脏标志、菜单路由
│   ├── rich_text_editor.py         # 新增：QTextEdit + 格式工具栏 + 格式动作封装
│   └── ...
├── model/
│   ├── snote_item.py               # content 字段继续存 HTML
│   └── ...
└── crypto/
    └── file_service.py             # 不改：加密保存/打开

tests/
├── ui/
│   ├── test_rich_text_editor.py    # 新增：格式动作和 HTML 输出
│   ├── test_main_window.py         # 补充：菜单动作/页面切换/dirty 集成
│   └── test_navigation.py          # 保持现有导航回归
└── model/
    └── test_serializer.py          # 补充 HTML 内容 round-trip（如缺口存在）
```

新增 `rich_text_editor.py` 是架构建议，当前仓库尚不存在该文件。[VERIFIED: Bash find src/secnotepad][ASSUMED]

### Pattern 1: 用 `mergeCurrentCharFormat` / `QTextCursor.mergeCharFormat` 应用字符格式

**What:** 对当前选区或当前输入位置合并粗体、斜体、下划线、删除线、字体、字号、颜色等字符格式。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextCharFormat.html]

**When to use:** 所有 EDIT-02、EDIT-03、EDIT-04 字符级格式动作。[VERIFIED: Read .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html
fmt = QTextCharFormat()
fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
editor.mergeCurrentCharFormat(fmt)
```

### Pattern 2: 段落级格式用 `QTextBlockFormat`，列表用 `QTextListFormat`

**What:** 对齐、标题、缩进、待办 marker 是 block/list 层级格式，不应只改选中文本字符属性。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextBlockFormat.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html]

**When to use:** EDIT-05、EDIT-06、EDIT-07、EDIT-08。[VERIFIED: Read .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html
cursor = editor.textCursor()
cursor.beginEditBlock()
block_fmt = cursor.blockFormat()
block_fmt.setHeadingLevel(heading_level)  # 0 = normal, 1..6 = H1..H6
cursor.setBlockFormat(block_fmt)
cursor.endEditBlock()
```

### Pattern 3: 工具栏状态跟随光标，而不是只跟随按钮点击

**What:** 光标移动到已有富文本时，工具栏按钮、字体框、字号框、标题/列表状态应反映当前位置格式。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html]

**When to use:** 当连接 `currentCharFormatChanged`、`cursorPositionChanged`、`copyAvailable`、`undoAvailable`、`redoAvailable` 等信号更新 QAction 状态。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html]

**Example:**

```python
# Source: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html
editor.currentCharFormatChanged.connect(sync_char_toolbar)
editor.cursorPositionChanged.connect(sync_block_toolbar)
editor.document().undoAvailable.connect(action_undo.setEnabled)
editor.document().redoAvailable.connect(action_redo.setEnabled)
```

### Pattern 4: 加载页面 HTML 时阻断信号并清理 undo 栈

**What:** 页面切换时 `setHtml()` 不应把“加载旧内容”记录成用户编辑，也不应立即 `mark_dirty()`。[VERIFIED: Read src/secnotepad/ui/main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html]

**When to use:** `_show_note_in_editor(note)` 或新组件 `load_html(html)`。[VERIFIED: Read src/secnotepad/ui/main_window.py][ASSUMED]

**Example:**

```python
# Source: current code + QTextDocument docs
editor.blockSignals(True)
try:
    editor.setHtml(note.content or "")
    editor.document().setModified(False)
    editor.document().clearUndoRedoStacks()
finally:
    editor.blockSignals(False)
```

### Anti-Patterns to Avoid

- **把格式工具栏实现为字符串拼 HTML：** Qt 文档只保证支持 HTML 4 子集，`setHtml()` 后 `toHtml()` 可能返回等价但不同的标记；应使用 Qt 文档模型 API 修改内容。[CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html]
- **将外部图片/资源粘贴进 v1 笔记：** v2 才支持插入图片，v1 不应保存图片资源、远程 URL 或临时文件引用。[VERIFIED: Read .planning/REQUIREMENTS.md][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html]
- **页面切换时不保存当前页面编辑结果：** 当前实现依赖 `textChanged` 实时同步 `note.content`，计划中若重构编辑器必须保留该同步机制或在切页前显式 flush。[VERIFIED: Read src/secnotepad/ui/main_window.py]
- **重复连接按钮/信号：** Phase 3 已因重复初始化导航补了大量回归测试；Phase 04 的工具栏动作也必须避免每次打开/新建笔记本重复绑定。[VERIFIED: Read tests/ui/test_navigation.py][VERIFIED: Read src/secnotepad/ui/main_window.py]
- **让编辑菜单继续灰显：** 现有编辑菜单动作全部禁用；Phase 04 必须将撤销/重做/剪切/复制/粘贴动作连接到活动编辑器并按状态启用。[VERIFIED: Read src/secnotepad/ui/main_window.py][VERIFIED: Read .planning/REQUIREMENTS.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 富文本编辑文档模型 | 自定义 HTML/DOM 编辑器 | `QTextEdit` / `QTextDocument` | EDIT-01 指定 `QTextEdit`，Qt 已提供富文本文档、光标、撤销栈和 HTML 导入导出。[VERIFIED: Read .planning/REQUIREMENTS.md][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html] |
| 字符格式合并 | 手动包裹 `<b>/<i>/<span>` | `QTextCharFormat` + `mergeCurrentCharFormat` | 合并格式能保留其他属性并作用于选区/输入位置。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| 列表和待办项 | 手写 `<ul>/<ol>/<input>` | `QTextListFormat` + `QTextBlockFormat.MarkerType` | Qt 文档模型支持列表样式和 block marker；手写 HTML 输入控件不属于 QTextDocument 的可靠编辑模型。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html][CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] |
| 撤销/重做 | 自建操作栈 | `QTextEdit.undo/redo` + `QTextDocument.undoAvailable/redoAvailable` | Qt 文档自带撤销/重做栈和可用性信号。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html] |
| 剪贴板 | 自己读写系统剪贴板 | `QTextEdit.cut/copy/paste`，必要时覆写 MIME 插入策略 | QTextEdit 已处理文本/HTML/rich text；安全限制只需在 MIME 边界处理。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html] |
| 对齐互斥状态 | 手写按钮互斥逻辑 | `QActionGroup` | Qt 为对齐类互斥动作提供 QActionGroup。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QActionGroup.html] |

**Key insight:** 本领域最容易低估的是“光标状态 + 选区格式 + 段落格式 + 撤销栈 + HTML round-trip”的组合复杂度；用 Qt 文档模型是标准路径，手写 HTML 会绕开这些已解决的问题。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html][ASSUMED]

## Common Pitfalls

### Pitfall 1: `setHtml()` / `toHtml()` 不是字节级稳定的 HTML round-trip

**What goes wrong:** 测试若比较原始 HTML 字符串会失败，因为 Qt 可能输出语义等价但标记不同的 HTML。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html]

**Why it happens:** Qt 支持的是 `QTextDocument` 可渲染的 HTML 子集，而不是完整浏览器 HTML。[CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html]

**How to avoid:** 测试应断言 `toHtml()` 包含关键样式、`toPlainText()` 内容正确、或通过 `QTextCursor`/格式对象检查格式状态。[ASSUMED]

**Warning signs:** 测试写成 `assert editor.toHtml() == input_html`，或计划要求保持外部 HTML 原样。[ASSUMED]

### Pitfall 2: 页面加载触发 `textChanged` 导致打开文件后立即变脏

**What goes wrong:** 切换页面或打开笔记本时 `setHtml()` 触发内容变化，窗口标题出现 `*`，用户被提示保存未修改内容。[VERIFIED: Read src/secnotepad/ui/main_window.py][ASSUMED]

**Why it happens:** `QTextEdit.textChanged` 在程序性内容修改和用户编辑时都会触发。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html]

**How to avoid:** 加载 HTML 时继续使用 `blockSignals(True)`，并在加载后清理 document modified 与 undo/redo 栈。[VERIFIED: Read src/secnotepad/ui/main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html]

**Warning signs:** 打开现有 `.secnote` 后未编辑就出现 dirty 标记。[VERIFIED: Read src/secnotepad/ui/main_window.py]

### Pitfall 3: 格式按钮状态不同步当前光标

**What goes wrong:** 光标移动到粗体文本时“加粗”按钮仍未选中，或选择标题行后标题下拉框不更新。[ASSUMED]

**Why it happens:** 只在按钮点击时更新 QAction 状态，没有监听 `currentCharFormatChanged` 和 `cursorPositionChanged`。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html]

**How to avoid:** 连接 `currentCharFormatChanged` 更新字符工具栏，连接 `cursorPositionChanged` 更新段落/列表/对齐工具栏。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html]

**Warning signs:** 测试只覆盖“点按钮后 HTML 变化”，没有覆盖“移动光标后按钮状态”。[ASSUMED]

### Pitfall 4: 列表/标题/缩进误用字符格式实现

**What goes wrong:** 标题只变大变粗但不是 heading block，列表缩进无法嵌套，待办项不能切换状态。[ASSUMED]

**Why it happens:** 段落级结构被错误地实现为局部字符样式。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextBlockFormat.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html]

**How to avoid:** 标题/缩进/checkbox marker 使用 `QTextBlockFormat`，有序/无序列表使用 `QTextListFormat`。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html]

**Warning signs:** 实现中只出现 `QTextCharFormat`，没有 `QTextBlockFormat` 或 `QTextListFormat`。[ASSUMED]

### Pitfall 5: 粘贴富文本引入图片或外部资源

**What goes wrong:** 笔记 HTML 内出现本地临时图片路径、远程 URL 或 Qt image resource，破坏“所有内容随加密 JSON 保存”的简单模型。[ASSUMED]

**Why it happens:** `QTextEdit` 默认能插入 plain text、HTML、rich text；图片拖放/粘贴可通过 MIME 路径进入文档。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QClipboard.html]

**How to avoid:** 本阶段不实现图片粘贴；如需安全边界，子类化 `QTextEdit` 并覆盖 `canInsertFromMimeData` / `insertFromMimeData`，只允许文本与安全 HTML 子集。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][VERIFIED: Read .planning/REQUIREMENTS.md]

**Warning signs:** 保存后的 HTML 包含 `<img`、`src="file:`、`http://`、`https://` 或 Qt resource 引用。[ASSUMED]

### Pitfall 6: 重复初始化造成多次信号触发

**What goes wrong:** 每次新建/打开笔记本都会重复连接工具栏 action，点击一次加粗执行多次或 dirty 状态异常。[ASSUMED]

**Why it happens:** Phase 3 已出现类似风险并通过 `_teardown_navigation()` 和大量回归测试防止重复绑定。[VERIFIED: Read src/secnotepad/ui/main_window.py][VERIFIED: Read tests/ui/test_navigation.py]

**How to avoid:** 富文本编辑器组件只创建一次，或者在重新绑定前明确 disconnect；避免在 `_setup_navigation()` 每次调用中重复创建/连接全局格式动作。[ASSUMED]

**Warning signs:** 重复新建笔记本后同一按钮点击效果叠加，或测试需要“第二次新建后仍只触发一次”。[VERIFIED: Read tests/ui/test_navigation.py]

## Code Examples

### 字符格式：加粗/斜体/下划线/删除线

```python
# Source: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html
fmt = QTextCharFormat()
fmt.setFontItalic(checked)
fmt.setFontUnderline(checked)
fmt.setFontStrikeOut(checked)
editor.mergeCurrentCharFormat(fmt)
```

### 段落对齐：互斥 QActionGroup + QTextEdit.setAlignment

```python
# Source: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html
# Source: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QActionGroup.html
align_group = QActionGroup(self)
align_group.setExclusive(True)
act_center.setCheckable(True)
align_group.addAction(act_center)
act_center.triggered.connect(lambda: editor.setAlignment(Qt.AlignCenter))
```

### 列表/待办：QTextListFormat + QTextBlockFormat marker

```python
# Source: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html
cursor = editor.textCursor()
cursor.beginEditBlock()
block_fmt = cursor.blockFormat()
block_fmt.setMarker(QTextBlockFormat.MarkerType.Unchecked)
cursor.setBlockFormat(block_fmt)
list_fmt = QTextListFormat()
list_fmt.setStyle(QTextListFormat.Style.ListDisc)
cursor.createList(list_fmt)
cursor.endEditBlock()
```

### 页面加载：避免加载即置脏

```python
# Source: existing MainWindow pattern + QTextDocument docs
editor.blockSignals(True)
try:
    editor.setHtml(note.content or "")
    editor.document().setModified(False)
    editor.document().clearUndoRedoStacks()
finally:
    editor.blockSignals(False)
```

### 编辑同步：保存 HTML 到当前 note

```python
# Source: src/secnotepad/ui/main_window.py
html = editor.toHtml()
if note.content != html:
    note.content = html
    main_window.mark_dirty()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手写 HTML 字符串拼接格式 | Qt 文档模型：`QTextCursor` + format objects | Qt 官方示例当前采用该模式；本会话通过 Context7/官方文档验证。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html] | 计划应围绕光标、block/list/char format 和信号同步拆任务。[ASSUMED] |
| 将所有 UI 逻辑放入 `MainWindow` | 抽出富文本编辑组件，`MainWindow` 负责集成 | 本项目已有 `MainWindow` 集中大量导航/文件逻辑，当前阶段适合拆分新组件。[VERIFIED: Read src/secnotepad/ui/main_window.py][ASSUMED] | 降低后续 Phase 5 标签/搜索和 Phase 6 美化时的耦合风险。[ASSUMED] |
| 认为 HTML 是浏览器级完整格式 | 接受 Qt 支持的 HTML 子集 | Qt 官方文档明确 `QTextDocument`/`QTextEdit` 支持 HTML 4 子集。[CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html] | 测试和数据兼容策略不得依赖完整 HTML 保真。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html] |

**Deprecated/outdated:**

- 本研究未发现 PySide6 6.11.0 中 `QTextEdit` 富文本 API 对本阶段需求的弃用信息；仍需执行阶段中以实际安装版本运行测试确认。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][ASSUMED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 建议抽出 `RichTextEditorWidget`，而不是继续把全部格式逻辑放进 `MainWindow`。 | Summary / Standard Stack / Architecture Patterns | 若团队偏好单文件快速实现，计划会多一个组件拆分任务；但不影响功能可行性。 |
| A2 | pytest-qt 可选；可继续沿用现有手写 `QApplication` fixture 做 UI 测试。 | Standard Stack | 若测试需要 `qtbot`，计划需添加测试依赖安装步骤。 |
| A3 | 测试应以渲染语义/关键格式断言为主，而非逐字比较 HTML。 | Common Pitfalls | 若 Qt 输出恰好稳定，测试仍可通过；若逐字比较则容易出现脆弱测试。 |
| A4 | 禁止图片/外部资源粘贴应通过 QTextEdit MIME 边界实现。 | Common Pitfalls / Security Domain | 若 Qt 默认不会在当前平台插入图片，额外子类化可能不是必需；但安全边界更清晰。 |
| A5 | `MainWindow` 当前体量已经适合拆分富文本组件。 | State of the Art | 若执行者继续内联实现，短期更快但维护风险更高。 |

## Open Questions (RESOLVED)

1. **格式工具栏是否作为独立 `QToolBar` 还是编辑区内局部 toolbar？**
   - RESOLVED: 采用右侧编辑区内的局部 toolbar。该 toolbar 固定在右侧编辑区上方，作为 `RichTextEditorWidget` / 编辑区容器的一部分，不使用 `QMainWindow.addToolBar()` 加入全局主工具栏；文件操作工具栏与文本格式工具栏保持分离（D-65）。
   - Planning implication: 计划 04-02 创建 `RichTextEditorWidget.format_toolbar()` 和 `_format_toolbar`，计划 04-05 将其嵌入 MainWindow 右侧编辑区内部，并用测试 `test_format_toolbar_is_inside_editor_area` 防止格式按钮进入主工具栏。

2. **待办事项复选框是否必须可鼠标点击切换？**
   - RESOLVED: D-73/D-75 锁定为轻量“☐ ”可编辑文本符号方案，不实现 HTML checkbox、鼠标点击复选框交互或完成状态切换。[VERIFIED: Read .planning/phases/04-rich-text-editor/04-CONTEXT.md]
   - Planning implication: EDIT-06 的待办按钮插入/应用普通文本“☐ ”列表行，并用 HTML/plain text 回归测试验证该符号保存；不得规划 `QTextBlockFormat.MarkerType.Checked/Unchecked` 或 `<input type="checkbox">` 作为 Phase 4 实现。

3. **粘贴 HTML 是否需要净化样式白名单？**
   - RESOLVED: 粘贴 HTML 必须走安全净化。允许纯文本与 Qt 支持的基础富文本 HTML 子集，包括文本和基础内联/段落格式；必须阻断 image/external resource、`script`、event handler 等不安全内容，不得持久化 `<img>`、`file:`、`http:`、`https:` 或任何外部资源引用。
   - Planning implication: 计划 04-01 先写 `test_clipboard_actions_and_safe_paste` RED 测试，计划 04-04 在 `SafeRichTextEdit.insertFromMimeData` 边界实现净化，保存 HTML 不含图片、外部资源、脚本或事件处理器；粘贴被净化时通过状态栏提示 `已粘贴文本内容；图片和外部资源未导入`。

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | 运行应用与测试 | ✓ | 3.13.5 | 项目要求 Python >=3.12，系统版本满足；仍应优先创建 `.venv`。[VERIFIED: Bash python3 --version][VERIFIED: Read pyproject.toml] |
| pip | 安装依赖 | ✓ | 25.1.1 | 使用 `python3 -m pip` 或 `.venv/bin/python -m pip`。[VERIFIED: Bash pip3 --version] |
| 项目 `.venv` | 按用户记忆运行 Python 测试/脚本 | ✗ | — | 创建 `.venv` 后安装依赖；不要用系统 Python 跑测试。[VERIFIED: Bash test .venv missing][VERIFIED: user memory] |
| PySide6 | 应用 UI 和富文本编辑器 | ✗（当前 Python 环境未安装） | PyPI 可用 6.11.0 | 在 `.venv` 中 `pip install -e .`。[VERIFIED: Bash importlib check][VERIFIED: pip index versions PySide6] |
| pytest | 测试运行 | ✗（当前 Python 环境未安装） | PyPI 可用 9.0.3 | 在 `.venv` 中安装 pytest。[VERIFIED: Bash importlib check][VERIFIED: pip index versions pytest] |
| pytest-qt | 可选 UI 测试辅助 | ✗（当前 Python 环境未安装） | PyPI 可用 4.5.0 | 可继续使用现有 `qapp` fixture；如使用 `qtbot` 则安装。[VERIFIED: Bash importlib check][VERIFIED: pip index versions pytest-qt][VERIFIED: Read tests/conftest.py][ASSUMED] |
| cryptography | 现有加密保存/打开 | ✗（当前 Python 环境未安装） | PyPI 可用 48.0.0 | 在 `.venv` 中 `pip install -e .`。[VERIFIED: Bash importlib check][VERIFIED: pip index versions cryptography][VERIFIED: Read pyproject.toml] |

**Missing dependencies with no fallback:**

- 项目 `.venv` 与运行依赖当前不存在；执行阶段必须先创建虚拟环境并安装项目依赖，否则应用和测试无法导入 PySide6/cryptography。[VERIFIED: Bash test .venv missing][VERIFIED: Bash importlib check]

**Missing dependencies with fallback:**

- pytest-qt 缺失但可选；若计划不使用 `qtbot`，可沿用现有 `tests/conftest.py` 的 `qapp` fixture。[VERIFIED: Read tests/conftest.py][ASSUMED]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest；当前环境未安装，PyPI 可用 9.0.3。[VERIFIED: Read pyproject.toml][VERIFIED: pip index versions pytest][VERIFIED: Bash importlib check] |
| Config file | `pyproject.toml` 中 `[tool.pytest.ini_options] testpaths = ["tests"]`。[VERIFIED: Read pyproject.toml] |
| Quick run command | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py -q`。[ASSUMED] |
| Full suite command | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`。[ASSUMED] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EDIT-01 | 选中页面后 QTextEdit 可编辑，编辑后 HTML 写回 `SNoteItem.content` 并置脏。 | integration | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_editing_page_updates_note_html_and_dirty -q` | ❌ Wave 0 |
| EDIT-02 | 加粗/斜体/下划线/删除线 action 改变当前选区格式。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_character_format_actions -q` | ❌ Wave 0 |
| EDIT-03 | 字体和字号控件应用到选区并随光标状态同步。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_font_family_and_size_controls -q` | ❌ Wave 0 |
| EDIT-04 | 前景色/背景色 action 应用到选区。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_text_and_background_color_actions -q` | ❌ Wave 0 |
| EDIT-05 | 左/中/右/两端对齐作用于当前段落且 QActionGroup 互斥。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_alignment_actions_are_exclusive -q` | ❌ Wave 0 |
| EDIT-06 | 无序/有序/待办列表可创建，待办状态可切换。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_list_and_checklist_actions -q` | ❌ Wave 0 |
| EDIT-07 | H1-H6 标题样式设置当前 block heading level。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_heading_levels -q` | ❌ Wave 0 |
| EDIT-08 | 增加/减少缩进改变当前 block/list 缩进。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_indent_outdent_actions -q` | ❌ Wave 0 |
| EDIT-09 | undo/redo action 连接 QTextEdit，状态随 document signals 更新。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_undo_redo_actions -q` | ❌ Wave 0 |
| EDIT-10 | cut/copy/paste action 连接 QTextEdit；粘贴不引入图片/外部资源。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_clipboard_actions_and_safe_paste -q` | ❌ Wave 0 |
| EDIT-11 | zoom in/out 改变显示缩放且不修改 `note.content`。 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_zoom_does_not_mark_content_dirty -q` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py -q`。[ASSUMED]
- **Per wave merge:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py tests/ui/test_main_window.py tests/ui/test_navigation.py -q`。[ASSUMED]
- **Phase gate:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` 全套通过后再进入 `/gsd-verify-work`。[ASSUMED]

### Wave 0 Gaps

- [ ] `tests/ui/test_rich_text_editor.py` — 覆盖 EDIT-01~EDIT-11 的富文本组件行为。[VERIFIED: Bash find tests]
- [ ] `tests/ui/test_main_window.py` — 补充编辑菜单启用、格式工具栏位置、页面切换不误置脏。[VERIFIED: Read tests/ui/test_main_window.py][ASSUMED]
- [ ] `tests/model/test_serializer.py` — 如现有测试未覆盖 HTML 内容 round-trip，应补充含中文与富文本 HTML 的序列化回归。[VERIFIED: Read tests/model/test_serializer.py][ASSUMED]
- [ ] 环境准备：创建 `.venv` 并安装项目依赖与 pytest；当前 `.venv` 不存在。[VERIFIED: Bash test .venv missing]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | 本阶段不新增认证；本地密钥打开/保存已在 Phase 2 实现。[VERIFIED: Read .planning/ROADMAP.md][VERIFIED: Read src/secnotepad/ui/main_window.py] |
| V3 Session Management | no | 本阶段无网络会话；只需保持关闭时清理 `_current_password` 的既有模式不被破坏。[VERIFIED: Read src/secnotepad/ui/main_window.py] |
| V4 Access Control | no | 单用户本地应用，不新增角色/权限模型。[VERIFIED: Read .planning/REQUIREMENTS.md] |
| V5 Input Validation | yes | 粘贴 HTML/MIME 输入应限制为 Qt 可处理文本/HTML，拒绝图片和外部资源。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][VERIFIED: Read .planning/REQUIREMENTS.md][ASSUMED] |
| V6 Cryptography | yes | 富文本 HTML 必须继续通过现有 Serializer + FileService 加密保存，不新增明文缓存或自定义加密。[VERIFIED: Read src/secnotepad/model/serializer.py][VERIFIED: Read src/secnotepad/crypto/file_service.py] |
| V12 File and Resources | yes | 不保存未加密临时文件，不嵌入本地/远程资源路径；v1 图片插入不在范围内。[VERIFIED: Read .planning/REQUIREMENTS.md][ASSUMED] |

### Known Threat Patterns for PySide6 local rich text editor

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| HTML/剪贴板输入污染笔记内容 | Tampering | 在 QTextEdit MIME 插入边界拒绝图片和外部资源，测试保存 HTML 不含 `<img`、`file:`、`http:` 资源。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][ASSUMED] |
| 明文内容落入临时文件或外部资源引用 | Information Disclosure | 不生成明文临时 HTML 文件，不把粘贴图片保存到未加密路径；只保存加密 `.secnote`。[VERIFIED: Read src/secnotepad/crypto/file_service.py][ASSUMED] |
| 加载页面触发 dirty 导致用户误保存 | Integrity / Reliability | `setHtml()` 时 block signals，加载后清理 modified/undo 栈，测试打开/切页不置脏。[VERIFIED: Read src/secnotepad/ui/main_window.py][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html] |
| 撤销栈跨页面保留旧页面明文片段 | Information Disclosure | 页面切换加载新 HTML 后清理 `QTextDocument` undo/redo stacks。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html][ASSUMED] |

## Sources

### Primary (HIGH confidence)

- `/websites/doc_qt_io_qtforpython-6` — Context7 查询了 `QTextEdit`、官方 richtext TextEdit 示例、`QTextCharFormat`、`QTextBlockFormat`、`QTextListFormat`、`QTextDocument`、`QFontComboBox`、`QActionGroup` 相关主题。[VERIFIED: Context7 CLI]
- https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html — QTextEdit HTML、富文本、剪贴板、撤销/重做、缩放与信号能力。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html]
- https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html — Qt 官方富文本 TextEdit 示例：工具栏、格式动作、列表/待办、标题、状态同步。[CITED: https://doc.qt.io/qtforpython-6/examples/example_widgets_richtext_textedit.html]
- https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html — Qt 支持 HTML 子集，非完整浏览器 HTML。[CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html]
- https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html — 文档 modified、undo/redo stacks 与相关 signals。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextDocument.html]
- https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextBlockFormat.html — 段落/block 格式、heading/marker/indent 相关 API。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextBlockFormat.html]
- https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html — 列表格式和列表样式。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QTextListFormat.html]
- https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFontComboBox.html — 系统字体选择控件。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QFontComboBox.html]
- https://doc.qt.io/qtforpython-6/PySide6/QtGui/QActionGroup.html — 互斥 action group。[CITED: https://doc.qt.io/qtforpython-6/PySide6/QtGui/QActionGroup.html]
- 本仓库文件：`pyproject.toml`、`src/secnotepad/ui/main_window.py`、`src/secnotepad/model/snote_item.py`、`src/secnotepad/model/serializer.py`、`src/secnotepad/crypto/file_service.py`、`tests/conftest.py`、`tests/ui/test_main_window.py`、`tests/ui/test_navigation.py`。[VERIFIED: Read/Bash]

### Secondary (MEDIUM confidence)

- PyPI index 查询：PySide6 6.11.0、cryptography 48.0.0、pytest 9.0.3、pytest-qt 4.5.0。[VERIFIED: pip index versions]

### Tertiary (LOW confidence)

- 组件拆分、测试断言风格、粘贴净化实现范围属于本研究建议，已在 Assumptions Log 标记。[ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — 项目依赖、PyPI 可用版本和 Qt 官方文档均已验证。[VERIFIED: Read pyproject.toml][VERIFIED: pip index versions][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html]
- Architecture: MEDIUM-HIGH — 现有代码集成点已验证；抽出 `RichTextEditorWidget` 是研究建议而非用户锁定决策。[VERIFIED: Read src/secnotepad/ui/main_window.py][ASSUMED]
- Pitfalls: MEDIUM-HIGH — Qt HTML 子集、信号、undo/redo、MIME 行为有官方来源；具体平台粘贴行为需执行阶段测试确认。[CITED: https://doc.qt.io/qtforpython-6/overviews/qtgui-richtext-html-subset.html][CITED: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QTextEdit.html][ASSUMED]
- Security: MEDIUM — 现有加密链路已验证；HTML 粘贴净化策略需实现与测试验证。[VERIFIED: Read src/secnotepad/crypto/file_service.py][ASSUMED]

**Research date:** 2026-05-09  
**Valid until:** 2026-06-08（Qt/PySide6 API 相对稳定；PyPI 最新版本需在执行前再次查询）[ASSUMED]
