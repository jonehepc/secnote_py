---
phase: 05
slug: tags-and-search
status: approved
shadcn_initialized: false
preset: none
created: 2026-05-11
reviewed_at: 2026-05-11
---

# Phase 05 — UI Design Contract

> 标签与搜索阶段的视觉与交互契约。由 gsd-ui-researcher 生成，供 gsd-ui-checker、planner、executor 和 auditor 使用。

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none（不使用 shadcn；本项目是 PySide6 / Qt Widgets 桌面应用） |
| Preset | not applicable |
| Component library | PySide6 Qt Widgets：`QWidget`、`QFrame`、`QLabel`、`QLineEdit`、`QToolButton`、`QPushButton`、`QCompleter`、`QStringListModel`、`QDialog`、`QCheckBox`、`QListWidget` 或等价 Model/View、`QTextDocumentFragment` |
| Icon library | Qt `QStyle.standardIcon()` 优先；标签移除可用短文本 `×`；若 Qt 无语义匹配图标，使用清晰中文文字按钮，不引入第三方图标库 |
| Font | 系统 UI 默认字体；标签 chip、搜索弹窗、结果列表均继承系统 UI 字体；富文本正文继续由 Phase 04 编辑器契约管理 |

**来源说明：** 技术栈来自 `/home/jone/projects/secnotepad/.planning/PROJECT.md`、`/home/jone/projects/secnotepad/.planning/phases/05-tags-and-search/05-RESEARCH.md` 和 `/home/jone/projects/secnotepad/pyproject.toml`；标签/搜索交互决策来自 `05-CONTEXT.md` 的 D-81 至 D-96；现有 UI 模式来自 `src/secnotepad/ui/main_window.py`、`rich_text_editor.py`、`welcome_widget.py`、`password_dialog.py`。shadcn gate 已执行：项目不是 React/Next.js/Vite，`components.json` 不适用，因此不初始化 shadcn。

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | 标签 chip 内图标与文本间距、chip 行内紧凑间隔、搜索筛选复选框之间的最小间距 |
| sm | 8px | 标签 chip 之间间距、标签行与富文本工具栏之间间距、搜索表单控件间距、结果项内部标题/路径/片段间距 |
| md | 16px | 标签区域左右内边距、搜索弹窗内容默认边距、结果列表与操作按钮之间间距 |
| lg | 24px | 搜索弹窗分区之间间距、空结果提示与输入区域的间距 |
| xl | 32px | 搜索弹窗主内容块间隔；不用于 chip 内部 |
| 2xl | 48px | 较大空状态中的垂直留白；搜索结果为空时可用于提示区域上方留白 |
| 3xl | 64px | 页面级空白；Phase 05 常规标签和搜索控件不使用 |

Exceptions:
- 沿用现有三栏布局与 Phase 04 富文本编辑器整体结构；Phase 05 新增布局不得继续扩散旧导航按钮栏中已有的 2px spacing。
- 标签 chip 最小高度 24px，推荐高度 28px；chip 内水平 padding 使用 8px，垂直 padding 使用 4px。
- 标签移除按钮可视尺寸不小于 20×20px，整颗 chip 可点击/聚焦区域高度不小于 28px。
- 添加标签输入框最小宽度 120px，推荐宽度 160px；搜索关键词输入框最小宽度 320px。
- 搜索弹窗最小尺寸 640×420px，初始推荐尺寸 720×520px；结果列表最小高度 240px。

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
- 标签 chip 文本使用 Label：12px / 400 / 1.4；chip 内 `×` 使用 12px / 600 / 1.0，不引入单独字重 token。
- 搜索结果标题使用 Body：14px / 600 / 1.5；分区路径使用 Label：12px / 400 / 1.4；匹配片段使用 Body：14px / 400 / 1.5。
- 搜索弹窗标题使用 Heading：18px / 600 / 1.2；不要在 Phase 05 新增大标题或营销式 Display 文案。

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | 系统窗口背景色 / Qt palette Window | 主窗口背景、右侧编辑区外层背景、搜索弹窗背景、空状态背景 |
| Secondary (30%) | 系统 Base / AlternateBase | QTextEdit 编辑面、标签 chip 背景、搜索结果列表、搜索字段筛选区域、分区树与页面列表 |
| Accent (10%) | 系统 Highlight 色 | 当前页面/分区选择态、标签添加入口焦点边框、搜索按钮、搜索结果当前选中态、关键词高亮背景 |
| Destructive | #d32f2f | 标签移除 hover/pressed 状态、删除/丢弃类现有确认、错误提示、搜索或标签校验错误 |

