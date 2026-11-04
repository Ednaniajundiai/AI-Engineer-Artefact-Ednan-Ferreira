"""Prompt e grafo da história 5 (FR-020, FR-021)."""

import json
from datetime import datetime

import pytest
from emporio.tools.complaints import COMPLAINTS_FILE, build_complaint_tool
from langchain_core.messages import AIMessage, ToolMessage
from tests.fakes import ScriptedChatModel, tool_call

from emporio.agent.graph import build_graph, get_tools
from emporio.agent.prompt import build_system_prompt
from emporio.config import TIMEZONE


@pytest.fixture(scope="module")
def prompt():
    return build_system_prompt(datetime(2026, 11, 3, 10, 30, tzinfo=TIMEZONE))


def test_registry_has_the_complaint_tool():
    assert "register_complaint" in {tool.name for tool in get_tools()}


def test_prompt_asks_for_empathy_and_only_the_missing_data(prompt):
    assert "register_complaint" in prompt
    assert "empatia" in prompt
    assert "só o que faltar" in prompt
    for field in ("nome", "contato (telefone ou e-mail)", "descrição", "número do pedido"):
        assert field in prompt


def test_prompt_gives_protocol_deadline_and_return_time(prompt):
    assert "protocolo" in prompt
    assert "24 horas úteis" in prompt
    assert "quando a equipe volta a atender" in prompt


def test_registered_complaint_returns_the_protocol(tmp_path, clock):
    fixed = clock(2026, 11, 3, 10, 0)
    model = ScriptedChatModel(
        responses=[
            tool_call(
                "register_complaint",
                {"name": "Ana", "contact": "ana@exemplo.com", "description": "Atraso."},
            ),
            AIMessage(content="Registrei sua reclamação."),
        ]
    )
    tool = build_complaint_tool(records_dir=tmp_path, clock=fixed)
    graph = build_graph(model, tools=[tool], clock=fixed)
    result = graph.invoke(
        {"messages": [("user", "quero reclamar")]}, {"configurable": {"thread_id": "r"}}
    )
    output = next(m for m in result["messages"] if isinstance(m, ToolMessage)).content
    record = json.loads((tmp_path / COMPLAINTS_FILE).read_text(encoding="utf-8"))
    assert record["protocol"] in output
    assert "24 horas úteis" in output
