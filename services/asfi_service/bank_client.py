import requests
from datetime import datetime
from decimal import Decimal

from config import ASFI_SHARED_TOKEN, AUTH_HEADER_NAME, REQUEST_TIMEOUT_SECONDS


def build_auth_headers() -> dict[str, str]:
    return {
        AUTH_HEADER_NAME: f"Bearer {ASFI_SHARED_TOKEN}"
    }


def fetch_bank_accounts(
    endpoint_api: str,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    base_url = endpoint_api.rstrip("/")
    url = f"{base_url}/accounts"

    params: dict[str, int] = {}
    if limit is not None and limit > 0:
        params["limit"] = int(limit)
    if offset and offset > 0:
        params["offset"] = int(offset)

    response = requests.get(
        url,
        headers=build_auth_headers(),
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        raise ValueError("La respuesta del banco no es una lista de cuentas")

    return data


def update_bank_account(
    endpoint_api: str,
    *,
    cuenta_id: int,
    saldo_bs: Decimal,
    fecha_conversion: datetime,
    codigo_verificacion: str,
) -> dict:
    base_url = endpoint_api.rstrip("/")
    url = f"{base_url}/accounts/update"

    payload = {
        "cuenta_id": int(cuenta_id),
        "saldo_bs": str(saldo_bs),
        "fecha_conversion": fecha_conversion.isoformat(),
        "codigo_verificacion": str(codigo_verificacion),
    }

    response = requests.post(
        url,
        headers=build_auth_headers(),
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("La respuesta del banco al update no es un objeto JSON")

    return data