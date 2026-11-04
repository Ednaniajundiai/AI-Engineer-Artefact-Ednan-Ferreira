"""Ferramenta `get_order_status` (FR-011 a FR-016; S-04, S-05, S-11, S-12, S-14)."""

import csv

import pytest

from emporio.tools.orders import (
    NOT_FOUND,
    build_order_tool,
    lookup_order,
    order_status_text,
    parse_order_id,
)

TODAY = (2026, 11, 3)


@pytest.fixture
def text(var_dir, clock):
    return lambda order, email: order_status_text(order, email, var_dir, clock(*TODAY)().date())


@pytest.fixture
def lookup(var_dir, clock):
    return lambda order, email: lookup_order(order, email, var_dir, clock(*TODAY)().date())


def _customers():
    from tests.conftest import DATA_DIR

    path = DATA_DIR / "desafio_tecnico_ai_eng - customers.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("8", 8), ("#8", 8), ("nº 8", 8), ("pedido 8", 8), ("Pedido nº 08", 8), ("n° 12", 12)],
)
def test_order_number_formats(raw, expected):
    assert parse_order_id(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "8 e 9", None])
def test_invalid_order_numbers(raw):
    assert parse_order_id(raw) is None


def test_correct_number_and_email_show_the_order(text):
    output = text("1", "pedro.oliveira@jmail.com")
    assert "Pedro" in output
    assert "entregue" in output
    assert "15/10/2025" in output
    assert "Martin D-28 Dreadnought Natural" in output
    assert "R$ 11.499,00" in output
    assert "BRAB1234567BR" in output


def test_email_is_case_and_space_insensitive(text):
    output = text("#1", "  Pedro.Oliveira@JMAIL.com ")
    assert "BRAB1234567BR" in output


def test_wrong_email_and_missing_order_give_the_same_answer(text):
    wrong_email = text("1", "outra.pessoa@jmail.com")
    missing = text("999", "pedro.oliveira@jmail.com")
    invalid = text("abc", "pedro.oliveira@jmail.com")
    assert wrong_email == missing == invalid == NOT_FOUND
    for leaked in ("Pedro", "BRAB1234567BR", "11.499", "Martin", "entregue"):
        assert leaked not in wrong_email


def test_shared_email_opens_only_the_order_of_customer_11(lookup):
    # S-11: clientes 11 e 43 têm o mesmo e-mail; só o 11 tem pedido (o 10).
    opened = [n for n in range(1, 21) if lookup(str(n), "bruno.martins@jmail.com") is not None]
    assert opened == [10]
    assert lookup("10", "bruno.martins@jmail.com").first_name == "Bruno"


def test_overdue_forecast_on_order_8(text, lookup):
    # S-12: enviado, com previsão em 28/02/2026, já vencida.
    order = lookup("8", "anacarol.ferreira@coldmail.com")
    assert order.forecast_overdue is True
    output = text("8", "anacarol.ferreira@coldmail.com")
    assert "BRJL5544332BR" in output
    assert "28/02/2026" in output
    assert "já passou" in output


def test_delivered_order_is_not_overdue(lookup):
    assert lookup("1", "pedro.oliveira@jmail.com").forecast_overdue is False


def test_cancelled_order_shows_the_reason(text):
    output = text("19", "pedro.oliveira@jmail.com")
    assert "cancelado" in output
    assert "Pagamento não confirmado dentro do prazo" in output


@pytest.mark.parametrize(
    ("order", "email", "total"),
    [
        ("1", "pedro.oliveira@jmail.com", "R$ 11.499,00"),  # PIX sem desconto (S-04)
        ("3", "isabela.moreira@jmail.com", "R$ 3.450,00"),  # total ≠ itens (S-05)
        ("5", "rafael.pereira@jmail.com", "R$ 4.599,00"),  # S-04
        ("10", "bruno.martins@jmail.com", "R$ 8.732,00"),  # S-04
        ("20", "thiago.barbosa@jmail.com", "R$ 1.400,00"),  # S-05
    ],
)
def test_registered_total_is_reported_without_recalculation(text, order, email, total):
    assert f"Total registrado: {total}" in text(order, email)


def test_pending_and_confirmed_have_no_tracking(text):
    output = text("13", "fernanda.ribeiro@coldmail.com")
    assert "pendente" in output
    assert "Rastreio" not in output
    assert "confirmado" in text("9", "juliana.almeida@hayoo.com.br")


def test_coming_soon_product_in_an_order_is_shown_to_the_owner(text):
    # S-06: o pedido existente com o produto 130 aparece normalmente.
    assert "Kala KA-ABP-CTG Barítono Cedar" in text("14", "diego.castro@coldmail.com")


def test_delivered_order_brings_the_after_sale_deadlines(text):
    output = text("1", "pedro.oliveira@jmail.com")
    assert "arrependimento" in output.lower()
    assert "estimativa" in output  # S-14
    assert "01/11/2025" in output  # 7 dias após 25/10/2025
    assert "14/11/2025" in output  # 30 dias após 15/10/2025
    assert "23/01/2026" in output  # 90 dias após 25/10/2025
    assert "encerrado" in output


def test_output_never_has_personal_data_beyond_the_first_name(text):
    customers = {int(c["customer_id"]): c for c in _customers()}
    from tests.conftest import DATA_DIR

    path = DATA_DIR / "desafio_tecnico_ai_eng - orders.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        orders = list(csv.DictReader(handle))
    for order in orders:
        owner = customers[int(order["customer_id"])]
        output = text(order["order_id"], owner["email"])
        assert owner["name"].split()[0] in output
        assert owner["email"] not in output
        assert owner["phone"] not in output
        assert owner["city"] not in output
        assert owner["name"] not in output  # nome completo


def test_each_call_verifies_again(text):
    # FR-015: a ferramenta não guarda estado entre chamadas.
    assert "BRAB1234567BR" in text("1", "pedro.oliveira@jmail.com")
    assert text("2", "pedro.oliveira@jmail.com") == NOT_FOUND


def test_tool_requires_both_fields(var_dir, clock):
    tool = build_order_tool(var_dir, clock(*TODAY))
    schema = tool.args_schema.model_json_schema()
    assert set(schema["required"]) == {"order_id", "email"}
    assert "BRAB1234567BR" in tool.invoke({"order_id": "1", "email": "pedro.oliveira@jmail.com"})
