"""Tests for PageListModel — QAbstractListModel 页面列表数据模型 (NAV-02, NAV-04)。

测试 PageListModel 的 rowCount、data、flags、setData、add_note、
remove_note、note_at 行为，以及 set_section 重置和数据源同步。
"""

import pytest
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtTest import QSignalSpy

from src.secnotepad.model.snote_item import SNoteItem
from src.secnotepad.model.page_list_model import PageListModel


# ── Fixtures ──


@pytest.fixture
def section_with_notes():
    """Create a section with mixed note and section children.

    section "测试分区"
    ├── note "页面1" (content "内容1")
    ├── note "页面2" (content "内容2")
    └── section "子分区" (should NOT appear in page list)
    """
    section = SNoteItem.new_section("测试分区")
    section.children.append(SNoteItem.new_note("页面1", "内容1"))
    section.children.append(SNoteItem.new_note("页面2", "内容2"))
    empty_section = SNoteItem.new_section("子分区")
    section.children.append(empty_section)
    return section


@pytest.fixture
def section_without_notes():
    """Create a section with no note children."""
    section = SNoteItem.new_section("空分区")
    section.children.append(SNoteItem.new_section("仅子分区"))
    return section


@pytest.fixture
def list_model(section_with_notes):
    """Create a PageListModel with a section that has 2 notes."""
    model = PageListModel()
    model.set_section(section_with_notes)
    return model


# ── rowCount Tests ──


class TestRowCount:
    """rowCount — 平铺展示分区下的 note 子节点列表。"""

    def test_rowcount_counts_only_notes(self, section_with_notes):
        """场景 1: set_section 传入含 2 个 note + 1 个 section 子节点的分区 → rowCount() == 2（只计 note）。"""
        model = PageListModel()
        model.set_section(section_with_notes)
        assert model.rowCount() == 2

    def test_rowcount_zero_when_no_notes(self, section_without_notes):
        """场景 2: set_section 传入无 note 子节点的分区 → rowCount() == 0。"""
        model = PageListModel()
        model.set_section(section_without_notes)
        assert model.rowCount() == 0

    def test_rowcount_zero_for_valid_parent_index(self, list_model):
        """扁平 list model 对有效 parent 查询子行数时返回 0。"""
        parent = list_model.index(0, 0)
        assert list_model.rowCount(parent) == 0

    def test_rowcount_zero_when_no_section(self):
        """场景 3: set_section(None) → rowCount() == 0。"""
        model = PageListModel()
        section = SNoteItem.new_section("test")
        section.children.append(SNoteItem.new_note("note1"))
        model.set_section(section)
        assert model.rowCount() == 1
        model.set_section(None)
        assert model.rowCount() == 0


# ── data Tests ──


class TestData:
    """data — 返回页面标题，单列布局 (D-54)。"""

    def test_display_role_returns_title(self, list_model):
        """场景 4: data(index 0, Qt.DisplayRole) → 返回第一个 note 的 title 字符串。"""
        idx = list_model.index(0, 0)
        assert list_model.data(idx, Qt.DisplayRole) == "页面1"

    def test_edit_role_returns_title(self, list_model):
        """场景 5: data(index 0, Qt.EditRole) → 返回第一个 note 的 title 字符串（与 DisplayRole 相同）。"""
        idx = list_model.index(0, 0)
        assert list_model.data(idx, Qt.EditRole) == "页面1"

    def test_invalid_index_returns_none(self, list_model):
        """场景 6: data(invalid_index, Qt.DisplayRole) → 返回 None。"""
        assert list_model.data(QModelIndex(), Qt.DisplayRole) is None

    def test_unsupported_role_returns_none(self, list_model):
        """场景 7: data(valid_index, Qt.DecorationRole) → 返回 None（未实现角色）。"""
        idx = list_model.index(0, 0)
        assert list_model.data(idx, Qt.DecorationRole) is None

    def test_wrong_column_returns_none(self, list_model):
        """column 非 0 的索引不应访问页面数据。"""
        idx = list_model.createIndex(0, 1)
        assert list_model.data(idx, Qt.DisplayRole) is None

    def test_external_model_index_returns_none(self, list_model, section_with_notes):
        """来自其他 model 的索引不应访问本 model 数据。"""
        other_model = PageListModel()
        other_model.set_section(section_with_notes)
        idx = other_model.index(0, 0)
        assert list_model.data(idx, Qt.DisplayRole) is None


# ── flags Tests ──


class TestFlags:
    """flags — 有效索引可编辑，无效索引无标志。"""

    def test_flags_valid_editable(self, list_model):
        """场景 8: flags(valid_index) → 包含 Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable。"""
        idx = list_model.index(0, 0)
        flags = list_model.flags(idx)
        assert flags & Qt.ItemIsEnabled
        assert flags & Qt.ItemIsSelectable
        assert flags & Qt.ItemIsEditable

    def test_flags_invalid_none(self, list_model):
        """场景 9: flags(invalid_index) → 返回 Qt.NoItemFlags。"""
        assert list_model.flags(QModelIndex()) == Qt.NoItemFlags

    def test_flags_wrong_column_none(self, list_model):
        """column 非 0 的索引无标志。"""
        idx = list_model.createIndex(0, 1)
        assert list_model.flags(idx) == Qt.NoItemFlags


