---
phase: 05-tags-and-search
plan: 04
subsystem: ui
tags: [pyside6, qt-widgets, search-dialog, search-service, tdd]

requires:
  - phase: 05-tags-and-search
    provides: "05-01 的 SearchService、SearchFields、SearchResult 搜索契约"
provides:
  - "SearchDialog modeless 搜索弹窗"
  - "关键词输入、字段筛选、搜索按钮/回车触发和结果计数"
  - "安全富文本片段展示和 result_activated(SearchResult) 信号"
affects: [05-tags-and-search, main-window-search-integration]

tech-stack:
  added: []
  patterns:
    - "PySide6 QDialog modeless 搜索弹窗"
    - "QListWidget item Qt.UserRole 保存 SearchResult 原始对象"
    - "SearchService.snippet 作为唯一片段数据源"

key-files:
  created:
    - src/secnotepad/ui/search_dialog.py
    - tests/ui/test_search_dialog.py
  modified:
    - tests/ui/test_search_dialog.py

key-decisions:
  - "SearchDialog 只发出 result_activated(SearchResult)，不承担 MainWindow 导航跳转和关闭弹窗职责。"
  - "结果片段只渲染 SearchService.snippet，不读取 SNoteItem.content，避免原始 HTML 注入 UI。"
  - "搜索仅由搜索按钮或输入框回车触发，不连接 textChanged，保持非实时搜索语义。"

patterns-established:
  - "字段筛选至少保留一个勾选项，避免向 SearchService 传递全禁用字段。"
  - "空查询和搜索异常使用固定 UI 文案，不调用搜索服务且不输出 query、正文或片段到日志。"

requirements-completed: [SRCH-01, SRCH-02]

duration: 5min
completed: 2026-05-11
---

# Phase 05 Plan 04: SearchDialog 搜索弹窗 Summary

**可保持打开的 PySide6 搜索弹窗，消费 SearchService 并安全展示标题、路径、高亮片段和结果激活信号**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-11T10:07:42Z
- **Completed:** 2026-05-11T10:12:28Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 创建 `SearchDialog`，提供关键词输入、标题/正文/标签字段筛选、搜索按钮、关闭按钮、结果计数和结果列表。
- 接入 `SearchService.search(root, query, fields)`，结果项保存原始 `SearchResult` 到 `Qt.UserRole`，为后续 MainWindow 跳转集成提供 payload。
- 通过 UI 测试覆盖空查询、无结果、按钮/回车触发、安全片段展示、非实时搜索和结果激活后弹窗保持打开。
- 按威胁模型约束实现：不读取原始 `note.content` 渲染片段、不记录 query/正文/片段、至少保持一个字段勾选。

## Task Commits

Each task was committed atomically:

1. **Task 1: 编写 SearchDialog 行为测试** - `b02d50a` (test)
2. **Task 2: 实现 SearchDialog 弹窗** - `f99e0c5` (feat)
3. **Task 3: 弹窗回归和无实时搜索检查** - `a4378e0` (test)

**Plan metadata:** 本 SUMMARY 由后续 docs commit 提交。

_Note: TDD tasks used RED/GREEN commits: Task 1 added failing tests, Task 2 implemented passing behavior._

## Files Created/Modified

- `src/secnotepad/ui/search_dialog.py` - 新增 modeless `SearchDialog`、字段筛选、结果列表、安全片段展示和 `result_activated` 信号。
- `tests/ui/test_search_dialog.py` - 新增搜索弹窗 UI 行为测试和回归测试。

## Decisions Made

