""".secnote 加密文件头定义与组装/解析 (D-23)."""

import struct

MAGIC = b'SN02'
VERSION = 2
HEADER_SIZE = 49  # 4 + 1 + 16 + 12 + 16


class HeaderError(Exception):
    """文件头解析失败时抛出的异常。"""

    pass


class Header:
    """文件头组装与解析。所有方法为静态方法，不维护状态。"""

    @staticmethod
    def build(salt: bytes, nonce: bytes, tag: bytes) -> bytes:
        """组装 49 字节文件头 (AES-GCM 版本)。

        Args:
            salt: 16 字节随机 salt
            nonce: 12 字节 GCM nonce
            tag: 16 字节 GCM 认证标签

        Returns:
            49 字节二进制文件头

        Raises:
            HeaderError: 如果任意参数长度不符合要求
        """
        if len(salt) != 16:
            raise HeaderError(f"salt must be 16 bytes, got {len(salt)}")
        if len(nonce) != 12:
            raise HeaderError(f"nonce must be 12 bytes, got {len(nonce)}")
        if len(tag) != 16:
            raise HeaderError(f"tag must be 16 bytes, got {len(tag)}")
        return struct.pack(
            '!4s B 16s 12s 16s',
            MAGIC, VERSION, salt, nonce, tag,
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
        magic, version, salt, nonce, tag = struct.unpack(
            '!4s B 16s 12s 16s', data[:HEADER_SIZE]
        )
        if magic != MAGIC:
            raise HeaderError(f"无效的魔数: {magic!r}")
        return {
            'version': version,
            'salt': salt,
            'nonce': nonce,
            'tag': tag,
            'ciphertext': data[HEADER_SIZE:],
        }