Accent reserved for:
- 当前页面/分区选中态；
- `QTextEdit` 文本选区；
- 标签添加输入框的焦点边框或焦点强调；
- 搜索弹窗的主按钮 `搜索`；
- 搜索结果当前选中行；
- 匹配关键词高亮（仅结果片段内，使用可读的 accent 淡色背景或系统 Highlight 派生色）。

**颜色约束：**
- Phase 05 不引入完整 QSS 主题；现代化全局视觉属于 Phase 06。
- 标签 chip 使用 Secondary 背景 + palette Text 文本；chip 边框使用 palette Mid 或等价系统分隔色。
- 标签移除 `×` 默认使用次要文本色，hover/pressed 时可使用 Destructive；不要让所有 chip 常态显示为红色。
- 搜索片段高亮必须先对用户内容做 HTML 转义，再插入高亮 span/mark；不要把原始笔记 HTML 注入结果列表。
- 错误/危险语义只使用 Destructive，不能用 Accent 表达删除、丢弃、无效输入或搜索失败。

---

## Copywriting Contract

| Element | Copy |
|---------|------|
| Primary CTA | 添加标签 |
| Empty state heading | 暂无标签 |
| Empty state body | 为当前页面添加标签，方便之后按标签搜索。 |
| Error state | 无法添加标签。请使用 1–32 个字符，且不要与当前页面已有标签重复。 |
| Destructive confirmation | 本阶段不新增需要弹窗确认的破坏性操作；移除单个标签通过 chip 上的 `×` 立即执行并置脏，不弹确认。沿用现有删除分区、丢弃未保存更改确认。 |

**标签区域文案：**
- 标签区域标签：`标签`
- 空标签占位：`暂无标签`
- 添加输入框 placeholder：`添加标签…`
- 添加按钮/入口：`添加标签`
- 标签移除按钮 tooltip：`移除标签：{tag}`
- 重复标签提示：`该页面已包含此标签`
- 空标签提示：`标签不能为空`
- 超长标签提示：`标签不能超过 32 个字符`
- 成功添加状态栏：`已添加标签：{tag}`
- 成功移除状态栏：`已移除标签：{tag}`

**搜索弹窗文案：**
- 菜单项：`搜索(&F)...`
- 快捷键：`Ctrl+F`
- 弹窗标题：`搜索笔记`
- 关键词输入框 label：`关键词`
- 关键词输入框 placeholder：`输入要搜索的标题、正文或标签`
- 搜索范围 label：`搜索范围`
- 字段筛选：`标题`、`正文`、`标签`
- 默认字段：`标题` 与 `正文` 勾选，`标签` 不勾选
- 主按钮：`搜索`
- 关闭按钮：`关闭`
- 空查询提示：`请输入关键词后搜索`
- 无结果 heading：`未找到匹配结果`
- 无结果 body：`请尝试更换关键词，或勾选更多搜索范围。`
- 结果计数：`找到 {count} 个结果`
- 搜索失败：`无法完成搜索。请检查笔记本数据后重试。`
- 结果跳转状态栏：`已跳转到：{title}`

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | 不适用 — PySide6/Qt Widgets 桌面应用，未初始化 shadcn — 2026-05-11 |
| third-party registries | none | 不适用 — 未声明第三方 registry 或 block — 2026-05-11 |

---

## Phase-Specific Interaction Contract

### 标签区域结构

