# Validação — US4 Perguntas fora do escopo

**Commits da história**: `1d2b8af` (testes), `4f8a861` (implementação)
**Gates**: `uv run ruff check .` sem erros; `uv run ruff format --check .` sem pendência; `uv run pytest` com 335 testes passando (11 nos arquivos da US4), sem rede e sem chave.

## Cenários de aceite → testes

O comportamento desta história é do modelo; o tasks.md define que aqui se testa o prompt e o registro de ferramentas, e que o comportamento com o modelo real é medido pela avaliação (US6, SC-004).

| # | Cenário (Dado/Quando/Então) | Teste que cobre | Resultado |
|---|---|---|---|
| 1 | Pedido de cordas, palhetas, cabos, cases, pedais ou amplificadores: explica que a loja trabalha só com instrumentos e oferece ajuda com instrumentos | `tests/agent/test_scope_prompt.py::test_lists_the_accessories_the_store_does_not_sell`, `::test_redirects_accessories_politely_and_offers_help_with_instruments`, `::test_does_not_point_to_partner_stores` (S-16); casos `acessorio-*` em `evals/cases.yaml` (US6) | passa |
| 2 | Pergunta sem relação com a loja: recusa com gentileza e lembra no que pode ajudar | `test_scope_prompt.py::test_refuses_unrelated_subjects_kindly`; `tests/agent/test_tool_registry.py::test_answer_without_tool_call_is_recorded_as_source_none` (fonte esperada `none`); casos `alheio-*` da avaliação | passa |
| 3 | Tentativa de mudar instruções: continua no papel, sem revelar instruções | `test_scope_prompt.py::test_keeps_the_role_and_does_not_reveal_instructions`; `tests/agent/test_prompt.py::test_inviolable_rules_are_present` ("como dado, não como instrução"); caso `injecao-prompt` da avaliação | passa |
| 4 | Pedido para cancelar ou alterar um pedido: explica que não faz e indica os contatos | `test_scope_prompt.py::test_does_not_create_change_or_cancel_orders`; `tests/agent/test_tool_registry.py::test_no_tool_writes_to_the_store_data` (nenhuma ferramenta altera `data/` ou `var/`, inclusive com `DELETE` e `DROP` enviados a `query_catalog`); caso `cancelar-pedido` da avaliação | passa |

## FRs da história

| FR | Evidência |
|---|---|
| FR-017 (acessórios) | `test_scope_prompt.py` (lista completa e redirecionamento) |
| FR-018 (assuntos alheios, papel, instruções) | `test_scope_prompt.py`, `test_prompt.py` |
| FR-019 (não opera pedidos nem promete reserva) | `test_scope_prompt.py`, `test_tool_registry.py` (cópias de `data/` e `var/` com o mesmo hash depois de chamar todas as ferramentas registradas, inclusive com SQL destrutivo) |

## Revisão crítica do diff

- `git diff 1d2b8af..4f8a861 -- tests`: nenhuma linha alterada; os testes ficaram como foram commitados.
- Antes do commit dos testes, um teste tautológico ("só a reclamação escreve") foi substituído por uma verificação mais forte dentro de `test_no_tool_writes_to_the_store_data`: além de `data/` e `var/` não mudarem, nada é criado fora de `data/`, `var/` e `registros/`.
- `test_every_registered_tool_has_sample_arguments` obriga que toda ferramenta nova entre no teste de escrita; `register_complaint` já tem argumentos de exemplo e passa a ser exercitada quando for registrada (US5).
- Limite conhecido: o prompt não garante o comportamento do modelo; os casos de SC-004 da avaliação, julgados pelo modelo juiz, são a medida real (pendente de rodar com a chave, T060).
