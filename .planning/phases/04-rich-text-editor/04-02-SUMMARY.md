---
phase: 04-rich-text-editor
plan: 02
subsystem: ui
tags: [pyside6, qt, qtextedit, rich-text, qtextcharformat]

requires:
  - phase: 04-00
    provides: 富文本编辑器 RED 测试
  - phase: 04-01
    provides: 富文本编辑器测试导入修复
provides:
  - RichTextEditorWidget 与 SafeRichTextEdit 基础组件
  - 固定不可浮动的局部格式工具栏
  - QTextEdit HTML 加载、输出与 content_changed 同步
  - 加粗、斜体、下划线、删除线、字体、字号、文字颜色和背景色工具栏动作
affects: [04-03, 04-04, 04-05, rich-text-editor, main-window-integration]

tech-stack:
  added: [PySide6 6.11.0, pytest 9.0.3]
  patterns: [QTextEdit wrapper component, QTextCharFormat merge formatting, signal-blocked HTML load]

key-files:
  created:
    - src/secnotepad/ui/rich_text_editor.py
  modified:
    - tests/ui/test_rich_text_editor.py

key-decisions:
  - "富文本字符格式统一通过 QTextCharFormat 和 QTextEdit.mergeCurrentCharFormat 应用，避免手写 HTML。"
  - "load_html 阻断 QTextEdit 信号并清理 document modified/undo-redo 栈，避免页面加载导致 dirty 或跨页面撤销数据残留。"
  - "测试中使用 insertPlainText 替代 QTest.keyClicks 输入中文，规避 offscreen/Qt 输入法导致的运行时崩溃。"

patterns-established:
  - "RichTextEditorWidget 封装编辑器、局部格式工具栏与字符格式 action，后续 MainWindow 只需消费组件接口。"
  - "状态同步使用 _syncing_toolbar 锁与 blockSignals，避免控件状态更新反向触发格式应用。"

requirements-completed: [EDIT-01, EDIT-02, EDIT-03, EDIT-04]

duration: 1h 34m
completed: 2026-05-10
---

# Phase 04 Plan 02: 富文本字符格式编辑器 Summary

**基于 QTextEdit 的 RichTextEditorWidget，提供 HTML 内容同步、固定格式工具栏和字符级富文本格式动作。**

## Performance

- **Duration:** 1h 34m
- **Started:** 2026-05-10T03:20:10Z
- **Completed:** 2026-05-10T04:54:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- 新增 `SafeRichTextEdit(QTextEdit)` 与 `RichTextEditorWidget(QWidget)`，暴露 `editor()`、`format_toolbar()`、`set_editor_enabled()`、`load_html()`、`to_html()`、`set_status_callback()` 和 `zoom_percent()`。
- `load_html()` 使用 `blockSignals(True)` 加载 HTML，随后执行 `document().setModified(False)` 与 `document().clearUndoRedoStacks()`，不会触发 `content_changed`。
- 工具栏按 UI-SPEC 基础顺序创建段落样式占位、`QFontComboBox`、固定字号下拉、加粗/斜体/下划线/删除线、文字颜色与背景色 action。
- 字符格式通过 `QTextCharFormat` + `mergeCurrentCharFormat` 应用到当前选区或后续输入；颜色选择使用系统 `QColorDialog.getColor(parent=self)`。
- 修正 RED 测试中的 `content_changed` 信号签名与 offscreen 中文输入方式，使 EDIT-01~EDIT-04 组件测试可稳定运行。

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建 RichTextEditorWidget 结构和 HTML 同步基础** - `481be74` (feat)
2. **Task 2: 实现字符格式、字体字号与颜色工具栏** - `3a616a6` (feat)

**Plan metadata:** 本文件将在单独 docs commit 中提交。

## Files Created/Modified

- `src/secnotepad/ui/rich_text_editor.py` - 新增富文本编辑组件、局部格式工具栏、HTML 加载/输出、字符格式 action 与状态同步。
- `tests/ui/test_rich_text_editor.py` - 修正组件测试中 `content_changed` 信号参数处理，并将中文输入从 `QTest.keyClicks` 调整为 `insertPlainText`。

## Decisions Made

