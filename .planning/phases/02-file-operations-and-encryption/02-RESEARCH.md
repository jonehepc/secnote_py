# Phase 02: 文件操作与加密 — 研究

**研究日期:** 2026-05-07
**领域:** Python cryptography 加密库、PySide6 对话框设计、文件 I/O 与安全清零
**置信度:** HIGH

## 摘要

本阶段实现 `.secnote` 加密文件的完整生命周期：新建 → 保存（加密写入）→ 打开（解密读取）→ 另存为 → 关闭时未保存检测。核心加密方案使用 `cryptography` 库的 PBKDF2HMAC + AES-256-CFB + HMAC-SHA256，所有用户决策已在 CONTEXT.md 中锁定。

**关键发现:** `cryptography` 库自 v42.0.0 起已将 CFB 模式移入 `decrepit` 模块，计划在 v49.0.0 从当前命名空间移除。当前最新版本为 48.0.0，需要使用 `cryptography.hazmat.decrepit.ciphers.modes.CFB` 导入路径。此发现已记录在 Common Pitfalls 中，需在 plan-check 阶段告知用户。

**主要建议:** 严格遵循 D-21 至 D-48 的锁定决策。密码对话框使用统一 `PasswordDialog(QDialog)` 配合模式参数。文件头采用 69 字节固定二进制布局。

<phase_requirements>
## Phase 需求

| ID | 描述 | 研究支撑 |
|----|------|----------|
| FILE-02 | 打开 .secnote 文件，输入密钥解密加载 | `cryptography` AES-CFB 解密流程 + HMAC 验证 + `PasswordDialog(ENTER_PASSWORD)` |
| FILE-03 | 保存笔记本，加密写入 | PBKDF2 派生密钥 + AES-CFB 加密 + HMAC 附加 + 二进制文件头写入 |
| FILE-04 | 另存为新文件，指定新路径和新密钥 | 重新生成 salt/IV + 可选重新派生密钥 + QFileDialog |
| FILE-05 | 关闭时未保存更改提示保存 | `_is_dirty` 标志 + `closeEvent()` 重写 + QMessageBox 三按钮 |
| CRYPT-01 | 新建/另存时输入密钥，支持显示/隐藏 | `PasswordDialog(SET_PASSWORD)` / `(CHANGE_PASSWORD)` + QLineEdit QAction 切换 EchoMode |
| CRYPT-02 | 打开时输入密钥解密，错误时提示 | `PasswordDialog(ENTER_PASSWORD)` 错误保留 + HMAC 验证失败返回 |
| CRYPT-03 | SHA-512 + AES-256-CFB 加密 | **已升级为 PBKDF2-SHA256 (D-21)** — 见用户决策 |
| CRYPT-04 | 密码生成工具 | `secrets` 模块 + `PasswordGenerator` 子对话框 |
</phase_requirements>

## 架构职责映射

| 能力 | 主层 | 辅助层 | 理由 |
|------|------|--------|------|
| 密钥派生 (PBKDF2) | 数据/加密层 | — | 纯算法运算，无 UI 依赖 |
| AES 加密/解密 | 数据/加密层 | — | 操作字节数据，无 UI 依赖 |
| HMAC 计算与验证 | 数据/加密层 | — | 完整性校验，无 UI 依赖 |
| 文件头组装/解析 | 数据/加密层 | — | 二进制布局操作 |
| 文件读写 (QFile) | 数据/加密层 | — | 磁盘 I/O，不涉及渲染 |
| 密码对话框 | UI 层 | — | Qt 组件，QDialog 子类 |
| 密码生成器 | UI 层 | 标准库 `secrets` | 子对话框 + CSPRNG |
| 最近文件列表 | UI/数据边界 | QSettings | Qt 持久化存储 |
| 关闭保护 | UI 层 | — | MainWindow.closeEvent() |
| 脏标志管理 | 应用层 (MainWindow) | — | 公开接口供 Phase 3/4 |

## 标准栈

### 核心
| 库 | 版本 | 用途 | 为什么是标准 |
|-----|---------|---------|--------------|
| `cryptography` | 48.0.0 | PBKDF2 密钥派生、AES-256-CFB 加解密、HMAC-SHA256 | 项目约束指定 ([CITED: .planning/PROJECT.md]) |
| `PySide6` | 6.11.0 | QDialog、QLineEdit、QFileDialog、QSettings、QMessageBox | 项目技术栈已锁定 |

