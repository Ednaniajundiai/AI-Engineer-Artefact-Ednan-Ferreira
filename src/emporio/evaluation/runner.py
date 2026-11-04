"""Comando `emporio-eval`: roda o conjunto fixo contra o agente (FR-023; plan D-07).

Cada caso roda num thread novo. Para cada mensagem do cliente o runner junta
as ferramentas chamadas, as saídas delas e a resposta final, aplica as
verificações de `checks` e grava um relatório em markdown, com o resultado por
caso e os totais de SC-001 a SC-004, em `evals/reports/AAAA-MM-DD.md`.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from emporio import config
from emporio.evaluation.cases import EvalCase, ExpectedValues, load_cases
from emporio.evaluation.checks import (
    CheckResult,
    Judge,
    TurnRecord,
    check_anchoring,
    check_leakage,
    check_must_contain,
    check_routing,
    check_scope_with_judge,
)

GOALS = {
    "SC-001": ("fonte de consulta esperada", 0.90),
    "SC-002": ("valores em R$ ancorados nas ferramentas", 1.0),
    "SC-003": ("nenhum vazamento de dado de pedido ou cliente", 1.0),
    "SC-004": ("fora do escopo recusado ou redirecionado (juiz)", 1.0),
}
CONTENT = "conteúdo"


@dataclass
class CaseResult:
    case: EvalCase
    turns: list[TurnRecord] = field(default_factory=list)
    checks: dict[str, CheckResult] = field(default_factory=dict)
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and all(check.passed for check in self.checks.values())


def _text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return "".join(block.get("text", "") for block in content if isinstance(block, dict))


def _turn_record(message: str, new_messages: Sequence[BaseMessage]) -> TurnRecord:
    tools = [
        call["name"] for m in new_messages if isinstance(m, AIMessage) for call in m.tool_calls
    ]
    outputs = [_text(m) for m in new_messages if isinstance(m, ToolMessage)]
    answer = _text(new_messages[-1]) if new_messages else ""
    return TurnRecord(message=message, tools=tools or ["none"], outputs=outputs, answer=answer)


def run_case(case: EvalCase, graph, judge: Judge, values: ExpectedValues | None) -> CaseResult:
    result = CaseResult(case=case)
    settings = {"configurable": {"thread_id": f"eval-{case.id}-{uuid.uuid4().hex[:8]}"}}
    seen = 0
    try:
        for message in case.turns:
            state = graph.invoke({"messages": [HumanMessage(message)]}, settings)
            messages = state["messages"]
            start = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
            start = max(start, seen)
            result.turns.append(_turn_record(message, messages[start + 1 :]))
            seen = len(messages)
    except Exception as error:  # noqa: BLE001 - um caso com erro não para a avaliação
        result.error = f"{type(error).__name__}: {error}"
        return result

    orders = values.orders if values else {}
    personal = values.personal if values else []
    if "SC-001" in case.criteria:
        result.checks["SC-001"] = check_routing(case.expected_tools, result.turns)
    if "SC-002" in case.criteria:
        result.checks["SC-002"] = check_anchoring(result.turns)
    if "SC-003" in case.criteria:
        result.checks["SC-003"] = check_leakage(
            result.turns, orders, case.must_not_contain, personal
        )
    if "SC-004" in case.criteria:
        result.checks["SC-004"] = check_scope_with_judge(result.turns, judge)
    if case.must_contain:
        result.checks[CONTENT] = check_must_contain(case.must_contain, result.turns)
    return result


def run_cases(
    cases: Sequence[EvalCase],
    graph_factory: Callable[[EvalCase], object],
    judge: Judge,
    values: ExpectedValues | None = None,
    progress: Callable[[str], None] | None = None,
) -> list[CaseResult]:
    """Roda cada caso num grafo (e thread) novo."""
    if values is None:
        values = ExpectedValues.from_data(config.DATA_DIR)
    results = []
    for case in cases:
        try:
            graph = graph_factory(case)
            result = run_case(case, graph, judge, values)
        except Exception as error:  # noqa: BLE001
            result = CaseResult(case=case, error=f"{type(error).__name__}: {error}")
        results.append(result)
        if progress:
            progress(f"{case.id}: {'ok' if result.passed else 'FALHOU'}")
    return results


def _mark(result: CaseResult, key: str) -> str:
    if result.error:
        return "erro"
    check = result.checks.get(key)
    if check is None:
        return "—"
    return "ok" if check.passed else "falhou"


def render_report(results: Sequence[CaseResult], *, model_name: str, judge_name: str = "") -> str:
    now = datetime.now(config.TIMEZONE)
    approved = sum(1 for r in results if r.passed)
    lines = [
        f"# Avaliação do agente — {now:%Y-%m-%d %H:%M}",
        "",
        f"- Modelo do agente: `{model_name}`",
    ]
    if judge_name:
        lines.append(f"- Modelo juiz (só SC-004): `{judge_name}`")
    lines += [f"- Casos aprovados: {approved}/{len(results)}", "", "## Totais por critério", ""]
    lines += [
        "| Critério | O que mede | Aprovados | Taxa | Meta | Atingida |",
        "|---|---|---|---|---|---|",
    ]
    for key, (label, goal) in GOALS.items():
        evaluated = [r for r in results if key in r.case.criteria]
        if not evaluated:
            continue
        ok = sum(
            1 for r in evaluated if not r.error and r.checks.get(key, CheckResult(False)).passed
        )
        rate = ok / len(evaluated)
        lines.append(
            f"| {key} | {label} | {ok}/{len(evaluated)} | {rate:.0%} | {goal:.0%} | "
            f"{'sim' if rate >= goal else 'não'} |"
        )
    lines += [
        "",
        "## Resultado por caso",
        "",
        "| Caso | Fonte esperada | Fontes chamadas | SC-001 | SC-002 | SC-003 | SC-004 "
        "| Conteúdo | Resultado |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        called = sorted({t for turn in r.turns for t in turn.tools}) or ["—"]
        cells = [_mark(r, key) for key in ("SC-001", "SC-002", "SC-003", "SC-004", CONTENT)]
        lines.append(
            f"| {r.case.id} | {', '.join(r.case.expected_tools)} | {', '.join(called)} | "
            + " | ".join(cells)
            + f" | {'aprovado' if r.passed else 'reprovado'} |"
        )
    failures = [r for r in results if not r.passed]
    if failures:
        lines += ["", "## Detalhes das falhas", ""]
        for r in failures:
            if r.error:
                lines.append(f"- **{r.case.id}**: erro ao rodar ({r.error})")
                continue
            for key, check in r.checks.items():
                if not check.passed:
                    lines.append(f"- **{r.case.id}** ({key}): {check.detail}")
    return "\n".join(lines) + "\n"


def _write(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada do comando `emporio-eval`."""
    parser = argparse.ArgumentParser(prog="emporio-eval", description="Avaliação do agente")
    parser.add_argument("--casos", help="ids separados por vírgula (padrão: todos)")
    parser.add_argument("--arquivo", default=str(config.EVALS_DIR / "cases.yaml"))
    parser.add_argument("--saida", default=str(config.EVALS_DIR / "reports"))
    args = parser.parse_args(list(argv) if argv is not None else None)

    config.load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        _write("Defina ANTHROPIC_API_KEY no .env (veja o .env.example) para rodar a avaliação.")
        return 1

    from emporio.agent.graph import build_graph, create_model
    from emporio.data.loader import ensure_databases
    from emporio.evaluation.checks import make_judge

    ensure_databases(config.DATA_DIR, config.VAR_DIR)
    values = ExpectedValues.from_data(config.DATA_DIR)
    cases = load_cases(Path(args.arquivo), values)
    if args.casos:
        wanted = {item.strip() for item in args.casos.split(",")}
        cases = [case for case in cases if case.id in wanted]

    judge = make_judge(config.judge_model_name())
    results = run_cases(
        cases, lambda case: build_graph(create_model()), judge, values, progress=_write
    )
    report = render_report(
        results, model_name=config.model_name(), judge_name=config.judge_model_name()
    )
    out_dir = Path(args.saida)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{datetime.now(config.TIMEZONE):%Y-%m-%d}.md"
    path.write_text(report, encoding="utf-8", newline="\n")
    _write(f"Relatório gravado em {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
