"""
ASFI Service - Plataforma central de supervisión.

Flujo de barrido:
  1. ASFI obtiene tipo de cambio del BCB  (rate_client)
  2. ASFI barre los 14 bancos en paralelo (bank_client  → lectura paralela)
  3. Calcula saldo convertido a Bs         (conversion_service)
  4. Guarda SÓLO en la base central ASFI   (persistence_service)

Los saldos convertidos NO se escriben de vuelta en las bases de los bancos.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from audit_service import get_audit_file_path, write_audit_log
from bank_client import fetch_bank_accounts          # lectura paralela
from config import PORT, SERVICE_NAME
from conversion_service import convert_usd_to_bs     # conversión
from database.connection import SessionLocal, get_db
from decryption_service import decrypt_account_payload
from persistence_service import upsert_asfi_account  # persistencia exclusiva ASFI
from rate_client import fetch_current_rate            # tipo de cambio
from verification_service import generate_verification_code

app = FastAPI(title=SERVICE_NAME)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _safe_audit(**kwargs):
    """Escribe auditoría sin interrumpir el flujo principal."""
    try:
        write_audit_log(**kwargs)
    except Exception:
        pass


def _fetch_bank_row(db: Session, banco_id: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE banco_id = :banco_id AND is_deleted = FALSE
            """
        ),
        {"banco_id": banco_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail=f"Banco {banco_id} no encontrado")
    return dict(row)


# ---------------------------------------------------------------------------
# Núcleo del barrido por banco (usado en sweep paralelo)
# ---------------------------------------------------------------------------

def _process_bank(bank_row: dict, db: Session) -> dict:
    """
    Pipeline completo para un banco:
      lectura → descifrado → tipo de cambio → conversión → persistencia ASFI
    """
    banco_id = int(bank_row["banco_id"])

    # 1. Lectura paralela: obtiene cuentas cifradas del banco
    encrypted_accounts = fetch_bank_accounts(bank_row["endpoint_api"], limit=None)

    # 2. Descifrado
    decrypted_accounts = [
        decrypt_account_payload(banco_id, account)
        for account in encrypted_accounts
    ]

    # 3. Tipo de cambio (una sola consulta BCB por banco para coherencia)
    tipo_cambio = Decimal(str(fetch_current_rate()))
    fecha_conversion = datetime.utcnow()

    # 4. Conversión + 5. Persistencia exclusiva en ASFI
    synced_count = 0
    for account in decrypted_accounts:
        codigo_verificacion = generate_verification_code()
        saldo_bs = convert_usd_to_bs(account["saldo_usd_original"], tipo_cambio)

        upsert_asfi_account(
            db,
            cuenta_id=account["cuenta_id"],
            banco_id=account["banco_id"],
            ci=account["ci"],
            nombre=account["nombre"],
            apellido=account["apellido"],
            numero_cuenta=account["numero_cuenta"],
            saldo_usd_original=account["saldo_usd_original"],
            saldo_bs=saldo_bs,
            tipo_cambio_aplicado=tipo_cambio,
            codigo_verificacion=codigo_verificacion,
            fecha_conversion=fecha_conversion,
            estado="CONVERTIDO",
        )

        _safe_audit(
            evento="SWEEP_ACCOUNT",
            banco_id=banco_id,
            cuenta_id=account["cuenta_id"],
            tipo_cambio_aplicado=tipo_cambio,
            codigo_verificacion=codigo_verificacion,
            estado="OK",
            detalle="Cuenta convertida y persistida en ASFI (barrido paralelo)",
            extra={
                "saldo_usd_original": str(account["saldo_usd_original"]),
                "saldo_bs": str(saldo_bs),
                "algoritmo": account.get("algoritmo", ""),
                "fecha_conversion": fecha_conversion.isoformat(),
            },
        )
        synced_count += 1

    db.commit()

    return {
        "banco_id": banco_id,
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "total_sincronizadas": synced_count,
        "tipo_cambio_aplicado": float(tipo_cambio),
    }


