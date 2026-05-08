# Phase 03: 导航系统 - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

## Phase Boundary

实现分区树和页面列表的交互管理——左侧 QTreeView 仅显示分区（多级嵌套），中间 QListView 显示当前选中分区下的页面列表，右侧编辑区展示选中页面的只读内容预览。支持分区和页面的创建、重命名、删除操作，结构变更触发脏标志。

## Implementation Decisions

### 分区树显示策略

- **D-49:** 使用 QSortFilterProxyModel 子类过滤分区树——重写 filterAcceptsRow，仅显示 item_type == "section" 的节点。TreeModel 保持完整数据不变，过滤在视图层完成。
- **D-50:** 新建 PageListModel(QAbstractListModel) 驱动中间 QListView——接收 SNoteItem(section) 为数据源，平铺显示其 children 中的 note 类型节点。仅支持单列标题显示。
- **D-51:** 分区选择 → 页面列表更新通过 QItemSelectionModel.selectionChanged 信号驱动——获取选中分区的 SNoteItem，调用 PageListModel.set_section() 刷新列表。
- **D-52:** 打开笔记本后自动选中根分区下的第一个子分区，页面列表随之显示其下页面。
- **D-53:** 打开笔记本后分区树仅展开第一层，更深层子分区保持折叠状态。
- **D-54:** 页面列表仅显示标题（Qt.DisplayRole），单列布局。

### CRUD 触发方式

- **D-55:** 工具栏按钮 + 右键菜单组合——分区树上方放置「新建分区」「新建子分区」按钮，页面列表上方放置「新建页面」按钮。
- **D-56:** 右键菜单根据目标类型变化：右键分区 → 新建子分区、新建页面、重命名分区、删除分区；右键页面 → 重命名页面、删除页面；右键空白区域 → 新建分区/页面。
- **D-57:** 标准键盘快捷键——Delete 删除选中项、F2 重命名、Ctrl+N 新建页面（页面列表聚焦时）。
- **D-58:** 删除确认——仅当分区含子内容（子分区或页面）时弹警告对话框说明级联删除内容；删除空分区或单页面不弹确认。

### 重命名交互方式

- **D-59:** 原地编辑——QTreeView/QListView 设置 EditTriggers = DoubleClicked | EditKeyPressed。双击或选中+F2 进入编辑，Enter 确认，Esc 取消还原。
- **D-60:** 空名称拒绝——Model.setData() 中若 EditRole 数据为空字符串，返回 False，视图自动还原旧名称。可配合状态栏提示"名称不能为空"。
- **D-61:** 所有结构变更操作（创建/重命名/删除分区和页面）后调用 MainWindow.mark_dirty() 标记笔记本已修改。

### 页面列表与编辑区联动

- **D-62:** 点击页面后在右侧编辑区显示只读 QTextEdit，渲染选中页面的 HTML 内容。Phase 4 将同一 QTextEdit 切换为可编辑模式并添加格式工具栏。
- **D-63:** 未选中任何页面时，编辑区显示居中提示文字"请在页面列表中选择一个页面"。
- **D-64:** 新建页面后自动在页面列表中选中新创建的页面，编辑区随之显示空白内容。

### Claude's Discretion

所有决策均由用户选择——无"Claude 决定"的领域。

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 需求与项目
- `.planning/ROADMAP.md` — Phase 3 目标、NAV-01~04 需求和 4 条成功标准
- `.planning/REQUIREMENTS.md` — NAV-01~04 完整定义
- `.planning/PROJECT.md` — 技术栈约束（PySide6 + Qt6、QTextEdit 方案）、关键决策（分区树+页面列表分离布局）

### 前置 Phase Context
- `.planning/phases/02-file-operations-and-encryption/02-CONTEXT.md` — D-45（mark_dirty/mark_clean 接口）、D-47（新建不脏）、信号驱动架构、数据/视图分离模式

### 现有代码集成点
- `src/secnotepad/model/tree_model.py` — TreeModel（QAbstractItemModel），已提供 add_item()/remove_item() 方法。需新增 setData() 支持 EditRole 以实现原地重命名。
- `src/secnotepad/model/snote_item.py` — SNoteItem 数据模型（new_section/new_note 工厂方法，item_type 区分分区/页面）
- `src/secnotepad/ui/main_window.py` — MainWindow 主窗口：`_tree_view` (QTreeView)、`_list_view` (QListView)、`_editor_placeholder` (QWidget)、`_stack` (QStackedWidget)、mark_dirty()/mark_clean()。`_on_new_notebook()` 和 `_on_open_notebook()` 是 Phase 3 导航设置的主要集成点。

## Existing Code Insights

### Reusable Assets
- **TreeModel:** 已有 add_item()/remove_item() 方法，支持 beginInsertRows/endInsertRows 信号。树遍历辅助方法 _find_parent()/_child_row() 可用。
- **SNoteItem:** new_section()/new_note() 工厂方法、item_type 字段、children 列表——为过滤和 CRUD 提供数据基础。
- **MainWindow._tree_view / _list_view:** 两个视图已创建并布局好，仅需绑定新模型和交互。
- **mark_dirty():** Phase 2 已暴露的脏标志接口，Phase 3 直接调用。

### Established Patterns
- **信号驱动架构:** WelcomeWidget 信号 → MainWindow 槽的模式延续到导航（selectionChanged 信号 → 更新页面列表）。
- **数据与视图分离:** SNoteItem（纯数据）→ Model（QAbstractItemModel 子类）→ View（QTreeView/QListView）。新增 PageListModel 和 SectionFilterProxy 遵循此模式。
- **QStackedWidget 页切换:** index 0 = Welcome、index 1 = 三栏布局。打开/新建笔记本后切换，Phase 3 不改变此逻辑。

### Integration Points
- `MainWindow._on_new_notebook()` — 创建根分区 + TreeModel + 设置 QTreeView 后，需额外：创建 SectionFilterProxy + PageListModel + 设置 QListView + 放置只读 QTextEdit
- `MainWindow._on_open_notebook()` / `_on_open_recent()` — 同上，加载已有笔记本后设置导航三栏
- `_tree_view` — 当前直接设置 TreeModel，需改为 SectionFilterProxy（包装 TreeModel）
- `_list_view` — 当前无模型，需绑定 PageListModel
- `_editor_placeholder` — 需替换为只读 QTextEdit，通过 selectionChanged 信号更新内容

## Specific Ideas

- 旧项目 SafetyNotebook 在同一个 QTreeView 中混合显示分区和笔记——Phase 3 通过 Proxy 过滤 + 独立 PageListModel 实现分区与页面的分离展示
- 只读 QTextEdit 预览为 Phase 4 富文本编辑器铺路——Phase 4 只需移除只读限制、添加格式工具栏即可

## Deferred Ideas

None — discussion stayed within phase scope.

---

*Phase: 03-navigation-system*
*Context gathered: 2026-05-08*
