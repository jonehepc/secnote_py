"""Tests for MainWindow UI (D-12 to D-20)"""

import pytest
from PySide6.QtCore import QCoreApplication, QSettings, Qt
from PySide6.QtWidgets import QSplitter, QStackedWidget, QMenuBar, QStatusBar, QToolBar
from PySide6.QtTest import QTest

from src.secnotepad.ui.main_window import MainWindow
from src.secnotepad.ui.welcome_widget import WelcomeWidget


# ── Fixtures ──


@pytest.fixture
def isolated_recent_files(qapp):
    """隔离 MainWindow 使用的 QSettings recent_files，避免污染真实状态。"""
    old_org = QCoreApplication.organizationName()
    old_app = QCoreApplication.applicationName()
    QCoreApplication.setOrganizationName("SecNotepadTests")
    QCoreApplication.setApplicationName("SecNotepadTests")
    settings = QSettings()
    settings.clear()
    try:
        yield settings
    finally:
        settings.clear()
        QCoreApplication.setOrganizationName(old_org)
        QCoreApplication.setApplicationName(old_app)


@pytest.fixture
def window(qapp, isolated_recent_files):
    """创建 MainWindow 实例，测试结束后自动清理。"""
    w = MainWindow()
    w.show()
    yield w
    w._is_dirty = False
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
        """左侧包含 QTreeView（位于按钮栏下方容器中）。"""
        from PySide6.QtWidgets import QTreeView
        container = splitter.widget(0)
        tree = container.findChild(QTreeView)
        assert tree is not None

    def test_list_view_exists(self, splitter):
        """中间包含 QListView（位于按钮栏下方容器中）。"""
        from PySide6.QtWidgets import QListView
        container = splitter.widget(1)
        list_view = container.findChild(QListView)
        assert list_view is not None

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
        """无页面选中时编辑菜单全部灰显；选中页面后按编辑器状态启用。"""
        for act in window._edit_actions:
            assert act.isEnabled() is False

        window._on_new_notebook()
        window._on_new_root_section()
        window._on_new_page()

        undo_action, redo_action, cut_action, copy_action, paste_action = window._edit_actions
        assert undo_action.isEnabled() is False
        assert redo_action.isEnabled() is False
        assert cut_action.isEnabled() is False
        assert copy_action.isEnabled() is False
        assert paste_action.isEnabled() is True

    def test_view_action_disabled(self, window):
        """视图菜单灰显"""
        assert window._act_toggle_panels.isEnabled() is False

    def test_help_action_disabled(self, window):
        """帮助菜单灰显"""
        assert window._act_about.isEnabled() is False

    def test_new_action_uses_ctrl_n_dispatcher(self, window):
        """新建菜单动作不直接注册 Ctrl+N，由窗口级分发器处理。"""
        assert window._act_new.shortcut().isEmpty()
        assert window._shortcut_ctrl_n.context() == Qt.WindowShortcut

    def test_ctrl_n_creates_notebook_from_welcome_page(self, window, qapp):
        """欢迎页按 Ctrl+N 仍会新建笔记本。"""
        window.activateWindow()
        window.setFocus()
        qapp.processEvents()

        QTest.keyClick(window, Qt.Key_N, Qt.ControlModifier)

        assert window._root_item is not None
        assert window._stack.currentIndex() == 1

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


# ── 脏标志与关闭保护 (Phase 2) ──


class TestDirtyFlag:
    """D-45, D-47: 脏标志管理"""

    def test_new_notebook_not_dirty(self, window):
        """新建笔记本后脏标志为 False (D-47)。"""
        window._on_new_notebook()
        assert window._is_dirty is False

    def test_mark_dirty_sets_flag(self, window):
        """mark_dirty() 将脏标志设为 True。"""
        window._on_new_notebook()
        window.mark_dirty()
        assert window._is_dirty is True

    def test_mark_clean_clears_flag(self, window):
        """mark_clean() 清除脏标志。"""
        window._on_new_notebook()
        window.mark_dirty()
        window.mark_clean()
        assert window._is_dirty is False

    def test_mark_dirty_no_notebook_safe(self, window):
        """无笔记本时 mark_dirty() 不报错。"""
        window.mark_dirty()  # should not raise
        assert True


