"""SecNotepad 主窗口 (D-12 至 D-20)"""

from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QWidget, QSplitter,
                                QTreeView, QListView, QStackedWidget,
                                QStyle, QVBoxLayout)
from PySide6.QtCore import Qt

from ..model.snote_item import SNoteItem
from ..model.tree_model import TreeModel
from .welcome_widget import WelcomeWidget


class MainWindow(QMainWindow):
    """SecNotepad 应用主窗口

    包含欢迎页/三栏布局切换、菜单栏、工具栏、状态栏。
    """

    def __init__(self):
        super().__init__()
        # 当前笔记本数据 (Phase 2 后持久化)
        self._root_item: SNoteItem = None
        self._tree_model: TreeModel = None

        self._setup_window()
        self._setup_menu_bar()
        self._setup_tool_bar()
        self._setup_central_area()
        self._setup_status_bar()
        self._connect_actions()

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

    # ── 动作处理 ──

    # ── 动作连接 ──

    def _connect_actions(self):
        """连接菜单/工具栏动作到处理函数"""
        # 新建：菜单、工具栏、欢迎页按钮均已连接
        self._act_new.triggered.connect(self._on_new_notebook)
        self._tb_new.triggered.connect(self._on_new_notebook)
        # 打开（Phase 2 实现）
        self._act_open.triggered.connect(self._on_open_notebook)
        self._tb_open.triggered.connect(self._on_open_notebook)

    def _on_new_notebook(self):
        """新建空白笔记本 (D-14)"""
        self._root_item = SNoteItem.new_section("根分区")
        self._tree_model = TreeModel(self._root_item, self)
        self._tree_view.setModel(self._tree_model)
        self._stack.setCurrentIndex(1)               # 切换到三栏布局
        self.statusBar().showMessage("新建笔记本 - 未保存")

    def _on_open_notebook(self):
        """打开笔记本 (Phase 2 实现)"""
        self.statusBar().showMessage("打开笔记本 - 功能待实现")
