#!/usr/bin/env python3
"""
Barrido paralelo ASFI.
Llama al endpoint POST /sweep de ASFI, que internamente procesa
todos los bancos en paralelo con ThreadPoolExecutor.

Uso:
    python parallel/sweep.py
    python parallel/sweep.py --asfi http://localhost:9000
"""
import argparse
import sys
import time

import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Barrido paralelo ASFI")
    parser.add_argument(
        "--asfi",
        default="http://localhost:9000",
        help="URL base del servicio ASFI (default: http://localhost:9000)",
    )
    args = parser.parse_args()

    asfi_url = args.asfi.rstrip("/")

    print("=" * 65)
    print("  BARRIDO PARALELO - Plataforma ASFI")
    print(f"  Endpoint: {asfi_url}/sweep")
    print("=" * 65)

    t0 = time.time()
    try:
        resp = requests.post(f"{asfi_url}/sweep", timeout=300)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: No se pudo conectar a {asfi_url}")
        print("Asegúrate de que el servicio ASFI esté corriendo (puerto 9000).")
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"\nERROR HTTP {resp.status_code}: {resp.text}")
        sys.exit(1)
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)

    elapsed = time.time() - t0
    data = resp.json()

    print(f"\nBancos procesados : {data['total_bancos']}")
    print(f"Cuentas sincronizadas : {data['total_cuentas_sincronizadas']}")
    print(f"Bancos con error  : {data['total_bancos_con_error']}")
    print(f"Tiempo total      : {elapsed:.1f}s")
    print()
    print(f"{'Banco':<6} {'Algoritmo':<12} {'Cuentas':<10} Estado")
    print("-" * 50)

    for r in data["results"]:
        bid = r["banco_id"]
        if r.get("error"):
            print(f"  {bid:<4} {'':12} {'':10} ERROR: {r['error'][:50]}")
        else:
            algo = r.get("algoritmo", "?")
            total = r.get("total_sincronizadas", 0)
            tc = r.get("tipo_cambio_aplicado", "?")
            print(f"  {bid:<4} {algo:<12} {total:<10} OK (TC={tc})")

    print("=" * 65)
    if data["total_bancos_con_error"] == 0:
        print("  BARRIDO COMPLETADO SIN ERRORES")
    else:
        print(f"  BARRIDO COMPLETADO CON {data['total_bancos_con_error']} ERROR(ES)")
    print("=" * 65)

    sys.exit(0 if data["total_bancos_con_error"] == 0 else 1)


if __name__ == "__main__":
    main()
