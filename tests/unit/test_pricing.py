"""Preço final, PIX, promoção e disponibilidade (FR-006, FR-007, FR-009, FR-010, FR-024)."""

from decimal import Decimal

import pytest

from emporio.rules.pricing import (
    Availability,
    PromotionRecord,
    active_promotion,
    availability,
    price_quote,
)


def test_without_promotion_pix_is_list_price_minus_five_percent():
    quote = price_quote(Decimal("2199"), None)
    assert quote.final_price == Decimal("2199.00")
    assert quote.pix_price == Decimal("2089.05")
    assert quote.promo_discount_pct is None
    assert quote.has_promotion is False


def test_with_active_promotion_final_price_is_list_minus_percent_and_pix_does_not_stack():
    quote = price_quote(Decimal("2399"), Decimal("18"))
    assert quote.list_price == Decimal("2399.00")
    assert quote.final_price == Decimal("1967.18")
    assert quote.pix_price == quote.final_price  # FR-006: o PIX não se soma
    assert quote.promo_discount_pct == Decimal("18")
    assert quote.has_promotion is True


def test_rounding_is_half_up_to_cents():
    # 599,90 x 0,95 = 569,905 -> 569,91
    assert price_quote(Decimal("599.9"), None).pix_price == Decimal("569.91")


def test_accepts_floats_without_binary_noise():
    assert price_quote(799.9, None).pix_price == Decimal("759.91")


def test_inactive_promotions_are_ignored():
    # S-13: inativa = encerrada.
    promos = [
        PromotionRecord(name="Oferta Especial", discount_pct=Decimal("12"), is_active=False),
    ]
    assert active_promotion(promos) is None


def test_active_promotion_is_chosen():
    promos = [
        PromotionRecord(name="Black Friday", discount_pct=Decimal("10"), is_active=False),
        PromotionRecord(name="Desconto Exclusivo", discount_pct=Decimal("18"), is_active=True),
    ]
    assert active_promotion(promos).name == "Desconto Exclusivo"


def test_two_active_promotions_do_not_stack_and_the_largest_applies():
    # Suposição N-02: promoções não são cumulativas (manual 6.2); vale uma só.
    promos = [
        PromotionRecord(name="A", discount_pct=Decimal("10"), is_active=True),
        PromotionRecord(name="B", discount_pct=Decimal("15"), is_active=True),
    ]
    assert active_promotion(promos).discount_pct == Decimal("15")


@pytest.mark.parametrize(
    ("status", "stock", "expected"),
    [
        ("active", 5, Availability.AVAILABLE),
        ("active", 0, Availability.OUT_OF_STOCK),  # S-08 (produto 96)
        ("discontinued", 13, Availability.DISCONTINUED),  # S-07 (produto 136)
        ("discontinued", 0, Availability.DISCONTINUED),
        ("coming_soon", 2, Availability.COMING_SOON),  # S-06 (produto 130)
        ("coming_soon", 0, Availability.COMING_SOON),
    ],
)
def test_availability_follows_status_before_stock(status, stock, expected):
    assert availability(status, stock) is expected


def test_unknown_status_is_never_available():
    assert availability("archived", 10) is not Availability.AVAILABLE


def test_availability_values_are_the_plan_strings():
    assert {a.value for a in Availability} == {
        "available",
        "out_of_stock",
        "discontinued",
        "coming_soon",
    }
