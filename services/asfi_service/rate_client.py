import requests

from config import BCB_RATE_API_URL, REQUEST_TIMEOUT_SECONDS


def fetch_current_rate() -> float:
    base_url = BCB_RATE_API_URL.rstrip("/")
    url = f"{base_url}/rate"

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    data = response.json()
    if "rate" not in data:
        raise ValueError("La respuesta del BCB no contiene 'rate'")

    return float(data["rate"])