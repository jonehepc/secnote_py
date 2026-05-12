"""Read-only search service for the current in-memory notebook tree."""

from __future__ import annotations

from dataclasses import dataclass
import html
from collections.abc import Iterator

from PySide6.QtGui import QTextDocumentFragment

from .snote_item import SNoteItem


@dataclass(frozen=True)
class SearchFields:
    """Fields included in a search query."""

    title: bool = True
    content: bool = True
    tags: bool = False


@dataclass(frozen=True)
class SearchResult:
    """One search result for a note in the current notebook."""

    note: SNoteItem
    title: str
    section_path: str
    matched_field: str
    snippet: str


class SearchService:
    """Search the decrypted in-memory SNoteItem tree without persistence."""

    _SNIPPET_RADIUS = 40

    @staticmethod
    def html_to_plain_text(html: str) -> str:
        """Extract plain text from QTextEdit HTML using Qt's document parser."""
        return QTextDocumentFragment.fromHtml(html or "").toPlainText()

    @staticmethod
    def search(
        root: SNoteItem | None,
        query: str,
        fields: SearchFields | None = None,
    ) -> list[SearchResult]:
        """Search note titles, content plain text and optional tags in tree order."""
        normalized_query = query.strip()
        search_fields = fields or SearchFields()
        if (
            root is None
            or not normalized_query
            or not (search_fields.title or search_fields.content or search_fields.tags)
        ):
            return []

        results: list[SearchResult] = []
        query_key = normalized_query.casefold()
        for note, section_path in _iter_notes_with_paths(root):
            result = _match_note(note, section_path, normalized_query, query_key, search_fields)
            if result is not None:
                results.append(result)
        return results


def _iter_notes_with_paths(root: SNoteItem) -> Iterator[tuple[SNoteItem, str]]:
    """Yield note items with the section path containing the hidden root title."""
    root_path = [root.title] if root.title else []
    yield from _walk_children(root.children, root_path)


def _walk_children(
    children: list[SNoteItem],
    section_path: list[str],
) -> Iterator[tuple[SNoteItem, str]]:
    for item in children:
        if item.item_type == "section":
            next_path = [*section_path, item.title] if item.title else section_path
            yield from _walk_children(item.children, next_path)
        elif item.item_type == "note":
            yield item, " / ".join(section_path)


def _match_note(
    note: SNoteItem,
    section_path: str,
    query: str,
    query_key: str,
    fields: SearchFields,
) -> SearchResult | None:
    if fields.title and query_key in note.title.casefold():
        return SearchResult(
            note=note,
            title=note.title,
            section_path=section_path,
            matched_field="title",
            snippet=_make_snippet(note.title, query),
        )

    if fields.content:
        plain_content = SearchService.html_to_plain_text(note.content)
        if query_key in plain_content.casefold():
            return SearchResult(
                note=note,
                title=note.title,
                section_path=section_path,
                matched_field="content",
                snippet=_make_snippet(plain_content, query),
            )

    if fields.tags:
        for tag in note.tags:
            if isinstance(tag, str) and query_key in tag.casefold():
                return SearchResult(
                    note=note,
                    title=note.title,
                    section_path=section_path,
                    matched_field="tags",
                    snippet=_make_snippet(tag, query),
                )

    return None


def _make_snippet(text: str, query: str) -> str:
    """Return escaped text with the literal query wrapped in a controlled mark tag."""
    start, end = _find_casefold_span(text, query)
    if start < 0:
        return html.escape(text)

    snippet_start = max(0, start - SearchService._SNIPPET_RADIUS)
    snippet_end = min(len(text), end + SearchService._SNIPPET_RADIUS)
    prefix = "…" if snippet_start > 0 else ""
    suffix = "…" if snippet_end < len(text) else ""
    raw_snippet = text[snippet_start:snippet_end]
    local_start = start - snippet_start
    local_end = end - snippet_start

    highlighted = _highlight_span(raw_snippet, local_start, local_end)
    return f"{prefix}{highlighted}{suffix}"


def _find_casefold_span(text: str, query: str) -> tuple[int, int]:
    folded_query = query.casefold()
    folded_parts: list[str] = []
    index_map: list[int] = []
    for index, char in enumerate(text):
        folded = char.casefold()
        folded_parts.append(folded)
        index_map.extend([index] * len(folded))

    folded_text = "".join(folded_parts)
    folded_start = folded_text.find(folded_query)
    if folded_start < 0:
        return -1, -1
    folded_end = folded_start + len(folded_query) - 1
    return index_map[folded_start], index_map[folded_end] + 1


def _highlight_span(text: str, start: int, end: int) -> str:
    return "".join((
        html.escape(text[:start]),
        f"<mark>{html.escape(text[start:end])}</mark>",
        html.escape(text[end:]),
    ))
