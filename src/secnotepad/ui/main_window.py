"""SecNotepad 主窗口 (D-12 至 D-20, Phase 2 文件操作 + 加密集成)"""

import os

from PySide6.QtGui import QAction, QKeySequence, QCloseEvent
from PySide6.QtWidgets import (QMainWindow, QWidget, QSplitter,
                                QTreeView, QListView, QStackedWidget,
                                QStyle, QVBoxLayout, QMessageBox,
                                QFileDialog, QDialog)
from PySide6.QtCore import Qt

from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
from .welcome_widget import WelcomeWidget
from ..crypto.file_service import FileService
from ..model.serializer import Serializer
from .password_dialog import PasswordDialog, PasswordMode


class MainWindow(QMainWindow):
    """SecNotepad 应用主窗口

    包含欢迎页/三栏布局切换、菜单栏、工具栏、状态栏。
    """

    def __init__(self):
        super().__init__()
        # 当前笔记本数据 (Phase 2 后持久化)
        self._root_item: SNoteItem = None
        self._tree_model: TreeModel = None

        # ── 文件操作状态 (Phase 2) ──
        self._is_dirty: bool = False
        self._current_path: str = ""        # 当前文件路径，空=未保存
        self._current_password: str = ""    # 当前会话密码

        self._setup_window()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_central_area()
        self._setup_status_bar()
        self._connect_actions()

        # 加载最近文件列表到欢迎页 (D-40)
        recent = self._load_recent_files()
        self._welcome.set_recent_files(recent)

    # ── 窗口设置 ──

    def _setup_window(self):
        """设置窗口属性 (D-19)"""
        self.setWindowTitle("SecNotepad")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

    # ── 菜单栏 ──

    def _setup_menu_bar(self):
        """设置菜单栏 (D-16)"""
        mb = self.menuBar()

        # ── 文件菜单 ──
        file_menu = mb.addMenu("文件(&F)")

        self._act_new = QAction("新建(&N)", self)
        self._act_new.setShortcut(QKeySequence("Ctrl+N"))
        file_menu.addAction(self._act_new)

        self._act_open = QAction("打开(&O)...", self)
        self._act_open.setShortcut(QKeySequence("Ctrl+O"))
        file_menu.addAction(self._act_open)

        self._act_save = QAction("保存(&S)", self)
        self._act_save.setShortcut(QKeySequence("Ctrl+S"))
        self._act_save.setEnabled(False)           # D-16: 灰显
        file_menu.addAction(self._act_save)

        self._act_save_as = QAction("另存为(&A)...", self)
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_save_as.setEnabled(False)        # D-16: 灰显
        file_menu.addAction(self._act_save_as)

        file_menu.addSeparator()

        self._act_exit = QAction("退出(&Q)", self)
        self._act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self._act_exit.triggered.connect(self.close)
        file_menu.addAction(self._act_exit)

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

        # ── 帮助菜单 ──
        help_menu = mb.addMenu("帮助(&H)")
        self._act_about = QAction("关于(&A)...", self)
        self._act_about.setEnabled(False)           # D-16: 灰显
        help_menu.addAction(self._act_about)

    # ── 工具栏 ──

    def _setup_tool_bar(self):
        """设置工具栏 (D-17)"""
        tb = self.addToolBar("工具栏")
        tb.setMovable(False)
        style = self.style()

        new_icon = style.standardIcon(QStyle.SP_FileIcon)
        open_icon = style.standardIcon(QStyle.SP_DialogOpenButton)
        save_icon = style.standardIcon(QStyle.SP_DialogSaveButton)
        saveas_icon = style.standardIcon(QStyle.SP_DialogSaveButton)

        self._tb_new = tb.addAction(new_icon, "新建")
        self._tb_open = tb.addAction(open_icon, "打开")
        self._tb_save = tb.addAction(save_icon, "保存")
        self._tb_save.setEnabled(False)             # D-17: 灰显
        self._tb_saveas = tb.addAction(saveas_icon, "另存为")
        self._tb_saveas.setEnabled(False)            # D-17: 灰显

    # ── 中央区域 ──

    def _setup_central_area(self):
        """设置中央区域: QStackedWidget (D-14)

        index 0 = 欢迎页
        index 1 = 三栏布局 (QSplitter)
        """
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # 欢迎页 (D-15)
        self._welcome = WelcomeWidget()
        self._welcome.new_notebook_clicked.connect(self._on_new_notebook)
        self._welcome.open_notebook_clicked.connect(self._on_open_notebook)
        self._welcome.recent_file_clicked.connect(self._on_open_recent)

        # 三栏布局 (D-12, D-13)
        splitter = QSplitter(Qt.Horizontal)

        self._tree_view = QTreeView()
        self._tree_view.setMinimumWidth(100)
        splitter.addWidget(self._tree_view)          # 左侧

        self._list_view = QListView()
        self._list_view.setMinimumWidth(100)
        splitter.addWidget(self._list_view)          # 中间

        self._editor_placeholder = QWidget()
        splitter.addWidget(self._editor_placeholder)  # 右侧

        splitter.setSizes([200, 250, 750])           # D-12
        splitter.setCollapsible(0, True)             # D-13: 左可折叠
        splitter.setCollapsible(1, False)            # D-13: 中始终可见
        splitter.setCollapsible(2, True)             # D-13: 右可折叠

        self._stack.addWidget(self._welcome)          # index 0
        self._stack.addWidget(splitter)               # index 1
        self._stack.setCurrentIndex(0)                # 默认欢迎页

    # ── 状态栏 ──

    def _setup_status_bar(self):
        """设置状态栏 (D-18)"""
        self.statusBar().showMessage("就绪")

    # ── 窗口事件 ──

    def closeEvent(self, event: QCloseEvent):
        """关闭窗口时检查未保存更改 (D-46)。

        同时处理 X 按钮关闭和 File→退出菜单 (D-46)。
        空的未保存新建笔记本不提示 (D-47)。
        """
        if self._is_dirty and self._root_item is not None:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("未保存的更改")
            msg_box.setText("笔记本有未保存的更改。是否在关闭前保存？")
            msg_box.setIcon(QMessageBox.Question)
            btn_save = msg_box.addButton("保存(&S)", QMessageBox.AcceptRole)
            btn_discard = msg_box.addButton("不保存(&D)", QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton("取消(&C)", QMessageBox.RejectRole)
            msg_box.setDefaultButton(btn_save)
            msg_box.exec()

            clicked = msg_box.clickedButton()
            if clicked == btn_save:
                event.ignore()
                self._on_save()
                # 保存成功后关闭
                if not self._is_dirty:
                    event.accept()
                # 如果保存取消（用户取消了另存为对话框），不关闭
            elif clicked == btn_discard:
                self._clear_session()
                event.accept()
            else:  # cancel
                event.ignore()
        else:
            self._clear_session()
            event.accept()

    def _clear_session(self):
        """清理当前会话的所有敏感数据。"""
        self._current_password = ""
        self._is_dirty = False
        self._current_path = ""
        self._root_item = None
        self._tree_model = None

    def _confirm_discard_changes(self) -> bool:
        """检查脏状态，如有未保存更改则弹出确认对话框。

        Returns:
            True 表示可以继续（用户选择保存或丢弃），False 表示取消。
        """
        if self._root_item is not None and self._is_dirty:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("未保存的更改")
            msg_box.setText("当前笔记本有未保存的更改。是否在继续前保存？")
            msg_box.setIcon(QMessageBox.Question)
            btn_save = msg_box.addButton("保存", QMessageBox.AcceptRole)
            btn_discard = msg_box.addButton("不保存", QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton("取消", QMessageBox.RejectRole)
            msg_box.setDefaultButton(btn_save)
            msg_box.exec()
            clicked = msg_box.clickedButton()
            if clicked == btn_save:
                self._on_save()
                if self._is_dirty:
                    return False
            elif clicked == btn_cancel:
                return False
        return True

    # ── 脏标志管理 (D-45) ──

    def mark_dirty(self):
        """标记笔记本已修改。Phase 3（结构编辑）和 Phase 4（文本编辑）调用此方法。"""
        if not self._is_dirty and self._root_item is not None:
            self._is_dirty = True
            self._update_window_title()

    def mark_clean(self):
        """标记笔记本为已保存状态。"""
        if self._is_dirty:
            self._is_dirty = False
            self._update_window_title()

    # ── 窗口标题管理 ──

    def _update_window_title(self):
        """根据当前文件路径和脏状态更新窗口标题 (UI-06)。"""
        if self._current_path:
            filename = os.path.basename(self._current_path)
            base = f"{filename} - SecNotepad"
        else:
            base = "SecNotepad"
        if self._is_dirty:
            self.setWindowTitle(f"{base} *")
        else:
            self.setWindowTitle(base)

    # ── 动作连接 ──

    def _connect_actions(self):
        """连接菜单/工具栏动作到处理函数"""
        # 新建：菜单、工具栏、欢迎页按钮均已连接
        self._act_new.triggered.connect(self._on_new_notebook)
        self._tb_new.triggered.connect(self._on_new_notebook)

        self._act_open.triggered.connect(self._on_open_notebook)
        self._tb_open.triggered.connect(self._on_open_notebook)

        # Phase 2: 连接保存/另存为
        self._act_save.triggered.connect(self._on_save)
        self._tb_save.triggered.connect(self._on_save)
        self._act_save_as.triggered.connect(self._on_save_as)
        self._tb_saveas.triggered.connect(self._on_save_as)

    def _on_new_notebook(self):
        """新建空白笔记本 (D-14)"""
        if self._root_item is not None and self._is_dirty:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("未保存的更改")
            msg_box.setText("当前笔记本有未保存的更改。是否在创建新笔记本前保存？")
            msg_box.setIcon(QMessageBox.Question)
            btn_save = msg_box.addButton("保存", QMessageBox.AcceptRole)
            btn_discard = msg_box.addButton("不保存", QMessageBox.DestructiveRole)
            btn_cancel = msg_box.addButton("取消", QMessageBox.RejectRole)
            msg_box.setDefaultButton(btn_save)
            msg_box.exec()
            clicked = msg_box.clickedButton()
            if clicked == btn_save:
                self._on_save()
                if self._is_dirty:
                    return
            elif clicked == btn_cancel:
                return
        if self._tree_model is not None:
            self._tree_model.deleteLater()
        self._root_item = SNoteItem.new_section("根分区")
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)
        self._stack.setCurrentIndex(1)               # 切换到三栏布局

        # Phase 2: 启用保存/另存为 (D-47: 新建笔记本不脏)
        self._is_dirty = False
        self._current_path = ""
        self._current_password = ""
        self._act_save.setEnabled(True)
        self._tb_save.setEnabled(True)
        self._act_save_as.setEnabled(True)
        self._tb_saveas.setEnabled(True)
        self._update_window_title()
        self.statusBar().showMessage("新建笔记本 - 未保存")

        # 新建后更新欢迎页的最近文件（不影响当前显示，但切换回欢迎页时正确）
        recent = self._load_recent_files()
        self._welcome.set_recent_files(recent)

    def _on_open_notebook(self):
        """打开 .secnote 文件 → 输入密码 → 解密 → 加载到编辑器 (FILE-02)。

        密码错误时在对话框内显示错误提示并允许重试 (D-35)。
        """
        if not self._confirm_discard_changes():
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "打开加密笔记本", "",
            "SecNotepad 加密笔记本 (*.secnote)",
        )
        if not path:
            return

        # 复用密码重试逻辑
        json_str, password_correct = self._open_with_password_retry(path)
        if json_str is None:
            return

        # 更新数据模型
        root = Serializer.from_json(json_str)
        if self._tree_model is not None:
            self._tree_model.deleteLater()
        self._root_item = root
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)

        # 更新状态
        self._current_path = path
        self._current_password = password_correct
        self._is_dirty = False
        self._act_save.setEnabled(True)
        self._tb_save.setEnabled(True)
        self._act_save_as.setEnabled(True)
        self._tb_saveas.setEnabled(True)

        self._stack.setCurrentIndex(1)
        self._update_window_title()
        self.statusBar().showMessage(f"已打开《{os.path.basename(path)}》")

        # 添加到最近文件 (D-44)
        self._add_recent_file(path)

    # ── 保存/另存为 ──

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
        else:
            # 无路径 → 触发另存为
            self._on_save_as()

    def _on_save_as(self):
        """另存为 — 选择路径 → 可选换密码 → 加密写入 (FILE-04)。"""
        if self._root_item is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "保存加密笔记本", "",
            "SecNotepad 加密笔记本 (*.secnote)",
        )
        if not path:
            return

        # 密码对话框（CHANGE_PASSWORD 模式：默认不换密码）
        dialog = PasswordDialog(mode=PasswordMode.CHANGE_PASSWORD, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        new_password = dialog.password()
        dialog.clear_password()

        # 如果对话框返回空密码，使用当前密码
        if not new_password:
            new_password = self._current_password or ""

        # 如果当前无密码且用户没输入新密码，要求设置密码
        if not new_password:
            set_dialog = PasswordDialog(mode=PasswordMode.SET_PASSWORD, parent=self)
            if set_dialog.exec() != QDialog.Accepted:
                return
            new_password = set_dialog.password()
            set_dialog.clear_password()

        json_str = Serializer.to_json(self._root_item)
        try:
            FileService.save_as(json_str, path, new_password)
        except (OSError, IOError) as e:
            QMessageBox.critical(self, "保存失败", f"无法保存文件:\n{e}")
            return

        # 更新状态
        self._current_path = path
        self._current_password = new_password
        self._is_dirty = False
        self._update_window_title()
        self.statusBar().showMessage("笔记本已另存为")

        # 添加到最近文件 (D-44)
        self._add_recent_file(path)

    # ── 最近文件管理 (D-40~D-44) ──

    MAX_RECENT_FILES = 5
    SETTINGS_KEY = "recent_files"

    def _load_recent_files(self) -> list[str]:
        """从 QSettings 加载最近文件列表，过滤不存在的文件 (D-42)。"""
        from PySide6.QtCore import QSettings
        settings = QSettings()
        paths = settings.value(self.SETTINGS_KEY, [])
        if paths is None:
            return []
        # QSettings 可能将单元素列表退化为字符串 (WR-08)
        if isinstance(paths, str):
            paths = [paths]
        # 过滤不存在的文件 (D-42)
        valid = [p for p in paths if isinstance(p, str) and os.path.isfile(p)]
        # 如有移除，回写更新
        if len(valid) < len(paths):
            settings.setValue(self.SETTINGS_KEY, valid)
        return valid

    def _add_recent_file(self, path: str):
        """添加文件到最近列表，去重并限制数量 (D-40, D-44)。"""
        from PySide6.QtCore import QSettings
        settings = QSettings()
        paths = settings.value(self.SETTINGS_KEY, [])
        if paths is None:
            paths = []
        if isinstance(paths, str):
            paths = [paths]
        # 去重: 移到顶部 (D-44)
        path = os.path.abspath(path)
        if path in paths:
            paths.remove(path)
        paths.insert(0, path)
        # 限制数量 (D-40)
        paths = paths[:self.MAX_RECENT_FILES]
        settings.setValue(self.SETTINGS_KEY, paths)

        # 更新欢迎页显示
        self._welcome.set_recent_files(paths)

    def _remove_recent_file(self, path: str):
        """从最近列表中移除指定路径。"""
        from PySide6.QtCore import QSettings
        settings = QSettings()
        paths = settings.value(self.SETTINGS_KEY, [])
        if paths is None:
            return
        if isinstance(paths, str):
            paths = [paths]
        path = os.path.abspath(path)
        if path in paths:
            paths.remove(path)
        settings.setValue(self.SETTINGS_KEY, paths)
        self._welcome.set_recent_files(paths)

    # ── 最近文件点击 ──

    def _open_with_password_retry(self, path: str) -> tuple:
        """打开文件时处理密码输入与重试 (D-35)。

        在密码错误时显示错误提示并允许用户重试。提取为独立方法
        供 _on_open_notebook 和 _on_open_recent 复用。

        Args:
            path: .secnote 文件路径

        Returns:
            (json_str, password) 解密成功时返回；用户取消时返回 (None, None)
        """
        dialog = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD, parent=self)
        while dialog.exec() == QDialog.Accepted:
            password = dialog.password()
            dialog.clear_password()

            try:
                json_str = FileService.open(path, password)
            except ValueError:
                dialog.set_error_message("密码错误，请重试")
                continue

            return json_str, password
        return None, None

    def _on_open_recent(self, path: str):
        """单击最近文件 → 触发打开流程 (D-43)。

        密码错误时在对话框内显示错误提示并允许重试 (D-35)。
        """
        if not os.path.isfile(path):
            # 文件已不存在，从最近列表中移除
            self._remove_recent_file(path)
            return

        if not self._confirm_discard_changes():
            return

        # 复用密码重试逻辑
        json_str, password_correct = self._open_with_password_retry(path)
        if json_str is None:
            return

        root = Serializer.from_json(json_str)
        if self._tree_model is not None:
            self._tree_model.deleteLater()
        self._root_item = root
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)

        self._current_path = path
        self._current_password = password_correct
        self._is_dirty = False
        self._act_save.setEnabled(True)
        self._tb_save.setEnabled(True)
        self._act_save_as.setEnabled(True)
        self._tb_saveas.setEnabled(True)

        self._stack.setCurrentIndex(1)
        self._update_window_title()
        self.statusBar().showMessage(f"已打开《{os.path.basename(path)}》")
        # 更新最近文件顺序
        self._add_recent_file(path)
