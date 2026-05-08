---
phase: 03
slug: navigation-system
status: active
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-08
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x+ (项目已安装 9.0.3) |
| **Config file** | pytest.ini (项目根目录) |
| **Quick run command** | `python -m pytest tests/model/ -x --timeout=10` |
| **Full suite command** | `python -m pytest tests/ -x --timeout=30` |
| **Estimated runtime** | ~15 秒 (quick), ~60 秒 (full) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/model/ -x --timeout=10`
- **After every plan wave:** Run `python -m pytest tests/ -x --timeout=30`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 秒

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-TDD | 01 | 1 | NAV-01 | N/A | SectionFilterProxy 仅显示 section 类型节点 | unit | `python -m pytest tests/model/test_section_filter_proxy.py -x` | ❌ W0 | ⬜ pending |
| 03-02-TDD | 02 | 1 | NAV-02, NAV-04 | N/A | PageListModel 展示选中分区下的页面列表 | unit | `python -m pytest tests/model/test_page_list_model.py -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | NAV-01, NAV-02, NAV-03 | N/A | TreeModel.setData(EditRole) 支持原地重命名 | unit | `python -m pytest tests/model/test_tree_model.py -x` | ✅ | ⬜ pending |
| 03-03-02 | 03 | 2 | NAV-01, NAV-02 | N/A | MainWindow 导航系统骨架搭建 | integration | `python -m pytest tests/ui/test_main_window.py -x` | ✅ | ⬜ pending |
| 03-04-01 | 04 | 3 | NAV-03, NAV-04 | N/A | 分区/页面 CRUD + 右键菜单 + 工具栏 + 快捷键 | integration | `python -m pytest tests/ui/test_navigation.py -x --timeout=15` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/model/test_section_filter_proxy.py` — SectionFilterProxy 过滤逻辑桩（TDD RED 阶段自动创建）
- [x] `tests/model/test_page_list_model.py` — PageListModel setData/set_section 桩（TDD RED 阶段自动创建）
- [x] `tests/model/test_tree_model.py` — 已存在，Phase 01 创建，仅需添加 TestTreeModelSetData 类
- [x] `tests/ui/test_navigation.py` — 导航 CRUD 集成测试（Plan 03-04 Task 3 创建）

*Existing infrastructure covers pytest + QApplication fixture + QSignalSpy — no framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 右键菜单目标类型切换 | NAV-03, NAV-04 | 上下文菜单弹出位置依赖视觉确认 | 右键分区 → 验证菜单选项（新建子分区/页面/重命名/删除）；右键页面 → 验证（重命名/删除） |
| 删除含子内容分区警告对话框 | NAV-03 | 对话框交互依赖用户确认 | 删除含子分区的分区 → 验证警告对话框出现；删除空分区 → 验证无对话框 |
| 新建页面后自动选中 | NAV-04 | 选择焦点切换需视觉确认 | 创建新页面 → 验证列表自动选中 → 编辑区显示空白内容 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-05-08
