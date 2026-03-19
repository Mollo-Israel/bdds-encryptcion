import csv
import os
import time
from collections import defaultdict

import requests

DATASET_FILE = os.getenv("DATASET_FILE", "etl/dataset_clean.csv")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "60"))
RETRIES = int(os.getenv("RETRIES", "3"))

BANK_ENDPOINTS = {
    1: os.getenv("BANK_1_URL", "http://127.0.0.1:8001/accounts/load"),
    2: os.getenv("BANK_2_URL", "http://127.0.0.1:8002/accounts/load"),
    3: os.getenv("BANK_3_URL", "http://127.0.0.1:8003/accounts/load"),
    4: os.getenv("BANK_4_URL", "http://127.0.0.1:8004/accounts/load"),
    5: os.getenv("BANK_5_URL", "http://127.0.0.1:8005/accounts/load"),
    6: os.getenv("BANK_6_URL", "http://127.0.0.1:8006/accounts/load"),
    7: os.getenv("BANK_7_URL", "http://127.0.0.1:8007/accounts/load"),
    8: os.getenv("BANK_8_URL", "http://127.0.0.1:8008/accounts/load"),
    9: os.getenv("BANK_9_URL", "http://127.0.0.1:8009/accounts/load"),
    10: os.getenv("BANK_10_URL", "http://127.0.0.1:8010/accounts/load"),
    11: os.getenv("BANK_11_URL", "http://127.0.0.1:8011/accounts/load"),
    12: os.getenv("BANK_12_URL", "http://127.0.0.1:8012/accounts/load"),
    13: os.getenv("BANK_13_URL", "http://127.0.0.1:8113/accounts/load"),
    14: os.getenv("BANK_14_URL", "http://127.0.0.1:8014/accounts/load"),
}


def normalize_row(row: dict) -> dict:
    return {
        "cuenta_id": int(row["cuenta_id"]),
        "ci": str(row["ci"]),
        "nombre": str(row["nombre"]),
        "apellido": str(row["apellido"]),
        "numero_cuenta": str(row["numero_cuenta"]),
        "banco_id": int(row["banco_id"]),
        "saldo_usd": float(row["saldo_usd"]),
    }


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def load_dataset_grouped():
    grouped = defaultdict(list)

    with open(DATASET_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            record = normalize_row(row)
            grouped[record["banco_id"]].append(record)

    return grouped


def send_batch(session: requests.Session, bank_id: int, batch: list[dict]) -> int:
    url = BANK_ENDPOINTS.get(bank_id)
    if not url:
        raise ValueError(f"No hay endpoint configurado para banco {bank_id}")

    payload = {"accounts": batch}
    last_error = None

    for attempt in range(1, RETRIES + 1):
        try:
            response = session.post(url, json=payload, timeout=TIMEOUT_SECONDS)

            if response.status_code in (200, 201):
                data = response.json()
                return int(data.get("inserted", 0))

            last_error = (
                f"Banco {bank_id} | intento {attempt}/{RETRIES} | "
                f"status={response.status_code} | body={response.text}"
            )

        except requests.RequestException as exc:
            last_error = f"Banco {bank_id} | intento {attempt}/{RETRIES} | excepción: {exc}"

        time.sleep(1)

    raise RuntimeError(last_error or f"Falló el envío al banco {bank_id}")


def main():
    grouped = load_dataset_grouped()
    total_records = sum(len(v) for v in grouped.values())

    print("=" * 70)
    print("INICIO DE CARGA MASIVA POR APIs BANCARIAS")
    print(f"Dataset: {DATASET_FILE}")
    print(f"Total registros a enrutar: {total_records}")
    print(f"Tamaño de lote: {BATCH_SIZE}")
    print("=" * 70)

    total_inserted = 0
    total_batches = 0
    failed_batches = 0

    with requests.Session() as session:
        for bank_id in sorted(grouped.keys()):
            bank_records = grouped[bank_id]
            bank_total = len(bank_records)
            bank_inserted = 0
            bank_failed = 0

            print(f"\n[BANCO {bank_id}] registros: {bank_total}")

            for idx, batch in enumerate(chunked(bank_records, BATCH_SIZE), start=1):
                total_batches += 1
                try:
                    inserted = send_batch(session, bank_id, batch)
                    bank_inserted += inserted
                    total_inserted += inserted
                    print(
                        f"  lote {idx}: enviados={len(batch)} insertados={inserted}"
                    )
                except Exception as exc:
                    failed_batches += 1
                    bank_failed += 1
                    print(f"  lote {idx}: ERROR -> {exc}")

            print(
                f"[BANCO {bank_id}] final -> "
                f"registros={bank_total} insertados={bank_inserted} lotes_fallidos={bank_failed}"
            )

    print("\n" + "=" * 70)
    print("CARGA FINALIZADA")
    print(f"Total insertados reportados por APIs: {total_inserted}")
    print(f"Total lotes procesados: {total_batches}")
    print(f"Total lotes fallidos: {failed_batches}")
    print("=" * 70)


if __name__ == "__main__":
    main()