# Workflow do Projeto: Agente de Atendimento da Empório da Música

## Definition of Done

- Todo requisito funcional escrito em formato **Dado/Quando/Então** tem pelo
  menos um teste automatizado que cobre o cenário principal antes de a feature
  ser dada como concluída.
- Toda regra de negócio (preço, desconto, parcelamento, prazo, verificação de
  identidade) tem teste unitário, incluindo os casos de borda e as suposições
  documentadas.
- Toda ferramenta que o agente pode chamar tem teste da ferramenta em si, sem o
  modelo.
- O conjunto fixo de perguntas de avaliação cobre cada tipo de pergunta que a
  feature trata, com a ferramenta e o desfecho esperados.
- Nenhuma feature é fechada com teste quebrado, ou pulado sem justificativa
  registrada.

## Segurança e Dados Sensíveis

- Segredos (chaves de API, tokens) nunca são commitados em texto puro. Vêm
  sempre de variável de ambiente, e o `.env` está no `.gitignore`.
- Dados pessoais de clientes não vão para logs, para o prompt nem para as
  conversas de exemplo além do necessário para demonstrar o atendimento.
- O acesso aos dados pelo agente é só de leitura (princípio IV), e consultas
  geradas pelo modelo são validadas em código antes de rodar.

## Branch, Commit e Pull Request

- Uma branch por feature, com o nome `NNN-slug` (o mesmo da pasta em `specs/`).
  Nunca se commita direto em `main`.
- Mensagens de commit em português, com o verbo no presente e sem prefixo, como
  em "Adiciona carga do catálogo no SQLite". O assunto tem até ~72 caracteres e,
  quando for útil, o corpo explica o porquê.
- Commits feitos só como o usuário git local, sem trailers de coautoria.
- Cada commit representa um passo real e coerente do trabalho; nada de juntar a
  feature inteira num commit só.
- Um commit por história de usuário na implementação. Push, abertura de PR e
  merge só com autorização do dono do projeto, e o merge é sempre feito por ele.
- Os relatórios de análise e validação ficam versionados em `specs/NNN-slug/`
  (`ANALISE_CONSISTENCIA.md`, `validacao/USn.md`).
- Nomes de código (módulos, funções, variáveis) em inglês, seguindo a PEP 8.
  Textos para o cliente, documentação e mensagens de commit em português.

## Gates antes de abrir PR

Rodados ao fechar cada história de usuário e antes de declarar a feature
concluída:

- `uv run ruff check .` sem erros.
- `uv run ruff format --check .` sem mudança pendente.
- `uv run pytest`, com todos os testes passando, sem rede e sem a chave da API
  (o modelo é simulado).
- Nenhum `print()` de depuração esquecido no código.
- Toda variável de ambiente nova documentada no `.env.example` e no README.

Fora do gate, mas obrigatória antes da entrega: a avaliação com o modelo real
(`uv run` do script de avaliação definido no plano), com o resultado registrado
no README.
