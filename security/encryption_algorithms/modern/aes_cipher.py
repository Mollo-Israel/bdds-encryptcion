import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from security.encryption_algorithms.base_cipher import BaseCipher


class AESCipher(BaseCipher):
    def __init__(self, key: str = "FORTALEZA_AES_KEY_2026_32_BYTES!!"):
        key_bytes = key.encode("utf-8")

        if len(key_bytes) <= 16:
            target = 16
        elif len(key_bytes) <= 24:
            target = 24
        else:
            target = 32

        if len(key_bytes) < target:
            key_bytes = key_bytes.ljust(target, b"0")
        elif len(key_bytes) > target:
            key_bytes = key_bytes[:target]

        self.key = key_bytes
        self.block_size = AES.block_size

    def encrypt(self, data: str) -> str:
        cipher = AES.new(self.key, AES.MODE_ECB)
        padded = pad(str(data).encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, data: str) -> str:
        cipher = AES.new(self.key, AES.MODE_ECB)
        encrypted_bytes = base64.b64decode(data.encode("utf-8"))
        decrypted = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted, self.block_size).decode("utf-8")