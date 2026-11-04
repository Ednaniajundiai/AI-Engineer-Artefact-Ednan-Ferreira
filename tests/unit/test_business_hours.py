"""Horário de funcionamento no fuso de Campo Grande (FR-003, FR-021, FR-024).

Datas de referência: 03/11/2025 é segunda-feira, 07/11 sexta, 08/11 sábado e
09/11 domingo.
"""

from datetime import datetime

import pytest

from emporio.config import TIMEZONE
from emporio.rules.business_hours import describe_next_opening, opening_status


def at(day, hour, minute=0):
    return datetime(2025, 11, day, hour, minute, tzinfo=TIMEZONE)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (at(3, 8, 59), False),
        (at(3, 9, 0), True),
        (at(3, 17, 59), True),
        (at(3, 18, 0), False),
        (at(7, 9, 0), True),
        (at(8, 8, 59), False),
        (at(8, 9, 0), True),
        (at(8, 12, 59), True),
        (at(8, 13, 0), False),
        (at(9, 10, 0), False),
        (at(9, 12, 0), False),
    ],
)
def test_is_open(moment, expected):
    assert opening_status(moment).is_open is expected


def test_open_store_has_no_next_opening_and_reports_closing_time():
    status = opening_status(at(3, 10, 0))
    assert status.is_open
    assert status.next_opening is None
    assert status.closes_at == at(3, 18, 0)


def test_saturday_closes_at_one_pm():
    assert opening_status(at(8, 10, 0)).closes_at == at(8, 13, 0)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (at(3, 7, 30), at(3, 9, 0)),  # antes de abrir: abre hoje
        (at(3, 18, 0), at(4, 9, 0)),  # depois de fechar: amanhã
        (at(7, 19, 0), at(8, 9, 0)),  # sexta à noite: sábado de manhã
        (at(8, 13, 0), at(10, 9, 0)),  # sábado à tarde: segunda
        (at(8, 20, 0), at(10, 9, 0)),
        (at(9, 11, 0), at(10, 9, 0)),  # domingo: segunda
    ],
)
def test_next_opening(moment, expected):
    assert opening_status(moment).next_opening == expected


def test_converts_other_timezones_to_campo_grande():
    from datetime import UTC

    utc_moment = datetime(2025, 11, 3, 13, 0, tzinfo=UTC)  # 09:00 em Campo Grande (UTC-4)
    assert opening_status(utc_moment).is_open is True


@pytest.mark.parametrize(
    ("now", "opening", "text"),
    [
        (at(3, 7, 30), at(3, 9, 0), "hoje, às 09:00"),
        (at(3, 18, 30), at(4, 9, 0), "amanhã (terça-feira), às 09:00"),
        (at(7, 19, 0), at(8, 9, 0), "amanhã (sábado), às 09:00"),
        (at(9, 11, 0), at(10, 9, 0), "amanhã (segunda-feira), às 09:00"),
        (at(8, 14, 0), at(10, 9, 0), "segunda-feira (10/11), às 09:00"),
    ],
)
def test_describe_next_opening(now, opening, text):
    assert describe_next_opening(now, opening) == text