- 沿用 Qt 文档模型：所有字符级格式均通过 `QTextCharFormat` 合并到 `QTextEdit`，不拼接 HTML 字符串。
- 颜色按钮只调用系统 `QColorDialog` 并应用 `QColor` 到前景/背景格式，不引入第三方图标或自定义调色板。
- 在 offscreen 测试环境中，中文输入采用直接编辑器 API，保持测试目标为“真实内容变化触发信号”，避免平台输入法崩溃干扰。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修正 `content_changed` 测试槽签名**
- **Found during:** Task 1（创建 RichTextEditorWidget 结构和 HTML 同步基础）
- **Issue:** 计划要求 `content_changed = Signal(str)`，但 RED 测试连接了无参数 lambda；真实编辑时 PySide 会向槽传入 HTML 字符串，导致运行时异常。
- **Fix:** 将测试槽改为 `lambda _html: ...`，与公开信号签名一致。
- **Files modified:** `tests/ui/test_rich_text_editor.py`
- **Verification:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_editing_page_updates_note_html_and_dirty -q`
- **Committed in:** `481be74`

**2. [Rule 1 - Bug] 修正 offscreen 中文键盘输入崩溃**
- **Found during:** Task 1（创建 RichTextEditorWidget 结构和 HTML 同步基础）
- **Issue:** `QTest.keyClicks(editor, "新内容")` 在当前 PySide6/offscreen 环境中触发 Qt 运行时中止，不是组件行为失败。
- **Fix:** 测试改用 `editor.insertPlainText("新内容")` 触发真实 `textChanged` 路径并验证 HTML 输出。
- **Files modified:** `tests/ui/test_rich_text_editor.py`
- **Verification:** 同上，Task 1 测试通过。
- **Committed in:** `481be74`

**3. [Rule 1 - Bug] 避免 `QTextCharFormat.fontFamily()` 在当前 PySide6 环境中崩溃**
- **Found during:** Task 2（实现字符格式、字体字号与颜色工具栏）
- **Issue:** 格式同步中直接调用 `char_format.fontFamily()` 会在 currentCharFormatChanged 路径触发段错误。
- **Fix:** 改为 `char_format.font().family()`，并在更新 `QFontComboBox` 时阻断控件信号，避免递归格式应用。
- **Files modified:** `src/secnotepad/ui/rich_text_editor.py`
- **Verification:** `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_character_format_actions tests/ui/test_rich_text_editor.py::test_font_family_and_size_controls tests/ui/test_rich_text_editor.py::test_text_and_background_color_actions -q`
- **Committed in:** `3a616a6`

---

**Total deviations:** 3 auto-fixed (3 Rule 1 bugs)
**Impact on plan:** 修复均为测试稳定性或运行时正确性要求，没有扩大功能范围。

## Issues Encountered

- 当前 `tests/ui/test_rich_text_editor.py` 包含 04-03 及后续计划的 RED 测试（对齐、列表、标题、缩进、撤销/重做、粘贴净化、缩放）。本计划只要求并验证 EDIT-01~EDIT-04；全文件运行仍会因后续功能未实现而失败，属于后续计划范围。

## Known Stubs

- `src/secnotepad/ui/rich_text_editor.py`：`SafeRichTextEdit` 当前仅继承 `QTextEdit`，粘贴/资源安全边界由后续计划 04-04 实现；本计划仅需要类存在与基础编辑能力。
- `src/secnotepad/ui/rich_text_editor.py`：`zoom_percent()` 当前返回 `100`，会话级缩放由后续计划实现；不影响本计划 EDIT-01~EDIT-04。
- `src/secnotepad/ui/rich_text_editor.py`：`paragraph_style_combo` 已按工具栏顺序创建，但标题/段落逻辑由 04-03 实现。

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 04-03 可在现有 `paragraph_style_combo` 和工具栏结构上继续实现标题、对齐、列表与缩进。
- 04-04 可扩展 `SafeRichTextEdit` 的粘贴安全边界，并补齐撤销/重做、剪切/复制/粘贴和缩放能力。
- 04-05 可将 `RichTextEditorWidget` 接入 `MainWindow`，替换当前右侧裸 `QTextEdit`。

## Self-Check: PASSED

- Found `src/secnotepad/ui/rich_text_editor.py`.
- Found task commit `481be74`.
- Found task commit `3a616a6`.
- Verified EDIT-01~EDIT-04 targeted tests pass.

---
*Phase: 04-rich-text-editor*
*Completed: 2026-05-10*
