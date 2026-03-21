import hashlib

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from ..base_cipher import BaseCipher
from ..utils import b64encode_bytes, b64decode_str


def _seeded_randfunc(seed: str):
    """
    Genera bytes pseudo-aleatorios deterministas a partir de `seed`.
    SHA-256 en modo contador: mismo seed → misma secuencia → mismo par RSA
    en cualquier proceso, sin importar el momento del arranque.
    """
    seed_bytes = hashlib.sha256(seed.encode("utf-8")).digest()
    counter = [0]

    def randfunc(n: int) -> bytes:
        result = b""
        while len(result) < n:
            block = hashlib.sha256(
                seed_bytes + counter[0].to_bytes(8, "big")
            ).digest()
            result += block
            counter[0] += 1
        return result[:n]

    return randfunc


class RSACipher(BaseCipher):
    def __init__(self, seed: str | None = None, key_size: int = 2048):
        randfunc = _seeded_randfunc(seed) if seed else None
        self.key = RSA.generate(key_size, randfunc=randfunc)
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
