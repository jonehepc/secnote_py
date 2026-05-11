"""Tests for SearchDialog — 搜索弹窗 UI 行为。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QLabel, QLineEdit, QListWidget, QPushButton

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.ui.search_dialog import SearchDialog


class CountingSearchService:
    """Test double that records search calls while delegating to the real SearchService."""

    def __init__(self) -> None:
        from src.secnotepad.model.search_service import SearchService

        self._service = SearchService()
        self.calls = []

    def search(self, root, query, fields):
        self.calls.append((root, query, fields))
        return self._service.search(root, query, fields)


class FailingSearchService:
    """Search service that raises without leaking query/content into logs."""

    def search(self, root, query, fields):
        raise RuntimeError("boom")


def test_search_dialog_initial_state_and_field_guards(qapp):
    dialog = SearchDialog()
    try:
        assert dialog.windowTitle() == "搜索笔记"
        assert not dialog.isModal()
        assert dialog.minimumWidth() >= 640
        assert dialog.minimumHeight() >= 420

        query_input = _query_input(dialog)
        assert query_input.placeholderText() == "输入要搜索的标题、正文或标签"

        fields = _field_checkboxes(dialog)
        assert set(fields) == {"标题", "正文", "标签"}
        assert fields["标题"].isChecked()
        assert fields["正文"].isChecked()
        assert not fields["标签"].isChecked()

        fields["标题"].setChecked(False)
        fields["正文"].setChecked(False)
        fields["标签"].setChecked(False)
        assert any(checkbox.isChecked() for checkbox in fields.values())
    finally:
        dialog.close()
        dialog.deleteLater()


def test_empty_query_shows_prompt_without_calling_search(qapp):
    service = CountingSearchService()
    dialog = SearchDialog(search_service=service)
    try:
        dialog.set_root_item(_sample_root())
        _click_search(dialog)

        assert service.calls == []
        assert _visible_label_texts(dialog) == ["请输入关键词后搜索"]
        assert _results_list(dialog).count() == 0
    finally:
        dialog.close()
        dialog.deleteLater()


def test_button_and_return_trigger_search_with_count_and_safe_results(qapp):
    service = CountingSearchService()
    dialog = SearchDialog(search_service=service)
    try:
        dialog.set_root_item(_sample_root())
        query_input = _query_input(dialog)
        query_input.setText("季度")

        _click_search(dialog)
        assert len(service.calls) == 1
        assert _count_label(dialog).text() == "找到 2 个结果"
        assert _results_list(dialog).count() == 2
        first_text = _result_widget_text(_results_list(dialog), 0)
        assert "季度计划" in first_text
        assert "根分区 / 工作 / 项目A" in first_text
        assert "<mark>季度</mark>" in first_text

        second_text = _result_widget_text(_results_list(dialog), 1)
        assert "会议记录" in second_text
        assert "根分区 / 工作" in second_text
        assert "<mark>季度</mark>" in second_text
        assert "<p" not in second_text
        assert "style=" not in second_text
        assert "<!DOCTYPE" not in second_text

        query_input.returnPressed.emit()
        assert len(service.calls) == 2
    finally:
        dialog.close()
        dialog.deleteLater()


def test_empty_results_show_empty_state(qapp):
    dialog = SearchDialog()
    try:
        dialog.set_root_item(_sample_root())
        _query_input(dialog).setText("不存在")
        _click_search(dialog)

        assert _count_label(dialog).text() == "找到 0 个结果"
        texts = _visible_label_texts(dialog)
        assert "未找到匹配结果" in texts
        assert "请尝试更换关键词，或勾选更多搜索范围。" in texts
        assert _results_list(dialog).count() == 0
    finally:
        dialog.close()
        dialog.deleteLater()


def test_result_activation_emits_payload_and_keeps_dialog_open(qapp):
    dialog = SearchDialog()
    activated = []
    try:
        dialog.set_root_item(_sample_root())
        dialog.result_activated.connect(activated.append)
        dialog.show()
        _query_input(dialog).setText("季度")
        _click_search(dialog)

        results_list = _results_list(dialog)
        item = results_list.item(0)
        results_list.setCurrentItem(item)
        results_list.itemClicked.emit(item)
        results_list.itemDoubleClicked.emit(item)

        assert len(activated) == 2
        assert activated[0].title == "季度计划"
        assert activated[0] is item.data(Qt.UserRole)
        assert dialog.isVisible()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_set_text_does_not_trigger_realtime_search(qapp):
    """设置文本不应触发实时搜索；只能由回车或搜索按钮触发。"""
    service = CountingSearchService()
    dialog = SearchDialog(search_service=service)
    try:
        dialog.set_root_item(_sample_root())
        assert _count_label(dialog).text() == ""

        _query_input(dialog).setText("季度")

        assert service.calls == []
        assert _count_label(dialog).text() == ""
        _click_search(dialog)
        assert len(service.calls) == 1
    finally:
        dialog.close()
        dialog.deleteLater()


def test_search_error_uses_fixed_message(qapp):
    dialog = SearchDialog(search_service=FailingSearchService())
    try:
        dialog.set_root_item(_sample_root())
        _query_input(dialog).setText("季度")
        _click_search(dialog)

        assert _visible_label_texts(dialog) == ["无法完成搜索。请检查笔记本数据后重试。"]
        assert _results_list(dialog).count() == 0
    finally:
        dialog.close()
        dialog.deleteLater()


def _sample_root() -> SNoteItem:
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    project = SNoteItem.new_section("项目A")
    personal = SNoteItem.new_section("个人")

    quarter_title = SNoteItem.new_note("季度计划", "<p>没有正文命中</p>")
    quarter_content = SNoteItem.new_note(
        "会议记录",
        '<!DOCTYPE HTML><html><head><style>p { color:red; }</style></head>'
        '<body><p style="color:red;">本次讨论季度目标和排期。</p></body></html>',
    )
    tagged = SNoteItem.new_note("标签页", "<p>无匹配正文</p>")
    tagged.tags.append("Roadmap")
    other = SNoteItem.new_note("日记", "<p>完全无关</p>")

    project.children.append(quarter_title)
    work.children.extend([project, quarter_content, tagged])
    personal.children.append(other)
    root.children.extend([work, personal])
    return root


def _query_input(dialog: SearchDialog) -> QLineEdit:
    widget = dialog.findChild(QLineEdit, "search_query_input")
    assert widget is not None
    return widget


def _results_list(dialog: SearchDialog) -> QListWidget:
    widget = dialog.findChild(QListWidget, "search_results_list")
    assert widget is not None
    return widget


def _count_label(dialog: SearchDialog) -> QLabel:
    widget = dialog.findChild(QLabel, "search_count_label")
    assert widget is not None
    return widget


def _field_checkboxes(dialog: SearchDialog) -> dict[str, QCheckBox]:
    return {checkbox.text(): checkbox for checkbox in dialog.findChildren(QCheckBox)}


def _click_search(dialog: SearchDialog) -> None:
    buttons = [button for button in dialog.findChildren(QPushButton) if button.text() == "搜索"]
    assert len(buttons) == 1
    buttons[0].click()


def _visible_label_texts(dialog: SearchDialog) -> list[str]:
    return [
        label.text()
        for label in dialog.findChildren(QLabel)
        if not label.isHidden() and label.text() in {
            "请输入关键词后搜索",
            "未找到匹配结果",
            "请尝试更换关键词，或勾选更多搜索范围。",
            "无法完成搜索。请检查笔记本数据后重试。",
        }
    ]


def _result_widget_text(results_list: QListWidget, row: int) -> str:
    item = results_list.item(row)
    widget = results_list.itemWidget(item)
    assert widget is not None
    return "\n".join(label.text() for label in widget.findChildren(QLabel))
