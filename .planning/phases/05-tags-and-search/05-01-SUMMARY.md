---
phase: 05-tags-and-search
plan: 01
subsystem: model
tags: [search, PySide6, QTextDocumentFragment, pytest, tdd]

requires:
  - phase: 03-navigation-system
    provides: SNoteItem 树形分区与页面模型
  - phase: 04-rich-text-editor
    provides: QTextEdit HTML 正文存储约定
provides:
  - 当前已解密 SNoteItem 树的只读全文搜索服务
  - HTML 正文到纯文本的搜索边界
  - 安全转义并高亮关键词的搜索片段契约
affects: [05-tags-and-search, search-dialog, main-window-search-integration]

tech-stack:
  added: []
  patterns:
    - SearchService 作为 UI 可复用的只读业务服务
    - QTextDocumentFragment.fromHtml 用于 QTextEdit HTML 纯文本提取
    - html.escape + re.escape 生成安全字面量高亮片段

key-files:
  created:
    - src/secnotepad/model/search_service.py
    - tests/model/test_search_service.py
  modified: []

key-decisions:
  - "搜索服务仅遍历当前内存 SNoteItem 树，不创建索引、缓存、数据库或搜索历史。"
  - "正文片段先通过 Qt HTML parser 提取纯文本，再转义用户内容并插入受控 <mark> 高亮。"
  - "搜索结果保留 note 原对象引用，供后续搜索弹窗和 MainWindow 跳转集成使用。"

patterns-established:
  - "SearchFields 默认覆盖标题和正文，标签搜索必须显式开启。"
  - "SearchResult 使用 frozen dataclass 固定 title、section_path、matched_field、snippet 与 note 引用契约。"
  - "关键词匹配和高亮大小写不敏感，但 query 按字面字符串处理。"

requirements-completed: [SRCH-01, SRCH-02]

duration: 4min
completed: 2026-05-11
---

# Phase 05 Plan 01: 搜索服务 Summary

**当前内存笔记本树的标题、正文纯文本和可选标签搜索服务，带安全转义高亮片段**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-11T09:56:44Z
- **Completed:** 2026-05-11T10:00:42Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- 新增 `SearchService`、`SearchFields`、`SearchResult` 公开契约，供后续搜索弹窗和跳转集成消费。
- 实现当前已解密 `SNoteItem` 树的自然顺序遍历，只返回 note 类型结果并生成包含根分区的 section path。
- 使用 `QTextDocumentFragment.fromHtml()` 从 QTextEdit HTML 正文提取纯文本，避免原始 HTML 进入结果片段。
- 对标题、正文和标签命中片段执行 `html.escape()`，并用 `re.escape()` 确保 `C++`、`[abc]`、`a.b`、`foo(bar)` 等 query 按字面量高亮。
- 覆盖空查询、空 root、全部字段关闭、大小写不敏感、默认标签关闭、标签显式开启和树顺序保持等行为。

## Task Commits

Each task was committed atomically:

1. **Task 1: RED: 编写 SearchService 失败测试** - `a88b423` (test)
2. **Task 2: GREEN: 实现 SearchService 公开契约** - `76f39bb` (feat)
3. **Task 3: REFACTOR: 收紧服务边界与全量回归** - `5f5d6da` (refactor)

**Plan metadata:** pending final docs commit

_Note: This TDD plan has RED, GREEN, and REFACTOR commits._

## Files Created/Modified

- `src/secnotepad/model/search_service.py` - 只读搜索服务、HTML 纯文本提取、字段筛选、自然树遍历和安全片段生成。
- `tests/model/test_search_service.py` - SRCH-01/SRCH-02 的 TDD 行为测试，覆盖默认标题/正文、可选标签、HTML 安全片段和字面量高亮。

## Decisions Made

- 搜索服务保持无副作用：不读取或写入文件，不创建索引、缓存、数据库或明文历史。
- 正文搜索使用 Qt 文档 API 提取纯文本，不使用正则剥离 HTML。
- 片段展示只允许插入受控 `<mark>` 标签；所有来自笔记或标签的文本先 HTML 转义。
- 命中优先级为标题、正文、标签；同一 note 返回第一类命中结果，结果列表顺序保持树遍历自然顺序。

## Deviations from Plan

None - plan executed exactly as written.

## Auth Gates

None.

## Issues Encountered

- Worktree 内没有独立 `.venv`，首次按 worktree 路径运行 pytest 失败；根据项目记忆和计划命令改用项目根目录 `/home/jone/projects/secnotepad/.venv/bin/python`，测试在当前 worktree rootdir 下正常运行。此问题不涉及代码变更。

## Known Stubs

None.

## Threat Flags

None.

## TDD Gate Compliance

- RED gate: `a88b423` 创建失败测试，失败原因是缺少 `src.secnotepad.model.search_service` 公开契约。
- GREEN gate: `76f39bb` 实现搜索服务并通过 `tests/model/test_search_service.py`。
- REFACTOR gate: `5f5d6da` 收紧 helper 边界并通过 `tests/model` 全量回归。

## Verification

- `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest tests/model/test_search_service.py -x` — 7 passed.
- `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest tests/model -x` — 163 passed.
- `grep -n "print\|logging\|QSettings\|sqlite\|Path(\|open(" src/secnotepad/model/search_service.py` — no output.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `SearchDialog` 可直接导入 `SearchService.search()`，并使用 `SearchResult.note` 做结果跳转目标。
- 后续 UI 展示搜索片段时应直接使用 `SearchResult.snippet`，不要读取 `result.note.content` 或自行插入原始 HTML。

## Self-Check: PASSED

- FOUND: `src/secnotepad/model/search_service.py`
- FOUND: `tests/model/test_search_service.py`
- FOUND: `.planning/phases/05-tags-and-search/05-01-SUMMARY.md`
- FOUND commit: `a88b423`
- FOUND commit: `76f39bb`
- FOUND commit: `5f5d6da`

---
*Phase: 05-tags-and-search*
*Completed: 2026-05-11*
