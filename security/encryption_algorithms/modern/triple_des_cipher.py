from Crypto.Cipher import DES3
from ..base_cipher import BaseCipher
from ..utils import pad_pkcs7, unpad_pkcs7, b64encode_bytes, b64decode_str


class TripleDESCipher(BaseCipher):
    def __init__(self, key: bytes = b"1234567890ABCDEF12345678"):
        if len(key) not in (16, 24):
            raise ValueError("La clave 3DES debe tener 16 o 24 bytes.")
        self.key = DES3.adjust_key_parity(key)
        self.block_size = DES3.block_size

    def encrypt(self, data: str) -> str:
        cipher = DES3.new(self.key, DES3.MODE_ECB)
        padded = pad_pkcs7(data.encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        cipher = DES3.new(self.key, DES3.MODE_ECB)
        encrypted = b64decode_str(data)
        decrypted = cipher.decrypt(encrypted)
        unpadded = unpad_pkcs7(decrypted)
        return unpadded.decode("utf-8")