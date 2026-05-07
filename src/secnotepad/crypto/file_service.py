""".secnote 加密文件服务 — PBKDF2 + AES-256-CFB + HMAC-SHA256 完整编排。

密钥派生 (D-21, D-22):
- PBKDF2-SHA256, 16B salt, 600,000 iterations
- 两次独立派生：aes_key (32B) + hmac_key (32B), 不同 context 标签

加密流程 (D-24):
明文 JSON → HMAC-SHA256(明文) → AES-256-CFB 加密 → 文件头(魔数+版本+salt+IV+HMAC+密文)

解密流程 (D-24):
文件头解析 → 提取 salt+IV → 派生密钥 → AES-256-CFB 解密 → 验证 HMAC
"""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
from cryptography.hazmat.decrepit.ciphers.modes import CFB
from cryptography.hazmat.primitives import hmac as hmac_mod
from cryptography.hazmat.primitives.constant_time import bytes_eq

from .header import Header, HeaderError


# ── 密钥派生参数 (D-21, D-22) ──

SALT_SIZE = 16
IV_SIZE = 16
KEY_SIZE = 32
PBKDF2_ITERATIONS = 600_000
AES_CONTEXT = b'secnotepad-aes-key'
HMAC_CONTEXT = b'secnotepad-hmac-key'


class FileService:
    """加密文件服务 — 无状态静态方法编排。"""

    @staticmethod
    def _derive_keys(password: str, salt: bytes) -> tuple[bytes, bytes]:
        """派生 AES-256 密钥和 HMAC-SHA256 密钥。

        Args:
            password: 用户密码 (ASCII, 见 D-29)
            salt: 16 字节随机 salt

        Returns:
            (aes_key, hmac_key) 各 32 字节
        """
        password_bytes = password.encode('ascii')

        aes_kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        aes_key = aes_kdf.derive(password_bytes + AES_CONTEXT)

        hmac_kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        hmac_key = hmac_kdf.derive(password_bytes + HMAC_CONTEXT)

        return aes_key, hmac_key

    @staticmethod
    def _generate_iv() -> bytes:
        """生成 16 字节随机 IV。"""
        return os.urandom(IV_SIZE)

    @staticmethod
    def _generate_salt() -> bytes:
        """生成 16 字节随机 salt。"""
        return os.urandom(SALT_SIZE)

    @staticmethod
    def encrypt(plaintext: str, password: str) -> bytes:
        """加密明文 JSON 字符串，返回完整 .secnote 文件数据。

        Args:
            plaintext: 明文字符串（JSON 格式）
            password: 用户密码

        Returns:
            bytes: 完整文件数据（69B 头 + 密文）

        Raises:
            ValueError: 密码为空或包含非 ASCII 字符
        """
        if not password:
            raise ValueError("密码不能为空")
        if not password.isascii():
            raise ValueError("密码仅支持 ASCII 字符 (D-29)")

        plaintext_bytes = plaintext.encode('utf-8')
        salt = FileService._generate_salt()
        iv = FileService._generate_iv()
        aes_key, hmac_key = FileService._derive_keys(password, salt)

        # 先计算 HMAC (D-24)
        h = hmac_mod.HMAC(hmac_key, hashes.SHA256())
        h.update(plaintext_bytes)
        hmac_tag = h.finalize()

        # 再加密
        cipher = Cipher(algorithms.AES(aes_key), CFB(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()

        # 组装文件头 (D-23)
        header = Header.build(salt, iv, hmac_tag)

        return header + ciphertext

    @staticmethod
    def decrypt(file_data: bytes, password: str) -> str:
        """解密 .secnote 文件数据，返回明文 JSON 字符串。

        Args:
            file_data: 完整文件数据（69B 头 + 密文）
            password: 用户密码

        Returns:
            str: 明文 JSON 字符串

        Raises:
            ValueError: 密码错误、文件格式无效或数据被篡改
        """
        if not password:
            raise ValueError("密码不能为空")

        try:
            parsed = Header.parse(file_data)
        except HeaderError as e:
            raise ValueError(f"无效的文件格式: {e}") from e

        salt = parsed['salt']
        iv = parsed['iv']
        stored_hmac = parsed['hmac_tag']
        ciphertext = parsed['ciphertext']

        aes_key, hmac_key = FileService._derive_keys(password, salt)

        # 先解密
        cipher = Cipher(algorithms.AES(aes_key), CFB(iv))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # 验证 HMAC (D-24, 常量时间比较)
        h = hmac_mod.HMAC(hmac_key, hashes.SHA256())
        h.update(plaintext)
        computed_hmac = h.finalize()

        if not bytes_eq(computed_hmac, stored_hmac):
            raise ValueError("密码错误")

        return plaintext.decode('utf-8')

    @staticmethod
    def save(plaintext: str, path: str, password: str):
        """加密并写入文件到磁盘。

        Args:
            plaintext: 明文 JSON 字符串
            path: 文件保存路径
            password: 用户密码
        """
        data = FileService.encrypt(plaintext, password)
        with open(path, 'wb') as f:
            f.write(data)

    @staticmethod
    def open(path: str, password: str) -> str:
        """从磁盘读取并解密文件。

        Args:
            path: 文件路径
            password: 用户密码

        Returns:
            str: 明文 JSON 字符串

        Raises:
            ValueError: 密码错误或文件格式无效
            FileNotFoundError: 文件不存在
        """
        with open(path, 'rb') as f:
            data = f.read()
        return FileService.decrypt(data, password)

    @staticmethod
    def save_as(plaintext: str, path: str, password: str):
        """另存为的别名 — 行为与 save 相同，但语义上表示新路径/新密码。

        实际另存为流程（生成新 salt+IV）已由 encrypt() 内部的
        _generate_salt() 和 _generate_iv() 隐式完成 (D-28)。
        """
        FileService.save(plaintext, path, password)
