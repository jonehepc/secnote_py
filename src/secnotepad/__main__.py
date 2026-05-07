"""应用入口: python -m secnotepad"""

import sys
from .app import create_app


def main():
    """启动 SecNotepad 应用"""
    app = create_app()
    # MainWindow 由 Plan 05 (ui/main_window.py) 创建
    # 此模块在 Plan 05 完成后才能正常运行
    from .ui.main_window import MainWindow  # noqa: F811
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
