---
phase: 04-rich-text-editor
plan: 05
subsystem: ui
tags: [pyside6, qt-widgets, qtextedit, rich-text, menu-actions, zoom]

requires:
  - phase: 04-rich-text-editor
    provides: RichTextEditorWidget 与格式工具栏基础能力
provides:
  - MainWindow 右侧富文本编辑区集成
  - 编辑菜单撤销/重做/剪切/复制/粘贴路由
  - 视图菜单会话级缩放入口
affects: [rich-text-editor, navigation-system, ui-tests]

tech-stack:
  added: []
  patterns:
    - MainWindow 保留 _editor_preview 与 _editor_stack 兼容别名
    - 页面 HTML 通过 RichTextEditorWidget.load_html/to_html 同步
    - 编辑器显示缩放保持会话级状态，不进入 SNoteItem.content

key-files:
  created:
    - .planning/phases/04-rich-text-editor/04-05-SUMMARY.md
  modified:
    - src/secnotepad/ui/main_window.py
    - tests/ui/test_navigation.py

key-decisions:
  - "格式工具栏固定在右侧编辑区容器内，主文件工具栏仍只承载文件操作。"
  - "缩放操作仅调用 RichTextEditorWidget 的会话显示方法，不读取或写入页面 HTML。"
  - "中文输入回归测试改用 insertPlainText，避免 Qt offscreen QTest.keyClicks 对非 ASCII 文本触发底层断言。"

patterns-established:
  - "MainWindow 菜单 QAction 使用命名字段并保留 _edit_actions 列表兼容旧测试。"
  - "页面切换使用 load_html 清理 undo/redo 栈并阻断 content_changed 误置脏。"

requirements-completed: [EDIT-01, EDIT-09, EDIT-10, EDIT-11]

duration: 9min
completed: 2026-05-10T03:58:56Z
---

# Phase 04 Plan 05: MainWindow 富文本集成 Summary

**MainWindow 右侧 RichTextEditorWidget 集成，编辑菜单路由与会话级缩放菜单可用且不污染页面 HTML**

## Performance

- **Duration:** 9min
- **Started:** 2026-05-10T03:50:02Z
- **Completed:** 2026-05-10T03:58:56Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 将 `RichTextEditorWidget` 接入 MainWindow 右侧编辑区，并保留 `_editor_preview` / `_editor_stack` 兼容接口。
- 页面切换通过 `load_html()` 加载 HTML，避免触发 dirty，并清空 undo/redo 栈以防跨页面明文恢复。
- 编辑菜单的撤销、重做、剪切、复制、粘贴改为路由到当前富文本编辑器，并根据页面/文档状态启用。
- 视图菜单新增放大、缩小、重置缩放动作，状态栏显示当前百分比，缩放状态不写入页面内容。

## Task Commits

Each task was committed atomically:

1. **Task 1: 接入右侧富文本编辑区和页面 HTML 同步** - `006ca42` (feat)
2. **Task 2: 连接编辑菜单动作到富文本编辑器** - `a6be6cb` (feat)
3. **Task 3: 添加视图缩放菜单并验证不置脏** - `c8c54f4` (feat)

**Plan metadata:** 本 SUMMARY 文件提交见最终 docs commit。

## Files Created/Modified

- `src/secnotepad/ui/main_window.py` - 集成 RichTextEditorWidget，新增编辑菜单路由、状态同步与视图缩放动作。
- `tests/ui/test_navigation.py` - 将中文富文本输入回归测试从 `QTest.keyClicks` 调整为 `insertPlainText`，避免 offscreen 环境 Qt 非 ASCII key 断言。
- `.planning/phases/04-rich-text-editor/04-05-SUMMARY.md` - 本计划执行总结。

## Verification

