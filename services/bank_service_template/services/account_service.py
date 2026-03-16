import random
import string
from datetime import datetime

from sqlalchemy.orm import Session

from config import BANK_ID
from models.account import AccountORM, AccountUpdateRequest
from services.encryption_service import encryption_service


def _generate_verification_code() -> str:
    """Genera código de 8 caracteres hexadecimales (0-9, A-F)."""
    return "".join(random.choices(string.digits + "ABCDEF", k=8))


def get_all_accounts(db: Session) -> list[AccountORM]:
    return db.query(AccountORM).all()


def load_accounts(db: Session, accounts_data: list[dict]) -> int:
    """
    Recibe lista de cuentas en texto plano, las cifra y las inserta en la BD.
    Retorna la cantidad de registros insertados.
    """
    inserted = 0
    for item in accounts_data:
        existing = db.query(AccountORM).filter(AccountORM.cuenta_id == item["cuenta_id"]).first()
        if existing:
            continue
        account = AccountORM(
            cuenta_id=item["cuenta_id"],
            banco_id=BANK_ID,
            saldo_usd_cifrado=encryption_service.encrypt(str(item["saldo_usd"])),
        )
        db.add(account)
        inserted += 1
    db.commit()
    return inserted


def update_account(db: Session, payload: AccountUpdateRequest) -> AccountORM | None:
    account = db.query(AccountORM).filter(AccountORM.cuenta_id == payload.cuenta_id).first()
    if not account:
        return None
    account.saldo_bs = payload.saldo_bs
    account.fecha_conversion = payload.fecha_conversion
    account.codigo_verificacion = payload.codigo_verificacion
    db.commit()
    db.refresh(account)
    return account
