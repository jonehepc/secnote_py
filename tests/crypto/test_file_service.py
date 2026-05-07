"""Tests for FileService — 加密/解密/保存/打开 roundtrip."""

import json
import pytest

from src.secnotepad.crypto.file_service import FileService
from src.secnotepad.crypto.header import Header, HEADER_SIZE


# ── 纯加密/解密测试 ──


class TestEncryptDecrypt:
    """加密/解密 roundtrip (CRYPT-03)."""

    def test_encrypt_decrypt_roundtrip(self, sample_json_str, test_password):
        """加密再解密还原原文。"""
        encrypted = FileService.encrypt(sample_json_str, test_password)
        decrypted = FileService.decrypt(encrypted, test_password)
        assert decrypted == sample_json_str

    def test_encrypt_output_has_header(self, sample_json_str, test_password):
        """加密输出以 SN02 魔数开头。"""
        encrypted = FileService.encrypt(sample_json_str, test_password)
        assert encrypted[:4] == b'SN02'
        assert len(encrypted) >= HEADER_SIZE

    def test_encrypt_output_not_readable(self, sample_json_str, test_password):
        """加密输出不含明文内容。"""
        encrypted = FileService.encrypt(sample_json_str, test_password)
        plaintext_bytes = sample_json_str.encode('utf-8')
        assert plaintext_bytes not in encrypted

    def test_decrypt_wrong_password(self, sample_json_str, test_password):
        """错误密码抛出 ValueError。"""
        encrypted = FileService.encrypt(sample_json_str, test_password)
        with pytest.raises(ValueError, match="密码错误"):
            FileService.decrypt(encrypted, "WrongP@ss1")

    def test_encrypt_empty_string(self, test_password):
        """加密空字符串。"""
        encrypted = FileService.encrypt("", test_password)
        decrypted = FileService.decrypt(encrypted, test_password)
        assert decrypted == ""

    def test_decrypt_empty_data(self, test_password):
        """解密空数据抛出 ValueError。"""
        with pytest.raises(ValueError, match="无效的文件格式|数据过短"):
            FileService.decrypt(b"", test_password)


# ── 文件保存/打开 roundtrip ──


class TestFileSaveOpen:
    """保存到文件再打开 (FILE-02, FILE-03)."""

    def test_save_and_open_roundtrip(self, sample_json_str, test_password, tmp_path):
        """保存到文件再打开还原原文。"""
        file_path = tmp_path / "test.secnote"
        FileService.save(sample_json_str, str(file_path), test_password)
        result = FileService.open(str(file_path), test_password)
        assert result == sample_json_str

    def test_save_creates_file(self, sample_json_str, test_password, tmp_path):
        """保存后在磁盘上存在文件。"""
        file_path = tmp_path / "exists.secnote"
        FileService.save(sample_json_str, str(file_path), test_password)
        assert file_path.exists()
        assert file_path.stat().st_size >= HEADER_SIZE

    def test_open_wrong_password(self, sample_json_str, test_password, tmp_path):
        """用错误密码打开文件抛出 ValueError。"""
        file_path = tmp_path / "wrong.secnote"
        FileService.save(sample_json_str, str(file_path), test_password)
        with pytest.raises(ValueError, match="密码错误"):
            FileService.open(str(file_path), "WrongP@ss1")

    def test_open_nonexistent_file(self, tmp_path):
        """打开不存在的文件抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            FileService.open(str(tmp_path / "nonexist.secnote"), "pw")


# ── 另存为测试 ──


class TestSaveAs:
    """另存为功能 (FILE-04, D-28)."""

    def test_save_as_new_path(self, sample_json_str, test_password, tmp_path):
        """另存为新路径可正常打开。"""
        path1 = tmp_path / "original.secnote"
        path2 = tmp_path / "saveas.secnote"
        FileService.save(sample_json_str, str(path1), test_password)
        FileService.save_as(sample_json_str, str(path2), test_password)
        result = FileService.open(str(path2), test_password)
        assert result == sample_json_str

    def test_save_as_new_password(self, sample_json_str, test_password, tmp_path):
        """另存为并更换密码后，旧密码无法打开新文件。"""
        path = tmp_path / "newpw.secnote"
        new_password = "NewP@ss456"
        FileService.save_as(sample_json_str, str(path), new_password)
        # 新密码可打开
        result = FileService.open(str(path), new_password)
        assert result == sample_json_str
        # 旧密码不可打开
        with pytest.raises(ValueError, match="密码错误"):
            FileService.open(str(path), test_password)


# ── 边界情况 ──


class TestEdgeCases:
    """边界情况测试。"""

    def test_tampered_ciphertext(self, sample_json_str, test_password):
        """篡改密文后解密失败。"""
        encrypted = bytearray(FileService.encrypt(sample_json_str, test_password))
        # 翻转密文部分的一个字节
        encrypted[70] ^= 0xFF
        with pytest.raises(ValueError, match="密码错误"):
            FileService.decrypt(bytes(encrypted), test_password)

    def test_tampered_header_magic(self, sample_json_str, test_password):
        """篡改魔数后解密失败。"""
        encrypted = bytearray(FileService.encrypt(sample_json_str, test_password))
        encrypted[0] = ord('X')
        with pytest.raises(ValueError, match="无效的文件格式"):
            FileService.decrypt(bytes(encrypted), test_password)

    def test_tampered_hmac(self, sample_json_str, test_password):
        """篡改 HMAC tag 后解密失败。"""
        encrypted = bytearray(FileService.encrypt(sample_json_str, test_password))
        # HMAC 位于文件头 37-68 字节
        encrypted[40] ^= 0xFF
        with pytest.raises(ValueError, match="密码错误"):
            FileService.decrypt(bytes(encrypted), test_password)

    def test_empty_password_raises(self, sample_json_str):
        """空密码抛出 ValueError。"""
        with pytest.raises(ValueError, match="密码不能为空"):
            FileService.encrypt(sample_json_str, "")
