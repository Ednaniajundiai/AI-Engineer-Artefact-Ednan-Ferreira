"""Normalização de nomes e marca dos produtos (plan S2-06 e S2-07; base de FR-005)."""

import csv

import pytest

from emporio.data.normalize import BRANDS, derive_brand, normalize_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Takamine GD20 Dreadnought Natural", "takaminegd20dreadnoughtnatural"),
        ("takamine gd 20", "takaminegd20"),
        ("Takamine GD-20", "takaminegd20"),
        ("  Violão   Elétrico ", "violaoeletrico"),
        ("Baixo Barítono", "baixobaritono"),
    ],
)
def test_normalize_removes_accents_case_spaces_and_hyphens(raw, expected):
    assert normalize_name(raw) == expected


def test_typed_name_is_substring_of_catalog_name():
    assert normalize_name("takamine gd 20") in normalize_name("Takamine GD20 Dreadnought Natural")


@pytest.mark.parametrize(
    ("name", "brand"),
    [
        ("Yamaha C40 Nylon Natural", "Yamaha"),
        ("Music Man Bass 1X Electric Bass", "Music Man"),
        ("Bateria Acústica Pearl Kit 2 Studio", "Pearl"),
        ("Teclado Sintetizador Korg Synth 1 Pro", "Korg"),
        ("Kala KA-15S Soprano Mogno", "Kala"),
        ("Kalani KAL-300S Soprano Natural", "Kalani"),
        ("PRS SE Custom 24", "PRS"),
    ],
)
def test_derive_brand(name, brand):
    assert derive_brand(name) == brand


def test_every_product_gets_a_brand_from_the_closed_list(data_dir):
    path = data_dir / "desafio_tecnico_ai_eng - products.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        names = [row["name"] for row in csv.DictReader(handle)]
    assert names
    for name in names:
        assert derive_brand(name) in BRANDS, name
