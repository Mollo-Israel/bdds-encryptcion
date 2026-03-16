import re

VALID_BANK_IDS = set(range(1, 15))

# Reglas configurables para el filtro 2
CI_MIN_LENGTH = 5
CI_MAX_LENGTH = 15
ACCOUNT_MIN_LENGTH = 6


def normalize_text(value) -> str:
    """
    Limpia espacios al inicio/final y colapsa espacios internos.
    """
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def normalize_name(value) -> str:
    """
    Normaliza nombres/apellidos:
    - elimina espacios sobrantes
    - convierte a mayúsculas
    """
    return normalize_text(value).upper()


def normalize_identity_text(value) -> str:
    """
    Normaliza texto para comparar identidad.
    """
    return normalize_name(value)


def clean_record(row: dict) -> dict:
    """
    Mapea columnas del dataset original al modelo del sistema.
    La columna 'Nro' se ignora porque no pertenece al dominio bancario.
    """
    return {
        "ci": normalize_text(row.get("Identificacion", "")),
        "nombre": normalize_name(row.get("Nombres", "")),
        "apellido": normalize_name(row.get("Apellidos", "")),
        "numero_cuenta": normalize_text(row.get("NroCuenta", "")),
        "banco_id": normalize_text(row.get("IdBanco", "")),
        "saldo_usd": normalize_text(row.get("Saldo", "")),
    }


# =========================
# FILTRO 1: OBLIGATORIO
# =========================

def validate_required_fields(record: dict) -> bool:
    required_fields = [
        "ci",
        "nombre",
        "apellido",
        "numero_cuenta",
        "banco_id",
        "saldo_usd",
    ]

    for field in required_fields:
        if field not in record:
            return False
        if normalize_text(record[field]) == "":
            return False

    return True


def parse_balance(balance):
    try:
        return float(normalize_text(balance))
    except (TypeError, ValueError):
        return None


def validate_balance(balance) -> bool:
    value = parse_balance(balance)
    return value is not None and value >= 0


def parse_bank_id(banco_id):
    try:
        return int(normalize_text(banco_id))
    except (TypeError, ValueError):
        return None


def validate_bank(banco_id) -> bool:
    value = parse_bank_id(banco_id)
    return value in VALID_BANK_IDS if value is not None else False


def build_duplicate_key(record: dict):
    """
    Duplicado lógico: banco_id + numero_cuenta
    """
    return (
        str(record["banco_id"]),
        normalize_text(record["numero_cuenta"]),
    )


def build_identity_key(record: dict):
    """
    Identidad lógica por CI usando nombre y apellido normalizados.
    """
    return (
        normalize_identity_text(record["nombre"]),
        normalize_identity_text(record["apellido"]),
    )


# =========================
# FILTRO 2: FORMATO
# =========================

def validate_ci_format(ci: str) -> bool:
    """
    Regla ajustada al dataset:
    - solo números
    - longitud entre CI_MIN_LENGTH y CI_MAX_LENGTH
    """
    ci = normalize_text(ci)

    if not ci.isdigit():
        return False

    return CI_MIN_LENGTH <= len(ci) <= CI_MAX_LENGTH


def validate_account_format(numero_cuenta: str) -> bool:
    """
    Regla ajustada al dataset:
    - solo números
    - longitud mínima ACCOUNT_MIN_LENGTH
    """
    numero_cuenta = normalize_text(numero_cuenta)

    if not numero_cuenta.isdigit():
        return False

    return len(numero_cuenta) >= ACCOUNT_MIN_LENGTH