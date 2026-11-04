# Cobertura — FRs e suposições (T061)

Revisão feita ao fechar a feature: cada FR do `spec.md` tem teste rastreável, e
cada suposição S-01 a S-18 aparece no código (comentário com o ID), em teste e
no README. A rastreabilidade foi conferida com `grep` pelos IDs em `src/`,
`tests/` e `README.md`; onde o ID não está no teste, o teste é citado pelo
nome.

## Requisitos funcionais

| FR | Testes | Validação |
|---|---|---|
| FR-001 tom e fluxo de atendimento | `tests/agent/test_prompt.py` (persona, fluxo em ordem, apresentação, nome) | [US1](US1.md) |
| FR-002 só o manual; senão "não tenho a informação" | `tests/unit/test_policies.py`, `tests/tools/test_policy_tool.py`, `tests/tools/test_store.py`, `tests/agent/test_prompt.py` | [US1](US1.md) |
| FR-003 aberta agora, no fuso de Campo Grande | `tests/unit/test_business_hours.py`, `tests/tools/test_store.py` | [US1](US1.md) |
| FR-004 preço e disponibilidade só por consulta | `tests/tools/test_query_catalog.py`, `tests/unit/test_sql_guard.py`, `tests/agent/test_catalog_flow.py` | [US2](US2.md) |
| FR-005 busca por nome, tipo, marca e preço; só disponíveis nas opções | `tests/tools/test_find_product.py`, `tests/tools/test_query_catalog.py`, `tests/unit/test_normalize.py`, `tests/agent/test_catalog_flow.py` | [US2](US2.md) |
| FR-006 promoção, PIX e não cumulatividade | `tests/unit/test_pricing.py`, `tests/tools/test_catalog_view.py`, `tests/tools/test_find_product.py` | [US2](US2.md) |
| FR-007 preço original e percentual junto da promoção | `tests/tools/test_find_product.py`, `tests/agent/test_catalog_flow.py` | [US2](US2.md) |
| FR-008 faixas de parcelamento da 3.1 | `tests/unit/test_installments.py`, `tests/tools/test_catalog_view.py` | [US2](US2.md) |
| FR-009 disponibilidade pelo status e alternativas | `tests/unit/test_pricing.py`, `tests/tools/test_find_product.py` | [US2](US2.md) |
| FR-010 promoção encerrada | `tests/unit/test_pricing.py`, `tests/tools/test_find_product.py`, `tests/agent/test_catalog_flow.py` | [US2](US2.md) |
| FR-011 número e e-mail antes de revelar | `tests/tools/test_orders.py`, `tests/agent/test_orders_flow.py` | [US3](US3.md) |
| FR-012 falha sem dizer qual dado está errado | `tests/tools/test_orders.py::test_wrong_email_and_missing_order_give_the_same_answer`, `tests/agent/test_orders_flow.py` | [US3](US3.md) |
| FR-013 dado pessoal mínimo, nada de terceiros | `tests/tools/test_orders.py::test_output_never_has_personal_data_beyond_the_first_name`, `tests/tools/test_loader.py`, `tests/tools/test_query_catalog.py`, `tests/agent/test_orders_flow.py` | [US3](US3.md) |
| FR-014 conteúdo do pedido por status | `tests/tools/test_orders.py` (status, data, itens, total, rastreio, previsão vencida, motivo do cancelamento) | [US3](US3.md) |
| FR-015 verificação por pedido | `tests/tools/test_orders.py::test_each_call_verifies_again`, `tests/agent/test_orders_flow.py` | [US3](US3.md) |
| FR-016 arrependimento, defeito e garantia | `tests/unit/test_deadlines.py`, `tests/tools/test_orders.py`, `tests/tools/test_policy_tool.py`, `tests/agent/test_orders_flow.py` | [US1](US1.md), [US3](US3.md) |
| FR-017 acessórios redirecionados | `tests/agent/test_scope_prompt.py` | [US4](US4.md) |
| FR-018 assuntos alheios, papel e instruções | `tests/agent/test_scope_prompt.py`, `tests/agent/test_prompt.py` | [US4](US4.md) |
| FR-019 não opera pedidos nem promete reserva | `tests/agent/test_scope_prompt.py`, `tests/agent/test_tool_registry.py` | [US4](US4.md) |
| FR-020 reclamação com protocolo e 24 horas úteis | `tests/tools/test_complaints.py`, `tests/agent/test_complaint_prompt.py` | [US5](US5.md) |
| FR-021 fora do expediente, quando a equipe volta | `tests/tools/test_complaints.py`, `tests/tools/test_store.py`, `tests/unit/test_business_hours.py` | [US1](US1.md), [US5](US5.md) |
| FR-022 contexto dentro do atendimento | `tests/agent/test_graph.py`, `tests/agent/test_cli.py` | Fundação |
| FR-023 avaliação com conjunto fixo e relatório | `tests/unit/test_eval_checks.py`, `tests/unit/test_eval_cases.py`, `tests/agent/test_eval_runner.py` | [US6](US6.md) |
| FR-024 teste próprio para cada regra | `tests/unit/` (dinheiro, preço, parcelas, horário, prazos, SQL) e `tests/tools/test_orders.py` (verificação) | [US6](US6.md) |
| FR-025 README e conversas de exemplo | `tests/test_deliverables.py` (o teste das conversas fica pulado até T059, com o motivo registrado) | este arquivo |

