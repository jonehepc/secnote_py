---
phase: 04-rich-text-editor
plan: 04
subsystem: ui
tags: [pyside6, qt, qtextedit, clipboard, rich-text, zoom]

requires:
  - phase: 04-rich-text-editor/04-03
    provides: RichTextEditorWidget、SafeRichTextEdit、格式工具栏、段落格式、列表和缩进基础
provides:
  - RichTextEditorWidget 撤销、重做、剪切、复制、粘贴与 can_paste 公共 API
  - SafeRichTextEdit 剪贴板 MIME 安全边界，阻断图片、外部资源、script、event handler 和 javascript URL
  - 会话级 zoom_in、zoom_out、reset_zoom 和 zoom_percent，不写入 HTML
  - MainWindow 后续可绑定的 undo/redo/copy 可用性信号与状态消息信号
affects: [04-rich-text-editor, main-window-integration, edit-menu, view-menu]

tech-stack:
  added: []
  patterns:
    - QTextEdit 标准 undo/redo/cut/copy/paste 由组件 public wrapper 转发
    - QTextDocument undoAvailable/redoAvailable 与 QTextEdit copyAvailable 直接转发为组件信号
    - SafeRichTextEdit 在 canInsertFromMimeData/insertFromMimeData 边界净化不可信剪贴板 HTML
    - QTextEdit zoomIn/zoomOut 只配合内存 _zoom_steps 维护会话显示缩放

key-files:
  created:
    - .planning/phases/04-rich-text-editor/04-04-SUMMARY.md
  modified:
    - src/secnotepad/ui/rich_text_editor.py

key-decisions:
  - "剪贴板 HTML 的安全检查集中在 SafeRichTextEdit MIME 插入边界， unsafe HTML 降级为 source.text() 纯文本。"
  - "RichTextEditorWidget.to_html() 去除 Qt 自动生成的外部 DTD doctype URL，避免持久化或测试输出包含外部 http:// 引用。"
  - "缩放以 _zoom_steps 内存字段表达，不修改 QTextDocument 内容、SNoteItem、Serializer 或 QSettings。"

patterns-established:
  - "编辑菜单集成通过 RichTextEditorWidget wrapper API 和 *_available_changed 信号完成，MainWindow 不需要直接访问 QTextDocument 信号。"
  - "不可信 HTML 粘贴只保留文本内容，并通过 status_message_requested 与 paste_sanitized 通知 UI。"
  - "会话显示缩放使用固定 1 个 QTextEdit zoom step 对应 10% 状态栏百分比。"

requirements-completed: [EDIT-09, EDIT-10, EDIT-11]

duration: 7min
completed: 2026-05-10T03:46:54Z
---

# Phase 04 Plan 04: 编辑命令、安全粘贴与会话缩放 Summary

**QTextEdit 编辑命令包装、安全剪贴板净化和不落盘会话缩放 API 已接入 RichTextEditorWidget**

## Performance

- **Duration:** 7min
- **Started:** 2026-05-10T03:39:28Z
- **Completed:** 2026-05-10T03:46:54Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 新增 `undo()`、`redo()`、`cut()`、`copy()`、`paste()`、`can_paste()` 公共 API，并提供 `action_undo`、`action_redo`、`action_cut`、`action_copy`、`action_paste` 动作供菜单集成复用。
- 将 `QTextDocument.undoAvailable`、`redoAvailable` 和 `QTextEdit.copyAvailable` 转发为组件信号，同时更新对应编辑动作启用状态。
- 实现 `SafeRichTextEdit.canInsertFromMimeData()` 与 `insertFromMimeData()`，对包含图片、本地/远程资源、script、event handler 或 `javascript:` 的 HTML 粘贴降级为纯文本。
- 新增 `zoom_in()`、`zoom_out()`、`reset_zoom()` 与 `zoom_percent`，缩放只影响当前会话显示并通过状态消息提示百分比。

## Task Commits

Each task was committed atomically:

1. **Task 1: 实现撤销/重做与剪切复制粘贴 API** - `837f9c2` (feat)
2. **Task 2: 实现安全粘贴边界** - `5570606` (feat)
3. **Task 3: 实现会话级缩放 API** - `410ae38` (feat)

**Plan metadata:** 本 SUMMARY 将单独提交。

## Files Created/Modified

