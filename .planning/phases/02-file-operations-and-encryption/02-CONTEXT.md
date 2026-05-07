# Phase 02: 文件操作与加密 - Context

**Gathered:** 2026-05-07
**Status:** Ready for planning

## Phase Boundary

实现 `.secnote` 加密文件的完整生命周期——新建笔记本→保存（加密写入）→打开已有文件（解密读取）→另存为（更换路径/密码）→关闭时未保存变更检测与提示。密码输入对话框、最近文件列表管理和加密文件格式在此 Phase 中一并确定。

## Implementation Decisions

### 加密文件结构与密钥派生

- **D-21:** 使用 PBKDF2-SHA256 派生密钥，随机生成 16 字节 salt，迭代 600,000 轮。（超越 CRYPT-03 的纯 SHA-512 要求，增强暴力破解防护。）
- **D-22:** 独立派生 AES-256 密钥和 HMAC-SHA256 密钥——两次 PBKDF2 调用，使用不同 context 标签：`b'secnotepad-aes-key'` 和 `b'secnotepad-hmac-key'`，共用同一个 salt。每次派生输出 32 字节。
- **D-23:** 文件头采用固定二进制布局：`4B 魔数 'SN02'` + `1B 版本号 (1)` + `16B salt` + `16B IV` + `32B HMAC` + `AES-256-CFB 密文`。总头长度 69 字节。
- **D-24:** 加密流程：先对明文 JSON 计算 HMAC-SHA256 → 再对 JSON 做 AES-256-CFB 加密。解密时反向：解密 → 验证 HMAC。HMAC 不匹配时拒绝加载。
- **D-25:** 文件头版本号（二进制格式演进）与 JSON 内部 `version` 字段（数据格式演进，D-11）独立管理，两层各自迭代。
- **D-26:** 一次性全量文件读写——整个文件读入内存后解密，序列化后整个加密写入。不支持流式分块处理。
- **D-27:** AES 密钥和用户密码在内存中使用后显式清零（使用 `bytearray` 或 cryptography 库的安全缓冲区），不依赖 Python GC。
- **D-28:** 另存为时重新生成随机 salt 和随机 IV，使用新密码（如有）独立派生密钥。
- **D-29:** 密码仅支持 ASCII 字符（1-127）。

### 密码输入对话框设计

- **D-30:** 统一 `PasswordDialog(QDialog)`，通过模式参数切换三种场景：`SET_PASSWORD`（新建/首次保存）| `ENTER_PASSWORD`（打开文件）| `CHANGE_PASSWORD`（另存为可选更换）。
- **D-31:** `SET_PASSWORD` 模式显示确认密码字段，两个字段内容不一致时禁用确认按钮并显示警告。
- **D-32:** 实时密码强度指示器——用进度条或文字（弱/中/强）显示密码熵值评估。
- **D-33:** 密码生成器（CRYPT-04）：设密码模式下，对话框内放置「生成密码」按钮，点击弹出子对话框，可调长度（默认 16）和字符集（大小写字母+数字+符号可选）。
- **D-34:** 密码最小长度 8 字符。
- **D-35:** 打开文件密码错误时——在密码对话框内显示错误提示，允许用户重试，不关闭对话框。无重试次数限制。
- **D-36:** 首次保存流程顺序：先弹出 `QFileDialog` 选择保存路径（`.secnote` 过滤器）→ 确定路径后弹出密码对话框输入新密码。
- **D-37:** 密码显示/隐藏切换：`QLineEdit` 右侧内嵌眼睛图标按钮（`QAction` + `QIcon`），点击切换 EchoMode。
- **D-38:** 另存为模式：默认不显示密码字段，加 `QCheckBox「更换密码」`，勾选后才显示新密码和确认密码字段。不勾选则沿用当前密码。
- **D-39:** 对话框通过 `password()` getter 方法返回密码字符串。对话框 `accept()` 后调用方获取密码，用完立即清零。对话框内部不持有密码副本。

### 最近文件列表管理

- **D-40:** 使用 `QSettings` 存储，最多 5 条记录。
- **D-41:** 每条记录仅存储文件绝对路径。
- **D-42:** 加载列表时检查文件是否存在——不存在的条目静默跳过并从 QSettings 中移除，不弹错误提示。
- **D-43:** WelcomeWidget 中最近文件列表：单击文件名直接触发打开流程（弹出密码对话框）。
- **D-44:** 去重：打开已在列表中的文件时，将该条目移到列表顶部，不产生重复条目。

### 未保存检测与关闭保护

