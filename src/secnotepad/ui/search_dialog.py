"""Modeless search dialog for the current in-memory notebook tree."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..model.search_service import SearchFields, SearchResult, SearchService
from ..model.snote_item import SNoteItem


class SearchDialog(QDialog):
    """Search notes without taking ownership of result navigation."""

    result_activated = Signal(object)

    def __init__(self, parent=None, search_service: SearchService | None = None) -> None:
        super().__init__(parent)
        self._root_item: SNoteItem | None = None
        self._search_service = search_service or SearchService()
        self._field_guard_active = False

        self.setWindowTitle("搜索笔记")
        self.setModal(False)
        self.setMinimumSize(640, 420)
        self.resize(720, 520)

        self._build_ui()
        self._connect_signals()
        self._show_message("")

    def set_root_item(self, root: SNoteItem | None) -> None:
        """Set the current decrypted notebook root used by future searches."""
        self._root_item = root
        self._clear_results()
        self._count_label.setText("")
        self._show_message("")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        query_row = QHBoxLayout()
        query_row.setSpacing(8)
        query_row.addWidget(QLabel("关键词"))
        self._query_input = QLineEdit()
        self._query_input.setObjectName("search_query_input")
        self._query_input.setPlaceholderText("输入要搜索的标题、正文或标签")
        self._query_input.setMinimumWidth(320)
        query_row.addWidget(self._query_input, 1)
        layout.addLayout(query_row)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(8)
        fields_row.addWidget(QLabel("搜索范围"))
        self._title_checkbox = QCheckBox("标题")
        self._title_checkbox.setObjectName("search_field_title")
        self._title_checkbox.setChecked(True)
        self._content_checkbox = QCheckBox("正文")
        self._content_checkbox.setObjectName("search_field_content")
        self._content_checkbox.setChecked(True)
        self._tags_checkbox = QCheckBox("标签")
        self._tags_checkbox.setObjectName("search_field_tags")
        self._tags_checkbox.setChecked(False)
        fields_row.addWidget(self._title_checkbox)
        fields_row.addWidget(self._content_checkbox)
        fields_row.addWidget(self._tags_checkbox)
        fields_row.addStretch(1)
        layout.addLayout(fields_row)

        action_row = QHBoxLayout()
        action_row.addStretch(1)
        self._search_button = QPushButton("搜索")
        self._search_button.setObjectName("search_button")
        self._close_button = QPushButton("关闭")
        action_row.addWidget(self._search_button)
        action_row.addWidget(self._close_button)
        layout.addLayout(action_row)

        self._count_label = QLabel("")
        self._count_label.setObjectName("search_count_label")
        layout.addWidget(self._count_label)

        self._results_list = QListWidget()
        self._results_list.setObjectName("search_results_list")
        self._results_list.setMinimumHeight(240)
        layout.addWidget(self._results_list, 1)

        self._message_heading = QLabel("")
        self._message_heading.setObjectName("search_message_heading")
        self._message_heading.setAlignment(Qt.AlignCenter)
        self._message_heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        self._message_body = QLabel("")
        self._message_body.setObjectName("search_message_body")
        self._message_body.setAlignment(Qt.AlignCenter)
        self._message_body.setWordWrap(True)
        layout.addWidget(self._message_heading)
        layout.addWidget(self._message_body)

    def _connect_signals(self) -> None:
        self._search_button.clicked.connect(self._on_search)
        self._query_input.returnPressed.connect(self._on_search)
        self._close_button.clicked.connect(self.close)
        for checkbox in self._field_checkboxes():
            checkbox.toggled.connect(self._ensure_one_field_checked)
        self._results_list.itemClicked.connect(self._emit_result_for_item)
        self._results_list.itemDoubleClicked.connect(self._emit_result_for_item)

    def _on_search(self) -> None:
        query = self._query_input.text().strip()
        self._clear_results()
        self._count_label.setText("")

        if not query:
            self._show_message("请输入关键词后搜索")
            return

        try:
            results = self._search_service.search(self._root_item, query, self._selected_fields())
        except Exception:
            self._show_message("无法完成搜索。请检查笔记本数据后重试。")
            return

        self._count_label.setText(f"找到 {len(results)} 个结果")
        if not results:
            self._show_message("未找到匹配结果", "请尝试更换关键词，或勾选更多搜索范围。")
            return

        self._show_message("")
        for result in results:
            self._add_result(result)

    def _selected_fields(self) -> SearchFields:
        return SearchFields(
            title=self._title_checkbox.isChecked(),
            content=self._content_checkbox.isChecked(),
            tags=self._tags_checkbox.isChecked(),
        )

    def _ensure_one_field_checked(self, checked: bool) -> None:
        if checked or self._field_guard_active:
            return
        if any(checkbox.isChecked() for checkbox in self._field_checkboxes()):
            return
        sender = self.sender()
        if isinstance(sender, QCheckBox):
            self._field_guard_active = True
            sender.setChecked(True)
            self._field_guard_active = False

    def _field_checkboxes(self) -> tuple[QCheckBox, QCheckBox, QCheckBox]:
        return (self._title_checkbox, self._content_checkbox, self._tags_checkbox)

    def _clear_results(self) -> None:
        self._results_list.clear()

    def _show_message(self, heading: str, body: str = "") -> None:
        self._message_heading.setText(heading)
        self._message_body.setText(body)
        self._message_heading.setVisible(bool(heading))
        self._message_body.setVisible(bool(body))

    def _add_result(self, result: SearchResult) -> None:
        item = QListWidgetItem(self._results_list)
        item.setData(Qt.UserRole, result)
        widget = _SearchResultWidget(result)
        item.setSizeHint(widget.sizeHint())
        self._results_list.addItem(item)
        self._results_list.setItemWidget(item, widget)

    def _emit_result_for_item(self, item: QListWidgetItem) -> None:
        result = item.data(Qt.UserRole)
        if result is not None:
            self.result_activated.emit(result)


class _SearchResultWidget(QWidget):
    """Small widget used to display a SearchResult safely."""

    def __init__(self, result: SearchResult) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        title = QLabel(result.title)
        title.setTextFormat(Qt.PlainText)
        title.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout.addWidget(title)

        path = QLabel(result.section_path)
        path.setTextFormat(Qt.PlainText)
        path.setStyleSheet("font-size: 12px;")
        layout.addWidget(path)

        snippet = QLabel(result.snippet)
        snippet.setTextFormat(Qt.RichText)
        snippet.setWordWrap(True)
        snippet.setStyleSheet("font-size: 14px;")
        layout.addWidget(snippet)
