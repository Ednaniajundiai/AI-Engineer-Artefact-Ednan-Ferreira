"""Dinheiro: arredondamento e formatação (plan S2-02; base de FR-006 e FR-008)."""

from decimal import Decimal

import pytest

from emporio.money import format_brl, round_money


def test_round_half_up_to_cents():
    assert round_money(Decimal("569.905")) == Decimal("569.91")


def test_round_half_up_does_not_use_bankers_rounding():
    assert round_money(Decimal("0.125")) == Decimal("0.13")
    assert round_money(Decimal("0.135")) == Decimal("0.14")


def test_round_accepts_float_and_string_without_binary_noise():
    assert round_money(2.675) == Decimal("2.68")
    assert round_money("2089.05") == Decimal("2089.05")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("1234.56"), "R$ 1.234,56"),
        (Decimal("599.9"), "R$ 599,90"),
        (2199, "R$ 2.199,00"),
        (Decimal("0"), "R$ 0,00"),
        (Decimal("1234567.8"), "R$ 1.234.567,80"),
        (Decimal("569.905"), "R$ 569,91"),
    ],
)
def test_format_brl(value, expected):
    assert format_brl(value) == expected
