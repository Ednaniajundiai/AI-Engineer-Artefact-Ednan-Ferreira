"""Prompt e grafo da história 3 (FR-011, FR-013, FR-015, FR-016; S-12, S-14)."""

from datetime import datetime

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from tests.fakes import ScriptedChatModel, tool_call

from emporio.agent.graph import build_graph, get_tools
from emporio.agent.prompt import build_system_prompt
from emporio.config import TIMEZONE
from emporio.tools.orders import NOT_FOUND, build_order_tool


@pytest.fixture(scope="module")
def prompt():
    return build_system_prompt(datetime(2026, 11, 3, 10, 30, tzinfo=TIMEZONE))


def test_registry_has_the_order_tool():
    assert "get_order_status" in {tool.name for tool in get_tools()}


def test_asks_number_and_email_before_any_lookup(prompt):
    assert "get_order_status" in prompt
    assert "número do pedido e o e-mail" in prompt
    assert "antes de consultar" in prompt


def test_confirms_the_email_again_for_another_order(prompt):
    # FR-015.
    assert "outro pedido" in prompt
    assert "verificação de novo" in prompt


def test_never_reveals_third_party_data(prompt):
    # FR-013, US3 cenário 6.
    assert "dados pessoais" in prompt
    assert "de outro cliente" in prompt


def test_failed_verification_does_not_say_which_field_is_wrong(prompt):
    # FR-012.
    assert "qual dos dois" in prompt


def test_withdrawal_asks_the_channel_and_warns_the_date_is_an_estimate(prompt):
    # FR-016, S-14.
    assert "compra foi online" in prompt
    assert "estimativa" in prompt
    assert "troca por defeito" in prompt
    assert "garantia" in prompt


def test_overdue_forecast_offers_a_complaint(prompt):
    # US3 cenário 4, S-12.
    assert "previsão de entrega já passou" in prompt
    assert "reclamação" in prompt


def test_registered_total_is_not_recalculated(prompt):
    # S-04, S-05.
    assert "total registrado" in prompt


def _run(var_dir, clock, responses, question):
    model = ScriptedChatModel(responses=responses)
    fixed = clock(2026, 11, 3, 10, 0)
    graph = build_graph(model, tools=[build_order_tool(var_dir, fixed)], clock=fixed)
    return graph.invoke({"messages": [("user", question)]}, {"configurable": {"thread_id": "o"}})


def test_failed_verification_leaves_no_order_data_in_the_thread(var_dir, clock):
    result = _run(
        var_dir,
        clock,
        [
            tool_call("get_order_status", {"order_id": "1", "email": "intruso@jmail.com"}),
            AIMessage(content="Não localizei o pedido com esses dados."),
        ],
        "pedido 1, e-mail intruso@jmail.com",
    )
    everything = "\n".join(str(message.content) for message in result["messages"])
    for leaked in ("Pedro", "BRAB1234567BR", "11.499", "Martin", "15/10/2025", "entregue"):
        assert leaked not in everything
    tool_output = next(m for m in result["messages"] if isinstance(m, ToolMessage)).content
    assert tool_output == NOT_FOUND


def test_verified_order_reaches_the_model(var_dir, clock):
    result = _run(
        var_dir,
        clock,
        [
            tool_call(
                "get_order_status", {"order_id": "#8", "email": "anacarol.ferreira@coldmail.com"}
            ),
            AIMessage(content="Seu pedido foi enviado."),
        ],
        "cadê meu pedido #8? anacarol.ferreira@coldmail.com",
    )
    tool_output = next(m for m in result["messages"] if isinstance(m, ToolMessage)).content
    assert "BRJL5544332BR" in tool_output
    assert "já passou" in tool_output
