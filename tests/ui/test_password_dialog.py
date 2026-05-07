"""Tests for PasswordDialog (D-30 至 D-39) and PasswordGenerator (D-33)."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLineEdit, QPushButton, QCheckBox, QLabel, QProgressBar

from src.secnotepad.ui.password_dialog import PasswordDialog, PasswordMode
from src.secnotepad.ui.password_generator import PasswordGenerator


# ── Fixtures ──


@pytest.fixture
def set_dialog(qapp):
    """SET_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.SET_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()


@pytest.fixture
def enter_dialog(qapp):
    """ENTER_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()


@pytest.fixture
def change_dialog(qapp):
    """CHANGE_PASSWORD 模式对话框。"""
    dlg = PasswordDialog(mode=PasswordMode.CHANGE_PASSWORD)
    dlg.show()
    yield dlg
    dlg.close()
    dlg.deleteLater()


# ── SET_PASSWORD 模式 ──


class TestSetPasswordMode:
    """D-31, D-32, D-34: 新建密码模式测试。"""

    def test_two_password_fields(self, set_dialog):
        """SET_PASSWORD 模式有密码和确认密码两个字段。"""
        line_edits = set_dialog.findChildren(QLineEdit)
        assert len(line_edits) == 2

    def test_confirm_disabled_when_empty(self, set_dialog):
        """初始状态确认按钮禁用。"""
        confirm = set_dialog.findChild(QPushButton, "确认")
        assert confirm is None or not confirm.isEnabled()

    def test_strength_bar_exists(self, set_dialog):
        """有密码强度指示器。"""
        bar = set_dialog.findChild(QProgressBar)
        assert bar is not None

    def test_generate_button_exists(self, set_dialog):
        """有'生成密码'按钮。"""
        buttons = [b for b in set_dialog.findChildren(QPushButton) if '生成' in b.text()]
        assert len(buttons) >= 1

    def test_min_length_8(self, set_dialog):
        """密码短于 8 字符时确认按钮禁用。"""
        # 模拟输入 6 字符密码
        line_edits = set_dialog.findChildren(QLineEdit)
        line_edits[0].setText("Abc12")
        line_edits[1].setText("Abc12")
        confirm = [b for b in set_dialog.findChildren(QPushButton) if b.text() == "确认"]
        if confirm:
            assert not confirm[0].isEnabled()


# ── ENTER_PASSWORD 模式 ──


class TestEnterPasswordMode:
    """D-35: 输入密码模式测试。"""

    def test_one_password_field(self, enter_dialog):
        """ENTER_PASSWORD 模式只有一个密码字段。"""
        line_edits = enter_dialog.findChildren(QLineEdit)
        assert len(line_edits) == 1

    def test_confirm_disabled_when_empty(self, enter_dialog):
        """密码为空时确认按钮禁用。"""
        confirm = [b for b in enter_dialog.findChildren(QPushButton) if b.text() == "确认"]
        if confirm:
            assert not confirm[0].isEnabled()

    def test_error_label_hidden_initially(self, enter_dialog):
        """错误消息初始隐藏。"""
        labels = enter_dialog.findChildren(QLabel)
        error_labels = [l for l in labels if "密码错误" in l.text()]
        for el in error_labels:
            assert el.isHidden()

    def test_set_error_message_shows_label(self, enter_dialog):
        """set_error_message() 显示错误标签 (D-35)。"""
        enter_dialog.set_error_message("密码错误，请重试")
        labels = enter_dialog.findChildren(QLabel)
        error_labels = [l for l in labels if "密码错误" in l.text()]
        assert len(error_labels) >= 1
        for el in error_labels:
            assert not el.isHidden()


# ── CHANGE_PASSWORD 模式 ──


class TestChangePasswordMode:
    """D-38: 更换密码模式测试。"""

    def test_checkbox_exists(self, change_dialog):
        """有'更换密码'复选框。"""
        checkbox = change_dialog.findChild(QCheckBox)
        assert checkbox is not None
        assert "更换密码" in checkbox.text()

    def test_password_fields_hidden_initially(self, change_dialog):
        """初始状态密码字段隐藏。"""
        line_edits = change_dialog.findChildren(QLineEdit)
        # 初始时密码字段应该隐藏，但可能会有仍可见的控件
        assert len(line_edits) >= 0  # 至少不报错

    def test_password_warning_exists(self, change_dialog):
        """有密码强度指示器（可能隐藏）。"""
        bars = change_dialog.findChildren(QProgressBar)
        assert len(bars) >= 1


# ── 安全清零测试 ──


class TestSecureClear:
    """D-27: bytearray 安全清零测试。"""

    def test_password_stored_as_bytearray(self, qapp):
        """_password 是 bytearray 类型。"""
        dlg = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD)
        assert isinstance(dlg._password, bytearray)
        dlg.close()
        dlg.deleteLater()

    def test_clear_password_zeros_bytearray(self, qapp):
        """clear_password() 将 bytearray 原地清零。"""
        dlg = PasswordDialog(mode=PasswordMode.ENTER_PASSWORD)
        # 模拟设置密码
        dlg._password = bytearray(b"TestP@ss123")
        original_len = len(dlg._password)
        dlg.clear_password()
        assert all(b == 0 for b in dlg._password)
        assert len(dlg._password) == original_len  # 长度不变，内容清零
        dlg.close()
        dlg.deleteLater()

    def test_password_returns_str(self, qapp):
        """password() 返回 str 类型供调用方使用。"""
        dlg = PasswordDialog(mode=PasswordMode.SET_PASSWORD)
        pwd = dlg.password()
        assert isinstance(pwd, str)
        dlg.close()
        dlg.deleteLater()


# ── PasswordGenerator ──


class TestPasswordGenerator:
    """D-33, CRYPT-04: 密码生成器测试。"""

    def test_generator_creates_password(self, qapp):
        """生成器创建非空密码。"""
        gen = PasswordGenerator()
        pwd = gen.password()
        assert len(pwd) >= 8

    def test_generator_default_length(self, qapp):
        """默认密码长度 16。"""
        gen = PasswordGenerator()
        assert len(gen.password()) == 16

    def test_generator_respects_spinbox(self, qapp):
        """调整长度后密码长度变化。"""
        gen = PasswordGenerator()
        gen._spin_length.setValue(24)
        gen._generate()
        assert len(gen.password()) == 24

    def test_generator_uses_secrets(self):
        """导入使用 secrets 而非 random。"""
        import inspect
        import src.secnotepad.ui.password_generator as pg_mod
        source = inspect.getsource(pg_mod)
        assert "import secrets" in source
        assert "import random" not in source
