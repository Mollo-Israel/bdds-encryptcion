import csv
from collections import defaultdict
from validators import (
    clean_record,
    validate_required_fields,
    validate_account_id,
    parse_account_id,
    validate_balance,
    validate_bank,
    parse_balance,
    parse_bank_id,
    build_duplicate_key,
    build_identity_key,
    validate_ci_format,
    validate_account_format,
    has_irregular_spacing,
    CI_MIN_LENGTH,
    CI_MAX_LENGTH,
    ACCOUNT_MIN_LENGTH,
)

INPUT_FILE = "etl/input/01 - Practica 2 Dataset.csv"
OUTPUT_FILE = "etl/dataset_clean.csv"
REJECTED_FILE = "etl/rejected_records.csv"
REPORT_FILE = "etl/etl_report.txt"


def validate_expected_columns(fieldnames):
    expected = {
        "Nro",
        "Identificacion",
        "Nombres",
        "Apellidos",
        "NroCuenta",
        "IdBanco",
        "Saldo",
    }

    missing = expected - set(fieldnames or [])
    if missing:
        raise ValueError(
            f"El CSV original no contiene todas las columnas requeridas. "
            f"Faltan: {sorted(missing)}"
        )


def reject_record(rejected_rows, raw_row, reason):
    rejected_rows.append({
        "Nro": raw_row.get("Nro", ""),
        "Identificacion": raw_row.get("Identificacion", ""),
        "Nombres": raw_row.get("Nombres", ""),
        "Apellidos": raw_row.get("Apellidos", ""),
        "NroCuenta": raw_row.get("NroCuenta", ""),
        "IdBanco": raw_row.get("IdBanco", ""),
        "Saldo": raw_row.get("Saldo", ""),
        "motivo_rechazo": reason,
    })


def _pre_scan(all_raw_rows):
    """
    Primera pasada: detecta TODOS los registros que pertenecen a un grupo
    conflictivo, para poder rechazarlos en bloque en la segunda pasada.

    - conflict_cis: CIs que aparecen con más de una identidad (nombre+apellido)
    - duplicate_account_keys: claves banco_id+numero_cuenta que aparecen más de una vez

    Solo analiza registros que pasarían las validaciones básicas (filtro 1 y 2),
    para no generar falsos conflictos por datos basura.
    """
    ci_names_map = defaultdict(set)
    account_key_count = defaultdict(int)

    for raw_row in all_raw_rows:
        record = clean_record(raw_row)

        if not validate_required_fields(record):
            continue
        if not validate_account_id(record["cuenta_id"]):
            continue
        if not validate_balance(record["saldo_usd"]):
            continue
        if not validate_bank(record["banco_id"]):
            continue
        if not validate_ci_format(record["ci"]):
            continue
        if not validate_account_format(record["numero_cuenta"]):
            continue

        ci_names_map[record["ci"]].add(build_identity_key(record))
        account_key_count[build_duplicate_key(record)] += 1

    conflict_cis = {ci for ci, names in ci_names_map.items() if len(names) > 1}
    duplicate_account_keys = {key for key, cnt in account_key_count.items() if cnt > 1}

    return conflict_cis, duplicate_account_keys


