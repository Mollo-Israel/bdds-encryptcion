from decimal import Decimal, ROUND_HALF_UP


FOUR_DECIMALS = Decimal("0.0001")


def convert_usd_to_bs(saldo_usd_original: Decimal, tipo_cambio: float | Decimal) -> Decimal:
    usd = Decimal(str(saldo_usd_original))
    rate = Decimal(str(tipo_cambio))

    saldo_bs = usd * rate
    return saldo_bs.quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)