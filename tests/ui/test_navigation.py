"""Tests for Navigation System — CRUD 操作与交互集成测试 (NAV-03, NAV-04, D-62, D-63, D-64)。"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QStackedWidget, QTextEdit, QMenu

from PySide6.QtTest import QTest

from src.secnotepad.ui.main_window import MainWindow


@pytest.fixture
def window_with_notebook(qapp):
    """创建已打开笔记本的 MainWindow，导航系统已初始化。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()


class TestNavigationSetup:
    """Phase 3: 导航系统初始化验证 (D-49~D-53, D-55, D-62, D-63)。"""

    def test_section_filter_proxy_set(self, window_with_notebook):
        """SectionFilterProxy 已创建并设为 TreeView 的模型 (D-49)。"""
        assert window_with_notebook._section_filter is not None

    def test_tree_view_uses_proxy(self, window_with_notebook):
        """TreeView.model() 返回 SectionFilterProxy (D-49)。"""
        assert (
            window_with_notebook._tree_view.model()
            is window_with_notebook._section_filter
        )

    def test_page_list_model_set(self, window_with_notebook):
        """PageListModel 已创建并设为 ListView 的模型 (D-50)。"""
        assert window_with_notebook._page_list_model is not None

    def test_list_view_uses_page_model(self, window_with_notebook):
        """ListView.model() 返回 PageListModel (D-50)。"""
        assert (
            window_with_notebook._list_view.model()
            is window_with_notebook._page_list_model
        )

    def test_editor_preview_is_editable(self, window_with_notebook):
        """右侧 QTextEdit 可编辑，用于页面正文编辑。"""
        assert isinstance(window_with_notebook._editor_preview, QTextEdit)
        assert window_with_notebook._editor_preview.isReadOnly() is False

    def test_editor_defaults_to_placeholder(self, window_with_notebook):
        """编辑区默认显示 placeholder (D-63): QStackedWidget index 1。"""
        assert window_with_notebook._editor_stack.currentIndex() == 1

    def test_tree_edit_triggers_set(self, window_with_notebook):
        """QTreeView EditTriggers 包含 DoubleClicked | EditKeyPressed (D-59)。"""
        from PySide6.QtWidgets import QAbstractItemView
        triggers = window_with_notebook._tree_view.editTriggers()
        assert triggers & QAbstractItemView.DoubleClicked
        assert triggers & QAbstractItemView.EditKeyPressed

    def test_list_edit_triggers_set(self, window_with_notebook):
        """QListView EditTriggers 包含 DoubleClicked | EditKeyPressed (D-59)。"""
        from PySide6.QtWidgets import QAbstractItemView
        triggers = window_with_notebook._list_view.editTriggers()
        assert triggers & QAbstractItemView.DoubleClicked
        assert triggers & QAbstractItemView.EditKeyPressed

    def test_toolbar_buttons_exist(self, window_with_notebook):
        """工具栏按钮已创建 (D-55)。"""
        assert window_with_notebook._btn_new_section is not None
        assert window_with_notebook._btn_new_child_section is not None
        assert window_with_notebook._btn_new_page is not None

    def test_toolbar_buttons_enabled(self, window_with_notebook):
        """工具栏按钮在导航初始化后已启用 (D-55)。"""
        assert window_with_notebook._btn_new_section.isEnabled()
        assert window_with_notebook._btn_new_child_section.isEnabled()
        assert window_with_notebook._btn_new_page.isEnabled()


