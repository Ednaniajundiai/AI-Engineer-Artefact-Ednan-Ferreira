"""Caminhos, variáveis de ambiente e relógio injetável (plan S2-03)."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
VAR_DIR = ROOT / "var"
RECORDS_DIR = ROOT / "registros"
EVALS_DIR = ROOT / "evals"

TIMEZONE = ZoneInfo("America/Campo_Grande")

DEFAULT_MODEL = "claude-sonnet-5-5"
DEFAULT_JUDGE_MODEL = "claude-haiku-5-5"

Clock = Callable[[], datetime]


def system_clock() -> datetime:
    """Data e hora atuais em Campo Grande."""
    return datetime.now(TIMEZONE)


def load_env() -> None:
    """Lê o `.env` local, se existir, sem sobrescrever o ambiente."""
    load_dotenv(ROOT / ".env", override=False)


def model_name() -> str:
    """Modelo do agente (`MODEL_NAME`)."""
    return os.environ.get("MODEL_NAME") or DEFAULT_MODEL


def judge_model_name() -> str:
    """Modelo juiz da avaliação (`JUDGE_MODEL_NAME`)."""
    return os.environ.get("JUDGE_MODEL_NAME") or DEFAULT_JUDGE_MODEL
