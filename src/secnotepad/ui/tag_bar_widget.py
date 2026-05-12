"""Reusable tag chip bar widget for SecNotepad Phase 05."""

import html

from PySide6.QtCore import QMargins, QPoint, QRect, QSize, Qt, Signal, QStringListModel
from PySide6.QtWidgets import (QCompleter, QFrame, QHBoxLayout, QLabel, QLayout,
                                QLayoutItem, QLineEdit, QPushButton, QSizePolicy,
                                QToolButton, QVBoxLayout, QWidget)


class FlowLayout(QLayout):
    """Simple wrapping layout for tag chips and the add controls."""

    def __init__(self, parent=None, margin: int = 0, spacing: int = 8):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._margins = QMargins(margin, margin, margin, margin)
        self.setContentsMargins(self._margins)
        self.setSpacing(spacing)

    def addItem(self, item: QLayoutItem) -> None:
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self._margins
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        margins = self._margins
        effective_rect = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        spacing = self.spacing()
        right = effective_rect.right()

        for item in self._items:
            hint = item.sizeHint()
            item_width = min(hint.width(), max(1, effective_rect.width()))
            next_x = x + item_width + spacing
            if next_x - spacing > right and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + spacing
                next_x = x + item_width + spacing
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), QSize(item_width, hint.height())))

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + margins.bottom()


class TagBarWidget(QWidget):
    """Tag chip row with validation, completion, and add/remove intent signals."""

    tag_added = Signal(str)
    tag_removed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tags: list[str] = []
        self._remove_buttons: list[QToolButton] = []
        self._tag_widgets: list[QWidget] = []
        self._editing_enabled = True

        self._available_tags_model = QStringListModel(self)
        self._completer = QCompleter(self._available_tags_model, self)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setWrapAround(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._title_label = QLabel("标签", self)
        layout.addWidget(self._title_label)

        self._flow_container = QWidget(self)
        self._flow_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._flow_layout = FlowLayout(self._flow_container, spacing=8)
        layout.addWidget(self._flow_container)

        self._empty_label = QLabel("暂无标签", self)
        self._empty_label.setObjectName("empty_tag_label")
        self._flow_layout.addWidget(self._empty_label)

        self._input = QLineEdit(self)
        self._input.setObjectName("tag_input")
        self._input.setPlaceholderText("添加标签…")
        self._input.setMinimumWidth(120)
        self._input.setMaximumWidth(180)
        self._input.setCompleter(self._completer)
        self._input.returnPressed.connect(self._try_add_tag)
        self._flow_layout.addWidget(self._input)

        self._add_button = QPushButton("添加标签", self)
        self._add_button.setObjectName("add_tag_button")
        self._add_button.clicked.connect(self._try_add_tag)
        self._flow_layout.addWidget(self._add_button)

        self._error_label = QLabel("", self)
        self._error_label.setObjectName("tag_error_label")
        self._error_label.setStyleSheet("color: #d32f2f;")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        self._refresh_tags()

    def set_tags(self, tags: list[str]) -> None:
        """Refresh displayed tags without emitting add/remove intent signals."""
        self._tags = list(tags)
        self._clear_error()
        self._refresh_tags()

    def set_available_tags(self, tags: list[str]) -> None:
        """Refresh completer candidates without emitting add/remove intent signals."""
        sorted_tags = sorted(list(dict.fromkeys(tags)), key=str.casefold)
        self._available_tags_model.setStringList(sorted_tags)

    def set_tag_editing_enabled(self, enabled: bool) -> None:
        """Enable or disable tag input, add button, and chip remove buttons."""
        self._editing_enabled = enabled
        self._input.setEnabled(enabled)
        self._add_button.setEnabled(enabled)
        for button in self._remove_buttons:
            button.setEnabled(enabled)

    def tags(self) -> list[str]:
        """Return the currently displayed tags in order."""
        return list(self._tags)

    def _refresh_tags(self) -> None:
        for tag_widget in self._tag_widgets:
            self._flow_layout.removeWidget(tag_widget)
            tag_widget.setParent(None)
            tag_widget.deleteLater()
        self._tag_widgets.clear()
        self._remove_buttons.clear()

        self._empty_label.setVisible(not self._tags)

        # Rebuild layout order explicitly: chips, empty label/input/button.
        controls = [self._empty_label, self._input, self._add_button]
        for control in controls:
            self._flow_layout.removeWidget(control)
        for tag in self._tags:
            chip = self._create_chip(tag)
            self._tag_widgets.append(chip)
            self._flow_layout.addWidget(chip)
        self._flow_layout.addWidget(self._empty_label)
        self._flow_layout.addWidget(self._input)
        self._flow_layout.addWidget(self._add_button)
        self._flow_container.updateGeometry()
        self._flow_container.update()

    def _create_chip(self, tag: str) -> QFrame:
        chip = QFrame(self._flow_container)
        chip.setObjectName("tag_chip")
        chip.setFrameShape(QFrame.StyledPanel)
        chip.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout = QHBoxLayout(chip)
        layout.setContentsMargins(8, 4, 4, 4)
        layout.setSpacing(4)

        label = QLabel(tag, chip)
        label.setTextFormat(Qt.PlainText)
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        layout.addWidget(label)

        remove_button = QToolButton(chip)
        remove_button.setText("×")
        remove_button.setToolTip(f"移除标签：{html.escape(tag)}")
        remove_button.setMinimumSize(20, 20)
        remove_button.setEnabled(self._editing_enabled)
        remove_button.clicked.connect(lambda _checked=False, value=tag: self.tag_removed.emit(value))
        layout.addWidget(remove_button)
        self._remove_buttons.append(remove_button)
        return chip

    def _try_add_tag(self) -> None:
        raw_text = self._input.text()
        tag = raw_text.strip()
        if not tag:
            self._show_error("标签不能为空")
            return
        if len(tag) > 32:
            self._show_error("标签不能超过 32 个字符")
            return
        if tag.casefold() in {existing.casefold() for existing in self._tags}:
            self._show_error("该页面已包含此标签")
            return

        self._clear_error()
        self._input.clear()
        self.tag_added.emit(tag)

    def _show_error(self, message: str) -> None:
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def _clear_error(self) -> None:
        self._error_label.setText("")
        self._error_label.setVisible(False)
