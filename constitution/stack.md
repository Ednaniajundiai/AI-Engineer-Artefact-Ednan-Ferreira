# Stack de Referência: Agente de Atendimento da Empório da Música

Tudo aqui é padrão, não obrigação: é a stack usada a menos que o `plan.md` da
feature justifique outra coisa e registre a exceção.

## Stack padrão

- **Linguagem**: Python 3.11 ou superior (a única restrição técnica imposta
  pelo desafio).
- **Ambiente e dependências**: `uv` com `pyproject.toml` e `uv.lock`
  versionados; tudo roda com `uv run`.
- **Orquestração do agente**: LangChain e LangGraph.
- **Modelo de linguagem**: família Claude, via API da Anthropic. O modelo exato
  é escolhido e justificado no plano.
- **Dados**: os CSVs de `data/` carregados num SQLite local, gerado a partir
  deles e aberto só para leitura pelo agente. O arquivo gerado não é
  versionado.
- **Políticas**: `data/políticas_da_loja.pdf` como fonte única das regras da
  loja.
- **Interface**: linha de comando (CLI).
- **Qualidade**: `ruff` (lint e formatação) e `pytest`.

## Restrições Técnicas

- A chave da API vem de variável de ambiente (`ANTHROPIC_API_KEY`), lida de um
  `.env` local que não é versionado. O repositório traz um `.env.example`.
- Os arquivos de `data/` são a entrada original da loja e não são editados. As
  correções e normalizações acontecem na carga, em código, e são documentadas.
- O projeto precisa rodar numa máquina limpa só com os passos do README (Python,
  `uv` e a chave da API).
- A suíte de testes obrigatória não depende de rede nem da chave da API.

## Integrações que não podem quebrar

- API da Anthropic: única dependência externa em tempo de execução.
- Nenhum sistema da loja é integrado nesta fase. Os dados vêm só dos arquivos
  de `data/`.
