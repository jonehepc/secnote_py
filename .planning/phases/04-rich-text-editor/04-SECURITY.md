---
phase: 04
slug: rich-text-editor
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-11
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI/本地包安装 → `.venv` | 安装依赖会把第三方包写入本地虚拟环境，但不应写入仓库源代码或提交产物。 | 第三方包、本地测试环境 |
| 系统 Python → 项目 `.venv` | 只允许系统 Python 用于创建虚拟环境；测试和项目脚本运行必须切换到 `.venv/bin/python`。 | 测试执行环境 |
| 测试输入 → 编辑器组件契约 | 测试模拟恶意剪贴板 HTML、图片和外部 URL，防止实现遗漏安全边界。 | 不可信 HTML、剪贴板内容 |
| 编辑器组件 → `SNoteItem.content` | HTML 只应进入内存模型字段，不应引入明文临时文件或外部资源引用。 | 富文本 HTML、笔记明文内容 |
| 用户点击格式工具栏 → `QTextDocument` | 用户操作修改富文本文档格式，必须通过 Qt 文档模型而非手写 HTML。 | 富文本格式命令 |
| `QColorDialog` → `QTextCharFormat` | 系统颜色对话框返回外部 UI 输入，必须只转换为 `QColor` 格式属性。 | 本地颜色选择 |
| 段落工具栏 → `QTextDocument` block/list model | 用户输入改变段落结构，必须保持 Qt 文档语义和 undo 边界。 | 段落、列表、缩进命令 |
| 待办按钮 → HTML 输出 | 待办项必须是普通文本，不能引入可执行/交互表单控件。 | 待办文本标记 |
| OS Clipboard → `QTextEdit` | 剪贴板是不可信输入，可能包含 HTML、图片、本地路径、远程 URL。 | 不可信剪贴板 MIME 数据 |
| `QTextDocument` undo stack → 页面切换 | undo 栈可能保留上一页明文片段，页面加载必须清理。 | 页面明文内容、撤销历史 |
| View menu zoom → editor display | 缩放是显示偏好，不应进入加密数据模型。 | 会话级显示状态 |
| MainWindow menu shortcuts → `RichTextEditorWidget` | 菜单/快捷键事件可能在无页面状态触发，必须按页面状态禁用或安全 no-op。 | 编辑命令 |
| `RichTextEditorWidget.content_changed` → `SNoteItem.content` | 编辑器 HTML 写回当前页面，是核心数据完整性边界。 | 富文本 HTML、当前笔记模型 |
| Serializer JSON → encrypted FileService | 富文本 HTML 进入 JSON 后必须继续通过既有加密保存链路，不新增明文缓存。 | 序列化笔记 JSON、加密文件内容 |
| Automated tests → release confidence | 自动测试必须覆盖安全粘贴、缩放不持久化、undo 栈清理，避免人工遗漏。 | 验证结果 |
| Human GUI verification → final acceptance | 颜色对话框和真实桌面快捷键需要人工确认。 | 人工验收结论 |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-04-00-01 | Tampering | `.venv` dependency install | mitigate | 使用项目本地 `.venv/bin/python -m pip install -e . pytest`；不修改生产代码或依赖声明。 | closed |
| T-04-00-02 | Information Disclosure | `.venv` local files | mitigate | `.venv` 已被 `.gitignore` 忽略且未暂存/提交。 | closed |
| T-04-00-03 | Repudiation | test runner selection | mitigate | 验证命令显式使用项目 `.venv/bin/python`。 | closed |
| T-04-01 | Information Disclosure | safe paste tests | mitigate | 安全粘贴测试断言输出不含图片、本地/远程 URL、脚本、事件处理器和 `javascript:`。 | closed |
| T-04-02 | Tampering | todo tests | mitigate | 待办测试要求普通 `☐ ` 文本，并禁止 HTML checkbox/input。 | closed |
| T-04-03 | Information Disclosure | navigation undo stack tests | mitigate | 页面切换测试验证撤销不能恢复上一页明文。 | closed |
| T-04-04 | Integrity | main window zoom tests | mitigate | 缩放测试验证不修改 `note.content` 且不置脏。 | closed |
| T-04-05 | Tampering | character actions | mitigate | 字符格式通过 `QTextCharFormat` 与 Qt merge API 应用，不拼接 HTML。 | closed |
| T-04-06 | Information Disclosure | `RichTextEditorWidget.load_html` | mitigate | `load_html()` 阻断信号、重置 modified 状态并清理 undo/redo stacks。 | closed |
| T-04-07 | Spoofing | color buttons | accept | 系统 `QColorDialog` 是本地可信 UI；颜色只影响文档格式，不执行外部代码。 | closed |
| T-04-08 | Denial of Service | font list | accept | `QFontComboBox` 由 Qt 管理系统字体枚举；不加载外部字体文件。 | closed |
| T-04-09 | Tampering | heading actions | mitigate | 标题使用 `QTextBlockFormat.setHeadingLevel`，不手写 HTML。 | closed |
| T-04-10 | Tampering | todo action | mitigate | 待办 action 只插入普通 `☐ ` 文本，测试禁止 checkbox/input。 | closed |
| T-04-11 | Denial of Service | indent action | mitigate | 缩进/反缩进路径将缩进值限制为非负。 | closed |
| T-04-12 | Repudiation | paragraph/list actions | accept | 本地单用户编辑器不记录操作审计；Qt undo 栈提供会话内撤销。 | closed |
| T-04-13 | Tampering | `SafeRichTextEdit.insertFromMimeData` | mitigate | 粘贴处理拒绝/降级包含图片、文件/网络资源、脚本、事件处理器或 `javascript:` 的 HTML。 | closed |
| T-04-14 | Information Disclosure | `QTextDocument` undo stack | mitigate | `load_html()` 清理 undo/redo stacks，导航回归覆盖跨页面泄漏。 | closed |
| T-04-15 | Information Disclosure | zoom API | mitigate | 缩放仅保存在内存 `_zoom_steps`，不进入 HTML、`SNoteItem`、Serializer 或 QSettings。 | closed |
| T-04-16 | Denial of Service | paste HTML | accept | 本地桌面大文本粘贴由 Qt 处理；本阶段不增加额外大小限制。 | closed |
| T-04-17 | Tampering | MainWindow edit actions | mitigate | 无页面时编辑 action 禁用；有页面时只路由到 `_rich_text_editor`。 | closed |
| T-04-18 | Information Disclosure | `_show_note_in_editor` | mitigate | 页面显示使用 `load_html()` 清理 undo/redo stacks，测试覆盖跨页面撤销。 | closed |
| T-04-19 | Integrity | `_on_editor_content_changed` | mitigate | 仅编辑器页、当前 note 存在且 HTML 变化时写回并 mark dirty。 | closed |
| T-04-20 | Information Disclosure | zoom menu | mitigate | 缩放 handler 只调用编辑器缩放 API 和状态栏，不访问 Serializer/SNoteItem/HTML 写入。 | closed |
| T-04-21 | Information Disclosure | Serializer rich HTML | mitigate | 富文本 HTML 仅在 `content` 字段 round-trip；保存仍走既有加密 `.secnote` 链路。 | closed |
| T-04-22 | Information Disclosure | zoom state | mitigate | `SNoteItem` 无 zoom/scale 字段，JSON 测试断言无 zoom、zoom_percent 或 scale。 | closed |
| T-04-23 | Tampering | legacy tests | mitigate | Phase 04 关键安全测试函数保留并通过，旧测试更新为富文本目标而非删除验证。 | closed |
| T-04-24 | Repudiation | manual GUI verification | accept | 本地单用户应用不做审计；人工验收记录在 04-06 SUMMARY。 | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-07 | 系统 `QColorDialog` 是本地桌面可信 UI；颜色只影响文档格式，不执行外部代码。 | Plan-time phase threat model | 2026-05-10 |
| AR-04-02 | T-04-08 | `QFontComboBox` 枚举系统字体由 Qt 管理；不加载外部字体文件。 | Plan-time phase threat model | 2026-05-10 |
| AR-04-03 | T-04-12 | 本地单用户编辑器不记录操作审计；Qt undo 栈提供会话内可撤销性。 | Plan-time phase threat model | 2026-05-10 |
| AR-04-04 | T-04-16 | 本地桌面粘贴大文本由 Qt 处理；本阶段不增加额外大小限制。 | Plan-time phase threat model | 2026-05-10 |
| AR-04-05 | T-04-24 | 本地单用户应用不做操作审计；人工验收已记录在 SUMMARY。 | Plan-time phase threat model | 2026-05-11 |

*Accepted risks do not resurface in future audit runs.*

---

## Verification Evidence

| Evidence | Result |
|----------|--------|
| `QT_QPA_PLATFORM=offscreen /home/jone/projects/secnotepad/.venv/bin/python -m pytest /home/jone/projects/secnotepad/tests/ui/test_rich_text_editor.py /home/jone/projects/secnotepad/tests/ui/test_main_window.py /home/jone/projects/secnotepad/tests/ui/test_navigation.py /home/jone/projects/secnotepad/tests/model/test_serializer.py -q` | `188 passed in 17.38s` |
| SUMMARY Threat Flags | 04-00、04-01、04-03、04-04、04-05、04-06 均为 None；04-02 未登记新增 Threat Flags。 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-11 | 27 | 27 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-11