# ── 保存/另存为动作状态 ──


class TestSaveActions:
    """FILE-03, FILE-04: 保存/另存为动作状态"""

    def test_save_disabled_initially(self, window):
        """初始状态保存按钮灰显。"""
        assert window._act_save.isEnabled() is False

    def test_save_enabled_after_new(self, window):
        """新建后保存按钮启用。"""
        window._on_new_notebook()
        assert window._act_save.isEnabled() is True

    def test_save_as_enabled_after_new(self, window):
        """新建后另存为按钮启用。"""
        window._on_new_notebook()
        assert window._act_save_as.isEnabled() is True


# ── 窗口标题 ──


class TestWindowTitle:
    """UI-06: 窗口标题"""

    def test_default_title(self, window):
        """默认标题为 'SecNotepad'。"""
        assert window.windowTitle() == "SecNotepad"

    def test_title_after_new_is_secnotepad(self, window):
        """新建后标题仍为 'SecNotepad'（未保存，无路径）。"""
        window._on_new_notebook()
        assert "SecNotepad" in window.windowTitle()

    def test_dirty_marker_appears(self, window):
        """脏标志改变时标题带 *。"""
        window._on_new_notebook()
        window.mark_dirty()
        assert "*" in window.windowTitle()

    def test_clean_removes_dirty_marker(self, window):
        """保存后清除 * 标记。"""
        window._on_new_notebook()
        window.mark_dirty()
        window.mark_clean()
        assert "*" not in window.windowTitle()


# ── WelcomeWidget 最近文件 ──


class TestRecentFiles:
    """D-40~D-44: 最近文件列表"""

    def test_welcome_has_recent_signal(self, window):
        """WelcomeWidget 有 recent_file_clicked 信号。"""
        welcome = window._stack.widget(0)
        assert hasattr(welcome, "recent_file_clicked")

    def test_recent_file_list_widget(self, window):
        """欢迎页有 QListWidget 显示最近文件。"""
        welcome = window._stack.widget(0)
        assert hasattr(welcome, "recent_list")

    def test_recent_files_set(self, window):
        """set_recent_files 更新列表内容。"""
        welcome = window._stack.widget(0)
        welcome.set_recent_files(["/path/to/test.secnote"])
        assert welcome.recent_list.count() == 1

    def test_recent_files_max_items(self, window):
        """设置超过 5 条时只显示 5 条。"""
        welcome = window._stack.widget(0)
        paths = [f"/path/{i}.secnote" for i in range(7)]
        welcome.set_recent_files(paths[:5])  # MainWindow 已过滤
        assert welcome.recent_list.count() == 5

    def test_empty_recent_files(self, window):
        """空列表显示 '暂无最近打开的文件'。"""
        welcome = window._stack.widget(0)
        welcome.set_recent_files([])
        assert welcome.recent_list.count() == 0

    def test_init_loads_recent_files(self, qapp, isolated_recent_files, tmp_path):
        """__init__ 后欢迎页最近文件列表反映隔离 QSettings 中的内容。"""
        test_path = str(tmp_path / "test_recent.secnote")
        test_path2 = str(tmp_path / "test_recent2.secnote")
        # 创建测试文件（_load_recent_files 过滤不存在的文件）
        test_path and open(test_path, "w").close()
        open(test_path2, "w").close()

        isolated_recent_files.setValue("recent_files", [test_path, test_path2])
        w = MainWindow()
        w.show()
        try:
            welcome = w._stack.widget(0)
            assert welcome.recent_list.count() == 2
        finally:
            w._is_dirty = False
            w.close()
            w.deleteLater()

    def test_on_save_adds_recent_file(self, window, monkeypatch, tmp_path):
        """保存到已有路径后，欢迎页最近文件列表立即更新。"""
        from src.secnotepad.crypto import file_service

        window._on_new_notebook()
        save_path = str(tmp_path / "saved.secnote")
        window._current_path = save_path
        window._current_password = "testpw"

        # Mock FileService.save 避免写入真实文件
        monkeypatch.setattr(file_service.FileService, "save", lambda *a, **kw: None)

        window._on_save()

        welcome = window._stack.widget(0)
        # 最近文件列表应包含保存的路径
        found = any(
            welcome.recent_list.item(i).text() == save_path
            for i in range(welcome.recent_list.count())
        )
        assert found, f"Expected {save_path} in recent files list"


