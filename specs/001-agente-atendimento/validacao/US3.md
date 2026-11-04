# Validação — US3 Status de pedido com verificação de identidade

**Commits da história**: `759edf1` (testes), `b3cbd37` (implementação)
**Gates**: `uv run ruff check .` sem erros; `uv run ruff format --check .` sem pendência; `uv run pytest` com 324 testes passando (47 nos arquivos da US3), sem rede e sem chave.

## Cenários de aceite → testes

| # | Cenário (Dado/Quando/Então) | Teste que cobre | Resultado |
|---|---|---|---|
| 1 | Sem número e e-mail, o agente pede os dois antes de consultar | `tests/agent/test_orders_flow.py::test_asks_number_and_email_before_any_lookup`; `tests/tools/test_orders.py::test_tool_requires_both_fields` (os dois campos são obrigatórios no esquema da ferramenta) | passa |
| 2 | Número e e-mail do mesmo cliente: status em português, data, itens, total registrado e, conforme o status, rastreio e previsão ou motivo do cancelamento | `tests/tools/test_orders.py::test_correct_number_and_email_show_the_order`, `::test_cancelled_order_shows_the_reason`, `::test_pending_and_confirmed_have_no_tracking`, `::test_registered_total_is_reported_without_recalculation` (pedidos 1, 3, 5, 10 e 20; S-04, S-05); `tests/agent/test_orders_flow.py::test_verified_order_reaches_the_model` | passa |
| 3 | Número e e-mail que não correspondem: "não localizei", sem dizer qual está errado e sem revelar dado | `tests/tools/test_orders.py::test_wrong_email_and_missing_order_give_the_same_answer` (e-mail errado, pedido inexistente e número ilegível dão a mesma resposta); `tests/agent/test_orders_flow.py::test_failed_verification_leaves_no_order_data_in_the_thread`, `::test_failed_verification_does_not_say_which_field_is_wrong` | passa |
| 4 | Enviado com previsão vencida (pedido 8): status, rastreio, aviso de previsão vencida e oferta de reclamação | `tests/tools/test_orders.py::test_overdue_forecast_on_order_8` (S-12), `::test_delivered_order_is_not_overdue`; `tests/agent/test_orders_flow.py::test_overdue_forecast_offers_a_complaint` | passa |
| 5 | Verificado para um pedido, pergunta por outro: nova verificação | `tests/tools/test_orders.py::test_each_call_verifies_again` (o e-mail do pedido 1 não abre o 2); `tests/agent/test_orders_flow.py::test_confirms_the_email_again_for_another_order` | passa |
| 6 | Pedido de dados de outro cliente: recusa e explica que não compartilha dados pessoais | `tests/agent/test_orders_flow.py::test_never_reveals_third_party_data`; `tests/tools/test_orders.py::test_output_never_has_personal_data_beyond_the_first_name` (todos os 20 pedidos: sem e-mail, telefone, cidade nem nome completo); `tests/tools/test_query_catalog.py::test_reading_customers_fails_in_validation_and_in_the_connection` | passa |
| 7 | Entregue + arrependimento + compra online: previsão como recebimento, diz se os 7 dias valem e, se não, troca por defeito e garantia | `tests/unit/test_deadlines.py` (limites exatos de 7, 30 e 90 dias, estimativa, data injetada); `tests/tools/test_orders.py::test_delivered_order_brings_the_after_sale_deadlines` (01/11/2025, 14/11/2025, 23/01/2026, "estimativa", "encerrado"); `tests/agent/test_orders_flow.py::test_withdrawal_asks_the_channel_and_warns_the_date_is_an_estimate` | passa |

## Casos de borda e suposições

| Caso | Teste | Resultado |
|---|---|---|
| Número do pedido em formatos diferentes ("pedido 8", "#8", "nº 8") e e-mail com maiúsculas | `test_orders.py::test_order_number_formats`, `::test_invalid_order_numbers`, `::test_email_is_case_and_space_insensitive` | passa |
| Totais que não batem com os itens ou PIX sem desconto (S-04, S-05) | `test_orders.py::test_registered_total_is_reported_without_recalculation` | passa |
| E-mail compartilhado entre os clientes 11 e 43 (S-11) | `test_orders.py::test_shared_email_opens_only_the_order_of_customer_11` | passa |
| Produto "em breve" num pedido existente (S-06) | `test_orders.py::test_coming_soon_product_in_an_order_is_shown_to_the_owner` | passa |

## FRs da história

FR-011 (pede e verifica os dois dados), FR-012 (falha indistinguível), FR-013 (mínimo de dado pessoal), FR-014 (conteúdo por status), FR-015 (verificação por pedido), FR-016 (prazos de arrependimento, defeito e garantia): todos com os testes acima.

## Revisão crítica do diff

- `git diff 759edf1..b3cbd37 -- tests`: só a ordem de um import em `tests/agent/test_orders_flow.py` (o `ruff` passou a reconhecer `emporio.tools.orders` como módulo do projeto depois que ele existiu). Nenhum teste removido, pulado ou afrouxado.
- Isolamento: `get_order_status` lê só `orders.sqlite`; o nome do produto foi copiado para `order_items` na carga, para que a ferramenta não precise abrir o catálogo.
- Dependências do modelo: pedir os dois dados antes de chamar a ferramenta e recusar dados de terceiros dependem do prompt (testado). A ferramenta, por desenho, não responde nada sem o par correto, então mesmo um modelo que chame cedo demais não recebe dado.
- Limitações registradas no README: sem limite de tentativas de verificação; e-mail compartilhado dá acesso aos pedidos de qualquer cadastro com ele (S-11).
