"""Rich text editor widget for SecNotepad Phase 04."""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont,
                            QTextBlockFormat, QTextCharFormat, QTextCursor,
                            QTextListFormat)
from PySide6.QtWidgets import (QColorDialog, QComboBox, QFontComboBox, QStyle,
                                QTextEdit, QToolBar, QVBoxLayout, QWidget)


class SafeRichTextEdit(QTextEdit):
    """QTextEdit with Phase 04 paste/resource safety boundaries."""


class RichTextEditorWidget(QWidget):
    """Composite rich text editor with local formatting toolbar."""

    content_changed = Signal(str)
    paste_sanitized = Signal()

    COMMON_FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_callback: Callable[[str], None] | None = None
        self._syncing_toolbar = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._format_toolbar = QToolBar("格式工具栏", self)
        self._format_toolbar.setMovable(False)
        layout.addWidget(self._format_toolbar)

        self._editor = SafeRichTextEdit(self)
        self._editor.setReadOnly(False)
        layout.addWidget(self._editor)

        self._setup_toolbar()
        self._connect_editor_signals()

    def editor(self) -> SafeRichTextEdit:
        """Return the underlying rich text editor."""
        return self._editor

    def format_toolbar(self) -> QToolBar:
        """Return the fixed local formatting toolbar."""
        return self._format_toolbar

    def set_editor_enabled(self, enabled: bool) -> None:
        """Enable or disable both the toolbar and text editor."""
        self._format_toolbar.setEnabled(enabled)
        self._editor.setEnabled(enabled)

    def load_html(self, html: str) -> None:
        """Load HTML without emitting content changes or preserving old undo data."""
        self._editor.blockSignals(True)
        try:
            self._editor.setHtml(html or "")
            self._editor.document().setModified(False)
            self._editor.document().clearUndoRedoStacks()
        finally:
            self._editor.blockSignals(False)

    def to_html(self) -> str:
        """Return the current editor content as Qt HTML."""
        return self._editor.toHtml()

    def set_status_callback(self, callback: Callable[[str], None] | None) -> None:
        """Set an optional callback for user-visible status messages."""
        self._status_callback = callback

    def zoom_percent(self) -> int:
        """Return current zoom percentage. Detailed zoom is implemented later."""
        return 100

    def _setup_toolbar(self) -> None:
        """Create toolbar controls in UI-SPEC order."""
        self.paragraph_style_combo = QComboBox(self)
        self.paragraph_style_combo.setToolTip("段落样式")
        self.paragraph_style_combo.addItems(["正文", "H1", "H2", "H3", "H4", "H5", "H6"])
        self.paragraph_style_combo.setMinimumWidth(96)
        self._format_toolbar.addWidget(self.paragraph_style_combo)

        self.font_combo = QFontComboBox(self)
        self.font_combo.setToolTip("字体")
        self.font_combo.setMinimumWidth(160)
        self._format_toolbar.addWidget(self.font_combo)

        self.size_combo = QComboBox(self)
        self.size_combo.setToolTip("字号")
        self.size_combo.setEditable(False)
        self.size_combo.setMinimumWidth(72)
        self.size_combo.addItems([str(size) for size in self.COMMON_FONT_SIZES])
        self.size_combo.setCurrentText("14")
        self._format_toolbar.addWidget(self.size_combo)

        self._format_toolbar.addSeparator()
        self.action_bold = self._add_checkable_action("加粗", self._on_bold)
        self.action_italic = self._add_checkable_action("斜体", self._on_italic)
        self.action_underline = self._add_checkable_action("下划线", self._on_underline)
        self.action_strike = self._add_checkable_action("删除线", self._on_strike)

        self._format_toolbar.addSeparator()
        self.action_text_color = QAction("文字颜色", self)
        self.action_text_color.setToolTip("文字颜色")
        self.action_text_color.triggered.connect(self._on_text_color)
        self._format_toolbar.addAction(self.action_text_color)

        self.action_background_color = QAction("背景色", self)
        self.action_background_color.setToolTip("背景色")
        self.action_background_color.triggered.connect(self._on_background_color)
        self._format_toolbar.addAction(self.action_background_color)

        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        self.size_combo.currentTextChanged.connect(self._on_size_changed)

    def _connect_editor_signals(self) -> None:
        self._editor.textChanged.connect(self._emit_content_changed)
        self._editor.currentCharFormatChanged.connect(self._sync_char_format)

    def _add_checkable_action(self, text: str, slot: Callable[[bool], None]) -> QAction:
        action = QAction(text, self)
        action.setToolTip(text)
        action.setCheckable(True)
        action.triggered.connect(slot)
        self._format_toolbar.addAction(action)
        return action

    def _emit_content_changed(self) -> None:
        self.content_changed.emit(self._editor.toHtml())

    def _merge_char_format(self, fmt: QTextCharFormat) -> None:
        cursor = self._editor.textCursor()
        self._editor.mergeCurrentCharFormat(fmt)
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _on_bold(self, checked: bool) -> None:
        if self._syncing_toolbar:
            return
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_char_format(fmt)

    def _on_italic(self, checked: bool) -> None:
        if self._syncing_toolbar:
            return
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_char_format(fmt)

    def _on_underline(self, checked: bool) -> None:
        if self._syncing_toolbar:
            return
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_char_format(fmt)

    def _on_strike(self, checked: bool) -> None:
        if self._syncing_toolbar:
            return
        fmt = QTextCharFormat()
        fmt.setFontStrikeOut(checked)
        self._merge_char_format(fmt)

    def _on_font_changed(self, font: QFont) -> None:
        if self._syncing_toolbar:
            return
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self._merge_char_format(fmt)

    def _on_size_changed(self, text: str) -> None:
        if self._syncing_toolbar or not text:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(text))
        self._merge_char_format(fmt)

    def _on_text_color(self) -> None:
        color = self._choose_color()
        if not color.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        self._merge_char_format(fmt)
        self._set_status("已设置文字颜色")

    def _on_background_color(self) -> None:
        color = self._choose_color()
        if not color.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setBackground(color)
        self._merge_char_format(fmt)
        self._set_status("已设置背景色")

    def _choose_color(self) -> QColor:
        return QColorDialog.getColor(parent=self)

    def _set_status(self, message: str) -> None:
        if self._status_callback is not None:
            self._status_callback(message)

    def _sync_char_format(self, char_format: QTextCharFormat) -> None:
        self._syncing_toolbar = True
        try:
            self.action_bold.setChecked(char_format.fontWeight() >= QFont.Weight.Bold)
            self.action_italic.setChecked(char_format.fontItalic())
            self.action_underline.setChecked(char_format.fontUnderline())
            self.action_strike.setChecked(char_format.fontStrikeOut())
            family = char_format.fontFamily()
            if family and self.font_combo.currentFont().family() != family:
                self.font_combo.setCurrentFont(QFont(family))
            point_size = char_format.fontPointSize()
            if point_size > 0:
                self.size_combo.setCurrentText(str(int(point_size)))
        finally:
            self._syncing_toolbar = False
