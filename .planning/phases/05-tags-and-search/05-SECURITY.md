---
phase: 05
slug: tags-and-search
status: verified
threats_open: 0
threats_total: 25
asvs_level: default
created: 2026-05-12
---

# Phase 05 — Security

本文件记录 Phase 05 tags-and-search 的安全威胁缓解核验结果。审计范围限于计划期 threat register 与 SUMMARY Threat Flags；未对无关新漏洞做盲扫。

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| 解密内存数据 → 搜索服务 | 已解密页面标题、HTML 正文和标签进入只读搜索逻辑 | 页面标题、正文纯文本、标签；敏感本地笔记内容 |
| 搜索服务 → UI rich text 片段 | 用户内容被转换、高亮并交给 Qt 结果项展示 | 转义后的搜索片段与受控 `<mark>` 标签 |
| 用户输入 → TagBarWidget/MainWindow | 未可信标签字符串进入 UI 校验、信号和当前页面元数据 | 标签文本 |
| SNoteItem.tags → Serializer/FileService | 标签元数据随整体 JSON 进入既有加密保存链路 | 标签元数据；随 `.secnote` 加密持久化 |
| SearchDialog → MainWindow navigation | 搜索结果对象请求改变主窗口选中状态 | 内存对象引用与导航状态 |
| 会话清理 → 搜索弹窗/root | 打开、新建或清理会话时断开旧解密树引用 | 已解密内存树引用 |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-05-01-01 | I | SearchService | mitigate | 无外部索引、数据库、缓存文件或搜索历史；`search_service.py` grep 无 `open(`、`Path(`、`sqlite`、`QSettings`。 | closed |
| T-05-01-02 | T/I | snippet generation | mitigate | 正文经 `QTextDocumentFragment.fromHtml()` 转纯文本，用户内容经 `html.escape()`，只插入受控 `<mark>`。 | closed |
| T-05-01-03 | D | tag/query length | accept | SearchService 不持久化 query，空 query 返回空结果；标签长度在 UI/MainWindow 限制为 32 字符。 | closed |
| T-05-01-04 | R/I | logging | mitigate | `search_service.py` grep 无 `print(` 或 `logging`，不输出 query、片段、正文或标签。 | closed |
| T-05-02-01 | T | TagBarWidget input | mitigate | `tag_bar_widget.py` 对输入 trim，拒绝空值、超过 32 字符和当前页面内 casefold 重复，保留合法原始显示文本。 | closed |
| T-05-02-02 | D | Tag chip layout | mitigate | 32 字符限制配合 FlowLayout 换行；测试覆盖 chip 不横向撑破主窗口。 | closed |
| T-05-02-03 | I | TagBarWidget | mitigate | 组件无文件写入、日志或保存链路引用，仅通过 `tag_added` / `tag_removed` Signal 传递输入。 | closed |
| T-05-02-04 | T | HTML content boundary | mitigate | `TagBarWidget` 不导入 `SNoteItem`、不写 content、不调用 `mark_dirty()`。 | closed |
| T-05-03-01 | T | `_on_tag_added` | mitigate | MainWindow handler 复核 trim、32 字符上限和 casefold 去重。 | closed |
| T-05-03-02 | R/T | dirty-state | mitigate | 成功 add/remove 调用 `mark_dirty()`；重复或无效输入不置脏，测试断言 `_is_dirty`。 | closed |
| T-05-03-03 | I | persistence | mitigate | 不新增明文 tags 文件；保存仍通过 `Serializer.to_json()` 进入既有加密 `.secnote` 链路。 | closed |
| T-05-03-04 | T/I | content boundary | mitigate | 标签处理不写 `SNoteItem.content`，测试断言 tags 与 content 分离。 | closed |
| T-05-03-05 | I | session leakage | mitigate | `_collect_available_tags()` 每次从当前 `_root_item` 收集；测试覆盖新笔记本候选清空。 | closed |
| T-05-04-01 | T/I | result snippet display | mitigate | `SearchDialog` 只展示 `SearchService.snippet`，不读取 `note.content` 或注入原始 HTML。 | closed |
| T-05-04-02 | I | query/results logging | mitigate | `search_dialog.py` grep 无 `print(` / `logging`；异常只显示固定错误文案。 | closed |
| T-05-04-03 | D | field filter | mitigate | 至少保留一个字段勾选；空 query 不搜索并显示提示。 | closed |
| T-05-04-04 | R/T | dialog lifecycle | mitigate | 结果激活只 emit 信号，不关闭弹窗、不修改数据、不置脏。 | closed |
| T-05-05-01 | T | `_select_note` | mitigate | 使用对象身份 `is` 定位目标，并通过 `SectionFilterProxy.mapFromSource()` 映射，避免同名/同值页面误选。 | closed |
| T-05-05-02 | R/T | dirty-state | mitigate | 搜索入口、展示和跳转路径不调用 `mark_dirty()`；集成测试断言 `_is_dirty is False`。 | closed |
| T-05-05-03 | I | dialog root/session | mitigate | `_clear_session()` 禁用搜索 action，清空并关闭 dialog root，避免旧解密树继续被弹窗引用。 | closed |
| T-05-05-04 | D | invalid stale result | mitigate | 目标不存在时仅显示固定状态栏提示，不崩溃、不打印敏感数据。 | closed |
| T-05-06-01 | I | search persistence boundary | mitigate | grep gate 无外部索引/缓存/历史命中；测试验证序列化无 search/index/history 字段。 | closed |
| T-05-06-02 | T/I | rich text snippet | mitigate | 测试覆盖 script/style/event 内容只以转义纯文本片段展示，不注入原始 HTML。 | closed |
| T-05-06-03 | R/T | dirty semantics | mitigate | 集成测试覆盖标签/正文修改置脏，搜索/跳转不置脏；人工验证 checkpoint 已记录。 | closed |
| T-05-06-04 | I | session cleanup | mitigate | 搜索 action 与 dialog root 在 session 清理后禁用/清空，有实现和测试覆盖。 | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-05-01-03 | T-05-01-03 | SearchService 层未设置 query 长度硬上限；query 不落盘，应用为本地个人笔记本规模，风险限定为局部可用性风险。空 query 返回空结果，标签输入有 32 字符控制。 | plan-time disposition | 2026-05-12 |

