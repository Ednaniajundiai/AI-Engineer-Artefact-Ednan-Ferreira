"""Prompt de sistema, montado a cada chamada do nó do modelo.

Blocos (plan, "Prompt de sistema"):
1. persona e tom (manual 7.1) e fluxo de atendimento (manual 7.2);
2. data, hora e dia da semana atuais em Campo Grande;
3. regras invioláveis;
4. guia de quando usar cada ferramenta;
5. escopo.
"""

from __future__ import annotations

from datetime import datetime

WEEKDAYS = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

PERSONA_BLOCK = """\
Você é a assistente virtual da Empório da Música, uma loja de instrumentos \
musicais em Campo Grande/MS. Atenda sempre em português do Brasil, num tom \
informal, mas profissional: acolhedor, como um amigo que entende de música, \
sem linguagem robotizada nem formal demais."""


def datetime_block(now: datetime) -> str:
    """Bloco 2: data, hora e dia da semana locais."""
    weekday = WEEKDAYS[now.weekday()]
    return (
        f"Agora, em Campo Grande: {weekday}, {now:%d/%m/%Y}, {now:%H:%M}. "
        "Use esta data e esta hora para qualquer pergunta sobre o momento atual."
    )


def build_system_prompt(now: datetime) -> str:
    """Monta o prompt de sistema para a data e a hora informadas."""
    return "\n\n".join([PERSONA_BLOCK, datetime_block(now)])
