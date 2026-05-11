---
phase: 04
slug: rich-text-editor
status: draft
shadcn_initialized: false
preset: none
created: 2026-05-09
---

# Phase 04 — UI Design Contract

> 富文本编辑器阶段的视觉与交互契约。由 gsd-ui-researcher 生成，供 gsd-ui-checker、planner、executor 和 auditor 使用。

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none（不使用 shadcn；本项目是 PySide6 / Qt Widgets 桌面应用） |
| Preset | not applicable |
| Component library | PySide6 Qt Widgets：`QTextEdit`、`QToolBar` 或编辑区内局部工具栏、`QAction`、`QActionGroup`、`QFontComboBox`、`QComboBox`、`QColorDialog`、`QMessageBox` |
| Icon library | Qt `QStyle.standardIcon()` 优先；若 Qt 无语义匹配图标，使用清晰中文文字按钮或短标签，不引入第三方图标库 |
| Font | 系统 UI 默认字体；编辑器正文默认使用系统字体，内容字体可由 `QFontComboBox` 改写到 HTML |

**来源说明：** 技术栈来自 `04-RESEARCH.md` 与 `pyproject.toml`；现有 UI 模式来自 `src/secnotepad/ui/main_window.py`、`welcome_widget.py`、`password_dialog.py`。shadcn gate 已执行：项目不是 React/Next.js/Vite，`components.json` 不适用，因此不初始化 shadcn。

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | 工具栏内图标/按钮间距、颜色按钮内部留白、紧凑控件间隔 |
| sm | 8px | 格式工具栏分组间距、按钮组与下拉框间距、编辑区 placeholder 周边留白 |
| md | 16px | 编辑器容器默认内边距、工具栏与正文编辑区之间的垂直间距 |
| lg | 24px | 右侧编辑区空状态内容块与边缘的最小间距 |
| xl | 32px | 大块区域分隔；工具栏需要换行时的行间视觉留白上限 |
| 2xl | 48px | 右侧编辑区空状态在较大窗口中的主要垂直间隔 |
| 3xl | 64px | 页面级空白，不用于常规工具栏 |

Exceptions: 
- 新增 Phase 04 UI 不再扩散现有左/中导航按钮栏的 2px spacing；右侧富文本编辑区新增布局必须使用上表 4px 倍数。
- 工具栏可点击控件最小高度 32px；颜色按钮/图标按钮最小宽高 32px。
- 字体下拉框最小宽度 160px，字号下拉框最小宽度 72px，段落样式下拉框最小宽度 96px。

---

## Typography

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body | 14px | 400 | 1.5 |
| Label | 12px | 400 | 1.4 |
| Heading | 18px | 600 | 1.2 |
| Display | 24px | 600 | 1.2 |

**字体契约：**
- 全局 UI 只使用两种字重：400 regular 与 600 semibold/bold。不要新增 light、medium、heavy 等额外权重。
- 编辑器正文默认字号为 14px；用户通过字号下拉选择时，写入文档 HTML 的字号可不同于 UI 默认字号。
- 标题样式 H1-H6 使用 `QTextBlockFormat.headingLevel` 的段落语义为主，不得只用字号和加粗模拟标题。
- H1-H6 在编辑器内的视觉层级由 Qt 文档模型输出为准；工具栏中的“段落样式”下拉显示文本固定为：`正文`、`H1`、`H2`、`H3`、`H4`、`H5`、`H6`。

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | 系统窗口背景色 / Qt palette Window | 主窗口背景、右侧编辑区外层背景、空状态背景 |
| Secondary (30%) | 系统 Base / AlternateBase | QTextEdit 编辑面、分区树、页面列表、工具栏背景 |
| Accent (10%) | 系统 Highlight 色 | 当前选中文本、当前页面/分区选择态、checkable 格式按钮选中态、焦点边框、主操作反馈 |
| Destructive | #d32f2f | 删除、丢弃更改、错误提示、密码错误、危险确认按钮/文案 |

Accent reserved for: 
- 当前页面/分区选中态；
- `QTextEdit` 文本选区；
- 加粗、斜体、下划线、删除线、对齐、列表等 checkable QAction 的选中态；
- 当前聚焦输入控件/编辑器的焦点提示；
- 状态栏成功/信息提示不使用 accent 强刷背景，只使用文字消息。

