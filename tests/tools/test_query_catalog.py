"""Ferramenta `query_catalog` (FR-004, FR-005, FR-013; plan D-08, D-09, D-09a e S2-05)."""

import json
import sqlite3
from decimal import Decimal

import pytest

from emporio.data.loader import open_catalog
from emporio.money import format_brl
from emporio.tools.catalog import query_catalog_text, run_catalog_query


@pytest.fixture
def query(var_dir):
    return lambda sql, **kw: run_catalog_query(sql, var_dir, **kw)


def test_violoes_up_to_1000_only_available_and_within_the_limit(query, var_dir):
    result = query(
        "SELECT product_id, name, final_price, availability FROM v_products "
        "WHERE category = 'Violões' AND availability = 'available' AND final_price <= 1000 "
        "ORDER BY final_price"
    )
    assert result.error is None
    assert result.rows
    conn = open_catalog(var_dir)
    try:
        raw = {
            r["product_id"]: r
            for r in conn.execute("SELECT product_id, final_price, availability FROM v_products")
        }
    finally:
        conn.close()
    for row in result.rows:
        assert row["availability"] == "available"
        assert raw[row["product_id"]]["final_price"] <= 1000
        assert row["final_price"] == format_brl(raw[row["product_id"]]["final_price"])
    assert 96 not in {row["product_id"] for row in result.rows}  # sem estoque


def test_money_columns_are_formatted_and_others_kept(query):
    result = query("SELECT product_id, list_price, stock, max_installments FROM v_products")
    row = next(r for r in result.rows if r["product_id"] == 95)
    assert row["list_price"] == "R$ 2.199,00"
    assert row["stock"] == 5
    assert row["max_installments"] == 12


def test_min_by_category_is_formatted_and_matches_the_rules(query):
    result = query("SELECT category, MIN(final_price) FROM v_products GROUP BY category")
    by_category = {r["category"]: r["MIN(final_price)"] for r in result.rows}
    assert by_category["Violões"] == "R$ 429,90"  # produto 83


def test_max_with_alias_is_formatted(query):
    result = query("SELECT MAX(final_price) AS mais_caro FROM v_products")
    assert result.rows[0]["mais_caro"] == "R$ 19.567,00"


def test_alias_of_money_column_is_formatted(query):
    result = query("SELECT name, final_price AS preco FROM v_products WHERE product_id = 95")
    assert result.rows[0]["preco"] == "R$ 2.199,00"


def test_star_formats_the_four_money_columns(query):
    row = query("SELECT * FROM v_products WHERE product_id = 95").rows[0]
    assert row["list_price"] == "R$ 2.199,00"
    assert row["final_price"] == "R$ 2.199,00"
    assert row["pix_price"] == "R$ 2.089,05"
    assert row["installment_value"] == "R$ 183,25"
    assert row["stock"] == 5
    assert row["promo_discount_pct"] is None


def test_subquery_and_cte_keep_the_origin(query):
    sub = query(
        "SELECT nome, valor FROM (SELECT name AS nome, pix_price AS valor FROM v_products) AS t "
        "WHERE nome LIKE 'Takamine GD20%'"
    )
    assert sub.rows[0]["valor"] == "R$ 2.089,05"
    cte = query(
        "WITH c AS (SELECT category, MIN(final_price) AS menor FROM v_products "
        "GROUP BY category) SELECT * FROM c WHERE category = 'Violões'"
    )
    assert cte.rows[0]["menor"] == "R$ 429,90"


def test_qualified_star_and_join_keep_the_origin(query):
    result = query(
        "SELECT p.*, c.available_products FROM v_products AS p "
        "JOIN v_categories AS c ON p.category = c.category WHERE p.product_id = 95"
    )
    row = result.rows[0]
    assert row["pix_price"] == "R$ 2.089,05"
    assert isinstance(row["available_products"], int)


def test_count_stays_numeric(query):
    result = query("SELECT COUNT(*) AS total FROM v_products WHERE category = 'Violões'")
    assert isinstance(result.rows[0]["total"], int)


def test_promo_discount_pct_is_not_money(query):
    row = query("SELECT promo_discount_pct FROM v_products WHERE product_id = 90").rows[0]
    assert row["promo_discount_pct"] == 18


def test_text_output_has_the_formatted_values_and_row_count(var_dir):
    text = query_catalog_text(
        "SELECT name, pix_price FROM v_products WHERE product_id = 95", var_dir
    )
    assert "R$ 2.089,05" in text
    assert "1 linha" in text
    payload = json.loads(text[text.index("[") :])
    assert payload[0]["pix_price"] == "R$ 2.089,05"


def test_invalid_sql_comes_back_as_text(var_dir):
    text = query_catalog_text("SELECT SUM(final_price) FROM v_products", var_dir)
    assert text.startswith("Erro")
    text = query_catalog_text("SELECT nada FROM lugar_nenhum", var_dir)
    assert text.startswith("Erro")


def test_unknown_column_error_comes_back_as_text(var_dir):
    text = query_catalog_text("SELECT preco_inexistente FROM v_products", var_dir)
    assert text.startswith("Erro")


def test_heavy_query_hits_the_timeout_and_the_tool_keeps_working(var_dir):
    heavy = (
        "SELECT COUNT(*) FROM v_products AS a, v_products AS b, v_products AS c, v_products AS d"
    )
    result = run_catalog_query(heavy, var_dir, timeout_s=0.05)
    assert result.error is not None
    assert "tempo" in result.error.lower()
    light = run_catalog_query(
        "SELECT name FROM v_products WHERE product_id = 95", var_dir, timeout_s=0.05
    )
    assert light.error is None
    assert light.rows[0]["name"].startswith("Takamine")


def test_reading_customers_fails_in_validation_and_in_the_connection(var_dir):
    assert run_catalog_query("SELECT * FROM customers", var_dir).error is not None
    conn = open_catalog(var_dir)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("SELECT * FROM customers")
    finally:
        conn.close()


def test_at_most_twenty_rows(query):
    assert len(query("SELECT name FROM v_products LIMIT 100").rows) == 20


def test_formatting_uses_the_money_module(query):
    row = query("SELECT pix_price FROM v_products WHERE product_id = 81").rows[0]
    assert row["pix_price"] == format_brl(Decimal("599.9") * Decimal("0.95"))