- `src/secnotepad/ui/rich_text_editor.py` - 增加编辑命令 wrapper、可用性信号转发、安全粘贴边界、状态消息信号和会话缩放 API。
- `.planning/phases/04-rich-text-editor/04-04-SUMMARY.md` - 记录本计划执行结果、验证命令、偏差和提交清单。

## Verification

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_undo_redo_actions -q` — 1 passed
- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_clipboard_actions_and_safe_paste -q` — 1 passed
- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_zoom_does_not_mark_content_dirty -q` — 1 passed
- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_undo_redo_actions tests/ui/test_rich_text_editor.py::test_clipboard_actions_and_safe_paste tests/ui/test_rich_text_editor.py::test_zoom_does_not_mark_content_dirty -q` — 3 passed
- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py -q` — 11 passed
- Acceptance grep gates passed for `def undo`, `def redo`, `undoAvailable.connect`, `copyAvailable.connect`, `QApplication.clipboard`, `def insertFromMimeData`, blocked HTML markers, event-handler regex, paste status copy, `insertPlainText`, zoom API methods, `_zoom_steps`, and `缩放：100%`.

## Decisions Made

- 按计划使用 Qt 自带撤销栈和剪贴板能力，不自建编辑历史或剪贴板抽象。
- 安全粘贴的阻断规则集中在 `SafeRichTextEdit._html_has_blocked_resources()`，阻断后只插入 `source.text()`。
- `to_html()` 去掉 Qt 自动 doctype，避免输出中包含 `http://www.w3.org/...`，使 EDIT-10 的“输出 HTML 不包含外部 URL”要求可以真实成立。
- `zoom_percent` 作为只读 property 暴露，兼容现有测试断言，并保持缩放状态只在组件内存中。

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 创建项目虚拟环境并安装测试依赖**
- **Found during:** Task 1 RED 验证
- **Issue:** `.venv/bin/python` 不存在，计划指定的 pytest 命令无法运行。
- **Fix:** 使用项目虚拟环境创建 `.venv` 并安装 editable 项目与 pytest，符合用户记忆中“测试使用项目虚拟环境”的要求。
- **Files modified:** 未修改受跟踪文件；虚拟环境未纳入提交。
- **Verification:** 后续所有指定 pytest 命令均可在 `.venv` 中运行。
- **Committed in:** 不适用（环境准备，不提交生成目录）。

**2. [Rule 2 - Missing Critical] 去除 Qt HTML doctype 外部 URL**
- **Found during:** Task 2 安全粘贴验证
- **Issue:** 即使 unsafe paste 已降级为纯文本，`QTextEdit.toHtml()` 默认 doctype 仍包含 `http://www.w3.org/TR/REC-html40/strict.dtd`，违反“输出 HTML 不包含 `http://`”的安全验收条件。
- **Fix:** `RichTextEditorWidget.to_html()` 返回前移除 Qt 自动生成的 doctype；`content_changed` 同步也统一使用该安全输出。
- **Files modified:** `src/secnotepad/ui/rich_text_editor.py`
- **Verification:** `test_clipboard_actions_and_safe_paste` 通过，输出 HTML 不再包含测试阻断的外部 URL。
- **Committed in:** `5570606`

---

**Total deviations:** 2 auto-fixed (1 Rule 3 blocking, 1 Rule 2 missing critical)
**Impact on plan:** 两项偏差均为验证与安全正确性所需；未新增产品范围或架构面。

## Issues Encountered

- Task 1 RED 测试按预期失败，原因是缺少 `action_undo` 等编辑动作；实现 wrapper 与信号连接后通过。
- Task 2 初次实现粘贴净化后仍因 Qt 默认 doctype 含外部 DTD URL 导致安全断言失败；改为输出前移除 doctype 后通过。
- Task 3 RED 测试按预期失败，原因是缺少缩放 API；实现会话级缩放后通过。

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- RichTextEditorWidget 已提供 MainWindow 可直接绑定的编辑动作、状态信号、安全粘贴提示和缩放 API。
- 后续计划可将编辑菜单与视图菜单 action 路由到本组件，并保持缩放不进入加密数据模型。

## Self-Check: PASSED

- FOUND: `src/secnotepad/ui/rich_text_editor.py`
- FOUND: `.planning/phases/04-rich-text-editor/04-04-SUMMARY.md`
- FOUND: `837f9c2`
- FOUND: `5570606`
- FOUND: `410ae38`

---
*Phase: 04-rich-text-editor*
*Completed: 2026-05-10*
