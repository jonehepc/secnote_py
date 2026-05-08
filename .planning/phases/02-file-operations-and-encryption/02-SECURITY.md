---
phase: 02
slug: file-operations-and-encryption
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-08
---

# Phase 02 — 安全威胁验证

> 每阶段安全合约：威胁登记、已接受风险、审计跟踪。

---

## 信任边界

| 边界 | 描述 | 穿越数据 |
|------|------|----------|
| 磁盘文件 → 应用 | 文件头从不可信磁盘文件读取，解析时可能遇到篡改数据 | 二进制文件数据 (.secnote) |
| 用户 → 对话框 | 用户输入密码，密码在对话框内存中短暂存在 | 用户密码 (ASCII) |
| 对话框 → 调用方 | password() getter 传递密码字符串 | 密码明文 |
| 应用内存 → 磁盘文件 | 加密数据从内存写入磁盘（加密后） | AES-256-CFB 密文 + 69B 文件头 |
| 磁盘文件 → 应用内存 | 文件从磁盘读入内存后解密 | 加密文件 → 明文 JSON |
| 用户密码流 | 密码从 UI 经 FileService 到 PBKDF2 | 用户密码 → 派生密钥 |
| 用户 → MainWindow | 用户通过文件操作触发加密/解密流程 | 文件路径、密码 |
| MainWindow → 磁盘 | 保存/另存为写入加密文件 | 加密 .secnote 文件 |
| 内存中密码 | MainWindow 持有 _current_password 用于会话期间 | 当前会话密码 |

---

## 威胁登记

| Threat ID | 类别 | 组件 | 处置 | 缓解措施 | 状态 |
|-----------|------|------|------|----------|------|
| T-02-01 | S (欺骗) | Header.parse() | mitigate | 魔数校验 'SN02' 拒绝非 .secnote 文件 | closed |
| T-02-02 | T (篡改) | Header.parse() | mitigate | 固定 69 字节结构解析，struct.unpack 自动验证长度 | closed |
| T-02-03 | I (信息泄露) | HeaderError 消息 | mitigate | 错误消息不泄露文件名或路径，仅报告"无效的魔数" | closed |
| T-02-04 | I (信息泄露) | PasswordDialog | mitigate | bytearray 存储密码 + clear_password() 显式原地清零 (D-27, D-39) | closed |
| T-02-05 | I (信息泄露) | QLineEdit 眼睛图标 | mitigate | 默认 EchoMode=Password，点击切换可见性 (D-37) | closed |
| T-02-06 | S (欺骗) | 密码强度指示器 | accept | 简易熵评估仅用于 UX 反馈，非安全机制 | closed |
| T-02-07 | I (信息泄露) | 密码生成器预览 | accept | 预览仅在本地对话框内显示，不写入日志或持久化 | closed |
| T-02-08 | T (篡改) | FileService.decrypt() | mitigate | HMAC-SHA256 验证完整性，篡改数据被拒收 (D-24) | closed |
| T-02-09 | I (信息泄露) | _derive_keys() | mitigate | 每次加密生成新随机 salt (os.urandom)，避免 salt 重用 (D-28) | closed |
| T-02-10 | I (信息泄露) | decrypt() 错误消息 | mitigate | 统一返回 "密码错误"，不区分 HMAC 失败或解密失败 | closed |
| T-02-11 | S (欺骗) | Header.parse() | mitigate | 魔数校验 'SN02' 拒绝非 .secnote 文件（与 T-02-01 相同防线） | closed |
| T-02-12 | T (篡改) | bytes_eq() 比较 | mitigate | 常量时间比较 `cryptography.hazmat.primitives.constant_time.bytes_eq` 防止时序侧信道 | closed |
| T-02-13 | I (信息泄露) | AES 密钥派生 | mitigate | PBKDF2-SHA256 600,000 迭代减缓暴力破解 (D-21) | closed |
| T-02-14 | I (信息泄露) | 密码 ASCII 限制 | accept | 用户决策 (D-29)，非安全机制；密码在 encrypt() 入口处校验 isascii() | closed |
| T-02-15 | T (篡改) | CFB 加密模式 | accept | 用户锁定 AES-256-CFB (D-24)；从 `cryptography.hazmat.decrepit` 导入以兼容未来版本 | closed |
| T-02-16 | D (拒绝服务) | closeEvent | accept | 保存失败时用户可选择"不保存"继续关闭，不阻塞退出 | closed |
| T-02-17 | D (数据丢失) | closeEvent 三按钮 | mitigate | 提供保存/不保存/取消三选项 (D-48)，防止意外丢失未保存数据 | closed |
| T-02-18 | I (信息泄露) | _current_password | accept | 会话期间持有密码是可行设计；关闭时通过 _clear_session() 清空字符串 | closed |
| T-02-19 | I (信息泄露) | 最近文件列表 | accept | 仅存储文件绝对路径 (QSettings)，不包含任何笔记内容或密码 | closed |
| T-02-20 | T (篡改) | 最近文件路径 | accept | D-42 加载时通过 os.path.isfile() 检查文件存在性，不存在的条目静默移除 | closed |

*状态: open · closed*

*处置: mitigate (需要实现) · accept (已记录风险) · transfer (第三方)*

---

## 已接受风险

| Risk ID | 威胁引用 | 理由 | 接受方 | 日期 |
|---------|----------|------|--------|------|
| A-02-01 | T-02-06 | 密码强度指示器仅为 UX 辅助，熵值评估非安全机制；不影响实际加密强度 | 用户 (D-32) | 2026-05-07 |
| A-02-02 | T-02-07 | 密码生成器预览仅在本地对话框内存中存在，不被日志记录或持久化 | 用户 (D-33) | 2026-05-07 |
| A-02-03 | T-02-14 | ASCII 密码限制是明确的用户决策 (D-29)，非安全漏洞；未来可通过 UTF-8 规范化扩展 | 用户 (D-29) | 2026-05-07 |
| A-02-04 | T-02-15 | AES-256-CFB 是用户选择的加密模式 (D-24)；需关注 cryptography 库未来版本中 CFB 的弃用状态 | 用户 (D-24) | 2026-05-07 |
| A-02-05 | T-02-16 | closeEvent 保存失败允许"不保存"退出是合理的可用性权衡；不阻塞应用程序关闭 | 设计决策 (D-46) | 2026-05-07 |
| A-02-06 | T-02-18 | MainWindow 会话期间持有 _current_password 是必需的（用于保存操作）；窗口关闭时通过 _clear_session() 清空 | 设计约束 | 2026-05-07 |
| A-02-07 | T-02-19 | 最近文件列表仅存储文件路径字符串，QSettings 是本地用户级存储，不暴露笔记内容 | 用户 (D-40) | 2026-05-07 |
| A-02-08 | T-02-20 | 最近文件路径在加载时通过 os.path.isfile() 验证，不存在的条目静默移除 (D-42) | 设计决策 (D-42) | 2026-05-07 |

---

## 安全审计跟踪

| 审计日期 | 威胁总数 | 已关闭 | 仍开启 | 执行方 |
|----------|----------|--------|--------|--------|
| 2026-05-08 | 20 | 20 | 0 | gsd-secure-phase (Claude) |

---

## 签核

- [x] 所有威胁均有处置方案 (mitigate / accept / transfer)
- [x] 已接受风险已记录在已接受风险日志中
- [x] `threats_open: 0` 已确认
- [x] `status: verified` 已在前言中设置

**审批:** verified 2026-05-08
