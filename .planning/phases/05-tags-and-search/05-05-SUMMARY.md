---
phase: 05-tags-and-search
plan: 05
subsystem: ui
tags: [pyside6, qt, search, navigation, modeless-dialog]

requires:
  - phase: 05-tags-and-search
    provides: "05-01 页面标签数据模型与 UI 基础"
  - phase: 05-tags-and-search
    provides: "05-04 SearchDialog 与 SearchService"
provides:
  - "MainWindow 编辑菜单搜索入口与 Ctrl+F 快捷键"
  - "当前笔记本 SearchDialog 生命周期与 root 绑定/清理"
  - "搜索结果到分区树、页面列表和编辑器的同步跳转"
affects: [phase-05-tags-and-search, ui-navigation, search]

tech-stack:
  added: []
  patterns:
    - "modeless QDialog 由 MainWindow 持有并复用"
    - "搜索结果跳转使用对象引用与 SectionFilterProxy.mapFromSource 映射"

key-files:
  created:
    - tests/ui/test_main_window_search.py
  modified:
    - src/secnotepad/ui/main_window.py

key-decisions:
  - "搜索弹窗保持 modeless，MainWindow 复用单实例并在会话清理时清空 root，避免旧解密树引用残留。"
  - "搜索结果跳转通过对象引用定位目标页面和父分区，不依赖 id 或值相等，避免同名/同值页面误选。"

patterns-established:
  - "MainWindow 只读导航操作不得调用 mark_dirty()，由测试覆盖 _is_dirty 保持 False。"
  - "跨模型选择必须源模型 index → SectionFilterProxy.mapFromSource → 视图 currentIndex。"

requirements-completed: [SRCH-01, SRCH-02, SRCH-03]

duration: 4min
completed: 2026-05-11
---

# Phase 05 Plan 05: MainWindow 搜索入口与结果跳转 Summary

**MainWindow 中的 Ctrl+F modeless 搜索弹窗与搜索结果三栏同步跳转，且全流程保持只读不置脏**

## Performance

- **Duration:** 4min
- **Started:** 2026-05-11T10:35:10Z
- **Completed:** 2026-05-11T10:39:21Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 新增 MainWindow 编辑菜单 `搜索(&F)...` 和 `Ctrl+F` 快捷键，未打开笔记本时禁用，打开笔记本后启用。
- 接入单实例 modeless `SearchDialog`，每次打开绑定当前 `_root_item`，会话清理时清空 root 并关闭弹窗。
- 实现搜索结果跳转：定位目标页面父分区、映射到 `SectionFilterProxy`、选中页面列表并加载右侧编辑器；弹窗保持打开且 `_is_dirty` 不变化。
- 新增 UI 集成测试覆盖入口生命周期、嵌套分区跳转、状态栏提示、旧结果容错和对象引用定位。

## Task Commits

1. **Task 1: 编写 MainWindow 搜索入口与跳转测试** - `6a8cf65` (test)
2. **Task 2: 实现搜索菜单动作和弹窗生命周期** - `bbb7710` (feat)
3. **Task 3: 实现搜索结果跳转到分区与页面** - `7f80a55` (feat)

## Files Created/Modified

- `tests/ui/test_main_window_search.py` - MainWindow 搜索入口、弹窗生命周期、搜索结果跳转、不置脏和旧结果容错集成测试。
- `src/secnotepad/ui/main_window.py` - 搜索菜单 action、SearchDialog 生命周期、root 清理、搜索结果对象引用定位和分区/页面同步选择。

## Verification

- `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest tests/ui/test_main_window_search.py -x`：通过（生命周期子集在 Task 2 后通过）。
- `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest tests/ui/test_main_window_search.py tests/ui/test_search_dialog.py tests/ui/test_navigation.py -x`：106 passed。
- Acceptance grep 检查通过：`_act_search` / `搜索(&F)...` / `Ctrl+F`、`SearchResult` / `_select_search_result`、`_is_dirty is False` / `isVisible`、`mapFromSource`、`result_activated.connect` 均存在，且 `_select_search_result` 不调用 `mark_dirty()`。

## Decisions Made

- 搜索弹窗使用 MainWindow 持有的单实例 modeless `SearchDialog`，避免 `exec()` 阻塞并满足结果点击后弹窗保持打开。
- `_select_note()` 使用 `TreeModel._find_parent()` 与递归对象引用查找 source index，再通过 `SectionFilterProxy.mapFromSource()` 选择分区，避免源/代理 index 混用。
- 旧搜索结果目标不存在时只显示固定状态栏提示 `搜索结果对应页面不存在`，不输出页面内容或敏感数据。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- 工作树内未包含 `.venv`，因此验证命令按项目记忆改为使用主项目虚拟环境 `/home/jone/projects/secnotepad/.venv/bin/python`，未修改代码或计划范围。

## Known Stubs

None. 扫描发现的 `placeholder` 均为既有编辑器空状态 UI 文案和方法名，不是本计划新增未接数据的 stub。

## User Setup Required

None - no external service configuration required.

## Self-Check: PASSED

- 文件存在性验证通过：`src/secnotepad/ui/main_window.py`、`tests/ui/test_main_window_search.py`、`.planning/phases/05-tags-and-search/05-05-SUMMARY.md`。
- 提交存在性验证通过：`6a8cf65`、`bbb7710`、`7f80a55`。

## Next Phase Readiness

- SRCH-01/SRCH-02/SRCH-03 的端到端 MainWindow 搜索流程已完成，可进入 Phase 05 后续收尾计划。
- 搜索跳转已与现有导航和标签栏加载路径复用，后续 UI 美化可直接针对菜单、弹窗和状态栏表现做样式打磨。

---
*Phase: 05-tags-and-search*
*Completed: 2026-05-11*
