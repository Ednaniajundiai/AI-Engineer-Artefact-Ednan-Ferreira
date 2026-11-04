"""Prompt e grafo da história 2 (FR-004 a FR-010; plan D-03, D-09)."""

from datetime import datetime

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from tests.fakes import ScriptedChatModel, tool_call

from emporio.agent.graph import build_graph, get_tools
from emporio.agent.prompt import build_system_prompt
from emporio.config import TIMEZONE
from emporio.tools.catalog import build_catalog_tools


@pytest.fixture(scope="module")
def prompt():
    return build_system_prompt(datetime(2025, 11, 3, 10, 30, tzinfo=TIMEZONE))


def test_registry_has_the_catalog_tools():
    names = {tool.name for tool in get_tools()}
    assert {"find_product", "query_catalog"} <= names


def test_guide_names_the_catalog_tools(prompt):
    assert "find_product" in prompt
    assert "query_catalog" in prompt


def test_values_are_copied_without_recalculating(prompt):
    # FR-004, SC-002: o modelo não faz conta de dinheiro.
    lowered = prompt.lower()
    assert "copie os valores" in lowered
    assert "sem recalcular" in lowered


def test_promotion_is_shown_with_original_price_and_percent(prompt):
    # FR-007 e manual 6.2.
    assert "preço original" in prompt
    assert "percentual" in prompt
    assert "não se soma" in prompt


def test_unavailable_products_get_alternatives(prompt):
    # FR-009: sem estoque, descontinuado ou em breve, sempre com alternativas.
    for phrase in ("temporariamente indisponível", "não faz mais parte do catálogo"):
        assert phrase in prompt
    assert "ainda não está à venda" in prompt
    assert "alternativas" in prompt


def test_options_lists_only_available_products(prompt):
    # FR-005: quando o cliente pede opções, só disponíveis.
    assert "availability = 'available'" in prompt


def test_ended_promotion_is_reported_with_transparency(prompt):
    # FR-010.
    assert "não está mais vigente" in prompt


def test_empty_category_points_to_the_store_contacts(prompt):
    # US2 cenário 8, S-10.
    assert "encomenda" in prompt


def test_short_selection_when_there_are_many_results(prompt):
    assert "seleção curta" in prompt


def test_installments_follow_the_tool(prompt):
    # FR-008: número de parcelas e valor vêm da ferramenta.
    assert "parcelas" in prompt


def test_find_product_runs_inside_the_graph(var_dir, clock):
    model = ScriptedChatModel(
        responses=[
            tool_call("find_product", {"name": "takamine gd 20"}),
            AIMessage(content="O Takamine GD20 sai por R$ 2.199,00."),
        ]
    )
    tools = build_catalog_tools(var_dir)
    graph = build_graph(model, tools=tools, clock=clock(2025, 11, 3, 10, 0))
    result = graph.invoke(
        {"messages": [("user", "quanto custa o takamine gd 20?")]},
        {"configurable": {"thread_id": "us2"}},
    )
    output = next(m for m in result["messages"] if isinstance(m, ToolMessage)).content
    assert "R$ 2.089,05" in output


def test_query_catalog_error_goes_back_to_the_model_as_text(var_dir, clock):
    model = ScriptedChatModel(
        responses=[
            tool_call("query_catalog", {"sql": "SELECT SUM(final_price) FROM v_products"}),
            AIMessage(content="Deixa eu tentar de outro jeito."),
        ]
    )
    graph = build_graph(model, tools=build_catalog_tools(var_dir), clock=clock(2025, 11, 3))
    result = graph.invoke(
        {"messages": [("user", "quanto custa tudo?")]}, {"configurable": {"thread_id": "e"}}
    )
    output = next(m for m in result["messages"] if isinstance(m, ToolMessage)).content
    assert output.startswith("Erro")
    assert result["messages"][-1].content == "Deixa eu tentar de outro jeito."
