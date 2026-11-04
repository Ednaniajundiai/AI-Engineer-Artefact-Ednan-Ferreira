"""Registro de ferramentas: nada escreve nos dados da loja (FR-019; princípio IV)."""

import hashlib
import shutil

import pytest
from langchain_core.messages import AIMessage
from tests.fakes import ScriptedChatModel, tool_call

from emporio import config
from emporio.agent.graph import build_graph, called_tools, get_tools

SAMPLE_ARGS = {
    "get_store_info": [{}],
    "get_policy": [{"topic": "frete"}],
    "find_product": [{"name": "takamine gd 20"}],
    "query_catalog": [
        {"sql": "SELECT * FROM v_products"},
        {"sql": "DELETE FROM products"},
        {"sql": "SELECT * FROM v_products; DROP TABLE products"},
    ],
    "get_order_status": [{"order_id": "1", "email": "pedro.oliveira@jmail.com"}],
    "register_complaint": [
        {"name": "Cliente Teste", "contact": "teste@exemplo.com", "description": "Teste."}
    ],
}

WRITERS = {"register_complaint"}


def _digest(folder):
    return {
        path.relative_to(folder).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


@pytest.fixture
def sandbox(tmp_path, var_dir, monkeypatch, clock):
    data = tmp_path / "data"
    var = tmp_path / "var"
    records = tmp_path / "registros"
    shutil.copytree(config.DATA_DIR, data)
    shutil.copytree(var_dir, var)
    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "VAR_DIR", var)
    monkeypatch.setattr(config, "RECORDS_DIR", records)
    return data, var, records, get_tools(clock(2026, 11, 3, 10, 0))


def test_every_registered_tool_has_sample_arguments(sandbox):
    *_, tools = sandbox
    assert {tool.name for tool in tools} <= set(SAMPLE_ARGS)


def test_no_tool_writes_to_the_store_data(sandbox, tmp_path):
    data, var, records, tools = sandbox
    before_data, before_var = _digest(data), _digest(var)
    for tool in tools:
        for args in SAMPLE_ARGS[tool.name]:
            tool.invoke(args)
        assert _digest(data) == before_data, tool.name
        assert _digest(var) == before_var, tool.name
        if tool.name not in WRITERS:
            assert not records.exists() or not any(records.iterdir()), tool.name
    # Fora de data/, var/ e registros/ nada foi criado.
    assert {p.name for p in tmp_path.iterdir()} <= {"data", "var", "registros"}


def test_answer_without_tool_call_is_recorded_as_source_none(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Posso ajudar com instrumentos!")])
    graph = build_graph(model, tools=[], clock=clock(2026, 11, 3, 10, 0))
    result = graph.invoke(
        {"messages": [("user", "qual a capital da França?")]}, {"configurable": {"thread_id": "x"}}
    )
    assert called_tools(result["messages"]) == ["none"]


def test_called_tools_lists_the_tools_of_the_turn(clock, var_dir):
    model = ScriptedChatModel(
        responses=[tool_call("get_policy", {"topic": "frete"}), AIMessage(content="Pronto.")]
    )
    graph = build_graph(model, clock=clock(2026, 11, 3, 10, 0))
    result = graph.invoke(
        {"messages": [("user", "como funciona o frete?")]}, {"configurable": {"thread_id": "y"}}
    )
    assert called_tools(result["messages"]) == ["get_policy"]
