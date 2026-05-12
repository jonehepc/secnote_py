"""RED tests for Phase 05 TagBarWidget behavior."""

from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QAbstractButton, QLabel, QLineEdit, QPushButton

from src.secnotepad.ui.tag_bar_widget import TagBarWidget


def _visible_label_texts(widget):
    return [label.text() for label in widget.findChildren(QLabel) if label.isVisible()]


def _button_with_text(widget, text):
    for button in widget.findChildren(QAbstractButton):
        if button.text() == text:
            return button
    raise AssertionError(f"button not found: {text}")


def _remove_button_for(widget, tag):
    tooltip = f"移除标签：{tag}"
    for button in widget.findChildren(QAbstractButton):
        if button.toolTip() == tooltip:
            return button
    raise AssertionError(f"remove button not found: {tag}")


def _add_tag(widget, text, *, press_return=True):
    input_widget = widget.findChild(QLineEdit)
    input_widget.setFocus()
    input_widget.clear()
    input_widget.setText(text)
    if press_return:
        QTest.keyClick(input_widget, Qt.Key_Return)
    else:
        QTest.mouseClick(_button_with_text(widget, "添加标签"), Qt.LeftButton)
    return input_widget


def test_set_tags_displays_chips_and_preserves_order(qapp):
    widget = TagBarWidget()
    widget.show()

    widget.set_tags(["Python", "安全 笔记"])
    qapp.processEvents()

    assert widget.tags() == ["Python", "安全 笔记"]
    assert "Python" in _visible_label_texts(widget)
    assert "安全 笔记" in _visible_label_texts(widget)
    assert "暂无标签" not in _visible_label_texts(widget)

    widget.close()
    widget.deleteLater()


def test_tag_chip_renders_user_text_as_plain_text(qapp):
    widget = TagBarWidget()
    widget.set_tags(["<b>安全</b>"])

    chip_label = next(label for label in widget.findChildren(QLabel) if label.text() == "<b>安全</b>")
    assert chip_label.textFormat() == Qt.PlainText

    widget.deleteLater()


def test_refresh_methods_do_not_emit_add_or_remove(qapp):
    widget = TagBarWidget()
    added = QSignalSpy(widget.tag_added)
    removed = QSignalSpy(widget.tag_removed)

    widget.set_tags(["Python", "安全 笔记"])
    widget.set_available_tags(["Python", "安全 笔记"])

    assert added.count() == 0
    assert removed.count() == 0

    widget.deleteLater()


def test_add_tag_trims_and_emits_original_inner_text_by_return_and_button(qapp):
    widget = TagBarWidget()
    widget.show()
    added = QSignalSpy(widget.tag_added)

    input_widget = _add_tag(widget, "  新 标签  ")

    assert added.count() == 1
    assert added.at(0) == ["新 标签"]
    assert input_widget.text() == ""

    input_widget = _add_tag(widget, "  C++/安全#1  ", press_return=False)

    assert added.count() == 2
    assert added.at(1) == ["C++/安全#1"]
    assert input_widget.text() == ""

    widget.close()
    widget.deleteLater()


def test_invalid_inputs_show_errors_without_emitting(qapp):
    widget = TagBarWidget()
    widget.set_tags(["Python"])
    widget.show()
    added = QSignalSpy(widget.tag_added)
    error_label = widget.findChild(QLabel, "tag_error_label")

    _add_tag(widget, "   ")
    assert added.count() == 0
    assert error_label.text() == "标签不能为空"

    _add_tag(widget, "一" * 33)
    assert added.count() == 0
    assert error_label.text() == "标签不能超过 32 个字符"

    _add_tag(widget, "python")
    assert added.count() == 0
    assert error_label.text() == "该页面已包含此标签"

    widget.close()
    widget.deleteLater()


def test_remove_button_emits_original_tag(qapp):
    widget = TagBarWidget()
    widget.set_tags(["Python", "安全 笔记"])
    widget.show()
    removed = QSignalSpy(widget.tag_removed)

    QTest.mouseClick(_remove_button_for(widget, "Python"), Qt.LeftButton)

    assert removed.count() == 1
    assert removed.at(0) == ["Python"]

    widget.close()
    widget.deleteLater()


def test_available_tags_configures_case_insensitive_qcompleter(qapp):
    widget = TagBarWidget()
    widget.set_available_tags(["安全 笔记", "Python"])
    input_widget = widget.findChild(QLineEdit)
    completer = input_widget.completer()

    assert completer is not None
    assert type(completer).__name__ == "QCompleter"
    assert completer.caseSensitivity() == Qt.CaseInsensitive
    model_values = [completer.model().index(row, 0).data() for row in range(completer.model().rowCount())]
    assert model_values == ["Python", "安全 笔记"]

    widget.deleteLater()


def test_set_tag_editing_enabled_disables_inputs_add_button_and_remove_buttons(qapp):
    widget = TagBarWidget()
    widget.set_tags(["Python"])
    widget.set_tag_editing_enabled(False)

    assert widget.findChild(QLineEdit, "tag_input").isEnabled() is False
    assert widget.findChild(QPushButton, "add_tag_button").isEnabled() is False
    assert _remove_button_for(widget, "Python").isEnabled() is False

    widget.set_tag_editing_enabled(True)

    assert widget.findChild(QLineEdit, "tag_input").isEnabled() is True
    assert widget.findChild(QPushButton, "add_tag_button").isEnabled() is True
    assert _remove_button_for(widget, "Python").isEnabled() is True

    widget.deleteLater()


def test_tag_chips_wrap_without_horizontal_overflow(qapp):
    widget = TagBarWidget()
    widget.resize(240, 160)
    widget.set_tags([f"标签{i:02d}-很长名称" for i in range(10)])
    widget.show()
    qapp.processEvents()

    chip_labels = [label for label in widget.findChildren(QLabel) if label.text().startswith("标签")]
    assert chip_labels
    assert max(label.mapTo(widget, label.rect().topRight()).x() for label in chip_labels) <= widget.width()
    assert len({label.mapTo(widget, label.rect().topLeft()).y() for label in chip_labels}) > 1

    widget.close()
    widget.deleteLater()
