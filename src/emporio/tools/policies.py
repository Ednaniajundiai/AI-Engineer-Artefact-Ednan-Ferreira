"""Ferramenta `get_policy`: seções do manual por tópico (FR-002, FR-008, FR-016; plan D-02).

Devolve o texto das seções do manual que compõem o tópico e as notas de
interpretação adotadas na spec (S-01, S-02, S-03, S-13, S-14, S-15, S-16).
"""

from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool

from emporio import config
from emporio.data.policies import UnknownTopicError, find_policy_pdf, policy_topic

PolicyTopicName = Literal[
    "pagamento",
    "parcelamento",
    "trocas_devolucoes",
    "frete",
    "promocoes",
    "garantia",
    "privacidade",
    "atendimento",
    "sobre_loja",
]


def policy_text(topic: str) -> str:
    """Texto do tópico com as notas, ou a recusa para um tópico desconhecido."""
    try:
        found = policy_topic(topic, find_policy_pdf(config.DATA_DIR))
    except UnknownTopicError as error:
        return f"Não encontrei esse tópico. {error}"
    parts = [f"Tópico: {found.topic} (manual de políticas da loja)", found.text]
    if found.notes:
        notes = "\n".join(f"- [{note.id}] {note.text}" for note in found.notes)
        parts.append(f"Notas de interpretação adotadas pela loja:\n{notes}")
    return "\n\n".join(parts)


@tool
def get_policy(topic: PolicyTopicName) -> str:
    """Consulta o manual de políticas da loja por tópico: pagamento (formas de
    pagamento, PIX, combinação de formas), parcelamento (faixas de parcela
    mínima), trocas_devolucoes (arrependimento, defeito, preferência), frete
    (entregas, modalidades, prazos, rastreio), promocoes (regras de promoção),
    garantia, privacidade (LGPD), atendimento (diretrizes, escopo, reclamações)
    e sobre_loja (a loja, dados da empresa e horário)."""
    return policy_text(topic)
