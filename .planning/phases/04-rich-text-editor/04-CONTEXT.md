# Phase 04: 富文本编辑器 - Context

**Gathered:** 2026-05-09
**Status:** Ready for planning

<domain>
## Phase Boundary

实现右侧页面编辑区的完整 QTextEdit 富文本编辑能力：页面内容以 HTML 存储并同步到当前 SNoteItem；编辑区上方提供格式工具栏；支持字体、字号、加粗、斜体、下划线、删除线、文字颜色、背景色、段落对齐、H1-H6 标题、无序/有序/待办列表、缩进、撤销/重做、剪切/复制/粘贴和会话级缩放。Phase 4 不新增图片、表格、Markdown、云同步或高级待办交互。

</domain>

<decisions>
## Implementation Decisions

### 格式工具栏
- **D-65:** 格式工具栏固定放在右侧编辑区上方；未选中页面时整体禁用，选中页面后可用。不要把格式按钮混入现有主工具栏，文件操作工具栏和文本格式工具栏保持分离。
- **D-66:** 格式动作状态必须跟随光标当前位置更新。连接 QTextEdit 的 `currentCharFormatChanged` / `cursorPositionChanged` 等信号，使加粗、斜体、下划线、删除线、字体、字号、颜色、对齐、标题等控件反映当前光标或选区状态。
- **D-67:** 文字颜色和背景色使用系统 `QColorDialog`。分别提供文字颜色与背景色按钮，点击后打开原生颜色选择对话框并应用到选区/后续输入。
- **D-68:** 字体和字号控件使用 Qt 原生控件：`QFontComboBox` 提供系统字体列表，字号使用常用字号下拉。无需支持任意自由输入字号。

### 标题与段落
- **D-69:** H1-H6 标题优先使用 `QTextBlockFormat.headingLevel` / 标题块语义实现，使保存的 HTML 尽量接近语义化标题结构；不要仅用字号和加粗模拟标题。
- **D-70:** 标题控件采用“段落样式”下拉框，包含“正文、H1、H2、H3、H4、H5、H6”。不要在工具栏铺开 6 个标题按钮。
- **D-71:** 段落对齐提供四个互斥按钮：左对齐、居中、右对齐、两端对齐。按钮应为 checkable QAction，并随当前段落同步选中状态。
- **D-72:** 标题、对齐、列表、缩进等段落格式作用于当前光标所在段落，或选区覆盖的所有段落。不要只作用于后续输入。

### 待办列表与缩进
- **D-73:** 待办事项列表采用轻量符号方案：插入类似“☐ ”的可编辑文本行，并作为普通 HTML 文本保存。不要在 Phase 4 中实现 HTML checkbox 或鼠标点击复选框交互。
- **D-74:** 无序列表、有序列表、待办列表使用三个独立按钮。待办按钮负责插入/应用待办符号列表；无序/有序列表使用 QTextEdit/QTextCursor 标准列表能力。
- **D-75:** Phase 4 不需要提供待办完成状态切换。用户可手动编辑“☐”字符；不要新增点击切换或快捷键切换“☐/☑”的交互。
- **D-76:** 增加/减少缩进使用 QTextEdit/QTextCursor/QTextList 的标准能力；列表嵌套效果以 Qt 原生表现为准，不要求自定义严格多级列表引擎。

### 缩放行为
- **D-77:** EDIT-11 的缩放是会话级编辑器显示偏好，不写入页面 HTML、不写入 `.secnote` 文件，也不新增 SNoteItem 字段。
- **D-78:** 缩放入口放在“视图”菜单并提供快捷键：放大、缩小、重置。建议使用桌面常见快捷键 Ctrl+Plus、Ctrl+Minus、Ctrl+0。
- **D-79:** 同一编辑会话中切换页面时保持当前编辑器缩放，直到用户重置或关闭应用。不要每次切页自动回到 100%。
- **D-80:** 执行放大、缩小或重置时，在状态栏短暂提示当前缩放百分比；不需要在 Phase 4 中增加常驻百分比显示控件。

