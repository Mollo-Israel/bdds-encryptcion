import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
AUDIT_DIR = BASE_DIR / "audit"
AUDIT_FILE = AUDIT_DIR / "asfi_transactions.log"


def get_audit_file_path() -> str:
    return str(AUDIT_FILE)


def write_audit_log(
    *,
    evento: str,
    banco_id: int,
    cuenta_id: int,
    tipo_cambio_aplicado: Decimal | float | str,
    codigo_verificacion: str | None = None,
    estado: str = "OK",
    detalle: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "evento": evento,
        "banco_id": int(banco_id),
        "cuenta_id": int(cuenta_id),
        "tipo_cambio_aplicado": str(tipo_cambio_aplicado),
        "codigo_verificacion": codigo_verificacion,
        "estado": estado,
        "detalle": detalle,
        "extra": extra or {},
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")