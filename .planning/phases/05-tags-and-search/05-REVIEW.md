---
phase: "05"
phase_name: tags-and-search
status: fixed
review_depth: standard
files_reviewed: 10
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
original_findings:
  blocker: 3
  warning: 1
fixed_commits:
  - 42f660a
---

# Phase 05 代码审查报告

## 结果

标准深度代码审查发现 3 个阻塞问题和 1 个警告，均已在提交 `42f660a` 中修复并补充回归测试。

## 已修复的问题

### BL-01：生产代码使用 `src.secnotepad` 导入

- 影响文件：`src/secnotepad/model/search_service.py`、`src/secnotepad/ui/search_dialog.py`
- 修复：改为包内相对导入，避免安装后运行依赖源码树 `src` 命名空间。

### BL-02：标签 chip 可能按富文本解释用户标签

- 影响文件：`src/secnotepad/ui/tag_bar_widget.py`
- 修复：`QLabel` 强制 `Qt.PlainText`，tooltip 中用户标签使用 HTML 转义。

### BL-03：非法 `tags` 数据可能在打开文件后触发 UI 崩溃

- 影响文件：`src/secnotepad/model/serializer.py`、`src/secnotepad/model/search_service.py`
- 修复：反序列化边界拒绝非字符串列表的 `tags`；搜索标签路径忽略非字符串防御性输入。

### WR-01：Unicode casefold 命中与高亮语义不一致

- 影响文件：`src/secnotepad/model/search_service.py`
- 修复：使用统一的 casefold span 映射生成 snippet，高亮逻辑与命中逻辑一致。

## 验证

- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/model/test_search_service.py tests/model/test_serializer.py tests/ui/test_tag_bar_widget.py tests/ui/test_search_dialog.py tests/ui/test_main_window_search.py tests/ui/test_main_window_tags.py -q` — 70 passed

## 当前状态

所有审查发现均已修复；无剩余 Critical/Warning/Info 项。
