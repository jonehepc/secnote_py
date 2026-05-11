---
phase: 04-rich-text-editor
reviewed: 2026-05-11T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - .gitignore
  - src/secnotepad/ui/main_window.py
  - src/secnotepad/ui/rich_text_editor.py
  - tests/model/test_serializer.py
  - tests/ui/test_main_window.py
  - tests/ui/test_navigation.py
  - tests/ui/test_rich_text_editor.py
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: fixed
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-11T00:00:00Z  
**Depth:** standard  
**Files Reviewed:** 7  
**Status:** issues_found

## Summary

审查了 Phase 04 富文本编辑器相关实现与测试文件。发现 2 个必须修复的 BLOCKER：一个会导致在光标处设置格式后后续输入不生效，另一个会导致待办列表命令在无选区时误修改下一段内容。两者均属于用户可直接触发的正文编辑错误，可能污染笔记内容。

## Fix Status

已在 `d7dcea1` 修复两个 Critical 问题，并补充回归测试。验证命令：`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q --tb=short`，结果：375 passed。

## Critical Issues

### CR-01: BLOCKER — 光标处字符格式不会应用到后续输入

**File:** `src/secnotepad/ui/rich_text_editor.py:330-334`

**Issue:** `_merge_char_format()` 在调用 `self._editor.mergeCurrentCharFormat(fmt)` 后又把旧的 `cursor` 设回编辑器。无选区时，`mergeCurrentCharFormat()` 本应设置“后续输入使用的字符格式”，但随后 `setTextCursor(cursor)` 会恢复旧光标状态，导致用户在光标处点击“加粗/斜体/字号/字体”等按钮后继续输入的文本仍是原格式。这个错误会让常见富文本编辑流程失效。

**Fix:**

```python
def _merge_char_format(self, fmt: QTextCharFormat) -> None:
    cursor = self._editor.textCursor()
    if cursor.hasSelection():
        cursor.mergeCharFormat(fmt)
        self._editor.setTextCursor(cursor)
    else:
        self._editor.mergeCurrentCharFormat(fmt)
    self._editor.setFocus()
```

同时补充无选区回归测试：光标位于文本中间或空文档中时，触发加粗后输入的新字符应带有对应格式。

### CR-02: BLOCKER — 无选区插入待办项会误修改下一段

**File:** `src/secnotepad/ui/rich_text_editor.py:417-434`

**Issue:** `_insert_todo_item()` 在无选区时 `selectionStart() == selectionEnd()`，按预期只应修改当前段落。但循环中每处理一个块都会在 `block.position() <= end` 时递增 `end_block_number`。无选区时当前块满足该条件，因此循环范围被扩展到下一块，导致用户只在当前段落插入待办项时，下一段也被自动加上 `☐ `。这是正文内容的非预期修改，有笔记内容污染风险。

**Fix:**

```python
def _insert_todo_item(self) -> None:
    cursor = self._editor.textCursor()
    start = cursor.selectionStart()
    end = cursor.selectionEnd()
    doc = self._editor.document()

    cursor.beginEditBlock()
    try:
        block = doc.findBlock(start)
        end_block = doc.findBlock(end)

        if not cursor.hasSelection():
            end_block_number = block.blockNumber()
        else:
            end_block_number = end_block.blockNumber() if end_block.isValid() else block.blockNumber()

        while block.isValid() and block.blockNumber() <= end_block_number:
            if not block.text().startswith("☐ "):
                block_cursor = QTextCursor(block)
                block_cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                block_cursor.insertText("☐ ")
            block = block.next()
    finally:
        cursor.endEditBlock()

    self._editor.setTextCursor(cursor)
    self._editor.setFocus()
    self._set_status("已插入待办项")
```

同时补充测试：文档包含多段、光标无选区时，触发待办列表只应修改当前段，不应修改下一段。

---

_Reviewed: 2026-05-11T00:00:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
