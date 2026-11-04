"""Validação do SQL escrito pelo modelo (FR-004, FR-006, FR-008, FR-013; plan D-08 e S2-05)."""

import pytest
import sqlglot

from emporio.tools.sql_guard import MAX_ROWS, SqlValidationError, validate_sql


def limit_of(sql):
    return int(sqlglot.parse_one(sql, read="sqlite").args["limit"].expression.name)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT name, final_price FROM v_products WHERE availability = 'available'",
        "SELECT * FROM v_products",
        "SELECT category, available_products FROM v_categories",
        "SELECT COUNT(*) FROM v_products WHERE category = 'Violões'",
        "SELECT category, MIN(final_price) FROM v_products GROUP BY category",
        "SELECT MAX(final_price) AS mais_caro FROM v_products",
        "SELECT name FROM v_products WHERE final_price <= 1000 ORDER BY final_price",
        "SELECT name FROM v_products WHERE lower(brand) = 'yamaha'",
        "SELECT name FROM v_products WHERE trim(category) LIKE 'Viol%'",
        "SELECT name FROM v_products WHERE upper(name) LIKE '%GD20%'",
        "SELECT name FROM v_products WHERE final_price BETWEEN 500 AND 1000",
        "SELECT name FROM v_products WHERE category IN ('Violões', 'Ukuleles')",
        "SELECT name FROM v_products WHERE promo_name IS NOT NULL AND NOT stock = 0",
        "SELECT name, final_price AS preco FROM v_products",
        "SELECT p.name FROM v_products AS p WHERE p.final_price < 500",
        "WITH baratos AS (SELECT name, final_price FROM v_products WHERE final_price < 500) "
        "SELECT name, final_price FROM baratos",
        "SELECT name FROM (SELECT name, final_price FROM v_products) AS t WHERE final_price > 10",
        "SELECT category, COUNT(*) FROM v_products GROUP BY category HAVING COUNT(*) > 2",
        "SELECT COUNT(DISTINCT brand) FROM v_products",
        "SELECT name FROM v_products WHERE final_price > -1",
    ],
)
def test_accepts_safe_selects_on_the_views(sql):
    validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO v_products (name) VALUES ('x')",
        "UPDATE products SET price_brl = 1",
        "DELETE FROM v_products",
        "DROP TABLE products",
        "PRAGMA table_info(products)",
        "ATTACH DATABASE 'var/orders.sqlite' AS o",
        "SELECT * FROM v_products; DELETE FROM products",
        "SELECT * FROM v_products; -- só um comentário\nDROP TABLE products",
        "SELECT * FROM v_products /* ; DROP TABLE products */",
        "SELECT * FROM v_products -- comentário",
        "SELECT * FROM products",
        "SELECT * FROM customers",
        "SELECT name FROM sqlite_master",
        "SELECT * FROM main.v_products",
        "SELECT name FROM v_products WHERE random() > 0",
        "SELECT load_extension('x')",
        "SELECT name FROM v_products UNION SELECT name FROM v_categories",
        "SELECT name FROM v_products WHERE name IN (SELECT name FROM customers)",
        "SELECT a.name FROM v_products AS a JOIN products AS b ON a.product_id = b.product_id",
        "",
        "não é sql",
    ],
)
def test_rejects_writes_other_tables_multiple_statements_and_unknown_functions(sql):
    with pytest.raises(SqlValidationError):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT final_price / 10 FROM v_products",
        "SELECT list_price * 0.85 FROM v_products",
        "SELECT pix_price - 50 FROM v_products",
        "SELECT final_price + 1 AS preco FROM v_products",
        "SELECT list_price * 0.85 AS desconto FROM v_products",
        "SELECT SUM(final_price) FROM v_products",
        "SELECT AVG(final_price) AS media FROM v_products",
        "SELECT ROUND(final_price, 0) FROM v_products",
        "SELECT MIN(final_price * 0.9) FROM v_products",
        "SELECT abs(final_price) FROM v_products",
        "SELECT CASE WHEN stock > 0 THEN 1 ELSE 0 END FROM v_products",
        "SELECT CAST(final_price AS INTEGER) FROM v_products",
        "SELECT 42",
        "SELECT name, 'x' FROM v_products",
        "SELECT name FROM (SELECT name, final_price * 2 AS dobro FROM v_products) AS t",
        "WITH t AS (SELECT SUM(final_price) AS total FROM v_products) SELECT total FROM t",
        "SELECT name FROM v_products WHERE final_price * 0.95 < 500",
        "SELECT name FROM v_products ORDER BY final_price / max_installments",
    ],
)
def test_rejects_arithmetic_and_other_functions_in_the_select_list(sql):
    # D-08: o SQL do modelo não gera valor novo de dinheiro, com ou sem apelido.
    with pytest.raises(SqlValidationError):
        validate_sql(sql)


def test_error_message_explains_the_rule():
    with pytest.raises(SqlValidationError) as error:
        validate_sql("SELECT SUM(final_price) FROM v_products")
    assert "SELECT" in str(error.value)


def test_limit_is_added_when_missing():
    assert limit_of(validate_sql("SELECT name FROM v_products")) == MAX_ROWS


def test_larger_limit_is_reduced():
    assert limit_of(validate_sql("SELECT name FROM v_products LIMIT 500")) == MAX_ROWS


def test_smaller_limit_is_kept():
    assert limit_of(validate_sql("SELECT name FROM v_products LIMIT 5")) == 5


def test_non_literal_limit_is_rejected():
    with pytest.raises(SqlValidationError):
        validate_sql("SELECT name FROM v_products LIMIT (SELECT COUNT(*) FROM v_products)")


def test_max_rows_is_twenty():
    assert MAX_ROWS == 20