---

## Summary Threat Flags

| Plan | Threat Flags | Disposition |
|------|--------------|-------------|
| 05-01 | None. | 无新增计划外安全表面。 |
| 05-02 | 新增组件仅处理本地 UI 输入和 Qt 信号，不新增网络端点、文件访问、认证路径或信任边界外 schema 变更。 | 已由 T-05-02-01 至 T-05-02-04 覆盖。 |
| 05-03 | None beyond plan model. | 已由 T-05-03-01 至 T-05-03-05 覆盖。 |
| 05-04 | None beyond plan model. | 已由 T-05-04-01 至 T-05-04-04 覆盖。 |
| 05-05 | SUMMARY 未显式 Threat Flags 节；记录了 stale result 固定文案和 root cleanup 决策。 | 已映射到 T-05-05-03 / T-05-05-04。 |
| 05-06 | 仅修改测试与 SUMMARY，未新增网络端点、认证路径、文件访问模式或信任边界处 schema。 | 已由 T-05-06-01 至 T-05-06-04 覆盖。 |

---

## Evidence Highlights

- `src/secnotepad/model/search_service.py`：未使用文件、数据库、QSettings 或日志；片段生成使用纯文本转换、HTML 转义和受控 `<mark>`。
- `src/secnotepad/ui/tag_bar_widget.py`：输入校验、长度限制、casefold 去重和 Signal-only 边界已实现。
- `src/secnotepad/ui/main_window.py`：标签 handler 复核输入并维护 dirty 语义；搜索会话清理断开旧 root；结果跳转使用对象身份和 proxy 映射。
- `src/secnotepad/ui/search_dialog.py`：空 query 与字段筛选防护、固定错误文案、只展示 `SearchResult.snippet`、结果激活只发信号。
- `tests/model/test_search_service.py`、`tests/ui/test_tag_bar_widget.py`、`tests/ui/test_main_window_tags.py`、`tests/ui/test_search_dialog.py`、`tests/ui/test_main_window_search.py`：覆盖片段安全、标签边界、序列化、dirty 语义、弹窗生命周期和 stale result 容错。

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-12 | 25 | 25 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-12
