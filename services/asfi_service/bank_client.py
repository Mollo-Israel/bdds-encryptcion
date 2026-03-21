"""
Cliente HTTP para comunicarse con los microservicios de los 14 bancos.

Responsabilidad única: lectura de cuentas cifradas.
La persistencia de saldos convertidos es exclusiva de la base central ASFI.
"""

import requests

from config import ASFI_SHARED_TOKEN, AUTH_HEADER_NAME, REQUEST_TIMEOUT_SECONDS


def _auth_headers() -> dict[str, str]:
    return {AUTH_HEADER_NAME: f"Bearer {ASFI_SHARED_TOKEN}"}


def fetch_bank_accounts(
    endpoint_api: str,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    """
    Lee las cuentas cifradas de un banco.

    Parámetros
    ----------
    endpoint_api : URL base del banco (ej. http://localhost:8001)
    limit        : máximo de cuentas a traer (None = todas)
    offset       : desplazamiento para paginación

    Retorna
    -------
    Lista de dicts con los datos de cuentas cifradas.
    """
    url = f"{endpoint_api.rstrip('/')}/accounts"

    params: dict[str, int] = {}
    if limit is not None and limit > 0:
        params["limit"] = int(limit)
    if offset and offset > 0:
        params["offset"] = int(offset)

    response = requests.get(
        url,
        headers=_auth_headers(),
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, list):
        raise ValueError("La respuesta del banco no es una lista de cuentas")

    return data
