---
phase: 05-tags-and-search
plan: 03
subsystem: ui
tags: [pyside6, qt-widgets, tags, main-window, serializer]

requires:
  - phase: 05-tags-and-search
    provides: 05-02 TagBarWidget 组件契约与 tag_added/tag_removed 信号
provides:
  - MainWindow 右侧编辑区顶部标签栏集成
  - 当前页面 SNoteItem.tags 添加、移除、展示和 dirty 语义
  - 当前笔记本标签补全候选刷新与序列化回归验证
affects: [phase-05-tags-and-search, phase-06-ui-polish]

tech-stack:
  added: []
  patterns:
    - MainWindow 通过 TagBarWidget 信号修改当前 SNoteItem.tags
    - 标签补全候选每次从当前 _root_item 树遍历收集，大小写去重并保留首次文本
    - 标签元数据只进入 Serializer JSON，不写入富文本 HTML 正文

key-files:
  created:
    - tests/ui/test_main_window_tags.py
  modified:
    - src/secnotepad/ui/main_window.py

key-decisions:
  - "标签栏固定插入 editor_container 布局首位，保持 标签栏 → 格式工具栏 → 正文/placeholder 顺序。"
  - "MainWindow 在 handler 中复核 trim、长度和 casefold 重复，不能只信任 TagBarWidget 校验。"
  - "补全候选不做跨会话缓存，每次从当前笔记本 root 树收集，避免旧会话标签泄漏。"

patterns-established:
  - "TagBarWidget 只发出意图信号，MainWindow 负责真实数据写入和 dirty 状态。"
  - "标签持久化沿用 SNoteItem.tags → Serializer.to_json → FileService.save 的既有加密保存链路。"

requirements-completed: [TAG-01, TAG-02, TAG-03]

duration: 23min
completed: 2026-05-11
---

# Phase 05 Plan 03: MainWindow 标签集成 Summary

**右侧编辑区标签栏连接当前页面 SNoteItem.tags，支持添加、移除、补全刷新、dirty 标记和加密保存前 JSON 持久化链路。**

## Performance

- **Duration:** 23 min
- **Started:** 2026-05-11T10:08:35Z
- **Completed:** 2026-05-11T10:31:44Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 在 `MainWindow` 右侧编辑容器中集成 `TagBarWidget`，布局顺序满足 D-81：标签栏、格式工具栏、正文/placeholder。
- 实现当前页面标签 add/remove handler：成功变更写入 `SNoteItem.tags`、刷新标签栏和补全候选、调用 `mark_dirty()` 并显示中文状态栏反馈。
- 加固 MainWindow 侧输入防御：再次执行 trim、空值、32 字符长度和 casefold 重复检查，满足威胁模型 T-05-03-01/T-05-03-02。
- 新增 MainWindow 标签集成测试，覆盖展示、添加、重复忽略、移除、placeholder 禁用、页面列表单列标题和序列化 round-trip。
- 验证标签只通过 `Serializer.to_json()` 进入既有 `.secnote` 加密保存前 JSON 链路，不新增明文标签文件，不写入 `note.content`。

## Task Commits

Each task was committed atomically:

1. **Task 1: 编写 MainWindow 标签集成测试**
   - `5b5d8b9` test(05-03): add failing MainWindow tag integration tests
2. **Task 2: 集成标签栏到右侧编辑区和当前页面**
   - `f90f357` feat(05-03): integrate tag bar with current page
3. **Task 3: 标签持久化链路与回归验证**
   - `77f045b` test(05-03): verify tag persistence regressions
   - `60f73b8` test(05-03): harden tag regression test isolation

**Plan metadata:** committed after summary creation.

_Note: Tasks 1 and 2 followed the requested TDD RED/GREEN flow; Task 3 added regression coverage and a small test-isolation hardening commit._

## Files Created/Modified

- `tests/ui/test_main_window_tags.py` - MainWindow 标签集成、持久化链路和页面列表回归测试。
- `src/secnotepad/ui/main_window.py` - `TagBarWidget` 导入、布局插入、信号连接、当前页面标签同步、补全候选收集和 dirty 语义。

## Decisions Made

