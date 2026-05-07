"""Tests for Header - .secnote 加密文件头组装与解析 (D-23)."""

import pytest

from src.secnotepad.crypto.header import HEADER_SIZE, MAGIC, VERSION, Header, HeaderError


class TestHeaderConstants:
    """文件头常量测试."""

    def test_header_size(self):
        """HEADER_SIZE == 69."""
        assert HEADER_SIZE == 69

    def test_magic(self):
        """MAGIC == b'SN02'."""
        assert MAGIC == b'SN02'

    def test_version(self):
        """VERSION == 1."""
        assert VERSION == 1


class TestHeaderBuild:
    """Header.build() 测试."""

    def test_build_header_length(self):
        """build_header(salt, iv, hmac_tag) 返回 bytes，长度 == 69."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        header = Header.build(salt, iv, hmac_tag)
        assert isinstance(header, bytes)
        assert len(header) == 69

    def test_build_header_magic(self):
        """前 4 字节为 b'SN02'."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        header = Header.build(salt, iv, hmac_tag)
        assert header[:4] == b'SN02'

    def test_build_header_version(self):
        """第 5 字节为 1."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        header = Header.build(salt, iv, hmac_tag)
        assert header[4] == 1

    def test_build_rejects_wrong_salt_length(self):
        """salt 不是 16 字节时抛出 AssertionError."""
        with pytest.raises(AssertionError):
            Header.build(b'\x00' * 15, b'\x01' * 16, b'\x02' * 32)

    def test_build_rejects_wrong_iv_length(self):
        """IV 不是 16 字节时抛出 AssertionError."""
        with pytest.raises(AssertionError):
            Header.build(b'\x00' * 16, b'\x01' * 15, b'\x02' * 32)

    def test_build_rejects_wrong_hmac_length(self):
        """HMAC tag 不是 32 字节时抛出 AssertionError."""
        with pytest.raises(AssertionError):
            Header.build(b'\x00' * 16, b'\x01' * 16, b'\x02' * 31)


class TestHeaderParse:
    """Header.parse() 测试."""

    def test_parse_header_roundtrip(self):
        """build → parse 返回相同 salt, iv, hmac_tag."""
        salt = b'\xAA' * 16
        iv = b'\xBB' * 16
        hmac_tag = b'\xCC' * 32
        header = Header.build(salt, iv, hmac_tag)
        result = Header.parse(header + b'extra_data')
        assert result['salt'] == salt
        assert result['iv'] == iv
        assert result['hmac_tag'] == hmac_tag

    def test_parse_header_ciphertext(self):
        """parse 正确提取头后的密文部分."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        ciphertext = b'\xDE\xAD\xBE\xEF'
        header = Header.build(salt, iv, hmac_tag)
        result = Header.parse(header + ciphertext)
        assert result['ciphertext'] == ciphertext

    def test_parse_header_empty_ciphertext(self):
        """头后无密文时 ciphertext 为空 bytes."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        header = Header.build(salt, iv, hmac_tag)
        result = Header.parse(header)
        assert result['ciphertext'] == b''

    def test_parse_header_roundtrip_version(self):
        """往返测试保留 version 字段."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        header = Header.build(salt, iv, hmac_tag)
        result = Header.parse(header + b'data')
        assert result['version'] == VERSION


class TestHeaderErrors:
    """Header.parse() 错误处理测试."""

    def test_parse_header_invalid_magic(self):
        """魔数不匹配时抛出 HeaderError."""
        # 用 'BAD' 替代 'SN02'
        bad_header = b'BAD\x00' + b'\x00' * 65
        with pytest.raises(HeaderError) as exc_info:
            Header.parse(bad_header)
        assert "魔数" in str(exc_info.value)

    def test_parse_header_short_data(self):
        """数据少于 69 字节时抛出 HeaderError."""
        with pytest.raises(HeaderError) as exc_info:
            Header.parse(b'\x00' * 68)
        assert "过短" in str(exc_info.value) or "短" in str(exc_info.value)

    def test_parse_header_unknown_version(self):
        """版本号 > 1 时不拒绝，返回实际版本号."""
        # 构建一个版本号为 2 的头部
        import struct
        data = struct.pack('!4s B 16s 16s 32s',
                          b'SN02', 2, b'\x00' * 16, b'\x00' * 16, b'\x00' * 32)
        result = Header.parse(data + b'cipher')
        assert result['version'] == 2
        assert result['ciphertext'] == b'cipher'

    def test_parse_header_error_is_exception(self):
        """HeaderError 是 Exception 的子类."""
        err = HeaderError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"

    def test_parse_header_exact_size_only_header(self):
        """恰好 69 字节（无密文）解析成功."""
        salt = b'\x00' * 16
        iv = b'\x01' * 16
        hmac_tag = b'\x02' * 32
        header = Header.build(salt, iv, hmac_tag)
        assert len(header) == 69
        result = Header.parse(header)
        assert result['salt'] == salt
        assert result['iv'] == iv
        assert result['hmac_tag'] == hmac_tag
        assert result['ciphertext'] == b''
