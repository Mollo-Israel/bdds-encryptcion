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

    BANK_MAP = {
        "BANCO_UNION": "CAESAR",
        "BANCO_MERCANTIL": "ATBASH",
        "BANCO_BISA": "VIGENERE",
        "BANCO_FORTALEZA": "PLAYFAIR",
        "BANCO_GANADERO": "HILL",
        "BANCO_NACIONAL": "AES",
        "BANCO_ECONOMICO": "DES",
        "BANCO_SOL": "3DES",
        "BANCO_CREDITO": "BLOWFISH",
        "BANCO_PRODEM": "CHACHA20",
        "BANCO_FASSIL": "TWOFISH",
        "BANCO_DIEZ": "RSA",
        "BANCO_ONCE": "ELGAMAL",
        "BANCO_DOCE": "ECC",
    }

    @classmethod
    def get_cipher(cls, algorithm_name: str):
        algorithm_name = algorithm_name.upper()

        if algorithm_name not in cls.ALGORITHM_MAP:
            raise ValueError(f"Algoritmo no soportado: {algorithm_name}")

        return cls.ALGORITHM_MAP[algorithm_name]()

    @classmethod
    def get_cipher_by_bank(cls, bank_name: str):
        bank_name = bank_name.upper()

        if bank_name not in cls.BANK_MAP:
            raise ValueError(f"Banco no configurado: {bank_name}")

        algorithm_name = cls.BANK_MAP[bank_name]
        return cls.get_cipher(algorithm_name)