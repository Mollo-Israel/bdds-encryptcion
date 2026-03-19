import json
from pathlib import Path

from .key_store import BankKeyRecord

KEYS_FILE = Path(__file__).resolve().parent / "keys.json"


def load_keys() -> dict[int, BankKeyRecord]:
    if not KEYS_FILE.exists():
        raise FileNotFoundError(f"No existe archivo de llaves: {KEYS_FILE}")

    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    records: dict[int, BankKeyRecord] = {}

    for bank_id_str, payload in raw.items():
        bank_id = int(bank_id_str)
        records[bank_id] = BankKeyRecord(
            bank_id=bank_id,
            algorithm=str(payload["algorithm"]).upper(),
            key_material=dict(payload.get("key_material", {})),
        )

    return records