"""Grafo do agente: modelo -> ferramentas -> modelo (plan D-01 e D-06).

Um único agente com ferramentas, num `StateGraph` explícito. O prompt de
sistema é montado a cada chamada do modelo, com a data e a hora locais. O
histórico fica no checkpointer em memória, um thread por atendimento.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from emporio.agent.prompt import build_system_prompt
from emporio.config import Clock, model_name, system_clock
from emporio.tools.catalog import build_catalog_tools
from emporio.tools.complaints import build_complaint_tool
from emporio.tools.orders import build_order_tool
from emporio.tools.policies import get_policy
from emporio.tools.store import build_store_tool


def get_tools(clock: Clock = system_clock) -> list[BaseTool]:
    """Registro das ferramentas do agente."""
    return [
        build_store_tool(clock),
        get_policy,
        *build_catalog_tools(),
        build_order_tool(clock=clock),
        build_complaint_tool(clock=clock),
    ]


def called_tools(messages: Sequence[BaseMessage]) -> list[str]:
    """Ferramentas chamadas no último turno, ou `["none"]` se nenhuma (FR-023)."""
    start = max(
        (i for i, message in enumerate(messages) if isinstance(message, HumanMessage)),
        default=0,
    )
    names = [
        call["name"]
        for message in messages[start:]
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]
    return names or ["none"]


def create_model() -> BaseChatModel:
    """Modelo real da Anthropic, com os parâmetros padrão da API (plan D-05)."""
    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model=model_name())


def build_graph(
    model: BaseChatModel,
    tools: Sequence[BaseTool] | None = None,
    clock: Clock = system_clock,
    checkpointer: Any | None = None,
):
    """Compila o grafo. O modelo, as ferramentas e o relógio são injetáveis."""
    registered = list(get_tools(clock) if tools is None else tools)
    bound = model.bind_tools(registered) if registered else model

    def call_model(state: MessagesState) -> dict[str, list]:
        system = SystemMessage(build_system_prompt(clock()))
        return {"messages": [bound.invoke([system, *state["messages"]])]}

    builder = StateGraph(MessagesState)
    builder.add_node("model", call_model)
    builder.add_node("tools", ToolNode(registered))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition)
    builder.add_edge("tools", "model")
    return builder.compile(checkpointer=checkpointer or InMemorySaver())
