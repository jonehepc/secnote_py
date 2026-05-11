---
phase: 04-rich-text-editor
plan: 01
subsystem: testing
tags: [pyside6, qtextedit, rich-text, pytest, tdd]

requires:
  - phase: 04-rich-text-editor
    provides: Phase 04 上下文、UI 契约和测试运行环境准备
provides:
  - RichTextEditorWidget 的 EDIT-01~EDIT-11 RED 行为测试契约
  - MainWindow 富文本工具栏、编辑菜单、缩放和跨页面 undo 安全 RED 集成测试
  - Serializer 富文本 HTML round-trip 与缩放不序列化 characterization 测试
affects: [04-rich-text-editor, ui, testing, serializer]

tech-stack:
  added: []
  patterns:
    - PySide6 widget 测试通过 qapp fixture 与 QT_QPA_PLATFORM=offscreen 执行
    - TDD RED 任务以 pytest 非零退出且非语法错误作为成功验证
    - 富文本安全边界通过恶意剪贴板 HTML 断言锁定

key-files:
  created:
    - tests/ui/test_rich_text_editor.py
    - .planning/phases/04-rich-text-editor/04-01-SUMMARY.md
  modified:
    - tests/ui/test_main_window.py
    - tests/ui/test_navigation.py
    - tests/model/test_serializer.py
    - .gitignore

key-decisions:
  - "本计划仅建立测试契约，不修改 src/secnotepad 生产代码。"
  - "工作树内使用主项目 .venv 的本地符号链接运行计划指定命令，并将 .venv 符号链接加入忽略规则避免提交生成环境。"

patterns-established:
  - "富文本组件测试集中断言 RichTextEditorWidget 的动作、控件、信号和安全粘贴输出。"
  - "MainWindow 集成测试通过明确私有属性名锁定 Phase 04 UI 接入点。"
  - "Serializer characterization 测试只验证纯 JSON 字符串 round-trip，不依赖 QTextEdit HTML 标准化。"

requirements-completed: [EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, EDIT-06, EDIT-07, EDIT-08, EDIT-09, EDIT-10, EDIT-11]

duration: 7min
completed: 2026-05-10T03:17:03Z
---

# Phase 04 Plan 01: 富文本编辑器 RED 测试契约 Summary

**QTextEdit 富文本编辑的格式、安全粘贴、缩放、菜单集成和 HTML 持久化行为测试契约**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-10T03:10:52Z
- **Completed:** 2026-05-10T03:17:03Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- 创建 `RichTextEditorWidget` RED 行为测试，覆盖 EDIT-01~EDIT-11，包括字符格式、字体字号、颜色、对齐、列表、标题、缩进、撤销重做、安全粘贴和缩放不置脏。
- 补充 `MainWindow` RED 集成测试，锁定格式工具栏位置、未选页面禁用、编辑菜单路由、视图缩放入口和缩放不修改页面内容。
- 增加跨页面 undo 栈清理安全回归，防止上一页明文通过撤销恢复到当前页面。
- 增加 Serializer characterization 测试，确认富文本 HTML 字符串原样 round-trip，且 zoom/zoom_percent/scale 不进入序列化数据。

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建 RichTextEditorWidget RED 行为测试** - `f4c71d7` (test)
2. **Task 2: 添加 MainWindow 集成 RED 测试** - `1526bad` (test)
3. **Task 3: 添加富文本 HTML 持久化 characterization 测试** - `c87b31b` (test)

Additional deviation commit:

- `9c4e889` (fix): 忽略工作树内用于执行测试命令的 `.venv` 符号链接。

## Files Created/Modified

- `tests/ui/test_rich_text_editor.py` - 新增 RichTextEditorWidget 行为 RED 测试契约。
- `tests/ui/test_main_window.py` - 新增 `TestRichTextIntegration`，覆盖工具栏、编辑菜单和缩放集成。
- `tests/ui/test_navigation.py` - 新增页面切换清理 undo 栈且不置脏的安全回归测试。
- `tests/model/test_serializer.py` - 新增富文本 HTML round-trip 和缩放状态不序列化测试。
- `.gitignore` - 增加 `.venv` 忽略项以覆盖工作树符号链接。

