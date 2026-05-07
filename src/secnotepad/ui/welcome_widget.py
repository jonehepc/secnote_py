"""欢迎页组件 (D-15)"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                                QPushButton)


class WelcomeWidget(QWidget):
    """笔记本应用的欢迎页面

    提供应用名称、简介、新建/打开按钮和最近文件预留区域。
    按钮点击通过信号通知 MainWindow。
    """

    new_notebook_clicked = Signal()
    open_notebook_clicked = Signal()

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

        # 最近文件列表占位区域（后续 Phase 实现）
        layout.addWidget(QLabel("最近文件（功能待实现）"))

        layout.addStretch()

    @property
    def new_button(self) -> QPushButton:
        """新建笔记本按钮"""
        return self._btn_new

    @property
    def open_button(self) -> QPushButton:
        """打开笔记本按钮"""
        return self._btn_open
