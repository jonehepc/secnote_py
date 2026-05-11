---
phase: 05-tags-and-search
plan: 02
subsystem: ui
tags: [pyside6, qt-widgets, tags, qcompleter, flow-layout, pytest-qt]

requires:
  - phase: 04-rich-text-editor
    provides: 右侧富文本编辑区和 UI 回归测试模式
  - phase: 05-tags-and-search
    provides: 标签与搜索 UI 契约、标签输入规则和补全边界
provides:
  - 可复用 TagBarWidget，提供标签 chip 展示、添加入口、输入校验、补全和移除意图信号
  - 标签控件 UI 行为测试，覆盖渲染、校验、补全、禁用状态和换行防溢出
  - MainWindow 后续集成所需的 tag_added/tag_removed 信号契约
affects: [phase-05-tags-and-search, main-window-tag-integration, tag-search]

tech-stack:
  added: []
  patterns:
    - PySide6 QWidget 组合组件
    - QCompleter + QStringListModel 大小写不敏感补全
    - 自定义 FlowLayout 支持标签 chip 换行

key-files:
  created:
    - src/secnotepad/ui/tag_bar_widget.py
    - tests/ui/test_tag_bar_widget.py
  modified: []

key-decisions:
  - "TagBarWidget 只发出 add/remove 意图信号，不直接修改 SNoteItem、HTML content 或 dirty 状态。"
  - "使用 Qt 官方 QCompleter + QStringListModel 提供当前笔记本标签补全，候选文本保留原始显示形式。"
  - "标签 chip 容器使用 FlowLayout/heightForWidth 实现换行，避免横向撑破右侧编辑区。"

patterns-established:
  - "标签 UI 组件边界：组件负责展示、校验和信号，MainWindow 负责数据写入和 mark_dirty。"
  - "标签输入规则：strip 首尾空白，保留内部大小写、中文、空格和符号，casefold 判断当前页面重复。"

requirements-completed: [TAG-01, TAG-02, TAG-03]

duration: 18min
completed: 2026-05-11
---

# Phase 05 Plan 02: TagBarWidget 组件 Summary

**可复用 PySide6 标签 chip 栏，具备输入校验、大小写不敏感补全、换行防溢出和 add/remove 信号边界**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-11T09:45:00Z
- **Completed:** 2026-05-11T10:03:27Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 新增 `TagBarWidget`，可显示多个标签 chip、无标签空态、添加输入框和 `添加标签` 按钮。
- 实现标签输入校验：空白、超过 32 字符、当前页面 casefold 重复均拒绝并显示 UI-SPEC 文案；合法输入 trim 后通过 `tag_added(str)` 发出。
- 实现 chip 移除入口 `×`，tooltip 为 `移除标签：{tag}`，通过 `tag_removed(str)` 发出原始标签。
- 使用 `QCompleter` + `QStringListModel` 提供大小写不敏感补全，并通过 `FlowLayout.heightForWidth()` 覆盖多标签换行/非横向溢出。
- 新增 UI 行为测试并回归富文本编辑器测试，确认标签控件不破坏 Phase 04 编辑器能力。

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建 TagBarWidget 行为测试** - `5b3ff29` (test)
2. **Task 2: 实现 TagBarWidget 组件** - `70167cb` (feat)
3. **Task 3: 组件回归与安全边界检查** - `0c1a0a8` (test)

**Plan metadata:** 本 SUMMARY 提交见最终 docs commit。

## Files Created/Modified

- `src/secnotepad/ui/tag_bar_widget.py` - 新增标签栏组件、FlowLayout、输入校验、补全和 add/remove 信号。
- `tests/ui/test_tag_bar_widget.py` - 新增 UI 行为测试，覆盖渲染、刷新无信号、添加、校验、移除、补全、禁用状态和换行防溢出。

## Verification

- `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-a48392ce3c355dd95/tests/ui/test_tag_bar_widget.py -x` — 8 passed
- `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-a48392ce3c355dd95/tests/ui/test_tag_bar_widget.py /home/jone/projects/secnotepad/.claude/worktrees/agent-a48392ce3c355dd95/tests/ui/test_rich_text_editor.py -x` — 21 passed

## Decisions Made

- `TagBarWidget` 不导入或修改 `SNoteItem`，不写入正文 HTML，不调用 `mark_dirty()`；后续 MainWindow 集成负责持久化和 dirty 语义。
- 补全候选使用 `QStringListModel` 排序并由 `QCompleter` 处理大小写不敏感匹配，避免自定义浮层。
- 标签 chip 布局采用自定义 `FlowLayout`，通过 `heightForWidth()` 让父容器在窄宽度下换行。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 使用项目主虚拟环境运行测试**
- **Found during:** Task 1（创建 TagBarWidget 行为测试）
- **Issue:** worktree 内不存在 `.venv/bin/python`，直接运行计划命令会因解释器路径缺失失败。
- **Fix:** 按项目记忆要求使用 `/home/jone/projects/secnotepad/.venv/bin/python`，同时保持 pytest rootdir 指向 worktree。
- **Files modified:** 无。
- **Verification:** RED 阶段因缺少 `TagBarWidget` 导入失败，GREEN 和最终回归均通过。
- **Committed in:** 不涉及代码提交。

**2. [Rule 1 - Bug] 避免 offscreen 环境中 QTest.keyClicks 中文输入崩溃**
- **Found during:** Task 2（实现 TagBarWidget 组件）
- **Issue:** 使用 `QTest.keyClicks()` 输入中文字符串时 offscreen 测试进程中止，阻塞组件行为验证。
- **Fix:** 测试 helper 改为 `QLineEdit.setText()` 填入输入内容，再使用回车或按钮触发添加行为；保留对中文、空格和符号 payload 的断言。
- **Files modified:** `tests/ui/test_tag_bar_widget.py`
- **Verification:** `tests/ui/test_tag_bar_widget.py` 8 passed，联合富文本回归 21 passed。
- **Committed in:** `70167cb`

---

**Total deviations:** 2 auto-fixed（1 blocking，1 bug）
**Impact on plan:** 均为完成计划验证所需；组件功能范围未扩大。

## Issues Encountered

- 首次 RED 运行按 worktree `.venv` 路径失败；改用项目虚拟环境后正确进入 RED 导入失败状态。
- offscreen Qt 对中文 keyClicks 不稳定；测试改为直接设置输入框文本后验证同一业务路径。

## Known Stubs

None - 未发现阻碍目标达成的 stub、TODO、FIXME、占位数据源或硬编码空 UI 数据流。

## Threat Flags

无新增计划外安全表面。新增组件仅处理本地 UI 输入和 Qt 信号，不新增网络端点、文件访问、认证路径或信任边界外 schema 变更。

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 03 可将 `TagBarWidget` 挂到右侧编辑区顶部，并连接 `tag_added` / `tag_removed` 到当前页面 `SNoteItem.tags` 与 `mark_dirty()`。
- 后续集成应从当前笔记本收集所有页面标签并调用 `set_available_tags()`，页面切换时调用 `set_tags()`。

## Self-Check: PASSED

- Created files exist: `src/secnotepad/ui/tag_bar_widget.py`, `tests/ui/test_tag_bar_widget.py`
- Task commits found: `5b3ff29`, `70167cb`, `0c1a0a8`
- Verification commands passed: tag widget tests 8/8，联合 UI 回归 21/21

---
*Phase: 05-tags-and-search*
*Completed: 2026-05-11*
