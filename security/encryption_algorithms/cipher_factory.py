from .classical.caesar_cipher import CaesarCipher
from .classical.atbash_cipher import AtbashCipher
from .classical.vigenere_cipher import VigenereCipher
from .classical.playfair_cipher import PlayfairCipher
from .classical.hill_cipher import HillCipher

from .modern.aes_cipher import AESCipher
from .modern.des_cipher import DESCipher
from .modern.triple_des_cipher import TripleDESCipher
from .modern.blowfish_cipher import BlowfishCipher
from .modern.chacha20_cipher import ChaCha20Cipher
from .modern.twofish_cipher import TwofishCipher
from .modern.rsa_cipher import RSACipher
from .modern.elgamal_cipher import ElGamalCipher
from .modern.ecc_cipher import ECCCipher


class CipherFactory:
    ALGORITHM_MAP = {
        "CAESAR": CaesarCipher,
        "ATBASH": AtbashCipher,
        "VIGENERE": VigenereCipher,
        "PLAYFAIR": PlayfairCipher,
        "HILL": HillCipher,
        "AES": AESCipher,
        "DES": DESCipher,
        "3DES": TripleDESCipher,
        "BLOWFISH": BlowfishCipher,
        "CHACHA20": ChaCha20Cipher,
        "TWOFISH": TwofishCipher,
        "RSA": RSACipher,
        "ELGAMAL": ElGamalCipher,
        "ECC": ECCCipher,
    }

    @classmethod
    def get_cipher(cls, algorithm_name: str, key_material: dict | None = None):
        algorithm_name = algorithm_name.upper()
        key_material = key_material or {}

        if algorithm_name not in cls.ALGORITHM_MAP:
            raise ValueError(f"Algoritmo no soportado: {algorithm_name}")

        if algorithm_name == "CAESAR":
            return CaesarCipher(shift=key_material.get("shift", 3))

        if algorithm_name == "ATBASH":
            return AtbashCipher()

        if algorithm_name == "VIGENERE":
            return VigenereCipher(key=key_material.get("key", "CLAVE"))

        if algorithm_name == "PLAYFAIR":
            return PlayfairCipher(key=key_material.get("key", "SEGURIDAD"))

        if algorithm_name == "HILL":
            return HillCipher(key_matrix=key_material.get("key_matrix"))

        cipher_cls = cls.ALGORITHM_MAP[algorithm_name]

        try:
            return cipher_cls(**key_material)
        except TypeError:
            return cipher_cls()