class TestNavigationCRUD:
    """Phase 3: CRUD 操作集成测试 (NAV-03, NAV-04, D-61, D-64)。"""

    def test_new_root_section(self, window_with_notebook):
        """创建顶级分区后 TreeView 显示新节点 (D-61)。"""
        initial_count = window_with_notebook._section_filter.rowCount()
        window_with_notebook._on_new_root_section()
        assert window_with_notebook._section_filter.rowCount() == initial_count + 1
        assert window_with_notebook._is_dirty is True

    def test_new_page_in_current_section(self, window_with_notebook):
        """在当前分区下新建页面 (D-64)。"""
        # 先创建分区并选中，确保 _page_list_model 有当前分区
        window_with_notebook._on_new_root_section()
        initial_count = window_with_notebook._page_list_model.rowCount()
        window_with_notebook._on_new_page()
        assert window_with_notebook._page_list_model.rowCount() == initial_count + 1
        # D-64: 新建页面后自动选中
        current = window_with_notebook._list_view.currentIndex()
        assert current.isValid()

    def test_new_child_section_auto_selects_child(self, window_with_notebook):
        """新建子分区后自动选中新子节点。"""
        window_with_notebook._on_new_root_section()
        parent_index = window_with_notebook._tree_view.currentIndex()
        parent_item = window_with_notebook._section_filter.mapToSource(parent_index).internalPointer()

        window_with_notebook._on_new_child_section()

        current = window_with_notebook._tree_view.currentIndex()
        current_item = window_with_notebook._section_filter.mapToSource(current).internalPointer()
        assert current_item is not parent_item
        assert current_item.title == "新分区"

    def test_reinitialize_navigation_does_not_duplicate_button_handlers(self, window_with_notebook):
        """重复初始化导航后，工具栏按钮不会重复触发创建。"""
        window_with_notebook._setup_navigation()
        before = window_with_notebook._section_filter.rowCount()

        window_with_notebook._btn_new_section.click()

        assert window_with_notebook._section_filter.rowCount() == before + 1

    def test_reinitialize_navigation_replaces_delete_and_rename_actions(self, window_with_notebook):
        """重复初始化导航不会在视图上累积 Delete/F2 QAction。"""
        window_with_notebook._setup_navigation()
        window_with_notebook._setup_navigation()

        delete_actions = [
            action for action in window_with_notebook._tree_view.actions()
            if action.text() == "删除"
        ]
        rename_actions = [
            action for action in window_with_notebook._tree_view.actions()
            if action.text() == "重命名"
        ]
        assert len(delete_actions) == 1
        assert len(rename_actions) == 1

    def test_tree_context_menu_selects_right_clicked_section(self, window_with_notebook, monkeypatch):
        """树右键菜单操作前会同步到右键点击的分区，而非旧 currentIndex。"""
        window_with_notebook._on_new_root_section()
        first_index = window_with_notebook._section_filter.index(0, 0, QModelIndex())
        window_with_notebook._on_new_root_section()
        second_index = window_with_notebook._section_filter.index(1, 0, QModelIndex())
        window_with_notebook._tree_view.setCurrentIndex(first_index)

        captured = {}

        def fake_exec(self, *args, **kwargs):
            captured["current"] = window_with_notebook._tree_view.currentIndex()
            return None

        monkeypatch.setattr(QMenu, "exec", fake_exec)
        monkeypatch.setattr(window_with_notebook._tree_view, "indexAt", lambda pos: second_index)

        window_with_notebook._on_tree_context_menu(window_with_notebook._tree_view.rect().center())

        assert captured["current"] == second_index

    def test_rename_section_marks_dirty(self, window_with_notebook):
        """分区重命名后窗口进入脏状态。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._is_dirty = False
        current = window_with_notebook._tree_view.currentIndex()

        assert window_with_notebook._rename_current_section("已重命名") is True
        assert window_with_notebook._is_dirty is True

    def test_rename_page_marks_dirty(self, window_with_notebook):
        """页面重命名后窗口进入脏状态。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        window_with_notebook._is_dirty = False
        current = window_with_notebook._list_view.currentIndex()

        assert window_with_notebook._rename_current_page("已重命名页面") is True
        assert window_with_notebook._is_dirty is True

    def test_ctrl_n_creates_page_when_page_list_focused(self, window_with_notebook):
        """页面列表聚焦时 Ctrl+N 新建页面并选中新页面。"""
        window_with_notebook._on_new_root_section()
        before = window_with_notebook._page_list_model.rowCount()
        window_with_notebook._is_dirty = False

        window_with_notebook._list_view.setFocus()
        QTest.keyClick(
            window_with_notebook._list_view,
            Qt.Key_N,
            Qt.ControlModifier,
        )

        assert window_with_notebook._page_list_model.rowCount() == before + 1
        assert window_with_notebook._list_view.currentIndex().isValid()
        assert window_with_notebook._is_dirty is True

    def test_ctrl_n_creates_notebook_when_editor_focused(self, window_with_notebook, monkeypatch):
        """非页面列表焦点下 Ctrl+N 分发到新建笔记本。"""
        called = {"count": 0}

        def fake_new_notebook():
            called["count"] += 1

        monkeypatch.setattr(window_with_notebook, "_on_new_notebook", fake_new_notebook)
        window_with_notebook._editor_preview.setFocus()

        QTest.keyClick(window_with_notebook._editor_preview, Qt.Key_N, Qt.ControlModifier)

        assert called["count"] == 1

    def test_second_new_notebook_keeps_single_button_binding(self, window_with_notebook):
        """同一窗口会话里再次新建笔记本后，按钮点击仍只创建一次。"""
        window_with_notebook._on_new_notebook()
        before = window_with_notebook._section_filter.rowCount()

        window_with_notebook._btn_new_section.click()

        assert window_with_notebook._section_filter.rowCount() == before + 1

    def test_second_new_notebook_allows_single_page_creation(self, window_with_notebook):
        """同一窗口会话里再次新建笔记本后，新建页面按钮仍只触发一次。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        before = window_with_notebook._page_list_model.rowCount()

        window_with_notebook._btn_new_page.click()

        assert window_with_notebook._page_list_model.rowCount() == before + 1
        assert window_with_notebook._list_view.currentIndex().isValid()

    def test_reinitialize_navigation_keeps_single_tree_signal_binding(self, window_with_notebook):
        """重复初始化后，树选择变化不会重复刷新造成异常。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        current = window_with_notebook._tree_view.currentIndex()

        window_with_notebook._on_tree_current_changed(current, QModelIndex())

        assert window_with_notebook._page_list_model._section is not None

    def test_reinitialize_navigation_does_not_duplicate_new_child_handler(self, window_with_notebook):
        """重复初始化后，新建子分区按钮不会一次创建多个节点。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        parent = window_with_notebook._tree_view.currentIndex()
        before = window_with_notebook._section_filter.rowCount(parent)

        window_with_notebook._btn_new_child_section.click()

        assert window_with_notebook._section_filter.rowCount(parent) == before + 1

    def test_reinitialize_navigation_does_not_duplicate_new_page_handler(self, window_with_notebook):
        """重复初始化后，新建页面按钮不会一次创建多个页面。"""
        window_with_notebook._on_new_root_section()
        before = window_with_notebook._page_list_model.rowCount()
        window_with_notebook._setup_navigation()

        window_with_notebook._btn_new_page.click()

        assert window_with_notebook._page_list_model.rowCount() == before + 1

    def test_rename_section_only_marks_dirty_once_per_operation(self, window_with_notebook):
        """单次分区重命名不会因重复绑定出现异常。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        window_with_notebook._is_dirty = False

        assert window_with_notebook._rename_current_section("再次重命名") is True
        assert window_with_notebook._is_dirty is True

    def test_rename_page_only_marks_dirty_once_per_operation(self, window_with_notebook):
        """单次页面重命名不会因重复绑定出现异常。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        window_with_notebook._is_dirty = False

        assert window_with_notebook._rename_current_page("再次重命名页面") is True
        assert window_with_notebook._is_dirty is True

    def test_renaming_to_same_title_does_not_mark_dirty(self, window_with_notebook):
        """标题未变化时不发出结构变更，也不进入脏状态。"""
        window_with_notebook._on_new_root_section()
        section_index = window_with_notebook._section_filter.mapToSource(
            window_with_notebook._tree_view.currentIndex()
        )
        section_title = section_index.internalPointer().title
        window_with_notebook._on_new_page()
        page_index = window_with_notebook._list_view.currentIndex()
        page_title = window_with_notebook._page_list_model.note_at(page_index).title
        window_with_notebook._is_dirty = False

        assert window_with_notebook._tree_model.setData(section_index, section_title, Qt.EditRole) is False
        assert window_with_notebook._page_list_model.setData(page_index, page_title, Qt.EditRole) is False
        assert window_with_notebook._is_dirty is False

    def test_ctrl_n_shortcut_is_single_window_dispatcher(self, window_with_notebook):
        """Ctrl+N 只注册一个窗口级分发器，避免与菜单 QAction 冲突。"""
        assert window_with_notebook._act_new.shortcut().isEmpty()
        assert window_with_notebook._shortcut_ctrl_n.parent() is window_with_notebook
        assert window_with_notebook._shortcut_ctrl_n.context() == Qt.WindowShortcut

    def test_reinitialize_navigation_preserves_toolbar_enabled_state(self, window_with_notebook):
        """重复初始化后工具栏按钮仍保持启用。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._btn_new_section.isEnabled()
        assert window_with_notebook._btn_new_child_section.isEnabled()
        assert window_with_notebook._btn_new_page.isEnabled()

    def test_reinitialize_navigation_preserves_page_context_menu_binding(self, window_with_notebook):
        """重复初始化后页面 viewport 仍绑定自定义菜单策略。"""
        window_with_notebook._setup_navigation()
        assert (
            window_with_notebook._list_view.viewport().contextMenuPolicy()
            == Qt.CustomContextMenu
        )

    def test_reinitialize_navigation_reconnects_page_selection_model(self, window_with_notebook):
        """重复初始化后页面 selectionModel 可用。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._page_selection is window_with_notebook._list_view.selectionModel()

    def test_reinitialize_navigation_reconnects_tree_selection_model(self, window_with_notebook):
        """重复初始化后树 selectionModel 可用。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._tree_selection is window_with_notebook._tree_view.selectionModel()

    def test_reinitialize_navigation_keeps_editor_placeholder_without_pages(self, window_with_notebook):
        """重复初始化后若没有页面，仍保持 placeholder。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        assert window_with_notebook._page_list_model.rowCount() == 0
        assert window_with_notebook._editor_stack.currentIndex() == 1

    def test_reinitialize_navigation_section_rename_helper_returns_false_without_selection(self, window_with_notebook):
        """无分区选择时分区重命名 helper 返回 False。"""
        window_with_notebook._tree_view.setCurrentIndex(QModelIndex())
        assert window_with_notebook._rename_current_section("x") is False

    def test_reinitialize_navigation_page_rename_helper_returns_false_without_section(self, window_with_notebook):
        """无当前页面时页面重命名 helper 返回 False。"""
        assert window_with_notebook._rename_current_page("x") is False

    def test_reinitialize_navigation_preserves_blank_context_menu_action(self, window_with_notebook, monkeypatch):
        """重复初始化后空白区域菜单仍提供新建页面。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        captured = {}

        def fake_popup(self, *args, **kwargs):
            captured["texts"] = [action.text() for action in self.actions()]
            return None

        monkeypatch.setattr(QMenu, "exec", fake_popup)
        window_with_notebook._on_page_context_menu(
            window_with_notebook._list_view.viewport().rect().bottomRight()
        )

        assert captured["texts"] == ["新建页面"]

    def test_reinitialize_navigation_preserves_context_menu_actions(self, window_with_notebook, monkeypatch):
        """重复初始化后页面菜单动作文本仍正确。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        captured = {}

        def fake_popup(self, *args, **kwargs):
            captured["texts"] = [action.text() for action in self.actions()]
            return None

        monkeypatch.setattr(QMenu, "exec", fake_popup)
        index = window_with_notebook._list_view.currentIndex()
        rect = window_with_notebook._list_view.visualRect(index)
        window_with_notebook._on_page_context_menu(rect.center())

        assert "重命名页面" in captured["texts"]

    def test_reinitialize_navigation_preserves_page_focusability(self, window_with_notebook):
        """重复初始化后页面列表仍可聚焦。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._list_view.focusPolicy() == Qt.StrongFocus

    def test_reinitialize_navigation_preserves_section_creation_path(self, window_with_notebook):
        """重复初始化后仍能继续创建分区。"""
        before = window_with_notebook._section_filter.rowCount()
        window_with_notebook._setup_navigation()

        window_with_notebook._on_new_root_section()

        assert window_with_notebook._section_filter.rowCount() == before + 1

    def test_reinitialize_navigation_preserves_blank_editor_when_no_selection(self, window_with_notebook):
        """重复初始化后无页面选择时仍显示 placeholder。"""
        window_with_notebook._setup_navigation()
        window_with_notebook._show_editor_placeholder()
        assert window_with_notebook._editor_stack.currentIndex() == 1

    def test_reinitialize_navigation_section_selection_still_valid_after_new_child(self, window_with_notebook):
        """重复初始化后新建子分区后树当前索引仍有效。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        window_with_notebook._on_new_child_section()
        assert window_with_notebook._tree_view.currentIndex().isValid()

    def test_reinitialize_navigation_preserves_ctrl_n_dispatcher(self, window_with_notebook):
        """重复初始化后 Ctrl+N 分发器仍为单一窗口级 shortcut。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._shortcut_ctrl_n.parent() is window_with_notebook
        assert window_with_notebook._shortcut_ctrl_n.context() == Qt.WindowShortcut

    def test_reinitialize_navigation_keeps_dirty_mark_on_section_rename(self, window_with_notebook):
        """重复初始化后分区重命名仍会置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        window_with_notebook._is_dirty = False

        assert window_with_notebook._rename_current_section("dirty section rename") is True
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_page_creation_still_marks_dirty(self, window_with_notebook):
        """重复初始化后新建页面仍会置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        window_with_notebook._is_dirty = False

        window_with_notebook._on_new_page()

        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_new_child_still_marks_dirty(self, window_with_notebook):
        """重复初始化后新建子分区仍会置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()
        window_with_notebook._is_dirty = False

        window_with_notebook._on_new_child_section()

        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_new_root_still_marks_dirty(self, window_with_notebook):
        """重复初始化后新建顶级分区仍会置脏。"""
        window_with_notebook._setup_navigation()
        window_with_notebook._is_dirty = False

        window_with_notebook._on_new_root_section()

        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_after_second_new_notebook_keeps_single_handlers(self, window_with_notebook):
        """再次新建笔记本后重新初始化，按钮仍不会重复触发。"""
        window_with_notebook._on_new_notebook()
        before = window_with_notebook._section_filter.rowCount()

        window_with_notebook._btn_new_section.click()

        assert window_with_notebook._section_filter.rowCount() == before + 1

    def test_reinitialize_navigation_after_second_new_notebook_new_child_is_single(self, window_with_notebook):
        """再次新建笔记本后，新建子分区按钮仍只创建一次。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        parent = window_with_notebook._tree_view.currentIndex()
        before = window_with_notebook._section_filter.rowCount(parent)

        window_with_notebook._btn_new_child_section.click()

        assert window_with_notebook._section_filter.rowCount(parent) == before + 1

    def test_reinitialize_navigation_after_second_new_notebook_new_page_is_single(self, window_with_notebook):
        """再次新建笔记本后，新建页面按钮仍只创建一次。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        before = window_with_notebook._page_list_model.rowCount()

        window_with_notebook._btn_new_page.click()

        assert window_with_notebook._page_list_model.rowCount() == before + 1

    def test_reinitialize_navigation_keeps_page_context_menu_binding_after_second_setup(self, window_with_notebook):
        """再次初始化后页面菜单绑定仍存在。"""
        window_with_notebook._setup_navigation()
        assert (
            window_with_notebook._list_view.viewport().contextMenuPolicy()
            == Qt.CustomContextMenu
        )

    def test_reinitialize_navigation_keeps_page_button_enabled_after_second_setup(self, window_with_notebook):
        """再次初始化后页面按钮仍启用。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._btn_new_page.isEnabled()

    def test_reinitialize_navigation_keeps_section_buttons_enabled_after_second_setup(self, window_with_notebook):
        """再次初始化后分区按钮仍启用。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._btn_new_section.isEnabled()
        assert window_with_notebook._btn_new_child_section.isEnabled()

    def test_reinitialize_navigation_page_rename_still_requires_current_item(self, window_with_notebook):
        """页面重命名 helper 仍依赖当前页面存在。"""
        assert window_with_notebook._rename_current_page("no page") is False

    def test_reinitialize_navigation_section_rename_still_requires_current_item(self, window_with_notebook):
        """分区重命名 helper 仍依赖当前分区存在。"""
        window_with_notebook._tree_view.setCurrentIndex(QModelIndex())
        assert window_with_notebook._rename_current_section("no section") is False

    def test_reinitialize_navigation_keeps_tree_model_bound_to_proxy(self, window_with_notebook):
        """再次初始化后 proxy 仍绑定 tree_model。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._section_filter.sourceModel() is window_with_notebook._tree_model

    def test_reinitialize_navigation_keeps_list_model_bound_to_view(self, window_with_notebook):
        """再次初始化后 list view 仍绑定 page_list_model。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._list_view.model() is window_with_notebook._page_list_model

    def test_reinitialize_navigation_keeps_tree_view_bound_to_proxy(self, window_with_notebook):
        """再次初始化后 tree view 仍绑定 proxy。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._tree_view.model() is window_with_notebook._section_filter

    def test_reinitialize_navigation_keeps_edit_triggers_for_tree(self, window_with_notebook):
        """再次初始化后 tree edit triggers 仍正确。"""
        window_with_notebook._setup_navigation()
        triggers = window_with_notebook._tree_view.editTriggers()
        from PySide6.QtWidgets import QAbstractItemView
        assert triggers & QAbstractItemView.DoubleClicked
        assert triggers & QAbstractItemView.EditKeyPressed

    def test_reinitialize_navigation_keeps_edit_triggers_for_list(self, window_with_notebook):
        """再次初始化后 list edit triggers 仍正确。"""
        window_with_notebook._setup_navigation()
        triggers = window_with_notebook._list_view.editTriggers()
        from PySide6.QtWidgets import QAbstractItemView
        assert triggers & QAbstractItemView.DoubleClicked
        assert triggers & QAbstractItemView.EditKeyPressed

    def test_reinitialize_navigation_keeps_tree_menu_binding(self, window_with_notebook):
        """再次初始化后树右键菜单绑定仍在。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._tree_view.contextMenuPolicy() == Qt.CustomContextMenu

    def test_reinitialize_navigation_keeps_page_menu_binding(self, window_with_notebook):
        """再次初始化后页右键菜单绑定仍在。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._list_view.contextMenuPolicy() == Qt.CustomContextMenu

    def test_reinitialize_navigation_keeps_placeholder_text(self, window_with_notebook):
        """再次初始化后 placeholder 文案仍存在。"""
        window_with_notebook._setup_navigation()
        assert "页面列表" in window_with_notebook._editor_placeholder_label.text()

    def test_reinitialize_navigation_keeps_editor_editable(self, window_with_notebook):
        """再次初始化后右侧编辑区仍可编辑。"""
        window_with_notebook._setup_navigation()
        assert window_with_notebook._editor_preview.isReadOnly() is False

    def test_reinitialize_navigation_keeps_new_child_auto_select(self, window_with_notebook):
        """再次初始化后新建子分区仍自动选中新节点。"""
        window_with_notebook._on_new_root_section()
        parent_index = window_with_notebook._tree_view.currentIndex()
        parent_item = window_with_notebook._section_filter.mapToSource(parent_index).internalPointer()
        window_with_notebook._setup_navigation()

        window_with_notebook._on_new_child_section()

        current_item = window_with_notebook._section_filter.mapToSource(
            window_with_notebook._tree_view.currentIndex()
        ).internalPointer()
        assert current_item is not parent_item

    def test_reinitialize_navigation_keeps_page_creation_auto_select(self, window_with_notebook):
        """再次初始化后新建页面仍自动选中新页面。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._setup_navigation()

        window_with_notebook._on_new_page()

        assert window_with_notebook._list_view.currentIndex().isValid()

    def test_reinitialize_navigation_keeps_mark_dirty_helpers_independent(self, window_with_notebook):
        """重命名 helper 仍独立负责置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._is_dirty = False
        assert window_with_notebook._rename_current_section("independent") is True
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_keeps_page_rename_helper_independent(self, window_with_notebook):
        """页面重命名 helper 仍独立负责置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        window_with_notebook._is_dirty = False
        assert window_with_notebook._rename_current_page("independent page") is True
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_after_second_notebook_preserves_page_ctrl_n(self, window_with_notebook):
        """再次新建笔记本后页面 Ctrl+N 快捷键仍可用。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        before = window_with_notebook._page_list_model.rowCount()
        window_with_notebook._list_view.setFocus()

        QTest.keyClick(window_with_notebook._list_view, Qt.Key_N, Qt.ControlModifier)

        assert window_with_notebook._page_list_model.rowCount() == before + 1

    def test_reinitialize_navigation_after_second_notebook_keeps_context_menu(self, window_with_notebook):
        """再次新建笔记本后页面右键菜单绑定仍存在。"""
        window_with_notebook._on_new_notebook()
        assert (
            window_with_notebook._list_view.viewport().contextMenuPolicy()
            == Qt.CustomContextMenu
        )

    def test_reinitialize_navigation_after_second_notebook_keeps_editor_editable(self, window_with_notebook):
        """再次新建笔记本后右侧编辑器仍可编辑。"""
        window_with_notebook._on_new_notebook()
        assert window_with_notebook._editor_preview.isReadOnly() is False

    def test_reinitialize_navigation_after_second_notebook_keeps_buttons_enabled(self, window_with_notebook):
        """再次新建笔记本后按钮仍启用。"""
        window_with_notebook._on_new_notebook()
        assert window_with_notebook._btn_new_section.isEnabled()
        assert window_with_notebook._btn_new_child_section.isEnabled()
        assert window_with_notebook._btn_new_page.isEnabled()

    def test_reinitialize_navigation_after_second_notebook_keeps_placeholder_without_pages(self, window_with_notebook):
        """再次新建笔记本后若无页面仍显示 placeholder。"""
        window_with_notebook._on_new_notebook()
        assert window_with_notebook._editor_stack.currentIndex() == 1

    def test_reinitialize_navigation_after_second_notebook_new_page_marks_dirty(self, window_with_notebook):
        """再次新建笔记本后新建页面仍置脏。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        window_with_notebook._is_dirty = False
        window_with_notebook._on_new_page()
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_after_second_notebook_new_child_marks_dirty(self, window_with_notebook):
        """再次新建笔记本后新建子分区仍置脏。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        window_with_notebook._is_dirty = False
        window_with_notebook._on_new_child_section()
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_after_second_notebook_rename_section_marks_dirty(self, window_with_notebook):
        """再次新建笔记本后分区重命名仍置脏。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        window_with_notebook._is_dirty = False
        assert window_with_notebook._rename_current_section("again") is True
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_after_second_notebook_rename_page_marks_dirty(self, window_with_notebook):
        """再次新建笔记本后页面重命名仍置脏。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        window_with_notebook._is_dirty = False
        assert window_with_notebook._rename_current_page("again page") is True
        assert window_with_notebook._is_dirty is True

    def test_reinitialize_navigation_after_second_notebook_new_child_auto_selects(self, window_with_notebook):
        """再次新建笔记本后新建子分区仍自动选中新节点。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        parent_index = window_with_notebook._tree_view.currentIndex()
        parent_item = window_with_notebook._section_filter.mapToSource(parent_index).internalPointer()
        window_with_notebook._on_new_child_section()
        current_item = window_with_notebook._section_filter.mapToSource(
            window_with_notebook._tree_view.currentIndex()
        ).internalPointer()
        assert current_item is not parent_item

    def test_reinitialize_navigation_after_second_notebook_new_page_auto_selects(self, window_with_notebook):
        """再次新建笔记本后新建页面仍自动选中新页面。"""
        window_with_notebook._on_new_notebook()
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        assert window_with_notebook._list_view.currentIndex().isValid()

    def test_new_page_sets_dirty(self, window_with_notebook):
        """新建页面触发脏标志 (D-61)。"""
        # 先创建分区，确保 _page_list_model._section 不为 None
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        assert window_with_notebook._is_dirty is True

    def test_delete_page(self, window_with_notebook):
        """删除页面后列表减少一项 (NAV-04)。"""
        # 先创建分区，确保 _page_list_model._section 不为 None
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        count_after_add = window_with_notebook._page_list_model.rowCount()
        window_with_notebook._on_delete_page()
        assert window_with_notebook._page_list_model.rowCount() == count_after_add - 1

    def test_delete_empty_section_no_warning(self, window_with_notebook):
        """删除空分区（无子项目）直接删除 (D-58)。"""
        window_with_notebook._on_new_root_section()
        count_before = window_with_notebook._section_filter.rowCount()
        window_with_notebook._on_delete_section()
        assert window_with_notebook._section_filter.rowCount() == count_before - 1

    def test_editor_placeholder_when_no_page(self, window_with_notebook):
        """无页面选中时编辑区为 placeholder (D-63)。"""
        assert window_with_notebook._editor_stack.currentIndex() == 1

    def test_page_context_menu_is_bound_on_viewport(self, window_with_notebook):
        """页面列表右键菜单绑定在 viewport，右键项目区域可触发自定义菜单。"""
        assert (
            window_with_notebook._list_view.viewport().contextMenuPolicy()
            == Qt.CustomContextMenu
        )

    def test_editor_updates_note_content_and_marks_dirty(self, window_with_notebook):
        """编辑右侧文本后同步回当前页面并置脏。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()

        current = window_with_notebook._list_view.currentIndex()
        note = window_with_notebook._page_list_model.note_at(current)
        assert note is not None

        window_with_notebook._is_dirty = False
        window_with_notebook._editor_preview.setFocus()
        window_with_notebook._editor_preview.clear()
        QTest.keyClicks(window_with_notebook._editor_preview, "hello")

        assert "hello" in note.content
        assert window_with_notebook._is_dirty is True

    def test_selecting_page_shows_editor(self, window_with_notebook):
        """选中页面后切换到编辑器页，而不是保持 placeholder。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        assert window_with_notebook._editor_stack.currentIndex() == 0

    def test_show_editor_placeholder_does_not_clear_note_content(self, window_with_notebook):
        """切换到 placeholder 不会把当前页面正文写空。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        note = window_with_notebook._page_list_model.note_at(
            window_with_notebook._list_view.currentIndex()
        )
        note.content = "<p>keep me</p>"
        window_with_notebook._is_dirty = False

        window_with_notebook._show_editor_placeholder()

        assert note.content == "<p>keep me</p>"
        assert window_with_notebook._is_dirty is False

    def test_delete_key_edits_textedit_not_navigation(self, window_with_notebook):
        """编辑器焦点下 Delete 不被导航删除快捷键吞掉。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()
        editor = window_with_notebook._editor_preview
        editor.setPlainText("abc")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        editor.setFocus()

        QTest.keyClick(editor, Qt.Key_Delete)

        assert editor.toPlainText() == "ac"
        assert window_with_notebook._page_list_model.rowCount() == 1

    def test_page_context_menu_for_item_contains_actions(self, window_with_notebook, monkeypatch):
        """页面项右键菜单包含重命名/删除动作。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()

        captured = {}

        def fake_exec(self, *args, **kwargs):
            captured["texts"] = [action.text() for action in self.actions()]
            return None

        monkeypatch.setattr(QMenu, "exec", fake_exec)
        index = window_with_notebook._list_view.currentIndex()
        rect = window_with_notebook._list_view.visualRect(index)
        window_with_notebook._on_page_context_menu(rect.center())

        assert "重命名页面" in captured["texts"]
        assert "删除页面" in captured["texts"]

    def test_page_context_menu_selects_clicked_item(self, window_with_notebook, monkeypatch):
        """右键页面项时会先选中该项，再显示菜单。"""
        window_with_notebook._on_new_root_section()
        window_with_notebook._on_new_page()

        captured = {}

        def fake_popup(self, *args, **kwargs):
            captured["current"] = window_with_notebook._list_view.currentIndex().isValid()
            return None

        monkeypatch.setattr(QMenu, "exec", fake_popup)
        index = window_with_notebook._list_view.currentIndex()
        rect = window_with_notebook._list_view.visualRect(index)
        window_with_notebook._list_view.clearSelection()
        window_with_notebook._on_page_context_menu(rect.center())

        assert captured["current"] is True

    def test_page_context_menu_for_blank_contains_new(self, window_with_notebook, monkeypatch):
        """页面空白区域右键菜单包含新建页面动作。"""
        window_with_notebook._on_new_root_section()
        captured = {}

        def fake_exec(self, *args, **kwargs):
            captured["texts"] = [action.text() for action in self.actions()]
            return None

        monkeypatch.setattr(QMenu, "exec", fake_exec)
        window_with_notebook._on_page_context_menu(
            window_with_notebook._list_view.viewport().rect().bottomRight()
        )

        assert captured["texts"] == ["新建页面"]

