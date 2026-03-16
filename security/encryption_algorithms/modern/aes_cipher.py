from Crypto.Cipher import AES
from ..base_cipher import BaseCipher
from ..utils import pad_pkcs7, unpad_pkcs7, b64encode_bytes, b64decode_str


class AESCipher(BaseCipher):
    def __init__(self, key: bytes = b"1234567890ABCDEF"):
        if len(key) not in (16, 24, 32):
            raise ValueError("La clave AES debe tener 16, 24 o 32 bytes.")
        self.key = key
        self.block_size = AES.block_size

    def encrypt(self, data: str) -> str:
        cipher = AES.new(self.key, AES.MODE_ECB)
        padded = pad_pkcs7(data.encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        cipher = AES.new(self.key, AES.MODE_ECB)
        encrypted = b64decode_str(data)
        decrypted = cipher.decrypt(encrypted)
        unpadded = unpad_pkcs7(decrypted)
        return unpadded.decode("utf-8")