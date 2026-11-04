"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A suíte obrigatória não usa a chave da API."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
