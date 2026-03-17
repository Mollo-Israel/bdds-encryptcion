from Crypto.Cipher import DES
from ..base_cipher import BaseCipher
from ..utils import pad_pkcs7, unpad_pkcs7, b64encode_bytes, b64decode_str


class DESCipher(BaseCipher):
    def __init__(self, key: bytes = b"8bytekey"):
        if len(key) != 8:
            raise ValueError("La clave DES debe tener 8 bytes.")
        self.key = key
        self.block_size = DES.block_size

    def encrypt(self, data: str) -> str:
        cipher = DES.new(self.key, DES.MODE_ECB)
        padded = pad_pkcs7(data.encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        cipher = DES.new(self.key, DES.MODE_ECB)
        encrypted = b64decode_str(data)
        decrypted = cipher.decrypt(encrypted)
        unpadded = unpad_pkcs7(decrypted)
        return unpadded.decode("utf-8")