""".secnote 加密文件服务 — PBKDF2 + AES-256-GCM 完整编排。

密钥派生 (D-21, D-22):
- PBKDF2-SHA256, 16B salt, 600,000 iterations
- 派生单一 AES-256 密钥（GCM 提供认证加密，无需独立 HMAC）

加密流程 (D-24):
明文 JSON → AES-256-GCM 加密 → 文件头(魔数+版本+salt+nonce+tag+密文)

解密流程 (D-24):
文件头解析 → 提取 salt+nonce → 派生密钥 → AES-256-GCM 解密（含认证验证）
"""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.exceptions import InvalidTag

from .header import Header, HeaderError


# ── 密钥派生参数 (D-21, D-22) ──

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
PBKDF2_ITERATIONS = 600_000
PBKDF2_CONTEXT = b'secnotepad-aes-key'


class FileService:
    """加密文件服务 — 无状态静态方法编排。"""

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        """派生 AES-256 密钥。

        Args:
            password: 用户密码 (ASCII, 见 D-29)
            salt: 16 字节随机 salt

        Returns:
            32 字节 AES-256 密钥
        """
        password_bytes = password.encode('ascii')

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        return kdf.derive(password_bytes + PBKDF2_CONTEXT)

    @staticmethod
    def _generate_nonce() -> bytes:
        """生成 12 字节随机 GCM nonce。"""
        return os.urandom(NONCE_SIZE)

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
            bytes: 完整文件数据（49B 头 + 密文）

        Raises:
            ValueError: 密码为空或包含非 ASCII 字符
        """
        if not password:
            raise ValueError("密码不能为空")
        if not password.isascii():
            raise ValueError("密码仅支持 ASCII 字符 (D-29)")

        plaintext_bytes = plaintext.encode('utf-8')
        salt = FileService._generate_salt()
        nonce = FileService._generate_nonce()
        key = FileService._derive_key(password, salt)

        # AES-256-GCM 加密 (内置认证，无需独立 HMAC)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()
        tag = encryptor.tag  # 16 字节认证标签

        # 组装文件头 (D-23)
        header = Header.build(salt, nonce, tag)

        return header + ciphertext

    @staticmethod
    def decrypt(file_data: bytes, password: str) -> str:
        """解密 .secnote 文件数据，返回明文 JSON 字符串。

        Args:
            file_data: 完整文件数据（49B 头 + 密文）
            password: 用户密码

        Returns:
            str: 明文 JSON 字符串

        Raises:
            ValueError: 密码错误、文件格式无效或数据被篡改
        """
        if not password:
            raise ValueError("密码不能为空")
        if not password.isascii():
            raise ValueError("密码仅支持 ASCII 字符 (D-29)")

        try:
            parsed = Header.parse(file_data)
        except HeaderError as e:
            raise ValueError(f"无效的文件格式: {e}") from e

        salt = parsed['salt']
        nonce = parsed['nonce']
        stored_tag = parsed['tag']
        ciphertext = parsed['ciphertext']

        key = FileService._derive_key(password, salt)

        # AES-256-GCM 解密（内置认证验证）
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        decryptor = cipher.decryptor()
        try:
            plaintext = decryptor.update(ciphertext) + decryptor.finalize_with_tag(stored_tag)
        except InvalidTag as e:
            raise ValueError("密码错误") from e

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

        实际另存为流程（生成新 salt+nonce）已由 encrypt() 内部的
        _generate_salt() 和 _generate_nonce() 隐式完成 (D-28)。
        """
        FileService.save(plaintext, path, password)
