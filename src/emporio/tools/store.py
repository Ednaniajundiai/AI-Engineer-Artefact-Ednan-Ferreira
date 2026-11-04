"""Ferramenta `get_store_info`: endereço, contatos e horário (FR-002, FR-003, FR-021).

Os contatos seguem as suposições S-01 (telefone e WhatsApp com rótulo) e S-02
(e-mail sem acento). A situação "aberta agora" vem de `rules.business_hours`,
com o relógio injetado; feriados não são afirmados (S-15).
"""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool

from emporio.config import Clock, system_clock
from emporio.rules.business_hours import WEEKDAY_NAMES, describe_next_opening, opening_status

ADDRESS = "Rua 14 de Maio, 3200 — Centro, Campo Grande/MS, CEP 79202-333"
PHONE = "(67) 3341-4444"  # S-01: telefone da capa e da seção 1.2
WHATSAPP = "(67) 3321-4500"  # S-01: a seção 7, específica do canal, prevalece
EMAIL = "contato@emporiodamusica.com.br"  # S-02: sem acento, como na capa

CONTACTS = f"Telefone da loja: {PHONE}\nWhatsApp de atendimento: {WHATSAPP}\nE-mail: {EMAIL}"

HOURS = (
    "Horário de funcionamento (loja e WhatsApp):\n"
    "- Segunda a sexta-feira: 09:00 às 18:00\n"
    "- Sábado: 09:00 às 13:00\n"
    "- Domingos e feriados: fechado"
)

# S-15: o manual não traz o calendário de feriados.
HOLIDAYS = (
    "A loja fecha nos feriados, mas não consigo confirmar se uma data específica é "
    "feriado: a situação 'agora' abaixo considera só o dia da semana e a hora."
)

SPECIAL_DATES = (
    "Em datas especiais (Black Friday, Aniversário da Loja, Natal) o horário pode ser "
    "estendido; as mudanças são comunicadas com antecedência nas redes sociais e no "
    "WhatsApp."
)


def store_info_text(clock: Clock = system_clock) -> str:
    """Texto completo da ferramenta para o instante do relógio."""
    now = clock()
    status = opening_status(now)
    weekday = WEEKDAY_NAMES[status.now.weekday()]
    moment = f"{weekday}, {status.now:%d/%m/%Y}, {status.now:%H:%M}"
    if status.is_open:
        situation = (
            f"Agora ({moment}, horário de Campo Grande): a loja está ABERTA "
            f"e fecha hoje às {status.closes_at:%H:%M}."
        )
    else:
        opening = describe_next_opening(status.now, status.next_opening)
        situation = (
            f"Agora ({moment}, horário de Campo Grande): a loja está FECHADA. "
            f"A equipe volta a atender {opening}."
        )
    return "\n\n".join(
        [f"Endereço: {ADDRESS}", CONTACTS, HOURS, situation, HOLIDAYS, SPECIAL_DATES]
    )


def build_store_tool(clock: Clock = system_clock) -> BaseTool:
    """Cria a ferramenta com o relógio informado (injetável nos testes)."""

    @tool
    def get_store_info() -> str:
        """Endereço, telefone, WhatsApp, e-mail e horário da loja, e se ela está
        aberta agora (com a próxima abertura, se estiver fechada). Use para
        perguntas sobre localização, contatos, horário ou "está aberto?"."""
        return store_info_text(clock)

    return get_store_info
