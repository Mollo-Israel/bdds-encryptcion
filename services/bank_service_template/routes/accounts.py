from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from models.account import AccountResponse, AccountUpdateRequest, AccountUpdateResponse
from services import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


class LoadRequest(BaseModel):
    accounts: list[dict]


class LoadResponse(BaseModel):
    inserted: int
    status: str


@router.post("/load", response_model=LoadResponse)
def load_accounts(payload: LoadRequest, db: Session = Depends(get_db)):
    """Carga cuentas en texto plano, las cifra y las persiste en la BD del banco."""
    inserted = account_service.load_accounts(db, payload.accounts)
    return LoadResponse(inserted=inserted, status="ok")


@router.get("", response_model=list[AccountResponse])
def get_accounts(db: Session = Depends(get_db)):
    """Devuelve todas las cuentas con saldo cifrado."""
    return account_service.get_all_accounts(db)


@router.post("/update", response_model=AccountUpdateResponse)
def update_account(payload: AccountUpdateRequest, db: Session = Depends(get_db)):
    """Actualiza el saldo convertido en Bs. para una cuenta."""
    account = account_service.update_account(db, payload)
    if not account:
        raise HTTPException(status_code=404, detail=f"Cuenta {payload.cuenta_id} no encontrada")
    return AccountUpdateResponse(
        cuenta_id=account.cuenta_id,
        status="updated",
        codigo_verificacion=account.codigo_verificacion,
    )
