"""PageListModel - QAbstractListModel 子类，平铺展示分区下的页面列表 (D-50, D-54)。

将纯数据类 SNoteItem(section) 的 children 列表平铺为单列页面标题列表。
仅显示 item_type=="note" 的子节点，过滤掉 section 类型子节点。
支持原地重命名 (EditRole)、添加和删除页面。
数据/视图分离 (D-01)：数据源始终是 SNoteItem 对象。
"""

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from .snote_item import SNoteItem


class PageListModel(QAbstractListModel):
    """自定义列表模型，将分区下的 note 子节点平铺为页面列表 (D-50, D-54)。

    内部持有 _section 引用作为数据源，_notes 缓存列表中的元素
    与 _section.children 中的原始 SNoteItem 为同一对象引用 (Pitfall 5)。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._section: SNoteItem | None = None
        self._notes: list[SNoteItem] = []

    # ── 数据源管理 ──

    def set_section(self, section: SNoteItem | None):
        """设置当前分区并刷新 note 列表。

        使用 beginResetModel/endResetModel 进行完整模型重置。
        如果 section 为 None，清空列表。

        _notes 缓存中的元素 == _section.children 中的同一对象引用 (Pitfall 5)。
        """
        self.beginResetModel()
        self._section = section
        if section is not None:
            self._notes = [c for c in section.children if c.item_type == "note"]
        else:
            self._notes = []
        self.endResetModel()

    # ── QAbstractListModel 必需契约方法 ──

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """返回当前分区下 note 子节点的数量。

        仅计数 item_type == "note" 的子节点，忽略 section 子节点。
        """
        if parent.isValid():
            return 0
        return len(self._notes)

    def _is_valid_note_index(self, index: QModelIndex) -> bool:
        """Return True when index safely references a note in this model."""
        return (
            index.isValid()
            and index.model() is self
            and index.column() == 0
            and 0 <= index.row() < len(self._notes)
        )

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """返回索引处的数据显示。

        DisplayRole 和 EditRole 均返回页面标题 (D-54: 单列布局)。
        未实现的角色返回 None。
        """
        if not self._is_valid_note_index(index):
            return None

        note = self._notes[index.row()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            return note.title
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """返回索引的标志。

        有效索引: ItemIsEnabled | ItemIsSelectable | ItemIsEditable
        无效索引: NoItemFlags
        """
        if not self._is_valid_note_index(index):
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        """重命名页面标题 (EditRole, D-60)。

        D-60 空名称拒绝: 如果 value 为空字符串、纯空格或非 str 类型，返回 False。
        设置成功时发出 dataChanged 信号通知视图刷新。

        Pitfall 5: 直接修改 note.title，因为 _notes[i] IS _section.children[j]。
        """
        if role != Qt.EditRole:
            return False
        if not self._is_valid_note_index(index):
            return False
        # D-60: reject empty/non-string values
        if not isinstance(value, str) or value.strip() == "":
            return False

        note = self._notes[index.row()]
        new_title = value.strip()
        if note.title == new_title:
            return False
        note.title = new_title
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    # ── CRUD 数据变更接口 ──

    def add_note(self, note: SNoteItem) -> bool:
        """向当前分区追加新页面。

        同时更新 _section.children 源数据和 _notes 缓存。
        如果 _section 为 None，返回 False。
        """
        if self._section is None:
            return False
        if note.item_type != "note":
            return False

        row = len(self._notes)
        self.beginInsertRows(QModelIndex(), row, row)
        self._section.children.append(note)
        self._notes.append(note)
        self.endInsertRows()
        return True

    def remove_note(self, index: QModelIndex) -> bool:
        """从当前分区删除指定索引的页面。

        同时从 _section.children 源数据和 _notes 缓存中移除。
        返回 True 表示删除成功，False 表示索引无效。
        """
        if not self._is_valid_note_index(index):
            return False

        row = index.row()
        note = self._notes[row]
        source_row = -1
        for i, child in enumerate(self._section.children):
            if child is note:
                source_row = i
                break
        if source_row == -1:
            return False

        self.beginRemoveRows(QModelIndex(), row, row)
        del self._section.children[source_row]
        self._notes.pop(row)
        self.endRemoveRows()
        return True

    def note_at(self, index: QModelIndex) -> SNoteItem | None:
        """通过索引获取对应的 SNoteItem 对象。

        有效索引返回 SNoteItem，无效索引返回 None。
        """
        if not self._is_valid_note_index(index):
            return None
        return self._notes[index.row()]
