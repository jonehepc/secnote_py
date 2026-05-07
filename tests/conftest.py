"""共享测试 fixture 和配置"""

import pytest
from PySide6.QtWidgets import QApplication

from src.secnotepad.model.snote_item import SNoteItem


@pytest.fixture(scope="session")
def qapp():
    """提供 QApplication 实例用于 pytest-qt 测试

    使用 session scope 确保整个测试套件复用同一个
    QApplication 实例，避免多个实例创建导致的崩溃。
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ── Model Fixtures ──


@pytest.fixture
def sample_tree() -> SNoteItem:
    """创建 3 层示例 SNoteItem 树。

    根分区 (section, hidden in TreeModel)
    └── 工作 (section)
        ├── 周报 (note)
        └── 项目A (section)
            └── 需求文档 (note)
    """
    root = SNoteItem.new_section("根分区")
    work = SNoteItem.new_section("工作")
    report = SNoteItem.new_note("周报")
    project = SNoteItem.new_section("项目A")
    doc = SNoteItem.new_note("需求文档")
    project.children.append(doc)
    work.children.append(report)
    work.children.append(project)
    root.children.append(work)
    return root


@pytest.fixture
def section_item() -> SNoteItem:
    """单个 section 节点，无子节点。"""
    return SNoteItem.new_section("单分区")


@pytest.fixture
def note_item() -> SNoteItem:
    """单个 note 节点。"""
    return SNoteItem.new_note("单笔记", "这是内容")


# ── Crypto Test Fixtures ──


@pytest.fixture
def test_password() -> str:
    """测试用密码（含大小写字母、数字、符号，> 8 字符）。"""
    return "TestP@ss123"


@pytest.fixture
def sample_json_str() -> str:
    """有效的加密载荷 JSON 字符串。"""
    import json
    document = {
        "version": 1,
        "data": {
            "id": "a" * 32,
            "title": "根分区",
            "item_type": "section",
            "content": "",
            "children": [],
            "tags": [],
            "created_at": "2026-05-07T10:00:00Z",
            "updated_at": "2026-05-07T10:00:00Z",
        },
    }
    return json.dumps(document, ensure_ascii=False)
