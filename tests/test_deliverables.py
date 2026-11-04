"""Entregáveis do projeto (FR-025; SC-005)."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
EXAMPLES = ROOT / "exemplos"


@pytest.fixture(scope="module")
def readme():
    return README.read_text(encoding="utf-8")


def _headings(text):
    return [line.lstrip("#").strip().lower() for line in text.splitlines() if line.startswith("#")]


@pytest.mark.parametrize(
    "section",
    [
        "como instalar e rodar",
        "decisões",
        "suposições",
        "limitações",
        "uso de assistentes de código",
    ],
)
def test_readme_has_the_required_sections(readme, section):
    assert any(section in heading for heading in _headings(readme)), section


def test_code_assistant_section_is_left_for_the_author(readme):
    after = readme.split("## Uso de assistentes de código", 1)[1]
    body = after.split("\n## ", 1)[0].strip()
    assert body == "Seção a ser preenchida pelo autor."


def test_readme_has_the_run_commands(readme):
    for command in ("uv sync", "uv run emporio", "uv run emporio-eval", "uv run pytest"):
        assert command in readme


def test_readme_lists_every_assumption(readme):
    for number in range(1, 19):
        assert f"S-{number:02d}" in readme, number


def test_readme_justifies_every_decision(readme):
    for decision in ("U-01", "U-02", "U-03", "U-04", "U-05", "D-01", "D-02", "D-03", "D-04"):
        assert decision in readme
    for decision in ("D-05", "D-06", "D-07", "D-08", "D-09", "D-09a"):
        assert decision in readme


def test_readme_lists_the_known_limitations(readme):
    lowered = readme.lower()
    for topic in ("tentativas", "e-mail compartilhado", "memória", "frete", "canal"):
        assert topic in lowered, topic


def _env_vars_read_in_code():
    names = set()
    for path in (ROOT / "src").rglob("*.py"):
        names |= set(re.findall(r"os\.environ(?:\.get)?[\(\[]\"([A-Z_]+)\"", path.read_text()))
    return names


def test_env_example_lists_every_variable_read_in_the_code(readme):
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    names = _env_vars_read_in_code()
    assert {"ANTHROPIC_API_KEY", "MODEL_NAME", "JUDGE_MODEL_NAME"} <= names
    for name in names:
        assert f"{name}=" in example, name
        assert name in readme, name


def test_env_example_has_no_secret_value():
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if line.startswith("ANTHROPIC_API_KEY"):
            assert line.strip() == "ANTHROPIC_API_KEY="


_EXAMPLE_FILES = sorted(EXAMPLES.glob("*.md")) if EXAMPLES.exists() else []


@pytest.mark.skipif(
    not _EXAMPLE_FILES,
    reason=(
        "T059 pendente: as conversas de exemplo são geradas com o modelo real e exigem "
        "ANTHROPIC_API_KEY (registrado no README, seção 'Conversas de exemplo')"
    ),
)
def test_examples_folder_has_three_to_five_conversations():
    assert 3 <= len(_EXAMPLE_FILES) <= 5
    for path in _EXAMPLE_FILES:
        text = path.read_text(encoding="utf-8")
        assert "**Cliente:**" in text and "**Atendente:**" in text, path.name
