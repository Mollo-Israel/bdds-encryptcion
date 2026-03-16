from Crypto.Cipher import Blowfish
from ..base_cipher import BaseCipher
from ..utils import pad_pkcs7, unpad_pkcs7, b64encode_bytes, b64decode_str


class BlowfishCipher(BaseCipher):
    def __init__(self, key: bytes = b"blowfish_key"):
        if not (4 <= len(key) <= 56):
            raise ValueError("La clave Blowfish debe tener entre 4 y 56 bytes.")
        self.key = key
        self.block_size = Blowfish.block_size

    def encrypt(self, data: str) -> str:
        cipher = Blowfish.new(self.key, Blowfish.MODE_ECB)
        padded = pad_pkcs7(data.encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        cipher = Blowfish.new(self.key, Blowfish.MODE_ECB)
        encrypted = b64decode_str(data)
        decrypted = cipher.decrypt(encrypted)
        unpadded = unpad_pkcs7(decrypted)
        return unpadded.decode("utf-8")