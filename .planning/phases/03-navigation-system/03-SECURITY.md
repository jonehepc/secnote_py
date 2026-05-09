---
phase: 03
slug: navigation-system
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-09
---

# Phase 03 — Security

> Phase 03 导航系统安全审计合同：威胁登记、接受风险和审计轨迹。

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| SNoteItem 数据 → setData() | 用户通过 Qt EditRole 输入标题并写入数据模型 | 分区/页面标题字符串 |
| QTextEdit → HTML 渲染/编辑 | 页面内容显示到右侧 QTextEdit，并在编辑时同步回 note.content | 页面 HTML 内容 |
| 用户交互 → CRUD handler | 工具栏、右键菜单、键盘快捷键触发分区/页面结构变更 | 本地笔记结构变更 |
| Qt signal/event → MainWindow handler | 选择、模型变更、快捷键事件进入窗口状态管理 | UI 状态、dirty 标记 |
| 主窗口快捷键 → 页面列表快捷键 | 同一键序列在不同焦点上下文中分发 | Ctrl+N 用户意图 |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-01 | Tampering | TreeModel.setData() / PageListModel.setData() | mitigate | setData 拒绝非字符串、空字符串和纯空格；成功时 strip 标题并发出 dataChanged。证据：[tree_model.py:185-205](../../../src/secnotepad/model/tree_model.py#L185-L205)、[page_list_model.py:96-110](../../../src/secnotepad/model/page_list_model.py#L96-L110)。 | closed |
| T-03-02 | Tampering | QTextEdit HTML 内容渲染 | accept | 接受风险：计划阶段记录 QTextEdit HTML 渲染风险；桌面本地应用且文件内容受前序加密层保护。Phase 03 后续把编辑区改为可编辑后，内容变更通过 `_on_editor_text_changed()` 写回并标记 dirty。证据：[03-03-PLAN.md:447](03-03-PLAN.md#L447)、[main_window.py:451-464](../../../src/secnotepad/ui/main_window.py#L451-L464)。 | closed |
| T-03-03 | Denial of Service | selection/current 信号反馈循环 | mitigate | 使用 currentChanged 而非 selectionChanged；PageListModel.set_section 使用 beginResetModel/endResetModel。证据：[main_window.py:290-299](../../../src/secnotepad/ui/main_window.py#L290-L299)、[page_list_model.py:36-41](../../../src/secnotepad/model/page_list_model.py#L36-L41)。 | closed |
| T-03-04 | Denial of Service | CRUD handler 信号反馈循环 | accept | 原计划要求 Ctrl+N 仅绑定 list view；当前实现改为窗口级单一分发器，用户在 2026-05-09 接受该实现偏差。删除当前分区时仍清空 PageListModel。证据：[main_window.py:557-575](../../../src/secnotepad/ui/main_window.py#L557-L575)、[main_window.py:671-681](../../../src/secnotepad/ui/main_window.py#L671-L681)。 | closed |
| T-03-05 | Elevation of Privilege | 重复快速点击导致状态不一致 | accept | 接受风险：单用户桌面应用，Qt 单线程事件循环序列化用户交互。证据：[03-04-PLAN.md:700](03-04-PLAN.md#L700)。 | closed |
| T-03-06 | Information Disclosure | 删除确认对话框显示分区名称 | accept | 接受风险：本地 UI 有意显示待删除分区名称以确认用户意图。证据：[03-04-PLAN.md:701](03-04-PLAN.md#L701)、[main_window.py:658-667](../../../src/secnotepad/ui/main_window.py#L658-L667)。 | closed |
| T-03-07 | Tampering | Ctrl+N 页面快捷键 | mitigate | Ctrl+N 分发到 `_on_new_page()`；该 handler 使用 PageListModel.add_note 并调用 mark_dirty。证据：[main_window.py:566-575](../../../src/secnotepad/ui/main_window.py#L566-L575)、[main_window.py:685-696](../../../src/secnotepad/ui/main_window.py#L685-L696)。 | closed |
| T-03-08 | Denial of Service | 重复 _setup_navigation() 后重复快捷键绑定 | accept | 原计划要求 teardown 清理 `_shortcut_new_page`；当前实现没有页面级 `_shortcut_new_page`，而是窗口生命周期内单一 `_shortcut_ctrl_n` 分发器。用户在 2026-05-09 接受该偏差；重复初始化测试覆盖页面创建不重复触发。证据：[main_window.py:327-382](../../../src/secnotepad/ui/main_window.py#L327-L382)、[main_window.py:557-560](../../../src/secnotepad/ui/main_window.py#L557-L560)、[test_navigation.py:228-237](../../../tests/ui/test_navigation.py#L228-L237)。 | closed |
| T-03-09 | Spoofing | Ctrl+N 键序列同时代表新建笔记本和新建页面 | accept | 原计划要求 list-view WidgetShortcut；当前实现为窗口级 Ctrl+N 分发器，并清空主 QAction shortcut 以避免 Qt ambiguous shortcut。用户在 2026-05-09 接受该偏差。证据：[main_window.py:557-575](../../../src/secnotepad/ui/main_window.py#L557-L575)、[test_navigation.py:304-308](../../../tests/ui/test_navigation.py#L304-L308)。 | closed |
| T-03-10 | Denial of Service | 重复 _setup_navigation() 重复 signal/action 绑定 | accept | teardown 已清理 selection、按钮、菜单、actions、dataChanged；shortcut 采用窗口级单一分发器，不随导航重复初始化创建。用户在 2026-05-09 接受“未按计划清理 navigation shortcut”的偏差。证据：[main_window.py:268-269](../../../src/secnotepad/ui/main_window.py#L268-L269)、[main_window.py:327-382](../../../src/secnotepad/ui/main_window.py#L327-L382)、[test_navigation.py:219-268](../../../tests/ui/test_navigation.py#L219-L268)。 | closed |
| T-03-11 | Tampering | Rename dirty-state path | mitigate | TreeModel/PageListModel dataChanged 接入 `_on_structure_data_changed()`，统一调用 mark_dirty。证据：[main_window.py:300-302](../../../src/secnotepad/ui/main_window.py#L300-L302)、[main_window.py:384-385](../../../src/secnotepad/ui/main_window.py#L384-L385)。 | closed |
| T-03-12 | Tampering | 新建子分区后后续操作作用在错误父节点 | mitigate | add_item 后在 proxy parent 下定位新增 child index，并 setCurrentIndex/scrollTo。证据：[main_window.py:387-398](../../../src/secnotepad/ui/main_window.py#L387-L398)、[main_window.py:610-620](../../../src/secnotepad/ui/main_window.py#L610-L620)。 | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-02 | QTextEdit HTML 渲染风险在 Phase 03 被接受；本地加密文件层降低未授权内容篡改可能性。 | PLAN.md plan-time disposition | 2026-05-08 |
| AR-03-02 | T-03-04 | 当前实现使用窗口级 Ctrl+N 单一分发器，而不是仅绑定 `_list_view`；用户接受该实现偏差。 | user | 2026-05-09 |
| AR-03-03 | T-03-05 | 单用户桌面应用，快速重复点击由 Qt 单线程事件循环序列化；无多用户权限边界。 | PLAN.md plan-time disposition | 2026-05-08 |
| AR-03-04 | T-03-06 | 删除确认对话框显示分区名称是确认用户意图所需的本地 UI 行为。 | PLAN.md plan-time disposition | 2026-05-08 |
| AR-03-05 | T-03-08 | 当前实现没有页面级 `_shortcut_new_page`，Ctrl+N 为窗口生命周期内单一 `_shortcut_ctrl_n`；用户接受未按计划 teardown 页面级 shortcut 的偏差。 | user | 2026-05-09 |
| AR-03-06 | T-03-09 | 为避免 Qt ambiguous shortcut，当前实现清空主 QAction shortcut 并通过窗口级分发器区分焦点；用户接受与原 WidgetShortcut 计划不同的实现。 | user | 2026-05-09 |
| AR-03-07 | T-03-10 | `_teardown_navigation()` 不清理窗口级 Ctrl+N shortcut，因为该 shortcut 不随导航初始化重复创建；用户接受该偏差。 | user | 2026-05-09 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-09 | 12 | 8 | 4 | gsd-security-auditor |
| 2026-05-09 | 12 | 12 | 0 | orchestrator after user accepted AR-03-02/05/06/07 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-09