## Decisions Made

- 本计划保持纯测试契约范围，未创建或修改 `src/secnotepad/` 生产代码。
- Serializer 测试明确断言纯 JSON round-trip，不把 QTextEdit 可能产生的 HTML 标准化纳入该层职责。
- 工作树执行环境缺少本地 `.venv` 时，使用主项目 `.venv` 的符号链接满足项目“测试使用虚拟环境”的约束。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 忽略工作树虚拟环境符号链接**
- **Found during:** Task 2（MainWindow 集成 RED 测试）
- **Issue:** 工作树中没有 `.venv`，为运行计划指定命令创建了指向主项目 `.venv` 的本地符号链接后，`.gitignore` 的 `.venv/` 未忽略符号链接，导致 `git status` 留下未跟踪项。
- **Fix:** 在 `.gitignore` 增加 `.venv`，保留原有 `.venv/`，避免提交生成环境或本地符号链接。
- **Files modified:** `.gitignore`
- **Verification:** 后续 `git status --short` 不再显示 `.venv` 未跟踪项；Task 3 pytest 通过。
- **Committed in:** `9c4e889`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** 仅修复测试执行环境的阻塞问题；未扩大生产代码范围。

## Issues Encountered

- 初始工作树缺少由并行任务生成的 plan 文件和本地 `.venv`；计划内容从用户提供的执行上下文读取，测试运行通过链接主项目 `.venv` 解决。
- Task 1/2 RED 验证按预期失败，失败来源为尚未实现的 `rich_text_editor` 模块和 `_rich_text_editor`、`_format_toolbar`、`_act_zoom_*` 等 Phase 04 接入点。

## Verification

- Task 1 RED: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py -q` 返回非 0，且无 `SyntaxError` / `IndentationError`。
- Task 2 RED: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window.py tests/ui/test_navigation.py -q` 返回非 0，且无 `SyntaxError` / `IndentationError`。
- Task 3 GREEN: `.venv/bin/python -m pytest tests/model/test_serializer.py::TestSerializerFromJson::test_rich_text_html_content_roundtrip tests/model/test_serializer.py::TestSerializerFromJson::test_zoom_state_not_serialized -q` 通过，结果 `2 passed`。
- Success criteria: `git log --oneline --grep="^test(04-01)"` 有 RED/characterization 测试提交；`git diff --name-only fe1c7ad..HEAD -- src/secnotepad/` 无输出。

## TDD Gate Compliance

- RED gate commit exists: `f4c71d7` and `1526bad` use `test(04-01)` and establish failing UI tests before implementation.
- GREEN/characterization commit exists: `c87b31b` adds Serializer regression tests that pass against existing behavior.
- No production implementation was added in this plan, matching the plan objective.

## Known Stubs

None. Stub-pattern scan only found existing `placeholder` terminology in UI/navigation tests for the intentional empty editor state.

## Threat Flags

None. This plan added tests for existing/planned UI and serializer boundaries only; no new runtime endpoint, auth path, file access pattern, or schema trust boundary was introduced.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 04 implementation plans can now use these tests as RED gates for `src/secnotepad/ui/rich_text_editor.py` and `MainWindow` integration.
- The safety-sensitive expectations for paste sanitization, no HTML checkbox, undo stack clearing, and zoom not entering content are explicitly locked by tests.

## Self-Check: PASSED

- Found created/modified files: `tests/ui/test_rich_text_editor.py`, `tests/ui/test_main_window.py`, `tests/ui/test_navigation.py`, `tests/model/test_serializer.py`, `.gitignore`, `.planning/phases/04-rich-text-editor/04-01-SUMMARY.md`.
- Found commits: `f4c71d7`, `1526bad`, `9c4e889`, `c87b31b`.

---
*Phase: 04-rich-text-editor*
*Completed: 2026-05-10T03:17:03Z*