### 支撑
| 库 | 版本 | 用途 | 何时使用 |
|---------|---------|---------|-----------|
| `zxcvbn` (可选) | 4.5.0 | 密码熵值评估，替代简单的组合计数评估 | 密码强度指示器 [VERIFIED: pip registry] |
| `secrets` | Python 3.12 标准库 | CSPRNG 生成随机密码、salt、IV | 密码生成器、加密随机数 [ASSUMED] |
| `pytest-qt` | — | pytest plugin 用于 Qt 对话框测试 | 对话框中密码输入场景测试 [ASSUMED] |

### 考虑过的替代方案
| 替代方案 | 可考虑使用 | 取舍 |
|------------|-----------|---------|
| — | — | 所有决策已锁定 (D-21 至 D-48) |

### 安装
```bash
pip install cryptography>=48.0.0
# 可选密码强度评估
pip install zxcvbn>=4.5.0
```

### 版本验证
```bash
pip index versions cryptography  # 当前最新: 48.0.0
pip index versions zxcvbn        # 当前最新: 4.5.0
```

## 架构模式

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│  MainWindow                                              │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  Phase 2 新增: _is_dirty flag                       │ │
│  │  File Actions: New | Open | Save | SaveAs | Close   │ │
│  └──────────┬──────────────────────────────────────────┘ │
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │  PasswordDialog  (模式参数切换)                     │ │
│  │  SET_PASSWORD ─── ENTER_PASSWORD ─── CHANGE_PASSWORD│ │
│  │     ┌──────────────────────┐                        │ │
│  │     │ PasswordGenerator   │  (子对话框)             │ │
│  │     └──────────────────────┘                        │ │
│  └─────────────────────────────────────────────────────┘ │
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │  FileService  (新增: 加密/解密/文件I/O)              │ │
│  │  ┌────────────────────────────────────────────────┐  │ │
│  │  │ encrypt(json_str, password) → bytes            │  │ │
│  │  │ decrypt(file_bytes, password) → json_str       │  │ │
│  │  │ save(root_item, path, password)                │  │ │
│  │  │ open(path, password) → json_str                │  │ │
│  │  └────────────────────────────────────────────────┘  │ │
│  └──────────┬──────────────────────────────────────────┘ │
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │  Serializer (已有)  to_json / from_json              │ │
│  └─────────────────────────────────────────────────────┘ │
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │  SNoteItem (已有) + TreeModel (已有)                 │ │
│  └─────────────────────────────────────────────────────┘ │
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐ │
│  │  WelcomeWidget (改进)                               │ │
│  │  ┌─ 最近文件列表 (QListWidget) ───────────────────┐ │ │
│  │  │  最近打开的文件                      │
│  │  │  ├ /path/to/笔记1.secnote  ← 单击触发打开     │ │
│  │  │  ├ /path/to/笔记2.secnote                     │ │
│  │  │  └ (最多5条, 不存在则静默移除)                │ │
│  │  └───────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘

数据流 (保存):
  Serializer.to_json(root) → str → (PBKDF2 派生密钥) → HMAC(明文) →
  AES-256-CFB 加密(明文) → 组装文件头(魔数+版本+salt+IV+HMAC+密文) →
  QFile 写入

数据流 (打开):
  QFile 读取 → 解析文件头(魔数校验+版本+salt+IV+存储HMAC+密文) →
  PBKDF2 派生密钥 → AES-256-CFB 解密 → HMAC 验证(解密后明文) →
  Serializer.from_json(str) → SNoteItem 树
```

### 推荐项目结构

```
src/secnotepad/
├── __init__.py              # 已有
├── __main__.py              # 已有
├── app.py                   # 已有
├── model/                   # 已有
│   ├── __init__.py
│   ├── snote_item.py
│   ├── serializer.py
│   ├── tree_model.py
│   └── validator.py
├── crypto/                  # ★ 新增: 加密模块
│   ├── __init__.py
│   ├── file_service.py      # 加密/解密/文件读写编排
│   └── header.py            # 文件头定义 + 组装/解析
└── ui/                      # 已有 + 扩展
    ├── __init__.py
    ├── main_window.py       # 修改: _on_open/closeEvent/dirty flag
    ├── welcome_widget.py    # 修改: 最近文件列表
    ├── password_dialog.py   # ★ 新增: 统一密码对话框
    └── password_generator.py# ★ 新增: 密码生成器子对话框

