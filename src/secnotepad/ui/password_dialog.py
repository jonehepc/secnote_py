"""统一密码对话框 (D-30 至 D-39)"""

import math
from enum import Enum, auto

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                                QLabel, QLineEdit, QPushButton,
                                QCheckBox, QProgressBar, QStyle)


class PasswordMode(Enum):
    """密码对话框模式 (D-30)"""
    SET_PASSWORD = auto()       # 新建/首次保存
    ENTER_PASSWORD = auto()     # 打开文件
    CHANGE_PASSWORD = auto()    # 另存为


class PasswordDialog(QDialog):
    """统一密码对话框，支持三种模式。

    内部以 bytearray 存储密码，支持显式安全清零 (D-27, D-39)。
    """

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

        # --- SET_PASSWORD / CHANGE_PASSWORD 共有: 密码+确认密码字段 ---
        # 这些控件在 CHANGE_PASSWORD 模式下初始隐藏
        self._pwd_input = QLineEdit()
        self._pwd_input.setEchoMode(QLineEdit.Password)
        self._pwd_input.setPlaceholderText("")
        self._add_eye_toggle(self._pwd_input)

        self._confirm_input = QLineEdit()
        self._confirm_input.setEchoMode(QLineEdit.Password)
        self._confirm_input.setPlaceholderText("")
        self._add_eye_toggle(self._confirm_input)

        # 密码不一致警告
        self._mismatch_warning = QLabel("两次输入的密码不一致")
        self._mismatch_warning.setStyleSheet("color: red;")
        self._mismatch_warning.setVisible(False)

        # 密码强度指示器
        self._strength_bar = QProgressBar()
        self._strength_bar.setRange(0, 100)
        self._strength_bar.setVisible(False)
        self._strength_bar.setTextVisible(False)

        self._strength_label = QLabel()
        self._strength_label.setVisible(False)

        # 生成密码按钮
        self._btn_generate = QPushButton("生成密码")
        self._btn_generate.clicked.connect(self._on_open_generator)

        if mode == PasswordMode.SET_PASSWORD:
            layout.addWidget(QLabel("密码"))
            layout.addWidget(self._pwd_input)
            layout.addWidget(QLabel("确认密码"))
            layout.addWidget(self._confirm_input)
            layout.addWidget(self._mismatch_warning)

            # 强度布局
            strength_layout = QHBoxLayout()
            strength_layout.addWidget(self._strength_bar)
            strength_layout.addWidget(self._strength_label)
            layout.addLayout(strength_layout)

            layout.addWidget(self._btn_generate)
            self._change_widgets = []

        elif mode == PasswordMode.ENTER_PASSWORD:
            layout.addWidget(QLabel("请输入文件加密密码"))
            layout.addWidget(self._pwd_input)
            # 错误标签
            self._error_label = QLabel("密码错误，请重试")
            self._error_label.setStyleSheet("color: red;")
            self._error_label.setVisible(False)
            layout.addWidget(self._error_label)
            # ENTER_PASSWORD 不需要确认字段, 强度条, 生成按钮
            self._confirm_input.setVisible(False)
            self._mismatch_warning.setVisible(False)
            self._strength_bar.setVisible(False)
            self._strength_label.setVisible(False)
            self._btn_generate.setVisible(False)

        elif mode == PasswordMode.CHANGE_PASSWORD:
            # 新密码相关控件初始隐藏
            layout.addWidget(QLabel("新密码"))
            layout.addWidget(self._pwd_input)
            layout.addWidget(QLabel("确认密码"))
            layout.addWidget(self._confirm_input)
            layout.addWidget(self._mismatch_warning)

            strength_layout = QHBoxLayout()
            strength_layout.addWidget(self._strength_bar)
            strength_layout.addWidget(self._strength_label)
            layout.addLayout(strength_layout)

            layout.addWidget(self._btn_generate)
            self._change_widgets = [
                self._pwd_input, self._confirm_input,
                self._mismatch_warning,
                self._strength_bar, self._strength_label,
                self._btn_generate,
            ]
            # 初始隐藏所有 change 相关控件
            self._set_change_visible(False)

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

    # ── 公开接口 ──

    def set_error_message(self, text: str):
        """设置 ENTER_PASSWORD 模式的错误提示文字并显示 (D-35)。

        Args:
            text: 错误提示文案，如 "密码错误，请重试"
        """
        if self._mode == PasswordMode.ENTER_PASSWORD:
            self._error_label.setText(text)
            self._error_label.show()

    def password(self) -> str:
        """返回密码字符串。

        调用方使用后应立即调用 clear_password() 清空。
        内部以 bytearray 存储实现安全清零 (D-27, D-39)。

        Returns:
            密码字符串，空 bytearray 时返回空字符串。
        """
        return str(self._password, encoding='ascii') if self._password else ""

    def clear_password(self):
        """显式清空内存中的密码 (D-27, D-39)。

        使用 bytearray 原地覆盖清零，不依赖 Python GC。
        """
        self._password[:] = b'\x00' * len(self._password)

    # ── 内部方法 ──

    @staticmethod
    def _evaluate_strength(password: str) -> tuple[int, str]:
        """评估密码强度。

        Returns:
            (百分比 0-100, 标签文字)
        """
        if not password:
            return 0, ""
        # 计算字符集大小
        charset_size = 0
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            charset_size += 32
        # 熵 = length * log2(charset_size)
        if charset_size == 0:
            return 0, ""
        entropy = len(password) * math.log2(charset_size)
        # 映射到百分比
        # < 40 bits: 弱, 40-60: 中, > 60: 强
        if entropy < 40:
            return max(1, int(entropy / 40 * 33)), "弱"
        elif entropy < 60:
            return 33 + int((entropy - 40) / 20 * 34), "中"
        else:
            return 67 + min(33, int((entropy - 60) / 40 * 33)), "强"

    def _add_eye_toggle(self, line_edit: QLineEdit):
        """在 QLineEdit 右侧添加眼睛图标切换密码可见性 (D-37)。"""
        action = QAction(line_edit)
        action.setCheckable(True)
        icon = self.style().standardIcon(QStyle.SP_DialogApplyButton)
        action.setIcon(icon)
        action.triggered.connect(lambda checked: line_edit.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        ))
        line_edit.addAction(action, QLineEdit.TrailingPosition)

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

    def _update_confirm_button(self):
        """根据当前模式更新确认按钮启用状态。"""
        if self._mode == PasswordMode.SET_PASSWORD:
            pwd = self._pwd_input.text()
            confirm = self._confirm_input.text()
            valid = len(pwd) >= 8 and pwd == confirm
            self._btn_confirm.setEnabled(valid)

        elif self._mode == PasswordMode.ENTER_PASSWORD:
            pwd = self._pwd_input.text()
            self._btn_confirm.setEnabled(len(pwd) > 0)

        elif self._mode == PasswordMode.CHANGE_PASSWORD:
            if self._cb_change and not self._cb_change.isChecked():
                self._btn_confirm.setEnabled(True)
            else:
                pwd = self._pwd_input.text()
                confirm = self._confirm_input.text()
                valid = len(pwd) >= 8 and pwd == confirm
                self._btn_confirm.setEnabled(valid)

    def _on_confirm(self):
        """确认按钮点击处理。"""
        pwd_text = self._pwd_input.text()
        if self._mode == PasswordMode.CHANGE_PASSWORD:
            if self._cb_change and self._cb_change.isChecked():
                self._password = bytearray(pwd_text.encode('ascii'))
            else:
                self._password = bytearray()
        else:
            self._password = bytearray(pwd_text.encode('ascii'))
        self.accept()

    def _on_open_generator(self):
        """打开密码生成器子对话框 (D-33)。"""
        from .password_generator import PasswordGenerator
        gen = PasswordGenerator(self)
        if gen.exec() == QDialog.Accepted:
            generated = gen.password()
            self._pwd_input.setText(generated)
            self._confirm_input.setText(generated)

    def _on_change_toggled(self, checked: bool):
        """CHANGE_PASSWORD 模式复选框切换。"""
        self._set_change_visible(checked)
        if not checked:
            self._pwd_input.clear()
            self._confirm_input.clear()
            self._mismatch_warning.setVisible(False)
            self._strength_bar.setVisible(False)
            self._strength_label.setVisible(False)
        self._update_confirm_button()

    def _set_change_visible(self, visible: bool):
        """切换 CHANGE_PASSWORD 模式下的密码字段可见性。"""
        for w in self._change_widgets:
            w.setVisible(visible)
        # 查找布局中的新密码/确认密码标签并设置可见性
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                text = item.widget().text()
                if text in ("新密码", "确认密码"):
                    item.widget().setVisible(visible)
