"""Tests for MainWindow UI (D-12 to D-20)"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QStackedWidget, QMenuBar, QStatusBar

from src.secnotepad.ui.main_window import MainWindow
from src.secnotepad.ui.welcome_widget import WelcomeWidget


# ── Fixtures ──


@pytest.fixture
def window(qapp):
    """创建 MainWindow 实例，测试结束后自动清理。"""
    w = MainWindow()
    w.show()
    yield w
    w.close()
    w.deleteLater()


# ── 窗口设置 (D-19) ──


class TestWindowSetup:
    """D-19: 窗口标题、大小"""

    def test_window_title(self, window):
        """窗口标题为 'SecNotepad'"""
        assert window.windowTitle() == "SecNotepad"

    def test_window_default_size(self, window):
        """初始大小 1200x800"""
        assert window.width() >= 1200
        assert window.height() >= 800

    def test_window_minimum_size(self, window):
        """最小 800x600"""
        assert window.minimumWidth() == 800
        assert window.minimumHeight() == 600


# ── 欢迎页 (D-15) ──


class TestWelcomePage:
    """D-15: 欢迎页显示与按钮"""

    def test_default_welcome_page(self, window):
        """默认显示欢迎页 (stack index 0)"""
        assert isinstance(window._stack, QStackedWidget)
        assert window._stack.currentIndex() == 0
        assert isinstance(window._stack.widget(0), WelcomeWidget)

    def test_welcome_has_buttons(self, window):
        """欢迎页有新建/打开按钮"""
        welcome = window._stack.widget(0)
        assert isinstance(welcome, WelcomeWidget)
        assert welcome.new_button is not None
        assert welcome.open_button is not None
        assert welcome.new_button.text() == "新建笔记本"
        assert welcome.open_button.text() == "打开笔记本"

    def test_welcome_signals_exist(self, window):
        """WelcomeWidget 具备所需的信号"""
        welcome = window._stack.widget(0)
        assert hasattr(welcome, "new_notebook_clicked")
        assert hasattr(welcome, "open_notebook_clicked")


# ── 新建笔记本 ──


class TestNewNotebook:
    """D-14: 新建笔记本流程"""

    def test_new_notebook_switches_to_editor(self, window):
        """新建后切换到三栏布局 (stack index 1)"""
        window._on_new_notebook()
        assert window._stack.currentIndex() == 1

    def test_new_notebook_sets_model(self, window):
        """新建后 tree_view 有 model"""
        window._on_new_notebook()
        assert window._tree_view.model() is not None

    def test_new_notebook_creates_root_item(self, window):
        """新建后 _root_item 已设置"""
        window._on_new_notebook()
        assert window._root_item is not None

    def test_new_notebook_updates_status(self, window):
        """新建后状态栏显示未保存"""
        window._on_new_notebook()
        assert "未保存" in window.statusBar().currentMessage()

    def test_new_notebook_stack_has_two_pages(self, window):
        """QStackedWidget 有两个页面 (欢迎页 + 编辑器)"""
        assert window._stack.count() == 2

    def test_editor_page_is_splitter(self, window):
        """三栏布局是 QSplitter 实例"""
        splitter = window._stack.widget(1)
        assert isinstance(splitter, QSplitter)


# ── 三栏布局 (D-12, D-13) ──


class TestSplitterLayout:
    """D-12, D-13: 三栏布局属性"""

    @pytest.fixture
    def splitter(self, window):
        """获取三栏 QSplitter"""
        window._on_new_notebook()
        return window._stack.widget(1)

    def test_splitter_layout(self, splitter):
        """分割线有三栏"""
        assert splitter.count() == 3

    def test_splitter_left_collapsible(self, splitter):
        """左侧面板可折叠 (D-13)"""
        assert splitter.isCollapsible(0) is True

    def test_splitter_middle_not_collapsible(self, splitter):
        """中间面板始终可见 (D-13)"""
        assert splitter.isCollapsible(1) is False

    def test_splitter_right_collapsible(self, splitter):
        """右侧面板可折叠 (D-13)"""
        assert splitter.isCollapsible(2) is True

    def test_splitter_left_min_width(self, splitter):
        """左侧 TreeView 最小 100px"""
        widget = splitter.widget(0)
        assert widget.minimumWidth() <= 100

    def test_splitter_middle_min_width(self, splitter):
        """中间 ListView 最小 100px"""
        widget = splitter.widget(1)
        assert widget.minimumWidth() <= 100

    def test_tree_view_exists(self, splitter):
        """左侧是 QTreeView"""
        from PySide6.QtWidgets import QTreeView
        assert isinstance(splitter.widget(0), QTreeView)

    def test_list_view_exists(self, splitter):
        """中间是 QListView"""
        from PySide6.QtWidgets import QListView
        assert isinstance(splitter.widget(1), QListView)

    def test_editor_placeholder_exists(self, splitter):
        """右侧是 QWidget 编辑区占位"""
        from PySide6.QtWidgets import QWidget
        assert isinstance(splitter.widget(2), QWidget)


# ── 菜单栏 (D-16) ──


class TestMenuBar:
    """D-16: 菜单栏结构"""

    def test_menu_bar_exists(self, window):
        """窗口有菜单栏"""
        assert window.menuBar() is not None

    def test_menu_actions_exist(self, window):
        """菜单栏有文件/编辑/视图/帮助"""
        mb = window.menuBar()
        actions = mb.actions()
        texts = [a.text() for a in actions]
        assert any("文件" in t for t in texts)
        assert any("编辑" in t for t in texts)
        assert any("视图" in t for t in texts)
        assert any("帮助" in t for t in texts)

    def test_save_action_disabled(self, window):
        """保存菜单灰显"""
        assert window._act_save.isEnabled() is False

    def test_save_as_action_disabled(self, window):
        """另存为菜单灰显"""
        assert window._act_save_as.isEnabled() is False

    def test_edit_actions_disabled(self, window):
        """编辑菜单全部灰显"""
        for act in window._edit_actions:
            assert act.isEnabled() is False

    def test_view_action_disabled(self, window):
        """视图菜单灰显"""
        assert window._act_toggle_panels.isEnabled() is False

    def test_help_action_disabled(self, window):
        """帮助菜单灰显"""
        assert window._act_about.isEnabled() is False

    def test_new_action_shortcut(self, window):
        """新建菜单快捷键 Ctrl+N"""
        assert window._act_new.shortcut().toString() == "Ctrl+N"

    def test_exit_action_shortcut(self, window):
        """退出菜单快捷键 Ctrl+Q"""
        assert window._act_exit.shortcut().toString() == "Ctrl+Q"


# ── 工具栏 (D-17) ──


class TestToolBar:
    """D-17: 工具栏属性"""

    def test_toolbar_exists(self, window):
        """工具栏存在"""
        tb = window.findChild(type(window._tb_new.parent()))
        assert tb is not None

    def test_toolbar_not_movable(self, window):
        """工具栏不可移动"""
        tbs = window.findChildren(type(window._tb_new.parent()))
        tb = tbs[0]
        assert tb.isMovable() is False

    def test_toolbar_save_disabled(self, window):
        """工具栏保存按钮灰显"""
        assert window._tb_save.isEnabled() is False

    def test_toolbar_saveas_disabled(self, window):
        """工具栏另存为按钮灰显"""
        assert window._tb_saveas.isEnabled() is False

    def test_toolbar_new_enabled(self, window):
        """工具栏新建按钮可用"""
        assert window._tb_new.isEnabled() is True

    def test_toolbar_open_enabled(self, window):
        """工具栏打开按钮可用"""
        assert window._tb_open.isEnabled() is True


# ── 状态栏 (D-18) ──


class TestStatusBar:
    """D-18: 状态栏初始状态"""

    def test_status_bar_ready(self, window):
        """状态栏显示 '就绪'"""
        assert window.statusBar().currentMessage() == "就绪"
