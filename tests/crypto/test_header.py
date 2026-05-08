"""Tests for Header - .secnote 加密文件头组装与解析 (D-23)."""

import pytest

from src.secnotepad.crypto.header import HEADER_SIZE, MAGIC, VERSION, Header, HeaderError


class TestHeaderConstants:
    """文件头常量测试."""

    def test_header_size(self):
        """HEADER_SIZE == 49 (GCM format)."""
        assert HEADER_SIZE == 49

    def test_magic(self):
        """MAGIC == b'SN02'."""
        assert MAGIC == b'SN02'

    def test_version(self):
        """VERSION == 2 (AES-GCM)."""
        assert VERSION == 2


class TestHeaderBuild:
    """Header.build() 测试."""

    def test_build_header_length(self):
        """build(salt, nonce, tag) 返回 bytes，长度 == 49."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        header = Header.build(salt, nonce, tag)
        assert isinstance(header, bytes)
        assert len(header) == 49

    def test_build_header_magic(self):
        """前 4 字节为 b'SN02'."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        header = Header.build(salt, nonce, tag)
        assert header[:4] == b'SN02'

    def test_build_header_version(self):
        """第 5 字节为 2."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        header = Header.build(salt, nonce, tag)
        assert header[4] == 2

    def test_build_rejects_wrong_salt_length(self):
        """salt 不是 16 字节时抛出 HeaderError."""
        with pytest.raises(HeaderError):
            Header.build(b'\x00' * 15, b'\x01' * 12, b'\x02' * 16)

    def test_build_rejects_wrong_nonce_length(self):
        """nonce 不是 12 字节时抛出 HeaderError."""
        with pytest.raises(HeaderError):
            Header.build(b'\x00' * 16, b'\x01' * 11, b'\x02' * 16)

    def test_build_rejects_wrong_tag_length(self):
        """tag 不是 16 字节时抛出 HeaderError."""
        with pytest.raises(HeaderError):
            Header.build(b'\x00' * 16, b'\x01' * 12, b'\x02' * 15)


class TestHeaderParse:
    """Header.parse() 测试."""

    def test_parse_header_roundtrip(self):
        """build -> parse 返回相同 salt, nonce, tag."""
        salt = b'\xAA' * 16
        nonce = b'\xBB' * 12
        tag = b'\xCC' * 16
        header = Header.build(salt, nonce, tag)
        result = Header.parse(header + b'extra_data')
        assert result['salt'] == salt
        assert result['nonce'] == nonce
        assert result['tag'] == tag

    def test_parse_header_ciphertext(self):
        """parse 正确提取头后的密文部分."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        ciphertext = b'\xDE\xAD\xBE\xEF'
        header = Header.build(salt, nonce, tag)
        result = Header.parse(header + ciphertext)
        assert result['ciphertext'] == ciphertext

    def test_parse_header_empty_ciphertext(self):
        """头后无密文时 ciphertext 为空 bytes."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        header = Header.build(salt, nonce, tag)
        result = Header.parse(header)
        assert result['ciphertext'] == b''

    def test_parse_header_roundtrip_version(self):
        """往返测试保留 version 字段."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        header = Header.build(salt, nonce, tag)
        result = Header.parse(header + b'data')
        assert result['version'] == VERSION


class TestHeaderErrors:
    """Header.parse() 错误处理测试."""

    def test_parse_header_invalid_magic(self):
        """魔数不匹配时抛出 HeaderError."""
        # 用 'BAD' 替代 'SN02'
        bad_header = b'BAD\x00' + b'\x00' * 45
        with pytest.raises(HeaderError) as exc_info:
            Header.parse(bad_header)
        assert "魔数" in str(exc_info.value)

    def test_parse_header_short_data(self):
        """数据少于 49 字节时抛出 HeaderError."""
        with pytest.raises(HeaderError) as exc_info:
            Header.parse(b'\x00' * 48)
        assert "过短" in str(exc_info.value) or "短" in str(exc_info.value)

    def test_parse_header_unknown_version(self):
        """版本号 > 2 时不拒绝，返回实际版本号."""
        import struct
        data = struct.pack('!4s B 16s 12s 16s',
                          b'SN02', 3, b'\x00' * 16, b'\x00' * 12, b'\x00' * 16)
        result = Header.parse(data + b'cipher')
        assert result['version'] == 3
        assert result['ciphertext'] == b'cipher'

    def test_parse_header_error_is_exception(self):
        """HeaderError 是 Exception 的子类."""
        err = HeaderError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"

    def test_parse_header_exact_size_only_header(self):
        """恰好 49 字节（无密文）解析成功."""
        salt = b'\x00' * 16
        nonce = b'\x01' * 12
        tag = b'\x02' * 16
        header = Header.build(salt, nonce, tag)
        assert len(header) == 49
        result = Header.parse(header)
        assert result['salt'] == salt
        assert result['nonce'] == nonce
        assert result['tag'] == tag
        assert result['ciphertext'] == b''
