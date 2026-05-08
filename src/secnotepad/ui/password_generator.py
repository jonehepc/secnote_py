"""密码生成器子对话框 (D-33, CRYPT-04)"""

import secrets
import string

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                QLabel, QSpinBox, QCheckBox,
                                QPushButton, QLineEdit, QDialogButtonBox)


class PasswordGenerator(QDialog):
    """可调长度和字符集的随机密码生成器。"""

    CHARSETS = {
        "uppercase": string.ascii_uppercase,   # ABCDEFGHIJKLMNOPQRSTUVWXYZ
        "lowercase": string.ascii_lowercase,   # abcdefghijklmnopqrstuvwxyz
        "digits": string.digits,               # 0123456789
        "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("生成密码")
        self.setModal(True)
        self._password = ""

        layout = QVBoxLayout(self)

        # 密码长度
        len_layout = QHBoxLayout()
        len_layout.addWidget(QLabel("密码长度："))
        self._spin_length = QSpinBox()
        self._spin_length.setRange(8, 128)
        self._spin_length.setValue(16)
        len_layout.addWidget(self._spin_length)
        len_layout.addStretch()
        layout.addLayout(len_layout)

        # 字符集选择
        self._checkboxes = {}
        charset_layout = QVBoxLayout()
        for key, label in [
            ("uppercase", "大写字母"),
            ("lowercase", "小写字母"),
            ("digits", "数字"),
            ("symbols", "符号"),
        ]:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.toggled.connect(self._on_charset_toggled)
            self._checkboxes[key] = cb
            charset_layout.addWidget(cb)
        layout.addLayout(charset_layout)

        # 密码预览
        preview_layout = QHBoxLayout()
        self._preview = QLineEdit()
        self._preview.setReadOnly(True)
        self._preview.setPlaceholderText("请至少选择一种字符类型")
        preview_layout.addWidget(self._preview)
        layout.addLayout(preview_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        self._btn_generate = QPushButton("生成并使用")
        self._btn_generate.clicked.connect(self._on_accept)
        btn_layout.addStretch()
        btn_layout.addWidget(self._btn_generate)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # 初始生成
        self._generate()

    def _on_charset_toggled(self):
        """至少一个字符集被选中时启用生成。"""
        any_checked = any(cb.isChecked() for cb in self._checkboxes.values())
        self._btn_generate.setEnabled(any_checked)
        if any_checked:
            self._generate()
        else:
            self._preview.clear()
            self._preview.setPlaceholderText("请至少选择一种字符类型")

    def _generate(self):
        """使用 secrets 模块生成随机密码。"""
        chars = ""
        for key, charset in self.CHARSETS.items():
            if self._checkboxes[key].isChecked():
                chars += charset
        if not chars:
            return
        length = self._spin_length.value()
        self._password = "".join(secrets.choice(chars) for _ in range(length))
        self._preview.setText(self._password)

    def _on_accept(self):
        """确认生成并关闭 — 使用当前显示的密码，不重新生成。"""
        self.accept()

    def password(self) -> str:
        """返回生成的密码字符串。"""
        return self._password
