"""CLI com o modelo simulado e entrada roteirizada (FR-022; plan S2-10)."""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from tests.fakes import ScriptedChatModel, tool_call

from emporio.agent.graph import build_graph
from emporio.cli import main


@tool
def echo(text: str) -> str:
    """Repete o texto recebido."""
    return f"eco: {text}"


def _run(model, lines, clock, argv=()):
    graph = build_graph(model, tools=[echo], clock=clock(2025, 11, 3, 10, 0))
    inputs = iter(lines)
    output: list[str] = []

    def read_line(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError from None

    code = main(list(argv), graph=graph, read_line=read_line, write=output.append)
    return code, "\n".join(output)


def test_sair_ends_the_conversation(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Olá, tudo bem?")])
    code, output = _run(model, ["oi", "/sair", "nunca lida"], clock)

    assert code == 0
    assert "Olá, tudo bem?" in output
    assert len(model.calls) == 1


def test_nova_starts_a_fresh_thread(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Oi!"), AIMessage(content="Olá!")])
    _run(model, ["meu nome é Rita", "/nova", "oi", "/sair"], clock)

    seen = [m.content for m in model.calls[1] if isinstance(m, HumanMessage)]
    assert seen == ["oi"]


def test_same_thread_keeps_context_between_messages(clock):
    model = ScriptedChatModel(responses=[AIMessage(content="Oi!"), AIMessage(content="Claro!")])
    _run(model, ["meu nome é Rita", "qual meu nome?", "/sair"], clock)

    seen = [m.content for m in model.calls[1] if isinstance(m, HumanMessage)]
    assert seen == ["meu nome é Rita", "qual meu nome?"]


def test_transcript_is_saved_as_markdown(clock, tmp_path):
    path = tmp_path / "conversa.md"
    model = ScriptedChatModel(responses=[AIMessage(content="Olá, tudo bem?")])
    _run(model, ["oi", "/sair"], clock, argv=["--transcricao", str(path)])

    text = path.read_text(encoding="utf-8")
    assert "**Cliente:** oi" in text
    assert "**Atendente:** Olá, tudo bem?" in text


def test_debug_shows_tool_names(clock):
    model = ScriptedChatModel(
        responses=[tool_call("echo", {"text": "oi"}), AIMessage(content="Pronto!")]
    )
    _, quiet = _run(model, ["oi", "/sair"], clock)
    assert "echo" not in quiet

    model = ScriptedChatModel(
        responses=[tool_call("echo", {"text": "oi"}), AIMessage(content="Pronto!")]
    )
    _, debug = _run(model, ["oi", "/sair"], clock, argv=["--debug"])
    assert "echo" in debug
    assert "Pronto!" in debug
