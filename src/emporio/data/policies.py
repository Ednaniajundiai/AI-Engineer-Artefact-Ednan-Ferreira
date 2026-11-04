"""Manual de políticas: extração do PDF por seção e por tópico (plan D-02 e S2-04).

O PDF é lido com o `pypdf` no modo de layout, que preserva as linhas. O texto é
recortado pelos títulos numerados (`N.` e `N.N`) que começam na margem; os
itens numerados da seção 7.2 são recuados e, por isso, não viram título. O
cabeçalho e o rodapé de cada página são descartados.

Cada tópico do agente junta algumas seções e traz as notas de interpretação
adotadas na spec para os pontos em que o manual é contraditório ou omisso.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class Section:
    number: str
    title: str
    text: str


@dataclass(frozen=True)
class Note:
    id: str
    text: str


@dataclass(frozen=True)
class PolicyTopic:
    topic: str
    sections: tuple[Section, ...]
    notes: tuple[Note, ...]

    @property
    def text(self) -> str:
        parts = [f"## {s.number} {s.title}\n{s.text}".rstrip() for s in self.sections]
        return "\n\n".join(parts)


class UnknownTopicError(ValueError):
    """Tópico fora da lista do plan."""


# Seções do manual que compõem cada tópico.
TOPIC_SECTIONS: dict[str, tuple[str, ...]] = {
    "sobre_loja": ("1", "1.1", "1.2", "2"),
    "pagamento": ("3", "3.1"),
    "parcelamento": ("3.1",),
    "trocas_devolucoes": ("4", "4.1", "4.2", "4.3", "4.4"),
    "frete": ("5", "5.1", "5.2", "5.3"),
    "promocoes": ("6", "6.1", "6.2"),
    "garantia": ("8", "8.1", "8.2", "8.3"),
    "privacidade": ("9",),
    "atendimento": ("7", "7.1", "7.2", "7.3"),
}
TOPICS: tuple[str, ...] = tuple(TOPIC_SECTIONS)

_NOTE_S01 = Note(
    "S-01",
    "O manual traz dois números. Telefone da loja: (67) 3341-4444. WhatsApp de "
    "atendimento: (67) 3321-4500 (a seção 7, específica do canal, prevalece sobre a "
    "linha 'Telefone / WhatsApp' da seção 1.2). Informe sempre os dois, com o rótulo.",
)
_NOTE_S02 = Note(
    "S-02",
    "E-mail da loja: contato@emporiodamusica.com.br, sem acento (forma válida de "
    "domínio, a mesma da capa do manual).",
)
_NOTE_S03 = Note(
    "S-03",
    "A tabela de pagamento cita 'parcela mínima de R$ 100,00', mas valem as faixas da "
    "seção 3.1: até 3x com parcela mínima de R$ 50,00; de 4x a 6x com parcela mínima "
    "de R$ 80,00; de 7x a 12x com parcela mínima de R$ 100,00. O número de parcelas e "
    "o valor de cada uma vêm calculados pelas ferramentas de catálogo; não faça a conta.",
)
_NOTE_S13 = Note(
    "S-13",
    "As promoções não têm datas no cadastro: promoção ativa é a vigente hoje; promoção "
    "inativa está encerrada e não vale mais.",
)
_NOTE_S14_RETURNS = Note(
    "S-14",
    "O direito de arrependimento vale só para compra online: pergunte o canal da "
    "compra. Os pedidos não registram a data real de entrega, então a previsão de "
    "entrega é usada como data de recebimento, avisando o cliente que é uma "
    "estimativa. A troca por defeito conta 30 dias a partir da data do pedido (4.2).",
)
_NOTE_S14_WARRANTY = Note(
    "S-14",
    "A garantia legal de 90 dias conta a partir do recebimento (8.1). Como os pedidos "
    "não registram a data real de entrega, a previsão de entrega é usada como data de "
    "recebimento, avisando o cliente que é uma estimativa.",
)
_NOTE_S15 = Note(
    "S-15",
    "O manual não traz o calendário de feriados: diga que a loja fecha nos feriados, "
    "mas não afirme se uma data específica é feriado. 'Aberta agora' considera só o "
    "dia da semana e a hora.",
)
_NOTE_S16 = Note(
    "S-16",
    "O manual sugere indicar lojas parceiras para acessórios, mas não lista nenhuma. "
    "Não indique lojas parceiras: explique que a loja trabalha só com instrumentos "
    "musicais e ofereça ajuda com instrumentos.",
)

TOPIC_NOTES: dict[str, tuple[Note, ...]] = {
    "sobre_loja": (_NOTE_S01, _NOTE_S02, _NOTE_S15),
    "pagamento": (_NOTE_S03,),
    "parcelamento": (_NOTE_S03,),
    "trocas_devolucoes": (_NOTE_S14_RETURNS,),
    "frete": (),
    "promocoes": (_NOTE_S13,),
    "garantia": (_NOTE_S14_WARRANTY,),
    "privacidade": (),
    "atendimento": (_NOTE_S01, _NOTE_S16),
}

# Correções de texto aplicadas na extração, cada uma ligada a uma suposição.
TEXT_FIXES: tuple[tuple[str, str], ...] = (
    # S-02: o e-mail da seção 1.2 tem acento; a forma válida é a da capa.
    ("contato@empóriodamusica.com.br", "contato@emporiodamusica.com.br"),
    # S-01: a linha "Telefone / WhatsApp" da 1.2 contradiz a seção 7.
    (
        "Telefone / WhatsApp | (67) 3341-4444",
        "Telefone da loja | (67) 3341-4444 (WhatsApp de atendimento: (67) 3321-4500)",
    ),
)

_PAGE_HEADER = "Empório da Música Manual de Políticas e Procedimentos"
_FOOTER = re.compile(r"^Página \d+$")
_TRAILER = ("Empório da Música — Sua música começa aqui.", "Última atualização:")
_TOP_TITLE = re.compile(r"^(\d{1,2})\.\s+([A-ZÀ-Ú].*)$")
_SUB_TITLE = re.compile(r"^(\d{1,2}\.\d{1,2})\s+([A-ZÀ-Ú].*)$")
_LIST_ITEM = re.compile(r"^(•|\d+\.\s)")
_LABEL = re.compile(r"^[A-ZÀ-Ú][\wÀ-ú ]{2,40}:\s")
_COLUMN_GAP = re.compile(r"\s{3,}")


def find_policy_pdf(data_dir: Path) -> Path:
    """Localiza o PDF do manual em `data/`, qualquer que seja a forma Unicode do nome."""
    for path in sorted(data_dir.glob("*.pdf")):
        name = unicodedata.normalize("NFC", path.name).lower()
        if "polít" in name or "polit" in name:
            return path
    raise FileNotFoundError(f"manual de políticas não encontrado em {data_dir}")


def _page_lines(reader: PdfReader) -> list[str]:
    """Linhas do corpo do manual, sem capa, cabeçalho e rodapé."""
    lines: list[str] = []
    for page in reader.pages[1:]:  # a página 1 é a capa
        for raw in page.extract_text(extraction_mode="layout").splitlines():
            stripped = raw.strip()
            if stripped == _PAGE_HEADER or _FOOTER.match(stripped):
                continue
            if stripped.startswith(_TRAILER):
                continue
            lines.append(raw.rstrip())
    return lines


def _join_lines(lines: list[str]) -> str:
    """Junta as linhas quebradas pelo layout em parágrafos, itens e linhas de tabela."""
    blocks: list[str] = []
    previous_blank = True
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            previous_blank = True
            continue
        indent = len(raw) - len(raw.lstrip())
        is_table_row = indent <= 2 and indent > 0 and _COLUMN_GAP.search(stripped) is not None
        starts_block = (
            previous_blank
            or not blocks
            or is_table_row
            or _LIST_ITEM.match(stripped) is not None
            or (indent == 0 and _LABEL.match(stripped) is not None)
        )
        cell = re.sub(r"^(•|\d+\.)\s+", r"\1 ", stripped)
        cell = _COLUMN_GAP.sub(" | ", cell)
        if starts_block:
            blocks.append(cell)
        else:
            blocks[-1] = f"{blocks[-1]} {cell}"
        previous_blank = False
    text = "\n".join(blocks)
    for wrong, right in TEXT_FIXES:
        text = text.replace(wrong, right)
    return text


@lru_cache(maxsize=4)
def load_sections(pdf_path: Path) -> dict[str, Section]:
    """Seções do manual, indexadas pelo número ("4.1")."""
    reader = PdfReader(pdf_path)
    sections: dict[str, Section] = {}
    current: tuple[str, str] | None = None
    body: list[str] = []

    def close() -> None:
        if current is not None:
            sections[current[0]] = Section(current[0], current[1], _join_lines(body))

    for line in _page_lines(reader):
        match = None
        if line and not line[0].isspace():
            match = _SUB_TITLE.match(line) or _TOP_TITLE.match(line)
        if match:
            close()
            current = (match.group(1), match.group(2).strip())
            body = []
        elif current is not None:
            body.append(line)
    close()
    return sections


def policy_topic(topic: str, pdf_path: Path) -> PolicyTopic:
    """Seções e notas de interpretação de um tópico do plan."""
    if topic not in TOPIC_SECTIONS:
        valid = ", ".join(TOPICS)
        raise UnknownTopicError(f"Tópico '{topic}' não existe. Tópicos válidos: {valid}.")
    sections = load_sections(pdf_path)
    chosen = tuple(sections[number] for number in TOPIC_SECTIONS[topic] if number in sections)
    return PolicyTopic(topic=topic, sections=chosen, notes=TOPIC_NOTES[topic])
