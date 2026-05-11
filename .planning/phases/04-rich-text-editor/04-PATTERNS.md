# Phase 04: 富文本编辑器 - Pattern Map

**Mapped:** 2026-05-09
**Files analyzed:** 6
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/secnotepad/ui/rich_text_editor.py` | component | event-driven + transform | `src/secnotepad/ui/password_dialog.py` | role-match |
| `src/secnotepad/ui/main_window.py` | component/controller | event-driven + file-I/O + request-response | `src/secnotepad/ui/main_window.py` | exact |
| `tests/ui/test_rich_text_editor.py` | test | event-driven UI | `tests/ui/test_password_dialog.py` + `tests/ui/test_navigation.py` | role-match |
| `tests/ui/test_main_window.py` | test | event-driven UI + request-response | `tests/ui/test_main_window.py` | exact |
| `tests/ui/test_navigation.py` | test | event-driven UI + CRUD | `tests/ui/test_navigation.py` | exact |
| `tests/model/test_serializer.py` | test | transform | `tests/model/test_serializer.py` | exact |

## Pattern Assignments

### `src/secnotepad/ui/rich_text_editor.py` (component, event-driven + transform)

**Analog:** `src/secnotepad/ui/password_dialog.py`

**Imports pattern** (lines 5-10):
```python
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                QLabel, QLineEdit, QPushButton,
                                QCheckBox, QProgressBar, QStyle)
```

**组件初始化与私有状态 pattern** (lines 25-50):
```python
    def __init__(self, mode: PasswordMode, parent=None):
        super().__init__(parent)
        self._mode = mode
        self._password = bytearray()

        self.setModal(True)

        # --- 窗口标题 ---
        titles = {
            PasswordMode.SET_PASSWORD: "设置加密密码",
            PasswordMode.ENTER_PASSWORD: "输入密码",
            PasswordMode.CHANGE_PASSWORD: "更换密码",
        }
        self.setWindowTitle(titles[mode])

        # --- 主布局 ---
        layout = QVBoxLayout(self)

        # --- CHANGE_PASSWORD 模式: 更换密码复选框 ---
        self._cb_change = None
        self._change_widgets = []  # 复选框控制显示/隐藏的控件
        if mode == PasswordMode.CHANGE_PASSWORD:
            self._cb_change = QCheckBox("更换密码")
            self._cb_change.setChecked(False)
            self._cb_change.toggled.connect(self._on_change_toggled)
            layout.addWidget(self._cb_change)
```

**Action 创建与 signal 连接 pattern** (lines 136-154):
```python
        # --- 确认 / 取消按钮 ---
        btn_layout = QHBoxLayout()
        self._btn_confirm = QPushButton("确认")
        self._btn_confirm.clicked.connect(self._on_confirm)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_confirm)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # --- 信号连接 ---
        self._pwd_input.textChanged.connect(self._on_password_changed)
        self._confirm_input.textChanged.connect(self._on_password_changed)
        self.rejected.connect(self.clear_password)

        # --- 初始状态 ---
        self._update_confirm_button()
