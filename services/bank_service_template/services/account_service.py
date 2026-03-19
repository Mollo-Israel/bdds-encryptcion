import random
import string
from decimal import Decimal
from datetime import datetime
from types import SimpleNamespace
from typing import Any

from pymongo import ReturnDocument
from sqlalchemy.orm import Session

from config import BANK_ID, DB_ENGINE
from models.account import AccountORM, AccountUpdateRequest
from services.encryption_service import encryption_service


def _generate_verification_code() -> str:
    return "".join(random.choices(string.digits + "ABCDEF", k=8))


def get_all_accounts(db, limit: int | None = None, offset: int = 0) -> list[dict[str, Any]]:
    limit = None if limit is None or limit <= 0 else int(limit)
    offset = max(int(offset or 0), 0)

    if DB_ENGINE == "mongodb":
        cursor = (
            db["cuentas"]
            .find({}, {"_id": 0})
            .sort("cuenta_id", 1)
            .skip(offset)
        )

        if limit is not None:
            cursor = cursor.limit(limit)

        return list(cursor)

    if DB_ENGINE == "cassandra":
        # Cassandra no soporta OFFSET de forma nativa.
        # Para no romper lo actual, se mantiene compatibilidad
        # y se hace slicing en memoria.
        rows = db.execute("""
            SELECT cuenta_id, banco_id, ci, nombre, apellido, numero_cuenta, saldo_usd_encrypted
            FROM cuentas
        """)
        rows_list = list(rows)

        if offset:
            rows_list = rows_list[offset:]

        if limit is not None:
            rows_list = rows_list[:limit]

        return list(rows_list)

    query = db.query(AccountORM).order_by(AccountORM.cuenta_id)

    if offset:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    rows = query.all()
    return [
        {
            "cuenta_id": row.cuenta_id,
            "banco_id": row.banco_id,
            "ci": row.ci,
            "nombre": row.nombre,
            "apellido": row.apellido,
            "numero_cuenta": row.numero_cuenta,
            "saldo_usd_encrypted": row.saldo_usd_encrypted,
        }
        for row in rows
    ]


def load_accounts(db, accounts_data: list[dict]) -> int:
    inserted = 0

    if DB_ENGINE == "mongodb":
        collection = db["cuentas"]

        for item in accounts_data:
            cuenta_id = int(item["cuenta_id"])
            existing = collection.find_one({"cuenta_id": cuenta_id})
            if existing:
                continue

            doc = {
                "cuenta_id": cuenta_id,
                "banco_id": BANK_ID,
                "ci": encryption_service.encrypt(str(item["ci"])),
                "nombre": str(item["nombre"]),
                "apellido": str(item["apellido"]),
                "numero_cuenta": encryption_service.encrypt(str(item["numero_cuenta"])),
                "saldo_usd_encrypted": encryption_service.encrypt(str(item["saldo_usd"])),
                "saldo_bs": None,
                "codigo_verificacion": None,
                "fecha_conversion": None,
            }

            collection.insert_one(doc)
            inserted += 1

        return inserted

    if DB_ENGINE == "cassandra":
        for item in accounts_data:
            cuenta_id = int(item["cuenta_id"])

            existing = db.execute(
                "SELECT cuenta_id FROM cuentas WHERE cuenta_id = %s",
                (cuenta_id,)
            ).one()

            if existing:
                continue

            db.execute("""
                INSERT INTO cuentas (
                    cuenta_id, banco_id, ci, nombre, apellido,
                    numero_cuenta, saldo_usd_encrypted,
                    saldo_bs, codigo_verificacion, fecha_conversion,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cuenta_id,
                BANK_ID,
                encryption_service.encrypt(str(item["ci"])),
                str(item["nombre"]),
                str(item["apellido"]),
                encryption_service.encrypt(str(item["numero_cuenta"])),
                encryption_service.encrypt(str(item["saldo_usd"])),
                None,
                None,
                None,
                datetime.utcnow(),
                datetime.utcnow(),
            ))
            inserted += 1

        return inserted

    for item in accounts_data:
        cuenta_id = int(item["cuenta_id"])

        existing = (
            db.query(AccountORM)
            .filter(AccountORM.cuenta_id == cuenta_id)
            .first()
        )
        if existing:
            continue

        account = AccountORM(
            cuenta_id=cuenta_id,
            banco_id=BANK_ID,
            ci=encryption_service.encrypt(str(item["ci"])),
            nombre=str(item["nombre"]),
            apellido=str(item["apellido"]),
            numero_cuenta=encryption_service.encrypt(str(item["numero_cuenta"])),
            saldo_usd_encrypted=encryption_service.encrypt(str(item["saldo_usd"])),
        )

        db.add(account)
        inserted += 1

    db.commit()
    return inserted


def update_account(db, payload: AccountUpdateRequest):
    if DB_ENGINE == "mongodb":
        updated = db["cuentas"].find_one_and_update(
            {"cuenta_id": payload.cuenta_id},
            {
                "$set": {
                    "saldo_bs": float(payload.saldo_bs),
                    "fecha_conversion": payload.fecha_conversion,
                    "codigo_verificacion": payload.codigo_verificacion,
                }
            },
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )

        if not updated:
            return None

        return SimpleNamespace(
            cuenta_id=updated["cuenta_id"],
            codigo_verificacion=updated.get("codigo_verificacion"),
        )

    if DB_ENGINE == "cassandra":
        existing = db.execute(
            "SELECT cuenta_id FROM cuentas WHERE cuenta_id = %s",
            (payload.cuenta_id,)
        ).one()

        if not existing:
            return None

        db.execute("""
            UPDATE cuentas
            SET saldo_bs = %s,
                fecha_conversion = %s,
                codigo_verificacion = %s,
                updated_at = %s
            WHERE cuenta_id = %s
        """, (
            Decimal(str(payload.saldo_bs)),
            payload.fecha_conversion,
            payload.codigo_verificacion,
            datetime.utcnow(),
            payload.cuenta_id,
        ))

        return SimpleNamespace(
            cuenta_id=payload.cuenta_id,
            codigo_verificacion=payload.codigo_verificacion,
        )

    account = db.query(AccountORM).filter(AccountORM.cuenta_id == payload.cuenta_id).first()
    if not account:
        return None

    account.saldo_bs = Decimal(str(payload.saldo_bs))
    account.fecha_conversion = payload.fecha_conversion
    account.codigo_verificacion = payload.codigo_verificacion
    db.commit()
    db.refresh(account)
    return account