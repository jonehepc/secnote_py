"""SecNotepad 主窗口 (D-12 至 D-20, Phase 2 文件操作 + 加密集成)"""

import os

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
from .rich_text_editor import RichTextEditorWidget


class MainWindow(QMainWindow):
    """SecNotepad 应用主窗口

    包含欢迎页/三栏布局切换、菜单栏、工具栏、状态栏。
    """

    def __init__(self):
        super().__init__()
        # 当前笔记本数据 (Phase 2 后持久化)
        self._root_item: SNoteItem = None
        self._tree_model: TreeModel = None

        # ── 导航系统状态 (Phase 3) ──
        self._section_filter: SectionFilterProxy = None
        self._page_list_model: PageListModel = None
        self._rich_text_editor: RichTextEditorWidget = None
        self._editor_preview: QTextEdit = None
        self._format_toolbar = None
        self._editor_container: QWidget = None
        self._editor_stack: QStackedWidget = None
        self._editor_placeholder_label: QLabel = None
        self._tree_button_bar: QFrame = None
        self._btn_new_section: QPushButton = None
        self._btn_new_child_section: QPushButton = None
        self._page_button_bar: QFrame = None
        self._btn_new_page: QPushButton = None
        self._navigation_initialized: bool = False
        self._tree_selection = None
        self._page_selection = None
        self._act_delete: QAction | None = None
        self._act_rename: QAction | None = None
        self._shortcut_ctrl_n: QShortcut | None = None
        self._data_changed_models = []

        # ── 文件操作状态 (Phase 2) ──
        self._is_dirty: bool = False
        self._current_path: str = ""        # 当前文件路径，空=未保存
        self._current_password: str = ""    # 当前会话密码

        self._setup_window()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_central_area()
        self._setup_status_bar()
        self._setup_global_shortcuts()
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
        # 左侧容器: 按钮栏 + 分区树 (D-55)
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        self._tree_button_bar = QFrame()
        self._tree_button_bar.setFrameShape(QFrame.NoFrame)
        tree_btn_layout = QHBoxLayout(self._tree_button_bar)
        tree_btn_layout.setContentsMargins(2, 2, 2, 2)
        tree_btn_layout.setSpacing(2)
        self._btn_new_section = QPushButton("新建分区")
        self._btn_new_child_section = QPushButton("新建子分区")
        self._btn_new_section.setEnabled(False)
        self._btn_new_child_section.setEnabled(False)
        tree_btn_layout.addWidget(self._btn_new_section)
        tree_btn_layout.addWidget(self._btn_new_child_section)
        tree_btn_layout.addStretch()
        left_layout.addWidget(self._tree_button_bar)
        left_layout.addWidget(self._tree_view)
        splitter.addWidget(left_container)          # 左侧

        self._list_view = QListView()
        self._list_view.setMinimumWidth(100)
        # 中间容器: 按钮栏 + 页面列表 (D-55)
        mid_container = QWidget()
        mid_layout = QVBoxLayout(mid_container)
        mid_layout.setContentsMargins(0, 0, 0, 0)
        mid_layout.setSpacing(2)
        self._page_button_bar = QFrame()
        self._page_button_bar.setFrameShape(QFrame.NoFrame)
        page_btn_layout = QHBoxLayout(self._page_button_bar)
        page_btn_layout.setContentsMargins(2, 2, 2, 2)
        page_btn_layout.setSpacing(2)
        self._btn_new_page = QPushButton("新建页面")
        self._btn_new_page.setEnabled(False)
        page_btn_layout.addWidget(self._btn_new_page)
        page_btn_layout.addStretch()
        mid_layout.addWidget(self._page_button_bar)
        mid_layout.addWidget(self._list_view)
        splitter.addWidget(mid_container)           # 中间

        self._setup_editor_area()
        splitter.addWidget(self._editor_container)     # 右侧

        splitter.setSizes([200, 250, 750])           # D-12
        splitter.setCollapsible(0, True)             # D-13: 左可折叠
        splitter.setCollapsible(1, False)            # D-13: 中始终可见
        splitter.setCollapsible(2, True)             # D-13: 右可折叠

        self._stack.addWidget(self._welcome)          # index 0
        self._stack.addWidget(splitter)               # index 1
        self._stack.setCurrentIndex(0)                # 默认欢迎页

    # ── 编辑区 (Phase 3) ──

    def _setup_editor_area(self):
        """创建右侧富文本编辑区 + placeholder 堆叠 (D-62, D-63, D-65)。

        右侧容器固定放置格式工具栏，下方使用 QStackedWidget 切换两种状态:
          index 0 = QTextEdit
          index 1 = QLabel ("请在页面列表中选择一个页面")
        默认为 placeholder (index 1)。
        """
        self._editor_container = QWidget()
        editor_layout = QVBoxLayout(self._editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(8)

        self._rich_text_editor = RichTextEditorWidget(self._editor_container)
        self._rich_text_editor.set_status_callback(
            lambda message: self.statusBar().showMessage(message)
        )
        self._rich_text_editor.content_changed.connect(
            self._on_editor_content_changed
        )
        self._editor_preview = self._rich_text_editor.editor()
        self._format_toolbar = self._rich_text_editor.format_toolbar()
        self._format_toolbar.setParent(self._editor_container)
        editor_layout.addWidget(self._format_toolbar)
        self._rich_text_editor.layout().removeWidget(self._format_toolbar)
        self._rich_text_editor.set_editor_enabled(False)

        self._editor_placeholder_label = QLabel(
            "请在页面列表中选择一个页面"
        )
        self._editor_placeholder_label.setAlignment(Qt.AlignCenter)
        self._editor_placeholder_label.setStyleSheet(
            "color: #888; font-size: 14px;"
        )

        self._editor_stack = QStackedWidget(self._editor_container)
        self._editor_stack.addWidget(self._rich_text_editor.editor())  # index 0
        self._editor_stack.addWidget(self._editor_placeholder_label)  # index 1
        self._editor_stack.setCurrentIndex(1)  # 默认显示 placeholder
        editor_layout.addWidget(self._editor_stack)

    # ── 导航系统 (Phase 3) ──

    def _setup_navigation(self):
        """Phase 3: 设置导航系统 — 代理模型、页面列表、信号连接、初始状态。

        必须在 _tree_model 存在且 _tree_view / _list_view 可见之后调用。
        即在 _on_new_notebook / _on_open_notebook / _on_open_recent 中
        设置 TreeModel 后调用。

        实现 D-49~D-54, D-59, D-62, D-63。
        """
        if self._navigation_initialized:
            self._teardown_navigation()

        # --- 1. SectionFilterProxy: 过滤分区树仅显示 section (D-49) ---
        self._section_filter = SectionFilterProxy(self)
        self._section_filter.setSourceModel(self._tree_model)
        self._tree_view.setModel(self._section_filter)

        # D-59: 原地编辑 — 必须在 setModel 之后设置 (Pitfall 2)
        self._tree_view.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )

        # --- 2. PageListModel: 平铺显示页面的列表 (D-50, D-54) ---
        self._page_list_model = PageListModel(self)
        self._list_view.setModel(self._page_list_model)

        # D-59: 原地编辑 — 必须在 setModel 之后设置 (Pitfall 2)
        self._list_view.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )

        # --- 3. 选择信号连接 (D-51, D-62, Pitfall 3) ---
        self._tree_selection = self._tree_view.selectionModel()
        self._tree_selection.currentChanged.connect(
            self._on_tree_current_changed
        )

        self._page_selection = self._list_view.selectionModel()
        self._page_selection.currentChanged.connect(
            self._on_page_current_changed
        )
        self._tree_model.dataChanged.connect(self._on_structure_data_changed)
        self._page_list_model.dataChanged.connect(self._on_structure_data_changed)
        self._data_changed_models = [self._tree_model, self._page_list_model]

        # --- 右键菜单 (D-56) ---
        self._setup_tree_context_menu()
        self._setup_page_context_menu()

        # --- 键盘快捷键 (D-57) ---
        self._setup_navigation_shortcuts()

        # --- 启用工具栏按钮 (D-55) ---
        self._btn_new_section.setEnabled(True)
        self._btn_new_child_section.setEnabled(True)
        self._btn_new_page.setEnabled(True)

        # 工具栏按钮信号连接 — 在导航初始化后连接 (D-55)
        self._btn_new_section.clicked.connect(self._on_new_root_section)
        self._btn_new_child_section.clicked.connect(self._on_new_child_section)
        self._btn_new_page.clicked.connect(self._on_new_page)

        self._navigation_initialized = True
        self._rebind_page_model_to_current_section()

        # --- 4. 初始导航状态 (D-52, D-53) ---
        self._initialize_navigation_state()

    def _teardown_navigation(self):
        """断开上一次导航初始化的信号，确保重复初始化幂等。"""
        if self._tree_selection is not None:
            try:
                self._tree_selection.currentChanged.disconnect(
                    self._on_tree_current_changed
                )
            except (RuntimeError, TypeError):
                pass
        if self._page_selection is not None:
            try:
                self._page_selection.currentChanged.disconnect(
                    self._on_page_current_changed
                )
            except (RuntimeError, TypeError):
                pass
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
        for signal, handler in (
            (self._tree_view.customContextMenuRequested,
             self._on_tree_context_menu),
            (self._list_view.customContextMenuRequested,
             self._on_page_context_menu),
            (self._list_view.viewport().customContextMenuRequested,
             self._on_page_context_menu),
        ):
            try:
                signal.disconnect(handler)
            except (RuntimeError, TypeError, AttributeError):
                pass
        for model in self._data_changed_models:
            try:
                model.dataChanged.disconnect(self._on_structure_data_changed)
            except (RuntimeError, TypeError, AttributeError):
                pass
        self._data_changed_models = []
        for action in (self._act_delete, self._act_rename):
            if action is None:
                continue
            self._tree_view.removeAction(action)
            self._list_view.removeAction(action)
            action.deleteLater()
        self._act_delete = None
        self._act_rename = None
        self._tree_selection = None
        self._page_selection = None
        self._navigation_initialized = False

    def _on_structure_data_changed(self, *args):
        self.mark_dirty()

    def _select_new_child_section(self, parent_proxy_index: QModelIndex):
        """在当前选中分区下创建子分区后选中新子节点。"""
        if not parent_proxy_index.isValid():
            return
        self._tree_view.expand(parent_proxy_index)
        child_row = self._section_filter.rowCount(parent_proxy_index) - 1
        if child_row < 0:
            return
        child_index = self._section_filter.index(child_row, 0, parent_proxy_index)
        if child_index.isValid():
            self._tree_view.setCurrentIndex(child_index)
            self._tree_view.scrollTo(child_index)

    def _rebind_page_model_to_current_section(self):
        """重复初始化后基于当前树选中项恢复页面列表绑定。"""
        current = self._tree_view.currentIndex()
        if current.isValid():
            self._on_tree_current_changed(current, QModelIndex())
            if self._page_list_model.rowCount() > 0:
                first_page = self._page_list_model.index(0, 0)
                self._list_view.setCurrentIndex(first_page)
                self._on_page_current_changed(first_page, QModelIndex())
        else:
            self._page_list_model.set_section(None)
            self._show_editor_placeholder()

    def _on_tree_current_changed(self, current: QModelIndex,
                                 previous: QModelIndex):
        """分区选择变化 → 更新页面列表 (D-51)。

        从 proxy 索引映射回源模型索引，获取 SNoteItem(section)，
        调用 PageListModel.set_section() 刷新列表。
        每次分区切换时重置编辑区为 placeholder (D-63)。
        """
        source_index = self._section_filter.mapToSource(current)
        if source_index.isValid():
            section_item = source_index.internalPointer()
            self._page_list_model.set_section(section_item)
        else:
            self._page_list_model.set_section(None)
        self._show_editor_placeholder()

    def _on_page_current_changed(self, current: QModelIndex,
                                 previous: QModelIndex):
        """页面选择变化 → 显示只读预览 (D-62, D-63)。

        获取 SNoteItem(note) 后调用 QTextEdit.setHtml() 显示内容。
        无效选择（取消选择）时显示 placeholder。
        """
        note = self._page_list_model.note_at(current)
        if note is not None:
            self._show_note_in_editor(note)
        else:
            self._show_editor_placeholder()

    def _show_editor_placeholder(self):
        """显示 placeholder 提示文字 (D-63)，不写回当前页面。"""
        self._editor_stack.setCurrentIndex(1)
        self._rich_text_editor.load_html("")
        self._rich_text_editor.set_editor_enabled(False)

    def _on_editor_text_changed(self):
        """兼容旧测试入口：同步当前富文本 HTML。"""
        self._on_editor_content_changed(self._rich_text_editor.to_html())

    def _on_editor_content_changed(self, html: str):
        """编辑器内容变化时同步回当前页面并标记脏状态。"""
        if self._editor_stack.currentIndex() != 0:
            return
        if self._page_list_model is None:
            return
        current = self._list_view.currentIndex()
        note = self._page_list_model.note_at(current)
        if note is None:
            return
        if note.content != html:
            note.content = html
            self.mark_dirty()

    def _show_note_in_editor(self, note: SNoteItem):
        """显示页面内容到右侧编辑器，避免触发无意义脏标记。"""
        self._rich_text_editor.load_html(note.content or "")
        self._editor_stack.setCurrentIndex(0)
        self._rich_text_editor.set_editor_enabled(True)

    def _setup_tree_context_menu(self):
        """分区树右键菜单 (D-56)。

        右键分区节点: 新建子分区、新建页面、重命名分区、删除分区。
        右键空白区域: 新建分区。
        """
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.customContextMenuRequested.connect(
            self._on_tree_context_menu
        )

    def _on_tree_context_menu(self, pos):
        from PySide6.QtCore import QPoint
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        proxy_index = self._tree_view.indexAt(pos)

        if proxy_index.isValid():
            self._tree_view.setCurrentIndex(proxy_index)
            # 确认是 section 节点（Proxy 已过滤）
            menu.addAction("新建子分区", self._on_new_child_section)
            menu.addAction("新建页面", self._on_new_page_in_section)
            menu.addSeparator()
            menu.addAction("重命名分区", self._on_rename_section)
            menu.addAction("删除分区", self._on_delete_section)
        else:
            menu.addAction("新建分区", self._on_new_root_section)

        self._exec_context_menu(menu, self._tree_view.viewport().mapToGlobal(pos))

    def _exec_context_menu(self, menu, global_pos):
        return menu.exec(global_pos)

    def _setup_page_context_menu(self):
        """页面列表右键菜单 (D-56)。"""
        self._list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_view.viewport().setContextMenuPolicy(Qt.CustomContextMenu)
        self._list_view.customContextMenuRequested.connect(
            self._on_page_context_menu
        )
        self._list_view.viewport().customContextMenuRequested.connect(
            self._on_page_context_menu
        )

    def _on_page_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        try:
            proxy_index = self._list_view.indexAt(pos)
            if proxy_index.isValid():
                self._list_view.setCurrentIndex(proxy_index)
                menu.addAction("重命名页面", self._on_rename_page)
                menu.addAction("删除页面", self._on_delete_page)
            else:
                menu.addAction("新建页面", self._on_new_page)
            self._exec_context_menu(menu, self._list_view.viewport().mapToGlobal(pos))
        finally:
            menu.deleteLater()

    def _setup_navigation_shortcuts(self):
        """键盘快捷键 (D-57): Delete 删除、F2 重命名、Ctrl+N 新建页面。

        QAction + addAction 绑定到视图——Qt 自动处理焦点上下文。
        """
        # Delete — 上下文感知
        self._act_delete = QAction("删除", self)
        self._act_delete.setShortcut(QKeySequence.StandardKey.Delete)
        self._act_delete.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self._tree_view.addAction(self._act_delete)
        self._list_view.addAction(self._act_delete)
        self._act_delete.triggered.connect(self._on_delete_selected)

        # F2 重命名
        self._act_rename = QAction("重命名", self)
        self._act_rename.setShortcut(QKeySequence("F2"))
        self._act_rename.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self._tree_view.addAction(self._act_rename)
        self._list_view.addAction(self._act_rename)
        self._act_rename.triggered.connect(self._on_rename_selected)

        self._list_view.setFocusPolicy(Qt.StrongFocus)

    def _setup_global_shortcuts(self):
        self._shortcut_ctrl_n = QShortcut(QKeySequence("Ctrl+N"), self)
        self._shortcut_ctrl_n.setContext(Qt.WindowShortcut)
        self._shortcut_ctrl_n.activated.connect(self._on_ctrl_n)

    def _focus_in(self, widget) -> bool:
        focused = self.focusWidget()
        return focused is widget or widget.isAncestorOf(focused)

    def _on_ctrl_n(self):
        if (
            self._navigation_initialized
            and self._focus_in(self._list_view)
            and self._page_list_model is not None
            and self._page_list_model._section is not None
        ):
            self._on_new_page()
        else:
            self._on_new_notebook()

    def _initialize_navigation_state(self):
        """打开笔记本后展开分区树第一层并自动选中第一个子分区 (D-52, D-53)。

        遍历代理模型的根级行，仅 expand(index) — 不递归展开 (D-53)。
        然后选中根节点的第一个子分区 (D-52)。
        """
        proxy = self._section_filter
        # D-53: 仅展开第一层（根节点的直接子节点）
        for row in range(proxy.rowCount()):
            index = proxy.index(row, 0, QModelIndex())
            self._tree_view.expand(index)

        # D-52: 自动选中第一个子分区
        if proxy.rowCount() > 0:
            first_index = proxy.index(0, 0, QModelIndex())
            if first_index.isValid():
                self._tree_view.setCurrentIndex(first_index)

    # ── CRUD 操作 handlers (D-55, D-56, D-57, D-58, D-59, D-61, D-64) ──

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

    def _on_new_child_section(self):
        """在选中分区下创建子分区 (D-55, D-61)。"""
        current = self._tree_view.currentIndex()
        if not current.isValid():
            return
        source_index = self._section_filter.mapToSource(current)
        section = SNoteItem.new_section("新分区")
        self._tree_model.add_item(source_index, section)
        self.mark_dirty()
        self._select_new_child_section(current)
        self.statusBar().showMessage("已创建子分区: 新分区")

    def _on_rename_section(self):
        """对选中的分区进入编辑模式 (D-59)。"""
        current = self._tree_view.currentIndex()
        if current.isValid():
            self._tree_view.edit(current)

    def _rename_current_section(self, new_title: str) -> bool:
        """重命名当前分区并在成功时标记脏状态。"""
        current = self._tree_view.currentIndex()
        if not current.isValid():
            return False
        if self._tree_model.setData(
            self._section_filter.mapToSource(current), new_title
        ):
            self.mark_dirty()
            return True
        return False

    def _rename_current_page(self, new_title: str) -> bool:
        """重命名当前页面并在成功时标记脏状态。"""
        current = self._list_view.currentIndex()
        if not current.isValid():
            return False
        if self._page_list_model.setData(current, new_title):
            self.mark_dirty()
            return True
        return False

    def _on_delete_section(self):
        """删除选中的分区 (D-58, D-61, Pitfall 7)。"""
        current = self._tree_view.currentIndex()
        if not current.isValid():
            return
        source_index = self._section_filter.mapToSource(current)
        item = source_index.internalPointer()

        # D-58: 仅含子内容时弹出确认对话框
        if item.children:
            reply = QMessageBox.warning(
                self,
                "确认删除",
                f"分区「{item.title}」包含 {len(item.children)} 个子项目"
                f"（子分区或页面），删除后将一并移除。\n\n确定删除？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        # Pitfall 7: 检查是否删除了当前 PageListModel 的分区
        current_section = self._page_list_model._section
        self._tree_model.remove_item(source_index)
        self.mark_dirty()

        if current_section is item:
            self._page_list_model.set_section(None)
            self._show_editor_placeholder()
            parent_index = self._tree_view.currentIndex().parent()
            if parent_index.isValid():
                self._tree_view.setCurrentIndex(parent_index)

        self.statusBar().showMessage(f"已删除分区: {item.title}")

    def _on_new_page(self):
        """在当前分区下新建页面 (D-55, D-61, D-64)。"""
        if self._page_list_model._section is None:
            return
        note = SNoteItem.new_note("新页面")
        if self._page_list_model.add_note(note):
            self.mark_dirty()
            # D-64: 自动选中新创建的页面
            new_row = self._page_list_model.rowCount() - 1
            new_index = self._page_list_model.index(new_row, 0)
            self._list_view.setCurrentIndex(new_index)
            self.statusBar().showMessage("已创建页面: 新页面")

    def _on_new_page_in_section(self):
        """右键分区 → 新建页面: 在当前分区下创建页面。"""
        self._on_new_page()

    def _on_rename_page(self):
        """对选中的页面进入编辑模式 (D-59)。"""
        current = self._list_view.currentIndex()
        if current.isValid():
            self._list_view.edit(current)

    def _on_delete_page(self):
        """删除选中的页面 (D-58: 单页面不弹确认, D-61)。"""
        current = self._list_view.currentIndex()
        if not current.isValid():
            return
        note = self._page_list_model.note_at(current)
        self._page_list_model.remove_note(current)
        self.mark_dirty()
        self.statusBar().showMessage(f"已删除页面: {note.title if note else ''}")

    def _on_delete_selected(self):
        """Delete 键 — 根据焦点视图分发删除 (D-57)。"""
        if self._focus_in(self._list_view):
            self._on_delete_page()
        elif self._focus_in(self._tree_view):
            self._on_delete_section()

    def _on_rename_selected(self):
        """F2 键 — 根据焦点视图进入编辑模式 (D-57)。"""
        if self._focus_in(self._list_view):
            self._on_rename_page()
        elif self._focus_in(self._tree_view):
            self._on_rename_section()

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
        self._setup_navigation()                     # Phase 3: 导航系统
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

        # 先完成反序列化校验，避免坏文件破坏当前会话
        root = self._deserialize_opened_notebook(json_str)
        if root is None:
            return

        # 更新数据模型
        if self._tree_model is not None:
            self._tree_model.deleteLater()
        self._root_item = root
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)
        self._setup_navigation()                     # Phase 3: 导航系统

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
            (json_str, password) 解密成功时返回；用户取消或读取失败时返回 (None, None)
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

        root = self._deserialize_opened_notebook(json_str)
        if root is None:
            return

        if self._tree_model is not None:
            self._tree_model.deleteLater()
        self._root_item = root
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)
        self._setup_navigation()                     # Phase 3: 导航系统

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