- SearchDialog 不直接操作 MainWindow；结果激活只发出 `result_activated(SearchResult)`，后续计划负责导航。
- 结果 item widget 的标题和路径使用 plain text，片段使用 rich text，但片段只来自 `SearchService.snippet`。
- 空查询不调用搜索服务；搜索异常只展示固定错误文案，避免泄漏用户 query 或笔记内容。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 使用项目主目录虚拟环境运行测试**
- **Found during:** Task 1（编写 SearchDialog 行为测试）
- **Issue:** 隔离 worktree 内不存在 `.venv/bin/python`，计划命令直接指向 worktree 会无法运行。
- **Fix:** 使用项目主目录 `/home/jone/projects/secnotepad/.venv/bin/python`，并设置 `PYTHONPATH` 指向当前 worktree，确保测试执行当前 worktree 代码。
- **Files modified:** 无代码文件改动。
- **Verification:** `QT_QPA_PLATFORM=offscreen PYTHONPATH="/home/jone/projects/secnotepad/.claude/worktrees/agent-a40e89ac1e2c2f44b" /home/jone/projects/secnotepad/.venv/bin/python -m pytest ...` 通过。
- **Committed in:** 不适用（执行环境调整）。

**2. [Rule 1 - Bug] 修正测试中未显示父对话框时的可见标签断言**
- **Found during:** Task 2（实现 SearchDialog 弹窗）
- **Issue:** Qt 子控件在父对话框未 show 时 `isVisible()` 为 false，导致消息文案测试无法观察到未隐藏状态。
- **Fix:** 测试辅助函数改为检查 `not label.isHidden()`，准确验证消息标签是否由 SearchDialog 显示。
- **Files modified:** `tests/ui/test_search_dialog.py`
- **Verification:** `tests/ui/test_search_dialog.py` 7 项测试通过。
- **Committed in:** `f99e0c5`

---

**Total deviations:** 2 auto-fixed（1 blocking, 1 bug）
**Impact on plan:** 两项均为完成计划验证和测试正确性的必要调整，无功能范围扩张。

## Issues Encountered

- RED 阶段按预期失败于 `ModuleNotFoundError: No module named 'src.secnotepad.ui.search_dialog'`，确认测试先于实现生效。
- Worktree 没有独立 `.venv`，根据用户记忆要求使用项目虚拟环境，并通过 `PYTHONPATH` 指向 worktree 代码。

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - scanned created/modified files. Empty strings/None usages are UI initial state defaults or optional constructor arguments, not user-visible placeholder stubs.

## Threat Flags

None - 本计划新增 UI 展示边界均已在计划 threat_model 中覆盖；没有新增网络端点、文件访问、认证路径或 schema 信任边界。

## TDD Gate Compliance

- RED gate commit exists: `b02d50a` (`test(05-04): add failing tests for search dialog`)
- GREEN gate commit exists after RED: `f99e0c5` (`feat(05-04): implement modeless search dialog`)
- Regression test commit exists after GREEN: `a4378e0`

## Verification

- `QT_QPA_PLATFORM=offscreen PYTHONPATH="/home/jone/projects/secnotepad/.claude/worktrees/agent-a40e89ac1e2c2f44b" /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-a40e89ac1e2c2f44b/tests/ui/test_search_dialog.py -x` — 7 passed
- `QT_QPA_PLATFORM=offscreen PYTHONPATH="/home/jone/projects/secnotepad/.claude/worktrees/agent-a40e89ac1e2c2f44b" /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-a40e89ac1e2c2f44b/tests/model/test_search_service.py /home/jone/projects/secnotepad/.claude/worktrees/agent-a40e89ac1e2c2f44b/tests/ui/test_search_dialog.py -x` — 14 passed

## Self-Check: PASSED

- Created file exists: `src/secnotepad/ui/search_dialog.py`
- Created file exists: `tests/ui/test_search_dialog.py`
- Summary file exists: `.planning/phases/05-tags-and-search/05-04-SUMMARY.md`
- Task commit found: `b02d50a`
- Task commit found: `f99e0c5`
- Task commit found: `a4378e0`

## Next Phase Readiness

- MainWindow 后续计划可创建/复用 `SearchDialog`，设置当前 root，并连接 `result_activated` 实现分区展开、页面选择和状态栏反馈。
- SearchDialog 已保持 modeless 生命周期，不阻塞主窗口，也不会在结果激活后关闭。

---
*Phase: 05-tags-and-search*
*Completed: 2026-05-11*
