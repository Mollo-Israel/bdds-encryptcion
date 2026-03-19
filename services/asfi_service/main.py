from datetime import datetime
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from audit_service import get_audit_file_path, write_audit_log
from bank_client import fetch_bank_accounts, update_bank_account
from config import PORT, SERVICE_NAME
from conversion_service import convert_usd_to_bs
from database.connection import get_db
from decryption_service import decrypt_account_payload
from persistence_service import upsert_asfi_account
from rate_client import fetch_current_rate
from verification_service import generate_verification_code

app = FastAPI(title=SERVICE_NAME)


def _safe_write_audit(**kwargs):
    """
    Escribe auditoría sin romper el flujo principal.
    Si algo falla en el log, la operación principal sigue.
    """
    try:
        write_audit_log(**kwargs)
    except Exception:
        pass


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


@app.get("/audit/path")
def audit_path():
    return {
        "audit_file": get_audit_file_path()
    }