- **D-45:** MainWindow 维护 `_is_dirty: bool` 标志。Phase 2 提供 `mark_dirty()` 和 `mark_clean()` 公开接口，供后续 Phase 3（结构编辑）和 Phase 4（文本编辑）调用。Phase 2 本身仅对文件操作（新建/打开/关闭）管理脏状态。
- **D-46:** 关闭拦截：重写 `MainWindow.closeEvent()`，统一处理窗口 X 按钮关闭和 File→退出菜单。所有关闭路径经同一检查。
- **D-47:** 新建笔记本后不自动设脏标志。仅在用户实际修改（后续 Phase 的编辑操作调用 `mark_dirty()`）后才在关闭时提示保存。空的未保存笔记本关闭时不提示。
- **D-48:** 未保存提示对话框：`QMessageBox` 三个按钮——保存（触发保存流程）/ 不保存（放弃更改）/ 取消（留在当前状态不关闭）。

### Claude's Discretion

所有决策均由用户选择——无"Claude 决定"的领域。

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 需求与项目
- `.planning/REQUIREMENTS.md` — Phase 2 需求 FILE-02~05, CRYPT-01~04 的完整定义
- `.planning/PROJECT.md` — 技术栈约束（Python cryptography 库、整体文件加密）和关键决策
- `.planning/ROADMAP.md` — Phase 2 目标和 4 条成功标准

### 现有代码集成点
- `src/secnotepad/model/serializer.py` — `Serializer.to_json()` / `from_json()` 接口，加密层包装序列化后的 JSON 字符串
- `src/secnotepad/model/snote_item.py` — SNoteItem 数据模型，加密文件的最终载荷
- `src/secnotepad/ui/main_window.py` — `_on_open_notebook()`（桩函数）、`_on_new_notebook()`（创建内存笔记本）、Save/SaveAs 按钮和菜单项（灰显待激活）、`_root_item` 和 `_tree_model` 引用
- `src/secnotepad/ui/welcome_widget.py` — 最近文件列表占位区域，`new_notebook_clicked` / `open_notebook_clicked` 信号

### 参考项目
- `/home/jone/projects/SafetyNotebook` — 旧项目 C++/Qt5 安全笔记本 v0.1.2，加密方案思路来源（SHA-512 + AES 整体文件加密）

## Existing Code Insights

### Reusable Assets
- **Serializer.to_json/from_json:** 已实现 SNoteItem 树 ↔ JSON 字符串的双向转换。加密层直接对 JSON 字符串做加密/解密，无需感知 SNoteItem 结构。
- **SNoteItem / TreeModel:** 数据模型和 Qt Model 适配已就绪，打开文件后 `Serializer.from_json()` → `SNoteItem` → `TreeModel` → `QTreeView` 链路完整。
- **MainWindow 文件操作入口:** `_on_new_notebook()` 已有完整实现（创建根节点 + TreeModel + 切换到三栏布局），`_on_open_notebook()` 是桩函数。Save/SaveAs 的 QAction 和工具栏按钮已创建仅灰显。

### Established Patterns
- **QStackedWidget 页切换:** index 0 = WelcomeWidget，index 1 = 三栏布局。打开/新建笔记本后切换到 index 1。
- **信号驱动:** WelcomeWidget 通过 `new_notebook_clicked` / `open_notebook_clicked` 信号通知 MainWindow。
- **数据与视图分离:** SNoteItem（纯 dataclass）→ TreeModel（QAbstractItemModel）→ QTreeView，Phase 2 加密层在此链路之上。

### Integration Points
- `MainWindow._on_open_notebook()` 需替换为：QFileDialog 选文件 → PasswordDialog 输密码 → 读文件 + 解密 → HMAC 验证 → Serializer.from_json() → 更新 _root_item + _tree_model
- `MainWindow._act_save` / `_tb_save` 当前灰显，需在笔记本加载后启用
- `MainWindow._act_save_as` / `_tb_saveas` 同上
- WelcomeWidget 最近文件占位 QLabel 需替换为可交互列表

## Specific Ideas

- 旧项目 SafetyNotebook 的加密思路（SHA-512 派生密钥 → AES 加密整体 JSON）延续到新项目，但升级为 PBKDF2 + HMAC 的现代方案
- 密码生成器是可调参数的子对话框——用户明确想要灵活控制长度和字符集

## Deferred Ideas

None — discussion stayed within phase scope.

---

*Phase: 02-file-operations-and-encryption*
*Context gathered: 2026-05-07*
