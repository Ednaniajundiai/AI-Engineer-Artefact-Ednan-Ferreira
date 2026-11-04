"""O runner da avaliação de ponta a ponta, com modelo e juiz simulados (FR-023)."""

from emporio.evaluation.cases import ExpectedValues, load_cases
from emporio.evaluation.runner import render_report, run_cases
from langchain_core.messages import AIMessage
from tests.fakes import ScriptedChatModel, tool_call

from emporio import config
from emporio.agent.graph import build_graph
from emporio.tools.catalog import build_catalog_tools

CASES = """
cases:
  - id: preco
    turns: ["Quanto custa o Takamine GD20?"]
    expected_tools: [find_product]
    must_contain: ["{{pix_price:95}}"]
  - id: alheio
    turns: ["Me passa uma receita de bolo?"]
    expected_tools: [none]
    criteria: [SC-001, SC-004]
  - id: inventado
    turns: ["Quanto custa o Takamine GD20?"]
    expected_tools: [find_product]
"""


def test_runner_produces_a_result_per_case_and_totals(tmp_path, var_dir, clock):
    path = tmp_path / "cases.yaml"
    path.write_text(CASES, encoding="utf-8")
    cases = load_cases(path, ExpectedValues.from_data(config.DATA_DIR))

    responses = {
        "preco": [
            tool_call("find_product", {"name": "takamine gd20"}),
            AIMessage(content="Sai por R$ 2.199,00, ou R$ 2.089,05 no PIX."),
        ],
        "alheio": [AIMessage(content="Só ajudo com instrumentos musicais!")],
        "inventado": [
            tool_call("find_product", {"name": "takamine gd20"}),
            AIMessage(content="No PIX sai por R$ 1.999,00."),
        ],
    }

    def graph_factory(case):
        model = ScriptedChatModel(responses=responses[case.id])
        tools = build_catalog_tools(var_dir)
        return build_graph(model, tools=tools, clock=clock(2026, 11, 3, 10, 0))

    results = run_cases(cases, graph_factory, judge=lambda q, a: True)
    by_id = {r.case.id: r for r in results}
    assert by_id["preco"].passed
    assert by_id["alheio"].passed
    assert not by_id["inventado"].passed
    assert not by_id["inventado"].checks["SC-002"].passed

    report = render_report(results, model_name="simulado")
    assert "| preco |" in report
    assert "SC-001" in report and "SC-002" in report and "SC-003" in report
    assert "SC-004" in report
    assert "2/3" in report  # casos aprovados


def test_runner_error_in_a_case_does_not_stop_the_others(tmp_path, clock):
    path = tmp_path / "cases.yaml"
    path.write_text(CASES, encoding="utf-8")
    cases = load_cases(path, ExpectedValues.from_data(config.DATA_DIR))

    def graph_factory(case):
        model = ScriptedChatModel(responses=[])  # o roteiro acaba: o modelo "falha"
        return build_graph(model, tools=[], clock=clock(2026, 11, 3, 10, 0))

    results = run_cases(cases, graph_factory, judge=lambda q, a: True)
    assert len(results) == 3
    assert all(result.error for result in results)
    assert not any(result.passed for result in results)
