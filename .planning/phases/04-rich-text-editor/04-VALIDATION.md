---
phase: 04
slug: rich-text-editor
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-09
---

# Phase 04 — Validation Strategy

> Phase 04 富文本编辑器执行期间的反馈采样与验证契约。

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest（通过项目 `.venv` 运行） |
| **Config file** | `pyproject.toml` 的 `[tool.pytest.ini_options] testpaths = ["tests"]` |
| **Quick run command** | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py -q` |
| **Full suite command** | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q` |
| **Estimated runtime** | ~30-90 seconds |

---

## Sampling Rate

- **After every task commit:** Run `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py -q`
- **After every plan wave:** Run `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py tests/ui/test_main_window.py tests/ui/test_navigation.py -q`
- **Before `/gsd-verify-work`:** Full suite must be green with `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q`
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | EDIT-01 | T-04-01 | 页面 HTML 只同步到 `SNoteItem.content` 并通过既有加密保存链路持久化 | integration | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_editing_page_updates_note_html_and_dirty -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | EDIT-02 | — | 字符格式通过 Qt 文档模型应用，不手写 HTML | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_character_format_actions -q` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | EDIT-03 | — | 字体/字号控件作用于选区并跟随光标同步 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_font_family_and_size_controls -q` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | EDIT-04 | — | 颜色动作只修改文档格式，不新增外部资源 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_text_and_background_color_actions -q` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 1 | EDIT-05 | — | 对齐动作互斥且作用于当前段落/选区段落 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_alignment_actions_are_exclusive -q` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | EDIT-06 | T-04-02 | 待办列表保存为普通“☐ ”文本，不引入 HTML checkbox 或外部资源 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_list_and_checklist_actions -q` | ❌ W0 | ⬜ pending |
| 04-01-07 | 01 | 1 | EDIT-07 | — | H1-H6 使用 `QTextBlockFormat.headingLevel` 语义块 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_heading_levels -q` | ❌ W0 | ⬜ pending |
| 04-01-08 | 01 | 1 | EDIT-08 | — | 缩进使用 Qt 原生 block/list 能力 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_indent_outdent_actions -q` | ❌ W0 | ⬜ pending |
| 04-01-09 | 01 | 1 | EDIT-09 | T-04-03 | 页面加载后清空 undo/redo 栈，避免跨页面明文片段残留 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_undo_redo_actions -q` | ❌ W0 | ⬜ pending |
| 04-01-10 | 01 | 1 | EDIT-10 | T-04-02 | 粘贴不保存 `<img`、`file:`、`http:`、`https:` 外部资源引用 | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_clipboard_actions_and_safe_paste -q` | ❌ W0 | ⬜ pending |
| 04-01-11 | 01 | 1 | EDIT-11 | — | 缩放只影响会话显示，不修改 HTML、不触发 dirty | unit/UI | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_rich_text_editor.py::test_zoom_does_not_mark_content_dirty -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/ui/test_rich_text_editor.py` — 覆盖 EDIT-01~EDIT-11 的富文本组件行为。
- [ ] `tests/ui/test_main_window.py` — 补充编辑菜单启用、格式工具栏位置、页面切换不误置脏、视图菜单缩放入口。
- [ ] `tests/model/test_serializer.py` — 如现有测试未覆盖 HTML 内容 round-trip，补充含中文与富文本 HTML 的序列化回归。
- [ ] `.venv` — 由 `04-00-PLAN.md` 在 Wave 0 创建/验证；执行阶段使用 `.venv/bin/python -m pip install -e . pytest` 准备依赖；不要用系统 Python 跑测试；`.venv` 不得提交。

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 颜色选择对话框可打开并应用颜色 | EDIT-04 / D-67 | 原生 `QColorDialog` 交互在 headless 自动测试中不稳定 | 启动应用，选择页面，点击文字颜色和背景色按钮，选择颜色后确认选区 HTML/视觉颜色变化 |
| 状态栏显示当前缩放百分比 | EDIT-11 / D-80 | 自动测试可覆盖状态文本，人工仍需确认桌面提示体验 | 使用 Ctrl+Plus、Ctrl+Minus、Ctrl+0，确认状态栏短暂提示百分比且页面内容未变脏 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references via `04-00-PLAN.md` for `.venv` and `04-01-PLAN.md` for RED test files
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
