"""Validator - SNoteItem 层级约束校验工具 (D-06, D-07)。

职责分离 (D-06)：
- SNoteItem: 纯数据类
- Serializer: JSON 序列化/反序列化
- Validator: 规则校验

层级约束 (D-07)：
- Section 可无限嵌套 Section + 包含 Note
- Note 为叶子节点，不可有 children
"""

from typing import Optional

from .snote_item import SNoteItem


class ValidationError(Exception):
    """SNoteItem 校验失败时抛出的异常。"""

    pass


class Validator:
    """SNoteItem 规则校验器。

    所有方法为静态方法，不维护状态。
    """

    @staticmethod
    def validate(item: SNoteItem) -> Optional[ValidationError]:
        """校验 SNoteItem 是否符合层级约束 (D-07)。

        Args:
            item: 待校验的 SNoteItem

        Returns:
            None 表示校验通过
            ValidationError 表示校验失败，异常消息描述原因
        """
        if item.item_type == "note" and item.children:
            return ValidationError(
                f"Note '{item.title}' cannot have children"
            )
        if item.item_type == "section":
            for child in item.children:
                err = Validator.validate(child)
                if err:
                    return err
        return None
