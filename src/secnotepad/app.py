"""应用初始化模块"""

import sys
from PySide6.QtWidgets import QApplication


def create_app() -> QApplication:
    """创建并返回 QApplication 实例

    使用 QApplication.instance() 检查是否已存在实例，
    避免在测试环境中重复创建。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setApplicationName("SecNotepad")
    return app
