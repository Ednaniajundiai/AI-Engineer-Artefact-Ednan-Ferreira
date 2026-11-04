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


@pytest.fixture(scope="session")
def var_dir(tmp_path_factory) -> Path:
    """Os dois SQLite gerados uma vez por sessão, numa pasta temporária."""
    from emporio.data.loader import build_databases

    target = tmp_path_factory.mktemp("var")
    build_databases(DATA_DIR, target)
    return target
