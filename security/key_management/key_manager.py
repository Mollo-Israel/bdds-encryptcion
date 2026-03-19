from typing import Any

from .bank_algorithm_map import BANK_ALGORITHM_MAP
from .key_loader import load_keys
from .key_store import BankKeyRecord


class KeyManager:
    def __init__(self):
        self._records: dict[int, BankKeyRecord] = {}
        self.reload()

    def reload(self) -> None:
        self._records = load_keys()

    def get_record(self, bank_id: int) -> BankKeyRecord:
        if bank_id not in self._records:
            raise KeyError(f"No existe configuración de llaves para bank_id={bank_id}")
        return self._records[bank_id]

    def get_algorithm(self, bank_id: int) -> str:
        record = self.get_record(bank_id)
        expected_algorithm = BANK_ALGORITHM_MAP.get(bank_id)

        if expected_algorithm and record.algorithm != expected_algorithm:
            raise ValueError(
                f"Algoritmo inconsistente para bank_id={bank_id}: "
                f"keys.json={record.algorithm}, esperado={expected_algorithm}"
            )

        return record.algorithm

    def get_key_material(self, bank_id: int) -> dict[str, Any]:
        return dict(self.get_record(bank_id).key_material)


key_manager = KeyManager()