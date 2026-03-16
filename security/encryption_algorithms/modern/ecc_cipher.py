from Crypto.PublicKey import ECC
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from ..base_cipher import BaseCipher
from ..utils import pad_pkcs7, unpad_pkcs7, b64encode_bytes, b64decode_str


class ECCCipher(BaseCipher):
    def __init__(self):
        self.private_key = ECC.generate(curve="P-256")
        self.public_key = self.private_key.public_key()
        self.block_size = 16

    def _derive_key(self, public_key_bytes: bytes) -> bytes:
        digest = SHA256.new(public_key_bytes).digest()
        return digest[:16]

    def encrypt(self, data: str) -> str:
        ephemeral_key = ECC.generate(curve="P-256")
        ephemeral_public = ephemeral_key.public_key().export_key(format="DER")

        aes_key = self._derive_key(ephemeral_public)
        cipher = AES.new(aes_key, AES.MODE_ECB)

        padded = pad_pkcs7(data.encode("utf-8"), self.block_size)
        encrypted = cipher.encrypt(padded)

        payload = len(ephemeral_public).to_bytes(2, "big") + ephemeral_public + encrypted
        return b64encode_bytes(payload)

    def decrypt(self, data: str) -> str:
        payload = b64decode_str(data)

        pub_len = int.from_bytes(payload[:2], "big")
        ephemeral_public = payload[2:2 + pub_len]
        encrypted = payload[2 + pub_len:]

        aes_key = self._derive_key(ephemeral_public)
        cipher = AES.new(aes_key, AES.MODE_ECB)

        decrypted = cipher.decrypt(encrypted)
        return unpad_pkcs7(decrypted).decode("utf-8")