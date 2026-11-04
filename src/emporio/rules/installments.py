"""Parcelamento sem juros pelas faixas da seção 3.1 do manual (FR-008; S-03).

- até 3x: parcela mínima de R$ 50,00 ("sem valor mínimo, exceto abaixo de
  R$ 50,00");
- de 4x a 6x: parcela mínima de R$ 80,00;
- de 7x a 12x: parcela mínima de R$ 100,00.

A tabela de pagamento cita só "parcela mínima de R$ 100,00"; valem as faixas
da 3.1, que são a regra detalhada (S-03). Uma compra abaixo de R$ 50,00 só
sai em 1x (N-03). O valor da parcela é arredondado para centavos com meio para
cima, sem juros.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from emporio.money import Number, round_money, to_decimal

MAX_INSTALLMENTS = 12

# (de, até, parcela mínima)
RANGES: tuple[tuple[int, int, Decimal], ...] = (
    (1, 3, Decimal("50")),
    (4, 6, Decimal("80")),
    (7, 12, Decimal("100")),
)


@dataclass(frozen=True)
class Installment:
    count: int
    value: Decimal


def minimum_installment(count: int) -> Decimal:
    """Parcela mínima da faixa a que `count` pertence."""
    for start, end, minimum in RANGES:
        if start <= count <= end:
            return minimum
    raise ValueError(f"número de parcelas fora das faixas: {count}")


def _allowed(total: Decimal, count: int) -> bool:
    return count == 1 or total >= count * minimum_installment(count)


def max_installments(total: Number) -> Installment:
    """Maior parcelamento sem juros permitido e o valor de cada parcela."""
    amount = to_decimal(total)
    count = max(n for n in range(1, MAX_INSTALLMENTS + 1) if _allowed(amount, n))
    return Installment(count, round_money(amount / count))


def installment_options(total: Number) -> list[Installment]:
    """Todas as opções de 1x até o máximo permitido."""
    amount = to_decimal(total)
    top = max_installments(amount).count
    return [Installment(n, round_money(amount / n)) for n in range(1, top + 1)]
