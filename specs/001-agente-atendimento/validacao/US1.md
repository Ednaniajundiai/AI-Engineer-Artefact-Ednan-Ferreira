# Validação — US1 Informações da loja e políticas

**Commits da história**: `eb76cbc` (testes), `13abf81` (testes complementares), `714d85b` (implementação)
**Gates**: `uv run ruff check .` sem erros; `uv run ruff format --check .` sem pendência; `uv run pytest` com 126 testes passando (85 deles nos arquivos da US1), sem rede e sem chave.

## Cenários de aceite → testes

| # | Cenário (Dado/Quando/Então) | Teste que cobre | Resultado |
|---|---|---|---|
| 1 | Primeira mensagem: apresenta-se como assistente virtual, cumprimenta pelo nome e pergunta como ajudar | `tests/agent/test_prompt.py::test_introduces_itself_as_virtual_assistant_of_the_store`, `::test_greets_by_name_when_the_customer_gives_it`, `::test_attendance_flow_is_in_order` | passa |
| 2 | Endereço e contatos: endereço, telefone (67) 3341-4444, WhatsApp (67) 3321-4500 e e-mail sem acento | `tests/tools/test_store.py::test_address_is_informed`, `::test_phone_and_whatsapp_are_labeled`, `::test_email_has_no_accent`; `tests/tools/test_policy_tool.py::test_sobre_loja_has_unaccented_email_and_both_labeled_phones` | passa |
| 3 | "Está aberta agora?" pelo dia e hora de Campo Grande e pelo horário do manual | `tests/unit/test_business_hours.py::test_is_open` (11 instantes, incluindo as fronteiras 8h59/9h/17h59/18h e sábado 12h59/13h), `::test_converts_other_timezones_to_campo_grande`, `::test_next_opening`; `tests/tools/test_store.py::test_open_now_on_a_weekday_morning`, `::test_closed_now_reports_the_next_opening`, `::test_sunday_is_closed_and_next_opening_is_monday`; `tests/agent/test_prompt.py::test_store_tool_runs_inside_the_graph_with_the_injected_clock` | passa |
| 4 | Devolução por arrependimento: 7 dias corridos do recebimento, embalagem original, sem uso; pergunta se a compra foi online | `tests/tools/test_policy_tool.py::test_trocas_devolucoes_states_the_withdrawal_conditions`, `::test_trocas_devolucoes_has_rules_and_the_s14_note`; `tests/agent/test_prompt.py::test_withdrawal_question_asks_whether_the_purchase_was_online` | passa |
| 5 | Frete para fora da região metropolitana: modalidades e prazos; valor depende do CEP, sem estimar | `tests/tools/test_policy_tool.py::test_frete_for_other_cities_has_modalities_deadlines_and_depends_on_the_cep`; `tests/agent/test_prompt.py::test_freight_value_is_never_estimated` | passa |
| 6 | Ponto que o manual não cobre: "não tenho essa informação" e contatos, sem inventar | `tests/agent/test_prompt.py::test_says_it_has_no_information_and_gives_the_contacts_when_the_manual_is_silent`, `::test_inviolable_rules_are_present` | passa |

## Casos de borda da spec ligados à história

| Caso | Teste | Resultado |
|---|---|---|
| Feriado específico: fecha nos feriados, sem afirmar a data (S-15) | `tests/tools/test_store.py::test_holidays_warning_without_affirming_dates`; nota S-15 em `tests/unit/test_policies.py::test_interpretation_notes_land_in_the_right_topics` | passa |
| Horário estendido em datas especiais: redes sociais e WhatsApp | `tests/tools/test_store.py::test_special_dates_note` | passa |
| PIX + cartão só acima de R$ 2.000,00 | `tests/tools/test_policy_tool.py::test_pagamento_allows_pix_plus_card_above_two_thousand` | passa |
| Instrumento de grande porte: frete especial com cotação | `tests/tools/test_policy_tool.py::test_frete_mentions_special_freight_for_large_instruments` | passa |
| Mensagem com duas perguntas | `tests/agent/test_prompt.py::test_answers_every_question_of_a_mixed_message` | passa |

## FRs da história

| FR | Evidência |
|---|---|
| FR-001 (tom e fluxo) | `test_prompt.py` (persona, fluxo em ordem, apresentação, nome) |
| FR-002 (só o manual; senão, "não tenho") | `test_policies.py`, `test_policy_tool.py`, `test_prompt.py` |
| FR-003 (aberta agora) | `test_business_hours.py`, `test_store.py` |
| FR-016 (parte da US1: regra e canal) | `test_policy_tool.py` (S-14), `test_prompt.py` (compra online) |
| FR-021 (fora do expediente, quando volta) | `test_business_hours.py::test_describe_next_opening`, `test_store.py::test_closed_now_reports_the_next_opening` |

## Revisão crítica do diff

- `git diff eb76cbc..714d85b -- tests`: só inclusões (66 linhas em `test_prompt.py` e `test_policy_tool.py`); nenhum teste removido, pulado ou afrouxado.
- Os testes de `eb76cbc` não cobriam os cenários 4 e 5 nem três casos de borda; eles foram acrescentados em `13abf81` antes de a história ser dada como concluída.
- Limite conhecido: o tom de voz (FR-001) é conferido pelo conteúdo do prompt; o comportamento com o modelo real entra na avaliação (US6) e nas conversas de exemplo (T059).
