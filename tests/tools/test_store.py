"""Ferramenta `get_store_info` (FR-002, FR-003, FR-021; S-01, S-02, S-15)."""

import pytest

from emporio.tools.store import build_store_tool


@pytest.fixture
def info(clock):
    def run(*moment):
        return build_store_tool(clock(*moment)).invoke({})

    return run


def test_phone_and_whatsapp_are_labeled(info):
    text = info(2025, 11, 3, 10, 0)
    assert "(67) 3341-4444" in text
    assert "(67) 3321-4500" in text
    assert "WhatsApp" in text
    assert "Telefone" in text


def test_email_has_no_accent(info):
    text = info(2025, 11, 3, 10, 0)
    assert "contato@emporiodamusica.com.br" in text
    assert "empórioda" not in text


def test_address_is_informed(info):
    assert "Rua 14 de Maio, 3200" in info(2025, 11, 3, 10, 0)


def test_open_now_on_a_weekday_morning(info):
    text = info(2025, 11, 3, 10, 0)
    assert "ABERTA" in text
    assert "18:00" in text


def test_closed_now_reports_the_next_opening(info):
    text = info(2025, 11, 7, 19, 0)  # sexta à noite
    assert "FECHADA" in text
    assert "amanhã (sábado), às 09:00" in text


def test_sunday_is_closed_and_next_opening_is_monday(info):
    text = info(2025, 11, 9, 11, 0)
    assert "FECHADA" in text
    assert "segunda-feira" in text


def test_hours_from_the_manual_are_listed(info):
    text = info(2025, 11, 3, 10, 0)
    assert "09:00 às 18:00" in text
    assert "09:00 às 13:00" in text


def test_holidays_warning_without_affirming_dates(info):
    text = info(2025, 11, 3, 10, 0)
    assert "feriados" in text
    assert "não consigo confirmar" in text  # S-15: não afirma se uma data é feriado


def test_special_dates_note(info):
    text = info(2025, 11, 3, 10, 0)
    assert "redes sociais" in text
    assert "WhatsApp" in text
