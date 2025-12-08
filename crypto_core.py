"""
文件加密/解密核心模块
使用 AES-256-GCM 加密算法

特性：
- AES-256-GCM 军事级加密
- PBKDF2 密钥派生（防暴力破解）
- 支持进度回调（大文件处理）
"""

import os
import secrets
from typing import Callable, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


class FileEncryptor:
    """文件加密器类"""
    
    # 常量配置
    SALT_LENGTH = 16        # 盐值长度（字节）
    NONCE_LENGTH = 12       # 随机数长度（字节）
    ITERATIONS = 100_000    # PBKDF2 迭代次数
    CHUNK_SIZE = 64 * 1024  # 分块读取大小（64KB）
    
    def __init__(self, password: str):
        """
        初始化加密器
        
        :param password: 用户密码
        """
        self.password = password.encode('utf-8')
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        从密码派生256位密钥
        
        :param salt: 盐值
        :return: 32字节密钥
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(self.password)
    
    def encrypt_file(
        self, 
        input_path: str, 
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        加密文件
        
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径
        :param progress_callback: 进度回调函数 (current, total)
        :return: 输出文件路径
        """
        # 生成随机盐值和nonce
        salt = secrets.token_bytes(self.SALT_LENGTH)
        nonce = secrets.token_bytes(self.NONCE_LENGTH)
        
        # 派生密钥
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        
        # 获取文件大小
        file_size = os.path.getsize(input_path)
        
        # 读取整个文件（AES-GCM需要一次性加密）
        plaintext = bytearray()
        bytes_read = 0
        
        with open(input_path, 'rb') as f:
            while True:
                chunk = f.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                plaintext.extend(chunk)
                bytes_read += len(chunk)
                
                if progress_callback:
                    # 读取阶段占50%进度
                    progress_callback(bytes_read // 2, file_size)
        
        # 加密
        ciphertext = aesgcm.encrypt(nonce, bytes(plaintext), None)
        
        if progress_callback:
            progress_callback(file_size * 3 // 4, file_size)
        
        # 写入加密文件：盐值 + nonce + 密文
        with open(output_path, 'wb') as f:
            f.write(salt + nonce + ciphertext)
        
        if progress_callback:
            progress_callback(file_size, file_size)
        
        return output_path
    
    def decrypt_file(
        self, 
        input_path: str, 
        output_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        解密文件
        
        :param input_path: 加密文件路径
        :param output_path: 输出文件路径
        :param progress_callback: 进度回调函数 (current, total)
        :return: 输出文件路径
        :raises: InvalidTag 如果密码错误
        :raises: ValueError 如果文件格式无效
        """
        # 获取文件大小
        file_size = os.path.getsize(input_path)
        
        # 验证文件大小（至少需要 salt + nonce + 16字节认证标签）
        min_size = self.SALT_LENGTH + self.NONCE_LENGTH + 16
        if file_size < min_size:
            raise ValueError("文件格式无效或已损坏")
        
        # 读取加密文件
        data = bytearray()
        bytes_read = 0
        
        with open(input_path, 'rb') as f:
            while True:
                chunk = f.read(self.CHUNK_SIZE)
                if not chunk:
                    break
                data.extend(chunk)
                bytes_read += len(chunk)
                
                if progress_callback:
                    progress_callback(bytes_read // 2, file_size)
        
        data = bytes(data)
        
        # 提取盐值、nonce和密文
        salt = data[:self.SALT_LENGTH]
        nonce = data[self.SALT_LENGTH:self.SALT_LENGTH + self.NONCE_LENGTH]
        ciphertext = data[self.SALT_LENGTH + self.NONCE_LENGTH:]
        
        # 派生密钥
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        
        if progress_callback:
            progress_callback(file_size * 3 // 4, file_size)
        
        # 解密（密码错误会抛出 InvalidTag 异常）
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        # 写入解密文件
        with open(output_path, 'wb') as f:
            f.write(plaintext)
        
        if progress_callback:
            progress_callback(file_size, file_size)
        
        return output_path

