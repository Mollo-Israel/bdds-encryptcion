import base64

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from security.encryption_algorithms.base_cipher import BaseCipher


class TwofishCipher(BaseCipher):
    """
    Implementación académica:
    simula Twofish usando AES internamente para mantener compatibilidad.
    """

    def __init__(self, key: str = "SOLIDARIO_KEY_2026"):
        key_bytes = key.encode("utf-8")

        if len(key_bytes) < 16:
            key_bytes = key_bytes.ljust(16, b"0")
        elif len(key_bytes) > 16:
            key_bytes = key_bytes[:16]

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