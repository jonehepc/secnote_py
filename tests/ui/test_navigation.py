"""Tests for Navigation System — CRUD 操作与交互集成测试 (NAV-03, NAV-04, D-62, D-63, D-64)。"""

import pytest
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import QStackedWidget, QTextEdit

from src.secnotepad.ui.main_window import MainWindow


@pytest.fixture
def window_with_notebook(qapp):
    """创建已打开笔记本的 MainWindow，导航系统已初始化。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    yield w
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

    def test_editor_preview_is_readonly(self, window_with_notebook):
        """Editor QTextEdit 是只读的 (D-62)。"""
        assert isinstance(window_with_notebook._editor_preview, QTextEdit)
        assert window_with_notebook._editor_preview.isReadOnly()

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