- 标签栏作为编辑区 UI 元素插入 `editor_container.layout()` 的第一个 widget，而不是放入页面列表或富文本 HTML 内容中，确保 D-81/D-83/T-05-03-04。
- `TagBarWidget` 保持组件级校验和信号职责，MainWindow handler 再做安全复核并负责写入 `SNoteItem.tags`，确保 UI payload 进入数据模型前有边界检查。
- `_collect_available_tags()` 不缓存历史候选，始终遍历当前 `_root_item` 下所有 note tags，避免打开/新建笔记本后跨会话标签泄漏。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修复标签测试窗口清理影响后续 Ctrl+N 导航测试**
- **Found during:** Task 3（标签持久化链路与回归验证）
- **Issue:** 新增标签测试在同一 pytest 进程中先运行后，Qt 延迟删除事件未及时处理，后续 `tests/ui/test_navigation.py::test_ctrl_n_creates_page_when_page_list_focused` 可能焦点分发失败。
- **Fix:** 在标签测试 fixture teardown 中关闭并 `deleteLater()` 后调用 `qapp.processEvents()`，确保测试窗口清理完成；同时保持当前笔记本补全候选重置测试 deterministic。
- **Files modified:** `tests/ui/test_main_window_tags.py`
- **Verification:** `QT_QPA_PLATFORM=offscreen PYTHONPATH=<worktree> /home/jone/projects/secnotepad/.venv/bin/python -m pytest tests/ui/test_main_window_tags.py tests/ui/test_navigation.py tests/model/test_serializer.py -x` 通过 123 项测试。
- **Committed in:** `60f73b8`

---

**Total deviations:** 1 auto-fixed（1 bug）
**Impact on plan:** 修复仅限新增测试的 Qt 清理隔离问题，保证计划要求的导航回归可稳定通过；无功能范围扩张。

## Issues Encountered

- 工作树内没有独立 `.venv`，按项目记忆和既有环境使用主项目虚拟环境 `/home/jone/projects/secnotepad/.venv/bin/python`，并设置 `PYTHONPATH` 指向当前 worktree 以测试 worktree 代码。
- 初次将完整回归命令误以后台方式启动，发现多个 pytest 进程因 Qt 对话框/焦点状态停滞后停止这些重复进程；随后改为修正测试隔离并用前台命令完成验证。

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - stub scan only found existing placeholder state handling and constructor defaults; no placeholder/mock data blocks plan completion.

## Threat Flags

None - no new network endpoints, auth paths, file access patterns, schema changes, or new trust boundaries beyond the plan threat model.

## Verification

- `QT_QPA_PLATFORM=offscreen PYTHONPATH=/home/jone/projects/secnotepad/.claude/worktrees/agent-a5be975d2ea21c21e /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-a5be975d2ea21c21e/tests/ui/test_main_window_tags.py -x` — passed during Task 2（8 passed before Task 3 additions）
- `QT_QPA_PLATFORM=offscreen PYTHONPATH=/home/jone/projects/secnotepad/.claude/worktrees/agent-a5be975d2ea21c21e /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-a5be975d2ea21c21e/tests/ui/test_main_window_tags.py /home/jone/projects/secnotepad/.claude/worktrees/agent-a5be975d2ea21c21e/tests/ui/test_navigation.py /home/jone/projects/secnotepad/.claude/worktrees/agent-a5be975d2ea21c21e/tests/model/test_serializer.py -x` — passed（123 passed）
- Acceptance grep checks passed for `_tag_bar` coverage, add/remove dirty/status assertions, `DisplayRole`, `Serializer.to_json` / `Serializer.from_json`, and no `note.content`/tag mixing in MainWindow.

## TDD Gate Compliance

- RED: `5b5d8b9` added failing MainWindow tag integration tests; failure observed as missing `MainWindow._tag_bar` before implementation.
- GREEN: `f90f357` integrated `TagBarWidget` and made tag integration tests pass.
- REFACTOR/Regression: `77f045b` and `60f73b8` added persistence/regression coverage and test isolation hardening.

## Next Phase Readiness

- Plan 05-03 is ready for downstream Phase 05 search work: pages now expose current tags in the editor area and persist tags in the existing notebook JSON model.
- Search plans can consume `SNoteItem.tags` directly from the in-memory tree and rely on `PageListModel` remaining title-only.

## Self-Check: PASSED

- Created file exists: `tests/ui/test_main_window_tags.py`
- Modified file exists: `src/secnotepad/ui/main_window.py`
- Summary file exists: `.planning/phases/05-tags-and-search/05-03-SUMMARY.md`
- Task commits found: `5b5d8b9`, `f90f357`, `77f045b`, `60f73b8`
- Final verification passed: 123 tests

---
*Phase: 05-tags-and-search*
*Completed: 2026-05-11*
