"""Nome normalizado e marca do produto (plan S2-06 e S2-07)."""

from __future__ import annotations

import re
import unicodedata

# Lista fechada das marcas presentes nos dados da loja. A marca não é uma
# coluna do cadastro: é derivada do nome na carga (S2-07).
BRANDS = (
    "Music Man",
    "Yamaha",
    "Tagima",
    "Giannini",
    "Rozini",
    "Shelby",
    "Crafter",
    "Martin",
    "Taylor",
    "Takamine",
    "Kalani",
    "Kala",
    "Ohana",
    "Fender",
    "Gibson",
    "Ibanez",
    "PRS",
    "Pearl",
    "Korg",
    "Nord",
    "Roland",
)

_BRAND_PATTERNS = [
    (brand, re.compile(rf"\b{re.escape(brand)}\b", re.IGNORECASE)) for brand in BRANDS
]


def normalize_name(text: str) -> str:
    """Minúsculas, sem acento, sem espaços nem hífens ("Takamine GD-20" -> "takaminegd20")."""
    decomposed = unicodedata.normalize("NFD", text)
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[\s\-]+", "", without_accents.lower())


def derive_brand(name: str) -> str | None:
    """Primeira marca da lista fechada que aparece no nome, ou `None`."""
    for brand, pattern in _BRAND_PATTERNS:
        if pattern.search(name):
            return brand
    return None
