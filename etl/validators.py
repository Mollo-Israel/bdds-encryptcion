import re

VALID_BANK_IDS = set(range(1, 15))


def normalize_text(value) -> str:
    """
    Limpia espacios al inicio/final y colapsa espacios internos.
    Ejemplo: '  Juan   Perez  ' -> 'Juan Perez'
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


def validate_required_fields(record: dict) -> bool:
    """
    Verifica que existan todos los campos obligatorios y no estén vacíos.
    """
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


def validate_ci(ci: str) -> bool:
    """
    Regla ajustada al dataset real:
    - solo números
    - entre 5 y 15 dígitos
    """
    ci = normalize_text(ci)
    return bool(re.fullmatch(r"\d{5,15}", ci))


def validate_account(numero_cuenta: str) -> bool:
    """
    Regla ajustada al dataset real:
    - solo números
    - mínimo 6 dígitos
    """
    numero_cuenta = normalize_text(numero_cuenta)
    return bool(re.fullmatch(r"\d{6,}", numero_cuenta))


def parse_balance(balance):
    """
    Convierte saldo a float si es posible.
    """
    try:
        return float(normalize_text(balance))
    except (TypeError, ValueError):
        return None


def validate_balance(balance) -> bool:
    """
    El saldo debe ser numérico y mayor o igual a cero.
    """
    value = parse_balance(balance)
    return value is not None and value >= 0


def parse_bank_id(banco_id):
    """
    Convierte banco_id a int si es posible.
    """
    try:
        return int(normalize_text(banco_id))
    except (TypeError, ValueError):
        return None


def validate_bank(banco_id) -> bool:
    """
    Valida que el banco esté entre 1 y 14.
    """
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