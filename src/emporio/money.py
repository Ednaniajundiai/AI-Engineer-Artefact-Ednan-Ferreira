"""Dinheiro: arredondamento e formatação (plan S2-02).

Todo valor em reais passa por aqui: `Decimal`, arredondamento `ROUND_HALF_UP`
para centavos e uma única função de formatação, `R$ 1.234,56`.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

Number = Decimal | int | float | str


def to_decimal(value: Number) -> Decimal:
    """Converte para `Decimal` sem carregar o ruído binário do `float`."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_money(value: Number) -> Decimal:
    """Arredonda para centavos, com meio para cima (569,905 vira 569,91)."""
    return to_decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def format_brl(value: Number) -> str:
    """Formata como `R$ 1.234,56`."""
    cents = round_money(value)
    integer, _, fraction = f"{cents:,.2f}".partition(".")
    return f"R$ {integer.replace(',', '.')},{fraction}"
