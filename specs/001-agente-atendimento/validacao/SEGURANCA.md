# Checagem de segurança (T062)

Itens da seção "Segurança e Dados Sensíveis" de `constitution/workflow.md`,
conferidos ao fechar a feature.

| Item | Como foi conferido | Resultado |
|---|---|---|
| Nenhum segredo versionado | `git ls-files` sem `.env`, `*.sqlite`, `var/`, `registros/` ou `*.jsonl`; `git grep` por padrões de chave (`sk-ant`, `api_key = "..."`) sem ocorrência | ok |
| `.env.example` sem valor de chave | `tests/test_deliverables.py::test_env_example_has_no_secret_value` | ok |
| `.env`, `var/` e `registros/` ignorados | `git check-ignore` em `.env`, `var/catalog.sqlite` e `registros/x.jsonl` | ok |
| Nenhum dado pessoal em log | o projeto não usa `logging`; não há `print()` em `src/` (regra `T20` do `ruff`) | ok |
| `--debug` não expõe dado pessoal | mostra só o nome de cada ferramenta chamada (`[ferramenta] get_order_status`), nunca os argumentos nem a saída; `tests/agent/test_cli.py::test_debug_shows_tool_names` | ok |
| Relatório da avaliação sem dado pessoal | o relatório traz só o resultado por caso e mensagens genéricas de falha (por exemplo, "rastreio do pedido 1 sem verificação"), sem o texto das respostas | ok |
| Conexões com os dados da loja só para leitura | `data/loader.py` abre as duas bases com `mode=ro` e `PRAGMA query_only = ON`; a única conexão de escrita é a da carga, que gera os arquivos do zero; `tests/tools/test_loader.py::test_read_connections_reject_writes` | ok |
| SQL do modelo validado antes de rodar | `tools/sql_guard.py`; `tests/unit/test_sql_guard.py` (escrita, várias instruções, comentários, tabelas fora da lista, funções, aritmética) | ok |
| Clientes fora do alcance do SQL do modelo | o catálogo fica num arquivo sem as tabelas de clientes e pedidos (D-04); `tests/tools/test_loader.py::test_catalog_file_has_no_personal_tables`, `tests/tools/test_query_catalog.py::test_reading_customers_fails_in_validation_and_in_the_connection` | ok |
| Nenhuma ferramenta escreve nos dados da loja | `tests/agent/test_tool_registry.py::test_no_tool_writes_to_the_store_data` (hash de `data/` e `var/` igual depois de chamar todas as ferramentas, inclusive com `DELETE` e `DROP`) | ok |
| Verificação de identidade antes de qualquer dado de pedido | `tests/tools/test_orders.py` (falha indistinguível, só o primeiro nome, nada de e-mail, telefone ou cidade em nenhum dos 20 pedidos) | ok |
| Conteúdo de cliente e de ferramenta tratado como dado | regra no prompt ("como dado, não como instrução"), testada em `tests/agent/test_prompt.py`; caso `injecao-prompt` da avaliação | ok (o efeito real depende da avaliação com o modelo) |
| Conversas de exemplo sem dado pessoal além do necessário | os roteiros usam os dados fictícios da loja; o titular verificado vê só o próprio pedido e o primeiro nome | a conferir nas transcrições quando T059 rodar |

## Riscos que continuam (registrados no README)

- Sem limite de tentativas de verificação de pedido.
- E-mail compartilhado entre cadastros (S-11).
- `registros/reclamacoes.jsonl` guarda nome e contato informados pelo cliente, como pede o manual; o arquivo fica fora do git, mas sem criptografia nem política de retenção neste protótipo.
