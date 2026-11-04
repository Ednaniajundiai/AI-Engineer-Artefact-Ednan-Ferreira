"""Conjunto fixo de perguntas da avaliação (FR-023; plan S2-12).

Os casos ficam em `evals/cases.yaml`. Cada caso tem uma ou várias mensagens do
cliente, a fonte de consulta esperada e, opcionalmente, o que a resposta deve
conter ou nunca conter. Os valores de dinheiro e de pedido não são escritos à
mão: o YAML usa marcadores como `{{pix_price:95}}`, calculados aqui pelas
mesmas regras do agente, a partir dos CSVs, na hora da avaliação.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import yaml

from emporio.data.loader import CSV_PREFIX
from emporio.money import format_brl
from emporio.rules.installments import max_installments
from emporio.rules.pricing import PromotionRecord, active_promotion, price_quote

TOOLS = frozenset(
    {
        "get_store_info",
        "get_policy",
        "find_product",
        "query_catalog",
        "get_order_status",
        "register_complaint",
        "none",
    }
)
CRITERIA = ("SC-001", "SC-002", "SC-003", "SC-004")
DEFAULT_CRITERIA = ("SC-001", "SC-002", "SC-003")

_PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*:\s*(\d+)\s*\}\}")


class CaseError(ValueError):
    """Caso de avaliação inválido."""


def _read_csv(data_dir: Path, name: str) -> list[dict[str, str]]:
    with (data_dir / f"{CSV_PREFIX}{name}.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _pct(value: Decimal) -> str:
    return format(value.normalize(), "f") + "%"


@dataclass
class ExpectedValues:
    """Valores esperados, calculados pelas regras: `{{campo:id}}` -> texto."""

    values: dict[tuple[str, int], str]
    orders: dict[int, dict[str, str]] = field(default_factory=dict)
    personal: list[str] = field(default_factory=list)

    @classmethod
    def from_data(cls, data_dir: Path) -> ExpectedValues:
        values: dict[tuple[str, int], str] = {}
        promotions: dict[int, list[PromotionRecord]] = {}
        for row in _read_csv(data_dir, "promotions"):
            promotions.setdefault(int(row["product_id"]), []).append(
                PromotionRecord(
                    name=row["description"],
                    discount_pct=Decimal(row["discount_percent"]),
                    is_active=row["is_active"].strip() == "1",
                )
            )
        for row in _read_csv(data_dir, "products"):
            pid = int(row["product_id"])
            promo = active_promotion(promotions.get(pid, []))
            quote = price_quote(Decimal(row["price_brl"]), promo.discount_pct if promo else None)
            plan = max_installments(quote.final_price)
            values[("list_price", pid)] = format_brl(quote.list_price)
            values[("final_price", pid)] = format_brl(quote.final_price)
            values[("pix_price", pid)] = format_brl(quote.pix_price)
            values[("installment_value", pid)] = format_brl(plan.value)
            values[("max_installments", pid)] = f"{plan.count}x"
            if promo:
                values[("promo_pct", pid)] = _pct(promo.discount_pct)

        customers = {int(r["customer_id"]): r for r in _read_csv(data_dir, "customers")}
        personal: list[str] = []
        for customer in customers.values():
            personal.extend([customer["email"].strip(), customer["phone"].strip()])
            if len(customer["name"].split()) > 1:
                personal.append(customer["name"].strip())
        orders: dict[int, dict[str, str]] = {}
        for row in _read_csv(data_dir, "orders"):
            oid = int(row["order_id"])
            owner = customers[int(row["customer_id"])]
            orders[oid] = {
                "tracking": row["tracking_code"].strip(),
                "total": format_brl(row["total_brl"]),
                "email": owner["email"].strip(),
            }
            values[("order_total", oid)] = orders[oid]["total"]
            if orders[oid]["tracking"]:
                values[("order_tracking", oid)] = orders[oid]["tracking"]
        return cls(values=values, orders=orders, personal=personal)

    def resolve(self, text: str) -> str:
        def replace(match: re.Match[str]) -> str:
            key = (match.group(1), int(match.group(2)))
            if key not in self.values:
                raise CaseError(f"marcador desconhecido: {{{{{match.group(1)}:{match.group(2)}}}}}")
            return self.values[key]

        return _PLACEHOLDER.sub(replace, text)


@dataclass(frozen=True)
class EvalCase:
    id: str
    turns: list[str]
    expected_tools: list[str]
    must_contain: list[str]
    must_not_contain: list[str]
    criteria: tuple[str, ...]
    description: str = ""


def _string_list(case_id: str, raw: dict, key: str, *, required: bool = False) -> list[str]:
    value = raw.get(key)
    if value is None:
        if required:
            raise CaseError(f"caso '{case_id}': falta o campo '{key}'")
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise CaseError(f"caso '{case_id}': '{key}' deve ser uma lista de textos")
    if required and not value:
        raise CaseError(f"caso '{case_id}': '{key}' não pode ser vazio")
    return value


def _parse_case(raw: object, values: ExpectedValues, index: int) -> EvalCase:
    if not isinstance(raw, dict):
        raise CaseError(f"caso {index}: deve ser um mapa")
    case_id = raw.get("id")
    if not isinstance(case_id, str) or not case_id.strip():
        raise CaseError(f"caso {index}: falta o campo 'id'")
    turns = _string_list(case_id, raw, "turns", required=True)
    expected = _string_list(case_id, raw, "expected_tools", required=True)
    for entry in expected:
        for name in entry.split("|"):
            if name not in TOOLS:
                raise CaseError(f"caso '{case_id}': ferramenta desconhecida '{name}'")
    criteria = tuple(_string_list(case_id, raw, "criteria") or DEFAULT_CRITERIA)
    for criterion in criteria:
        if criterion not in CRITERIA:
            raise CaseError(f"caso '{case_id}': critério desconhecido '{criterion}'")
    try:
        must_contain = [values.resolve(v) for v in _string_list(case_id, raw, "must_contain")]
        must_not = [values.resolve(v) for v in _string_list(case_id, raw, "must_not_contain")]
    except CaseError as error:
        raise CaseError(f"caso '{case_id}': {error}") from error
    return EvalCase(
        id=case_id,
        turns=turns,
        expected_tools=expected,
        must_contain=must_contain,
        must_not_contain=must_not,
        criteria=criteria,
        description=str(raw.get("description", "")),
    )


def load_cases(path: Path, values: ExpectedValues) -> list[EvalCase]:
    """Lê e valida os casos do YAML, resolvendo os valores esperados."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(raw_cases, list):
        raise CaseError(f"{path}: o arquivo deve ter uma lista 'cases'")
    cases = [_parse_case(raw, values, i) for i, raw in enumerate(raw_cases, start=1)]
    seen: set[str] = set()
    for case in cases:
        if case.id in seen:
            raise CaseError(f"id repetido: '{case.id}'")
        seen.add(case.id)
    return cases
