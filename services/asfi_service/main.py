from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from audit_service import get_audit_file_path, write_audit_log
from bank_client import fetch_bank_accounts, update_bank_account
from config import PORT, SERVICE_NAME
from conversion_service import convert_usd_to_bs
from database.connection import SessionLocal, get_db
from decryption_service import decrypt_account_payload
from persistence_service import upsert_asfi_account
from rate_client import fetch_current_rate
from verification_service import generate_verification_code

app = FastAPI(title=SERVICE_NAME)


def _safe_write_audit(**kwargs):
    """Escribe auditoría sin romper el flujo principal."""
    try:
        write_audit_log(**kwargs)
    except Exception:
        pass


def _sync_bank(bank_row: dict, db: Session) -> dict:
    """
    Ejecuta el ciclo completo persist+sync para un banco.
    Diseñado para ser llamado desde ThreadPoolExecutor con su propia sesión.
    """
    banco_id = int(bank_row["banco_id"])
    encrypted_accounts = fetch_bank_accounts(bank_row["endpoint_api"], limit=None)

    decrypted_accounts = [
        decrypt_account_payload(banco_id, account)
        for account in encrypted_accounts
    ]

    tipo_cambio = Decimal(str(fetch_current_rate()))
    fecha_conversion = datetime.utcnow()

    synced_count = 0
    for account in decrypted_accounts:
        codigo_verificacion = generate_verification_code()
        saldo_bs_convertido = convert_usd_to_bs(account["saldo_usd_original"], tipo_cambio)

        upsert_asfi_account(
            db,
            cuenta_id=account["cuenta_id"],
            banco_id=account["banco_id"],
            ci=account["ci"],
            nombre=account["nombre"],
            apellido=account["apellido"],
            numero_cuenta=account["numero_cuenta"],
            saldo_usd_original=account["saldo_usd_original"],
            saldo_bs=saldo_bs_convertido,
            tipo_cambio_aplicado=tipo_cambio,
            codigo_verificacion=codigo_verificacion,
            fecha_conversion=fecha_conversion,
            estado="CONVERTIDO",
        )

        update_bank_account(
            bank_row["endpoint_api"],
            cuenta_id=account["cuenta_id"],
            saldo_bs=saldo_bs_convertido,
            fecha_conversion=fecha_conversion,
            codigo_verificacion=codigo_verificacion,
        )

        _safe_write_audit(
            evento="SYNC_ACCOUNT",
            banco_id=account["banco_id"],
            cuenta_id=account["cuenta_id"],
            tipo_cambio_aplicado=tipo_cambio,
            codigo_verificacion=codigo_verificacion,
            estado="OK",
            detalle="Cuenta sincronizada (barrido paralelo)",
            extra={
                "saldo_usd_original": str(account["saldo_usd_original"]),
                "saldo_bs": str(saldo_bs_convertido),
                "algoritmo": account["algoritmo"],
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


def _sync_bank_safe(bank_row: dict) -> dict:
    """Wrapper con sesión propia para ThreadPoolExecutor."""
    db = SessionLocal()
    try:
        return _sync_bank(dict(bank_row), db)
    except Exception as exc:
        db.rollback()
        _safe_write_audit(
            evento="SYNC_ACCOUNT_ERROR",
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


@app.get("/")
def root():
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "port": PORT,
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "database": "connected",
    }


@app.get("/bcb/rate")
def get_bcb_rate():
    try:
        rate = fetch_current_rate()
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo consultar el BCB: {exc}",
        ) from exc

    return {
        "status": "ok",
        "rate": rate,
        "currency_from": "USD",
        "currency_to": "BOB",
    }


@app.get("/banks")
def get_banks(db: Session = Depends(get_db)):
    result = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE is_deleted = FALSE
            ORDER BY banco_id
            """
        )
    )

    rows = result.mappings().all()
    return [dict(row) for row in rows]


@app.get("/banks/{banco_id}/accounts")
def get_bank_accounts_from_asfi(
    banco_id: int,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    bank_row = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE banco_id = :banco_id
              AND is_deleted = FALSE
            """
        ),
        {"banco_id": banco_id},
    ).mappings().first()

    if not bank_row:
        raise HTTPException(status_code=404, detail=f"Banco {banco_id} no encontrado")

    try:
        accounts = fetch_bank_accounts(
            bank_row["endpoint_api"],
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo consultar el banco {banco_id}: {exc}",
        ) from exc

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
def get_decrypted_bank_accounts_from_asfi(
    banco_id: int,
    limit: int | None = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    bank_row = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE banco_id = :banco_id
              AND is_deleted = FALSE
            """
        ),
        {"banco_id": banco_id},
    ).mappings().first()

    if not bank_row:
        raise HTTPException(status_code=404, detail=f"Banco {banco_id} no encontrado")

    try:
        encrypted_accounts = fetch_bank_accounts(
            bank_row["endpoint_api"],
            limit=limit,
            offset=offset,
        )
        decrypted_accounts = [
            decrypt_account_payload(banco_id, account)
            for account in encrypted_accounts
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo consultar/descifrar el banco {banco_id}: {exc}",
        ) from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "total_cuentas": len(decrypted_accounts),
        "accounts": decrypted_accounts,
    }


@app.get("/banks/{banco_id}/accounts/converted")
def get_converted_bank_accounts_from_asfi(
    banco_id: int,
    limit: int | None = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    bank_row = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE banco_id = :banco_id
              AND is_deleted = FALSE
            """
        ),
        {"banco_id": banco_id},
    ).mappings().first()

    if not bank_row:
        raise HTTPException(status_code=404, detail=f"Banco {banco_id} no encontrado")

    try:
        encrypted_accounts = fetch_bank_accounts(
            bank_row["endpoint_api"],
            limit=limit,
            offset=offset,
        )

        decrypted_accounts = [
            decrypt_account_payload(banco_id, account)
            for account in encrypted_accounts
        ]

        tipo_cambio = fetch_current_rate()

        converted_accounts = []
        for account in decrypted_accounts:
            saldo_bs_convertido = convert_usd_to_bs(
                account["saldo_usd_original"],
                tipo_cambio,
            )

            converted_accounts.append(
                {
                    "cuenta_id": account["cuenta_id"],
                    "banco_id": account["banco_id"],
                    "algoritmo": account["algoritmo"],
                    "ci": account["ci"],
                    "nombre": account["nombre"],
                    "apellido": account["apellido"],
                    "numero_cuenta": account["numero_cuenta"],
                    "saldo_usd_original": account["saldo_usd_original"],
                    "tipo_cambio_aplicado": tipo_cambio,
                    "saldo_bs_convertido": saldo_bs_convertido,
                    "saldo_usd_encrypted": account["saldo_usd_encrypted"],
                }
            )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo consultar/convertir el banco {banco_id}: {exc}",
        ) from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "tipo_cambio_aplicado": tipo_cambio,
        "total_cuentas": len(converted_accounts),
        "accounts": converted_accounts,
    }