tests/
├── __init__.py
├── conftest.py              # 已有
├── model/                   # 已有测试
│   ├── test_serializer.py
│   ├── test_snote_item.py
│   ├── test_tree_model.py
│   └── test_validator.py
├── crypto/                  # ★ 新增: 加密模块测试
│   ├── __init__.py
│   ├── test_file_service.py
│   └── test_header.py
└── ui/                      # ★ 新增: UI 测试
    ├── __init__.py
    └── test_password_dialog.py
```

### 模式 1: 加密文件处理 (Encrypt-then-MAC)

**用途:** 所有加密文件操作的统一编排。

```
根据 D-24 设计:
1. PBKDF2-SHA256 派生 AES_KEY + HMAC_KEY (D-21, D-22)
2. 对明文 JSON 计算 HMAC-SHA256 (先 MAC 后加密)
3. AES-256-CFB 加密明文
4. 组装: 魔数(4B) + 版本(1B) + salt(16B) + IV(16B) + HMAC(32B) + 密文
5. 解密反向: 解析头 → 解密 → 验证 HMAC
```

### 反模式: 避免

- **不要在 UI 线程中进行大文件加解密:** 本阶段使用一次性全量读写 (D-26)，文件较小（KB-MB 级别），直接在 UI 线程操作可接受。如未来需要处理大文件，需迁移到 QThread。
- **不要在生产密码中使用直接 SHA-512:** 已通过 D-21 升级为 PBKDF2。
- **不要依赖 Python GC 清理敏感数据:** 使用 `bytearray` 显式清零 (D-27)。

## 非手写轮子清单

| 问题 | 不要自己构建 | 使用替代方案 | 为什么 |
|------|-------------|-------------|--------|
| 密钥派生 | PBKDF2 实现 | `cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC` | 侧信道攻击、内存安全、经过审计 |
| AES 加密 | 纯 Python AES 实现 | `cryptography.hazmat.primitives.ciphers.Cipher` + `algorithms.AES` | 性能、安全审计、硬件 AES-NI 加速 |
| HMAC | HMAC 实现 | `cryptography.hazmat.primitives.hmac.HMAC` | 标准实现，常量时间比较 |
| CSPRNG | `random` 模块 | `os.urandom()` / `secrets` 模块 | `random` 模块是伪随机，不可用于加密 |
| Qt 设置存储 | 自定义 JSON 配置文件 | `QSettings` | 跨平台、原生 API、自动处理 INI/注册表 |

**关键洞察:** 加密领域错误代价极高。使用 `cryptography` 库的 hazmat 层虽然 API 更低级，但只要正确使用模式（PBKDF2 + AES + HMAC），安全性远高于自行实现。

## 常见陷阱

### 陷阱 1: CFB 模式已废弃（重要）
**问题:** `cryptography` 库自 v42.0.0 起已将 CFB/CFB8/OFB 模式移入 `decrepit` 模块，计划在 v49.0.0 从当前命名空间移除。
**根因:** 库维护者认为这些模式在现代应用中应避免使用，推荐使用 AEAD 模式（如 AES-GCM）。
**如何避免:**
```
# 正确的导入路径 (cryptography >= 42.0.0):
from cryptography.hazmat.decrepit.ciphers.modes import CFB

