# Clone limpo seguindo só o README (T063, SC-005)

Repositório clonado numa pasta nova, sem `.venv`, `var/`, `.env` nem cache, e
os passos do README seguidos na ordem.

| Passo do README | Resultado |
|---|---|
| `uv sync` | ambiente criado a partir do `uv.lock`, sem erro |
| `cp .env.example .env` | ok (chave vazia, porque o ambiente da conferência não tem chave da API) |
| `uv run pytest` | 402 testes passando, 1 pulado (as conversas de exemplo, T059, com o motivo registrado), sem rede e sem chave |
| `uv run emporio` | sem chave, termina com código 1 e a mensagem "Defina ANTHROPIC_API_KEY no .env (veja o .env.example) para conversar." |
| `uv run emporio-eval` | sem chave, termina com código 1 e a mensagem equivalente |
| `uv run ruff check .` e `uv run ruff format --check .` | o `ruff check` acusou 3 imports fora de ordem que o cache local escondia; corrigido na causa (`known-first-party = ["emporio"]`, commit `6eda2f3`) e conferido de novo com `--no-cache` |
| Comando de geração das conversas (`uv run emporio --transcricao ... < roteiro`) | conferido com o modelo simulado no lugar do real: a CLI lê o roteiro pela entrada padrão, encerra no fim do arquivo e grava a transcrição em markdown |

## O que não deu para conferir

A conversa com o modelo real (o fim do caminho de SC-005) depende da chave da
API, que não estava disponível. Todos os passos até ela foram seguidos sem
travar, e a mensagem sem chave diz exatamente o que fazer. Quando a chave
estiver no `.env`, o próximo passo é `uv run emporio`.
