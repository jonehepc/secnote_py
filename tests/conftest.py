"""共享测试 fixture 和配置"""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """提供 QApplication 实例用于 pytest-qt 测试

    使用 session scope 确保整个测试套件复用同一个
    QApplication 实例，避免多个实例创建导致的崩溃。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
