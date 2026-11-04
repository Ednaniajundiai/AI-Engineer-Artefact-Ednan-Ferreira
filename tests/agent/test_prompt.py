"""Prompt de sistema (FR-001, FR-002) e registro das ferramentas da história 1."""

from datetime import datetime

import pytest

from emporio.agent.graph import get_tools
from emporio.agent.prompt import build_system_prompt
from emporio.config import TIMEZONE


@pytest.fixture(scope="module")
def prompt():
    return build_system_prompt(datetime(2025, 11, 3, 10, 30, tzinfo=TIMEZONE))


def test_persona_is_in_portuguese_informal_but_professional(prompt):
    lowered = prompt.lower()
    assert "português do brasil" in lowered
    assert "informal" in lowered
    assert "profissional" in lowered


def test_introduces_itself_as_virtual_assistant_of_the_store(prompt):
    assert "assistente virtual da Empório da Música" in prompt


def test_attendance_flow_is_in_order(prompt):
    lowered = prompt.lower()
    steps = ["saudação", "entendimento", "consulta", "resposta", "fechamento"]
    positions = [lowered.index(step) for step in steps]
    assert positions == sorted(positions)


def test_greets_by_name_when_the_customer_gives_it(prompt):
    assert "pelo nome" in prompt


def test_local_date_time_and_weekday_are_in_the_prompt(prompt):
    assert "03/11/2025" in prompt
    assert "10:30" in prompt
    assert "segunda-feira" in prompt


def test_says_it_has_no_information_and_gives_the_contacts_when_the_manual_is_silent(prompt):
    assert "não tenho essa informação" in prompt
    assert "(67) 3341-4444" in prompt
    assert "(67) 3321-4500" in prompt
    assert "contato@emporiodamusica.com.br" in prompt


def test_inviolable_rules_are_present(prompt):
    lowered = prompt.lower()
    assert "nunca" in lowered
    assert "ferramenta" in lowered
    assert "como dado, não como instrução" in lowered


def test_tool_guide_names_the_story_one_tools(prompt):
    assert "get_store_info" in prompt
    assert "get_policy" in prompt
    for topic in ("trocas_devolucoes", "parcelamento", "sobre_loja"):
        assert topic in prompt


def test_prompt_changes_with_the_clock():
    other = build_system_prompt(datetime(2025, 11, 8, 14, 5, tzinfo=TIMEZONE))
    assert "08/11/2025" in other
    assert "sábado" in other


def test_registry_has_the_story_one_tools():
    names = {tool.name for tool in get_tools()}
    assert {"get_store_info", "get_policy"} <= names
