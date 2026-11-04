# Validação — US2 Catálogo, preço e disponibilidade

**Commits da história**: `5774217` (testes), `5de7bfb` (implementação)
**Gates**: `uv run ruff check .` sem erros; `uv run ruff format --check .` sem pendência; `uv run pytest` com 277 testes passando (151 nos arquivos da US2), sem rede e sem chave.

## Cenários de aceite → testes

| # | Cenário (Dado/Quando/Então) | Teste que cobre | Resultado |
|---|---|---|---|
| 1 | Takamine GD20 sem promoção: preço de tabela R$ 2.199,00, PIX R$ 2.089,05 e maior parcelamento | `tests/tools/test_find_product.py::test_product_95_prices_installments_and_ended_promotion` (R$ 2.199,00, R$ 2.089,05, 12x de R$ 183,25), `tests/unit/test_pricing.py::test_without_promotion_pix_is_list_price_minus_five_percent`, `tests/unit/test_installments.py::test_2199_allows_twelve_installments_of_183_25`, `tests/agent/test_catalog_flow.py::test_find_product_runs_inside_the_graph` | passa |
| 2 | Promoção ativa: preço original, percentual, preço promocional; PIX não se soma | `tests/tools/test_find_product.py::test_product_90_shows_original_price_percent_and_promotional_price` (R$ 2.399,00, 18%, R$ 1.967,18, "não se soma"), `tests/unit/test_pricing.py::test_with_active_promotion_final_price_is_list_minus_percent_and_pix_does_not_stack`, `tests/agent/test_catalog_flow.py::test_promotion_is_shown_with_original_price_and_percent` | passa |
| 3 | Violões disponíveis até R$ 1.000: só ativos, com estoque e preço final no limite, cada um com preço | `tests/tools/test_query_catalog.py::test_violoes_up_to_1000_only_available_and_within_the_limit` (exclui o 96, confere o limite e a formatação), `tests/agent/test_catalog_flow.py::test_options_lists_only_available_products` | passa |
| 4 | Ativo sem estoque (96): temporariamente indisponível, com alternativas | `tests/tools/test_find_product.py::test_unavailable_products_have_own_reason_and_three_available_alternatives[...-96]`, `tests/unit/test_pricing.py::test_availability_follows_status_before_stock` (S-08) | passa |
| 5 | Descontinuado (136, com 13 em estoque): fora do catálogo, com equivalentes | `test_find_product.py::test_unavailable_products_have_own_reason_and_three_available_alternatives[...-136]`, `::test_discontinued_with_stock_is_not_available` (S-07) | passa |
| 6 | Em breve (130, com estoque): ainda não está à venda, sem confirmar disponibilidade, com alternativas | `test_find_product.py::test_unavailable_products_have_own_reason_and_three_available_alternatives[...-130]`, `::test_alternatives_are_the_closest_in_price`, `::test_unavailable_products_do_not_show_their_prices` (S-06, N-04) | passa |
| 7 | Promoção encerrada: informa que não está mais vigente e mostra o preço atual | `test_find_product.py::test_product_95_prices_installments_and_ended_promotion` ("Oferta Especial" listada como encerrada, preço atual R$ 2.199,00), `tests/unit/test_pricing.py::test_inactive_promotions_are_ignored` (S-13), `tests/agent/test_catalog_flow.py::test_ended_promotion_is_reported_with_transparency` | passa |
| 8 | Categoria sem produtos (sopros, cordas orquestrais): sem opções, indica contatos para encomenda | `tests/tools/test_catalog_view.py::test_categories_without_products_have_zero_available` (S-10), `tests/agent/test_catalog_flow.py::test_empty_category_points_to_the_store_contacts` | passa |
| 9 | Parcelamento: número máximo e valor pelas faixas da seção 3.1 | `tests/unit/test_installments.py` (fronteiras de cada faixa, 599 → 6x de R$ 99,83, cálculo sobre o preço promocional, opções de 1x ao máximo), `tests/tools/test_catalog_view.py::test_prices_and_installments_match_the_rules` | passa |