## Suposições

| ID | Código | Teste | README |
|---|---|---|---|
| S-01 | `tools/store.py`, `data/policies.py` | `tests/tools/test_store.py`, `tests/tools/test_policy_tool.py` | sim |
| S-02 | `tools/store.py`, `data/policies.py` | `tests/tools/test_store.py`, `tests/tools/test_policy_tool.py` | sim |
| S-03 | `rules/installments.py`, `data/policies.py` | `tests/unit/test_installments.py`, `tests/unit/test_policies.py` | sim |
| S-04 | `tools/orders.py` | `tests/tools/test_orders.py` | sim |
| S-05 | `tools/orders.py` | `tests/tools/test_orders.py` | sim |
| S-06 | `rules/pricing.py` | `tests/unit/test_pricing.py`, `tests/tools/test_find_product.py`, `tests/tools/test_orders.py` | sim |
| S-07 | `rules/pricing.py` | `tests/unit/test_pricing.py`, `tests/tools/test_find_product.py` | sim |
| S-08 | `rules/pricing.py` | `tests/unit/test_pricing.py`, `tests/tools/test_find_product.py` | sim |
| S-09 | `data/loader.py` | `tests/tools/test_catalog_view.py`, `tests/tools/test_find_product.py` | sim |
| S-10 | `data/loader.py` (visão `v_categories`) | `tests/tools/test_catalog_view.py`, `tests/agent/test_catalog_flow.py` | sim |
| S-11 | `tools/orders.py` | `tests/tools/test_orders.py::test_shared_email_opens_only_the_order_of_customer_11` | sim, e nas limitações |
| S-12 | `tools/orders.py` | `tests/tools/test_orders.py::test_overdue_forecast_on_order_8`, `tests/agent/test_orders_flow.py` | sim |
| S-13 | `rules/pricing.py`, `data/policies.py` | `tests/unit/test_pricing.py::test_inactive_promotions_are_ignored` | sim |
| S-14 | `rules/deadlines.py`, `data/policies.py` | `tests/unit/test_deadlines.py`, `tests/tools/test_orders.py`, `tests/tools/test_policy_tool.py` | sim |
| S-15 | `rules/business_hours.py`, `tools/store.py`, `data/policies.py` | `tests/tools/test_store.py::test_holidays_warning_without_affirming_dates` | sim, e nas limitações |
| S-16 | `data/policies.py` | `tests/agent/test_scope_prompt.py`, `tests/tools/test_policy_tool.py` | sim |
| S-17 | `data/loader.py` | `tests/tools/test_loader.py::test_suspicious_phone_is_kept_as_is`, `tests/tools/test_orders.py::test_phone_is_never_accepted_as_proof_of_identity` | sim |
| S-18 | `tools/complaints.py` | `tests/tools/test_complaints.py` | sim |

## Correções feitas nesta revisão

- S-10 e S-17 não tinham comentário com o ID no código: entraram em `data/loader.py`.
- S-17 não tinha teste: entraram dois (o telefone suspeito fica como está na carga; telefone nunca serve de prova de identidade).
- As suposições novas N-01 a N-07 estão no README e nas validações das histórias em que surgiram.
