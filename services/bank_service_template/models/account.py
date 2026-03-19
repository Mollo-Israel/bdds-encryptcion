from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)

from database.connection import Base


class AccountORM(Base):
    __tablename__ = "cuentas"
    __table_args__ = (
        UniqueConstraint("banco_id", "numero_cuenta", name="uq_cuentas_banco_numero"),
        Index("idx_cuentas_ci", "ci"),
        Index("idx_cuentas_banco_id", "banco_id"),
        Index("idx_cuentas_numero_cuenta", "numero_cuenta"),
        Index("idx_cuentas_fecha_conversion", "fecha_conversion"),
    )

    cuenta_id = Column(BigInteger, primary_key=True, autoincrement=False)
    banco_id = Column(Integer, nullable=False)
    ci = Column(String(64), nullable=False)
    nombre = Column(String(150), nullable=False)
    apellido = Column(String(150), nullable=False)
    numero_cuenta = Column(String(128), nullable=False)
    saldo_usd_encrypted = Column(Text, nullable=False)
    saldo_bs = Column(Numeric(18, 4), nullable=True)
    codigo_verificacion = Column(String(8), nullable=True)
    fecha_conversion = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class AccountResponse(BaseModel):
    cuenta_id: int
    banco_id: int
    ci: str
    nombre: str
    apellido: str
    numero_cuenta: str
    saldo_usd_encrypted: str

    model_config = ConfigDict(from_attributes=True)


class AccountUpdateRequest(BaseModel):
    cuenta_id: int
    saldo_bs: Decimal
    fecha_conversion: datetime
    codigo_verificacion: str


class AccountUpdateResponse(BaseModel):
    cuenta_id: int
    status: str
    codigo_verificacion: str