# 而不是:
from cryptography.hazmat.primitives.ciphers.modes import CFB  # 将在 v49 删除
```
**警告信号:** `ImportError: cannot import name 'CFB' from 'cryptography.hazmat.primitives.ciphers.modes'` （升级到 cryptography 49+ 时出现）
**建议:** 由于 D-24 锁定了 AES-256-CFB，使用 `decrepit` 导入路径。在 plan-check 或 discuss 阶段可告知用户此风险，询问是否愿意改为 AES-256-GCM（更现代、AEAD 内置完整性）。

### 陷阱 2: 密码字符串未及时清零
**问题:** Python `str` 是不可变对象，无法原地清空。密码在内存中残留。
**根因:** 使用 `str` 存储密码后，只能靠 GC 回收，无法主动擦除。
**如何避免:**
- 对话框内部使用 `bytearray` 存储密码 (D-39)
- 提供 `clear_password()` 方法，调用后 `password_bytes[:] = b'\x00' * len(password_bytes)`
- 调用方读取密码后立即清零
- 参见 `cryptography` 文档 [limitations.rst](https://github.com/pyca/cryptography/blob/main/docs/limitations.rst)

### 陷阱 3: QSettings 写入列表后需要 endArray
**问题:** QSettings 的 `beginWriteArray` 不自动结束数组，忘记调用 `endArray` 会导致后续写入混乱。
**根因:** Qt C++ 风格的数组写入 API 要求对称调用。
**如何避免:** 始终成对使用 `beginWriteArray` / `endArray`，或使用简单替代方案：
```python
settings.setValue("recent_files", paths)  # 直接存 QStringList
```
**注意:** 简单方式在 QSettings INI 格式中可能丢失类型区分。对本场景（纯路径字符串列表）足够。

### 陷阱 4: HMAC 验证时序攻击
**问题:** 使用常规比较（`==`）比对 HMAC tag 可能泄露信息。
**根因:** `==` 在发现第一个不同字节时即返回，具有时序差异。
**如何避免:**
```python
from cryptography.hazmat.primitives.constant_time import bytes_eq
if not bytes_eq(computed_hmac, stored_hmac):
    raise ValueError("密码错误")
```

### 陷阱 5: 文件路径编码问题
**问题:** 中文文件名在跨平台时可能出现编码问题。
**根因:** 不同系统默认编码不同。
**如何避免:** 使用 `QFileDialog.selectedFiles()` 返回的路径（Qt 内部处理编码），存储路径时使用绝对路径 `os.path.abspath()`。

## 代码示例

### 示例 1: PBKDF2 派生两个独立密钥 (D-21, D-22)

```python
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def derive_keys(password: bytes, salt: bytes) -> tuple[bytes, bytes]:
    """派生 AES-256 密钥和 HMAC-SHA256 密钥。

    Args:
        password: 用户密码 (ASCII, byte 编码)
        salt: 16 字节随机 salt

    Returns:
        (aes_key, hmac_key) 各 32 字节
    """
    aes_kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    aes_key = aes_kdf.derive(password + b'secnotepad-aes-key')

    hmac_kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    hmac_key = hmac_kdf.derive(password + b'secnotepad-hmac-key')

    return aes_key, hmac_key
```

### 示例 2: 加密文件头组装 (D-23)

```python
import struct

MAGIC = b'SN02'
VERSION = 1
HEADER_SIZE = 69  # 4 + 1 + 16 + 16 + 32

def build_header(salt: bytes, iv: bytes, hmac_tag: bytes) -> bytes:
    """组装固定 69 字节文件头。"""
    assert len(salt) == 16
    assert len(iv) == 16
    assert len(hmac_tag) == 32
    return struct.pack(
        '!4s B 16s 16s 32s',
        MAGIC, VERSION, salt, iv, hmac_tag,
    )

def parse_header(data: bytes) -> dict:
    """解析文件头，返回各部分。"""
    assert len(data) >= HEADER_SIZE
    magic, version, salt, iv, hmac_tag = struct.unpack(
        '!4s B 16s 16s 32s', data[:HEADER_SIZE]
    )
    if magic != MAGIC:
        raise ValueError(f"无效的魔数: {magic!r}")
    return {
        'version': version,
        'salt': salt,
        'iv': iv,
        'hmac_tag': hmac_tag,
        'ciphertext': data[HEADER_SIZE:],
    }
```

### 示例 3: 加密流程 (Encrypt-then-MAC)

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.decrepit.ciphers.modes import CFB
from cryptography.hazmat.primitives import hmac as hmac_mod, hashes

def encrypt(plaintext: bytes, aes_key: bytes, hmac_key: bytes, iv: bytes) -> bytes:
    """加密明文并计算 HMAC。"""
    # 先计算 HMAC
    h = hmac_mod.HMAC(hmac_key, hashes.SHA256())
    h.update(plaintext)
    hmac_tag = h.finalize()

    # 再加密
    cipher = Cipher(algorithms.AES(aes_key), CFB(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    return ciphertext, hmac_tag

def decrypt(ciphertext: bytes, aes_key: bytes, hmac_key: bytes,
            iv: bytes, expected_hmac: bytes) -> bytes:
    """解密密文并验证 HMAC。"""
    from cryptography.hazmat.primitives.constant_time import bytes_eq

    # 先解密
    cipher = Cipher(algorithms.AES(aes_key), CFB(iv))
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # 再验证 HMAC
    h = hmac_mod.HMAC(hmac_key, hashes.SHA256())
    h.update(plaintext)
    computed_hmac = h.finalize()

    if not bytes_eq(computed_hmac, expected_hmac):
        raise ValueError("密码错误")

    return plaintext
```

