# Phase 02: 文件操作与加密 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-07
**Phase:** 02-file-operations-and-encryption
**Areas discussed:** 加密文件结构与密钥派生, 密码输入对话框设计, 最近文件列表管理, 未保存检测与关闭保护

---

## 加密文件结构与密钥派生

| Option | Description | Selected |
|--------|-------------|----------|
| PBKDF2 + 随机盐 (推荐) | PBKDF2HMAC, 16B salt, 600k iterations (OWASP 2025) | ✓ |
| 纯 SHA-512（按需求来） | 直接 SHA-512(password), 取前 32B 做 AES-256 key | |
| SHA-512 + 随机盐 | SHA-512(password + salt) 折中方案 | |

| Option | Description | Selected |
|--------|-------------|----------|
| 二进制格式 (推荐) | 4B magic + salt + IV + encrypted data, compact | ✓ |
| JSON + Base64 包装 | Human-readable wrapper, ~33% size increase | |
| 参考旧项目格式 | Compatible with SafetyNotebook format | |

| Option | Description | Selected |
|--------|-------------|----------|
| 加 HMAC (推荐) | HMAC-SHA256 integrity check before encryption | ✓ |
| 不加，依赖 CFB 自身 | Rely on CFB error propagation | |
| 换用 AES-GCM | AEAD mode with built-in auth tag | |

| Option | Description | Selected |
|--------|-------------|----------|
| 独立派生两个密钥 | Separate PBKDF2 calls with different context labels | ✓ |
| 64 字节派生，前后拆分 | Single PBKDF2 → 64B output split into AES+HMAC keys | |

| Option | Description | Selected |
|--------|-------------|----------|
| 固定布局 | 4B magic + 1B version + 16B salt + 16B IV + 32B HMAC + ciphertext | ✓ |
| TLV 风格可变长头 | Type-length-value header for extensibility | |

| Option | Description | Selected |
|--------|-------------|----------|
| 600,000 轮 | OWASP 2025 recommended | ✓ |
| 210,000 轮 | Faster UX, shorter open delay | |
| 库默认值 | cryptography library default | |

| Option | Description | Selected |
|--------|-------------|----------|
| HMAC 明文后加密 | HMAC plaintext JSON, then encrypt | ✓ |
| HMAC 密文 | Encrypt first, then HMAC ciphertext | |
| HMAC 头+密文 | HMAC over header + ciphertext | |

| Option | Description | Selected |
|--------|-------------|----------|
| 不同 context 标签 | b'secnotepad-aes-key' / b'secnotepad-hmac-key' | ✓ |
| 不同 salt | Two separate random salts | |

| Option | Description | Selected |
|--------|-------------|----------|
| SHA-256 | Consistent with HMAC-SHA256 | ✓ |
| SHA-512 | Slower derivation, adds brute-force resistance | |

| Option | Description | Selected |
|--------|-------------|----------|
| 一次性全量读写 | Entire file in memory, simple for KB-MB notes | ✓ |
| 流式分块处理 | Chunked I/O for large files | |

| Option | Description | Selected |
|--------|-------------|----------|
| ASCII 限制 | ASCII-only passwords | ✓ |
| UTF-8 (推荐) | Support non-ASCII (e.g. Chinese) passwords | |

| Option | Description | Selected |
|--------|-------------|----------|
| 两层独立版本号 | File header version + JSON inner version evolve independently | ✓ |
| 单一版本号 | Single version field for both | |

| Option | Description | Selected |
|--------|-------------|----------|
| 用完即清零 | Zero keys/passwords via bytearray after use | ✓ |
| 不特殊处理 | Trust Python GC | |

| Option | Description | Selected |
|--------|-------------|----------|
| 全新 salt+IV | Regenerate on save-as with new password | ✓ |
| 保留原 salt+IV | Keep original, re-derive keys only | |

---

## 密码输入对话框设计

| Option | Description | Selected |
|--------|-------------|----------|
| 统一对话框 + 模式切换 | Single reusable QDialog with mode parameter | ✓ |
| 独立对话框 | Three separate dialogs | |
| 两个：设密码 / 输密码 | Set-password + enter-password only | |

| Option | Description | Selected |
|--------|-------------|----------|
| 设密码时确认 | Confirm password field, disable OK on mismatch | ✓ |
| 显示强度提示 | Real-time entropy bar (weak/medium/strong) | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| 对话框内按钮 + 子对话框 | Button in dialog → sub-dialog for params | ✓ |
| 可调长度+字符集 | Adjustable length (default 16) + charset options | ✓ |

