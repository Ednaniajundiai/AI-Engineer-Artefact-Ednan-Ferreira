"""Grafo do agente com o modelo simulado (FR-022; plan D-01 e D-06)."""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from tests.fakes import ScriptedChatModel, tool_call

from emporio.agent.graph import build_graph


@tool
def echo(text: str) -> str:
    """Repete o texto recebido."""
    return f"eco: {text}"


def _config(thread_id):
    return {"configurable": {"thread_id": thread_id}}


def _graph(model, clock):
    return build_graph(model, tools=[echo], clock=clock(2025, 11, 3, 10, 0))


def test_tool_call_is_followed_by_the_final_answer(clock):
    model = ScriptedChatModel(
        responses=[tool_call("echo", {"text": "oi"}), AIMessage(content="Pronto!")]
    )
    result = _graph(model, clock).invoke({"messages": [("user", "oi")]}, _config("a"))

    kinds = [type(message) for message in result["messages"]]
    assert kinds == [HumanMessage, AIMessage, ToolMessage, AIMessage]
    assert result["messages"][2].content == "eco: oi"
    assert result["messages"][-1].content == "Pronto!"


def test_prompt_is_built_at_each_model_call(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Olá!")])
    _graph(model, clock).invoke({"messages": [("user", "oi")]}, _config("a"))

    first_call = model.calls[0]
    assert isinstance(first_call[0], SystemMessage)
    assert "03/11/2025" in first_call[0].content


def test_second_message_in_the_same_thread_sees_the_first(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Oi!"), AIMessage(content="Claro!")])
    graph = _graph(model, clock)
    graph.invoke({"messages": [("user", "meu nome é Rita")]}, _config("a"))
    graph.invoke({"messages": [("user", "qual era meu nome?")]}, _config("a"))

    seen = [m.content for m in model.calls[1] if isinstance(m, HumanMessage)]
    assert seen == ["meu nome é Rita", "qual era meu nome?"]


def test_new_thread_starts_empty(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Oi!"), AIMessage(content="Olá!")])
    graph = _graph(model, clock)
    graph.invoke({"messages": [("user", "meu nome é Rita")]}, _config("a"))
    graph.invoke({"messages": [("user", "oi")]}, _config("b"))

    seen = [m.content for m in model.calls[1] if isinstance(m, HumanMessage)]
    assert seen == ["oi"]
