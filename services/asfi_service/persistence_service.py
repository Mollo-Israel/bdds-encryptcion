from datetime import datetime
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session


def upsert_asfi_account(
    db: Session,
    *,
    cuenta_id: int,
    banco_id: int,
    ci: str,
    nombre: str,
    apellido: str,
    numero_cuenta: str,
    saldo_usd_original: Decimal,
    saldo_bs: Decimal,
    tipo_cambio_aplicado: Decimal,
    codigo_verificacion: str | None,
    fecha_conversion: datetime | None,
    estado: str = "CONVERTIDO",
) -> None:
    db.execute(
        text(
            """
            INSERT INTO cuentas (
                cuenta_id,
                banco_id,
                ci,
                nombre,
                apellido,
                numero_cuenta,
                saldo_usd_original,
                saldo_bs,
                tipo_cambio_aplicado,
                codigo_verificacion,
                fecha_conversion,
                estado,
                created_at,
                updated_at,
                created_by,
                updated_by,
                is_deleted
            )
            VALUES (
                :cuenta_id,
                :banco_id,
                :ci,
                :nombre,
                :apellido,
                :numero_cuenta,
                :saldo_usd_original,
                :saldo_bs,
                :tipo_cambio_aplicado,
                :codigo_verificacion,
                :fecha_conversion,
                :estado,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP,
                'ASFI',
                'ASFI',
                FALSE
            )
            ON CONFLICT (banco_id, cuenta_id)
            DO UPDATE SET
                ci = EXCLUDED.ci,
                nombre = EXCLUDED.nombre,
                apellido = EXCLUDED.apellido,
                numero_cuenta = EXCLUDED.numero_cuenta,
                saldo_usd_original = EXCLUDED.saldo_usd_original,
                saldo_bs = EXCLUDED.saldo_bs,
                tipo_cambio_aplicado = EXCLUDED.tipo_cambio_aplicado,
                codigo_verificacion = EXCLUDED.codigo_verificacion,
                fecha_conversion = EXCLUDED.fecha_conversion,
                estado = EXCLUDED.estado,
                updated_at = CURRENT_TIMESTAMP,
                updated_by = 'ASFI',
                is_deleted = FALSE
            """
        ),
        {
            "cuenta_id": int(cuenta_id),
            "banco_id": int(banco_id),
            "ci": str(ci),
            "nombre": str(nombre),
            "apellido": str(apellido),
            "numero_cuenta": str(numero_cuenta),
            "saldo_usd_original": Decimal(str(saldo_usd_original)),
            "saldo_bs": Decimal(str(saldo_bs)),
            "tipo_cambio_aplicado": Decimal(str(tipo_cambio_aplicado)),
            "codigo_verificacion": codigo_verificacion,
            "fecha_conversion": fecha_conversion,
            "estado": estado,
        },
    )