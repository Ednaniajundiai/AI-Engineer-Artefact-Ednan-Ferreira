"""Os modelos atuais não aceitam temperatura fora do padrão da API."""

import pytest

from emporio.agent.graph import create_model
from emporio.evaluation.checks import make_judge


@pytest.fixture(autouse=True)
def _dummy_key(monkeypatch):
    # Só constrói o cliente; nenhuma chamada de rede é feita.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "chave-de-teste")


def test_agent_model_does_not_set_temperature():
    assert create_model().temperature is None


def test_judge_model_does_not_set_temperature(monkeypatch):
    captured = {}
    import langchain_anthropic

    real = langchain_anthropic.ChatAnthropic

    def spy(*args, **kwargs):
        captured["kwargs"] = kwargs
        return real(*args, **kwargs)

    monkeypatch.setattr(langchain_anthropic, "ChatAnthropic", spy)
    make_judge("claude-haiku-5-5")
    assert "temperature" not in captured["kwargs"]
