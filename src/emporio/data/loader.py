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
from decimal import Decimal
from pathlib import Path

from emporio.data.normalize import derive_brand, normalize_name
from emporio.rules.installments import max_installments
from emporio.rules.pricing import PromotionRecord, active_promotion, availability, price_quote

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

# Tabela materializada com os valores calculados em Python pelas regras
# testadas (princípio II). O SQL do modelo só enxerga as visões abaixo.
CATALOG_VIEW_SCHEMA = """
CREATE TABLE catalog_products (
    product_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    brand TEXT,
    list_price REAL NOT NULL,
    promo_name TEXT,
    promo_discount_pct REAL,
    final_price REAL NOT NULL,
    pix_price REAL NOT NULL,
    max_installments INTEGER NOT NULL,
    installment_value REAL NOT NULL,
    stock INTEGER NOT NULL,
    status TEXT NOT NULL,
    availability TEXT NOT NULL,
    description TEXT,
    specs TEXT
);
CREATE INDEX idx_catalog_category ON catalog_products (category_id, availability);
CREATE VIEW v_products AS
SELECT product_id, name, category, brand, list_price, promo_name, promo_discount_pct,
       final_price, pix_price, max_installments, installment_value, stock, status,
       availability, description, specs
FROM catalog_products;
-- S-10: sopros e cordas orquestrais existem como categoria, mas sem produtos;
-- available_products = 0 diz ao agente que não há opções no catálogo.
CREATE VIEW v_categories AS
SELECT c.name AS category,
       c.description AS description,
       (SELECT COUNT(*) FROM catalog_products AS p
        WHERE p.category_id = c.category_id AND p.availability = 'available')
           AS available_products
FROM categories AS c;
"""

# S-09: as descrições de 135 e 136 citam outros modelos. N-01: a mesma regra
# vale para as que citam outra marca (137 cita Ibanez; 139, Pearl; 140, Tama;
# 142, Roland; 144, Yamaha). A descrição desses produtos não é repetida.
MISMATCHED_DESCRIPTIONS = frozenset({135, 136, 137, 139, 140, 142, 144})

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
    product_name TEXT,
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
        _materialize_catalog(conn)
        conn.commit()
    finally:
        conn.close()


def _materialize_catalog(conn: sqlite3.Connection) -> None:
    """Calcula preço final, PIX, parcelamento e disponibilidade de cada produto."""
    conn.executescript(CATALOG_VIEW_SCHEMA)
    promotions: dict[int, list[PromotionRecord]] = {}
    for product_id, pct, name, active in conn.execute(
        "SELECT product_id, discount_percent, description, is_active FROM promotions"
    ):
        promotions.setdefault(product_id, []).append(
            PromotionRecord(name=name, discount_pct=Decimal(str(pct)), is_active=bool(active))
        )
    rows = []
    for product in conn.execute(
        "SELECT p.product_id, p.name, p.category_id, c.name, p.brand, p.price_brl, "
        "p.stock_quantity, p.status, p.description, p.specs "
        "FROM products AS p JOIN categories AS c ON c.category_id = p.category_id"
    ).fetchall():
        pid, name, cat_id, category, brand, price, stock, status, description, specs = product
        promo = active_promotion(promotions.get(pid, []))
        quote = price_quote(price, promo.discount_pct if promo else None)
        plan = max_installments(quote.final_price)
        rows.append(
            {
                "product_id": pid,
                "name": name,
                "category_id": cat_id,
                "category": category,
                "brand": brand,
                "list_price": float(quote.list_price),
                "promo_name": promo.name if promo else None,
                "promo_discount_pct": float(promo.discount_pct) if promo else None,
                "final_price": float(quote.final_price),
                "pix_price": float(quote.pix_price),
                "max_installments": plan.count,
                "installment_value": float(plan.value),
                "stock": stock,
                "status": status,
                "availability": availability(status, stock).value,
                "description": None if pid in MISMATCHED_DESCRIPTIONS else description,
                "specs": specs,
            }
        )
    _insert(conn, "catalog_products", rows)


def _build_orders(data_dir: Path, path: Path) -> None:
    # O nome do produto é copiado para o item, para que a ferramenta de pedidos
    # leia só este arquivo (D-04).
    product_names = {_int(r["product_id"]): r["name"].strip() for r in _read(data_dir, "products")}
    conn = _fresh(path)
    try:
        conn.executescript(ORDERS_SCHEMA)
        # S-17: o telefone (67) 99999-0000 do cliente 27 parece fictício; fica como
        # está, porque a verificação usa o e-mail e o telefone nunca sai da base.
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
                    "product_name": product_names.get(_int(r["product_id"])),
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
