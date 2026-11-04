"""Leitura dos casos de avaliação (FR-023, FR-024)."""

import re
from decimal import Decimal

import pytest

from emporio import config
from emporio.evaluation.cases import CaseError, ExpectedValues, load_cases
from emporio.rules.installments import max_installments
from emporio.rules.pricing import price_quote


@pytest.fixture(scope="module")
def values():
    return ExpectedValues.from_data(config.DATA_DIR)


def write(tmp_path, text):
    path = tmp_path / "cases.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_single_and_multi_turn_cases_are_read(tmp_path, values):
    path = write(
        tmp_path,
        """
cases:
  - id: um
    turns: ["Quanto custa o Takamine GD20?"]
    expected_tools: [find_product]
    must_contain: ["{{pix_price:95}}"]
  - id: dois
    turns:
      - "Quero saber do meu pedido"
      - "Pedido 8, anacarol.ferreira@coldmail.com"
    expected_tools: [get_order_status]
    must_not_contain: ["{{order_tracking:1}}"]
    criteria: [SC-001, SC-003]
""",
    )
    cases = load_cases(path, values)
    assert [case.id for case in cases] == ["um", "dois"]
    assert cases[1].turns[1].startswith("Pedido 8")
    assert cases[0].must_contain == ["R$ 2.089,05"]
    assert cases[1].must_not_contain == ["BRAB1234567BR"]


def test_expected_values_are_computed_by_the_rules(values):
    quote = price_quote(Decimal("2399"), Decimal("18"))
    plan = max_installments(quote.final_price)
    assert values.resolve("{{final_price:90}}") == "R$ 1.967,18"
    assert values.resolve("{{list_price:90}}") == "R$ 2.399,00"
    assert values.resolve("{{installment_value:90}}") == f"R$ {plan.value}".replace(".", ",")
    assert values.resolve("{{max_installments:95}}") == "12x"
    assert values.resolve("{{promo_pct:90}}") == "18%"
    assert values.resolve("{{order_total:10}}") == "R$ 8.732,00"
    assert values.resolve("{{order_tracking:8}}") == "BRJL5544332BR"
    assert values.resolve("PIX: {{pix_price:95}}!") == "PIX: R$ 2.089,05!"


def test_unknown_placeholder_is_a_clear_error(values):
    with pytest.raises(CaseError) as error:
        values.resolve("{{preco_magico:95}}")
    assert "preco_magico" in str(error.value)


@pytest.mark.parametrize(
    ("body", "fragment"),
    [
        ('  - turns: ["oi"]\n    expected_tools: [none]', "id"),
        ("  - id: x\n    expected_tools: [none]", "turns"),
        ('  - id: x\n    turns: ["oi"]\n    expected_tools: [teletransporte]', "teletransporte"),
        ('  - id: x\n    turns: ["oi"]', "expected_tools"),
        ('  - id: x\n    turns: ["oi"]\n    expected_tools: [none]\n    criteria: [SC-9]', "SC-9"),
        ("  - id: x\n    turns: []\n    expected_tools: [none]", "turns"),
    ],
)
def test_invalid_case_gives_a_clear_error(tmp_path, values, body, fragment):
    path = write(tmp_path, f"cases:\n{body}\n")
    with pytest.raises(CaseError) as error:
        load_cases(path, values)
    assert fragment in str(error.value)


def test_duplicate_ids_are_rejected(tmp_path, values):
    body = '  - id: x\n    turns: ["oi"]\n    expected_tools: [none]\n'
    path = write(tmp_path, f"cases:\n{body}{body}")
    with pytest.raises(CaseError) as error:
        load_cases(path, values)
    assert "x" in str(error.value)


# --- O conjunto fixo do projeto ----------------------------------------------


@pytest.fixture(scope="module")
def project_cases(values):
    return load_cases(config.EVALS_DIR / "cases.yaml", values)


def test_project_cases_load(project_cases):
    assert len(project_cases) >= 30


def test_project_cases_have_no_hand_written_money():
    # Os valores esperados vêm das regras ({{...}}), nunca escritos à mão.
    import yaml

    raw = yaml.safe_load((config.EVALS_DIR / "cases.yaml").read_text(encoding="utf-8"))
    for case in raw["cases"]:
        for entry in case.get("must_contain", []) + case.get("must_not_contain", []):
            assert not re.search(r"R\$\s?\d", entry), (case["id"], entry)


def test_project_cases_cover_every_question_type(project_cases):
    tools = {tool for case in project_cases for tool in case.expected_tools}
    assert {
        "get_store_info",
        "get_policy",
        "find_product",
        "query_catalog",
        "get_order_status",
        "none",
    } <= tools
    ids = {case.id for case in project_cases}
    for required in (
        "horario-aberto",
        "endereco-contatos",
        "arrependimento",
        "preco-takamine-95",
        "preco-promocao-90",
        "indisponivel-96",
        "descontinuado-136",
        "em-breve-130",
        "violoes-ate-1000",
        "promocao-encerrada",
        "categoria-sem-produtos",
        "pedido-verificado",
        "verificacao-falha",
        "pedido-a-depois-b",
        "dados-de-terceiro",
        "cancelar-pedido",
        "injecao-prompt",
        "acessorio-cordas",
        "alheio-receita",
    ):
        assert required in ids, required


def test_every_scope_case_goes_to_the_judge(project_cases):
    for case in project_cases:
        if case.id.startswith(("acessorio-", "alheio-")) or case.id in {
            "cancelar-pedido",
            "injecao-prompt",
        }:
            assert "SC-004" in case.criteria, case.id
