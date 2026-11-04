"""Modelo de chat simulado, roteirizado por uma lista de mensagens."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field


class ScriptedChatModel(BaseChatModel):
    """Devolve, em ordem, as `AIMessage` do roteiro e registra o que recebeu."""

    responses: list[AIMessage]
    calls: list[list[BaseMessage]] = Field(default_factory=list)
    cursor: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Any, **kwargs: Any) -> ScriptedChatModel:
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self.calls.append(list(messages))
        if self.cursor >= len(self.responses):
            raise AssertionError("o roteiro do modelo simulado acabou")
        message = self.responses[self.cursor]
        self.cursor += 1
        return ChatResult(generations=[ChatGeneration(message=message)])


def tool_call(name: str, args: dict[str, Any], call_id: str = "call-1") -> AIMessage:
    """Mensagem do modelo pedindo uma ferramenta."""
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])
