from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_asfi_auth
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


@router.get("", response_model=list[AccountResponse], dependencies=[Depends(require_asfi_auth)])
def get_accounts(
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Devuelve cuentas con saldo cifrado. Requiere autenticación ASFI.
    Soporta lectura por lotes con limit y offset.
    """
    return account_service.get_all_accounts(db, limit=limit, offset=offset)


@router.post("/update", response_model=AccountUpdateResponse, dependencies=[Depends(require_asfi_auth)])
def update_account(payload: AccountUpdateRequest, db: Session = Depends(get_db)):
    """Actualiza el saldo convertido en Bs. para una cuenta. Requiere autenticación ASFI."""
    account = account_service.update_account(db, payload)
    if not account:
        raise HTTPException(status_code=404, detail=f"Cuenta {payload.cuenta_id} no encontrada")
    return AccountUpdateResponse(
        cuenta_id=account.cuenta_id,
        status="updated",
        codigo_verificacion=account.codigo_verificacion,
    )