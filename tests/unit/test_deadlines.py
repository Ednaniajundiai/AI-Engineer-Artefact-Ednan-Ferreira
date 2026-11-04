"""Prazos de arrependimento, troca por defeito e garantia legal (FR-016, FR-024; S-14)."""

from datetime import date

import pytest

from emporio.rules.deadlines import (
    DEFECT_EXCHANGE_DAYS,
    LEGAL_WARRANTY_DAYS,
    WITHDRAWAL_DAYS,
    after_sale_deadlines,
    defect_exchange,
    legal_warranty,
    withdrawal,
)


def test_periods_come_from_the_manual():
    assert WITHDRAWAL_DAYS == 7  # 4.1
    assert DEFECT_EXCHANGE_DAYS == 30  # 4.2
    assert LEGAL_WARRANTY_DAYS == 90  # 8.1


def test_withdrawal_counts_seven_calendar_days_from_the_estimated_delivery():
    received = date(2025, 10, 25)
    assert withdrawal(received, today=date(2025, 11, 1)).last_day == date(2025, 11, 1)
    assert withdrawal(received, today=date(2025, 11, 1)).is_open is True  # último dia
    assert withdrawal(received, today=date(2025, 11, 2)).is_open is False
    assert withdrawal(received, today=date(2025, 10, 25)).is_open is True


def test_withdrawal_is_flagged_as_an_estimate():
    # S-14: a data de recebimento é a previsão de entrega.
    assert withdrawal(date(2025, 10, 25), today=date(2025, 10, 26)).estimated is True


def test_defect_exchange_counts_thirty_days_from_the_order_date():
    ordered = date(2026, 1, 5)
    assert defect_exchange(ordered, today=date(2026, 2, 4)).last_day == date(2026, 2, 4)
    assert defect_exchange(ordered, today=date(2026, 2, 4)).is_open is True
    assert defect_exchange(ordered, today=date(2026, 2, 5)).is_open is False
    assert defect_exchange(ordered, today=date(2026, 2, 5)).estimated is False


def test_legal_warranty_counts_ninety_days_from_the_estimated_delivery():
    received = date(2026, 1, 18)
    assert legal_warranty(received, today=date(2026, 4, 18)).last_day == date(2026, 4, 18)
    assert legal_warranty(received, today=date(2026, 4, 18)).is_open is True
    assert legal_warranty(received, today=date(2026, 4, 19)).is_open is False
    assert legal_warranty(received, today=date(2026, 4, 19)).estimated is True


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2025, 10, 30), (True, True, True)),
        (date(2025, 11, 10), (False, True, True)),
        (date(2025, 11, 15), (False, False, True)),
        (date(2026, 1, 24), (False, False, False)),
    ],
)
def test_after_sale_deadlines_with_the_injected_reference_date(today, expected):
    # Pedido 1: feito em 15/10/2025, previsão de entrega em 25/10/2025.
    result = after_sale_deadlines(date(2025, 10, 15), date(2025, 10, 25), today=today)
    assert (result.withdrawal.is_open, result.defect_exchange.is_open) == expected[:2]
    assert result.legal_warranty.is_open is expected[2]
