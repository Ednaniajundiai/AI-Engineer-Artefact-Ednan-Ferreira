# Validação — US5 Registro de reclamação

**Commits da história**: `8f6f39d` (testes), `9d9f522` (implementação)
**Gates**: `uv run ruff check .` sem erros; `uv run ruff format --check .` sem pendência; `uv run pytest` com 388 testes passando, sem rede e sem chave.

## Cenários de aceite → testes

| # | Cenário (Dado/Quando/Então) | Teste que cobre | Resultado |
|---|---|---|---|
| 1 | Cliente insatisfeito relata o problema: resposta com empatia e pedido do que falta entre nome, contato, descrição e número do pedido | `tests/agent/test_complaint_prompt.py::test_prompt_asks_for_empathy_and_only_the_missing_data`; `tests/tools/test_complaints.py::test_refuses_without_minimum_data_and_says_what_is_missing` (nome, contato e descrição, um de cada vez), `::test_lists_every_missing_field`, `::test_contact_must_be_a_phone_or_an_email`; caso `reclamacao-incompleta` da avaliação | passa |
| 2 | Dados mínimos coletados: registra, devolve protocolo e informa o prazo de 24 horas úteis | `test_complaints.py::test_protocol_has_the_date_and_four_hex_characters`, `::test_one_jsonl_line_per_complaint_only_in_the_records_folder`, `::test_response_brings_the_protocol_and_the_24_business_hours`, `::test_order_number_is_optional`, `::test_tool_schema_has_order_id_optional`; `test_complaint_prompt.py::test_registered_complaint_returns_the_protocol`, `::test_prompt_gives_protocol_deadline_and_return_time`; casos `reclamacao-completa` e `reclamacao-pedido-atrasado` | passa |
| 3 | Reclamação fora do horário: informa também quando a equipe volta | `test_complaints.py::test_outside_business_hours_says_when_the_team_returns` (sábado à tarde → segunda-feira), `::test_during_business_hours_no_return_notice` | passa |

## FRs da história

| FR | Evidência |
|---|---|
| FR-020 (nome, contato, descrição, pedido opcional; protocolo; 24 horas úteis) | `tests/tools/test_complaints.py` (12 testes) |
| FR-021 (fora do expediente, quando a equipe volta) | `test_complaints.py::test_outside_business_hours_says_when_the_team_returns`; `tests/tools/test_store.py::test_closed_now_reports_the_next_opening` |
| FR-022 (dados da reclamação mantidos no atendimento) | `tests/agent/test_graph.py::test_second_message_in_the_same_thread_sees_the_first`; caso multi-turno `reclamacao-incompleta` |
| Princípio IV (única escrita, fora dos dados da loja) | `test_complaints.py::test_one_jsonl_line_per_complaint_only_in_the_records_folder`; `tests/agent/test_tool_registry.py::test_no_tool_writes_to_the_store_data` (agora exercita `register_complaint` também) |

## Avaliação (T056)

Três casos novos em `evals/cases.yaml`: `reclamacao-completa`, `reclamacao-incompleta` (multi-turno, sem contato na primeira mensagem) e `reclamacao-pedido-atrasado` (pedido 8 com previsão vencida, S-12, consultado e depois reclamado). `tests/unit/test_eval_cases.py::test_project_cases_cover_complaints` exige esses casos. Total do conjunto: 37 casos.

## Revisão crítica do diff

- `git diff 8f6f39d..9d9f522 -- tests`: nenhuma linha alterada.
- O teste de registro (`test_tool_registry.py`), escrito na US4, passou a cobrir `register_complaint` sem mudança: a ferramenta grava em `config.RECORDS_DIR`, que o teste redireciona para uma pasta temporária, e `data/` e `var/` ficam com o mesmo hash.
- Suposição nova (N-07): o contato só é aceito se parecer um e-mail ou um telefone (8 ou mais dígitos); o manual não define o formato, e um contato inválido impediria o retorno de 24 horas úteis.
- Dado pessoal: o JSONL guarda nome e contato informados pelo próprio cliente, como pede o manual (7.3), em `registros/`, que está no `.gitignore`.