def _process_bank_safe(bank_row: dict) -> dict:
    """Wrapper con sesión propia para ThreadPoolExecutor."""
    db = SessionLocal()
    try:
        return _process_bank(dict(bank_row), db)
    except Exception as exc:
        db.rollback()
        _safe_audit(
            evento="SWEEP_ACCOUNT_ERROR",
            banco_id=bank_row["banco_id"],
            cuenta_id=-1,
            tipo_cambio_aplicado="N/A",
            codigo_verificacion=None,
            estado="ERROR",
            detalle=str(exc),
            extra={},
        )
        return {"banco_id": bank_row["banco_id"], "error": str(exc)}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"service": SERVICE_NAME, "status": "ok", "port": PORT}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"service": SERVICE_NAME, "status": "ok", "database": "connected"}


@app.get("/bcb/rate")
def get_bcb_rate():
    """Consulta el tipo de cambio actual del BCB."""
    try:
        rate = fetch_current_rate()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"No se pudo consultar el BCB: {exc}") from exc

    return {"status": "ok", "rate": rate, "currency_from": "USD", "currency_to": "BOB"}


@app.get("/banks")
def get_banks(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE is_deleted = FALSE
            ORDER BY banco_id
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


@app.get("/banks/{banco_id}/accounts")
def get_bank_accounts(
    banco_id: int,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retorna las cuentas cifradas directamente del banco."""
    bank_row = _fetch_bank_row(db, banco_id)

    try:
        accounts = fetch_bank_accounts(bank_row["endpoint_api"], limit=limit, offset=offset)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error consultando banco {banco_id}: {exc}") from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "total_cuentas": len(accounts),
        "accounts": accounts,
    }


@app.get("/banks/{banco_id}/accounts/decrypted")
def get_decrypted_accounts(
    banco_id: int,
    limit: int | None = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retorna las cuentas descifradas de un banco (sólo lectura, sin persistir)."""
    bank_row = _fetch_bank_row(db, banco_id)

    try:
        encrypted = fetch_bank_accounts(bank_row["endpoint_api"], limit=limit, offset=offset)
        decrypted = [decrypt_account_payload(banco_id, a) for a in encrypted]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error descifrado banco {banco_id}: {exc}") from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "total_cuentas": len(decrypted),
        "accounts": decrypted,
    }


@app.get("/banks/{banco_id}/accounts/converted")
def get_converted_accounts(
    banco_id: int,
    limit: int | None = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retorna las cuentas con saldo convertido a Bs (sólo lectura, sin persistir)."""
    bank_row = _fetch_bank_row(db, banco_id)

    try:
        encrypted = fetch_bank_accounts(bank_row["endpoint_api"], limit=limit, offset=offset)
        decrypted = [decrypt_account_payload(banco_id, a) for a in encrypted]
        tipo_cambio = fetch_current_rate()

        converted = []
        for account in decrypted:
            saldo_bs = convert_usd_to_bs(account["saldo_usd_original"], tipo_cambio)
            converted.append({
                "cuenta_id": account["cuenta_id"],
                "banco_id": account["banco_id"],
                "algoritmo": account.get("algoritmo"),
                "ci": account["ci"],
                "nombre": account["nombre"],
                "apellido": account["apellido"],
                "numero_cuenta": account["numero_cuenta"],
                "saldo_usd_original": account["saldo_usd_original"],
                "tipo_cambio_aplicado": tipo_cambio,
                "saldo_bs_convertido": saldo_bs,
                "saldo_usd_encrypted": account.get("saldo_usd_encrypted"),
            })
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Error conversión banco {banco_id}: {exc}") from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "tipo_cambio_aplicado": tipo_cambio,
        "total_cuentas": len(converted),
        "accounts": converted,
    }


@app.post("/banks/{banco_id}/accounts/persist")
def persist_bank_accounts_in_asfi(
    banco_id: int,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Lee, convierte y persiste las cuentas de un banco en la base central ASFI.
    No escribe nada en la base del banco.
    """
    bank_row = _fetch_bank_row(db, banco_id)

    try:
        encrypted = fetch_bank_accounts(bank_row["endpoint_api"], limit=limit, offset=offset)
        decrypted = [decrypt_account_payload(banco_id, a) for a in encrypted]

        tipo_cambio = Decimal(str(fetch_current_rate()))
        fecha_conversion = datetime.utcnow()

        persisted = []
        for account in decrypted:
            codigo_verificacion = generate_verification_code()
            saldo_bs = convert_usd_to_bs(account["saldo_usd_original"], tipo_cambio)

            upsert_asfi_account(
                db,
                cuenta_id=account["cuenta_id"],
                banco_id=account["banco_id"],
                ci=account["ci"],
                nombre=account["nombre"],
                apellido=account["apellido"],
                numero_cuenta=account["numero_cuenta"],
                saldo_usd_original=account["saldo_usd_original"],
                saldo_bs=saldo_bs,
                tipo_cambio_aplicado=tipo_cambio,
                codigo_verificacion=codigo_verificacion,
                fecha_conversion=fecha_conversion,
                estado="CONVERTIDO",
            )

            _safe_audit(
                evento="PERSIST_ACCOUNT",
                banco_id=banco_id,
                cuenta_id=account["cuenta_id"],
                tipo_cambio_aplicado=tipo_cambio,
                codigo_verificacion=codigo_verificacion,
                estado="OK",
                detalle="Cuenta persistida en ASFI",
                extra={
                    "saldo_usd_original": str(account["saldo_usd_original"]),
                    "saldo_bs": str(saldo_bs),
                    "algoritmo": account.get("algoritmo", ""),
                    "fecha_conversion": fecha_conversion.isoformat(),
                },
            )

            persisted.append({
                "cuenta_id": account["cuenta_id"],
                "banco_id": account["banco_id"],
                "codigo_verificacion": codigo_verificacion,
                "saldo_usd_original": account["saldo_usd_original"],
                "tipo_cambio_aplicado": tipo_cambio,
                "saldo_bs": saldo_bs,
                "fecha_conversion": fecha_conversion,
            })

        db.commit()

    except Exception as exc:
        db.rollback()
        _safe_audit(
            evento="PERSIST_ACCOUNT_ERROR",
            banco_id=banco_id,
            cuenta_id=-1,
            tipo_cambio_aplicado="N/A",
            codigo_verificacion=None,
            estado="ERROR",
            detalle=f"Error persistiendo banco {banco_id}: {exc}",
            extra={"limit": limit, "offset": offset},
        )
        raise HTTPException(status_code=502, detail=f"Error persistiendo banco {banco_id}: {exc}") from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "total_persistidas": len(persisted),
        "accounts": persisted,
    }


@app.post("/sweep")
def sweep_all_banks(db: Session = Depends(get_db)):
    """
    Barrido paralelo completo.

    1. Obtiene tipo de cambio BCB.
    2. Barre los 14 bancos simultáneamente con ThreadPoolExecutor.
    3. Persiste resultados SÓLO en la base central ASFI.
    """
    banks = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api
            FROM bancos
            WHERE is_deleted = FALSE
            ORDER BY banco_id
            """
        )
    ).mappings().all()

    bank_rows = [dict(r) for r in banks]

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(bank_rows)) as executor:
        futures = {executor.submit(_process_bank_safe, row): row["banco_id"] for row in bank_rows}
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda x: x["banco_id"])

    total_synced = sum(r.get("total_sincronizadas", 0) for r in results)
    total_errors = sum(1 for r in results if "error" in r)

    return {
        "total_bancos": len(results),
        "total_cuentas_sincronizadas": total_synced,
        "total_bancos_con_error": total_errors,
        "results": results,
    }


@app.get("/audit/path")
def audit_path():
    return {"audit_file": get_audit_file_path()}
