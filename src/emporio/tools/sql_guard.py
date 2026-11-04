"""Validação do SQL escrito pelo modelo para o catálogo (plan D-08, D-09a e S2-05).

Regras, todas verificadas com o `sqlglot` antes de a consulta rodar:

- uma única instrução `SELECT`, sem comentários;
- só as visões `v_products` e `v_categories` (e CTEs definidas na própria
  consulta), sem prefixo de banco;
- lista fechada de expressões: colunas, literais, comparações, `AND`/`OR`/`NOT`,
  `IN`, `BETWEEN`, `LIKE`, `IS NULL`, as funções `lower`, `upper` e `trim`, e as
  agregações `COUNT`, `MIN` e `MAX`. Nenhum operador aritmético, `CASE`,
  `CAST`, `UNION` ou outra função (N-05);
- na lista do `SELECT` (inclusive em subconsultas e CTEs) só entram colunas
  puras, `*`, `COUNT`, `MIN(coluna)` e `MAX(coluna)`, com ou sem apelido: o SQL
  do modelo não cria valor novo de dinheiro (D-08, princípio II);
- `LIMIT` imposto, no máximo 20 linhas.

Também resolve a coluna de origem de cada saída, para que a ferramenta formate
em `R$` todo valor que venha de uma coluna de dinheiro (D-09a).
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError, TokenError

MAX_ROWS = 20

VIEW_COLUMNS: dict[str, tuple[str, ...]] = {
    "v_products": (
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
    ),
    "v_categories": ("category", "description", "available_products"),
}
ALLOWED_VIEWS = frozenset(VIEW_COLUMNS)
MONEY_COLUMNS = frozenset({"list_price", "final_price", "pix_price", "installment_value"})

_ALLOWED_NODES: tuple[type[exp.Expression], ...] = (
    exp.Select,
    exp.From,
    exp.Join,
    exp.Table,
    exp.TableAlias,
    exp.Identifier,
    exp.Column,
    exp.Star,
    exp.Alias,
    exp.Subquery,
    exp.With,
    exp.CTE,
    exp.Where,
    exp.Group,
    exp.Having,
    exp.Order,
    exp.Ordered,
    exp.Limit,
    exp.Offset,
    exp.Literal,
    exp.Neg,
    exp.Boolean,
    exp.Null,
    exp.Paren,
    exp.EQ,
    exp.NEQ,
    exp.GT,
    exp.GTE,
    exp.LT,
    exp.LTE,
    exp.And,
    exp.Or,
    exp.Not,
    exp.In,
    exp.Between,
    exp.Like,
    exp.Is,
    exp.Lower,
    exp.Upper,
    exp.Trim,
    exp.Count,
    exp.Min,
    exp.Max,
    exp.Distinct,
)

SELECT_LIST_RULE = (
    "Na lista do SELECT só são permitidas colunas, *, COUNT, MIN(coluna) e MAX(coluna), "
    "com ou sem apelido; contas e outras funções não são permitidas. Os valores de "
    "preço, PIX e parcela já vêm calculados nas colunas da visão."
)


class SqlValidationError(ValueError):
    """Consulta recusada; a mensagem volta para o modelo corrigir o SQL."""


def _check_no_comments(sql: str) -> None:
    try:
        tokens = sqlglot.Dialect.get_or_raise("sqlite").tokenize(sql)
    except TokenError as error:
        raise SqlValidationError(f"SQL inválido: {error}") from error
    if any(token.comments for token in tokens):
        raise SqlValidationError("Comentários não são permitidos na consulta.")


def _parse_single_select(sql: str) -> exp.Select:
    if not sql or not sql.strip():
        raise SqlValidationError("A consulta está vazia.")
    _check_no_comments(sql)
    try:
        statements = [s for s in sqlglot.parse(sql, read="sqlite") if s is not None]
    except ParseError as error:
        raise SqlValidationError(f"SQL inválido: {error.errors[0]['description']}") from error
    if len(statements) != 1:
        raise SqlValidationError("Envie uma única instrução SELECT por consulta.")
    root = statements[0]
    if not isinstance(root, exp.Select):
        raise SqlValidationError(
            f"Só consultas SELECT são permitidas (recebido: {root.key.upper()})."
        )
    return root


def _cte_names(root: exp.Select) -> set[str]:
    return {cte.alias_or_name for cte in root.find_all(exp.CTE)}


def _check_nodes(root: exp.Select) -> None:
    for node in root.walk():
        if not isinstance(node, _ALLOWED_NODES):
            raise SqlValidationError(
                f"Expressão não permitida: {node.key.upper()}. Use só colunas, literais, "
                "comparações, AND/OR/NOT, IN, BETWEEN, LIKE, IS NULL, lower, upper, trim, "
                "COUNT, MIN e MAX."
            )
        if isinstance(node, exp.Neg) and not isinstance(node.this, exp.Literal):
            raise SqlValidationError("Operador aritmético não permitido.")
        if isinstance(node, exp.Limit | exp.Offset):
            value = node.expression
            if not (isinstance(value, exp.Literal) and value.is_int):
                raise SqlValidationError("LIMIT e OFFSET aceitam só um número inteiro.")


def _check_tables(root: exp.Select) -> None:
    ctes = _cte_names(root)
    for table in root.find_all(exp.Table):
        if table.args.get("db") or table.args.get("catalog"):
            raise SqlValidationError("Use o nome da visão sem prefixo de banco.")
        if table.name not in ALLOWED_VIEWS and table.name not in ctes:
            raise SqlValidationError(
                f"Tabela não permitida: {table.name}. Use só v_products e v_categories."
            )


def _is_allowed_projection(expression: exp.Expression) -> bool:
    inner = expression.this if isinstance(expression, exp.Alias) else expression
    if isinstance(inner, exp.Star | exp.Column):
        return True
    if isinstance(inner, exp.Count):
        arg = inner.this
        if isinstance(arg, exp.Distinct):
            return all(isinstance(e, exp.Column) for e in arg.expressions)
        return isinstance(arg, exp.Star | exp.Column)
    if isinstance(inner, exp.Min | exp.Max):
        return isinstance(inner.this, exp.Column)
    return False


def _check_select_lists(root: exp.Select) -> None:
    for select in root.find_all(exp.Select):
        for projection in select.expressions:
            if not _is_allowed_projection(projection):
                raise SqlValidationError(f"{SELECT_LIST_RULE} Recusado: {projection.sql()}")


def _enforce_limit(root: exp.Select) -> exp.Select:
    limit = root.args.get("limit")
    if limit is None:
        return root.limit(MAX_ROWS)
    if int(limit.expression.name) > MAX_ROWS:
        return root.limit(MAX_ROWS)
    return root


def parse_validated(sql: str) -> exp.Select:
    """Valida a consulta e devolve a árvore já com o `LIMIT` imposto."""
    root = _parse_single_select(sql)
    _check_select_lists(root)  # antes, para a mensagem citar a regra do SELECT
    _check_nodes(root)
    _check_tables(root)
    return _enforce_limit(root)


def validate_sql(sql: str) -> str:
    """Valida a consulta e devolve o SQL que pode rodar (com `LIMIT`)."""
    return parse_validated(sql).sql(dialect="sqlite")


# --- Coluna de origem de cada saída (D-09a) ---------------------------------

Output = tuple[str, bool]  # (nome, é dinheiro)


def _source_outputs(node: exp.Expression, ctes: dict[str, exp.Select]) -> tuple[str, list[Output]]:
    if isinstance(node, exp.Subquery):
        return node.alias_or_name, _select_outputs(node.this, ctes)
    if isinstance(node, exp.Table):
        if node.name in ctes:
            return node.alias_or_name, _select_outputs(ctes[node.name], ctes)
        columns = VIEW_COLUMNS.get(node.name, ())
        return node.alias_or_name, [(c, c in MONEY_COLUMNS) for c in columns]
    return node.alias_or_name, []


def _select_outputs(select: exp.Expression, ctes: dict[str, exp.Select]) -> list[Output]:
    if not isinstance(select, exp.Select):
        return []
    scope = dict(ctes)
    with_clause = select.args.get("with_") or select.args.get("with")
    if with_clause is not None:
        for cte in with_clause.expressions:
            scope[cte.alias_or_name] = cte.this

    sources: list[tuple[str, list[Output]]] = []
    from_clause = select.args.get("from_") or select.args.get("from")
    if from_clause is not None:
        sources.append(_source_outputs(from_clause.this, scope))
    for join in select.args.get("joins") or []:
        sources.append(_source_outputs(join.this, scope))

    def is_money(column: exp.Column) -> bool:
        for alias, outputs in sources:
            if column.table and column.table != alias:
                continue
            for name, money in outputs:
                if name == column.name:
                    return money
        return False

    result: list[Output] = []
    for projection in select.expressions:
        inner = projection.this if isinstance(projection, exp.Alias) else projection
        name = projection.alias_or_name
        if isinstance(inner, exp.Star):
            for _, outputs in sources:
                result.extend(outputs)
        elif isinstance(inner, exp.Column) and isinstance(inner.this, exp.Star):
            for alias, outputs in sources:
                if alias == inner.table:
                    result.extend(outputs)
        elif isinstance(inner, exp.Column):
            result.append((name, is_money(inner)))
        elif isinstance(inner, exp.Min | exp.Max) and isinstance(inner.this, exp.Column):
            result.append((name, is_money(inner.this)))
        else:
            result.append((name, False))
    return result


def money_output_flags(root: exp.Select) -> list[bool]:
    """Para cada coluna da saída, se o valor vem de uma coluna de dinheiro."""
    return [money for _, money in _select_outputs(root, {})]
