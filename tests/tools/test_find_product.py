"""Ferramenta `find_product` (FR-005, FR-006, FR-007, FR-009, FR-010; S-06 a S-09)."""

import pytest

from emporio.tools.catalog import find_product_details, find_product_text


@pytest.fixture
def details(var_dir):
    return lambda name: find_product_details(name, var_dir)


@pytest.fixture
def text(var_dir):
    return lambda name: find_product_text(name, var_dir)


@pytest.mark.parametrize(
    "query", ["takamine gd 20", "Takamine GD20", "takamine gd-20", "takamine gd20 dreadnought"]
)
def test_typo_and_spacing_tolerant_name_search_finds_the_95(details, query):
    result = details(query)
    assert result.candidates
    assert result.candidates[0].product_id == 95


def test_accent_is_ignored(details):
    assert details("yamaha f310 aco").candidates[0].product_id == 87  # "Aço" no cadastro


def test_product_95_prices_installments_and_ended_promotion(text):
    output = text("takamine gd 20")
    assert "Takamine GD20 Dreadnought Natural" in output
    assert "R$ 2.199,00" in output
    assert "R$ 2.089,05" in output
    assert "12x de R$ 183,25" in output
    assert "Oferta Especial" in output  # FR-010: promoção encerrada
    assert "encerrada" in output.lower()


def test_installment_options_go_from_one_to_the_maximum(details):
    product = details("takamine gd 20").candidates[0]
    assert [option.count for option in product.installments] == list(range(1, 13))


def test_product_90_shows_original_price_percent_and_promotional_price(text, details):
    output = text("Crafter HT-100")
    assert "R$ 2.399,00" in output
    assert "18%" in output
    assert "R$ 1.967,18" in output
    assert "não se soma" in output
    product = details("Crafter HT-100").candidates[0]
    assert product.pix_price == product.final_price  # FR-006


REASONS = {
    96: ("out_of_stock", "temporariamente indisponível"),
    136: ("discontinued", "não faz mais parte do catálogo"),
    130: ("coming_soon", "ainda não está à venda"),
}


@pytest.mark.parametrize(
    ("query", "pid"),
    [("Giannini GF-3D", 96), ("Ibanez Bass 2X", 136), ("Kala KA-ABP-CTG", 130)],
)
def test_unavailable_products_have_own_reason_and_three_available_alternatives(
    details, text, query, pid
):
    product = details(query).candidates[0]
    assert product.product_id == pid
    assert product.availability == REASONS[pid][0]
    assert REASONS[pid][1] in text(query)

    assert len(product.alternatives) == 3
    for alternative in product.alternatives:
        assert alternative.availability == "available"
        assert alternative.category == product.category
        assert alternative.product_id != pid


def test_alternatives_are_the_closest_in_price(details):
    product = details("Kala KA-ABP-CTG").candidates[0]  # R$ 1.749,00, ukuleles
    assert {a.product_id for a in product.alternatives} == {129, 126, 125}


def test_unavailable_products_do_not_show_their_prices(text):
    # N-04: não confirmar preço nem disponibilidade de quem não está à venda.
    output = text("Kala KA-ABP-CTG")
    main_block = output.split("Alternativas")[0]
    assert "R$ 1.749,00" not in main_block
    assert "Preço de tabela" not in main_block


def test_discontinued_with_stock_is_not_available(details):
    product = details("Ibanez Bass 2X").candidates[0]
    assert product.stock == 13
    assert product.availability == "discontinued"  # S-07


def test_unknown_name_returns_empty_without_inventing(details, text):
    assert details("xilofone quântico").candidates == []
    assert "Nenhum produto" in text("xilofone quântico")


def test_at_most_three_candidates_and_the_total_is_reported(details, text):
    result = details("Yamaha")
    assert len(result.candidates) == 3
    assert result.total_matches > 3
    assert "query_catalog" in text("Yamaha")


def test_mismatched_description_is_not_repeated(text):
    # S-09: a descrição do 135 cita o Fender Jazz Bass.
    output = text("Music Man Bass 1X")
    assert "Jazz Bass" not in output