### Claude's Discretion
无。所有本次讨论的灰区均由用户选择了明确方向。

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 需求与项目
- `.planning/ROADMAP.md` — Phase 4 目标、EDIT-01~11 需求映射和 5 条成功标准。
- `.planning/REQUIREMENTS.md` — EDIT-01~11 的完整需求定义，尤其 EDIT-06 待办列表、EDIT-07 标题、EDIT-11 缩放。
- `.planning/PROJECT.md` — 技术栈约束（Python 3 + PySide6 + Qt6）、QTextEdit 原生方案、不使用 QWebEngine、排除 Markdown/图片/表格等范围。

### 前置 Phase Context
- `.planning/phases/03-navigation-system/03-CONTEXT.md` — D-62/D-63/D-64 定义页面列表与右侧 QTextEdit 的联动；Phase 4 应在同一编辑器基础上完善格式工具栏和编辑能力。
- `.planning/phases/02-file-operations-and-encryption/02-CONTEXT.md` — D-45/D-47 定义 `mark_dirty()` / `mark_clean()` 和“新建不脏，实际编辑后才脏”的规则；Phase 4 文本变化必须沿用。

### 现有代码集成点
- `src/secnotepad/ui/main_window.py` — `MainWindow._editor_preview` 已是可编辑 `QTextEdit`，`textChanged` 已同步 `note.content = toHtml()` 并调用 `mark_dirty()`；Phase 4 主要新增格式工具栏、格式动作、编辑菜单动作和缩放行为。
- `src/secnotepad/model/snote_item.py` — `SNoteItem.content` 是 HTML 字符串字段；Phase 4 不应新增缩放字段。
- `tests/ui/test_navigation.py` — 已覆盖编辑器可编辑、页面选择和 HTML 同步的部分行为；Phase 4 应扩展 UI 测试覆盖格式动作。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MainWindow._editor_preview`: 现有 QTextEdit 实例，已放在右侧 `QStackedWidget` 中，已通过 `setHtml()` / `toHtml()` 与当前页面内容联动。
- `MainWindow._on_editor_text_changed()`: 已处理文本变化同步与 dirty 标记，可作为格式动作触发内容变化后的持久化基础。
- `MainWindow._edit_actions`: 编辑菜单当前有撤销、重做、剪切、复制、粘贴 QAction 但处于灰显，Phase 4 可以连接到 QTextEdit 标准槽并按页面选择状态启用。
- `MainWindow.statusBar()`: 现有状态栏用于操作反馈，缩放百分比提示应复用这个模式。

### Established Patterns
- 信号驱动架构：现有导航通过 Qt selectionChanged/currentChanged 信号更新页面列表和编辑区；格式工具栏状态同步也应使用 QTextEdit 信号驱动。
- 数据与视图分离：SNoteItem 只保存内容 HTML；编辑器显示状态（如缩放）不进入数据模型。
- 导航初始化幂等：`_setup_navigation()` 会重复初始化并调用 `_teardown_navigation()`；新增格式工具栏信号连接需避免重复绑定。

### Integration Points
- `_setup_editor_area()` 当前只创建 QTextEdit 和 placeholder；Phase 4 需要将右侧区域调整为“格式工具栏 + editor stack”的容器。
- `_show_note_in_editor()` / `_show_editor_placeholder()` 需要同步启用/禁用格式工具栏，并避免 `setHtml()` 触发 dirty。
- `_setup_menu_bar()` 中编辑菜单动作当前灰显；Phase 4 需要连接撤销/重做/剪切/复制/粘贴，并按当前页面/编辑器状态更新可用性。
- `_setup_tool_bar()` 是文件工具栏，不应承载格式动作；格式工具栏应在编辑区内部创建。

</code_context>

<specifics>
## Specific Ideas

- 格式工具栏应像传统桌面富文本编辑器：右侧编辑区上方固定显示，未选择页面时禁用，选择页面后启用并跟随光标状态。
- 待办列表刻意选择轻量文本符号方案，避免把 Phase 4 扩展为完整任务管理/复选框交互功能。
- 缩放是阅读/编辑显示偏好，不属于笔记内容；因此不进入加密文件或页面模型。

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-rich-text-editor*
*Context gathered: 2026-05-09*
