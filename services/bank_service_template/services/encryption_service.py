import sys
from pathlib import Path

from config import ALGORITHM, BANK_ID

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from security.encryption_algorithms.cipher_factory import CipherFactory  # noqa: E402
from security.key_management.key_manager import key_manager  # noqa: E402


class EncryptionService:
    def __init__(self, bank_id: int, algorithm_name: str):
        self.bank_id = bank_id
        self.algorithm_name = algorithm_name.upper()
        self.key_material = key_manager.get_key_material(bank_id)
        self.algorithm_from_store = key_manager.get_algorithm(bank_id)

        if self.algorithm_from_store != self.algorithm_name:
            raise ValueError(
                f"Algoritmo inconsistente para bank_id={bank_id}: "
                f"config.py/env={self.algorithm_name}, key_store={self.algorithm_from_store}"
            )

        self.cipher = CipherFactory.get_cipher(
            self.algorithm_name,
            self.key_material,
        )

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext)


encryption_service = EncryptionService(BANK_ID, ALGORITHM)