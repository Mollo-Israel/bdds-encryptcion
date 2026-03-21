#!/usr/bin/env python3
"""
Barrido paralelo ASFI.

Llama a POST /sweep en el servicio ASFI, que internamente:
  1. Obtiene tipo de cambio del BCB
  2. Lee los 14 bancos en paralelo (ThreadPoolExecutor)
  3. Convierte saldos USD → Bs
  4. Persiste SÓLO en la base central ASFI

Uso:
    python parallel/sweep.py
    python parallel/sweep.py --asfi http://localhost:9000
    python parallel/sweep.py --timeout 1800
    python parallel/sweep.py --timeout 0        # sin timeout de lectura
    python parallel/sweep.py --verbose          # muestra tipo de cambio por banco
"""

import argparse
import sys
import time
from typing import Optional

import requests


def build_timeout(timeout_seconds: int) -> Optional[tuple]:
    if timeout_seconds <= 0:
        return None
    return (10, timeout_seconds)


def _col(value: str, width: int) -> str:
    return str(value)[:width].ljust(width)


def print_results(data: dict, elapsed: float, verbose: bool) -> None:
    results = data.get("results", [])
    total_bancos = data.get("total_bancos", 0)
    total_cuentas = data.get("total_cuentas_sincronizadas", 0)
    total_errors = data.get("total_bancos_con_error", 0)

    print()

    # Cabecera de la tabla
    if verbose:
        header = f"{'ID':<4}  {'Banco':<38}  {'Algoritmo':<12}  {'TC (BOB)':<10}  {'Cuentas':<8}  Estado"
        sep = "-" * 95
    else:
        header = f"{'ID':<4}  {'Algoritmo':<12}  {'Cuentas':<8}  Estado"
        sep = "-" * 55

    print(header)
    print(sep)

    for r in results:
        bid = str(r.get("banco_id", "?"))
        if r.get("error"):
            err_msg = str(r["error"])[:60]
            if verbose:
                print(f"{_col(bid,4)}  {_col('',38)}  {_col('',12)}  {_col('',10)}  {_col('',8)}  ERROR: {err_msg}")
            else:
                print(f"{_col(bid,4)}  {_col('',12)}  {_col('',8)}  ERROR: {err_msg}")
        else:
            algo = r.get("algoritmo", "?")
            total = str(r.get("total_sincronizadas", 0))
            tc = f"{r.get('tipo_cambio_aplicado', 0):.4f}"
            nombre = r.get("nombre", "")
            if verbose:
                print(f"{_col(bid,4)}  {_col(nombre,38)}  {_col(algo,12)}  {_col(tc,10)}  {_col(total,8)}  OK")
            else:
                print(f"{_col(bid,4)}  {_col(algo,12)}  {_col(total,8)}  OK  (TC={tc})")

    print(sep)
    print(f"  Bancos procesados     : {total_bancos}")
    print(f"  Cuentas en ASFI       : {total_cuentas}")
    print(f"  Bancos con error      : {total_errors}")
    print(f"  Tiempo total          : {elapsed:.2f}s")
    if total_bancos > 0:
        print(f"  Tiempo por banco      : ~{elapsed / total_bancos:.2f}s (promedio paralelo)")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Barrido paralelo ASFI — persiste saldos convertidos SÓLO en base central."
    )
    parser.add_argument(
        "--asfi",
        default="http://localhost:9000",
        help="URL base del servicio ASFI (default: http://localhost:9000)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout de lectura en segundos. Usa 0 para sin límite. Default: 1800",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Muestra nombre del banco y tipo de cambio aplicado por banco",
    )
    args = parser.parse_args()

    asfi_url = args.asfi.rstrip("/")
    req_timeout = build_timeout(args.timeout)

    print("=" * 65)
    print("  BARRIDO PARALELO — Plataforma ASFI")
    print(f"  Endpoint : {asfi_url}/sweep")
    if req_timeout is None:
        print("  Timeout  : sin límite")
    else:
        print(f"  Timeout  : conexión=10s / lectura={args.timeout}s")
    print("  Flujo    : BCB → 14 bancos en paralelo → sólo ASFI")
    print("=" * 65)

    t0 = time.time()

    try:
        resp = requests.post(f"{asfi_url}/sweep", timeout=req_timeout)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"\nERROR: No se pudo conectar a {asfi_url}")
        print("Asegúrate de que el servicio ASFI esté corriendo (puerto 9000).")
        sys.exit(1)
    except requests.exceptions.ReadTimeout:
        print(f"\nERROR: El barrido excedió el timeout de lectura ({args.timeout}s).")
        print("Sube el timeout con --timeout 3600 o usa --timeout 0.")
        sys.exit(1)
    except requests.exceptions.HTTPError:
        print(f"\nERROR HTTP {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)

    elapsed = time.time() - t0

    try:
        data = resp.json()
    except Exception:
        print("\nERROR: La respuesta no es JSON válido.")
        print(resp.text[:2000])
        sys.exit(1)

    print_results(data, elapsed, verbose=args.verbose)

    print("=" * 65)
    if data.get("total_bancos_con_error", 1) == 0:
        print("  BARRIDO COMPLETADO SIN ERRORES")
    else:
        print(f"  BARRIDO COMPLETADO CON {data.get('total_bancos_con_error')} ERROR(ES)")
    print("=" * 65)

    sys.exit(0 if data.get("total_bancos_con_error", 1) == 0 else 1)


if __name__ == "__main__":
    main()
