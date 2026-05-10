"""Rich text editor widget for SecNotepad Phase 04."""

import re
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont,
                            QTextBlockFormat, QTextCharFormat, QTextCursor,
                            QTextDocumentFragment, QTextListFormat)
from PySide6.QtWidgets import (QApplication, QColorDialog, QComboBox,
                                QFontComboBox, QStyle, QTextEdit, QToolBar,
                                QVBoxLayout, QWidget)


class SafeRichTextEdit(QTextEdit):
    """QTextEdit with Phase 04 paste/resource safety boundaries."""

    paste_sanitized = Signal()

    def canInsertFromMimeData(self, source) -> bool:
        """Allow text/HTML insertion and reject image/URL-only MIME payloads."""
        if source.hasText() or source.hasHtml():
            return True
        if source.hasImage() or source.hasUrls():
            return False
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source) -> None:
        """Downgrade unsafe HTML paste payloads to plain text."""
        if source.hasHtml() and self._html_has_blocked_resources(source.html()):
            if source.hasText():
                self.insertPlainText(source.text())
            self.paste_sanitized.emit()
            return
        super().insertFromMimeData(source)

    def _html_has_blocked_resources(self, html: str) -> bool:
        lowered = html.lower()
        blocked_patterns = (
            '<img',
            'src="file:',
            "src='file:",
            'src="http:',
            "src='http:",
            'src="https:',
            "src='https:",
            '<script',
            'javascript:',
        )
        return any(pattern in lowered for pattern in blocked_patterns) or re.search(r"\son[a-z]+\s*=", lowered) is not None


