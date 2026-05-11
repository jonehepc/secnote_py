"""RED tests for Phase 04 RichTextEditorWidget behavior."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QActionGroup, QColor, QFont, QTextCursor, QTextListFormat
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFontComboBox

from src.secnotepad.ui.rich_text_editor import RichTextEditorWidget, SafeRichTextEdit


@pytest.fixture
def editor_widget(qapp):
    """Create the rich text editor widget under test."""
    widget = RichTextEditorWidget()
    widget.show()
    yield widget
    widget.close()
    widget.deleteLater()


def _select_all(editor_widget):
    editor = editor_widget.editor()
    cursor = editor.textCursor()
    cursor.select(QTextCursor.Document)
    editor.setTextCursor(cursor)
    return editor


def test_editing_page_updates_note_html_and_dirty(editor_widget):
    changes = []
    editor_widget.content_changed.connect(lambda _html: changes.append("changed"))

    editor_widget.load_html("<p>旧内容</p>")
    assert changes == []
    assert "旧内容" in editor_widget.to_html()

    editor = editor_widget.editor()
    editor.setFocus()
    editor.selectAll()
    editor.insertPlainText("新内容")

    assert changes
    assert "新内容" in editor_widget.to_html()


def test_character_format_actions(editor_widget):
    editor_widget.load_html("<p>format me</p>")
    editor = _select_all(editor_widget)

    editor_widget.action_bold.trigger()
    assert editor.textCursor().charFormat().fontWeight() == QFont.Bold

    editor_widget.action_italic.trigger()
    assert editor.textCursor().charFormat().fontItalic() is True

    editor_widget.action_underline.trigger()
    assert editor.textCursor().charFormat().fontUnderline() is True

    editor_widget.action_strike.trigger()
    assert editor.textCursor().charFormat().fontStrikeOut() is True


def test_character_format_without_selection_applies_to_new_text(editor_widget):
    editor_widget.load_html("")
    editor = editor_widget.editor()
    editor.setFocus()

    editor_widget.action_bold.trigger()
    editor.insertPlainText("bold")

    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, 4)
    assert cursor.charFormat().fontWeight() == QFont.Bold


def test_font_family_and_size_controls(editor_widget):
    editor_widget.load_html("<p>font me</p>")
    editor = _select_all(editor_widget)

    assert isinstance(editor_widget.font_combo, QFontComboBox)
    expected_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48"]
    actual_sizes = [editor_widget.size_combo.itemText(i) for i in range(editor_widget.size_combo.count())]
    assert actual_sizes == expected_sizes

    editor_widget.size_combo.setCurrentText("18")

    assert editor.textCursor().charFormat().fontPointSize() == pytest.approx(18)


def test_text_and_background_color_actions(editor_widget, monkeypatch):
    editor_widget.load_html("<p>color me</p>")
    editor = _select_all(editor_widget)
    colors = iter([QColor("#ff0000"), QColor("#ffff00")])
    monkeypatch.setattr(editor_widget, "_choose_color", lambda *_args, **_kwargs: next(colors))

    editor_widget.action_text_color.trigger()
    assert editor.textCursor().charFormat().foreground().color() == QColor("#ff0000")

    editor_widget.action_background_color.trigger()
    assert editor.textCursor().charFormat().background().color() == QColor("#ffff00")


def test_alignment_actions_are_exclusive(editor_widget):
    actions = [
        editor_widget.action_align_left,
        editor_widget.action_align_center,
        editor_widget.action_align_right,
        editor_widget.action_align_justify,
    ]
    assert all(action.isCheckable() for action in actions)
    groups = {action.actionGroup() for action in actions}
    assert len(groups) == 1
    group = next(iter(groups))
    assert isinstance(group, QActionGroup)
    assert group.isExclusive() is True

    editor_widget.load_html("<p>align me</p>")
    editor_widget.action_align_center.trigger()

    assert editor_widget.editor().alignment() & Qt.AlignCenter


def test_list_and_checklist_actions(editor_widget):
    editor_widget.load_html("<p>item</p>")
    editor = _select_all(editor_widget)

    editor_widget.action_bullet_list.trigger()
    assert editor.textCursor().currentList() is not None
    assert editor.textCursor().currentList().format().style() == QTextListFormat.ListDisc

    editor_widget.load_html("<p>item</p>")
    editor = _select_all(editor_widget)
    editor_widget.action_ordered_list.trigger()
    assert editor.textCursor().currentList() is not None
    assert editor.textCursor().currentList().format().style() == QTextListFormat.ListDecimal

    editor_widget.load_html("<p>todo</p>")
    editor_widget.action_todo_list.trigger()
    plain_text = editor_widget.editor().toPlainText()
    html = editor_widget.to_html().lower()
    assert "☐ " in plain_text
    assert "<input" not in html
    assert "checkbox" not in html


def test_todo_action_without_selection_only_updates_current_block(editor_widget):
    editor_widget.load_html("<p>first</p><p>second</p>")
    editor = editor_widget.editor()
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.setTextCursor(cursor)

    editor_widget.action_todo_list.trigger()

    lines = editor.toPlainText().splitlines()
    assert lines == ["☐ first", "second"]


def test_heading_levels(editor_widget):
    expected_styles = ["正文", "H1", "H2", "H3", "H4", "H5", "H6"]
    actual_styles = [editor_widget.paragraph_style_combo.itemText(i) for i in range(editor_widget.paragraph_style_combo.count())]
    assert actual_styles == expected_styles

    editor_widget.load_html("<p>heading</p>")
    editor_widget.paragraph_style_combo.setCurrentText("H2")

    assert editor_widget.editor().textCursor().blockFormat().headingLevel() == 2


def test_indent_outdent_actions(editor_widget):
    editor_widget.load_html("<p>indent me</p>")
    cursor = editor_widget.editor().textCursor()
    start_indent = cursor.blockFormat().indent()

    editor_widget.action_indent.trigger()
    indented = editor_widget.editor().textCursor().blockFormat().indent()
    assert indented > start_indent

    editor_widget.action_outdent.trigger()
    outdented = editor_widget.editor().textCursor().blockFormat().indent()
    assert outdented >= 0
    assert outdented <= indented


def test_undo_redo_actions(editor_widget):
    editor_widget.load_html("")
    editor = editor_widget.editor()
    editor.setFocus()
    assert editor_widget.action_undo.isEnabled() is False
    assert editor_widget.action_redo.isEnabled() is False

    QTest.keyClicks(editor, "undo me")
    assert editor_widget.action_undo.isEnabled() is True

    editor_widget.action_undo.trigger()
    assert "undo me" not in editor.toPlainText()
    assert editor_widget.action_redo.isEnabled() is True

    editor_widget.action_redo.trigger()
    assert "undo me" in editor.toPlainText()


def test_clipboard_actions_and_safe_paste(editor_widget):
    assert isinstance(editor_widget.editor(), SafeRichTextEdit)
    messages = []
    editor_widget.status_message_requested.connect(messages.append)
    unsafe_html = """
    <p>safe text</p>
    <img src="file:/tmp/a.png" onerror="steal()">
    <img src="http://example.com/a.png">
    <script>alert(1)</script>
    <span onclick="steal()">x</span>
    <a href="javascript:alert(1)">x</a>
    """
    clipboard = QApplication.clipboard()
    clipboard.setText("")
    mime = clipboard.mimeData()
    mime.setHtml(unsafe_html)
    mime.setText("safe text x")
    clipboard.setMimeData(mime)

    editor_widget.load_html("")
    editor_widget.action_paste.trigger()
    html = editor_widget.to_html().lower()

    assert "safe text" in html
    for blocked in ("<img", "file:", "http://", "https://", "<script", "onclick=", "onerror=", "javascript:"):
        assert blocked not in html
    assert "已粘贴文本内容；图片和外部资源未导入" in messages


def test_zoom_does_not_mark_content_dirty(editor_widget):
    changes = []
    editor_widget.content_changed.connect(lambda: changes.append("changed"))
    editor_widget.load_html("<p>zoom me</p>")
    before = editor_widget.to_html()

    editor_widget.zoom_in()
    assert editor_widget.zoom_percent == 110
    editor_widget.zoom_out()
    assert editor_widget.zoom_percent == 100
    editor_widget.zoom_in()
    editor_widget.reset_zoom()
    assert editor_widget.zoom_percent == 100

    assert editor_widget.to_html() == before
    assert changes == []
