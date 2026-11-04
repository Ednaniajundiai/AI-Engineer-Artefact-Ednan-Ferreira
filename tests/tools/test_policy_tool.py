"""Ferramenta `get_policy`, sem o modelo (FR-002, FR-008, FR-016; S-01, S-02, S-03, S-14, S-16)."""

import pytest

from emporio.data.policies import TOPICS
from emporio.tools.policies import get_policy


def run(topic):
    return get_policy.func(topic)


@pytest.mark.parametrize("topic", TOPICS)
def test_every_valid_topic_returns_text(topic):
    text = run(topic)
    assert len(text) > 100
    assert topic in text


def test_topic_is_restricted_to_the_plan_values_in_the_tool_schema():
    schema = get_policy.args_schema.model_json_schema()
    assert set(schema["properties"]["topic"]["enum"]) == set(TOPICS)


def test_unknown_topic_is_refused_with_a_clear_message():
    text = run("cambio")
    assert "cambio" in text
    assert "não" in text.lower()
    for topic in TOPICS:
        assert topic in text


def test_parcelamento_returns_ranges_and_the_s03_note():
    text = run("parcelamento")
    assert "R$ 50,00" in text and "R$ 80,00" in text and "R$ 100,00" in text
    assert "S-03" in text
    assert "Notas de interpretação" in text


def test_trocas_devolucoes_has_rules_and_the_s14_note():
    text = run("trocas_devolucoes")
    assert "7 (sete) dias corridos" in text
    assert "30 (trinta) dias corridos" in text
    assert "S-14" in text
    assert "previsão de entrega" in text


def test_garantia_has_the_s14_note():
    text = run("garantia")
    assert "90 (noventa) dias" in text
    assert "S-14" in text


def test_atendimento_has_the_s16_note_about_partner_stores():
    text = run("atendimento")
    assert "S-16" in text
    assert "lojas parceiras" in text


def test_sobre_loja_has_unaccented_email_and_both_labeled_phones():
    text = run("sobre_loja")
    assert "contato@emporiodamusica.com.br" in text
    assert "empórioda" not in text
    assert "Telefone da loja: (67) 3341-4444" in text
    assert "WhatsApp de atendimento: (67) 3321-4500" in text


def test_topics_without_notes_have_no_notes_section():
    assert "Notas de interpretação" not in run("frete")
