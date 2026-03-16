from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from ..base_cipher import BaseCipher
from ..utils import b64encode_bytes, b64decode_str


class RSACipher(BaseCipher):
    def __init__(self, key_size: int = 2048):
        self.key = RSA.generate(key_size)
        self.public_key = self.key.publickey()
        self.encrypt_cipher = PKCS1_OAEP.new(self.public_key)
        self.decrypt_cipher = PKCS1_OAEP.new(self.key)

    def encrypt(self, data: str) -> str:
        encrypted = self.encrypt_cipher.encrypt(data.encode("utf-8"))
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        encrypted = b64decode_str(data)
        decrypted = self.decrypt_cipher.decrypt(encrypted)
        return decrypted.decode("utf-8")