| Area | Contract |
|------|----------|
| 位置 | 标签编辑入口固定在右侧编辑区顶部，位于当前页面编辑区域内；不得放入中间页面列表、左侧分区树或主工具栏。 |
| 顺序 | 右侧编辑区垂直顺序为：标签栏 → Phase 04 格式工具栏 → QTextEdit/placeholder。标签栏不是富文本 HTML 内容的一部分。 |
| 展示 | 标签使用横向 chip 行展示，每个 chip 显示原始标签文本和移除入口 `×`。末尾提供添加标签输入/按钮。 |
| 换行 | 标签数量超出一行时允许 chip 行换行；不得横向撑破右侧编辑区，不得覆盖格式工具栏。 |
| 未选中页面 | 标签区域随编辑器状态禁用或隐藏为不可编辑状态；行为必须与 Phase 04 格式工具栏未选页面时禁用的模式一致。 |
| 页面列表 | 页面列表继续保持当前单列标题列表模式；不得新增标签 delegate、第二行标签或 chip 展示。 |

### 标签输入规则

| Trigger | Required UI Response |
|---------|----------------------|
| 输入标签后回车 | 对输入做首尾 trim；合法时添加标签并清空输入框。 |
| 点击 `添加标签` | 行为与回车一致。 |
| 输入空白 | 不新增标签；在标签区域内显示 `标签不能为空`，状态栏可同步显示同文案。 |
| 输入超过 32 字符 | 不新增标签；显示 `标签不能超过 32 个字符`。 |
| 输入与当前页面已有标签大小写忽略后重复 | 不新增标签；保留已有标签显示形式；显示 `该页面已包含此标签`。 |
| 输入中文、空格、大小写或常见符号 | 允许保存和展示；除 trim、空值、长度、当前页面内 casefold 去重外不做 slug 化或字符替换。 |
| 添加成功 | 更新当前页面 `SNoteItem.tags`，调用 `mark_dirty()`，刷新 chip 行与补全候选，状态栏显示 `已添加标签：{tag}`。 |
| 移除 chip | 立即从当前页面 `SNoteItem.tags` 移除，调用 `mark_dirty()`，刷新 chip 行与补全候选，状态栏显示 `已移除标签：{tag}`；不弹确认。 |

### 标签补全

| Aspect | Contract |
|--------|----------|
| Source | 补全候选来自当前打开笔记本内所有页面的 tags 集合。 |
| Matching | 使用大小写不敏感补全；候选显示保留首次收集到的原始文本。 |
| Component | 使用 `QCompleter` + `QStringListModel` 或 Qt 等价官方补全组件，不手写自定义浮层。 |
| Refresh | 新建/打开笔记本、页面切换、添加标签、移除标签后刷新候选；不得显示其他笔记本会话的历史标签。 |
| Free input | 补全仅帮助复用已有标签；用户仍可输入新标签。 |

### 搜索入口与弹窗

| Area | Contract |
|------|----------|
| 菜单位置 | 放入 `编辑(&E)` 菜单，菜单项文本为 `搜索(&F)...`。 |
| 快捷键 | 使用 `Ctrl+F` 打开搜索弹窗；快捷键作用域为主窗口。 |
| 弹窗模式 | 使用可保持打开的 modeless `QDialog` 或等价非阻塞对话框；点击结果跳转后弹窗保持打开。 |
| 触发方式 | 搜索只在用户按回车或点击 `搜索` 按钮时执行；不要实时搜索，不做 debounce 每次输入。 |
| 搜索范围 | 默认搜索当前打开笔记本内全部页面，不限当前分区。 |
| 字段筛选 | 弹窗提供 `标题`、`正文`、`标签` 三个筛选项；默认勾选 `标题` 和 `正文`，`标签` 可选。至少一个字段必须保持勾选。 |
| 无笔记本 | 未打开笔记本时，搜索菜单项禁用；不得打开空搜索弹窗。 |

### 搜索结果展示

