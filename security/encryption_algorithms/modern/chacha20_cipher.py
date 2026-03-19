from Crypto.Cipher import ChaCha20

from ..base_cipher import BaseCipher
from ..utils import b64encode_bytes, b64decode_str


class ChaCha20Cipher(BaseCipher):
    def __init__(
        self,
        key: str | bytes = "1234567890ABCDEF1234567890ABCDEF",
        nonce: str | bytes = "12345678",
    ):
        self.key = self._to_bytes(key, "clave")
        self.nonce = self._to_bytes(nonce, "nonce")

        if len(self.key) != 32:
            raise ValueError(
                f"La clave ChaCha20 debe tener 32 bytes. Actual: {len(self.key)} bytes."
            )

        if len(self.nonce) not in (8, 12, 24):
            raise ValueError(
                f"El nonce ChaCha20 debe tener 8, 12 o 24 bytes. Actual: {len(self.nonce)} bytes."
            )

    @staticmethod
    def _to_bytes(value: str | bytes, field_name: str) -> bytes:
        if isinstance(value, bytes):
            return value

        if isinstance(value, str):
            return value.encode("utf-8")

        raise TypeError(
            f"El campo '{field_name}' para ChaCha20 debe ser str o bytes, no {type(value).__name__}."
        )

    def encrypt(self, data: str) -> str:
        cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        encrypted = cipher.encrypt(str(data).encode("utf-8"))
        return b64encode_bytes(encrypted)

    def decrypt(self, data: str) -> str:
        cipher = ChaCha20.new(key=self.key, nonce=self.nonce)
        encrypted = b64decode_str(data)
        decrypted = cipher.decrypt(encrypted)
        return decrypted.decode("utf-8")