"""Interface de linha de comando (plan S2-10).

Comandos durante a conversa: `/nova` começa um novo atendimento e `/sair`
encerra. A flag `--debug` mostra as ferramentas chamadas, e `--transcricao`
salva a conversa em markdown.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from emporio import config
from emporio.data.loader import ensure_databases

GREETING = "Empório da Música — atendimento. Digite /nova para recomeçar ou /sair para encerrar."
PROMPT = "Você: "


def _text_of(message: BaseMessage) -> str:
    """Texto de uma mensagem, que pode vir em blocos."""
    content = message.content
    if isinstance(content, str):
        return content
    parts = [block.get("text", "") for block in content if isinstance(block, dict)]
    return "".join(parts)


def _tool_names(messages: Sequence[BaseMessage]) -> list[str]:
    names: list[str] = []
    for message in messages:
        if isinstance(message, AIMessage):
            names.extend(call["name"] for call in message.tool_calls)
    return names


def _stdout_write(text: str) -> None:
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def _append(path: Path | None, text: str) -> None:
    if path is None:
        return
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def run_conversation(
    graph,
    *,
    read_line: Callable[[str], str],
    write: Callable[[str], None],
    debug: bool = False,
    transcript: Path | None = None,
) -> None:
    """Laço de conversa: lê o cliente, chama o grafo e mostra a resposta."""
    write(GREETING)
    if transcript is not None:
        transcript.write_text("# Conversa com o atendimento\n\n", encoding="utf-8", newline="\n")

    thread_id = uuid.uuid4().hex
    while True:
        try:
            line = read_line(PROMPT).strip()
        except EOFError:
            return
        if not line:
            continue
        if line == "/sair":
            return
        if line == "/nova":
            thread_id = uuid.uuid4().hex
            _append(transcript, "---\n\n")
            write("Novo atendimento iniciado.")
            continue

        _append(transcript, f"**Cliente:** {line}\n\n")
        try:
            result = graph.invoke(
                {"messages": [HumanMessage(line)]},
                {"configurable": {"thread_id": thread_id}},
            )
        except Exception as error:  # noqa: BLE001 - a CLI não pode cair no meio da conversa
            write("Desculpe, não consegui responder agora. Tente de novo em instantes.")
            if debug:
                write(f"[erro] {type(error).__name__}: {error}")
            continue

        messages = result["messages"]
        last_human = max(i for i, m in enumerate(messages) if isinstance(m, HumanMessage))
        if debug:
            for name in _tool_names(messages[last_human:]):
                write(f"[ferramenta] {name}")
        answer = _text_of(messages[-1])
        write(f"Atendente: {answer}")
        _append(transcript, f"**Atendente:** {answer}\n\n")


def _build_default_graph():
    from emporio.agent.graph import build_graph, create_model

    config.load_env()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    ensure_databases(config.DATA_DIR, config.VAR_DIR)
    return build_graph(create_model())


def main(
    argv: Sequence[str] | None = None,
    *,
    graph=None,
    read_line: Callable[[str], str] = input,
    write: Callable[[str], None] = _stdout_write,
) -> int:
    """Ponto de entrada do comando `emporio`."""
    parser = argparse.ArgumentParser(prog="emporio", description="Atendimento da Empório da Música")
    parser.add_argument("--debug", action="store_true", help="mostra as ferramentas chamadas")
    parser.add_argument("--transcricao", metavar="ARQ.md", help="salva a conversa em markdown")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if graph is None:
        graph = _build_default_graph()
        if graph is None:
            write("Defina ANTHROPIC_API_KEY no .env (veja o .env.example) para conversar.")
            return 1

    transcript = Path(args.transcricao) if args.transcricao else None
    run_conversation(
        graph, read_line=read_line, write=write, debug=args.debug, transcript=transcript
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
