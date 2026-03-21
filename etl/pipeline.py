"""
Pipeline ETL completo:
  1. dataset_loader  → lee el CSV de input, limpia y genera dataset_clean.csv
  2. bank_router     → lee dataset_clean.csv y carga cada banco via API

Ejecutar desde la raíz del proyecto:
    python etl/pipeline.py
"""

import sys
import os

# El pipeline se ejecuta desde la raíz; añadimos etl/ al path para los imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dataset_loader
import bank_router


def main():
    print("=" * 70)
    print("PIPELINE ETL - INICIO")
    print("=" * 70)

    print()
    print(">>> PASO 1: LIMPIEZA DEL DATASET")
    print("-" * 70)
    dataset_loader.main()

    print()
    print(">>> PASO 2: CARGA A BASES BANCARIAS")
    print("-" * 70)
    bank_router.main()

    print()
    print("=" * 70)
    print("PIPELINE ETL - FINALIZADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