### 示例 4: QLineEdit 密码可见性切换

```python
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QStyle

class PasswordField(QLineEdit):
    """带显示/隐藏切换的密码输入框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.Password)

        # 眼睛图标按钮
        self._toggle_action = QAction(self)
        self._toggle_action.setCheckable(True)
        # 使用 Qt 内置图标
        eye_icon = self.style().standardIcon(
            QStyle.SP_FileDialogListView)  # 替换为合适的图标
        self._toggle_action.setIcon(eye_icon)
        self._toggle_action.triggered.connect(self._toggle_echo)
        self.addAction(self._toggle_action, QLineEdit.TrailingPosition)

    def _toggle_echo(self, checked: bool):
        self.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )
```

### 示例 5: QSettings 最近文件读写 (D-40 ~ D-44)

```python
from PySide6.QtCore import QSettings
import os

MAX_RECENT_FILES = 5
SETTINGS_KEY = "recent_files"

def load_recent_files() -> list[str]:
    """从 QSettings 加载最近文件列表，过滤不存在的文件。"""
    settings = QSettings()
    paths = settings.value(SETTINGS_KEY, [])
    if paths is None:
        return []
    # 过滤不存在的文件 (D-42)
    valid = [p for p in paths if os.path.isfile(p)]
    # 如有移除，回写更新
    if len(valid) < len(paths):
        settings.setValue(SETTINGS_KEY, valid)
    return valid

def add_recent_file(path: str):
    """添加文件到最近列表，去重并限制数量。"""
    settings = QSettings()
    paths = settings.value(SETTINGS_KEY, [])
    if paths is None:
        paths = []
    # 去重: 移到顶部 (D-44)
    if path in paths:
        paths.remove(path)
    paths.insert(0, path)
    # 限制数量 (D-40)
    paths = paths[:MAX_RECENT_FILES]
    settings.setValue(SETTINGS_KEY, paths)
```

## 技术现状

| 旧方法 | 当前方法 | 变更时间 | 影响 |
|----------|---------|-----------|--------|
| SHA-512(password) 直接派生 | PBKDF2-SHA256 600k 迭代 | D-21 决策 | 暴力破解难度大幅提升 |
| 单一密钥 | AES + HMAC 独立密钥派生 | D-22 决策 | 密钥分离增强安全性 |
| CFB 在 ciphers.modes 下 | CFB 在 hazmat.decrepit.ciphers.modes 下 | cryptography 42.0.0 | 需使用 decrepit 导入路径 |

**废弃/过时:**
- `cryptography.hazmat.primitives.ciphers.modes.CFB`: 自 cryptography 42.0.0 废弃，移入 decrepit 模块。v49.0.0 将从当前命名空间移除。当前最新版本 48.0.0 仍支持 `decrepit` 导入路径。

## 假设日志

