"""Tests for SearchService — 当前笔记本内存树全文搜索服务。"""

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.search_service import SearchFields, SearchService


class TestSearchService:
    """SearchService.search 行为测试。"""

    def test_search_matches_title_and_content_by_default_with_paths_and_plain_snippets(self):
        """默认搜索标题和 HTML 正文纯文本，结果包含标题、路径、字段和安全片段。"""
        root, notes = _sample_tree()

        results = SearchService.search(root, "季度", SearchFields())

        assert [result.note for result in results] == [
            notes["quarter_title"],
            notes["quarter_content"],
        ]
        assert results[0].title == "季度计划"
        assert results[0].section_path == "根分区 / 工作 / 项目A"
        assert results[0].matched_field == "title"
        assert "<mark>季度</mark>" in results[0].snippet
        assert results[1].title == "会议记录"
        assert results[1].section_path == "根分区 / 工作"
        assert results[1].matched_field == "content"
        assert "<mark>季度</mark>" in results[1].snippet
        _assert_no_raw_html(results[1].snippet)

    def test_html_to_plain_text_extracts_body_without_qtextedit_document_markup(self):
        """正文搜索必须从 QTextEdit HTML 中提取纯文本，而不是返回原始 HTML。"""
        html = (
            '<!DOCTYPE HTML><html><head><style>p { color: red; }</style></head>'
            '<body><p style="font-weight:600;">季度 <span>复盘</span></p></body></html>'
        )

        plain = SearchService.html_to_plain_text(html)

        assert "季度" in plain
        assert "复盘" in plain
        assert "<p>" not in plain
        assert "style=" not in plain
        assert "<!DOCTYPE" not in plain

    def test_search_fields_can_select_tags_only_and_tags_are_disabled_by_default(self):
        """SearchFields 支持只搜索标签；默认 tags=False 不匹配标签。"""
        root, notes = _sample_tree()

        default_results = SearchService.search(root, "Roadmap")
        tag_results = SearchService.search(
            root,
            "Roadmap",
            SearchFields(title=False, content=False, tags=True),
        )

        assert default_results == []
        assert [result.note for result in tag_results] == [notes["tagged"]]
        assert tag_results[0].matched_field == "tags"
        assert tag_results[0].snippet == "<mark>Roadmap</mark>"

    def test_empty_inputs_and_disabled_fields_return_empty_results(self):
        """空查询、空 root 和全部字段关闭均返回空列表。"""
        root, _ = _sample_tree()

        assert SearchService.search(root, "") == []
        assert SearchService.search(root, "   ") == []
        assert SearchService.search(None, "季度") == []
        assert SearchService.search(
            root,
            "季度",
            SearchFields(title=False, content=False, tags=False),
        ) == []

    def test_matching_is_case_insensitive_and_keeps_tree_order(self):
        """匹配大小写不敏感，返回顺序保持树遍历自然顺序而非标题排序。"""
        root = SNoteItem.new_section("根分区")
        section = SNoteItem.new_section("工作")
        beta = SNoteItem.new_note("Beta alpha")
        alpha = SNoteItem.new_note("Alpha")
        section.children.extend([beta, alpha])
        root.children.append(section)

        results = SearchService.search(root, "ALPHA", SearchFields(title=True, content=False))

        assert [result.note for result in results] == [beta, alpha]
        assert [result.title for result in results] == ["Beta alpha", "Alpha"]

    def test_query_metacharacters_are_highlighted_as_literal_text(self):
        """高亮必须把用户 query 当作字面字符串，而不是正则表达式。"""
        for query in ["C++", "[abc]", "a.b", "foo(bar)"]:
            root = SNoteItem.new_section("根分区")
            note = SNoteItem.new_note(f"查询 {query}")
            root.children.append(note)

            results = SearchService.search(root, query, SearchFields(title=True, content=False))

            assert len(results) == 1
            assert results[0].note is note
            assert results[0].snippet == f"查询 <mark>{query}</mark>"

    def test_content_snippet_escapes_user_text_before_inserting_mark_tags(self):
        """正文含脚本或标签字符时，片段只显示转义文本与受控 <mark>。"""
        root = SNoteItem.new_section("根分区")
        note = SNoteItem.new_note(
            "安全片段",
            '<p>before &lt;script&gt;alert(1)&lt;/script&gt; keyword &lt;b&gt;bold&lt;/b&gt;</p>',
        )
        root.children.append(note)

        results = SearchService.search(root, "keyword", SearchFields(title=False, content=True))

        assert len(results) == 1
        snippet = results[0].snippet
        assert "<mark>keyword</mark>" in snippet
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in snippet
        assert "&lt;b&gt;bold&lt;/b&gt;" in snippet
        assert "<script>" not in snippet
        assert "<b>" not in snippet

    def test_tags_only_search_matches_chinese_space_tag_without_content_or_title(self):
        """只勾选标签字段时可命中中文/空格标签，且不误用标题或正文。"""
        root = SNoteItem.new_section("根分区")
        section = SNoteItem.new_section("项目")
        target = SNoteItem.new_note("无关标题", "<p>无关正文</p>")
        target.tags = ["安全 项目"]
        decoy = SNoteItem.new_note("安全标题", "<p>安全正文</p>")
        section.children.extend([target, decoy])
        root.children.append(section)

        results = SearchService.search(
            root,
            "安全",
            SearchFields(title=False, content=False, tags=True),
        )

        assert [result.note for result in results] == [target]
        assert results[0].matched_field == "tags"
        assert results[0].section_path == "根分区 / 项目"
        assert results[0].snippet == "<mark>安全</mark> 项目"

    def test_html_script_style_and_event_text_are_plain_text_before_highlight(self):
        """HTML/脚本样式正文片段仅保留纯文本与受控 <mark>，不展示原始危险属性。"""
        root = SNoteItem.new_section("根分区")
        note = SNoteItem.new_note(
            "HTML 安全",
            (
                '<p style="color:red" onclick="steal()">alpha keyword</p>'
                '<script>alert("secret")</script>'
            ),
        )
        root.children.append(note)

        results = SearchService.search(root, "keyword", SearchFields(title=False, content=True))

        assert len(results) == 1
        snippet = results[0].snippet
        assert "alpha <mark>keyword</mark>" in snippet
        assert "<script>" not in snippet
        assert "script" not in snippet
        assert "style=" not in snippet
        assert "onclick" not in snippet


def _sample_tree() -> tuple[SNoteItem, dict[str, SNoteItem]]:
    """构造含根分区、嵌套分区、多个 note、HTML content 和 tags 的样例树。"""
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    project = SNoteItem.new_section("项目A")
    personal = SNoteItem.new_section("个人")

    quarter_title = SNoteItem.new_note("季度计划", "<p>没有正文命中</p>")
    quarter_content = SNoteItem.new_note(
        "会议记录",
        '<!DOCTYPE HTML><html><body><p style="color:red;">本次讨论季度目标和排期。</p></body></html>',
    )
    tagged = SNoteItem.new_note("标签页", "<p>无匹配正文</p>")
    tagged.tags.append("Roadmap")
    other = SNoteItem.new_note("日记", "<p>完全无关</p>")

    project.children.append(quarter_title)
    work.children.extend([project, quarter_content, tagged])
    personal.children.append(other)
    root.children.extend([work, personal])
    return root, {
        "quarter_title": quarter_title,
        "quarter_content": quarter_content,
        "tagged": tagged,
        "other": other,
    }


def _assert_no_raw_html(value: str) -> None:
    assert "<p>" not in value
    assert "style=" not in value
    assert "<!DOCTYPE" not in value
