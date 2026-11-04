"""Preço final, PIX, promoção vigente e disponibilidade (FR-006, FR-007, FR-009, FR-010).

- Com promoção ativa, o preço final é o de tabela menos o percentual da
  promoção, e o preço no PIX é o próprio preço promocional: o desconto do PIX
  não se soma à promoção (manual 6.2).
- Sem promoção ativa, o preço no PIX é o de tabela com 5% de desconto.
- Só a promoção marcada como ativa é vigente; inativa = encerrada (S-13).
- Disponível = ativo com estoque > 0. O status prevalece sobre o estoque
  (S-06, S-07, S-08).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from emporio.money import Number, round_money, to_decimal

PIX_DISCOUNT_PCT = Decimal("5")
_HUNDRED = Decimal("100")


class Availability(StrEnum):
    AVAILABLE = "available"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    COMING_SOON = "coming_soon"


@dataclass(frozen=True)
class PromotionRecord:
    name: str
    discount_pct: Decimal
    is_active: bool


@dataclass(frozen=True)
class PriceQuote:
    list_price: Decimal
    promo_discount_pct: Decimal | None
    final_price: Decimal
    pix_price: Decimal

    @property
    def has_promotion(self) -> bool:
        return self.promo_discount_pct is not None


def _discounted(price: Decimal, pct: Decimal) -> Decimal:
    return round_money(price * (_HUNDRED - pct) / _HUNDRED)


def price_quote(list_price: Number, promo_discount_pct: Number | None) -> PriceQuote:
    """Preço de tabela, preço final e preço no PIX de um produto."""
    base = round_money(list_price)
    if promo_discount_pct is not None:
        pct = to_decimal(promo_discount_pct)
        final = _discounted(base, pct)
        return PriceQuote(base, pct, final, final)  # o PIX não se soma à promoção
    return PriceQuote(base, None, base, _discounted(base, PIX_DISCOUNT_PCT))


def active_promotion(promotions: Iterable[PromotionRecord]) -> PromotionRecord | None:
    """A promoção vigente do produto, ou `None`.

    S-13: só a ativa vale. N-02: se houver mais de uma ativa, como as promoções
    não são cumulativas (manual 6.2), vale uma só, a de maior desconto. Nos
    dados atuais nenhum produto tem duas promoções ativas.
    """
    active = [promo for promo in promotions if promo.is_active]
    if not active:
        return None
    return max(active, key=lambda promo: promo.discount_pct)


def availability(status: str, stock: int) -> Availability:
    """Disponibilidade pelo status e pelo estoque (FR-009)."""
    if status == "discontinued":
        return Availability.DISCONTINUED  # S-07: fora do catálogo mesmo com estoque
    if status == "coming_soon":
        return Availability.COMING_SOON  # S-06: não está à venda mesmo com estoque
    if status == "active":
        return Availability.AVAILABLE if stock > 0 else Availability.OUT_OF_STOCK  # S-08
    # Status desconhecido: nunca é dado como disponível (conservador).
    return Availability.DISCONTINUED