```

**Checkable QAction pattern** (lines 219-232):
```python
    def _add_eye_toggle(self, line_edit: QLineEdit):
        """在 QLineEdit 右侧添加眼睛图标切换密码可见性 (D-37)。

        Note: Qt 无标准眼睛图标，使用显示/隐藏视觉替代。
        如需眼睛图标，应使用自定义资源文件 (QRC)。
        """
        action = QAction(line_edit)
        action.setCheckable(True)
        icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        action.setIcon(icon)
        action.triggered.connect(lambda checked: line_edit.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        line_edit.addAction(action, QLineEdit.TrailingPosition)
```

**状态同步 pattern** (lines 234-267):
```python
    def _on_password_changed(self):
        """密码字段变化时更新强度、警告和确认按钮状态。"""
        pwd_text = self._pwd_input.text()
        confirm_text = self._confirm_input.text()

        # 强度指示器（仅 SET_PASSWORD 或 CHANGE_PASSWORD+checked）
        if self._mode in (PasswordMode.SET_PASSWORD, PasswordMode.CHANGE_PASSWORD):
            if pwd_text:
                pct, label = self._evaluate_strength(pwd_text)
                self._strength_bar.setValue(pct)
                self._strength_label.setText(label)
                self._strength_bar.setVisible(True)
                self._strength_label.setVisible(True)
                # 设置颜色
                if pct <= 33:
                    self._strength_bar.setStyleSheet(
                        "QProgressBar::chunk { background-color: red; }")
                elif pct <= 66:
                    self._strength_bar.setStyleSheet(
                        "QProgressBar::chunk { background-color: orange; }")
                else:
                    self._strength_bar.setStyleSheet(
                        "QProgressBar::chunk { background-color: green; }")
            else:
                self._strength_bar.setVisible(False)
                self._strength_label.setVisible(False)

            # 警告：两次密码不一致
            if pwd_text and confirm_text and pwd_text != confirm_text:
                self._mismatch_warning.setVisible(True)
            else:
                self._mismatch_warning.setVisible(False)

        self._update_confirm_button()
```

**输入校验/确认处理 pattern** (lines 290-305):
```python
    def _on_confirm(self):
        """确认按钮点击处理。"""
        pwd_text = self._pwd_input.text()
        if pwd_text and not pwd_text.isascii():
            error_label = getattr(self, '_error_label', None) or self._mismatch_warning
            error_label.setText("密码仅支持 ASCII 字符")
            error_label.setVisible(True)
            return
        if self._mode == PasswordMode.CHANGE_PASSWORD:
            if self._cb_change and self._cb_change.isChecked():
                self._password = bytearray(pwd_text.encode('ascii'))
            else:
                self._password = bytearray()
        else:
            self._password = bytearray(pwd_text.encode('ascii'))
        self.accept()
```

**需要复制到新富文本组件的要点：**
- 像 `PasswordDialog` 一样在 `__init__` 中建立私有控件字段、布局、signal 连接和初始状态。
- 格式按钮用 `QAction` / `QToolBar` / `QActionGroup`；可选状态参考 `setCheckable(True)`。
- 光标/文档状态同步写成私有 `_sync_*` 方法，连接 `QTextEdit.currentCharFormatChanged`、`cursorPositionChanged`、`copyAvailable`、`document().undoAvailable`、`document().redoAvailable`。
- 粘贴净化若采用 `QTextEdit` 子类，应与 `PasswordDialog._on_confirm()` 一样在输入边界做校验并早返回。

---

### `src/secnotepad/ui/main_window.py` (component/controller, event-driven + file-I/O + request-response)

**Analog:** `src/secnotepad/ui/main_window.py`

**Imports pattern** (lines 4-20):
```python
from PySide6.QtGui import QAction, QKeySequence, QCloseEvent, QShortcut
from PySide6.QtWidgets import (QMainWindow, QWidget, QSplitter,
                                QTreeView, QListView, QStackedWidget,
                                QStyle, QVBoxLayout, QMessageBox,
                                QFileDialog, QDialog,
                                QTextEdit, QLabel, QAbstractItemView,
                                QPushButton, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt, QModelIndex

from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
from ..model.section_filter_proxy import SectionFilterProxy
from ..model.page_list_model import PageListModel
from .welcome_widget import WelcomeWidget
from ..crypto.file_service import FileService
from ..model.serializer import Serializer
from .password_dialog import PasswordDialog, PasswordMode
```

**菜单 action 初始化 pattern** (lines 112-126):
```python
        # ── 编辑菜单（全部灰显）──
        edit_menu = mb.addMenu("编辑(&E)")
        edit_texts = ["撤销(&U)", "重做(&R)", "剪切(&T)", "复制(&C)", "粘贴(&P)"]
        self._edit_actions = []
        for text in edit_texts:
            act = QAction(text, self)
            act.setEnabled(False)                  # D-16: 灰显
            edit_menu.addAction(act)
            self._edit_actions.append(act)

        # ── 视图菜单 ──
        view_menu = mb.addMenu("视图(&V)")
        self._act_toggle_panels = QAction("切换面板显示", self)
        self._act_toggle_panels.setEnabled(False)   # D-16: 灰显
        view_menu.addAction(self._act_toggle_panels)
```

**右侧编辑区组装 pattern** (lines 231-254):
```python
    def _setup_editor_area(self):
        """创建右侧编辑区: 只读预览 + placeholder 堆叠 (D-62, D-63)。

        使用 QStackedWidget 切换两种状态:
          index 0 = QTextEdit (只读 HTML 预览)
          index 1 = QLabel ("请在页面列表中选择一个页面")
        默认为 placeholder (index 1)。
        """
        self._editor_preview = QTextEdit()
        self._editor_preview.setReadOnly(False)
        self._editor_preview.textChanged.connect(self._on_editor_text_changed)

        self._editor_placeholder_label = QLabel(
            "请在页面列表中选择一个页面"
        )
        self._editor_placeholder_label.setAlignment(Qt.AlignCenter)
        self._editor_placeholder_label.setStyleSheet(
            "color: #888; font-size: 14px;"
        )

        self._editor_stack = QStackedWidget()
        self._editor_stack.addWidget(self._editor_preview)          # index 0
        self._editor_stack.addWidget(self._editor_placeholder_label)  # index 1
        self._editor_stack.setCurrentIndex(1)  # 默认显示 placeholder
```

**重复初始化/拆卸 signal pattern** (lines 267-324, 326-381):
```python
        if self._navigation_initialized:
            self._teardown_navigation()

        # --- 1. SectionFilterProxy: 过滤分区树仅显示 section (D-49) ---
        self._section_filter = SectionFilterProxy(self)
        self._section_filter.setSourceModel(self._tree_model)
        self._tree_view.setModel(self._section_filter)
```
```python
    def _teardown_navigation(self):
        """断开上一次导航初始化的信号，确保重复初始化幂等。"""
        if self._tree_selection is not None:
            try:
                self._tree_selection.currentChanged.disconnect(
                    self._on_tree_current_changed
                )
            except (RuntimeError, TypeError):
                pass
```
```python
        for button, handler in (
            (self._btn_new_section, self._on_new_root_section),
            (self._btn_new_child_section, self._on_new_child_section),
            (self._btn_new_page, self._on_new_page),
        ):
            if button is None:
                continue
            try:
                button.clicked.disconnect(handler)
            except (RuntimeError, TypeError):
                pass
```

**编辑器 HTML 同步与加载防脏 pattern** (lines 441-472):
```python
    def _show_editor_placeholder(self):
        """显示 placeholder 提示文字 (D-63)。"""
        self._editor_stack.setCurrentIndex(1)
        self._editor_preview.blockSignals(True)
        try:
            self._editor_preview.clear()
        finally:
            self._editor_preview.blockSignals(False)

    def _on_editor_text_changed(self):
        """编辑器内容变化时同步回当前页面并标记脏状态。"""
        if self._editor_stack.currentIndex() != 0:
            return
        if self._page_list_model is None:
            return
        current = self._list_view.currentIndex()
        note = self._page_list_model.note_at(current)
        if note is None:
            return
        html = self._editor_preview.toHtml()
        if note.content != html:
            note.content = html
            self.mark_dirty()

    def _show_note_in_editor(self, note: SNoteItem):
        """显示页面内容到右侧编辑器，避免触发无意义脏标记。"""
        self._editor_preview.blockSignals(True)
        try:
            self._editor_preview.setHtml(note.content or "")
        finally:
            self._editor_preview.blockSignals(False)
        self._editor_stack.setCurrentIndex(0)
```

**状态栏反馈 pattern** (lines 596-607, 733-735):
```python
    def _on_new_root_section(self):
        """在根节点下创建顶级分区 (D-55, D-61)。"""
        section = SNoteItem.new_section("新分区")
        self._tree_model.add_item(QModelIndex(), section)
        self.mark_dirty()
        # 展开根节点以显示新分区，然后选中新分区
        proxy = self._section_filter
        new_row = proxy.rowCount(QModelIndex()) - 1
        new_index = proxy.index(new_row, 0, QModelIndex())
        self._tree_view.expand(new_index.parent())
        self._tree_view.setCurrentIndex(new_index)
        self.statusBar().showMessage("已创建分区: 新分区")
```
```python
    def _setup_status_bar(self):
        """设置状态栏 (D-18)"""
        self.statusBar().showMessage("就绪")
```

**文件保存/错误处理 pattern** (lines 944-960):
```python
    def _on_save(self):
        """保存笔记本 — 有路径则直接保存，无路径则触发另存为 (FILE-03)。"""
        if self._root_item is None:
            return

        if self._current_path:
            # 直接保存到现有文件
            json_str = Serializer.to_json(self._root_item)
            try:
                FileService.save(json_str, self._current_path, self._current_password)
            except (OSError, IOError) as e:
                QMessageBox.critical(self, "保存失败", f"无法保存文件:\n{e}")
                return
            self._is_dirty = False
            self._update_window_title()
            self.statusBar().showMessage("笔记本已保存")
            self._add_recent_file(self._current_path)
```

**密码/打开错误处理 pattern** (lines 1073-1108):
```python
    def _open_with_password_retry(self, path: str) -> tuple:
        """打开文件时处理密码输入与重试 (D-35)。

        在密码错误时显示错误提示并允许用户重试。提取为独立方法
        供 _on_open_notebook 和 _on_open_recent 复用。
        """
        dialog = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD, parent=self)
        while dialog.exec() == QDialog.Accepted:
            password = dialog.password()
            dialog.clear_password()

            try:
                json_str = FileService.open(path, password)
            except ValueError:
                dialog.set_error_message("密码错误或文件格式无效，请重试")
                continue
            except OSError as e:
                QMessageBox.critical(self, "打开失败", f"无法读取文件:\n{e}")
                return None, None

            return json_str, password
        return None, None

    def _deserialize_opened_notebook(self, json_str: str) -> SNoteItem | None:
        """反序列化打开的笔记本，坏数据只提示错误，不改动当前会话。"""
        try:
            return Serializer.from_json(json_str)
        except (ValueError, TypeError, KeyError) as e:
            QMessageBox.critical(self, "打开失败", f"笔记本数据格式无效:\n{e}")
            return None
```

**需要复制到 MainWindow 修改的要点：**
- `_setup_editor_area()` 改为“格式工具栏/富文本组件 + placeholder”的容器，但保留 `QStackedWidget` placeholder 模式。
- `_show_note_in_editor()` / `_show_editor_placeholder()` 必须继续 `blockSignals(True)`，并在加载后由新组件清理 undo/redo 栈。
- 编辑菜单动作在 `_setup_menu_bar()` 中创建，在 `_connect_actions()` 或富文本组件绑定方法中连接到当前 editor 标准槽。
- 缩放 action 放在“视图”菜单，执行后用 `statusBar().showMessage()` 短暂提示百分比；不得写入 `SNoteItem`。

---

### `tests/ui/test_rich_text_editor.py` (test, event-driven UI)

**Analogs:** `tests/ui/test_password_dialog.py`, `tests/ui/test_navigation.py`

**UI test imports pattern** (`tests/ui/test_password_dialog.py` lines 2-8):
```python
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QPushButton, QCheckBox, QLabel, QProgressBar

from src.secnotepad.ui.password_dialog import PasswordDialog, PasswordMode
from src.secnotepad.ui.password_generator import PasswordGenerator
```

**组件 fixture pattern** (`tests/ui/test_password_dialog.py` lines 12-20):
```python
@pytest.fixture
def set_dialog(qapp):
    """SET_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.SET_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()
```

**按功能分组测试 class pattern** (`tests/ui/test_password_dialog.py` lines 43-67):
```python
# ── SET_PASSWORD 模式 ──


class TestSetPasswordMode:
    """D-31, D-32, D-34: 新建密码模式测试。"""

    def test_two_password_fields(self, set_dialog):
        """SET_PASSWORD 模式有密码和确认密码两个字段。"""
        line_edits = set_dialog.findChildren(QLineEdit)
        assert len(line_edits) == 2
```

**键盘/编辑器交互 pattern** (`tests/ui/test_navigation.py` lines 726-741):
```python
    def test_editor_updates_note_content_and_marks_dirty(self, window_with_notebook):
        """编辑右侧文本后同步回当前页面并置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()

        current = window_with_notebook._list_view.currentIndex()
        note = window_with_notebook._page_list_model.note_at(current)
        assert note is not None

        window_with_notebook._is_dirty = False
        window_with_notebook._editor_preview.setFocus()
        window_with_notebook._editor_preview.clear()
        QTest.keyClicks(window_with_notebook._editor_preview, "hello")

        assert "hello" in note.content
        assert window_with_notebook._is_dirty is True
```

**文本编辑快捷键边界 pattern** (`tests/ui/test_navigation.py` lines 764-778):
```python
    def test_delete_key_edits_textedit_not_navigation(self, window_with_notebook):
        """编辑器焦点下 Delete 不被导航删除快捷键吞掉。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        editor = window_with_notebook._editor_preview
        editor.setPlainText("abc")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        editor.setFocus()

        QTest.keyClick(editor, Qt.Key_Delete)

        assert editor.toPlainText() == "ac"
        assert window_with_notebook._page_list_model.rowCount() == 1
```

**需要复制到新测试的要点：**
- 每个富文本能力一组测试 class 或清晰测试函数，沿用 `qapp` fixture，不引入系统 Python。
- 测试格式不要逐字比较完整 HTML；断言 `toPlainText()`、关键 HTML 片段、`QTextCursor` 当前格式或 block/list format。
- 对颜色对话框用 monkeypatch/可注入方法避免真实弹窗。
- 对 paste 安全边界测试保存 HTML 不含 `<img`、`file:`、`http://`、`https://`。

---

### `tests/ui/test_main_window.py` (test, event-driven UI + request-response)

**Analog:** `tests/ui/test_main_window.py`

**隔离 QSettings fixture pattern** (lines 14-29):
```python
@pytest.fixture
def isolated_recent_files(qapp):
    """隔离 MainWindow 使用的 QSettings recent_files，避免污染真实状态。"""
    old_org = QCoreApplication.organizationName()
    old_app = QCoreApplication.applicationName()
    QCoreApplication.setOrganizationName("SecNotepadTests")
    QCoreApplication.setApplicationName("SecNotepadTests")
    settings = QSettings()
    settings.clear()
    try:
        yield settings
    finally:
        settings.clear()
        QCoreApplication.setOrganizationName(old_org)
        QCoreApplication.setApplicationName(old_app)
```

**MainWindow fixture pattern** (lines 31-39):
```python
@pytest.fixture
def window(qapp, isolated_recent_files):
    """创建 MainWindow 实例，测试结束后自动清理。"""
    w = MainWindow()
    w.show()
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()
```

**菜单结构测试 pattern** (lines 188-224):
```python
class TestMenuBar:
    """D-16: 菜单栏结构"""

    def test_menu_bar_exists(self, window):
        """窗口有菜单栏"""
        assert window.menuBar() is not None

    def test_menu_actions_exist(self, window):
        """菜单栏有文件/编辑/视图/帮助"""
        mb = window.menuBar()
        actions = mb.actions()
        texts = [a.text() for a in actions]
        assert any("文件" in t for t in texts)
        assert any("编辑" in t for t in texts)
        assert any("视图" in t for t in texts)
        assert any("帮助" in t for t in texts)
```

**状态/dirty 测试 pattern** (lines 295-319):
```python
class TestDirtyFlag:
    """D-45, D-47: 脏标志管理"""

    def test_new_notebook_not_dirty(self, window):
        """新建笔记本后脏标志为 False (D-47)。"""
        window._on_new_notebook()
        assert window._is_dirty is False

    def test_mark_dirty_sets_flag(self, window):
        """mark_dirty() 将脏标志设为 True。"""
        window._on_new_notebook()
        window.mark_dirty()
        assert window._is_dirty is True
```

**monkeypatch 文件保存 pattern** (lines 426-446):
```python
    def test_on_save_adds_recent_file(self, window, monkeypatch, tmp_path):
        """保存到已有路径后，欢迎页最近文件列表立即更新。"""
        from src.secnotepad.crypto import file_service

        window._on_new_notebook()
        save_path = str(tmp_path / "saved.secnote")
        window._current_path = save_path
        window._current_password = "testpw"

        # Mock FileService.save 避免写入真实文件
        monkeypatch.setattr(file_service.FileService, "save", lambda *a, **kw: None)

        window._on_save()
```

**需要复制到 MainWindow 测试的要点：**
- 增加测试：格式工具栏位于右侧编辑区内部，主工具栏不包含格式按钮。
- 增加测试：未选中页面时格式工具栏和编辑菜单禁用，选中页面后启用。
- 增加测试：View 菜单包含放大/缩小/重置快捷键，缩放不改变 `note.content` / 不置脏。
- 对保存/颜色/文件弹窗类交互继续用 monkeypatch，避免真实对话框。

---

### `tests/ui/test_navigation.py` (test, event-driven UI + CRUD)

**Analog:** `tests/ui/test_navigation.py`

**已打开笔记本 fixture pattern** (lines 11-20):
```python
@pytest.fixture
def window_with_notebook(qapp):
    """创建已打开笔记本的 MainWindow，导航系统已初始化。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()
```

**导航初始化断言 pattern** (lines 23-55):
```python
class TestNavigationSetup:
    """Phase 3: 导航系统初始化验证 (D-49~D-53, D-55, D-62, D-63)。"""

    def test_section_filter_proxy_set(self, window_with_notebook):
        """SectionFilterProxy 已创建并设为 TreeView 的模型 (D-49)。"""
        assert window_with_notebook._section_filter is not None

    def test_editor_preview_is_editable(self, window_with_notebook):
        """右侧 QTextEdit 可编辑，用于页面正文编辑。"""
        assert isinstance(window_with_notebook._editor_preview, QTextEdit)
        assert window_with_notebook._editor_preview.isReadOnly() is False

    def test_editor_defaults_to_placeholder(self, window_with_notebook):
        """编辑区默认显示 placeholder (D-63): QStackedWidget index 1。"""
        assert window_with_notebook._editor_stack.currentIndex() == 1
```

**重复初始化防重复绑定 pattern** (lines 118-126, 218-235):
```python
    def test_reinitialize_navigation_does_not_duplicate_button_handlers(self, window_with_notebook):
        """重复初始化导航后，工具栏按钮不会重复触发创建。"""
        window_with_notebook._setup_navigation()
        before = window_with_notebook._section_filter.rowCount()

        window_with_notebook._btn_new_section.click()

        assert window_with_notebook._section_filter.rowCount() == before + 1
```
```python
    def test_second_new_notebook_allows_single_page_creation(self, window_with_notebook):
        """同一窗口会话里再次新建笔记本后，新建页面按钮仍只触发一次。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        before = window_with_notebook._page_list_model.rowCount()

        window_with_notebook._btn_new_page.click()

        assert window_with_notebook._page_list_model.rowCount() == before + 1
        assert window_with_notebook._list_view.currentIndex().isValid()
```

**编辑区内容同步 pattern** (lines 726-741):
```python
    def test_editor_updates_note_content_and_marks_dirty(self, window_with_notebook):
        """编辑右侧文本后同步回当前页面并置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()

        current = window_with_notebook._list_view.currentIndex()
        note = window_with_notebook._page_list_model.note_at(current)
        assert note is not None

        window_with_notebook._is_dirty = False
        window_with_notebook._editor_preview.setFocus()
        window_with_notebook._editor_preview.clear()
        QTest.keyClicks(window_with_notebook._editor_preview, "hello")

        assert "hello" in note.content
        assert window_with_notebook._is_dirty is True
```

**placeholder 不清空内容 pattern** (lines 749-762):
```python
    def test_show_editor_placeholder_does_not_clear_note_content(self, window_with_notebook):
        """切换到 placeholder 不会把当前页面正文写空。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        note = window_with_notebook._page_list_model.note_at(
            window_with_notebook._list_view.currentIndex()
        )
        note.content = "<p>keep me</p>"
        window_with_notebook._is_dirty = False

        window_with_notebook._show_editor_placeholder()

        assert note.content == "<p>keep me</p>"
        assert window_with_notebook._is_dirty is False
```

**需要复制到导航回归的要点：**
- Phase 4 改 `_editor_preview` 为富文本组件后，要保留等价属性或提供兼容访问；否则更新测试命名但保持行为断言。
- 增加回归：重复 `_setup_navigation()` / 第二次新建笔记本后，格式工具栏 action 不重复触发。
- 增加回归：切换分区/页面显示 placeholder 或新页面时，不把上一页 HTML 清空、不误置脏。

---

### `tests/model/test_serializer.py` (test, transform)

**Analog:** `tests/model/test_serializer.py`

**测试 fixture pattern** (lines 13-33):
```python
@pytest.fixture
def sample_tree():
    """创建 3 层示例树用于序列化测试.

    根分区 (section)
    └── 工作 (section)
        ├── 周报 (note, content="<p>内容1</p>")
        └── 项目A (section)
            └── 需求文档 (note, content="<p>内容2</p>")
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    report = SNoteItem.new_note("周报", "<p>内容1</p>")
    project = SNoteItem.new_section("项目A")
    doc = SNoteItem.new_note("需求文档", "<p>内容2</p>")
```

**HTML content 序列化 pattern** (lines 81-88):
```python
    def test_note_content_serialized(self, sample_tree):
        """Note 的 content 被序列化."""
        result = json.loads(Serializer.to_json(sample_tree))
        work = result["data"]["children"][0]
        report = work["children"][0]
        assert report["title"] == "周报"
        assert report["content"] == "<p>内容1</p>"
```

**Round-trip pattern** (lines 132-144):
```python
    def test_nested_tree_roundtrip(self, sample_tree):
        """Round-trip: tree → JSON → tree' 结构一致."""
        json_str = Serializer.to_json(sample_tree)
        restored = Serializer.from_json(json_str)

        assert restored.title == sample_tree.title
        assert restored.item_type == sample_tree.item_type
        assert len(restored.children) == len(sample_tree.children)
        assert restored.children[0].title == "工作"
        assert restored.children[0].children[0].title == "周报"
        assert restored.children[0].children[0].content == "<p>内容1</p>"
        assert restored.children[0].children[1].title == "项目A"
        assert restored.children[0].children[1].children[0].title == "需求文档"
```

**缺省 content pattern** (lines 190-205):
```python
    def test_from_json_missing_content(self):
        """缺少 content 时默认为空字符串."""
        json_str = json.dumps({
            "version": 1,
            "data": {
                "id": "d" * 32,
                "title": "无内容",
                "item_type": "note",
                "children": [],
                "tags": [],
                "created_at": "",
                "updated_at": "",
            },
        })
        item = Serializer.from_json(json_str)
        assert item.content == ""
```

**需要复制到 serializer 测试的要点：**
- 补充富文本 HTML（标题、颜色、列表、中文、待办符号“☐ ”）round-trip，断言字符串原样经过 JSON 保存/读取。
- 不需要修改 `SNoteItem` 字段；缩放不应出现在 JSON data 中。

## Shared Patterns

### Qt signal-driven 状态同步
**Source:** `src/secnotepad/ui/main_window.py` lines 289-301; `src/secnotepad/ui/password_dialog.py` lines 147-154
**Apply to:** `rich_text_editor.py`, `main_window.py`, UI tests
```python
        self._page_selection = self._list_view.selectionModel()
        self._page_selection.currentChanged.connect(
            self._on_page_current_changed
        )
        self._tree_model.dataChanged.connect(self._on_structure_data_changed)
        self._page_list_model.dataChanged.connect(self._on_structure_data_changed)
```
```python
        self._pwd_input.textChanged.connect(self._on_password_changed)
        self._confirm_input.textChanged.connect(self._on_password_changed)
        self.rejected.connect(self.clear_password)
```

### 加载内容时阻断信号，避免误置脏
**Source:** `src/secnotepad/ui/main_window.py` lines 441-472
**Apply to:** `rich_text_editor.py`, `main_window.py`, `tests/ui/test_navigation.py`
```python
        self._editor_preview.blockSignals(True)
        try:
            self._editor_preview.setHtml(note.content or "")
        finally:
            self._editor_preview.blockSignals(False)
        self._editor_stack.setCurrentIndex(0)
```

### 脏标志只由真实数据变化触发
**Source:** `src/secnotepad/ui/main_window.py` lines 450-463, 808-818
**Apply to:** `main_window.py`, `rich_text_editor.py`, UI tests
```python
        html = self._editor_preview.toHtml()
        if note.content != html:
            note.content = html
            self.mark_dirty()
```
```python
    def mark_dirty(self):
        """标记笔记本已修改。Phase 3（结构编辑）和 Phase 4（文本编辑）调用此方法。"""
        if not self._is_dirty and self._root_item is not None:
            self._is_dirty = True
            self._update_window_title()
```

### 重复初始化必须 disconnect 或只创建一次
**Source:** `src/secnotepad/ui/main_window.py` lines 267-268, 326-381
**Apply to:** `main_window.py`, `rich_text_editor.py`, `tests/ui/test_navigation.py`
```python
        if self._navigation_initialized:
            self._teardown_navigation()
```
```python
            try:
                button.clicked.disconnect(handler)
            except (RuntimeError, TypeError):
                pass
```

### UI 测试资源清理
**Source:** `tests/ui/test_main_window.py` lines 31-39; `tests/ui/test_password_dialog.py` lines 14-20
**Apply to:** all UI test files
```python
@pytest.fixture
def window(qapp, isolated_recent_files):
    """创建 MainWindow 实例，测试结束后自动清理。"""
    w = MainWindow()
    w.show()
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()
```
```python
@pytest.fixture
def set_dialog(qapp):
    """SET_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.SET_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()
```

### 测试中避免真实外部副作用
**Source:** `tests/ui/test_main_window.py` lines 426-446
**Apply to:** color dialog tests, save tests, paste/file tests
```python
        # Mock FileService.save 避免写入真实文件
        monkeypatch.setattr(file_service.FileService, "save", lambda *a, **kw: None)

        window._on_save()
```

### JSON/HTML 持久化路径保持纯 transform
**Source:** `src/secnotepad/model/serializer.py` lines 20-34, 64-76; `src/secnotepad/model/snote_item.py` lines 13-32
**Apply to:** `main_window.py`, `tests/model/test_serializer.py`
```python
    @staticmethod
    def to_json(root: SNoteItem) -> str:
        """SNoteItem 树 → JSON 字符串。"""
        data = asdict(root)
        document = {
            "version": Serializer.FORMAT_VERSION,
            "data": data,
        }
        return json.dumps(document, ensure_ascii=False, indent=2)
```
```python
    content: str = ""
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/secnotepad/ui/rich_text_editor.py` | component | rich-text event-driven transform | 代码库没有现有富文本工具栏或 `QTextCursor`/`QTextCharFormat`/`QTextBlockFormat` 示例；只能复制 Qt 组件组织、Action/signal、状态同步和测试模式，具体富文本 API 需按 `04-RESEARCH.md` 的 Qt 官方模式实现。 |

## Metadata

**Analog search scope:** `src/secnotepad/ui`, `src/secnotepad/model`, `src/secnotepad/crypto`, `tests/ui`, `tests/model`, `tests/conftest.py`
**Files scanned:** 36
**Strong analogs read:** 9 (`main_window.py`, `password_dialog.py`, `page_list_model.py`, `serializer.py`, `snote_item.py`, `file_service.py`, `tests/conftest.py`, `tests/ui/test_main_window.py`, `tests/ui/test_navigation.py`, `tests/ui/test_password_dialog.py`, `tests/model/test_serializer.py`, `tests/model/test_page_list_model.py`)
**Pattern extraction date:** 2026-05-09
