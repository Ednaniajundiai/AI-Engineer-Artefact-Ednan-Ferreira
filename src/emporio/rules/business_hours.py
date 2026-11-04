"""Horário de funcionamento da loja (FR-003, FR-021; manual, seção 2).

Segunda a sexta, das 09:00 às 18:00; sábado, das 09:00 às 13:00; fechado aos
domingos e feriados. O manual não traz o calendário de feriados (S-15), então
"aberta agora" considera só o dia da semana e a hora, sempre no fuso de Campo
Grande.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta

from emporio.config import TIMEZONE

WEEKDAY_NAMES = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)

# Horário por dia da semana (0 = segunda). Domingo não abre.
OPENING_HOURS: dict[int, tuple[time, time]] = {
    0: (time(9), time(18)),
    1: (time(9), time(18)),
    2: (time(9), time(18)),
    3: (time(9), time(18)),
    4: (time(9), time(18)),
    5: (time(9), time(13)),
}


@dataclass(frozen=True)
class OpeningStatus:
    """Situação da loja num instante: aberta ou não, e o horário relevante."""

    now: datetime
    is_open: bool
    closes_at: datetime | None
    next_opening: datetime | None


def _at(day: datetime, moment: time) -> datetime:
    return day.replace(hour=moment.hour, minute=moment.minute, second=0, microsecond=0)


def opening_status(moment: datetime) -> OpeningStatus:
    """Diz se a loja está aberta e, se não estiver, quando abre de novo."""
    now = moment.astimezone(TIMEZONE)
    hours = OPENING_HOURS.get(now.weekday())
    if hours is not None:
        opens, closes = _at(now, hours[0]), _at(now, hours[1])
        if opens <= now < closes:
            return OpeningStatus(now=now, is_open=True, closes_at=closes, next_opening=None)
        if now < opens:
            return OpeningStatus(now=now, is_open=False, closes_at=None, next_opening=opens)

    day = now
    for _ in range(7):
        day = day + timedelta(days=1)
        hours = OPENING_HOURS.get(day.weekday())
        if hours is not None:
            return OpeningStatus(
                now=now, is_open=False, closes_at=None, next_opening=_at(day, hours[0])
            )
    raise RuntimeError("a tabela de horários não tem nenhum dia de funcionamento")


def describe_next_opening(now: datetime, opening: datetime) -> str:
    """Texto curto da próxima abertura: "hoje", "amanhã (sábado)" ou o dia e a data."""
    now = now.astimezone(TIMEZONE)
    opening = opening.astimezone(TIMEZONE)
    hour = f"às {opening:%H:%M}"
    days = (opening.date() - now.date()).days
    weekday = WEEKDAY_NAMES[opening.weekday()]
    if days == 0:
        return f"hoje, {hour}"
    if days == 1:
        return f"amanhã ({weekday}), {hour}"
    return f"{weekday} ({opening:%d/%m}), {hour}"
