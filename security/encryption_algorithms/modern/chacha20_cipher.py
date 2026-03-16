from Crypto.Cipher import ChaCha20
from ..base_cipher import BaseCipher
from ..utils import b64encode_bytes, b64decode_str


class ChaCha20Cipher(BaseCipher):
    def __init__(self, key: bytes = b"1234567890ABCDEF1234567890ABCDEF", nonce: bytes = b"12345678"):
        if len(key) != 32:
            raise ValueError("La clave ChaCha20 debe tener 32 bytes.")
        if len(nonce) != 8:
            raise ValueError("El nonce ChaCha20 debe tener 8 bytes.")
        self.key = key
        self.nonce = nonce

    def encrypt(self, data: str) -> str:
        cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        encrypted = cipher.encrypt(data.encode("utf-8"))
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        encrypted = b64decode_str(data)
        decrypted = cipher.decrypt(encrypted)
        return decrypted.decode("utf-8")