"""Verificações da avaliação (FR-023; plan D-07, D-09; SC-001 a SC-004)."""

from emporio.evaluation.checks import (
    TurnRecord,
    check_anchoring,
    check_leakage,
    check_must_contain,
    check_routing,
    check_scope_with_judge,
    money_values,
)


def turn(answer, tools=("none",), outputs=(), message="oi"):
    return TurnRecord(message=message, tools=list(tools), outputs=list(outputs), answer=answer)


# --- Roteamento (SC-001) ------------------------------------------------------


def test_routing_passes_when_the_expected_tool_was_called():
    turns = [turn("ok", tools=["find_product"])]
    assert check_routing(["find_product"], turns).passed


def test_routing_accepts_extra_tools_besides_the_expected_one():
    turns = [turn("ok", tools=["find_product", "get_policy"])]
    assert check_routing(["find_product"], turns).passed


def test_routing_fails_when_the_expected_tool_is_missing():
    result = check_routing(["get_order_status"], [turn("ok", tools=["find_product"])])
    assert not result.passed
    assert "get_order_status" in result.detail


def test_routing_none_requires_no_tool_at_all():
    assert check_routing(["none"], [turn("Só instrumentos!")]).passed
    assert not check_routing(["none"], [turn("ok", tools=["get_policy"])]).passed


def test_routing_looks_at_every_turn_of_the_case():
    turns = [turn("qual o e-mail?"), turn("achei", tools=["get_order_status"])]
    assert check_routing(["get_order_status"], turns).passed


# --- Ancoragem dos valores em R$ (SC-002) ------------------------------------


def test_money_values_are_extracted():
    text = "Sai por R$ 2.199,00 ou R$2.089,05 no PIX, e 12x de R$ 183,25."
    assert money_values(text) == ["R$ 2.199,00", "R$ 2.089,05", "R$ 183,25"]


def test_anchoring_passes_when_every_value_is_in_a_tool_output_of_the_turn():
    outputs = ["Preço de tabela: R$ 2.199,00\nPreço no PIX: R$ 2.089,05"]
    turns = [turn("R$ 2.199,00, ou R$ 2.089,05 no PIX", tools=["find_product"], outputs=outputs)]
    assert check_anchoring(turns).passed


def test_anchoring_accepts_the_formatted_rows_of_query_catalog():
    outputs = ['2 linhas:\n[{"name": "Yamaha C40", "final_price": "R$ 599,90"}]']
    turns = [turn("O Yamaha C40 sai por R$ 599,90.", tools=["query_catalog"], outputs=outputs)]
    assert check_anchoring(turns).passed


def test_invented_or_recalculated_value_fails():
    outputs = ["Preço de tabela: R$ 2.199,00"]
    recalculated = [turn("No PIX fica R$ 2.089,05.", tools=["find_product"], outputs=outputs)]
    result = check_anchoring(recalculated)
    assert not result.passed
    assert "R$ 2.089,05" in result.detail


def test_value_must_come_from_the_same_turn():
    turns = [
        turn("R$ 2.199,00", tools=["find_product"], outputs=["R$ 2.199,00"]),
        turn("R$ 1.967,18", tools=["none"], outputs=[]),
    ]
    assert not check_anchoring(turns).passed


def test_answer_without_money_passes_anchoring():
    assert check_anchoring([turn("Abrimos às 9h.")]).passed


# --- Vazamento (SC-003) -------------------------------------------------------

ORDERS = {
    1: {"tracking": "BRAB1234567BR", "total": "R$ 11.499,00", "email": "pedro.oliveira@jmail.com"},
    8: {
        "tracking": "BRJL5544332BR",
        "total": "R$ 349,90",
        "email": "anacarol.ferreira@coldmail.com",
    },
}


def test_tracking_of_an_unverified_order_is_a_leak():
    turns = [
        turn("Seu rastreio é BRAB1234567BR", tools=["get_order_status"], outputs=["not_found"])
    ]
    result = check_leakage(turns, ORDERS, forbidden=[])
    assert not result.passed


def test_tracking_of_a_verified_order_is_fine():
    outputs = ["Pedido 8 verificado. Titular: Ana\nRastreio: BRJL5544332BR"]
    turns = [turn("Rastreio BRJL5544332BR", tools=["get_order_status"], outputs=outputs)]
    assert check_leakage(turns, ORDERS, forbidden=[]).passed


def test_email_or_total_of_another_order_is_a_leak():
    outputs = ["Pedido 8 verificado. Titular: Ana\nTotal registrado: R$ 349,90"]
    leaked_email = [turn("O e-mail é pedro.oliveira@jmail.com", outputs=outputs)]
    assert not check_leakage(leaked_email, ORDERS, forbidden=[]).passed
    leaked_total = [turn("O pedido 1 custou R$ 11.499,00", outputs=outputs)]
    assert not check_leakage(leaked_total, ORDERS, forbidden=[]).passed


def test_email_typed_by_the_customer_is_not_a_leak():
    turns = [turn("Obrigada!", message="meu e-mail é pedro.oliveira@jmail.com")]
    assert check_leakage(turns, ORDERS, forbidden=[]).passed


def test_forbidden_strings_of_the_case_fail():
    turns = [turn("O nome dele é Lucas")]
    assert not check_leakage(turns, ORDERS, forbidden=["Lucas"]).passed


# --- Conteúdo esperado --------------------------------------------------------


def test_must_contain_checks_the_last_answer_case_insensitively():
    turns = [turn("primeira"), turn("O PIX fica em R$ 2.089,05")]
    assert check_must_contain(["r$ 2.089,05"], turns).passed
    assert not check_must_contain(["primeira"], turns).passed


# --- Juiz de SC-004 (simulado) ------------------------------------------------


def test_judge_yes_passes_and_no_fails():
    turns = [turn("Trabalhamos só com instrumentos, posso ajudar com um violão?")]
    assert check_scope_with_judge(turns, judge=lambda question, answer: True).passed
    assert not check_scope_with_judge(turns, judge=lambda question, answer: False).passed


def test_judge_receives_the_customer_message_and_the_answer():
    seen = {}

    def judge(question, answer):
        seen.update(question=question, answer=answer)
        return True

    check_scope_with_judge([turn("Não posso ajudar com isso.", message="receita de bolo?")], judge)
    assert seen == {"question": "receita de bolo?", "answer": "Não posso ajudar com isso."}


def test_judge_rubric_is_a_yes_or_no_question():
    from emporio.evaluation.checks import JUDGE_RUBRIC, parse_judge_verdict

    assert "SIM" in JUDGE_RUBRIC and "NÃO" in JUDGE_RUBRIC
    assert parse_judge_verdict("SIM") is True
    assert parse_judge_verdict("NÃO, inventou uma receita") is False
    assert parse_judge_verdict("talvez") is False
