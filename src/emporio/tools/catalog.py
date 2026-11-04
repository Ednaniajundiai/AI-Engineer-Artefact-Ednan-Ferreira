"""Ferramentas de catálogo: `find_product` e `query_catalog` (FR-004 a FR-010; plan D-03).

- `find_product` busca pelo nome com casamento aproximado (`rapidfuzz` sobre o
  nome normalizado, S2-06) e devolve o detalhe completo de até 3 candidatos,
  com preços, parcelamento, promoções encerradas e, para todo produto
  indisponível, 3 alternativas disponíveis da mesma categoria e preço próximo.
- `query_catalog` roda o SQL escrito pelo modelo sobre as visões, depois de
  validado (`sql_guard`), numa conexão só leitura com tempo-limite, e formata em
  `R$` todo valor cuja coluna de origem seja de dinheiro (D-09 e D-09a).

Todos os valores de dinheiro saem formatados por `money.format_brl`.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from langchain_core.tools import BaseTool, tool
from rapidfuzz import fuzz

from emporio import config
from emporio.data.loader import open_catalog
from emporio.data.normalize import normalize_name
from emporio.money import format_brl
from emporio.rules.installments import Installment, installment_options
from emporio.rules.pricing import Availability
from emporio.tools.sql_guard import (
    MAX_ROWS,
    SqlValidationError,
    money_output_flags,
    parse_validated,
)

MAX_CANDIDATES = 3
MAX_ALTERNATIVES = 3
MATCH_THRESHOLD = 80
QUERY_TIMEOUT_SECONDS = 2.0
_PROGRESS_STEPS = 1000

AVAILABILITY_TEXT = {
    Availability.AVAILABLE: "disponível",
    Availability.OUT_OF_STOCK: "temporariamente indisponível (sem estoque no momento)",
    Availability.DISCONTINUED: "não faz mais parte do catálogo (produto descontinuado)",
    Availability.COMING_SOON: "ainda não está à venda (lançamento em breve)",
}


@dataclass(frozen=True)
class ProductSummary:
    product_id: int
    name: str
    category: str
    availability: str
    final_price: Decimal
    pix_price: Decimal
    max_installments: int
    installment_value: Decimal


@dataclass(frozen=True)
class ProductDetail:
    product_id: int
    name: str
    category: str
    brand: str | None
    availability: str
    stock: int
    list_price: Decimal
    promo_name: str | None
    promo_discount_pct: Decimal | None
    final_price: Decimal
    pix_price: Decimal
    installments: list[Installment]
    ended_promotions: list[tuple[str, Decimal]]
    description: str | None
    specs: str | None
    alternatives: list[ProductSummary] = field(default_factory=list)


@dataclass(frozen=True)
class FindResult:
    query: str
    candidates: list[ProductDetail]
    total_matches: int


def _dec(value: float | int | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _pct(value: Decimal) -> str:
    """Percentual sem casas inúteis: 18.0 -> "18"."""
    return format(value.normalize(), "f")


def _score(query_norm: str, name_norm: str) -> float:
    return max(fuzz.partial_ratio(query_norm, name_norm), fuzz.ratio(query_norm, name_norm))


def _summary(row: sqlite3.Row) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        category=row["category"],
        availability=row["availability"],
        final_price=_dec(row["final_price"]),
        pix_price=_dec(row["pix_price"]),
        max_installments=row["max_installments"],
        installment_value=_dec(row["installment_value"]),
    )


def _alternatives(conn: sqlite3.Connection, row: sqlite3.Row) -> list[ProductSummary]:
    """3 produtos disponíveis da mesma categoria, com o preço mais próximo."""
    rows = conn.execute(
        "SELECT * FROM v_products WHERE category = ? AND availability = 'available' "
        "AND product_id != ? ORDER BY abs(final_price - ?), product_id LIMIT ?",
        (row["category"], row["product_id"], row["final_price"], MAX_ALTERNATIVES),
    ).fetchall()
    return [_summary(r) for r in rows]


def _detail(conn: sqlite3.Connection, row: sqlite3.Row) -> ProductDetail:
    ended = [
        (r["description"], _dec(r["discount_percent"]))
        for r in conn.execute(
            "SELECT description, discount_percent FROM promotions "
            "WHERE product_id = ? AND is_active = 0 ORDER BY promotion_id",
            (row["product_id"],),
        )
    ]
    unavailable = row["availability"] != Availability.AVAILABLE
    return ProductDetail(
        product_id=row["product_id"],
        name=row["name"],
        category=row["category"],
        brand=row["brand"],
        availability=row["availability"],
        stock=row["stock"],
        list_price=_dec(row["list_price"]),
        promo_name=row["promo_name"],
        promo_discount_pct=_dec(row["promo_discount_pct"]),
        final_price=_dec(row["final_price"]),
        pix_price=_dec(row["pix_price"]),
        installments=installment_options(_dec(row["final_price"])),
        ended_promotions=ended,
        description=row["description"],
        specs=row["specs"],
        alternatives=_alternatives(conn, row) if unavailable else [],
    )


def find_product_details(name: str, var_dir: Path | None = None) -> FindResult:
    """Até 3 produtos cujo nome casa com `name`, do mais parecido ao menos."""
    query_norm = normalize_name(name or "")
    conn = open_catalog(var_dir or config.VAR_DIR)
    try:
        rows = conn.execute("SELECT * FROM v_products").fetchall()
        if not query_norm:
            return FindResult(name, [], 0)
        scored = [
            (_score(query_norm, normalize_name(row["name"])), row)
            for row in rows
            if _score(query_norm, normalize_name(row["name"])) >= MATCH_THRESHOLD
        ]
        scored.sort(
            key=lambda item: (
                -item[0],
                -fuzz.ratio(query_norm, normalize_name(item[1]["name"])),
                item[1]["product_id"],
            )
        )
        candidates = [_detail(conn, row) for _, row in scored[:MAX_CANDIDATES]]
        return FindResult(name, candidates, len(scored))
    finally:
        conn.close()


def _format_specs(specs: str | None) -> str | None:
    if not specs:
        return None
    try:
        data = json.loads(specs)
    except json.JSONDecodeError:
        return specs
    return ", ".join(f"{key}: {value}" for key, value in data.items())


def _format_summary(item: ProductSummary) -> str:
    return (
        f"- Produto {item.product_id}: {item.name} — {format_brl(item.final_price)} "
        f"(PIX {format_brl(item.pix_price)}; até {item.max_installments}x de "
        f"{format_brl(item.installment_value)} sem juros)"
    )


def _format_detail(product: ProductDetail) -> str:
    status = Availability(product.availability)
    lines = [
        f"Produto {product.product_id}: {product.name}",
        f"Categoria: {product.category}" + (f" | Marca: {product.brand}" if product.brand else ""),
        f"Situação: {AVAILABILITY_TEXT[status]}",
    ]
    if status is Availability.AVAILABLE:
        lines.append(f"Estoque: {product.stock} unidade(s)")
        lines.append(f"Preço de tabela: {format_brl(product.list_price)}")
        if product.promo_name:
            lines.append(
                f"Promoção ativa: {product.promo_name}, {_pct(product.promo_discount_pct)}% de "
                f"desconto. Preço promocional: {format_brl(product.final_price)} (de "
                f"{format_brl(product.list_price)} por {format_brl(product.final_price)})"
            )
            lines.append(
                f"Preço no PIX: {format_brl(product.pix_price)} (o desconto de 5% do PIX "
                "não se soma à promoção)"
            )
        else:
            lines.append("Promoção ativa: nenhuma")
            lines.append(f"Preço no PIX (5% de desconto): {format_brl(product.pix_price)}")
        top = product.installments[-1]
        lines.append(
            f"Parcelamento sem juros no cartão: até {top.count}x de {format_brl(top.value)}"
        )
        options = "; ".join(f"{i.count}x de {format_brl(i.value)}" for i in product.installments)
        lines.append(f"Opções de parcelamento: {options}")
    else:
        # N-04: o preço de quem não está disponível não é informado.
        lines.append("Preço: não informado enquanto o produto não estiver disponível.")
    if product.ended_promotions:
        ended = "; ".join(f"{name} ({_pct(pct)}%)" for name, pct in product.ended_promotions)
        lines.append(f"Promoções encerradas (não valem mais): {ended}")
    if product.description:
        lines.append(f"Descrição: {product.description}")
    specs = _format_specs(product.specs)
    if specs:
        lines.append(f"Características: {specs}")
    if product.alternatives:
        lines.append("Alternativas disponíveis (mesma categoria, preço próximo):")
        lines.extend(_format_summary(item) for item in product.alternatives)
    return "\n".join(lines)


def find_product_text(name: str, var_dir: Path | None = None) -> str:
    """Texto da ferramenta `find_product`."""
    result = find_product_details(name, var_dir)
    if not result.candidates:
        return (
            f"Nenhum produto encontrado com o nome '{name}'. Não invente produtos: diga "
            "que não encontrou e sugira ampliar a busca (por tipo, marca ou faixa de "
            "preço, com query_catalog)."
        )
    header = f"{len(result.candidates)} produto(s) mais parecido(s) com '{name}':"
    if result.total_matches > len(result.candidates):
        header += (
            f" (há {result.total_matches} produtos com nome parecido; mostre uma seleção "
            "curta e ofereça filtrar mais, por exemplo com query_catalog)"
        )
    blocks = [_format_detail(product) for product in result.candidates]
    return "\n\n".join([header, *blocks])


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[dict[str, object]]
    error: str | None = None
    limit: int | None = None


def _unique(names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        result.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return result


def run_catalog_query(
    sql: str, var_dir: Path | None = None, *, timeout_s: float = QUERY_TIMEOUT_SECONDS
) -> QueryResult:
    """Valida e roda a consulta; erros voltam em `error`, nunca como exceção."""
    try:
        tree = parse_validated(sql)
    except SqlValidationError as error:
        return QueryResult([], [], f"consulta recusada. {error}")

    conn = open_catalog(var_dir or config.VAR_DIR)
    deadline = time.monotonic() + timeout_s
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), _PROGRESS_STEPS)
    try:
        cursor = conn.execute(tree.sql(dialect="sqlite"))
        raw_rows = cursor.fetchmany(MAX_ROWS)
        names = _unique([d[0] for d in cursor.description])
    except sqlite3.OperationalError as error:
        if "interrupted" in str(error):
            return QueryResult(
                [], [], "a consulta passou do tempo-limite. Simplifique o filtro ou a junção."
            )
        return QueryResult([], [], f"o banco recusou a consulta: {error}")
    finally:
        conn.close()

    flags = money_output_flags(tree)
    if len(flags) != len(names):  # fallback conservador: pelo nome da coluna
        flags = [
            name in {"list_price", "final_price", "pix_price", "installment_value"}
            for name in names
        ]
    rows = []
    for raw in raw_rows:
        row: dict[str, object] = {}
        for name, money, value in zip(names, flags, tuple(raw), strict=True):
            is_number = isinstance(value, int | float) and not isinstance(value, bool)
            row[name] = format_brl(value) if money and is_number else value
        rows.append(row)
    return QueryResult(names, rows, limit=int(tree.args["limit"].expression.name))


def query_catalog_text(
    sql: str, var_dir: Path | None = None, *, timeout_s: float = QUERY_TIMEOUT_SECONDS
) -> str:
    """Texto da ferramenta `query_catalog`."""
    result = run_catalog_query(sql, var_dir, timeout_s=timeout_s)
    if result.error:
        return f"Erro: {result.error}"
    count = len(result.rows)
    label = "1 linha" if count == 1 else f"{count} linhas"
    payload = json.dumps(result.rows, ensure_ascii=False)
    text = f"{label} (máximo de {MAX_ROWS}). Valores de dinheiro já formatados:\n{payload}"
    if result.limit is not None and count == result.limit:
        text += (
            f"\nAtenção: resultado limitado a {count} linhas pelo LIMIT; pode haver mais "
            "itens. Para informar o total, use COUNT(*)."
        )
    return text


QUERY_CATALOG_DESCRIPTION = f"""\
Consulta o catálogo com um SELECT em SQLite. Use para listas e filtros (tipo, \
marca, faixa de preço, mais barato por categoria, contagens). Para um produto \
pelo nome, prefira find_product.

