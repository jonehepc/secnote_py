""".secnote 加密文件头定义与组装/解析 (D-23)."""

import struct

MAGIC = b'SN02'
VERSION = 1
HEADER_SIZE = 69  # 4 + 1 + 16 + 16 + 32


class HeaderError(Exception):
    """文件头解析失败时抛出的异常。"""

    pass


class Header:
    """文件头组装与解析。所有方法为静态方法，不维护状态。"""

    @staticmethod
    def build(salt: bytes, iv: bytes, hmac_tag: bytes) -> bytes:
        """组装 69 字节文件头。

        Args:
            salt: 16 字节随机 salt
            iv: 16 字节初始化向量
            hmac_tag: 32 字节 HMAC 标签

        Returns:
            69 字节二进制文件头

        Raises:
            HeaderError: 如果任意参数长度不符合要求
        """
        if len(salt) != 16:
            raise HeaderError(f"salt must be 16 bytes, got {len(salt)}")
        if len(iv) != 16:
            raise HeaderError(f"IV must be 16 bytes, got {len(iv)}")
        if len(hmac_tag) != 32:
            raise HeaderError(f"HMAC tag must be 32 bytes, got {len(hmac_tag)}")
        return struct.pack(
            '!4s B 16s 16s 32s',
            MAGIC, VERSION, salt, iv, hmac_tag,
        )

    @staticmethod
    def parse(data: bytes) -> dict:
        """解析文件头，返回各部分字典。

        Args:
            data: 完整的文件数据（头 + 密文）

        Returns:
            dict with keys: version, salt, iv, hmac_tag, ciphertext

        Raises:
            HeaderError: 魔数无效或数据长度不足。
        """
        if len(data) < HEADER_SIZE:
            raise HeaderError(
                f"数据过短: {len(data)} 字节, 需要至少 {HEADER_SIZE}"
            )
        magic, version, salt, iv, hmac_tag = struct.unpack(
            '!4s B 16s 16s 32s', data[:HEADER_SIZE]
        )
        if magic != MAGIC:
            raise HeaderError(f"无效的魔数: {magic!r}")
        return {
            'version': version,
            'salt': salt,
            'iv': iv,
            'hmac_tag': hmac_tag,
            'ciphertext': data[HEADER_SIZE:],
        }
