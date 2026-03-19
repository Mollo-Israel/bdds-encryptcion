from hmac import compare_digest

from fastapi import HTTPException, Request, status

from config import ASFI_SHARED_TOKEN, AUTH_ENABLED, AUTH_HEADER_NAME


def _extract_token(raw_value: str | None) -> str:
    if not raw_value:
        return ""

    value = raw_value.strip()
    if not value:
        return ""

    parts = value.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()

    return value


def require_asfi_auth(request: Request) -> None:
    if not AUTH_ENABLED:
        return

    raw_header = request.headers.get(AUTH_HEADER_NAME)
    provided_token = _extract_token(raw_header)

    if not provided_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación no proporcionado",
        )

    if not compare_digest(provided_token, ASFI_SHARED_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido",
        )