| Element | Contract |
|---------|----------|
| 结果项标题 | 显示页面标题，使用 14px / 600；同名页面用路径区分，不改写标题。 |
| 分区路径 | 显示页面所在分区路径，例如 `根分区 / 项目 / 会议`；使用 12px 次要文本。 |
| 匹配片段 | 显示从标题、正文纯文本或标签字段生成的短片段；正文片段必须从 HTML 提取纯文本后生成。 |
| 高亮 | 高亮关键词在片段中的命中部分；所有用户内容先 HTML 转义，再插入高亮样式。 |
| 结果计数 | 搜索完成后显示 `找到 {count} 个结果`；0 个结果时显示空结果文案。 |
| 排序 | 使用遍历树时的自然顺序：分区树顺序优先，分区内页面顺序优先；不要按标题重新排序。 |
| 选择态 | 当前结果项选择态使用 Accent；hover 可使用 Secondary 派生背景。 |

### 搜索结果跳转

| Trigger | Required UI Response |
|---------|----------------------|
| 单击或双击结果项 | 主界面展开并选中对应分区，页面列表切换到该分区并选中对应页面，右侧编辑器加载页面内容与标签。 |
| 跳转完成 | 搜索弹窗保持打开；状态栏显示 `已跳转到：{title}`。 |
| 正文命中 | Phase 05 不要求把 QTextEdit 光标定位到正文匹配位置，也不要求在编辑器正文中高亮命中。 |
| 标签命中 | 跳转逻辑与标题/正文命中一致，只选中页面，不打开全局标签管理视图。 |
| Dirty 语义 | 搜索、结果展示和跳转都不得调用 `mark_dirty()`；只有标签 add/remove 修改 `SNoteItem.tags` 时置脏。 |

### 安全与隐私边界

- 搜索仅在当前已解密、已打开的内存 `SNoteItem` 树中执行。
- 不建立外部索引、数据库、缓存文件或明文搜索历史。
- 不记录搜索 query、匹配片段、页面正文或标签到日志/调试输出。
- 结果片段不保留富文本 HTML 格式；不得把 `SNoteItem.content` 原始 HTML 直接设置为结果项 rich text。
- 标签属于 `SNoteItem.tags` 页面元数据，不得写入 `SNoteItem.content` HTML。

---

## Component Inventory for Executor

| Component / Object | Required Role | Notes |
|--------------------|---------------|-------|
| `TagBarWidget` | 右侧编辑区顶部的页面标签 chip 行、添加入口、校验提示和补全 | 推荐新增独立 widget，发出 `tag_added(str)` / `tag_removed(str)` 信号；MainWindow 负责修改当前 `SNoteItem.tags`。 |
| `QFrame` / `QWidget` chip | 单个标签展示和移除入口 | chip 文本保留原始标签；移除按钮 tooltip 使用 `移除标签：{tag}`。 |
| `QLineEdit` | 添加标签输入 | placeholder 为 `添加标签…`；回车触发添加。 |
| `QCompleter` + `QStringListModel` | 当前笔记本已有标签补全 | 大小写不敏感；候选随当前笔记本刷新。 |
| `SearchDialog` | 搜索弹窗 | 包含关键词、字段筛选、搜索/关闭按钮、结果计数、结果列表和空状态。 |
| `SearchService` | 搜索当前内存树、HTML 转纯文本、片段生成和字段筛选 | UI 不直接遍历树；服务返回包含 note 引用/id、标题、路径、片段的结果对象。 |
| `QTextDocumentFragment` 或 `QTextDocument` | 从 QTextEdit HTML 提取纯文本 | 不用正则剥离 HTML。 |
| `QListWidget` + 自定义 item widget 或等价 Model/View | 搜索结果列表 | 需要同时展示标题、路径、片段和高亮；结果项数据保存目标 note。 |
| `MainWindow` 编辑菜单 action | `搜索(&F)...` 菜单项和 `Ctrl+F` 快捷键 | 未打开笔记本时禁用；打开笔记本后启用。 |
| `MainWindow` 导航集成 | 结果跳转选中分区和页面 | 必须正确处理 `SectionFilterProxy.mapFromSource()`，避免树、列表、编辑器不同步。 |
| `statusBar()` | 操作反馈 | 标签 add/remove、搜索结果计数、结果跳转提示。 |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
