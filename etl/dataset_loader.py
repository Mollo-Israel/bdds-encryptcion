import csv
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


def main():
    total_records = 0
    valid_records = 0
    removed_records = 0

    # Filtro 1
    removed_null_required = 0
    removed_invalid_account_id = 0
    removed_invalid_balance = 0
    removed_invalid_bank = 0
    duplicate_records = 0
    identity_inconsistency_records = 0

    # Filtro 2
    removed_invalid_ci_format = 0
    removed_invalid_account_format = 0

    seen_accounts = set()
    ci_identity_map = {}
    clean_data = []
    rejected_rows = []

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        validate_expected_columns(reader.fieldnames)

        for raw_row in reader:
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
                reject_record(rejected_rows, raw_row, "Saldo inválido")
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

            # Convertir tipos después de validar
            record["cuenta_id"] = parse_account_id(record["cuenta_id"])
            record["banco_id"] = parse_bank_id(record["banco_id"])
            record["saldo_usd"] = parse_balance(record["saldo_usd"])

            # =========================
            # REGLAS DE CONSISTENCIA
            # =========================

            duplicate_key = build_duplicate_key(record)
            if duplicate_key in seen_accounts:
                duplicate_records += 1
                removed_records += 1
                reject_record(rejected_rows, raw_row, "Duplicado por banco_id + numero_cuenta")
                continue
            seen_accounts.add(duplicate_key)

            current_identity = build_identity_key(record)
            ci = record["ci"]

            if ci in ci_identity_map:
                if ci_identity_map[ci] != current_identity:
                    identity_inconsistency_records += 1
                    removed_records += 1
                    reject_record(rejected_rows, raw_row, "Inconsistencia de identidad por CI")
                    continue
            else:
                ci_identity_map[ci] = current_identity

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
        f.write(f"Saldo inválido: {removed_invalid_balance}\n")
        f.write(f"Banco inválido: {removed_invalid_bank}\n")
        f.write("\n")

        f.write("FILTRO 2: VALIDACIÓN DE FORMATO\n")
        f.write("-" * 60 + "\n")
        f.write(f"CI inválido por formato/longitud: {removed_invalid_ci_format}\n")
        f.write(f"Número de cuenta inválido por formato/longitud: {removed_invalid_account_format}\n")
        f.write("\n")

        f.write("REGLAS DE CONSISTENCIA\n")
        f.write("-" * 60 + "\n")
        f.write(f"Duplicados detectados: {duplicate_records}\n")
        f.write(f"Inconsistencias de identidad: {identity_inconsistency_records}\n")
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

        f.write("COLUMNAS DEL DATASET LIMPIO\n")
        f.write("-" * 60 + "\n")
        f.write("cuenta_id,ci,nombre,apellido,numero_cuenta,banco_id,saldo_usd\n")
        f.write("\n")

        f.write("REGLAS APLICADAS\n")
        f.write("-" * 60 + "\n")
        f.write("- Se reutiliza la columna Nro como cuenta_id para integración con los microservicios bancarios.\n")
        f.write("- Nombres y apellidos normalizados a mayúsculas.\n")
        f.write("- Filtro 1 elimina registros con problemas estructurales u obligatorios.\n")
        f.write("- Filtro 2 valida formato de CI y número de cuenta con reglas ajustadas al dataset.\n")
        f.write("- Duplicado lógico: banco_id + numero_cuenta.\n")
        f.write("- Inconsistencia de identidad: mismo CI con distinto nombre o apellido.\n")

    print("ETL finalizado correctamente.")
    print(f"Dataset limpio generado en: {OUTPUT_FILE}")
    print(f"Registros rechazados en: {REJECTED_FILE}")
    print(f"Reporte generado en: {REPORT_FILE}")


if __name__ == "__main__":
    main()