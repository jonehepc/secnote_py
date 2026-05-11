---
phase: 05
slug: tags-and-search
status: ready
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-11
updated: 2026-05-11
---

# Phase 05 — Validation Strategy

> Phase 05 标签与搜索执行期间的自动化反馈采样契约。所有 Python 测试/脚本必须使用项目虚拟环境 `/home/jone/projects/secnotepad/.venv`，不要使用系统 Python。

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 + PySide6 Qt Widgets fixtures |
| **Config file** | `/home/jone/projects/secnotepad/pyproject.toml` |
| **Quick run command** | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q` |
| **Full suite command** | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests -x` |
| **Estimated runtime** | < 30 seconds for targeted commands; full suite expected within normal project test latency |

---

## Sampling Rate

- **After every task commit:** Run the task's `<verify><automated>` command from the relevant PLAN.md.
- **After every plan wave:** Run all commands listed for completed plans in that wave.
- **Before `/gsd-verify-work`:** Run `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests -x` plus the Phase 05 grep gates in Plan 05-06.
- **Max feedback latency:** 30 seconds for targeted checks; stop at first failure with `-x`.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-T1 | 05-01 | 1 | SRCH-01, SRCH-02 | T-05-01-01, T-05-01-02 | 搜索服务测试先失败，锁定无外部索引、HTML 转纯文本和安全片段行为 | unit / RED | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/model/test_search_service.py -x` | ✅ planned by task | ⬜ pending |
| 05-01-T2 | 05-01 | 1 | SRCH-01, SRCH-02 | T-05-01-01, T-05-01-02 | 搜索 query 作为字面量处理；高亮使用 `re.escape(query)` 或等价非正则字面量逻辑；不创建索引/缓存 | unit | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/model/test_search_service.py -x` | ✅ planned by task | ⬜ pending |
| 05-01-T3 | 05-01 | 1 | SRCH-01, SRCH-02 | T-05-01-01, T-05-01-04 | 服务边界无敏感日志、无明文持久化、片段只含转义文本与受控 `<mark>` | unit + grep | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/model -x` | ✅ planned by task | ⬜ pending |
| 05-02-T1 | 05-02 | 1 | TAG-01, TAG-02, TAG-03 | T-05-02-01, T-05-02-02 | 标签控件测试锁定 trim、长度、casefold 去重、补全和 chip 不横向撑破编辑区 | UI unit | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_tag_bar_widget.py -x` | ✅ planned by task | ⬜ pending |
| 05-02-T2 | 05-02 | 1 | TAG-01, TAG-02, TAG-03 | T-05-02-01, T-05-02-02, T-05-02-04 | TagBarWidget 不接触 `SNoteItem.content`/`mark_dirty()`；chip 布局必须换行或保证非横向溢出 | UI unit | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_tag_bar_widget.py -x` | ✅ planned by task | ⬜ pending |
| 05-02-T3 | 05-02 | 1 | TAG-01, TAG-02, TAG-03 | T-05-02-02, T-05-02-04 | 组件对象名、禁用状态和富文本编辑器回归稳定 | UI regression | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_tag_bar_widget.py tests/ui/test_rich_text_editor.py -x` | ✅ planned by task | ⬜ pending |
| 05-03-T1 | 05-03 | 2 | TAG-01, TAG-02, TAG-03 | T-05-03-01, T-05-03-02 | MainWindow 标签集成测试锁定页面 tags 更新、dirty 语义和页面列表不显示标签 | UI integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window_tags.py -x` | ✅ planned by task | ⬜ pending |
| 05-03-T2 | 05-03 | 2 | TAG-01, TAG-02, TAG-03 | T-05-03-01, T-05-03-05 | 标签栏在右侧编辑区顶部，补全只来自当前笔记本，成功变更调用 `mark_dirty()` | UI integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window_tags.py -x` | ✅ planned by task | ⬜ pending |
| 05-03-T3 | 05-03 | 2 | TAG-01, TAG-02, TAG-03 | T-05-03-03, T-05-03-04 | tags 通过既有 Serializer/FileService 加密保存链路，不写入正文 HTML | integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window_tags.py tests/ui/test_navigation.py tests/model/test_serializer.py -x` | ✅ planned by task | ⬜ pending |
| 05-04-T1 | 05-04 | 2 | SRCH-01, SRCH-02 | T-05-04-01, T-05-04-03 | 搜索弹窗测试锁定字段筛选、回车/按钮触发、结果安全展示和弹窗保持打开 | UI unit | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_search_dialog.py -x` | ✅ planned by task | ⬜ pending |
| 05-04-T2 | 05-04 | 2 | SRCH-01, SRCH-02 | T-05-04-01, T-05-04-02 | SearchDialog 只展示 SearchService snippet，不读取 `note.content` 直接注入 UI | UI unit | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_search_dialog.py -x` | ✅ planned by task | ⬜ pending |
| 05-04-T3 | 05-04 | 2 | SRCH-01, SRCH-02 | T-05-04-03, T-05-04-04 | 验证无实时搜索/debounce，结果激活后 dialog 仍 visible | UI regression | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/model/test_search_service.py tests/ui/test_search_dialog.py -x` | ✅ planned by task | ⬜ pending |
| 05-05-T1 | 05-05 | 3 | SRCH-01, SRCH-02, SRCH-03 | T-05-05-01, T-05-05-02 | MainWindow 搜索入口和跳转测试锁定 Ctrl+F、菜单禁用、导航同步和不置脏 | UI integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window_search.py -x` | ✅ planned by task | ⬜ pending |
| 05-05-T2 | 05-05 | 3 | SRCH-01, SRCH-02, SRCH-03 | T-05-05-03 | SearchDialog modeless 生命周期绑定当前 root，清理 session 后不保留旧明文对象 | UI integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window_search.py -x` | ✅ planned by task | ⬜ pending |
| 05-05-T3 | 05-05 | 3 | SRCH-03 | T-05-05-01, T-05-05-04 | 结果跳转经 SectionFilterProxy 映射选择分区和页面；目标不存在不崩溃 | UI integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ui/test_main_window_search.py tests/ui/test_search_dialog.py tests/ui/test_navigation.py -x` | ✅ planned by task | ⬜ pending |
| 05-06-T1 | 05-06 | 4 | TAG-01, TAG-02, TAG-03, SRCH-01, SRCH-02, SRCH-03 | T-05-06-01, T-05-06-02 | 标签与搜索协同测试覆盖标签字段搜索、跳转和序列化不新增搜索历史 | integration | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/model/test_search_service.py tests/ui/test_main_window_tags.py tests/ui/test_main_window_search.py -x` | ✅ planned by task | ⬜ pending |
| 05-06-T2 | 05-06 | 4 | TAG-01, TAG-02, TAG-03, SRCH-01, SRCH-02, SRCH-03 | T-05-06-01, T-05-06-02, T-05-06-03, T-05-06-04 | 安全 grep gate 与全套测试通过，无明文索引、敏感日志、原始 HTML 注入或错误 dirty | full regression + grep | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests -x` | ✅ planned by task | ⬜ pending |
| 05-06-T3 | 05-06 | 4 | TAG-01, TAG-02, TAG-03, SRCH-01, SRCH-02, SRCH-03 | T-05-06-03 | 人工仅验证视觉、焦点、桌面快捷键、弹窗保持打开和 dirty 观感；自动化命令仍作为 gate | human-verify + full regression | `cd /home/jone/projects/secnotepad && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests -x` | ✅ planned by task | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 requirements are satisfied by the first task of each producing plan:

- [x] Plan 05-01 Task 1 creates `/home/jone/projects/secnotepad/tests/model/test_search_service.py` before implementing `SearchService`.
- [x] Plan 05-02 Task 1 creates `/home/jone/projects/secnotepad/tests/ui/test_tag_bar_widget.py` before implementing `TagBarWidget`.
- [x] Plan 05-03 Task 1 creates `/home/jone/projects/secnotepad/tests/ui/test_main_window_tags.py` before MainWindow tag integration.
- [x] Plan 05-04 Task 1 creates `/home/jone/projects/secnotepad/tests/ui/test_search_dialog.py` before implementing `SearchDialog`.
- [x] Plan 05-05 Task 1 creates `/home/jone/projects/secnotepad/tests/ui/test_main_window_search.py` before MainWindow search integration.
- [x] All commands use `/home/jone/projects/secnotepad/.venv/bin/python` via `.venv/bin/python`; no system Python command is planned.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 标签栏位置、chip 换行/不溢出、焦点和桌面快捷键 | TAG-01, TAG-02, TAG-03 | PySide6 桌面 UI 的视觉布局、焦点顺序和真实窗口快捷键需要人眼确认 | 按 Plan 05-06 checkpoint 步骤启动应用，添加多标签，确认右侧编辑区不被横向撑破，标签栏位于格式工具栏上方 |
| 搜索弹窗保持打开和连续跳转观感 | SRCH-01, SRCH-02, SRCH-03 | 自动化可验证 visible 和选择状态，但真实桌面连续点击的视觉反馈需人工确认 | 打开 `编辑(&E) → 搜索(&F)...` 或 `Ctrl+F`，连续点击多个结果，确认弹窗保持打开且主窗口同步切换 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or explicit checkpoint automated gate.
- [x] Sampling continuity: no 3 consecutive tasks without automated verify.
- [x] Wave 0 covers all initially missing test files through first tasks in Plans 05-01 through 05-05.
- [x] No watch-mode flags.
- [x] Feedback latency target < 30s for targeted checks with `-x`.
- [x] `nyquist_compliant: true` set in frontmatter because every real task ID has an automated command mapped above.

**Approval:** ready for execution
