from Crypto.Cipher import AES
from ..base_cipher import BaseCipher
from ..utils import pad_pkcs7, unpad_pkcs7, b64encode_bytes, b64decode_str


class TwofishCipher(BaseCipher):
    """
    Implementación compatible para entorno académico.
    Simula comportamiento de cifrado tipo bloque (como Twofish)
    usando AES internamente debido a incompatibilidad de librería.
    """

    def __init__(self, key: bytes = b"TwofishSimulationKey"):
        self.key = key[:16]  # AES-128
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