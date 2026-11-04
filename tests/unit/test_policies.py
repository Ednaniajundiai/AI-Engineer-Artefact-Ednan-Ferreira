"""Extração do manual em PDF por tópico (FR-002, FR-016; plan S2-04 e D-02)."""

import pytest

from emporio.data.policies import (
    TOPICS,
    UnknownTopicError,
    find_policy_pdf,
    load_sections,
    policy_topic,
)

EXPECTED_TOPICS = {
    "pagamento",
    "parcelamento",
    "trocas_devolucoes",
    "frete",
    "promocoes",
    "garantia",
    "privacidade",
    "atendimento",
    "sobre_loja",
}


@pytest.fixture(scope="module")
def pdf(request):
    from tests.conftest import DATA_DIR

    return find_policy_pdf(DATA_DIR)


def test_topics_are_the_ones_in_the_plan():
    assert set(TOPICS) == EXPECTED_TOPICS


def test_sections_are_cut_by_numbered_titles(pdf):
    sections = load_sections(pdf)
    assert {"1", "2", "3", "3.1", "4.1", "4.2", "5.1", "5.2", "6.2", "7.3", "8.1", "9"} <= set(
        sections
    )
    assert sections["4.1"].title.startswith("Direito de Arrependimento")
    assert "7 (sete) dias corridos" in sections["4.1"].text


def test_numbered_list_of_section_7_2_is_not_taken_as_a_title(pdf):
    sections = load_sections(pdf)
    assert "Saudação" in sections["7.2"].text
    assert "Fechamento" in sections["7.2"].text
    assert "8" in sections
    assert sections["8"].title.startswith("Garantia")


def test_page_headers_and_footers_are_removed(pdf):
    for section in load_sections(pdf).values():
        assert "Manual de Políticas e Procedimentos" not in section.text
        assert "Página " not in section.text


KEY_FACTS = {
    "sobre_loja": ["09:00 às 18:00", "09:00 às 13:00", "instrumentos musicais"],
    "pagamento": ["PIX", "5% de desconto", "Até 12x sem juros"],
    "parcelamento": ["R$ 50,00", "R$ 80,00", "R$ 100,00"],
    "trocas_devolucoes": ["7 (sete) dias corridos", "30 (trinta) dias corridos"],
    "frete": ["R$ 500,00", "PAC", "SEDEX", "Jadlog"],
    "promocoes": ["não são cumulativas", "percentual de desconto"],
    "garantia": ["90 (noventa) dias"],
    "privacidade": ["LGPD"],
    "atendimento": ["24 horas úteis", "3321-4500"],
}


@pytest.mark.parametrize("topic", sorted(EXPECTED_TOPICS))
def test_each_topic_has_its_key_facts(pdf, topic):
    text = policy_topic(topic, pdf).text
    for fact in KEY_FACTS[topic]:
        assert fact in text, f"{topic}: falta '{fact}'"


def test_free_shipping_threshold_is_in_the_frete_topic(pdf):
    assert "Frete grátis para pedidos acima de R$ 500,00" in policy_topic("frete", pdf).text


def test_interpretation_notes_land_in_the_right_topics(pdf):
    def note_ids(topic):
        return {note.id for note in policy_topic(topic, pdf).notes}

    assert "S-03" in note_ids("pagamento")
    assert "S-03" in note_ids("parcelamento")
    assert "S-14" in note_ids("trocas_devolucoes")
    assert "S-14" in note_ids("garantia")
    assert "S-15" in note_ids("sobre_loja")
    assert "S-16" in note_ids("atendimento")
    assert note_ids("frete") == set()
    assert "S-03" not in note_ids("garantia")


def test_unknown_topic_gives_a_clear_error(pdf):
    with pytest.raises(UnknownTopicError) as error:
        policy_topic("cambio", pdf)
    message = str(error.value)
    assert "cambio" in message
    for topic in EXPECTED_TOPICS:
        assert topic in message
