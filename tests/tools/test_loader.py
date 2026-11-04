"""Carga dos CSVs nos dois SQLite (FR-013; plan D-04 e S2-09)."""

import csv
import hashlib
import os
import shutil
import sqlite3
import time

import pytest

from emporio.data.loader import (
    build_databases,
    ensure_databases,
    open_catalog,
    open_orders,
)


def _tables(path):
    conn = sqlite3.connect(path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    finally:
        conn.close()
    return {name for (name,) in rows}


def _count_csv(data_dir, table):
    path = data_dir / f"desafio_tecnico_ai_eng - {table}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


@pytest.fixture
def built(tmp_path, data_dir):
    var_dir = tmp_path / "var"
    build_databases(data_dir, var_dir)
    return var_dir


def test_catalog_file_has_no_personal_tables(built):
    tables = _tables(built / "catalog.sqlite")
    assert {"categories", "products", "promotions"} <= tables
    assert not tables & {"customers", "orders", "order_items"}


def test_orders_file_has_orders_and_customers(built):
    assert {"customers", "orders", "order_items"} <= _tables(built / "orders.sqlite")


def test_row_counts_match_the_csvs(built, data_dir):
    conn = open_catalog(built)
    try:
        assert _count(conn, "products") == _count_csv(data_dir, "products")
        assert _count(conn, "promotions") == _count_csv(data_dir, "promotions")
        assert _count(conn, "categories") == _count_csv(data_dir, "categories")
    finally:
        conn.close()
    conn = open_orders(built)
    try:
        assert _count(conn, "customers") == _count_csv(data_dir, "customers")
        assert _count(conn, "orders") == _count_csv(data_dir, "orders")
        assert _count(conn, "order_items") == _count_csv(data_dir, "order_items")
    finally:
        conn.close()


def test_products_carry_brand_and_normalized_name(built):
    conn = open_catalog(built)
    try:
        row = conn.execute(
            "SELECT brand, name_normalized FROM products WHERE name LIKE 'Takamine GD20%'"
        ).fetchone()
    finally:
        conn.close()
    assert row["brand"] == "Takamine"
    assert row["name_normalized"].startswith("takaminegd20")


@pytest.mark.parametrize(
    ("opener", "table"), [(open_catalog, "categories"), (open_orders, "customers")]
)
def test_read_connections_reject_writes(built, opener, table):
    conn = opener(built)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("CREATE TABLE intruder (id INTEGER)")
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(f"DELETE FROM {table}")
    finally:
        conn.close()


def test_catalog_connection_cannot_read_customers(built):
    conn = open_catalog(built)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("SELECT * FROM customers")
    finally:
        conn.close()


def test_data_files_are_not_modified(tmp_path, data_dir):
    def digest():
        return {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(data_dir.iterdir())
        }

    before = digest()
    build_databases(data_dir, tmp_path / "var")
    assert digest() == before


def test_ensure_builds_only_when_missing_or_stale(tmp_path, data_dir):
    work = tmp_path / "data"
    shutil.copytree(data_dir, work)
    var_dir = tmp_path / "var"

    assert ensure_databases(work, var_dir) is True
    assert ensure_databases(work, var_dir) is False

    # Envelhece os bancos e depois mexe num CSV: ele passa a ser o mais novo.
    old = time.time() - 1000
    for name in ("catalog.sqlite", "orders.sqlite"):
        os.utime(var_dir / name, (old, old))
    (work / "desafio_tecnico_ai_eng - products.csv").touch()
    assert ensure_databases(work, var_dir) is True
    assert ensure_databases(work, var_dir) is False