| Option | Description | Selected |
|--------|-------------|----------|
| 最少 8 字符 | Minimum 8 characters | ✓ |
| 非空即可 | Any non-empty password | |

| Option | Description | Selected |
|--------|-------------|----------|
| 对话框内重试 | Show error in dialog, allow retry without closing | ✓ |
| 提示后返回 | QMessageBox then return to welcome page | |

| Option | Description | Selected |
|--------|-------------|----------|
| 先选路径，后输密码 | QFileDialog first, then password dialog | ✓ |
| 先输密码，后选路径 | Password first, then file dialog | |

| Option | Description | Selected |
|--------|-------------|----------|
| 眼睛图标按钮 | Eye icon QAction embedded in QLineEdit | ✓ |
| 复选框切换 | QCheckBox "show password" below field | |

| Option | Description | Selected |
|--------|-------------|----------|
| 复选框控制显示 | QCheckBox "更换密码" toggles new password fields | ✓ |
| 可选字段，空则沿用 | New password field optional, empty = keep current | |

| Option | Description | Selected |
|--------|-------------|----------|
| 通过 getter 返回 | password() getter, caller clears after use | ✓ |
| 属性/成员变量 | Store in dialog attribute | |

---

## 最近文件列表管理

| Option | Description | Selected |
|--------|-------------|----------|
| QSettings | Qt-native cross-platform config storage | ✓ |
| 独立 JSON 配置文件 | ~/.config/secnotepad/recent.json | |
| 与笔记同目录 | Hidden file alongside .secnote files | |

| Option | Description | Selected |
|--------|-------------|----------|
| 5 个 | Max 5 entries | ✓ |
| 10 个 | Max 10 entries | |

| Option | Description | Selected |
|--------|-------------|----------|
| 仅路径 | Absolute file path only | ✓ |
| 路径+时间+名称 | Path + timestamp + display name | |

| Option | Description | Selected |
|--------|-------------|----------|
| 静默跳过+移除 | Check existence, skip stale, remove from list silently | ✓ |
| 弹提示后移除 | Show QMessageBox for stale entries | |
| 不做预检查 | Only error on click | |

| Option | Description | Selected |
|--------|-------------|----------|
| 单击直接打开 | Single click triggers open flow | ✓ |
| 双击打开 | Double-click to open | |
| 单击打开 + 移除按钮 | Click to open + X button to remove | |

| Option | Description | Selected |
|--------|-------------|----------|
| 移到顶部 | Move existing entry to top on re-open | ✓ |
| 删旧插新 | Remove old, insert new at top | |

---

## 未保存检测与关闭保护

| Option | Description | Selected |
|--------|-------------|----------|
| 布尔脏标志 | `_is_dirty: bool` flag in MainWindow | ✓ |
| JSON 内容比对 | Compare serialized JSON on save | |
| 编辑器+模型双标志 | Separate flags for editor and model | |

| Option | Description | Selected |
|--------|-------------|----------|
| 提示保存 | Prompt save/discard/cancel for new unsaved notebooks | ✓ |
| 直接丢弃 | Discard without prompt (FILE-01 compliance) | |

| Option | Description | Selected |
|--------|-------------|----------|
| 保存 / 不保存 / 取消 | Three-button QMessageBox | ✓ |
| 保存 / 不保存（无取消） | Two-button, no cancel option | |

| Option | Description | Selected |
|--------|-------------|----------|
| Phase 2 仅文件操作触发 | Reserve mark_dirty/mark_clean for Phase 3/4 | ✓ |
| 立即接入模型信号 | Connect TreeModel signals in Phase 2 | |

| Option | Description | Selected |
|--------|-------------|----------|
| closeEvent 统一拦截 | Override closeEvent for X button and File→Exit | ✓ |
| 仅菜单检查 | Only check in File→Exit menu action | |

| Option | Description | Selected |
|--------|-------------|----------|
| 仅修改后提示 | Don't flag new empty notebook as dirty | ✓ |
| 新建即脏 | Flag immediately as dirty on new | |

---

## Claude's Discretion

All decisions were made by the user — no areas were deferred to Claude.

## Deferred Ideas

None — discussion stayed within phase scope.