class RichTextEditorWidget(QWidget):
    """Composite rich text editor with local formatting toolbar."""

    content_changed = Signal(str)
    paste_sanitized = Signal()
    status_message_requested = Signal(str)
    undo_available_changed = Signal(bool)
    redo_available_changed = Signal(bool)
    copy_available_changed = Signal(bool)

    COMMON_FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status_callback: Callable[[str], None] | None = None
        self._syncing_toolbar = False
        self._zoom_steps = 0

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
        """Return current content as HTML without Qt's external doctype URL."""
        html = self._editor.toHtml()
        return re.sub(r'<!DOCTYPE[^>]*>\s*', '', html, count=1, flags=re.IGNORECASE)

    def set_status_callback(self, callback: Callable[[str], None] | None) -> None:
        """Set an optional callback for user-visible status messages."""
        self._status_callback = callback

    def undo(self) -> None:
        """Undo the latest edit in the underlying QTextEdit document."""
        self._editor.undo()

    def redo(self) -> None:
        """Redo the latest undone edit in the underlying QTextEdit document."""
        self._editor.redo()

    def cut(self) -> None:
        """Cut selected text through QTextEdit's standard clipboard handling."""
        self._editor.cut()

    def copy(self) -> None:
        """Copy selected text through QTextEdit's standard clipboard handling."""
        self._editor.copy()

    def paste(self) -> None:
        """Paste through SafeRichTextEdit's MIME safety boundary."""
        self._editor.paste()

    def can_paste(self) -> bool:
        """Return True when the clipboard contains text or HTML."""
        mime_data = QApplication.clipboard().mimeData()
        return mime_data.hasText() or mime_data.hasHtml()

    def zoom_percent(self) -> int:
        """Return current session-only zoom percentage."""
        return 100 + self._zoom_steps * 10

    def _setup_toolbar(self) -> None:
        """Create toolbar controls in UI-SPEC order."""
        self.paragraph_style_combo = QComboBox(self)
        self.paragraph_style_combo.setToolTip("段落样式")
        self.paragraph_style_combo.setEditable(False)
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
        self.action_undo = QAction("撤销", self)
        self.action_undo.setToolTip("撤销")
        self.action_undo.setEnabled(False)
        self.action_undo.triggered.connect(self.undo)
        self._format_toolbar.addAction(self.action_undo)

        self.action_redo = QAction("重做", self)
        self.action_redo.setToolTip("重做")
        self.action_redo.setEnabled(False)
        self.action_redo.triggered.connect(self.redo)
        self._format_toolbar.addAction(self.action_redo)

        self.action_cut = QAction("剪切", self)
        self.action_cut.setToolTip("剪切")
        self.action_cut.setEnabled(False)
        self.action_cut.triggered.connect(self.cut)
        self._format_toolbar.addAction(self.action_cut)

        self.action_copy = QAction("复制", self)
        self.action_copy.setToolTip("复制")
        self.action_copy.setEnabled(False)
        self.action_copy.triggered.connect(self.copy)
        self._format_toolbar.addAction(self.action_copy)

        self.action_paste = QAction("粘贴", self)
        self.action_paste.setToolTip("粘贴")
        self.action_paste.triggered.connect(self.paste)
        self._format_toolbar.addAction(self.action_paste)

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

        self._format_toolbar.addSeparator()
        self._setup_alignment_actions()

        self._format_toolbar.addSeparator()
        self._setup_list_actions()

        self._format_toolbar.addSeparator()
        self._setup_indent_actions()

        self.paragraph_style_combo.currentTextChanged.connect(self._on_paragraph_style_changed)
        self.font_combo.currentFontChanged.connect(self._on_font_changed)
        self.size_combo.currentTextChanged.connect(self._on_size_changed)

    def _connect_editor_signals(self) -> None:
        self._editor.textChanged.connect(self._emit_content_changed)
        self._editor.currentCharFormatChanged.connect(self._sync_char_format)
        self._editor.cursorPositionChanged.connect(self._sync_block_format)
        self._editor.document().undoAvailable.connect(self.undo_available_changed)
        self._editor.document().undoAvailable.connect(self.action_undo.setEnabled)
        self._editor.document().redoAvailable.connect(self.redo_available_changed)
        self._editor.document().redoAvailable.connect(self.action_redo.setEnabled)
        self._editor.copyAvailable.connect(self.copy_available_changed)
        self._editor.copyAvailable.connect(self.action_cut.setEnabled)
        self._editor.copyAvailable.connect(self.action_copy.setEnabled)
        self._editor.paste_sanitized.connect(self._on_paste_sanitized)

    def _add_checkable_action(self, text: str, slot: Callable[[bool], None]) -> QAction:
        action = QAction(text, self)
        action.setToolTip(text)
        action.setCheckable(True)
        action.triggered.connect(slot)
        self._format_toolbar.addAction(action)
        return action

    def _setup_alignment_actions(self) -> None:
        self.alignment_group = QActionGroup(self)
        self.alignment_group.setExclusive(True)
        self.action_align_left = self._add_alignment_action("左对齐", Qt.AlignLeft)
        self.action_align_center = self._add_alignment_action("居中", Qt.AlignCenter)
        self.action_align_right = self._add_alignment_action("右对齐", Qt.AlignRight)
        self.action_align_justify = self._add_alignment_action("两端对齐", Qt.AlignJustify)

    def _add_alignment_action(self, text: str, alignment: Qt.AlignmentFlag) -> QAction:
        action = QAction(text, self)
        action.setToolTip(text)
        action.setCheckable(True)
        self.alignment_group.addAction(action)
        action.triggered.connect(lambda _checked=False, value=alignment: self._on_alignment_changed(value))
        self._format_toolbar.addAction(action)
        return action

    def _setup_list_actions(self) -> None:
        self.action_bullet_list = QAction("无序列表", self)
        self.action_bullet_list.setToolTip("无序列表")
        self.action_bullet_list.triggered.connect(
            lambda: self._create_list(QTextListFormat.Style.ListDisc)
        )
        self._format_toolbar.addAction(self.action_bullet_list)

        self.action_numbered_list = QAction("有序列表", self)
        self.action_numbered_list.setToolTip("有序列表")
        self.action_numbered_list.triggered.connect(
            lambda: self._create_list(QTextListFormat.Style.ListDecimal)
        )
        self._format_toolbar.addAction(self.action_numbered_list)
        self.action_ordered_list = self.action_numbered_list

        self.action_todo_list = QAction("待办列表", self)
        self.action_todo_list.setToolTip("待办列表")
        self.action_todo_list.triggered.connect(self._insert_todo_item)
        self._format_toolbar.addAction(self.action_todo_list)

    def _setup_indent_actions(self) -> None:
        self.action_indent_less = QAction("减少缩进", self)
        self.action_indent_less.setToolTip("减少缩进")
        self.action_indent_less.triggered.connect(lambda: self._adjust_indent(-1))
        self._format_toolbar.addAction(self.action_indent_less)
        self.action_outdent = self.action_indent_less

        self.action_indent_more = QAction("增加缩进", self)
        self.action_indent_more.setToolTip("增加缩进")
        self.action_indent_more.triggered.connect(lambda: self._adjust_indent(1))
        self._format_toolbar.addAction(self.action_indent_more)
        self.action_indent = self.action_indent_more

    def _emit_content_changed(self) -> None:
        self.content_changed.emit(self.to_html())

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

    def _on_paragraph_style_changed(self, text: str) -> None:
        if self._syncing_toolbar:
            return
        level = 0 if text == "正文" else int(text.removeprefix("H"))
        cursor = self._editor.textCursor()
        cursor.beginEditBlock()
        try:
            block_fmt = cursor.blockFormat()
            block_fmt.setHeadingLevel(level)
            cursor.setBlockFormat(block_fmt)
        finally:
            cursor.endEditBlock()
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _on_alignment_changed(self, alignment: Qt.AlignmentFlag) -> None:
        if self._syncing_toolbar:
            return
        self._editor.setAlignment(alignment)
        self._editor.setFocus()

    def _create_list(self, style: QTextListFormat.Style) -> None:
        cursor = self._editor.textCursor()
        cursor.beginEditBlock()
        try:
            current_list = cursor.currentList()
            list_fmt = QTextListFormat()
            list_fmt.setStyle(style)
            if current_list is not None:
                list_fmt.setIndent(max(1, current_list.format().indent()))
            else:
                block_indent = cursor.blockFormat().indent()
                list_fmt.setIndent(max(1, block_indent))
            cursor.createList(list_fmt)
        finally:
            cursor.endEditBlock()
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def _insert_todo_item(self) -> None:
        cursor = self._editor.textCursor()
        start = min(cursor.selectionStart(), cursor.selectionEnd())
        end = max(cursor.selectionStart(), cursor.selectionEnd())
        doc = self._editor.document()

        cursor.beginEditBlock()
        try:
            block = doc.findBlock(start)
            end_block = doc.findBlock(end)
            end_block_number = end_block.blockNumber() if end_block.isValid() else block.blockNumber()
            while block.isValid() and block.blockNumber() <= end_block_number:
                if not block.text().startswith("☐ "):
                    block_cursor = QTextCursor(block)
                    block_cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    block_cursor.insertText("☐ ")
                    end_block_number += 1 if block.position() <= end else 0
                block = block.next()
        finally:
            cursor.endEditBlock()
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()
        self._set_status("已插入待办项")

    def _adjust_indent(self, delta: int) -> None:
        cursor = self._editor.textCursor()
        cursor.beginEditBlock()
        try:
            current_list = cursor.currentList()
            if current_list is not None:
                list_fmt = current_list.format()
                list_fmt.setIndent(max(1, list_fmt.indent() + delta))
                current_list.setFormat(list_fmt)
            else:
                block_fmt = cursor.blockFormat()
                block_fmt.setIndent(max(0, block_fmt.indent() + delta))
                cursor.setBlockFormat(block_fmt)
        finally:
            cursor.endEditBlock()
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

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
        self.status_message_requested.emit(message)
        if self._status_callback is not None:
            self._status_callback(message)

    def _on_paste_sanitized(self) -> None:
        self.paste_sanitized.emit()
        self._set_status("已粘贴文本内容；图片和外部资源未导入")

    def _sync_char_format(self, char_format: QTextCharFormat) -> None:
        self._syncing_toolbar = True
        try:
            self.action_bold.setChecked(char_format.fontWeight() >= QFont.Weight.Bold)
            self.action_italic.setChecked(char_format.fontItalic())
            self.action_underline.setChecked(char_format.fontUnderline())
            self.action_strike.setChecked(char_format.fontStrikeOut())
            font = char_format.font()
            family = font.family()
            if family:
                self.font_combo.blockSignals(True)
                try:
                    current_family = self.font_combo.currentText()
                    if current_family != family:
                        self.font_combo.setCurrentText(family)
                finally:
                    self.font_combo.blockSignals(False)
            point_size = char_format.fontPointSize()
            if point_size > 0:
                self.size_combo.setCurrentText(str(int(point_size)))
        finally:
            self._syncing_toolbar = False

    def _sync_block_format(self) -> None:
        cursor = self._editor.textCursor()
        block_fmt = cursor.blockFormat()
        heading_level = block_fmt.headingLevel()
        style_text = "正文" if heading_level <= 0 else f"H{min(heading_level, 6)}"
        alignment = self._editor.alignment()

        self._syncing_toolbar = True
        try:
            self.paragraph_style_combo.setCurrentText(style_text)
            if alignment & Qt.AlignJustify:
                self.action_align_justify.setChecked(True)
            elif alignment & Qt.AlignRight:
                self.action_align_right.setChecked(True)
            elif alignment & Qt.AlignCenter:
                self.action_align_center.setChecked(True)
            else:
                self.action_align_left.setChecked(True)
        finally:
            self._syncing_toolbar = False
