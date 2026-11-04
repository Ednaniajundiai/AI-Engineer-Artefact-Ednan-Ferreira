"""Ferramenta `register_complaint` (FR-020, FR-021; S-18)."""

import json
import re

import pytest
from emporio.tools.complaints import (
    COMPLAINTS_FILE,
    PROTOCOL_PATTERN,
    build_complaint_tool,
    register_complaint_text,
)

VALID = {
    "name": "Ana",
    "contact": "anacarol.ferreira@coldmail.com",
    "description": "Meu pedido 8 não chegou e a previsão já passou.",
    "order_id": "8",
}


@pytest.fixture
def register(tmp_path, clock):
    def run(moment=(2026, 11, 3, 10, 0), **fields):
        args = {**VALID, **fields}
        return register_complaint_text(records_dir=tmp_path, clock=clock(*moment), **args)

    return run


def _lines(folder):
    path = folder / COMPLAINTS_FILE
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_protocol_has_the_date_and_four_hex_characters(register):
    output = register()
    protocol = re.search(PROTOCOL_PATTERN, output).group(0)
    assert re.fullmatch(r"REC-20261103-[0-9A-F]{4}", protocol)


def test_one_jsonl_line_per_complaint_only_in_the_records_folder(register, tmp_path):
    register()
    register(description="Outra reclamação.")
    assert {p.name for p in tmp_path.iterdir()} == {COMPLAINTS_FILE}
    records = _lines(tmp_path)
    assert len(records) == 2
    assert records[0]["name"] == "Ana"
    assert records[0]["contact"] == "anacarol.ferreira@coldmail.com"
    assert records[0]["order_id"] == 8
    assert records[1]["description"] == "Outra reclamação."
    assert records[0]["protocol"] != records[1]["protocol"]
    assert records[0]["created_at"].startswith("2026-11-03T10:00")


def test_response_brings_the_protocol_and_the_24_business_hours(register, tmp_path):
    output = register()
    assert _lines(tmp_path)[0]["protocol"] in output
    assert "24 horas úteis" in output


@pytest.mark.parametrize(
    ("missing", "label"),
    [("name", "nome"), ("contact", "contato"), ("description", "descrição")],
)
def test_refuses_without_minimum_data_and_says_what_is_missing(register, tmp_path, missing, label):
    output = register(**{missing: "  "})
    assert label in output
    assert "REC-" not in output
    assert _lines(tmp_path) == []


def test_lists_every_missing_field(register):
    output = register(name="", contact="", description="")
    for label in ("nome", "contato", "descrição"):
        assert label in output


def test_contact_must_be_a_phone_or_an_email(register, tmp_path):
    assert "REC-" not in register(contact="na loja")
    assert "REC-" in register(contact="(67) 99654-7821")
    assert "REC-" in register(contact="ana@exemplo.com")


def test_order_number_is_optional(register, tmp_path):
    register(order_id=None)
    register(order_id="")
    assert [r["order_id"] for r in _lines(tmp_path)] == [None, None]


def test_outside_business_hours_says_when_the_team_returns(register):
    output = register(moment=(2026, 11, 7, 15, 0))  # sábado à tarde
    assert "volta a atender" in output
    assert "segunda-feira" in output


def test_during_business_hours_no_return_notice(register):
    assert "volta a atender" not in register(moment=(2026, 11, 3, 10, 0))


def test_tool_schema_has_order_id_optional(tmp_path, clock):
    tool = build_complaint_tool(records_dir=tmp_path, clock=clock(2026, 11, 3, 10, 0))
    schema = tool.args_schema.model_json_schema()
    assert set(schema["required"]) == {"name", "contact", "description"}
    assert "REC-" in tool.invoke(
        {"name": "Ana", "contact": "ana@exemplo.com", "description": "Produto com defeito."}
    )
