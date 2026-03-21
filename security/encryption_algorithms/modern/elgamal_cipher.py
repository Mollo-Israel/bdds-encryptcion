import hashlib
import os

from Crypto.PublicKey import ElGamal
from Crypto import Random
from Crypto.Util.number import bytes_to_long, long_to_bytes, inverse

from ..base_cipher import BaseCipher
from ..utils import b64encode_bytes, b64decode_str


def _seeded_randfunc(seed: str):
    """
    Genera bytes pseudo-aleatorios deterministas a partir de `seed`.
    SHA-256 en modo contador: mismo seed → mismo p,g,x,y ElGamal
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


class ElGamalCipher(BaseCipher):
    """
    Implementación académica de ElGamal sobre enteros.
    """

    def __init__(self, seed: str | None = None, key_size: int = 256):
        randfunc = _seeded_randfunc(seed) if seed else Random.new().read
        self.key = ElGamal.generate(key_size, randfunc)
        self.public_key = self.key.publickey()

        # Convertir a int puro para evitar problemas con IntegerCustom
        self.p = int(self.key.p)
        self.g = int(self.key.g)
        self.x = int(self.key.x)
        self.y = int(self.key.y)

    def encrypt(self, data: str) -> str:
        message_bytes = data.encode("utf-8")
        message_int = bytes_to_long(message_bytes)

        if message_int >= self.p:
            raise ValueError("Mensaje demasiado largo para esta clave ElGamal.")

        k = Random.random.randint(1, self.p - 2)

        c1 = pow(self.g, k, self.p)
        s = pow(self.y, k, self.p)
        c2 = (message_int * s) % self.p

        combined = f"{c1}:{c2}".encode("utf-8")
        return b64encode_bytes(combined)

    def decrypt(self, data: str) -> str:
        decoded = b64decode_str(data).decode("utf-8")
        c1_str, c2_str = decoded.split(":")
        c1 = int(c1_str)
        c2 = int(c2_str)

        s = pow(c1, self.x, self.p)
        s_inv = inverse(s, self.p)
        message_int = (c2 * s_inv) % self.p

        message_bytes = long_to_bytes(message_int)
        return message_bytes.decode("utf-8")
