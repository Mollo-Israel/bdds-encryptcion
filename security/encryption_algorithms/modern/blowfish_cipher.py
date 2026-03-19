import base64

from Crypto.Cipher import Blowfish
from Crypto.Util.Padding import pad, unpad

from security.encryption_algorithms.base_cipher import BaseCipher


class BlowfishCipher(BaseCipher):
    def __init__(self, key: str = "PRODEM_KEY_2026"):
        key_bytes = key.encode("utf-8")

        if len(key_bytes) < 4:
            key_bytes = key_bytes.ljust(4, b"0")
        elif len(key_bytes) > 56:
            key_bytes = key_bytes[:56]

        self.key = key_bytes
        self.block_size = Blowfish.block_size

    def encrypt(self, data: str) -> str:
        cipher = Blowfish.new(self.key, Blowfish.MODE_ECB)
        padded = pad(str(data).encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode("utf-8")

    def decrypt(self, data: str) -> str:
        cipher = Blowfish.new(self.key, Blowfish.MODE_ECB)
        encrypted_bytes = base64.b64decode(data.encode("utf-8"))
        decrypted = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted, self.block_size).decode("utf-8")