**颜色约束：**
- Phase 04 不引入完整 QSS 主题；现代化全局视觉属于 Phase 06。
- 格式工具栏的文字颜色与背景色按钮应展示当前颜色的小色块；色块颜色来自当前 `QTextCharFormat`，没有显式颜色时回退 Qt palette 文本/背景色。
- 文字颜色与背景色的用户选择由系统 `QColorDialog` 完成；不要自制调色板。
- 错误/危险语义只使用 Destructive，不能用 accent 表达删除或丢弃。

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | 选择页面 |
| Empty state heading | 请在页面列表中选择一个页面 |
| Empty state body | 选择页面后即可编辑富文本内容。没有页面时，请先在当前分区中新建页面。 |
| Error state | 无法应用格式。请先选择页面并将光标放入编辑区后重试。 |
| Destructive confirmation | 本阶段不新增删除类破坏性操作；沿用现有删除分区、丢弃未保存更改确认。富文本编辑相关操作（格式化、撤销/重做、剪切/粘贴、缩放）不弹破坏性确认。 |

**状态栏文案：**
- 放大：`缩放：{percent}%`
- 缩小：`缩放：{percent}%`
- 重置缩放：`缩放：100%`
- 应用文字颜色：`已设置文字颜色`
- 应用背景色：`已设置背景色`
- 应用待办列表：`已插入待办项`
- 粘贴内容被净化时：`已粘贴文本内容；图片和外部资源未导入`

**工具栏可见文案 / Tooltip：**
- 字体下拉：`字体`
- 字号下拉：`字号`
- 段落样式下拉：`段落样式`
- 字符格式：`加粗`、`斜体`、`下划线`、`删除线`
- 颜色：`文字颜色`、`背景色`
- 对齐：`左对齐`、`居中`、`右对齐`、`两端对齐`
- 列表：`无序列表`、`有序列表`、`待办列表`
- 缩进：`减少缩进`、`增加缩进`
- 编辑菜单：`撤销`、`重做`、`剪切`、`复制`、`粘贴`
- 视图菜单：`放大`、`缩小`、`重置缩放`

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | 不适用 — PySide6/Qt Widgets 桌面应用，未初始化 shadcn — 2026-05-09 |
| third-party registries | none | 不适用 — 未声明第三方 registry 或 block — 2026-05-09 |

---

## Phase-Specific Interaction Contract

### 编辑区结构

| Area | Contract |
|------|----------|
| 位置 | 富文本格式工具栏固定在右侧编辑区上方，不进入主窗口文件工具栏。 |
| 启用状态 | 未选中页面时，格式工具栏整体禁用并显示空状态；选中页面后工具栏与 `QTextEdit` 可用。 |
| 编辑器 | 使用现有 `QTextEdit` 能力或等价封装组件；内容以 `toHtml()` 同步到当前 `SNoteItem.content`。 |
| 空状态 | 保持居中提示：`请在页面列表中选择一个页面`，补充说明由 tooltip/status bar 承载，不新增复杂空状态卡片。 |
| 布局 | 右侧区域为垂直结构：格式工具栏在上，编辑器/placeholder stack 在下；工具栏不可浮动。 |

### 格式工具栏分组顺序

1. 段落样式下拉：`正文`、`H1`、`H2`、`H3`、`H4`、`H5`、`H6`
2. 字体下拉：系统字体列表（`QFontComboBox`）
3. 字号下拉：常用字号，固定选项 `8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48`
4. 字符格式按钮：加粗、斜体、下划线、删除线
5. 颜色按钮：文字颜色、背景色
6. 段落对齐按钮：左对齐、居中、右对齐、两端对齐，互斥选中
7. 列表按钮：无序列表、有序列表、待办列表
8. 缩进按钮：减少缩进、增加缩进

### 状态同步

