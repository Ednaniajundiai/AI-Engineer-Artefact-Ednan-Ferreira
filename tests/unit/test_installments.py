"""Parcelamento sem juros pelas faixas da seção 3.1 (FR-008, FR-024; S-03)."""

from decimal import Decimal

import pytest

from emporio.rules.installments import installment_options, max_installments
from emporio.rules.pricing import price_quote


def test_599_allows_six_installments_of_99_83():
    plan = max_installments(Decimal("599"))
    assert plan.count == 6
    assert plan.value == Decimal("99.83")


def test_2199_allows_twelve_installments_of_183_25():
    plan = max_installments(Decimal("2199"))
    assert plan.count == 12
    assert plan.value == Decimal("183.25")


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (Decimal("49.99"), 1),  # abaixo de R$ 50,00: só à vista (N-03)
        (Decimal("50.00"), 1),
        (Decimal("99.99"), 1),
        (Decimal("100.00"), 2),  # 2x de R$ 50,00
        (Decimal("149.99"), 2),
        (Decimal("150.00"), 3),  # 3x de R$ 50,00
        (Decimal("319.99"), 3),  # 4x daria R$ 79,99 < R$ 80,00
        (Decimal("320.00"), 4),  # 4x de R$ 80,00
        (Decimal("480.00"), 6),  # 6x de R$ 80,00
        (Decimal("699.99"), 6),  # 7x daria R$ 99,99 < R$ 100,00
        (Decimal("700.00"), 7),  # 7x de R$ 100,00
        (Decimal("1199.99"), 11),
        (Decimal("1200.00"), 12),
        (Decimal("50000.00"), 12),  # teto de 12x
    ],
)
def test_boundaries_of_each_range(total, expected):
    assert max_installments(total).count == expected


def test_every_installment_respects_its_range_minimum():
    for cents in range(1000, 300000, 737):
        total = Decimal(cents) / 100
        plan = max_installments(total)
        minimum = 50 if plan.count <= 3 else 80 if plan.count <= 6 else 100
        if plan.count > 1:
            assert total / plan.count >= minimum


def test_installments_are_computed_on_the_promotional_price():
    quote = price_quote(Decimal("2399"), Decimal("18"))  # R$ 1.967,18
    plan = max_installments(quote.final_price)
    assert plan.count == 12
    assert plan.value == Decimal("163.93")


def test_options_list_goes_from_one_to_the_maximum():
    options = installment_options(Decimal("599"))
    assert [option.count for option in options] == [1, 2, 3, 4, 5, 6]
    assert options[0].value == Decimal("599.00")
    assert options[1].value == Decimal("299.50")
    assert options[-1].value == Decimal("99.83")