| # | 声明 | 章节 | 风险 |
|---|-------|---------|---------|
| A1 | `secrets` 模块的 CSPRNG 足以生成密码、salt 和 IV | 标准栈 | 低 — Python 官方推荐用于加密随机数，参见 [random-numbers.rst](https://github.com/pyca/cryptography/blob/main/docs/random-numbers.rst) |
| A2 | `pytest-qt` 可用于 Qt 对话框测试 | 标准栈 | 低 — 标准 pytest 插件，与当前 pytest 9.0.3 兼容 |
| A3 | 使用 `QLineEdit.addAction` + `QLineEdit.TrailingPosition` 实现眼睛图标按钮 | 代码示例 | 低 — Qt6 标准 API，已在多个 Qt/Python 项目中使用 |
| A4 | zxcvbn 库可用于密码强度评估 | 标准栈 | 中 — 需在 plan-check 中与用户确认是否使用该库或实现简易评估 |

## 待解决问题（已全部解决）

以下三个问题已在规划阶段通过用户决策和 Claude 自主决策解决：

1. ~~**CFB 废弃是否影响用户选择 D-24 的 AES-256-CFB?**~~
   - **状态: RESOLVED** — 2026-05-07
   - **决策:** 锁定 D-24 保持 AES-256-CFB，使用 `cryptography.hazmat.decrepit.ciphers.modes.CFB` 导入路径。用户已知 CFB 废弃状态（已在 CONTEXT.md 中记录风险）。如果 cryptography 49+ 完全移除 CFB，届时迁移到 AES-256-GCM。
   - **代码示例 3 和 Plan 03 已使用 decrepit 导入路径。**

2. ~~**密码强度指示器实现方式?**~~
   - **状态: RESOLVED** — 2026-05-07
   - **决策:** 使用简易熵值计算（字符集大小 × 长度），不使用 zxcvbn 库。避免额外依赖，且当前场景对密码强度准确度要求不高。D-32 已锁定此方案。
   - **密码强度评估代码已在 Plan 02 Task 2 中实现。**

3. ~~**文件服务是独立类还是静态方法?**~~
   - **状态: RESOLVED** — 2026-05-07
   - **决策:** 纯静态方法（`@staticmethod`），不维护状态。加密操作每次独立派生密钥，无状态保持需求。
   - **Plan 03 FileService 已实现为静态方法类。**

## 环境可用性

| 依赖 | 需要者 | 可用 | 版本 | 回退方案 |
|------------|------------|---------|---------|----------|
| Python 3.12+ | 所有功能 | ✓ | 3.12.3 | — |
| PySide6 6.11+ | UI | ✓ | 6.11.0 | — |
| pytest 9.x | 测试 | ✓ | 9.0.3 | — |
| cryptography | 加密 | ✗ 需安装 | 48.0.0 (目标) | 无回退 — 项目强制要求 |

**缺失且无回退的依赖:**
- `cryptography`: 必须安装。`pip install cryptography>=48.0.0`

## 验证架构

### 测试框架
| 属性 | 值 |
|----------|-------|
| 框架 | pytest 9.0.3 |
| 配置文件 | `pyproject.toml` — `[tool.pytest.ini_options]` |
| 快速运行命令 | `python -m pytest tests/ -x --timeout=30 -q` |
| 完整套件命令 | `python -m pytest tests/` |

### Phase 需求 → 测试映射
| Req ID | 行为 | 测试类型 | 自动化命令 | 文件存在? |
|--------|----------|-----------|-------------------|-------------|
| FILE-02 | 打开 .secnote 文件并解密 | 集成 | `pytest tests/crypto/test_file_service.py::test_open_decrypt -x` | ❌ Wave 0 |
| FILE-03 | 保存时加密写入 | 集成 | `pytest tests/crypto/test_file_service.py::test_save_encrypt -x` | ❌ Wave 0 |
| FILE-04 | 另存为更换路径和密码 | 集成 | `pytest tests/crypto/test_file_service.py::test_save_as -x` | ❌ Wave 0 |
| FILE-05 | 关闭时脏检测提示 | UI | `pytest tests/ui/test_password_dialog.py::test_close_with_dirty -x` | ❌ Wave 0 |
| CRYPT-01 | 密码对话框模式切换 | UI | `pytest tests/ui/test_password_dialog.py::test_set_password_mode -x` | ❌ Wave 0 |
| CRYPT-02 | 密钥错误无法加载 | 集成 | `pytest tests/crypto/test_file_service.py::test_wrong_password -x` | ❌ Wave 0 |
| CRYPT-03 | PBKDF2 + AES-256-CFB | 单元 | `pytest tests/crypto/test_file_service.py::test_encrypt_decrypt_roundtrip -x` | ❌ Wave 0 |
| CRYPT-04 | 密码生成器 | UI | `pytest tests/ui/test_password_dialog.py::test_password_generator -x` | ❌ Wave 0 |

### 采样率
- **每次任务提交:** 运行 `python -m pytest tests/crypto/ -x --timeout=30 -q`
- **每次合并前:** 运行 `python -m pytest tests/ -x --timeout=60`
- **阶段门控:** 完整套件全部通过后执行 `/gsd-verify-work`

### Wave 0 差距
- [ ] `tests/crypto/__init__.py` — 空包文件
- [ ] `tests/crypto/test_header.py` — 文件头组装/解析测试
- [ ] `tests/crypto/test_file_service.py` — 加密/解密/保存/打开/另存为集成测试
- [ ] `tests/ui/__init__.py` — 空包文件
- [ ] `tests/ui/test_password_dialog.py` — 密码对话框模式测试
- [ ] `tests/conftest.py` 扩展 — 加密测试 fixture（临时目录、测试密码、示例密钥）
- [ ] pytest 插件: 无额外插件要求（pytest-qt 可选）
- [ ] 安全性测试: HMAC 篡改检测、空密码拒绝、暴力破解无限制（D-35）检查

## 安全领域

### 适用的 ASVS 类别

| ASVS 类别 | 适用 | 标准控制 |
|-----------|---------|-----------------|
| V2 认证 | 否 | 本地文件加密，非用户认证 |
| V3 会话管理 | 否 | 无会话 |
| V4 访问控制 | 否 | 无用户/角色系统 |
| V5 输入验证 | 是 | 密码 ASCII 限制 (D-29) + 文件头魔数校验 |
| V6 加密 | 是 | PBKDF2-SHA256 + AES-256-CFB + HMAC-SHA256 |
| V7 错误处理 | 是 | HMAC 验证失败返回通用错误消息("密码错误") |
| V8 数据保护 | 是 | 全量文件加密 + 内存中密钥清零 |
| V9 通信 | 否 | 纯本地应用 |
| V10 恶意代码 | 是 | 反序列化前验证 HMAC，拒绝篡改数据 |
| V11 业务逻辑 | 是 | 密码错误无重试限制 (D-35)，需在 UI 层避免暴力破解误解 |

### 已知 {加密栈} 的威胁模式

| 模式 | STRIDE | 标准缓解措施 |
|---------|--------|---------------------|
| 密码暴力破解 | 篡改 | PBKDF2 600k 迭代 (D-21) 减慢离线破解；无重试限制仅为用户体验选择 (D-35)，安全上可接受 |
| 文件篡改 | 篡改 | HMAC-SHA256 完整性校验 (D-24) |
| 内存中秘密泄露 | 信息泄露 | bytearray 显式清零 (D-27) |
| 时序侧信道 | 信息泄露 | `constant_time.bytes_eq` 常量时间比较 |
| PBKDF2 盐重复 | 篡改 | 每次保存生成新随机盐 (D-28) |
| 版本回滚攻击 | 篡改 | 文件头版本号 (D-25) 检查，不可降级到旧版本 |

## 来源

### 主要 (HIGH 置信度)
- [Context7: /pyca/cryptography](https://cryptography.io/en/latest/) — PBKDF2HMAC API、AES-CFB、HMAC-SHA256、decrepit 模块配置、常量时间比较、安全内存限制
- [Context7: /websites/doc_qt_io_qtforpython-6](https://doc.qt.io/qtforpython-6/) — QLineEdit、QSettings、QDialog 模式、QFileDialog
- [pip registry](https://pypi.org/project/cryptography/) — cryptography 48.0.0、zxcvbn 4.5.0 版本验证
- `.planning/REQUIREMENTS.md` — 需求定义
- `.planning/CONTEXT.md` — 锁定决策 D-21 至 D-48

### 次要 (MEDIUM 置信度)
- [documentation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QSettings.html) — QSettings beginWriteArray/beginReadArray API
- [documentation](https://cryptography.io/en/latest/hazmat/limitations/) — 安全内存限制说明

### 三级 (LOW 置信度)
- WebSearch: Qiita 博客相关引用 — 未使用，所有关键信息已通过 Context7 和官方文档验证

## 元数据

**置信度细分:**
- 标准栈: HIGH — 所有栈组件已验证（cryptography 48.0.0, PySide6 6.11.0）
- 架构: HIGH — 用户决策完全锁定，数据流清晰
- 陷阱: HIGH — CFB deprecated 状态通过官方文档验证
- 假设日志: 4 个 LOW 假设等待确认

**研究日期:** 2026-05-07
**有效期至:** 2026-06-07（稳定库版本，30 天内有效）
