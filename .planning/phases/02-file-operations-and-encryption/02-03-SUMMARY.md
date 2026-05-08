---
phase: 02-file-operations-and-encryption
plan: 03
subsystem: crypto
tags:
  - cryptography
  - pbkdf2
  - aes-256-cfb
  - hmac-sha256
  - file-io
  - tdd
requires:
  - 02-01-PLAN.md (header.py — Header.build/parse, HeaderError)
provides:
  - src/secnotepad/crypto/file_service.py
  - tests/crypto/test_file_service.py
affects:
  - MainWindow (will use FileService.save/open in 02-04)
tech-stack:
  added:
    - cryptography 48.0.0 (PBKDF2HMAC, AES-CFB, HMAC-SHA256)
  patterns:
    - Static-method service class (following Serializer pattern)
    - Encrypt-then-MAC: HMAC(plaintext) → AES-CFB encrypt → header assembly
    - Decrypt-then-verify: header parse → AES-CFB decrypt → HMAC verify
key-files:
  created:
    - src/secnotepad/crypto/file_service.py (202 lines)
    - tests/crypto/test_file_service.py (145 lines)
decisions:
  - password.isascii() guard at encrypt time (D-29)
  - CFB from cryptography.hazmat.decrepit (RESEARCH trap 1)
  - bytes_eq() constant-time comparison (RESEARCH trap 4)
metrics:
  duration: ~10 min
  completed_date: "2026-05-07"
---

# Phase 02 Plan 03: 加密文件服务 (FileService) — Summary

实现完整的加密文件服务层，提供 PBKDF2 + AES-256-CFB + HMAC-SHA256 的加密/解密/保存/打开/另存为编排。作为 MainWindow 与磁盘文件之间的加密桥梁。

## 执行摘要

使用 TDD 流程完成 RED/GREEN 阶段：

- **RED:** 创建 16 个测试用例覆盖加密 roundtrip、密码错误拒绝、空密码、空数据、篡改检测、文件保存/打开 roundtrip、另存为新密码、文件不存在等场景。
- **GREEN:** 实现 FileService 静态类，提供 `encrypt`, `decrypt`, `save`, `open`, `save_as` 五个方法，遵循 Encrypt-then-MAC 模式。
- **REFACTOR:** 不需要 — 代码已满足模块级常量、docstring 格式、import 顺序规范。

## 架构说明

FileService 作为纯数据层，不依赖 Qt 或 UI 组件：

- 输入输出均为 `str`（JSON 文本）/ `bytes`（加密文件）/ 文件路径
- 与 Header 模块的连接：`Header.build()` 组装文件头，`Header.parse()` 解析文件头
- 与 Serializer 的连接：FileService 操作 JSON 文本字符串，Serializer 负责 SNoteItem ↔ JSON 的转换（在 02-04 MainWindow 集成）

## 安全要点

| 控制 | 实现位置 | 覆盖威胁 |
|------|----------|----------|
| HMAC-SHA256 完整性校验 | `decrypt()` 中 `bytes_eq()` 比较 | T-02-08 |
| 每次加密新随机 salt | `encrypt()` 调用 `_generate_salt()` | T-02-09 |
| 统一错误消息 "密码错误" | `decrypt()` 不区分 HMAC/AES 错误 | T-02-10 |
| 魔数校验 | 委托给 `Header.parse()` | T-02-11 |
| 常量时间 HMAC 比较 | `bytes_eq()` | T-02-12 |
| PBKDF2 600k 迭代 | `_derive_keys()` | T-02-13 |
| CFB 从 decrepit 导入 | `from cryptography.hazmat.decrepit.ciphers.modes import CFB` | T-02-15 |

## 测试结果

16 项测试全部通过，耗时 2.9 秒：

| 类别 | 数量 | 覆盖内容 |
|------|------|----------|
| EncryptDecrypt | 6 | roundtrip、魔数校验、非明文、错误密码、空字符串、空数据 |
| FileSaveOpen | 4 | save/open roundtrip、文件存在校验、错误密码、文件不存在 |
| SaveAs | 2 | 新路径、新密码 |
| EdgeCases | 4 | 篡改密文、篡改魔数、篡改 HMAC、空密码 |

## Deviations from Plan

无 — 计划完全按预期执行。

## TDD Gate Compliance

- [x] RED gate: `c6c82bd` — `test(02-03): add failing test for FileService encrypt/decrypt/save/open`
- [x] GREEN gate: `a8124fd` — `feat(02-03): implement FileService with PBKDF2 + AES-256-CFB + HMAC-SHA256`
- [ ] REFACTOR gate: 未执行（代码已满足规范）

Compliant — RED 提交先于 GREEN 提交，门控顺序正确。

## Known Stubs

无。

## Threat Flags

无 — 所有加密表面均在计划 threat_model 覆盖范围内。

## Self-Check: PASSED

- [x] `src/secnotepad/crypto/file_service.py` 存在 (202 行，>= 150)
- [x] `tests/crypto/test_file_service.py` 存在 (145 行，>= 100)
- [x] RED commit `c6c82bd` 存在于 git log
- [x] GREEN commit `a8124fd` 存在于 git log
- [x] pytest 16/16 通过