@app.post("/banks/{banco_id}/accounts/persist")
def persist_converted_bank_accounts_in_asfi(
    banco_id: int,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    bank_row = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE banco_id = :banco_id
              AND is_deleted = FALSE
            """
        ),
        {"banco_id": banco_id},
    ).mappings().first()

    if not bank_row:
        raise HTTPException(status_code=404, detail=f"Banco {banco_id} no encontrado")

    try:
        encrypted_accounts = fetch_bank_accounts(
            bank_row["endpoint_api"],
            limit=limit,
            offset=offset,
        )

        decrypted_accounts = [
            decrypt_account_payload(banco_id, account)
            for account in encrypted_accounts
        ]

        tipo_cambio = Decimal(str(fetch_current_rate()))
        fecha_conversion = datetime.utcnow()

        persisted = []
        for account in decrypted_accounts:
            codigo_verificacion = generate_verification_code()
            saldo_bs_convertido = convert_usd_to_bs(
                account["saldo_usd_original"],
                tipo_cambio,
            )

            upsert_asfi_account(
                db,
                cuenta_id=account["cuenta_id"],
                banco_id=account["banco_id"],
                ci=account["ci"],
                nombre=account["nombre"],
                apellido=account["apellido"],
                numero_cuenta=account["numero_cuenta"],
                saldo_usd_original=account["saldo_usd_original"],
                saldo_bs=saldo_bs_convertido,
                tipo_cambio_aplicado=tipo_cambio,
                codigo_verificacion=codigo_verificacion,
                fecha_conversion=fecha_conversion,
                estado="CONVERTIDO",
            )

            _safe_write_audit(
                evento="PERSIST_ACCOUNT",
                banco_id=account["banco_id"],
                cuenta_id=account["cuenta_id"],
                tipo_cambio_aplicado=tipo_cambio,
                codigo_verificacion=codigo_verificacion,
                estado="OK",
                detalle="Cuenta persistida en ASFI",
                extra={
                    "saldo_usd_original": str(account["saldo_usd_original"]),
                    "saldo_bs": str(saldo_bs_convertido),
                    "algoritmo": account["algoritmo"],
                    "fecha_conversion": fecha_conversion.isoformat(),
                },
            )

            persisted.append(
                {
                    "cuenta_id": account["cuenta_id"],
                    "banco_id": account["banco_id"],
                    "codigo_verificacion": codigo_verificacion,
                    "saldo_usd_original": account["saldo_usd_original"],
                    "tipo_cambio_aplicado": tipo_cambio,
                    "saldo_bs": saldo_bs_convertido,
                    "fecha_conversion": fecha_conversion,
                }
            )

        db.commit()

    except Exception as exc:
        db.rollback()
        _safe_write_audit(
            evento="PERSIST_ACCOUNT_ERROR",
            banco_id=banco_id,
            cuenta_id=-1,
            tipo_cambio_aplicado="N/A",
            codigo_verificacion=None,
            estado="ERROR",
            detalle=f"No se pudo persistir en ASFI el banco {banco_id}: {exc}",
            extra={"limit": limit, "offset": offset},
        )
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo persistir en ASFI el banco {banco_id}: {exc}",
        ) from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "total_persistidas": len(persisted),
        "accounts": persisted,
    }


@app.post("/banks/{banco_id}/accounts/sync")
def sync_bank_accounts_between_asfi_and_bank(
    banco_id: int,
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    bank_row = db.execute(
        text(
            """
            SELECT banco_id, nombre, algoritmo, endpoint_api, version_llave
            FROM bancos
            WHERE banco_id = :banco_id
              AND is_deleted = FALSE
            """
        ),
        {"banco_id": banco_id},
    ).mappings().first()

    if not bank_row:
        raise HTTPException(status_code=404, detail=f"Banco {banco_id} no encontrado")

    try:
        encrypted_accounts = fetch_bank_accounts(
            bank_row["endpoint_api"],
            limit=limit,
            offset=offset,
        )

        decrypted_accounts = [
            decrypt_account_payload(banco_id, account)
            for account in encrypted_accounts
        ]

        tipo_cambio = Decimal(str(fetch_current_rate()))
        fecha_conversion = datetime.utcnow()

        synced = []
        for account in decrypted_accounts:
            codigo_verificacion = generate_verification_code()
            saldo_bs_convertido = convert_usd_to_bs(
                account["saldo_usd_original"],
                tipo_cambio,
            )

            upsert_asfi_account(
                db,
                cuenta_id=account["cuenta_id"],
                banco_id=account["banco_id"],
                ci=account["ci"],
                nombre=account["nombre"],
                apellido=account["apellido"],
                numero_cuenta=account["numero_cuenta"],
                saldo_usd_original=account["saldo_usd_original"],
                saldo_bs=saldo_bs_convertido,
                tipo_cambio_aplicado=tipo_cambio,
                codigo_verificacion=codigo_verificacion,
                fecha_conversion=fecha_conversion,
                estado="CONVERTIDO",
            )

            bank_update_response = update_bank_account(
                bank_row["endpoint_api"],
                cuenta_id=account["cuenta_id"],
                saldo_bs=saldo_bs_convertido,
                fecha_conversion=fecha_conversion,
                codigo_verificacion=codigo_verificacion,
            )

            _safe_write_audit(
                evento="SYNC_ACCOUNT",
                banco_id=account["banco_id"],
                cuenta_id=account["cuenta_id"],
                tipo_cambio_aplicado=tipo_cambio,
                codigo_verificacion=codigo_verificacion,
                estado="OK",
                detalle="Cuenta sincronizada entre ASFI y banco",
                extra={
                    "saldo_usd_original": str(account["saldo_usd_original"]),
                    "saldo_bs": str(saldo_bs_convertido),
                    "algoritmo": account["algoritmo"],
                    "fecha_conversion": fecha_conversion.isoformat(),
                    "bank_update_response": bank_update_response,
                },
            )

            synced.append(
                {
                    "cuenta_id": account["cuenta_id"],
                    "banco_id": account["banco_id"],
                    "codigo_verificacion": codigo_verificacion,
                    "saldo_usd_original": account["saldo_usd_original"],
                    "tipo_cambio_aplicado": tipo_cambio,
                    "saldo_bs": saldo_bs_convertido,
                    "fecha_conversion": fecha_conversion,
                    "bank_update_response": bank_update_response,
                }
            )

        db.commit()

    except Exception as exc:
        db.rollback()
        _safe_write_audit(
            evento="SYNC_ACCOUNT_ERROR",
            banco_id=banco_id,
            cuenta_id=-1,
            tipo_cambio_aplicado="N/A",
            codigo_verificacion=None,
            estado="ERROR",
            detalle=f"No se pudo sincronizar ASFI con el banco {banco_id}: {exc}",
            extra={"limit": limit, "offset": offset},
        )
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo sincronizar ASFI con el banco {banco_id}: {exc}",
        ) from exc

    return {
        "banco_id": bank_row["banco_id"],
        "nombre": bank_row["nombre"],
        "algoritmo": bank_row["algoritmo"],
        "limit": limit,
        "offset": offset,
        "total_sincronizadas": len(synced),
        "accounts": synced,
    }


@app.post("/sweep")
def sweep_all_banks(db: Session = Depends(get_db)):
    """
    Barrido paralelo completo: sincroniza todos los bancos activos en paralelo.
    Usa ThreadPoolExecutor para procesar los 14 bancos simultáneamente.
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

    bank_rows = [dict(row) for row in banks]

    results = []
    with ThreadPoolExecutor(max_workers=len(bank_rows)) as executor:
        futures = {
            executor.submit(_sync_bank_safe, row): row["banco_id"]
            for row in bank_rows
        }
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
    return {
        "audit_file": get_audit_file_path()
    }