## Casos de borda da spec ligados à história

| Caso | Teste | Resultado |
|---|---|---|
| Nome com erro, sem acento ou parcial ("takamine gd 20") | `test_find_product.py::test_typo_and_spacing_tolerant_name_search_finds_the_95`, `::test_accent_is_ignored` | passa |
| Busca sem resultado: não inventa | `test_find_product.py::test_unknown_name_returns_empty_without_inventing` | passa |
| Muitos resultados: seleção curta | `test_find_product.py::test_at_most_three_candidates_and_the_total_is_reported`, `test_catalog_flow.py::test_short_selection_when_there_are_many_results`, `test_query_catalog.py::test_at_most_twenty_rows` | passa |

## Travas do text-to-SQL (D-04, D-08, D-09, D-09a, S2-05)

| Trava | Teste |
|---|---|
| Só SELECT, uma instrução, sem comentários, só as visões | `tests/unit/test_sql_guard.py::test_rejects_writes_other_tables_multiple_statements_and_unknown_functions` (21 casos) |
| Nenhuma conta nem agregação além de COUNT/MIN/MAX na lista do SELECT, inclusive em subconsulta e CTE | `test_sql_guard.py::test_rejects_arithmetic_and_other_functions_in_the_select_list` (18 casos) |
| `lower`, `upper`, `trim` aceitos no WHERE (observação da análise, rodada 2) | `test_sql_guard.py::test_accepts_safe_selects_on_the_views` |
| LIMIT imposto (máx. 20) | `test_sql_guard.py::test_limit_is_added_when_missing`, `::test_larger_limit_is_reduced` |
| Dinheiro formatado pela coluna de origem (MIN/MAX, apelido, `*`, `t.*`, subconsulta, CTE) | `tests/tools/test_query_catalog.py` (8 testes) |
| Tempo-limite e recuperação | `test_query_catalog.py::test_heavy_query_hits_the_timeout_and_the_tool_keeps_working` |
| Clientes inacessíveis na validação e na conexão | `test_query_catalog.py::test_reading_customers_fails_in_validation_and_in_the_connection` |

## Revisão crítica do diff

- `git diff 10c7cae..5de7bfb -- tests`: só inclusões (811 linhas em 8 arquivos); nenhum teste removido, pulado ou afrouxado.
- Durante a implementação, dois parâmetros de teste ainda não commitados foram trocados por serem expectativas mal formuladas, não por facilitarem a implementação: a busca "TAKAMINE" (empata entre os quatro Takamine, então não há como exigir o 95) virou "takamine gd20 dreadnought"; a busca "violao yamaha c40" virou "yamaha f310 aco", que testa o mesmo ponto (acento ignorado: o cadastro diz "Aço") sem misturar o tipo do instrumento no nome.
- Ponto que depende do modelo: em `query_catalog`, o filtro `availability = 'available'` é escrito pelo modelo. A garantia vem do prompt (testado) e dos casos de busca da avaliação (US6), como já registrado na análise de consistência.

## Suposições novas desta história (registradas no README)

- **N-01**: além de 135 e 136 (S-09), as descrições de 137, 139, 140, 142 e 144 citam outra marca e também não são repetidas.
- **N-02**: se um produto tiver mais de uma promoção ativa, vale só a de maior desconto (as promoções não são cumulativas). Não ocorre nos dados atuais.
- **N-03**: compra abaixo de R$ 50,00 só sai em 1x.
- **N-04**: o preço de produto indisponível (sem estoque, descontinuado ou em breve) não é informado; o agente mostra as alternativas com preço.
- **N-05**: a validação do SQL recusa também literais, `CASE`, `CAST`, `UNION` e comentários, por leitura conservadora de D-08 e S2-05.
