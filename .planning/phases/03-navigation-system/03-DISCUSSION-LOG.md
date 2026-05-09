# Phase 03: 导航系统 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 03-navigation-system
**Areas discussed:** 分区树显示策略, CRUD 触发方式, 重命名交互方式, 页面列表与编辑区联动

---

## 分区树显示策略

| Option | Description | Selected |
|--------|-------------|----------|
| QSortFilterProxyModel（推荐） | 创建 SectionFilterProxy 子类，过滤 item_type=='section'，不改动现有 TreeModel | ✓ |
| TreeModel 添加分段方法 | 在 TreeModel 中新增 section_only 方法，改动集中在 Model 层 | |
| 独立 SectionTreeModel | 新建只含分区节点的独立模型，与 TreeModel 完全分离 | |

| Option | Description | Selected |
|--------|-------------|----------|
| QAbstractListModel 子类（推荐） | 新建 PageListModel，接收 section 为数据源，平铺 note 子节点 | ✓ |
| 复用 TreeModel + 第二个 Proxy | 为 QListView 也套 Proxy 过滤 note | |
| 直接用 QStandardItemModel | 点击分区时动态填充 | |

| Option | Description | Selected |
|--------|-------------|----------|
| QItemSelectionModel 信号（推荐） | 监听 selectionChanged 信号驱动页面列表更新 | ✓ |
| QTreeView clicked 信号 | 直接连接 clicked 信号 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 自动选中第一个分区（推荐） | 打开笔记本后自动选中根分区下第一个子分区 | ✓ |
| 不选中任何分区 | 分区树和页面列表均为空状态 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 展开所有分区（推荐） | 递归展开所有层级 | |
| 仅展开第一层 | 只展开根分区下的直接子分区 | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| 仅标题（推荐） | QListView 单列显示页面标题 | ✓ |
| 标题 + 更新时间 | 两列或双行显示 | |
| 标题 + 标签数 | 标题旁显示标签数量徽标 | |

---

## CRUD 触发方式

| Option | Description | Selected |
|--------|-------------|----------|
| 右键菜单为主，快捷键为辅（推荐） | 右键菜单 + Delete/F2/Ctrl+Shift+N | |
| 纯右键菜单 | 所有操作仅右键菜单 | |
| 工具栏按钮 + 右键菜单 | 分区树/页面列表上方按钮 + 右键菜单 | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| 分区树和页面列表上方各有一组（推荐） | 就近放置，上下文清晰 | ✓ |
| 统一放在菜单栏/主工具栏 | 顶部集中管理 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 根据右键目标类型（推荐） | 右键分区 vs 页面的菜单不同 | ✓ |
| 统一菜单 | 所有位置菜单相同，不适用的灰显 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 标准快捷键（推荐） | Delete/F2/Ctrl+N | ✓ |
| 不需要快捷键 | 仅鼠标操作 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 仅删除含子内容时警告（推荐） | 有子内容才弹级联删除警告 | ✓ |
| 始终弹出确认 | 每次删除都弹确认 | |
| 不确认，支持撤销 | 直接删除，状态栏提示可撤销 | |

---

## 重命名交互方式

| Option | Description | Selected |
|--------|-------------|----------|
| 原地编辑（推荐） | 双击/F2 触发 Qt EditTrigger，Enter 确认 Esc 取消 | ✓ |
| 弹出对话框 | QInputDialog 输入新名称 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 双击或 F2 触发（推荐） | EditTriggers = DoubleClicked \| EditKeyPressed | ✓ |
| 仅 F2 触发 | EditTriggers = EditKeyPressed | |

| Option | Description | Selected |
|--------|-------------|----------|
| 拒绝空名称并还原（推荐） | setData() 返回 False，视图还原旧名称 | ✓ |
| 允许空名称 | 接受空字符串 | |

---

## 页面列表与编辑区联动

| Option | Description | Selected |
|--------|-------------|----------|
| 只读内容预览（推荐） | 放置只读 QTextEdit，点击页面显示 HTML 内容 | ✓ |
| 页面标题 + 提示信息 | 显示标题和"编辑器将在后续版本实现" | |
| 保持空白 | 不改变当前空白占位符 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 显示提示文字（推荐） | 未选中页面时居中显示引导提示 | ✓ |
| 保持完全空白 | 空白白板 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 自动选中新页面（推荐） | 新建后自动选中，编辑区显示空白内容 | ✓ |
| 不选中，保持原选择 | 添加到列表但保持原选中项 | |

---

## Claude's Discretion

所有决策均由用户选择——无"Claude 决定"的领域。

## Deferred Ideas

None — discussion stayed within phase scope.
