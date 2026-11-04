"""Fixtures compartilhadas dos testes."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from emporio.config import TIMEZONE

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def data_dir() -> Path:
    """Pasta com os CSVs e o PDF originais da loja."""
    return DATA_DIR


def make_clock(year, month, day, hour=10, minute=0):
    """Relógio fixo no fuso de Campo Grande, para os testes."""
    fixed = datetime(year, month, day, hour, minute, tzinfo=TIMEZONE)
    return lambda: fixed


@pytest.fixture
def clock():
    """Fábrica de relógios fixos: `clock(2025, 11, 3, 10, 30)`."""
    return make_clock