def main():
    total_records = 0
    valid_records = 0
    removed_records = 0

    # Filtro 1
    removed_null_required = 0
    removed_invalid_account_id = 0
    removed_invalid_balance = 0
    removed_invalid_bank = 0

    # Filtro 2
    removed_invalid_ci_format = 0
    removed_invalid_account_format = 0
    removed_irregular_spacing = 0

    # Consistencia (dos pasadas)
    duplicate_records = 0
    identity_inconsistency_records = 0

    # Anomalías detectadas pero no rechazadas
    anomaly_zero_balance = 0

    clean_data = []
    rejected_rows = []

    # Leer todo en memoria para poder hacer dos pasadas
    all_raw_rows = []
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        validate_expected_columns(reader.fieldnames)
        all_raw_rows = list(reader)

    # Pre-scan: construir conjuntos de conflicto antes de procesar
    conflict_cis, duplicate_account_keys = _pre_scan(all_raw_rows)

    # Segunda pasada: procesar y filtrar
    for raw_row in all_raw_rows:
        total_records += 1
        record = clean_record(raw_row)

        # =========================
        # FILTRO 1: OBLIGATORIO
        # =========================

        if not validate_required_fields(record):
            removed_records += 1
            removed_null_required += 1
            reject_record(rejected_rows, raw_row, "Campos obligatorios vacíos")
            continue

        if not validate_account_id(record["cuenta_id"]):
            removed_records += 1
            removed_invalid_account_id += 1
            reject_record(rejected_rows, raw_row, "cuenta_id inválido")
            continue

        if not validate_balance(record["saldo_usd"]):
            removed_records += 1
            removed_invalid_balance += 1
            reject_record(rejected_rows, raw_row, "Saldo inválido o negativo")
            continue

        if not validate_bank(record["banco_id"]):
            removed_records += 1
            removed_invalid_bank += 1
            reject_record(rejected_rows, raw_row, "Banco inválido")
            continue

        # =========================
        # FILTRO 2: FORMATO
        # =========================

        if not validate_ci_format(record["ci"]):
            removed_records += 1
            removed_invalid_ci_format += 1
            reject_record(
                rejected_rows,
                raw_row,
                f"CI inválido (debe ser numérico y tener entre {CI_MIN_LENGTH} y {CI_MAX_LENGTH} dígitos)"
            )
            continue

        if not validate_account_format(record["numero_cuenta"]):
            removed_records += 1
            removed_invalid_account_format += 1
            reject_record(
                rejected_rows,
                raw_row,
                f"Número de cuenta inválido (debe ser numérico y tener al menos {ACCOUNT_MIN_LENGTH} dígitos)"
            )
            continue

        # Detectar espacios irregulares en el valor ORIGINAL (antes de normalizar)
        nombre_original = raw_row.get("Nombres", "") or ""
        apellido_original = raw_row.get("Apellidos", "") or ""
        if has_irregular_spacing(nombre_original) or has_irregular_spacing(apellido_original):
            removed_records += 1
            removed_irregular_spacing += 1
            reject_record(rejected_rows, raw_row, "Nombre o Apellido con espacios irregulares")
            continue

        # Convertir tipos después de validar
        record["cuenta_id"] = parse_account_id(record["cuenta_id"])
        record["banco_id"] = parse_bank_id(record["banco_id"])
        record["saldo_usd"] = parse_balance(record["saldo_usd"])

        # =========================
        # REGLAS DE CONSISTENCIA (dos pasadas: rechaza TODOS los del grupo)
        # =========================

        if record["ci"] in conflict_cis:
            identity_inconsistency_records += 1
            removed_records += 1
            reject_record(rejected_rows, raw_row, "Inconsistencia de identidad por CI")
            continue

        if build_duplicate_key(record) in duplicate_account_keys:
            duplicate_records += 1
            removed_records += 1
            reject_record(rejected_rows, raw_row, "Duplicado por banco_id + numero_cuenta")
            continue

        # =========================
        # ANOMALÍAS (se aceptan pero se registran en el reporte)
        # =========================

        if record["saldo_usd"] == 0.0:
            anomaly_zero_balance += 1

        clean_data.append(record)
        valid_records += 1

    # Guardar dataset limpio
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "cuenta_id",
            "ci",
            "nombre",
            "apellido",
            "numero_cuenta",
            "banco_id",
            "saldo_usd",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_data)

    # Guardar rechazados
    with open(REJECTED_FILE, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Nro",
            "Identificacion",
            "Nombres",
            "Apellidos",
            "NroCuenta",
            "IdBanco",
            "Saldo",
            "motivo_rechazo",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rejected_rows)

    # Distribución por banco para el reporte
    bank_distribution = {}
    for record in clean_data:
        bank_id = record["banco_id"]
        bank_distribution[bank_id] = bank_distribution.get(bank_id, 0) + 1

    # Guardar reporte
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("REPORTE ETL\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total registros originales: {total_records}\n")
        f.write(f"Registros válidos: {valid_records}\n")
        f.write(f"Registros rechazados totales: {removed_records}\n")
        f.write("\n")

        f.write("FILTRO 1: VALIDACIÓN OBLIGATORIA\n")
        f.write("-" * 60 + "\n")
        f.write(f"Campos obligatorios vacíos: {removed_null_required}\n")
        f.write(f"cuenta_id inválido: {removed_invalid_account_id}\n")
        f.write(f"Saldo inválido o negativo: {removed_invalid_balance}\n")
        f.write(f"Banco inválido: {removed_invalid_bank}\n")
        f.write("\n")

        f.write("FILTRO 2: VALIDACIÓN DE FORMATO\n")
        f.write("-" * 60 + "\n")
        f.write(f"CI inválido por formato/longitud: {removed_invalid_ci_format}\n")
        f.write(f"Número de cuenta inválido por formato/longitud: {removed_invalid_account_format}\n")
        f.write(f"Nombre o Apellido con espacios irregulares: {removed_irregular_spacing}\n")
        f.write("\n")

        f.write("REGLAS DE CONSISTENCIA (dos pasadas — se rechaza todo el grupo)\n")
        f.write("-" * 60 + "\n")
        f.write(f"Inconsistencias de identidad por CI: {identity_inconsistency_records}\n")
        f.write(f"Duplicados por banco_id + numero_cuenta: {duplicate_records}\n")
        f.write("\n")

        f.write("ANOMALÍAS DETECTADAS (registros aceptados pero sospechosos)\n")
        f.write("-" * 60 + "\n")
        f.write(f"Saldo igual a 0.0: {anomaly_zero_balance}\n")
        f.write("\n")

        f.write("DISTRIBUCIÓN FINAL POR BANCO\n")
        f.write("-" * 60 + "\n")
        for bank_id in sorted(bank_distribution.keys()):
            f.write(f"Banco {bank_id}: {bank_distribution[bank_id]} registros\n")
        f.write("\n")

        f.write("ARCHIVOS GENERADOS\n")
        f.write("-" * 60 + "\n")
        f.write(f"- {OUTPUT_FILE}\n")
        f.write(f"- {REJECTED_FILE}\n")
        f.write(f"- {REPORT_FILE}\n")
        f.write("\n")

        f.write("REGLAS APLICADAS\n")
        f.write("-" * 60 + "\n")
        f.write("- Se reutiliza la columna Nro como cuenta_id para integración con los microservicios bancarios.\n")
        f.write("- Nombres y apellidos normalizados a mayúsculas.\n")
        f.write("- Filtro 1 elimina registros con problemas estructurales u obligatorios.\n")
        f.write("- Filtro 2 valida formato de CI, número de cuenta y espacios en nombres.\n")
        f.write("- Consistencia en dos pasadas: se rechaza TODA la familia de registros conflictivos.\n")
        f.write("- Duplicado lógico: banco_id + numero_cuenta.\n")
        f.write("- Inconsistencia de identidad: mismo CI con distinto nombre o apellido.\n")
        f.write("- Saldo negativo: rechazado en filtro 1 (validate_balance).\n")
        f.write("- Saldo 0.0: aceptado pero contabilizado como anomalía en el reporte.\n")

    print("ETL finalizado correctamente.")
    print(f"Dataset limpio generado en: {OUTPUT_FILE}")
    print(f"Registros rechazados en: {REJECTED_FILE}")
    print(f"Reporte generado en: {REPORT_FILE}")


if __name__ == "__main__":
    main()
