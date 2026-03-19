import base64

from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad

from security.encryption_algorithms.base_cipher import BaseCipher


class DESCipher(BaseCipher):
    def __init__(self, key: str = "G4N4D3R0"):
        key_bytes = key.encode("utf-8")

        if len(key_bytes) < 8:
            key_bytes = key_bytes.ljust(8, b"0")
        elif len(key_bytes) > 8:
            key_bytes = key_bytes[:8]

        self.key = key_bytes

    def encrypt(self, data: str) -> str:
        cipher = DES.new(self.key, DES.MODE_ECB)
        padded = pad(str(data).encode("utf-8"), DES.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, data: str) -> str:
        cipher = DES.new(self.key, DES.MODE_ECB)
        encrypted_bytes = base64.b64decode(data.encode("utf-8"))
        decrypted = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted, DES.block_size).decode("utf-8")