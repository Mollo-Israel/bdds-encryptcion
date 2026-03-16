import csv
import requests

DATASET_FILE = "etl/dataset_clean.csv"

BANK_ENDPOINTS = {
    1: "http://localhost:8001/accounts",
    2: "http://localhost:8002/accounts",
    3: "http://localhost:8003/accounts",
    4: "http://localhost:8004/accounts",
    5: "http://localhost:8005/accounts",
    6: "http://localhost:8006/accounts",
    7: "http://localhost:8007/accounts",
    8: "http://localhost:8008/accounts",
    9: "http://localhost:8009/accounts",
    10: "http://localhost:8010/accounts",
    11: "http://localhost:8011/accounts",
    12: "http://localhost:8012/accounts",
    13: "http://localhost:8013/accounts",
    14: "http://localhost:8014/accounts",
}


def send_record(record: dict):
    bank_id = int(record["banco_id"])
    url = BANK_ENDPOINTS.get(bank_id)

    if not url:
        print(f"[ERROR] Banco inválido para routing: {bank_id}")
        return False

    try:
        response = requests.post(url, json=record, timeout=5)

        if response.status_code in (200, 201):
            return True

        print(
            f"[ERROR] Falló envío a banco {bank_id}. "
            f"Status: {response.status_code}. Respuesta: {response.text}"
        )
        return False

    except requests.RequestException as e:
        print(f"[ERROR] No se pudo conectar con banco {bank_id}: {e}")
        return False


def main():
    total_sent = 0
    total_ok = 0
    total_failed = 0

    with open(DATASET_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            total_sent += 1
            if send_record(row):
                total_ok += 1
            else:
                total_failed += 1

    print("Routing finalizado.")
    print(f"Total enviados: {total_sent}")
    print(f"Correctos: {total_ok}")
    print(f"Fallidos: {total_failed}")


if __name__ == "__main__":
    main()