| Trigger | Required UI Response |
|---------|----------------------|
| 页面被选中 | 加载 HTML，显示编辑器，启用工具栏，清理文档 modified 状态与 undo/redo 栈，不能立刻置脏。 |
| 页面取消选择或切换分区 | 显示 placeholder，禁用格式工具栏，清空编辑器显示时不能触发 dirty。 |
| 光标移动 | 字体、字号、字符格式、颜色、对齐、段落样式状态必须跟随当前位置更新。 |
| 选择文本 | 可应用字符格式；复制/剪切 action 按 `copyAvailable` 状态启用。 |
| 文本或格式变化 | 当前页面 HTML 更新到 `SNoteItem.content`，调用既有 `mark_dirty()`。 |
| 撤销/重做状态变化 | 编辑菜单对应 action 启用状态随 `QTextDocument.undoAvailable/redoAvailable` 更新。 |
| 缩放变化 | 只改变当前会话显示，不写入页面 HTML、不置脏、不新增模型字段。 |

### 快捷键与菜单

| Action | Shortcut | Location | Contract |
|--------|----------|----------|----------|
| 撤销 | Ctrl+Z | 编辑菜单 | 连接到活动 `QTextEdit.undo()`；无页面或不可撤销时禁用。 |
| 重做 | Ctrl+Y 或 Ctrl+Shift+Z | 编辑菜单 | 连接到活动 `QTextEdit.redo()`；无页面或不可重做时禁用。 |
| 剪切 | Ctrl+X | 编辑菜单 | 连接到活动 `QTextEdit.cut()`；无选区时禁用。 |
| 复制 | Ctrl+C | 编辑菜单 | 连接到活动 `QTextEdit.copy()`；无选区时禁用。 |
| 粘贴 | Ctrl+V | 编辑菜单 | 连接到安全粘贴逻辑；有页面且剪贴板含可插入文本/HTML 时启用。 |
| 放大 | Ctrl+Plus | 视图菜单 | 会话级缩放，状态栏显示百分比。 |
| 缩小 | Ctrl+Minus | 视图菜单 | 会话级缩放，状态栏显示百分比。 |
| 重置缩放 | Ctrl+0 | 视图菜单 | 重置到 100%，状态栏显示 `缩放：100%`。 |

### 待办列表契约

- 待办列表按钮插入或应用普通文本符号 `☐ `。
- 本阶段不实现 HTML checkbox、不实现鼠标点击切换、不提供 `☐/☑` 快捷切换。
- 用户可以像普通文本一样手动编辑 `☐` 字符。
- 保存的 HTML 中待办项必须作为普通文本保存，不依赖外部资源或表单控件。

### 粘贴与安全边界

- 允许粘贴纯文本与 Qt 支持的基础富文本 HTML 子集。
- 不导入图片、文件路径、远程资源或外部 URL 资源引用。
- 保存后的 HTML 不应包含 `<img`、`src="file:`、`src="http:`、`src="https:` 或未加密临时资源路径。
- 粘贴被净化时使用状态栏提示，不弹阻断式对话框。

---

## Component Inventory for Executor

| Component / Object | Required Role | Notes |
|--------------------|---------------|-------|
| `RichTextEditorWidget` 或等价封装 | 组合 `QTextEdit`、格式工具栏、格式动作和状态同步 | 推荐从 `MainWindow` 中抽出，便于测试；若内联实现，也必须满足本契约。 |
| `QTextEdit` | 富文本编辑核心 | HTML 存储、撤销/重做、剪贴板、缩放。 |
| `QFontComboBox` | 字体选择 | 使用系统字体列表，不支持自定义字体资源。 |
| `QComboBox` 字号 | 字号选择 | 固定常用字号，不支持任意自由输入。 |
| `QComboBox` 段落样式 | 正文/H1-H6 | H1-H6 走 heading block 语义。 |
| `QActionGroup` | 对齐互斥 | 左/中/右/两端只能一个选中。 |
| `QColorDialog` | 文字/背景色选择 | 使用系统原生对话框。 |
| `MainWindow` 编辑菜单 action | 撤销/重做/剪切/复制/粘贴 | Phase 04 必须从灰显占位变为按状态可用。 |
| `MainWindow` 视图菜单 action | 放大/缩小/重置缩放 | 只影响会话显示。 |
| `statusBar()` | 操作反馈 | 缩放、颜色、待办、粘贴净化提示。 |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