# ── setData Tests ──


class TestSetData:
    """setData — EditRole 重命名，空/纯空格/非 str 拒绝 (D-60)。"""

    def test_setdata_rename_updates_title_and_emits_signal(self, list_model):
        """场景 10: setData(valid_index, "新标题", Qt.EditRole) → 返回 True，note.title 更新，
        dataChanged 信号发射。"""
        idx = list_model.index(0, 0)
        spy = QSignalSpy(list_model.dataChanged)

        result = list_model.setData(idx, "新标题", Qt.EditRole)
        assert result is True
        assert list_model.data(idx, Qt.DisplayRole) == "新标题"
        assert list_model.data(idx, Qt.EditRole) == "新标题"
        assert spy.count() == 1

    def test_setdata_reject_empty_string(self, list_model):
        """场景 11: setData(valid_index, "", Qt.EditRole) → 返回 False，note.title 不变 (D-60)。"""
        idx = list_model.index(0, 0)
        original = list_model.data(idx, Qt.DisplayRole)
        result = list_model.setData(idx, "", Qt.EditRole)
        assert result is False
        assert list_model.data(idx, Qt.DisplayRole) == original

    def test_setdata_reject_whitespace(self, list_model):
        """场景 12: setData(valid_index, "   ", Qt.EditRole) → 返回 False，note.title 不变 (纯空格拒绝)。"""
        idx = list_model.index(0, 0)
        original = list_model.data(idx, Qt.DisplayRole)
        result = list_model.setData(idx, "   ", Qt.EditRole)
        assert result is False
        assert list_model.data(idx, Qt.DisplayRole) == original

    def test_setdata_reject_invalid_index(self, list_model):
        """场景 13: setData(invalid_index, "test", Qt.EditRole) → 返回 False。"""
        result = list_model.setData(QModelIndex(), "test", Qt.EditRole)
        assert result is False

    def test_setdata_reject_wrong_role(self, list_model):
        """场景 14: setData(valid_index, "test", Qt.DisplayRole) → 返回 False（非 EditRole）。"""
        idx = list_model.index(0, 0)
        result = list_model.setData(idx, "test", Qt.DisplayRole)
        assert result is False

    def test_setdata_reject_non_string(self, list_model):
        """场景 15: setData(valid_index, 12345, Qt.EditRole) → 返回 False（非 str 类型）。"""
        idx = list_model.index(0, 0)
        result = list_model.setData(idx, 12345, Qt.EditRole)
        assert result is False

    def test_setdata_reject_wrong_column(self, list_model):
        """column 非 0 的索引不能修改页面。"""
        idx = list_model.createIndex(0, 1)
        original = list_model.data(list_model.index(0, 0), Qt.DisplayRole)
        assert list_model.setData(idx, "错误修改", Qt.EditRole) is False
        assert list_model.data(list_model.index(0, 0), Qt.DisplayRole) == original

    def test_setdata_reject_external_model_index(self, list_model, section_with_notes):
        """来自其他 model 的索引不能修改页面。"""
        other_model = PageListModel()
        other_model.set_section(section_with_notes)
        idx = other_model.index(0, 0)
        original = list_model.data(list_model.index(0, 0), Qt.DisplayRole)
        assert list_model.setData(idx, "错误修改", Qt.EditRole) is False
        assert list_model.data(list_model.index(0, 0), Qt.DisplayRole) == original


# ── add_note Tests ──


class TestAddNote:
    """add_note — 追加新页面到当前分区。"""

    def test_add_note_appends_and_syncs_children(self, list_model, section_with_notes):
        """场景 16: add_note(SNoteItem.new_note("新页面")) → 返回 True，rowCount 从 N 变为 N+1，
        新 note 同时加入 self._section.children。"""
        original_count = list_model.rowCount()
        note = SNoteItem.new_note("新页面")
        result = list_model.add_note(note)
        assert result is True
        assert list_model.rowCount() == original_count + 1
        # Verify note is in section.children
        assert note in section_with_notes.children
        # Verify note appears in data
        last_idx = list_model.index(list_model.rowCount() - 1, 0)
        assert list_model.data(last_idx, Qt.DisplayRole) == "新页面"

    def test_add_note_without_section(self):
        """场景 17: set_section 为 None 时调用 add_note → 返回 False，rowCount 不变。"""
        model = PageListModel()
        assert model.rowCount() == 0
        note = SNoteItem.new_note("孤立的页面")
        result = model.add_note(note)
        assert result is False
        assert model.rowCount() == 0

    def test_add_note_rejects_section_item(self, list_model, section_with_notes):
        """add_note 只接受 note，拒绝将 section 插入页面列表。"""
        original_count = list_model.rowCount()
        section = SNoteItem.new_section("错误分区")
        result = list_model.add_note(section)
        assert result is False
        assert list_model.rowCount() == original_count
        assert section not in section_with_notes.children


