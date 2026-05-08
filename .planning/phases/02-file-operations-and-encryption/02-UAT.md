---
status: resolved
phase: 02-file-operations-and-encryption
source: 02-02-SUMMARY.md, 02-04-SUMMARY.md
started: 2026-05-08T00:00:00Z
updated: 2026-05-08T12:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. 新建笔记本并设置密码
expected: 点击"新建笔记本"后，弹出设置密码对话框。对话框包含：两个密码输入框（密码+确认）、密码强度指示器（红/橙/绿进度条 + "弱"/"中"/"强"文字）、"生成密码"按钮、"显示密码"切换按钮。确认按钮在密码少于8位或两次输入不一致时禁用。
result: pass

### 2. 密码生成器
expected: 在设置密码对话框中点击"生成密码"按钮，弹出密码生成器子对话框。默认长度16位，可调节8-128位。包含大写/小写/数字/符号四个复选框，至少保留一项选中。预览区域为只读。点击"生成并使用"后，生成的密码填入设置密码对话框的两个输入框。
result: pass

### 3. 保存加密笔记本
expected: 首次保存时弹出文件保存对话框（.secnote 格式），选择路径并确认后文件加密保存到磁盘。再次保存（Ctrl+S）直接覆盖已有文件，不弹出对话框。保存后窗口标题的脏标记 `*` 消失。
result: pass

### 4. 打开加密笔记本（正确密码）
expected: 点击"打开笔记本"或欢迎页的最近文件，弹出文件选择对话框。选择 .secnote 文件后弹出密码输入对话框（单输入框 + "请输入文件加密密码"标签 + 显示密码切换按钮）。输入正确密码后，笔记本内容加载显示，窗口标题显示文件名，最近文件列表更新。
result: pass

### 5. 密码错误提示与重试
expected: 打开加密文件时输入错误密码，对话框内出现红色错误提示"密码错误，请重试"。对话框不关闭，可立即重新输入密码。无限次重试。
result: pass

### 6. 显示/隐藏密码切换
expected: 所有密码输入框右侧有切换按钮。默认密码以圆点显示（EchoMode=Password）。点击切换按钮后密码明文显示，再次点击恢复圆点。
result: pass

### 7. 另存为（含更换密码选项）
expected: 点击"另存为"弹出文件保存对话框。密码对话框以 CHANGE_PASSWORD 模式打开，包含"更换密码"复选框（默认未选中）。不勾选时确认按钮始终可用；勾选后显示新旧密码字段，新密码需满足长度和确认一致要求。
result: pass

### 8. 关闭保护（未保存更改）
expected: 笔记本有未保存更改时（窗口标题带 `*`），点击 X 关闭窗口或文件→退出，弹出三按钮确认框："保存"（保存后关闭）、"不保存"（放弃更改直接关闭）、"取消"（返回编辑）。选择"不保存"直接关闭，选择"取消"留在编辑界面。
result: pass

### 9. 窗口标题反映文件状态
expected: 新建未保存时窗口标题显示 "未命名 - SecNotepad"；保存后显示 "文件名.secnote - SecNotepad"；有未保存更改时标题前加 `*` 标记，如 "* 文件名.secnote - SecNotepad"。
result: pass

### 10. 欢迎页最近文件列表
expected: 欢迎页显示最近打开的文件列表（最多5条）。点击列表中的文件直接触发打开流程（弹出密码输入对话框）。重新打开已存在的文件时，该条目移到列表顶部。已不存在的文件不会出现在列表中。
result: pass
resolved_by: "02-05 gap closure — __init__() 末尾添加 _load_recent_files() + set_recent_files()；_on_save() 已有路径分支添加 _add_recent_file()"

## Summary

total: 10
passed: 10
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "欢迎页显示最近打开的文件列表（最多5条）。保存过的文件应出现在列表中"
  status: resolved
  reason: "User reported: 最近打开的文件列表里面没有数据。我已经新建并保存过一个test2.secnote的笔记"
  severity: major
  test: 10
  root_cause: "1) MainWindow.__init__() 未调用 _load_recent_files()，启动时欢迎页列表始终为空；2) _on_save() 已有文件路径时未调用 _add_recent_file()"
  resolved_by: "02-05: __init__() 末尾加载最近文件并传入欢迎页；_on_save() 已有路径分支更新最近文件列表。2 个新测试验证。"
  artifacts:
    - path: "src/secnotepad/ui/main_window.py"
      issue: "__init__() 末尾缺少 _load_recent_files() + set_recent_files() 调用（约 L42）"
    - path: "src/secnotepad/ui/main_window.py"
      issue: "_on_save() 保存已有文件后未调用 _add_recent_file()（约 L375-393）"
  missing:
    - "在 __init__() 末尾添加 _load_recent_files() 调用并设置到 welcome widget"
    - "在 _on_save() 已有路径分支中添加 _add_recent_file() 调用"
