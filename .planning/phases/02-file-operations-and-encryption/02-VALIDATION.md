# Phase 02: 文件操作与加密 — 验证架构

**提取自:** 02-RESEARCH.md `## 验证架构` 章节
**状态:** 用户已接受 Nyquist 合规偏差（`Continue anyway`），此文件为最小提取版本

## 测试框架

| 属性 | 值 |
|----------|-------|
| 框架 | pytest 9.0.3 |
| 配置文件 | `pyproject.toml` — `[tool.pytest.ini_options]` |
| 快速运行命令 | `python -m pytest tests/ -x --timeout=30 -q` |
| 完整套件命令 | `python -m pytest tests/` |

## Phase 需求 → 测试映射

| Req ID | 行为 | 测试类型 | 自动化命令 | 文件存在? |
|--------|----------|-----------|-------------------|-------------|
| FILE-02 | 打开 .secnote 文件并解密 | 集成 | `pytest tests/crypto/test_file_service.py::test_open_decrypt -x` | Wave 0 |
| FILE-03 | 保存时加密写入 | 集成 | `pytest tests/crypto/test_file_service.py::test_save_encrypt -x` | Wave 0 |
| FILE-04 | 另存为更换路径和密码 | 集成 | `pytest tests/crypto/test_file_service.py::test_save_as -x` | Wave 0 |
| FILE-05 | 关闭时脏检测提示 | UI | `pytest tests/ui/test_password_dialog.py::test_close_with_dirty -x` | Wave 0 |
| CRYPT-01 | 密码对话框模式切换 | UI | `pytest tests/ui/test_password_dialog.py::test_set_password_mode -x` | Wave 0 |
| CRYPT-02 | 密钥错误无法加载 | 集成 | `pytest tests/crypto/test_file_service.py::test_wrong_password -x` | Wave 0 |
| CRYPT-03 | PBKDF2 + AES-256-CFB | 单元 | `pytest tests/crypto/test_file_service.py::test_encrypt_decrypt_roundtrip -x` | Wave 0 |
| CRYPT-04 | 密码生成器 | UI | `pytest tests/ui/test_password_dialog.py::test_password_generator -x` | Wave 0 |

## 采样率

- **每次任务提交:** 运行 `python -m pytest tests/crypto/ -x --timeout=30 -q`
- **每次合并前:** 运行 `python -m pytest tests/ -x --timeout=60`
- **阶段门控:** 完整套件全部通过后执行 `/gsd-verify-work`

## Wave 0 差距

- [ ] `tests/crypto/__init__.py` — 空包文件
- [ ] `tests/crypto/test_header.py` — 文件头组装/解析测试
- [ ] `tests/crypto/test_file_service.py` — 加密/解密/保存/打开/另存为集成测试
- [ ] `tests/ui/__init__.py` — 空包文件
- [ ] `tests/ui/test_password_dialog.py` — 密码对话框模式测试
- [ ] `tests/conftest.py` 扩展 — 加密测试 fixture（临时目录、测试密码、示例密钥）
- [ ] pytest 插件: 无额外插件要求（pytest-qt 可选）
- [ ] 安全性测试: HMAC 篡改检测、空密码拒绝、暴力破解无限制（D-35）检查

---

*提取自 RESEARCH.md 验证架构章节 · 2026-05-07*
