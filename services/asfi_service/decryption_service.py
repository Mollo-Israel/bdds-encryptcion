from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from security.encryption_algorithms.cipher_factory import CipherFactory  # noqa: E402
from security.key_management.key_manager import key_manager  # noqa: E402


@lru_cache(maxsize=32)
def _get_cipher_for_bank(bank_id: int):
    algorithm_name = key_manager.get_algorithm(bank_id).upper()
    key_material = key_manager.get_key_material(bank_id)

    cipher = CipherFactory.get_cipher(
        algorithm_name,
        key_material,
    )
    return cipher, algorithm_name


def decrypt_account_payload(bank_id: int, account_payload: dict) -> dict:
    cipher, algorithm_name = _get_cipher_for_bank(bank_id)

    decrypted_ci = cipher.decrypt(str(account_payload["ci"]))
    decrypted_numero_cuenta = cipher.decrypt(str(account_payload["numero_cuenta"]))
    decrypted_saldo_usd = cipher.decrypt(str(account_payload["saldo_usd_encrypted"]))

    try:
        saldo_usd_original = Decimal(str(decrypted_saldo_usd))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"No se pudo convertir saldo_usd descifrado a Decimal para banco {bank_id}: {decrypted_saldo_usd}"
        ) from exc

    return {
        "cuenta_id": int(account_payload["cuenta_id"]),
        "banco_id": int(account_payload["banco_id"]),
        "algoritmo": algorithm_name,
        "ci": decrypted_ci,
        "nombre": str(account_payload["nombre"]),
        "apellido": str(account_payload["apellido"]),
        "numero_cuenta": decrypted_numero_cuenta,
        "saldo_usd_original": saldo_usd_original,
        "saldo_usd_encrypted": str(account_payload["saldo_usd_encrypted"]),
    }