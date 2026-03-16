from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import BigInteger, Column, DateTime, Integer, String

from database.connection import Base


# ORM — tabla en la BD del banco
class AccountORM(Base):
    __tablename__ = "cuentas"

    cuenta_id = Column(BigInteger, primary_key=True, index=True)
    banco_id = Column(Integer, nullable=False)
    saldo_usd_cifrado = Column(String(512), nullable=False)   # saldo cifrado
    saldo_bs = Column(String(512), nullable=True)             # saldo convertido (cifrado)
    fecha_conversion = Column(DateTime, nullable=True)
    codigo_verificacion = Column(String(8), nullable=True)


# Pydantic — respuesta al exponer cuenta cifrada
class AccountResponse(BaseModel):
    cuenta_id: int
    banco_id: int
    saldo_usd_cifrado: str

    model_config = {"from_attributes": True}


# Pydantic — body para actualizar saldo convertido
class AccountUpdateRequest(BaseModel):
    cuenta_id: int
    saldo_bs: str
    fecha_conversion: datetime
    codigo_verificacion: str


# Pydantic — confirmación de actualización
class AccountUpdateResponse(BaseModel):
    cuenta_id: int
    status: str
    codigo_verificacion: str