- `QT_QPA_PLATFORM=offscreen PYTHONPATH="/home/jone/projects/secnotepad/.claude/worktrees/agent-af336db39316ed69f" /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/.claude/worktrees/agent-af336db39316ed69f/tests/ui/test_main_window.py /home/jone/projects/secnotepad/.claude/worktrees/agent-af336db39316ed69f/tests/ui/test_navigation.py -q`
- Result: `153 passed in 6.44s`

## Decisions Made

- 格式工具栏固定在右侧编辑区容器内，主文件工具栏不加入任何富文本格式动作。
- 缩放 handler 只调用 `_rich_text_editor.zoom_in()` / `zoom_out()` / `reset_zoom()`，不访问 `SNoteItem.content`。
- 对 Qt offscreen 测试环境中中文 `QTest.keyClicks` 崩溃，采用 `insertPlainText` 保留测试意图并避免底层断言。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修复 Qt offscreen 非 ASCII keyClicks 崩溃**
- **Found during:** Task 3 (添加视图缩放菜单并验证不置脏)
- **Issue:** `test_switching_pages_clears_undo_stack_and_does_not_mark_dirty` 使用 `QTest.keyClicks(editor, "第一页已编辑明文")` 在 offscreen 环境触发 Qt `qasciikey.cpp` 断言并中止进程。
- **Fix:** 将该测试中的中文输入改为 `editor.insertPlainText("第一页已编辑明文")`，继续验证同一 undo/dirty 安全边界。
- **Files modified:** `tests/ui/test_navigation.py`
- **Verification:** Task 3 定向测试通过；完整 UI 回归 `153 passed`。
- **Committed in:** `c8c54f4`

**2. [Rule 2 - Missing Critical] 保证无页面时编辑菜单全部禁用并安全 no-op**
- **Found during:** Task 2 (连接编辑菜单动作到富文本编辑器)
- **Issue:** 菜单快捷键属于 MainWindow 与编辑器之间的事件边界，必须防止无页面状态下快捷键误改数据。
- **Fix:** 新增 `_update_edit_action_states()`，在 placeholder/页面切换时统一更新撤销、重做、剪切、复制、粘贴状态；无当前页面时全部禁用。
- **Files modified:** `src/secnotepad/ui/main_window.py`
- **Verification:** `test_editor_menu_actions_route_to_rich_text_editor` 与完整 UI 回归通过。
- **Committed in:** `a6be6cb`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** 均为实现计划安全边界与测试稳定性所需，无功能范围扩张。

## Issues Encountered

- 项目 worktree 内没有 `.venv`，按用户记忆要求改用主项目虚拟环境 `/home/jone/projects/secnotepad/.venv/bin/python` 并设置 worktree `PYTHONPATH`。
- PySide6 `QMenuBar.addMenu(str)` 在当前 offscreen 测试环境下返回的菜单对象会被删除；改为显式创建 `QMenu(..., self)` 后加入菜单栏，保证测试和运行时对象生命周期稳定。

## Known Stubs

None - 扫描到的 `placeholder` 均为既定空状态 UI，不是未接线数据源或阻塞目标的 stub。

## Threat Flags

None - 本计划未新增网络端点、认证路径、文件访问模式或跨信任边界 schema 变更。

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- MainWindow 已具备可用富文本编辑入口，后续 Phase 04 可继续围绕富文本行为和真实 GUI 验收收敛。
- Phase 05 标签与搜索可依赖 `SNoteItem.content` 中已持续同步的 HTML 内容。

## Self-Check: PASSED

- Verified modified files exist: `src/secnotepad/ui/main_window.py`, `tests/ui/test_navigation.py`, `.planning/phases/04-rich-text-editor/04-05-SUMMARY.md`.
- Verified task commits exist: `006ca42`, `a6be6cb`, `c8c54f4`.
- Verified no shared orchestrator artifacts (`STATE.md`, `ROADMAP.md`) were modified by this executor.

---
*Phase: 04-rich-text-editor*
*Completed: 2026-05-10T03:58:56Z*
