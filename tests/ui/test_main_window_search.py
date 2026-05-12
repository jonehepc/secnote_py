"""MainWindow search entry and result navigation integration tests."""

import json

from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QKeySequence
import pytest

from src.secnotepad.crypto.file_service import FileService
from src.secnotepad.model.search_service import SearchFields, SearchResult, SearchService
from src.secnotepad.model.serializer import Serializer
from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.ui.main_window import MainWindow
from src.secnotepad.ui.search_dialog import SearchDialog


@pytest.fixture
def window_with_search_tree(qapp):
    """Create a MainWindow with nested sections and pages for search navigation."""
    window = MainWindow()
    window.show()
    window._on_new_notebook()

    root = window._root_item
    first_section = SNoteItem.new_section("项目")
    nested_section = SNoteItem.new_section("归档")
    first_note = SNoteItem.new_note("首页", "<p>普通内容</p>")
    target_note = SNoteItem.new_note("目标页面", "<p>目标正文</p>")
    first_section.children.append(first_note)
    nested_section.children.append(target_note)
    first_section.children.append(nested_section)
    root.children.append(first_section)
    window._setup_navigation()
    window._is_dirty = False

    yield window, first_section, nested_section, first_note, target_note

    window._is_dirty = False
    if window._search_dialog is not None:
        window._search_dialog.close()
    window.close()
    window.deleteLater()


def _current_tree_item(window: MainWindow):
    proxy_index = window._tree_view.currentIndex()
    source_index = window._section_filter.mapToSource(proxy_index)
    return source_index.internalPointer() if source_index.isValid() else None


def _current_page_item(window: MainWindow):
    return window._page_list_model.note_at(window._list_view.currentIndex())


def test_search_action_exists_disabled_on_welcome(qapp):
    window = MainWindow()
    try:
        assert window._act_search.text() == "搜索(&F)..."
        assert window._act_search.shortcut() == QKeySequence("Ctrl+F")
        assert window._act_search.isEnabled() is False
    finally:
        window.close()
        window.deleteLater()


def test_search_action_opens_modeless_dialog_with_current_root(window_with_search_tree):
    window, *_ = window_with_search_tree

    assert window._act_search.isEnabled() is True
    window._act_search.trigger()

    assert isinstance(window._search_dialog, SearchDialog)
    assert window._search_dialog.isModal() is False
    assert window._search_dialog.isVisible() is True
    assert window._search_dialog._root_item is window._root_item
    assert window._is_dirty is False


def test_search_action_enabled_after_opening_saved_notebook(qapp, tmp_path, monkeypatch):
    root = SNoteItem.new_section("根分区")
    root.children.append(SNoteItem.new_section("项目"))
    path = tmp_path / "search-enabled.secnote"
    FileService.save(Serializer.to_json(root), str(path), "secret")

    window = MainWindow()
    monkeypatch.setattr(
        "src.secnotepad.ui.main_window.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: (str(path), "SecNotepad 加密笔记本 (*.secnote)"),
    )
    monkeypatch.setattr(
        window,
        "_open_with_password_retry",
        lambda opened_path: (FileService.open(opened_path, "secret"), "secret"),
    )
    try:
        assert window._act_search.isEnabled() is False

        window._on_open_notebook()

        assert window._act_search.isEnabled() is True
        window._act_search.trigger()
        assert isinstance(window._search_dialog, SearchDialog)
        assert window._search_dialog._root_item is window._root_item
    finally:
        if window._search_dialog is not None:
            window._search_dialog.close()
        window.close()
        window.deleteLater()


def test_select_search_result_syncs_tree_list_editor_and_keeps_dialog_open(window_with_search_tree):
    window, _first_section, nested_section, _first_note, target_note = window_with_search_tree
    window._act_search.trigger()
    assert window._search_dialog.isVisible() is True

    result = SearchResult(
        note=target_note,
        title=target_note.title,
        section_path="根分区 / 项目 / 归档",
        matched_field="content",
        snippet="目标正文",
    )
    window._select_search_result(result)

    assert _current_tree_item(window) is nested_section
    assert _current_page_item(window) is target_note
    assert "目标正文" in window._rich_text_editor.editor().toPlainText()
    assert window.statusBar().currentMessage() == "已跳转到：目标页面"
    assert window._is_dirty is False
    assert window._search_dialog.isVisible() is True


def test_tags_only_search_result_navigation_does_not_create_search_persistence(window_with_search_tree):
    """标签搜索命中可跳转，搜索/跳转不置脏且序列化不出现索引或历史字段。"""
    window, _first_section, _nested_section, first_note, target_note = window_with_search_tree
    target_note.tags = ["安全 项目"]
    target_note.content = "<p>正文不含查询词</p>"
    first_note.tags = ["普通"]
    window._is_dirty = False

    before_payload = json.loads(Serializer.to_json(window._root_item))
    results = SearchService.search(
        window._root_item,
        "安全",
        SearchFields(title=False, content=False, tags=True),
    )
    assert [result.note for result in results] == [target_note]

    window._act_search.trigger()
    window._select_search_result(results[0])

    after_payload = json.loads(Serializer.to_json(window._root_item))
    serialized = Serializer.to_json(window._root_item)
    assert _current_page_item(window) is target_note
    assert window._search_dialog.isVisible() is True
    assert window.statusBar().currentMessage() == "已跳转到：目标页面"
    assert window._is_dirty is False
    assert before_payload == after_payload
    assert "tags" in serialized
    assert "search" not in serialized.lower()
    assert "index" not in serialized.lower()
    assert "history" not in serialized.lower()


def test_search_result_activation_signal_keeps_dialog_visible(window_with_search_tree):
    window, _first_section, _nested_section, _first_note, target_note = window_with_search_tree
    window._act_search.trigger()

    result = SearchResult(
        note=target_note,
        title=target_note.title,
        section_path="根分区 / 项目 / 归档",
        matched_field="title",
        snippet="目标页面",
    )
    window._search_dialog.result_activated.emit(result)

    assert _current_page_item(window) is target_note
    assert window._search_dialog.isVisible() is True
    assert window._is_dirty is False


def test_clear_session_disables_search_and_removes_old_dialog_root(window_with_search_tree):
    window, *_ = window_with_search_tree
    window._act_search.trigger()
    dialog = window._search_dialog
    assert dialog._root_item is window._root_item

    window._clear_session()

    assert window._act_search.isEnabled() is False
    assert dialog._root_item is None
    assert dialog.isVisible() is False


def test_select_stale_search_result_shows_fixed_message_without_dirty(window_with_search_tree):
    window, *_ = window_with_search_tree
    stale_note = SNoteItem.new_note("旧页面", "<p>旧内容</p>")
    result = SearchResult(
        note=stale_note,
        title=stale_note.title,
        section_path="根分区 / 已删除",
        matched_field="title",
        snippet="旧页面",
    )

    window._select_search_result(result)

    assert window.statusBar().currentMessage() == "搜索结果对应页面不存在"
    assert window._is_dirty is False


def test_find_item_source_index_uses_object_identity(window_with_search_tree):
    window, first_section, _nested_section, _first_note, _target_note = window_with_search_tree
    same_value_section = SNoteItem(
        id=first_section.id,
        title=first_section.title,
        item_type=first_section.item_type,
        children=list(first_section.children),
        created_at=first_section.created_at,
        updated_at=first_section.updated_at,
    )

    assert window._find_item_source_index(first_section).isValid() is True
    assert window._find_item_source_index(same_value_section) == QModelIndex()