# ── remove_note Tests ──


class TestRemoveNote:
    """remove_note — 删除页面并从分区 children 列表中移除。"""

    def test_remove_note_removes_and_syncs(self, list_model, section_with_notes):
        """场景 18: remove_note(valid_index) → 返回 True，rowCount 从 N 变为 N-1，
        note 从 self._section.children 中移除。"""
        original_count = list_model.rowCount()
        idx = list_model.index(0, 0)
        note_to_remove = list_model.note_at(idx)

        result = list_model.remove_note(idx)
        assert result is True
        assert list_model.rowCount() == original_count - 1
        # Verify note is removed from section.children
        assert note_to_remove not in section_with_notes.children

    def test_remove_note_invalid_index(self, list_model):
        """场景 19: remove_note(invalid_index) → 返回 False。"""
        result = list_model.remove_note(QModelIndex())
        assert result is False

    def test_remove_note_rejects_wrong_column(self, list_model):
        """column 非 0 的索引不能删除页面。"""
        idx = list_model.createIndex(0, 1)
        assert list_model.remove_note(idx) is False
        assert list_model.rowCount() == 2

    def test_remove_note_rejects_external_model_index(self, list_model, section_with_notes):
        """来自其他 model 的索引不能删除页面。"""
        other_model = PageListModel()
        other_model.set_section(section_with_notes)
        idx = other_model.index(0, 0)
        assert list_model.remove_note(idx) is False
        assert list_model.rowCount() == 2


# ── note_at Tests ──


class TestNoteAt:
    """note_at — 通过索引获取 SNoteItem 对象。"""

    def test_note_at_returns_item(self, list_model):
        """场景 20: note_at(valid_index) → 返回对应的 SNoteItem 对象。"""
        idx = list_model.index(0, 0)
        note = list_model.note_at(idx)
        assert isinstance(note, SNoteItem)
        assert note.item_type == "note"
        assert note.title == "页面1"

    def test_note_at_invalid_returns_none(self, list_model):
        """场景 21: note_at(invalid_index) → 返回 None。"""
        assert list_model.note_at(QModelIndex()) is None

    def test_note_at_wrong_column_returns_none(self, list_model):
        """column 非 0 的索引不返回页面。"""
        idx = list_model.createIndex(0, 1)
        assert list_model.note_at(idx) is None

    def test_note_at_external_model_index_returns_none(self, list_model, section_with_notes):
        """来自其他 model 的索引不返回页面。"""
        other_model = PageListModel()
        other_model.set_section(section_with_notes)
        idx = other_model.index(0, 0)
        assert list_model.note_at(idx) is None


# ── set_section Replacement Tests ──


class TestSetSectionReplacement:
    """set_section — 连续调用替换数据源。"""

    def test_set_section_replaces_previous(self, section_with_notes):
        """场景 22: 两次连续 set_section（不同分区）→ 第二次替换第一次的 _notes 列表，
        rowCount 反映新分区的 note 数量。"""
        model = PageListModel()
        model.set_section(section_with_notes)
        assert model.rowCount() == 2

        # Create a different section with a different number of notes
        other_section = SNoteItem.new_section("其他分区")
        other_section.children.append(SNoteItem.new_note("笔记A"))
        other_section.children.append(SNoteItem.new_note("笔记B"))
        other_section.children.append(SNoteItem.new_note("笔记C"))

        model.set_section(other_section)
        assert model.rowCount() == 3
        idx = model.index(0, 0)
        assert model.data(idx, Qt.DisplayRole) == "笔记A"


# ── Object Reference Consistency Tests ──


class TestObjectReferenceConsistency:
    """Pitfall 5: _notes 列表中的对象 == _section.children 中的同一对象（引用相同，非拷贝）。"""

    def test_notes_references_same_as_children(self, list_model, section_with_notes):
        """_notes 中的对象引用与 _section.children 中一致。"""
        idx = list_model.index(0, 0)
        note_from_model = list_model.note_at(idx)

        # Find the same note in section.children by title
        notes_in_children = [c for c in section_with_notes.children if c.item_type == "note"]
        assert len(notes_in_children) > 0
        # The object reference should be the same (is, not ==)
        assert note_from_model is notes_in_children[0]

    def test_setdata_affects_both_cache_and_source(self, list_model, section_with_notes):
        """setData 修改 note.title 同时影响 _notes 缓存和 _section.children 源数据。"""
        idx = list_model.index(0, 0)
        list_model.setData(idx, "修改后标题", Qt.EditRole)

        # Check via model data
        assert list_model.data(idx, Qt.DisplayRole) == "修改后标题"

        # Check via section.children — same object, title should be updated
        notes_in_children = [c for c in section_with_notes.children if c.item_type == "note"]
        assert notes_in_children[0].title == "修改后标题"