Visões disponíveis (só estas):
- v_products: product_id, name, category, brand, list_price (preço de tabela), \
promo_name e promo_discount_pct (só a promoção ATIVA; nulos se não houver), \
final_price (preço com a promoção ativa, ou o de tabela), pix_price (preço no \
PIX), max_installments e installment_value (maior parcelamento sem juros), \
stock, status, availability ('available', 'out_of_stock', 'discontinued', \
'coming_soon'), description, specs (JSON em texto).
- v_categories: category, description, available_products.
Categorias: Guitarras, Baixos, Baterias e Percussão, Teclados e Pianos, \
Violões, Instrumentos de Sopro (Madeiras), Instrumentos de Sopro (Metais), \
Cordas Orquestrais, Ukuleles.

Regras: uma única instrução SELECT, sem comentários. Na lista do SELECT só \
colunas, *, COUNT, MIN(coluna) e MAX(coluna); nada de contas (+ - * /), SUM, \
AVG, ROUND, CASE ou CAST. No WHERE/ORDER BY: comparações, AND/OR/NOT, IN, \
BETWEEN, LIKE, IS NULL, lower, upper e trim. No máximo {MAX_ROWS} linhas. \
Para opções ao cliente, filtre availability = 'available' e compare preço por \
final_price. Os valores de dinheiro voltam já formatados em R$: copie-os como \
vieram."""


def build_catalog_tools(
    var_dir: Path | None = None, *, timeout_s: float = QUERY_TIMEOUT_SECONDS
) -> list[BaseTool]:
    """Cria `find_product` e `query_catalog` sobre a pasta de dados informada."""

    @tool
    def find_product(name: str) -> str:
        """Busca um instrumento pelo nome (tolera erro de digitação, falta de
        acento e espaços) e devolve até 3 candidatos com preço de tabela,
        promoção ativa, preço no PIX, opções de parcelamento, disponibilidade,
        promoções encerradas e, se o produto estiver indisponível,
        alternativas disponíveis."""
        return find_product_text(name, var_dir)

    @tool(description=QUERY_CATALOG_DESCRIPTION)
    def query_catalog(sql: str) -> str:
        return query_catalog_text(sql, var_dir, timeout_s=timeout_s)

    return [find_product, query_catalog]
