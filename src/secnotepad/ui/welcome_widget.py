"""欢迎页组件 (D-15) — 含最近文件列表 (Phase 2)"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                                QPushButton, QListWidget)
from PySide6.QtCore import Qt


class WelcomeWidget(QWidget):
    """笔记本应用的欢迎页面"""

    new_notebook_clicked = Signal()
    open_notebook_clicked = Signal()
    recent_file_clicked = Signal(str)  # Phase 2: 单击最近文件 (D-43)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        layout.addStretch()

        # 应用名称
        title_label = QLabel("SecNotepad")
        title_font = title_label.font()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # 应用简介
        desc_label = QLabel("安全的本地加密笔记本")
        desc_font = desc_label.font()
        desc_font.setPointSize(12)
        desc_label.setFont(desc_font)
        layout.addWidget(desc_label)

        layout.addSpacing(20)

        # 新建笔记本按钮
        self._btn_new = QPushButton("新建笔记本")
        self._btn_new.setFixedWidth(200)
        self._btn_new.clicked.connect(self.new_notebook_clicked.emit)
        layout.addWidget(self._btn_new)

        # 打开笔记本按钮
        self._btn_open = QPushButton("打开笔记本")
        self._btn_open.setFixedWidth(200)
        self._btn_open.clicked.connect(self.open_notebook_clicked.emit)
        layout.addWidget(self._btn_open)

        layout.addSpacing(30)

        # ── 最近文件列表 (Phase 2, D-40~D-44) ──
        recent_label = QLabel("最近打开的文件")
        recent_font = recent_label.font()
        recent_font.setBold(True)
        recent_label.setFont(recent_font)
        layout.addWidget(recent_label)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(150)
        self._recent_list.setMinimumWidth(300)
        self._recent_list.itemClicked.connect(self._on_recent_item_clicked)
        layout.addWidget(self._recent_list)

        # 空状态标签（初始隐藏，无最近文件时显示）
        self._empty_label = QLabel("暂无最近打开的文件")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet("color: gray;")
        self._empty_label.hide()
        layout.addWidget(self._empty_label)

        layout.addStretch()

    # ── 公开方法 ──

    def set_recent_files(self, paths: list[str]):
        """设置最近文件列表显示。

        Args:
            paths: 文件绝对路径列表（最多 5 条）。
        """
        self._recent_list.clear()
        if not paths:
            self._recent_list.hide()
            self._empty_label.show()
        else:
            self._recent_list.show()
            self._empty_label.hide()
            for path in paths:
                self._recent_list.addItem(path)

    # ── 内部方法 ──

    def _on_recent_item_clicked(self, item):
        """单击最近文件条目，发射信号 (D-43)。"""
        self.recent_file_clicked.emit(item.text())

    # ── 属性 ──

    @property
    def new_button(self) -> QPushButton:
        """新建笔记本按钮"""
        return self._btn_new

    @property
    def open_button(self) -> QPushButton:
        """打开笔记本按钮"""
        return self._btn_open

    @property
    def recent_list(self) -> QListWidget:
        """最近文件列表"""
        return self._recent_list
