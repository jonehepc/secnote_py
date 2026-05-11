"""MainWindow 标签集成测试 (Phase 05 Plan 03)。"""

import json

import pytest
from PySide6.QtCore import Qt

from src.secnotepad.model.serializer import Serializer
from src.secnotepad.ui.main_window import MainWindow


@pytest.fixture
def window_with_page(qapp):
    """创建带当前页面的 MainWindow。"""
    w = MainWindow()
    w.show()
    w._on_new_notebook()
    w._on_new_root_section()
    w._on_new_page()
    w._is_dirty = False
    yield w
    w._is_dirty = False
    w.close()
    w.deleteLater()


def current_note(window):
    return window._page_list_model.note_at(window._list_view.currentIndex())


def test_tag_bar_exists_above_format_toolbar(window_with_page):
    """标签栏位于右侧编辑区顶部，且在格式工具栏之前。"""
    window = window_with_page
    assert window._tag_bar is not None

    layout = window._editor_container.layout()
    tag_index = layout.indexOf(window._tag_bar)
    toolbar_index = layout.indexOf(window._format_toolbar)

    assert tag_index >= 0
    assert toolbar_index >= 0
    assert tag_index < toolbar_index


def test_show_note_in_editor_displays_note_tags(window_with_page):
    """显示当前页面时标签栏同步 SNoteItem.tags。"""
    window = window_with_page
    note = current_note(window)
    note.tags = ["Python", "安全 笔记"]

    window._show_note_in_editor(note)

    assert window._tag_bar.tags() == ["Python", "安全 笔记"]


def test_on_tag_added_updates_note_marks_dirty_and_status(window_with_page):
    """添加标签更新当前页面、置脏并显示状态栏反馈。"""
    window = window_with_page
    note = current_note(window)
    note.tags = []
    window._is_dirty = False

    window._on_tag_added("Project A")

    assert note.tags == ["Project A"]
    assert window._tag_bar.tags() == ["Project A"]
    assert window._is_dirty is True
    assert window.statusBar().currentMessage() == "已添加标签：Project A"


def test_on_tag_added_ignores_case_insensitive_duplicate(window_with_page):
    """重复添加大小写不同的同页标签不新增且不置脏。"""
    window = window_with_page
    note = current_note(window)
    note.tags = ["Python"]
    window._show_note_in_editor(note)
    window._is_dirty = False

    window._on_tag_added("python")

    assert note.tags == ["Python"]
    assert window._tag_bar.tags() == ["Python"]
    assert window._is_dirty is False


def test_on_tag_removed_updates_note_marks_dirty_and_status(window_with_page):
    """移除标签更新当前页面、置脏并显示状态栏反馈。"""
    window = window_with_page
    note = current_note(window)
    note.tags = ["Python", "安全 笔记"]
    window._show_note_in_editor(note)
    window._is_dirty = False

    window._on_tag_removed("Python")

    assert note.tags == ["安全 笔记"]
    assert window._tag_bar.tags() == ["安全 笔记"]
    assert window._is_dirty is True
    assert window.statusBar().currentMessage() == "已移除标签：Python"


def test_show_editor_placeholder_disables_tags_without_mutating_note(window_with_page):
    """无当前页面时标签区域禁用且不修改原页面 tags。"""
    window = window_with_page
    note = current_note(window)
    note.tags = ["Python"]
    window._show_note_in_editor(note)
    window._is_dirty = False

    window._show_editor_placeholder()

    assert note.tags == ["Python"]
    assert window._tag_bar.tags() == []
    assert window._tag_bar._input.isEnabled() is False
    assert window._tag_bar._add_button.isEnabled() is False
    assert window._is_dirty is False


def test_page_list_display_role_only_returns_title(window_with_page):
    """页面列表 DisplayRole 保持单列标题，不包含标签文本。"""
    window = window_with_page
    note = current_note(window)
    note.title = "页面标题"
    note.tags = ["Python", "安全 笔记"]

    display = window._page_list_model.data(
        window._list_view.currentIndex(), Qt.DisplayRole
    )

    assert display == "页面标题"
    assert "Python" not in display
    assert "安全 笔记" not in display


def test_tags_persist_through_serializer_json_roundtrip(window_with_page):
    """MainWindow 当前树中的标签经 Serializer JSON 链路保留。"""
    window = window_with_page
    note = current_note(window)
    note.tags = ["Python", "安全 笔记"]
    note.content = "<p>正文不包含标签文本</p>"

    json_str = Serializer.to_json(window._root_item)
    payload = json.loads(json_str)

    assert "tags" in json_str
    assert payload["data"]["children"][0]["children"][0]["tags"] == [
        "Python",
        "安全 笔记",
    ]
    assert payload["data"]["children"][0]["children"][0]["content"] == (
        "<p>正文不包含标签文本</p>"
    )

    restored = Serializer.from_json(json_str)
    restored_note = restored.children[0].children[0]
    assert restored_note.tags == ["Python", "安全 笔记"]
    assert restored_note.content == "<p>正文不包含标签文本</p>"


def test_available_tags_refreshes_from_current_notebook_only(window_with_page):
    """补全候选来自当前笔记本，大小写去重并随新笔记本清空。"""
    window = window_with_page
    first_note = current_note(window)
    first_note.tags = ["Python"]
    window._on_new_page()
    second_note = current_note(window)
    second_note.tags = ["python", "安全"]

    assert window._collect_available_tags() == ["Python", "安全"]

    window._is_dirty = False
    window._on_new_notebook()

    assert window._collect_available_tags() == []
    assert window._tag_bar.tags() == []
