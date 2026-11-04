"""Ferramenta `get_order_status`, com verificação de identidade (FR-011 a FR-016).

A ferramenta lê só `orders.sqlite`, por conexão só leitura, e só responde
quando o número do pedido e o e-mail da compra pertencem ao mesmo cliente.
Qualquer falha (pedido inexistente, e-mail que não bate, número ilegível) tem
exatamente a mesma resposta, sem dizer qual dado está errado (FR-012).

O titular verificado vê o próprio pedido com o mínimo necessário: o primeiro
nome, nunca o e-mail, o telefone, a cidade ou o nome completo (FR-013). A
ferramenta não guarda estado: toda chamada verifica de novo (FR-015).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from langchain_core.tools import BaseTool, tool

from emporio import config
from emporio.config import Clock, system_clock
from emporio.data.loader import open_orders
from emporio.money import format_brl
from emporio.rules.deadlines import AfterSaleDeadlines, Deadline, after_sale_deadlines

NOT_FOUND = (
    "not_found: não localizei nenhum pedido com esse número e esse e-mail. Peça ao "
    "cliente para conferir os dois dados; não diga qual deles pode estar errado."
)

STATUS_PT = {
    "pending": "pendente",
    "confirmed": "confirmado",
    "shipped": "enviado",
    "delivered": "entregue",
    "cancelled": "cancelado",
}

PAYMENT_PT = {
    "pix": "PIX",
    "debit": "cartão de débito",
    "boleto": "boleto bancário",
}

_NUMBER = re.compile(r"\d+")


def parse_order_id(raw: str | int | None) -> int | None:
    """Aceita "8", "#8", "nº 8", "pedido 8"; recusa texto sem número ou com dois."""
    if raw is None:
        return None
    numbers = _NUMBER.findall(str(raw))
    if len(numbers) != 1:
        return None
    return int(numbers[0])


def normalize_email(raw: str | None) -> str:
    """E-mail sem espaços e em minúsculas."""
    return "".join((raw or "").split()).lower()


def _payment(method: str | None) -> str | None:
    if not method:
        return None
    if method.startswith("credit_"):
        return f"cartão de crédito em {method.removeprefix('credit_')}"
    return PAYMENT_PT.get(method, method)


@dataclass(frozen=True)
class OrderItem:
    name: str
    quantity: int


@dataclass(frozen=True)
class VerifiedOrder:
    order_id: int
    first_name: str
    status: str
    order_date: date
    items: list[OrderItem]
    total: str
    payment: str | None
    tracking_code: str | None
    estimated_delivery: date | None
    forecast_overdue: bool
    cancel_reason: str | None
    deadlines: AfterSaleDeadlines | None


def lookup_order(
    order_id: str | int | None, email: str | None, var_dir: Path | None, today: date
) -> VerifiedOrder | None:
    """Pedido verificado, ou `None` se o par número + e-mail não bater."""
    number = parse_order_id(order_id)
    address = normalize_email(email)
    if number is None or not address:
        return None
    conn = open_orders(var_dir or config.VAR_DIR)
    try:
        # S-11: a prova é o par pedido + e-mail do titular daquele pedido.
        row = conn.execute(
            "SELECT o.*, c.name AS customer_name FROM orders AS o "
            "JOIN customers AS c ON c.customer_id = o.customer_id "
            "WHERE o.order_id = ? AND c.email_normalized = ?",
            (number, address),
        ).fetchone()
        if row is None:
            return None
        items = [
            OrderItem(
                name=r["product_name"] or f"produto {r['product_id']}", quantity=r["quantity"]
            )
            for r in conn.execute(
                "SELECT product_id, product_name, quantity FROM order_items WHERE order_id = ?",
                (number,),
            )
        ]
    finally:
        conn.close()

    ordered = date.fromisoformat(row["order_date"])
    forecast = date.fromisoformat(row["estimated_delivery"]) if row["estimated_delivery"] else None
    status = row["status"]
    return VerifiedOrder(
        order_id=number,
        first_name=row["customer_name"].split()[0],
        status=status,
        order_date=ordered,
        items=items,
        total=format_brl(row["total_brl"]),  # S-04, S-05: o total registrado, sem recálculo
        payment=_payment(row["payment_method"]),
        tracking_code=row["tracking_code"],
        estimated_delivery=forecast,
        # S-12: enviado e com a previsão já vencida.
        forecast_overdue=status == "shipped" and forecast is not None and forecast < today,
        cancel_reason=row["notes"] if status == "cancelled" else None,
        deadlines=(
            after_sale_deadlines(ordered, forecast, today=today)
            if status == "delivered" and forecast is not None
            else None
        ),
    )


def _deadline_line(label: str, deadline: Deadline, base: str) -> str:
    situation = "ainda vale" if deadline.is_open else "prazo encerrado"
    estimate = " (estimativa, pela previsão de entrega)" if deadline.estimated else ""
    return f"- {label}: até {deadline.last_day:%d/%m/%Y}, contado {base}{estimate}: {situation}"


def format_order(order: VerifiedOrder) -> str:
    lines = [
        f"Pedido {order.order_id} verificado. Titular: {order.first_name}",
        f"Status: {STATUS_PT.get(order.status, order.status)}",
        f"Data do pedido: {order.order_date:%d/%m/%Y}",
        "Itens: " + "; ".join(f"{item.quantity}x {item.name}" for item in order.items),
        f"Total registrado: {order.total}",
    ]
    if order.payment:
        lines.append(f"Pagamento: {order.payment}")
    if order.tracking_code:
        lines.append(f"Rastreio: {order.tracking_code}")
    if order.estimated_delivery and order.status in {"shipped", "delivered"}:
        lines.append(f"Previsão de entrega: {order.estimated_delivery:%d/%m/%Y}")
    if order.forecast_overdue:
        lines.append(
            "Atenção: a previsão de entrega já passou e o pedido ainda consta como enviado. "
            "Informe com transparência e ofereça registrar uma reclamação."
        )
    if order.cancel_reason:
        lines.append(f"Motivo do cancelamento: {order.cancel_reason}")
    if order.deadlines:
        d = order.deadlines
        lines.append("Prazos de pós-venda (data de referência: hoje):")
        lines.append(
            _deadline_line(
                "Arrependimento (só compra online, 7 dias corridos)",
                d.withdrawal,
                "do recebimento",
            )
        )
        lines.append(
            _deadline_line(
                "Troca por defeito (30 dias corridos)", d.defect_exchange, "da data do pedido"
            )
        )
        lines.append(_deadline_line("Garantia legal (90 dias)", d.legal_warranty, "do recebimento"))
    return "\n".join(lines)


def order_status_text(
    order_id: str | int | None, email: str | None, var_dir: Path | None, today: date
) -> str:
    """Texto da ferramenta: o pedido verificado ou a resposta única de falha."""
    order = lookup_order(order_id, email, var_dir, today)
    return NOT_FOUND if order is None else format_order(order)


def build_order_tool(var_dir: Path | None = None, clock: Clock = system_clock) -> BaseTool:
    """Cria `get_order_status` com a pasta de dados e o relógio informados."""

    @tool
    def get_order_status(order_id: str, email: str) -> str:
        """Consulta o andamento de um pedido. Exige o número do pedido e o e-mail
        usado na compra, informados pelo cliente nesta conversa; só devolve dados
        se os dois pertencerem ao mesmo cliente. Devolve status, data, itens,
        total registrado, pagamento, rastreio, previsão de entrega, motivo de
        cancelamento e os prazos de arrependimento, troca e garantia."""
        return order_status_text(order_id, email, var_dir, clock().date())

    return get_order_status
