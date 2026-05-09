---
phase: 03-navigation-system
plan: 02
subsystem: ui
tags: [pyside6, qt6, qabstractlistmodel, model-view]
requires:
  - phase: 01-project-framework
    provides: SNoteItem dataclass, TreeModel pattern reference
provides:
  - PageListModel — QAbstractListModel 子类，平铺展示分区下的页面列表
  - 10+ 行为测试覆盖 rowCount/data/flags/setData/add_note/remove_note/note_at
affects: [03-03-navigation-integration, 03-04-crud-interactions]

tech-stack:
  added: []
  patterns:
    - PySide6 QAbstractListModel 子类遵循 tree_model.py 代码组织风格
    - QSignalSpy 用于测试 dataChanged 信号发射
    - beginResetModel/beginInsertRows/beginRemoveRows 模式用于模型变更
    - Unicode box-drawing 章节分隔注释 (tree_model.py 约定)

key-files:
  created:
    - src/secnotepad/model/page_list_model.py
    - tests/model/test_page_list_model.py
  modified: []

key-decisions:
  - "使用 QAbstractListModel 而非 QAbstractTableModel — D-54 明确单列布局"
  - "set_section 使用 beginResetModel/endResetModel 完整重置，简化变更追踪"
  - "_notes 缓存直接引用 _section.children 中的对象 (同一引用，非拷贝)，确保 setData/CRUD 操作同时影响两处"

patterns-established:
  - "QAbstractListModel 数据模型: 列表推导过滤 item_type，缓存引用与源数据一致"
  - "D-60 空名称拒绝: isinstance(value, str) and value.strip() != '' 双重检查"

requirements-completed: [NAV-02, NAV-04]

duration: 4min
completed: 2026-05-08
---

# Phase 03 Plan 02: PageListModel Summary

**QAbstractListModel 子类实现页面列表平铺，含 24 个行为测试通过 RED/GREEN TDD 循环**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-08T03:44:26Z
- **Completed:** 2026-05-08T03:48:12Z
- **Tasks:** 2 (RED + GREEN, no REFACTOR needed)
- **Files modified:** 2 created

## Accomplishments
- PageListModel(QAbstractListModel) 实现，将分区 children 中的 note 子节点平铺为单列标题列表
- rowCount 正确计列 note 类型子节点，忽略 section 子节点
- data(DisplayRole/EditRole) 返回页面标题，单列布局 (D-54)
- setData(EditRole) 支持原地重命名，拒绝空/纯空格/非 str 类型值 (D-60)，发出 dataChanged 信号
- add_note/remove_note 同步维护 _section.children 源数据和 _notes 缓存
- note_at 通过索引获取 SNoteItem 对象引用
- 对象引用一致性保证: _notes[i] is _section.children[j] (Pitfall 5)
- 所有 24 个测试通过，无现有测试回归 (117 total model tests)

## Task Commits

1. **RED: Test file** - `79a2bb9` (test) — 24 failing tests for PageListModel
2. **GREEN: Implementation** - `b509b36` (feat) — PageListModel with all CRUD operations, 24 tests pass

No REFACTOR commit — implementation is clean and follows plan patterns exactly.

## Files Created/Modified
- `src/secnotepad/model/page_list_model.py` — PageListModel 类，QAbstractListModel 子类 (D-50, D-54)
- `tests/model/test_page_list_model.py` — 24 个测试方法覆盖 22 个场景 + 2 个对象引用一致性测试

## Decisions Made
- 使用 QAbstractListModel 而非 QAbstractTableModel — D-54 明确单列布局
- set_section 使用 beginResetModel/endResetModel 完整重置，简化变更追踪
- _notes 缓存直接引用 _section.children 中的对象 (同一引用，非拷贝)，确保 setData/CRUD 操作同时影响两处
- QSignalSpy 使用 `.count()` 而非 `len()` — PySide6 API 约定

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed QSignalSpy API usage in test**
- **Found during:** GREEN phase testing
- **Issue:** Test used `len(spy)` but PySide6's QSignalSpy requires `.count()` method
- **Fix:** Changed `assert len(spy) == 1` to `assert spy.count() == 1`
- **Files modified:** tests/model/test_page_list_model.py
- **Committed in:** b509b36 (GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test API fix. No scope creep.

## Issues Encountered
None

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- PageListModel 就绪，可供 Plan 03-03 (Navigation Integration) 中的 MainWindow 绑定到 QListView
- note_at 方法为 Plan 04 (Page Selection → Editor Preview) 提供 SNoteItem 索引访问
- 需 SectionFilterProxy (Plan 03-01 实施) 和 MainWindow 信号集成 (Plan 03-03) 后才能完整使用

---
*Phase: 03-navigation-system*
*Completed: 2026-05-08*
