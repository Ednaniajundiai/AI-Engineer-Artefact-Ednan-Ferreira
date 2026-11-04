"""Carga dos CSVs de `data/` em dois SQLite (plan D-04 e S2-09).

- `catalog.sqlite`: categorias, produtos e promoções. É o único arquivo que a
  consulta SQL do modelo enxerga.
- `orders.sqlite`: clientes, pedidos e itens. Fica num arquivo separado para
  que nenhuma consulta ao catálogo alcance dado pessoal.

Os CSVs nunca são alterados. As normalizações (marca, nome normalizado, e-mail
em minúsculas) acontecem aqui, na carga.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from emporio.data.normalize import derive_brand, normalize_name

CATALOG_FILE = "catalog.sqlite"
ORDERS_FILE = "orders.sqlite"
CSV_PREFIX = "desafio_tecnico_ai_eng - "

CATALOG_SCHEMA = """
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL,
    brand TEXT,
    category_id INTEGER NOT NULL REFERENCES categories (category_id),
    price_brl REAL NOT NULL,
    description TEXT,
    stock_quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    specs TEXT,
    created_at TEXT
);
CREATE TABLE promotions (
    promotion_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products (product_id),
    discount_percent REAL NOT NULL,
    description TEXT,
    is_active INTEGER NOT NULL
);
CREATE INDEX idx_products_category ON products (category_id);
CREATE INDEX idx_products_name ON products (name_normalized);
CREATE INDEX idx_promotions_product ON promotions (product_id);
"""

ORDERS_SCHEMA = """
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT NOT NULL,
    email_normalized TEXT NOT NULL,
    city TEXT
);
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total_brl REAL NOT NULL,
    payment_method TEXT,
    tracking_code TEXT,
    estimated_delivery TEXT,
    notes TEXT
);
CREATE TABLE order_items (
    order_id INTEGER NOT NULL REFERENCES orders (order_id),
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL
);
CREATE INDEX idx_customers_email ON customers (email_normalized);
CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_items_order ON order_items (order_id);
"""

CSV_NAMES = ("categories", "products", "promotions", "customers", "orders", "order_items")


def _text(value: str) -> str | None:
    value = value.strip()
    return value or None


def _int(value: str) -> int:
    return int(value.strip())


def _real(value: str) -> float:
    return float(value.strip())


def _read(data_dir: Path, name: str) -> list[dict[str, str]]:
    path = data_dir / f"{CSV_PREFIX}{name}.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _insert(conn: sqlite3.Connection, table: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    columns = list(rows[0])
    placeholders = ", ".join("?" for _ in columns)
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
        [tuple(row[column] for column in columns) for row in rows],
    )


def _fresh(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    return sqlite3.connect(path)


def _build_catalog(data_dir: Path, path: Path) -> None:
    conn = _fresh(path)
    try:
        conn.executescript(CATALOG_SCHEMA)
        _insert(
            conn,
            "categories",
            [
                {
                    "category_id": _int(r["category_id"]),
                    "name": r["name"].strip(),
                    "description": _text(r["description"]),
                }
                for r in _read(data_dir, "categories")
            ],
        )
        _insert(
            conn,
            "products",
            [
                {
                    "product_id": _int(r["product_id"]),
                    "name": r["name"].strip(),
                    "name_normalized": normalize_name(r["name"]),
                    "brand": derive_brand(r["name"]),
                    "category_id": _int(r["category_id"]),
                    "price_brl": _real(r["price_brl"]),
                    "description": _text(r["description"]),
                    "stock_quantity": _int(r["stock_quantity"]),
                    "status": r["status"].strip(),
                    "specs": _text(r["specs"]),
                    "created_at": _text(r["created_at"]),
                }
                for r in _read(data_dir, "products")
            ],
        )
        _insert(
            conn,
            "promotions",
            [
                {
                    "promotion_id": _int(r["promotion_id"]),
                    "product_id": _int(r["product_id"]),
                    "discount_percent": _real(r["discount_percent"]),
                    "description": _text(r["description"]),
                    "is_active": _int(r["is_active"]),
                }
                for r in _read(data_dir, "promotions")
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _build_orders(data_dir: Path, path: Path) -> None:
    conn = _fresh(path)
    try:
        conn.executescript(ORDERS_SCHEMA)
        _insert(
            conn,
            "customers",
            [
                {
                    "customer_id": _int(r["customer_id"]),
                    "name": r["name"].strip(),
                    "phone": _text(r["phone"]),
                    "email": r["email"].strip(),
                    "email_normalized": r["email"].strip().lower(),
                    "city": _text(r["city"]),
                }
                for r in _read(data_dir, "customers")
            ],
        )
        _insert(
            conn,
            "orders",
            [
                {
                    "order_id": _int(r["order_id"]),
                    "customer_id": _int(r["customer_id"]),
                    "order_date": r["order_date"].strip(),
                    "status": r["status"].strip(),
                    "total_brl": _real(r["total_brl"]),
                    "payment_method": _text(r["payment_method"]),
                    "tracking_code": _text(r["tracking_code"]),
                    "estimated_delivery": _text(r["estimated_delivery"]),
                    "notes": _text(r["notes"]),
                }
                for r in _read(data_dir, "orders")
            ],
        )
        _insert(
            conn,
            "order_items",
            [
                {
                    "order_id": _int(r["order_id"]),
                    "product_id": _int(r["product_id"]),
                    "quantity": _int(r["quantity"]),
                }
                for r in _read(data_dir, "order_items")
            ],
        )
        conn.commit()
    finally:
        conn.close()


def build_databases(data_dir: Path, var_dir: Path) -> None:
    """Gera `catalog.sqlite` e `orders.sqlite` a partir dos CSVs, do zero."""
    _build_catalog(data_dir, var_dir / CATALOG_FILE)
    _build_orders(data_dir, var_dir / ORDERS_FILE)


def ensure_databases(data_dir: Path, var_dir: Path) -> bool:
    """Refaz a carga se faltar um arquivo ou se algum CSV for mais novo.

    Devolve `True` quando a carga foi refeita.
    """
    targets = [var_dir / CATALOG_FILE, var_dir / ORDERS_FILE]
    if all(target.exists() for target in targets):
        oldest = min(target.stat().st_mtime for target in targets)
        newest_csv = max(
            (data_dir / f"{CSV_PREFIX}{name}.csv").stat().st_mtime for name in CSV_NAMES
        )
        if newest_csv <= oldest:
            return False
    build_databases(data_dir, var_dir)
    return True


def _open_read_only(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only = ON")
    conn.row_factory = sqlite3.Row
    return conn


def open_catalog(var_dir: Path) -> sqlite3.Connection:
    """Conexão só leitura com o catálogo (`mode=ro` e `query_only`)."""
    return _open_read_only(var_dir / CATALOG_FILE)


def open_orders(var_dir: Path) -> sqlite3.Connection:
    """Conexão só leitura com clientes e pedidos."""
    return _open_read_only(var_dir / ORDERS_FILE)
