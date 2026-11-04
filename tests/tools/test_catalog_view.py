"""Tabela materializada do catálogo e visões (FR-006, FR-008, FR-009; S-09, S-10)."""

import csv
from decimal import Decimal

import pytest

from emporio.data.loader import open_catalog
from emporio.rules.installments import max_installments
from emporio.rules.pricing import PromotionRecord, active_promotion, availability, price_quote


def _csv(data_dir, name):
    path = data_dir / f"desafio_tecnico_ai_eng - {name}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def view_rows(var_dir):
    conn = open_catalog(var_dir)
    try:
        return {row["product_id"]: dict(row) for row in conn.execute("SELECT * FROM v_products")}
    finally:
        conn.close()


@pytest.fixture(scope="module")
def expected():
    from tests.conftest import DATA_DIR as data_dir

    promos: dict[int, list[PromotionRecord]] = {}
    for row in _csv(data_dir, "promotions"):
        promos.setdefault(int(row["product_id"]), []).append(
            PromotionRecord(
                name=row["description"],
                discount_pct=Decimal(row["discount_percent"]),
                is_active=row["is_active"] == "1",
            )
        )
    result = {}
    for row in _csv(data_dir, "products"):
        pid = int(row["product_id"])
        promo = active_promotion(promos.get(pid, []))
        quote = price_quote(Decimal(row["price_brl"]), promo.discount_pct if promo else None)
        plan = max_installments(quote.final_price)
        result[pid] = {
            "list_price": quote.list_price,
            "final_price": quote.final_price,
            "pix_price": quote.pix_price,
            "max_installments": plan.count,
            "installment_value": plan.value,
            "availability": availability(row["status"], int(row["stock_quantity"])).value,
            "promo_name": promo.name if promo else None,
        }
    return result


def test_every_product_is_in_the_view(view_rows, expected):
    assert set(view_rows) == set(expected)


def test_prices_and_installments_match_the_rules(view_rows, expected):
    for pid, want in expected.items():
        got = view_rows[pid]
        for column in ("list_price", "final_price", "pix_price", "installment_value"):
            assert Decimal(str(got[column])) == want[column], (pid, column)
        assert got["max_installments"] == want["max_installments"], pid
        assert got["availability"] == want["availability"], pid
        assert got["promo_name"] == want["promo_name"], pid


def test_known_products(view_rows):
    assert view_rows[95]["pix_price"] == 2089.05
    assert view_rows[95]["promo_name"] is None  # a "Oferta Especial" do 95 está inativa
    assert view_rows[90]["final_price"] == 1967.18
    assert view_rows[90]["promo_discount_pct"] == 18
    assert view_rows[96]["availability"] == "out_of_stock"
    assert view_rows[130]["availability"] == "coming_soon"
    assert view_rows[136]["availability"] == "discontinued"


def test_mismatched_descriptions_are_null(view_rows):
    # S-09: as descrições de 135 e 136 citam outros modelos.
    assert view_rows[135]["description"] is None
    assert view_rows[136]["description"] is None
    # N-01: a mesma regra vale para as descrições que citam outra marca.
    for pid in (137, 139, 140, 142, 144):
        assert view_rows[pid]["description"] is None, pid
    assert view_rows[95]["description"].startswith("Violão dreadnought Takamine")


def test_view_exposes_the_plan_columns(var_dir):
    conn = open_catalog(var_dir)
    try:
        columns = [d[0] for d in conn.execute("SELECT * FROM v_products LIMIT 1").description]
    finally:
        conn.close()
    assert columns == [
        "product_id",
        "name",
        "category",
        "brand",
        "list_price",
        "promo_name",
        "promo_discount_pct",
        "final_price",
        "pix_price",
        "max_installments",
        "installment_value",
        "stock",
        "status",
        "availability",
        "description",
        "specs",
    ]


def test_categories_without_products_have_zero_available(var_dir):
    # S-10: sopros e cordas orquestrais não têm produtos.
    conn = open_catalog(var_dir)
    try:
        rows = {
            r["category"]: r["available_products"]
            for r in conn.execute("SELECT category, available_products FROM v_categories")
        }
    finally:
        conn.close()
    assert rows["Instrumentos de Sopro (Madeiras)"] == 0
    assert rows["Instrumentos de Sopro (Metais)"] == 0
    assert rows["Cordas Orquestrais"] == 0
    assert rows["Violões"] > 0
