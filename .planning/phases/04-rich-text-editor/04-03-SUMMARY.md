---
phase: 04-rich-text-editor
plan: 03
subsystem: ui
tags: [pyside6, qt, qtextedit, rich-text, qtextblockformat, qtextlistformat]

requires:
  - phase: 04-rich-text-editor/04-02
    provides: RichTextEditorWidget、字符级格式工具栏和基础 QTextEdit 封装
provides:
  - 段落样式下拉框，使用 QTextBlockFormat.headingLevel 应用 H1-H6 与正文
  - 左对齐、居中、右对齐、两端对齐互斥 QActionGroup
  - 无序列表、有序列表、普通文本待办列表和增减缩进动作
affects: [04-rich-text-editor, rich-text-editor, main-window-integration]

tech-stack:
  added: []
  patterns:
    - QTextCursor beginEditBlock/endEditBlock 包裹段落、列表和缩进修改
    - QActionGroup 管理互斥段落对齐状态
    - cursorPositionChanged 同步段落样式与对齐按钮状态

key-files:
  created:
    - .planning/phases/04-rich-text-editor/04-03-SUMMARY.md
  modified:
    - src/secnotepad/ui/rich_text_editor.py

key-decisions:
  - "标题使用 QTextBlockFormat.headingLevel 段落语义，不用字号或粗体模拟。"
  - "待办列表保持为普通文本 `☐ ` 前缀，不创建 HTML checkbox/input。"
  - "减少缩进对 block 使用 max(0, current + delta)，对列表保持 Qt 支持的最小缩进 1。"

patterns-established:
  - "段落级格式通过 QTextCursor 和 block/list format 修改当前段落或选区覆盖段落。"
  - "格式工具栏状态使用 _syncing_toolbar 防止同步信号回写。"

requirements-completed: [EDIT-05, EDIT-06, EDIT-07, EDIT-08]

duration: 5min
completed: 2026-05-10T03:37:00Z
---

# Phase 04 Plan 03: 段落级富文本格式 Summary

**QTextEdit 段落工具栏支持语义标题、互斥对齐、Qt 原生列表、普通文本待办和安全缩进控制**

## Performance

- **Duration:** 5min
- **Started:** 2026-05-10T03:32:26Z
- **Completed:** 2026-05-10T03:37:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- 新增“正文、H1-H6”段落样式下拉框行为，H1-H6 通过 `QTextBlockFormat.setHeadingLevel()` 写入 block 语义。
- 新增左对齐、居中、右对齐、两端对齐四个 checkable QAction，并由 exclusive `QActionGroup` 管理互斥状态。
- 新增无序列表、有序列表、普通文本待办列表和增减缩进动作，列表使用 `QTextListFormat`，待办只插入 `☐ ` 文本。
- 连接 `cursorPositionChanged` 同步当前 block heading level 与 alignment 到工具栏状态。

## Task Commits

Each task was committed atomically:

1. **Task 1: 实现标题和段落对齐** - `e56a716` (feat)
2. **Task 2: 实现列表、待办文本和缩进** - `db40e88` (feat)

**Plan metadata:** 本 SUMMARY 将单独提交。

## Files Created/Modified

- `src/secnotepad/ui/rich_text_editor.py` - 增加段落样式、对齐、列表、待办和缩进工具栏动作及对应 QTextCursor/QTextEdit 行为。
- `.planning/phases/04-rich-text-editor/04-03-SUMMARY.md` - 记录本计划执行结果、验证命令和提交清单。

## Verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_alignment_actions_are_exclusive tests/ui/test_rich_text_editor.py::test_list_and_checklist_actions tests/ui/test_rich_text_editor.py::test_heading_levels tests/ui/test_rich_text_editor.py::test_indent_outdent_actions -q` — 4 passed
- Acceptance grep gates passed for `setHeadingLevel`, `QActionGroup`, `setExclusive(True)`, `AlignJustify`, `cursorPositionChanged.connect`, `QTextListFormat`, `ListDisc`, `ListDecimal`, `☐ `, absence of production `checkbox`, and multiple `beginEditBlock` calls.

## Decisions Made

- 标题按计划使用 Qt block heading 语义，避免字符级样式伪装。
- 待办列表按 D-73/D-75 作为普通文本前缀实现，不引入可交互表单控件。
- 为兼容现有测试命名，同时暴露 `action_numbered_list`/`action_indent_more` 等计划接口与 `action_ordered_list`/`action_indent` 等既有测试别名。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 创建项目虚拟环境并安装测试依赖**
- **Found during:** Task 1 RED 验证
- **Issue:** `.venv/bin/python` 不存在，计划指定的测试命令无法运行。
- **Fix:** 使用项目虚拟环境创建 `.venv` 并安装 editable 项目与 pytest。
- **Files modified:** 未修改受跟踪文件；虚拟环境未纳入提交。
- **Verification:** 后续所有指定 pytest 命令均可在 `.venv` 中运行。
- **Committed in:** 不适用（环境准备，不提交生成目录）。

---

**Total deviations:** 1 auto-fixed (Rule 3 blocking)
**Impact on plan:** 仅恢复计划验证环境；未改变产品范围或架构。

## Issues Encountered

- 初始 RED 测试按预期失败：缺少段落对齐 action、heading level 未应用、缺少列表和缩进 action。随后 GREEN 实现后对应测试通过。

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RichTextEditorWidget 已具备 EDIT-05~EDIT-08 的段落级格式能力，可供后续 MainWindow 集成任务启用。
- 后续计划可继续接入撤销/重做、剪切/复制/粘贴和缩放菜单行为。

## Self-Check: PASSED

- FOUND: `src/secnotepad/ui/rich_text_editor.py`
- FOUND: `.planning/phases/04-rich-text-editor/04-03-SUMMARY.md`
- FOUND: `e56a716`
- FOUND: `db40e88`

---
*Phase: 04-rich-text-editor*
*Completed: 2026-05-10*
