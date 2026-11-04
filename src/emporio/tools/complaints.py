"""Ferramenta `register_complaint` (FR-020, FR-021; S-18; princípio IV).

Única escrita do agente: uma linha JSONL por reclamação em
`registros/reclamacoes.jsonl`, separado dos dados da loja e fora do git. O
protocolo é `REC-AAAAMMDD-XXXX` (data local e 4 caracteres hexadecimais
aleatórios). O registro fica disponível para a equipe consultar; não há envio
nem notificação neste ciclo (S-18).
"""

from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from emporio import config
from emporio.config import Clock, system_clock
from emporio.rules.business_hours import describe_next_opening, opening_status
from emporio.tools.orders import parse_order_id

COMPLAINTS_FILE = "reclamacoes.jsonl"
PROTOCOL_PATTERN = r"REC-\d{8}-[0-9A-F]{4}"
RETURN_DEADLINE = "24 horas úteis"

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_contact(value: str) -> bool:
    """Telefone (8 ou mais dígitos) ou e-mail."""
    return bool(_EMAIL.match(value)) or len(re.sub(r"\D", "", value)) >= 8


def _new_protocol(clock: Clock) -> str:
    return f"REC-{clock():%Y%m%d}-{secrets.token_hex(2).upper()}"


def register_complaint_text(
    name: str | None,
    contact: str | None,
    description: str | None,
    order_id: str | None = None,
    *,
    records_dir: Path | None = None,
    clock: Clock = system_clock,
) -> str:
    """Valida, grava a reclamação e devolve o texto para o modelo."""
    name, contact, description = (
        (name or "").strip(),
        (contact or "").strip(),
        (description or "").strip(),
    )
    missing = [
        label
        for label, value in (("nome", name), ("contato", contact), ("descrição", description))
        if not value
    ]
    if missing:
        return (
            "Reclamação NÃO registrada: falta " + ", ".join(missing) + ". Peça ao cliente só "
            "o que falta (o contato pode ser telefone ou e-mail)."
        )
    if not _is_contact(contact):
        return (
            "Reclamação NÃO registrada: o contato precisa ser um telefone ou um e-mail. "
            "Peça ao cliente um contato válido."
        )

    now = clock()
    protocol = _new_protocol(clock)
    record = {
        "protocol": protocol,
        "created_at": now.isoformat(timespec="seconds"),
        "name": name,
        "contact": contact,
        "description": description,
        "order_id": parse_order_id(order_id) if order_id else None,
    }
    folder = records_dir or config.RECORDS_DIR
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / COMPLAINTS_FILE).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    lines = [
        f"Reclamação registrada. Protocolo: {protocol}.",
        f"Prazo de retorno da equipe: {RETURN_DEADLINE}.",
    ]
    status = opening_status(now)
    if not status.is_open:
        lines.append(
            "A loja está fechada agora; a equipe volta a atender "
            f"{describe_next_opening(status.now, status.next_opening)}."
        )
    return "\n".join(lines)


def build_complaint_tool(records_dir: Path | None = None, clock: Clock = system_clock) -> BaseTool:
    """Cria `register_complaint` com a pasta de registros e o relógio informados."""

    @tool
    def register_complaint(
        name: str, contact: str, description: str, order_id: str | None = None
    ) -> str:
        """Registra a reclamação de um cliente para a equipe e devolve o número de
        protocolo e o prazo de retorno. Exige o nome, um contato (telefone ou
        e-mail) e a descrição do problema; o número do pedido é opcional. Só
        chame depois de o cliente informar esses dados."""
        return register_complaint_text(
            name, contact, description, order_id, records_dir=records_dir, clock=clock
        )

    return register_complaint
