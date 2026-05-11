# Phase 05: 标签与搜索 - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

实现页面级多标签管理和当前打开笔记本内的全文搜索。用户可在当前页面编辑区顶部添加、查看和移除多个标签；标签随 SNoteItem 持久化到加密 `.secnote` 文件。用户可从菜单打开搜索弹窗，按关键词搜索页面标题、正文纯文本和标签字段，结果显示页面标题、分区路径与高亮片段，点击结果跳转并选中对应页面。Phase 5 不新增全局标签管理页、保存搜索、跨文件搜索、复杂查询语法或搜索索引服务。

</domain>

<decisions>
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 需求与项目
- `.planning/ROADMAP.md` — Phase 5 目标、TAG-01~03 / SRCH-01~03 需求映射和成功标准。
- `.planning/REQUIREMENTS.md` — 标签与搜索需求定义，尤其 TAG-01~03、SRCH-01~03。
- `.planning/PROJECT.md` — 项目范围、技术栈约束（Python 3 + PySide6 + Qt6）、本地加密单文件笔记本和排除范围。

### 前置 Phase Context
- `.planning/phases/04-rich-text-editor/04-CONTEXT.md` — D-65~D-80 定义右侧编辑区、格式工具栏、QTextEdit HTML 存储、安全粘贴和会话级显示状态；Phase 5 标签区域应集成到同一编辑区上下文。
- `.planning/phases/03-navigation-system/03-CONTEXT.md` — D-49~D-64 定义分区树、页面列表、页面选中和编辑区联动；搜索结果跳转必须复用这些导航模式。
- `.planning/phases/02-file-operations-and-encryption/02-CONTEXT.md` — D-45~D-48 定义 dirty 标记、保存/关闭保护和整体文件加密；标签变化必须通过相同脏标志进入保存流程。

### 现有代码集成点
- `src/secnotepad/model/snote_item.py` — `SNoteItem.tags` 已存在为 `list[str]` 字段，Phase 5 可直接用于页面标签持久化。
- `src/secnotepad/model/serializer.py` — 序列化已包含 `tags` 字段并对缺失 tags 提供默认空列表，支持旧数据兼容加载。
- `src/secnotepad/model/page_list_model.py` — 页面列表目前只返回标题 DisplayRole/EditRole；本次决策要求页面列表暂不显示标签。
- `src/secnotepad/ui/main_window.py` — 当前负责页面选择、编辑器切换、dirty 标记、菜单动作连接和状态栏反馈；标签 UI、搜索菜单弹窗和结果跳转将主要在这里集成。
- `src/secnotepad/ui/rich_text_editor.py` — 右侧富文本编辑器组件提供 QTextEdit 和格式工具栏；标签 chip 行应与该编辑区域协同，但标签不是富文本 HTML 内容的一部分。

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SNoteItem.tags`: 页面数据模型已有标签列表字段，不需要新增格式版本或外部标签表即可满足页面级标签。
- `Serializer.to_json()` / `Serializer.from_json()`: dataclass 序列化已写入 tags，反序列化对缺失 tags 使用空列表，可支持旧笔记本打开。
- `MainWindow.mark_dirty()`: 标签新增/删除和搜索跳转中的结构选择变化应复用现有 dirty/clean 机制；只有标签数据变化需要置脏，纯搜索与跳转不应置脏。
- `MainWindow._show_note_in_editor()` / `_show_editor_placeholder()`: 可作为同步标签区域启用、禁用和刷新当前页面标签的集成点。
- `PageListModel.note_at()`: 搜索结果跳转和标签编辑都需要通过当前页面索引拿到 `SNoteItem`。

### Established Patterns
- 信号驱动 UI：导航和富文本编辑均通过 Qt signal/slot 同步状态；标签 chip 的添加、删除和搜索弹窗结果点击也应遵循同一模式。
- 数据与视图分离：`SNoteItem` 保存数据，Qt Model/View 负责展示；标签规则和搜索遍历可以放在独立模型/服务类中，MainWindow 只负责集成。
- 编辑器状态不进入内容 HTML：标签属于 `SNoteItem.tags` 字段，不应写入 `SNoteItem.content` 的 HTML，也不应受富文本安全粘贴逻辑影响。
- 导航重复初始化需幂等：Phase 5 如果新增信号连接或弹窗引用，需避免 `_setup_navigation()` 重复调用导致重复绑定。

### Integration Points
- `_setup_menu_bar()` / `_connect_actions()`：新增搜索菜单项或动作，并连接到搜索弹窗打开逻辑。
- `_setup_editor_area()`：在右侧编辑器容器中加入标签 chip 行，位置应在当前页面编辑区顶部并随页面选择状态更新。
- `_show_note_in_editor()` / `_show_editor_placeholder()`：加载页面或空状态时刷新标签行。
- `_on_editor_content_changed()`：继续只负责 HTML 内容变化；标签变更应有独立 handler 并调用 `mark_dirty()`。
- 分区树与页面列表选择 API：搜索结果点击需要从目标 note 找到其父分区路径、选中对应分区并选中页面。

</code_context>

<specifics>
## Specific Ideas

- 标签交互应像当前页面的元数据编辑区：在编辑器顶部展示 chip，不污染页面正文 HTML。
- 标签补全基于当前笔记本已有标签集合，不需要单独全局标签库。
- 搜索弹窗保持打开，支持连续查看多个结果；点击结果只选中对应页面，不强制定位到正文命中位置。

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-tags-and-search*
*Context gathered: 2026-05-11*