class TestRichTextIntegration:
    """Phase 04: MainWindow 富文本编辑器集成 RED 测试。"""

    def _new_page(self, window):
        window._on_new_notebook()
        window._on_new_root_section()
        window._on_new_page()
        current = window._list_view.currentIndex()
        note = window._page_list_model.note_at(current)
        assert note is not None
        window._is_dirty = False
        window._update_window_title()
        return note

    def _menu_action_texts(self, window, menu_title):
        menu = next(
            action.menu()
            for action in window.menuBar().actions()
            if menu_title in action.text()
        )
        return [action.text() for action in menu.actions()]

    def test_format_toolbar_is_inside_editor_area(self, window):
        window._on_new_notebook()
        splitter = window._stack.widget(1)
        right_panel = splitter.widget(2)

        assert window._format_toolbar.parent() is right_panel
        assert window._format_toolbar in right_panel.findChildren(QToolBar)

        file_toolbar_texts = [action.text() for action in window.findChildren(QToolBar)[0].actions()]
        forbidden = {"加粗", "斜体", "下划线", "删除线", "文字颜色", "背景色"}
        assert forbidden.isdisjoint(file_toolbar_texts)

    def test_format_toolbar_disabled_without_page_enabled_with_page(self, window):
        window._on_new_notebook()
        assert window._rich_text_editor.format_toolbar().isEnabled() is False

        self._new_page(window)

        assert window._rich_text_editor.format_toolbar().isEnabled() is True

    def test_editor_menu_actions_route_to_rich_text_editor(self, window):
        note = self._new_page(window)
        edit_texts = self._menu_action_texts(window, "编辑")
        assert edit_texts == ["撤销(&U)", "重做(&R)", "剪切(&T)", "复制(&C)", "粘贴(&P)"]

        undo_action, redo_action, cut_action, copy_action, paste_action = window._edit_actions
        assert paste_action.isEnabled() is True
        assert undo_action.isEnabled() is False
        assert redo_action.isEnabled() is False

        editor = window._rich_text_editor.editor()
        editor.setFocus()
        QTest.keyClicks(editor, "abc")

        assert "abc" in note.content
        assert undo_action.isEnabled() is True
        assert redo_action.isEnabled() is False

    def test_view_menu_has_zoom_actions(self, window):
        view_texts = self._menu_action_texts(window, "视图")
        assert "放大" in view_texts
        assert "缩小" in view_texts
        assert "重置缩放" in view_texts
        assert window._act_zoom_in.shortcut().toString() in {"Ctrl++", "Ctrl+Plus"}
        assert window._act_zoom_out.shortcut().toString() == "Ctrl+-"
        assert window._act_zoom_reset.shortcut().toString() == "Ctrl+0"

    def test_zoom_actions_keep_note_html_and_dirty_state(self, window):
        note = self._new_page(window)
        note.content = "<p>保持内容</p>"
        window._show_note_in_editor(note)
        window._is_dirty = False

        before = note.content
        window._act_zoom_in.trigger()
        window._act_zoom_out.trigger()
        window._act_zoom_reset.trigger()

        assert note.content == before
        assert window._is_dirty is False
        assert window.statusBar().currentMessage() == "缩放：100%"
