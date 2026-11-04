"""Prazos de pós-venda (FR-016; manual 4.1, 4.2 e 8.1; S-14).

- Arrependimento: 7 dias corridos após o recebimento (só compra online).
- Troca por defeito: 30 dias corridos após a compra (data do pedido).
- Garantia legal: 90 dias a partir do recebimento.

Os pedidos não registram a data real de entrega, então o recebimento é a
previsão de entrega, e o prazo é marcado como estimativa (S-14). O último dia
do prazo ainda vale.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

WITHDRAWAL_DAYS = 7
DEFECT_EXCHANGE_DAYS = 30
LEGAL_WARRANTY_DAYS = 90


@dataclass(frozen=True)
class Deadline:
    start: date
    last_day: date
    is_open: bool
    estimated: bool


def _deadline(start: date, days: int, today: date, *, estimated: bool) -> Deadline:
    last_day = start + timedelta(days=days)
    return Deadline(start=start, last_day=last_day, is_open=today <= last_day, estimated=estimated)


def withdrawal(received: date, *, today: date) -> Deadline:
    """Direito de arrependimento, a partir da previsão de entrega (estimativa)."""
    return _deadline(received, WITHDRAWAL_DAYS, today, estimated=True)


def defect_exchange(ordered: date, *, today: date) -> Deadline:
    """Troca por defeito, a partir da data do pedido."""
    return _deadline(ordered, DEFECT_EXCHANGE_DAYS, today, estimated=False)


def legal_warranty(received: date, *, today: date) -> Deadline:
    """Garantia legal, a partir da previsão de entrega (estimativa)."""
    return _deadline(received, LEGAL_WARRANTY_DAYS, today, estimated=True)


@dataclass(frozen=True)
class AfterSaleDeadlines:
    withdrawal: Deadline
    defect_exchange: Deadline
    legal_warranty: Deadline


def after_sale_deadlines(ordered: date, received: date, *, today: date) -> AfterSaleDeadlines:
    """Os três prazos de um pedido entregue."""
    return AfterSaleDeadlines(
        withdrawal=withdrawal(received, today=today),
        defect_exchange=defect_exchange(ordered, today=today),
        legal_warranty=legal_warranty(received, today=today),
    )
