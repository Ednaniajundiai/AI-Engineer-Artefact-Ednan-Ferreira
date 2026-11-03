# Análise de consistência — 001-agente-atendimento (rodada 1)

**Data**: 2026-11-03 | **Base**: commit `be3e991` da branch `001-agente-atendimento`
**Artefatos**: `spec.md` (25 FRs, 6 histórias, S-01 a S-18), `plan.md` (U-01 a U-05, D-01 a D-07, S2-01 a S2-12), `tasks.md` (T001 a T064), `constitution/constitution.md`, `constitution/stack.md` e `constitution/workflow.md`.

## 1. Veredito

**BLOQUEADO: 7 divergências.**

A rastreabilidade mecânica está limpa: todo FR tem tarefa e tarefa de teste, não há ID duplicado, dependência inválida, história sem fase, clarificação aberta nem decisão sem dono. As divergências estão na qualidade de alguns testes, numa brecha da trava do text-to-SQL contra o princípio II, numa ambiguidade do plan sobre o formato dos valores e numa regra de suposição (S-11) que os dados não sustentam. Nenhuma exige mudar a arquitetura: todas se resolvem com ajustes pontuais no `spec.md`, no `plan.md` e no `tasks.md`.

| # | Tipo | Onde | Severidade |
|---|---|---|---|
| D1 | Desvio não registrado (princípio II) | plan S2-05; tasks T027, T034 | alta |
| D2 | Contradição entre artefatos | plan S2-02 × modelo de dados de `v_products`; tasks T030, T046 | média |
| D3 | Contradição spec × dados × teste | spec S-11; tasks T038 | média |
| D4 | Desvio da Definition of Done (conjunto de avaliação) | tasks T051; spec US4-4, US2-8 | média |
| D5 | Teste insuficiente | FR-009 / spec US2-5; tasks T029 | baixa |
| D6 | Trava sem teste | plan S2-05 (tempo-limite); tasks T027, T034 | baixa |
| D7 | Ferramenta sem teste próprio (Definition of Done) | `get_policy`; tasks T017, T023 | baixa |

## 2. Requisitos sem cobertura (Fases 1.1 e 1.3)

Nenhum FR sem tarefa e nenhum FR sem tarefa de teste: o script de rastreabilidade (`rastrear.sh`) encontrou 25 FRs e 64 tarefas, com 0 achados objetivos. Na amostragem da qualidade dos testes:

- **D5. FR-009 / US2 cenário 5 (alternativas para o descontinuado) [TESTE INSUFICIENTE].** FR-009 diz "Para os indisponíveis, DEVE sugerir alternativas semelhantes disponíveis", e o cenário 5 da História 2 exige que o descontinuado venha com "modelos equivalentes disponíveis, mesmo que o cadastro ainda mostre unidades em estoque". T029 só testa as alternativas no produto 96 (ativo sem estoque); para o 136 verifica apenas que "aparece como fora do catálogo", e para o 130 apenas que aparece "como em breve". O cenário principal do caso de borda S-07 (descontinuado com estoque, onde a falha mais provável é tratar o produto como disponível e não sugerir nada) fica sem teste. Ajuste sugerido em T029: exigir alternativas disponíveis da mesma categoria também para o 136 e decidir, de forma explícita na spec, se o "em breve" (130) também recebe alternativas.

Pontos amostrados e considerados cobertos: FR-006/FR-007/FR-008 (T025, T026, T028, T029, com valores conferidos contra os CSVs: 95 → R$ 2.199,00, PIX R$ 2.089,05, 12x de R$ 183,25; 90 → 18% ativo, "Desconto Exclusivo"); FR-011/FR-012 (T038: mesma resposta `not_found` para e-mail errado e pedido inexistente); FR-013 (T006, T027, T030, T038, T039); FR-020/FR-021 (T016, T018, T052); FR-022 (T007, T008).

## 3. Tarefas órfãs (Fase 1.2)

Nenhuma. As 16 tarefas sem `[USn]` nem FR citado (T001 a T003, T009 a T015, T058 a T060, T062 a T064) rastreiam a decisões do `plan.md` (U-01, D-01, D-06, S2-02, S2-03, S2-06, S2-07, S2-09, S2-10), ao FR-025, ao SC-005 ou aos gates e à checagem de segurança de `constitution/workflow.md`.

## 4. Divergências de constituição e decisões sem dono (Fase 2)

Stack: o plan segue `constitution/stack.md` (Python 3.11+, `uv`, LangChain/LangGraph, Claude via API da Anthropic, SQLite gerado dos CSVs e só leitura, PDF como fonte das políticas, CLI, `ruff` e `pytest`). As dependências extras estão justificadas (princípio VII). Todas as decisões da tabela "Decisões técnicas" têm "Decidida por". A spec declara "Sem exceções", e o plan não introduz desvio de stack.

- **D1. O SQL escrito pelo modelo pode fazer conta de dinheiro [DESVIO NÃO REGISTRADO, princípio II].**
  - Princípio II (INEGOCIÁVEL): "Preço final, desconto do PIX, aplicação de promoção, parcelamento e qualquer outra conta de dinheiro são calculados de forma determinística em código [...]. O modelo apresenta o resultado; ele não faz a conta."
  - plan S2-05 limita a consulta a "uma única instrução `SELECT`, só as visões permitidas, sem `PRAGMA`/`ATTACH` nem funções fora da lista". Operadores aritméticos não são funções: `SELECT name, final_price / 10 AS parcela FROM v_products` ou `SELECT list_price * 0.85 ...` passam na validação descrita. A fórmula é do modelo, e o resultado contorna as faixas de FR-008 e a regra de não acumular PIX com promoção (FR-006). Agregações que geram valor novo (`SUM`, `AVG`) caem no mesmo caso se estiverem na lista de funções; o plan não diz quais funções a lista contém.
  - A verificação de ancoragem de SC-002 (plan, "Avaliação"; T046) não pega o caso, porque o valor derivado aparece numa saída de ferramenta (`query_catalog`).
  - T027 testa comandos de escrita, várias instruções, tabelas e funções fora da lista, mas não expressões aritméticas sobre colunas de dinheiro. A "Checagem de Constituição" do plan marca o princípio II como ✅ sem tratar o SQL gerado.
  - Ajuste sugerido: no plan S2-05, proibir aritmética e agregações que produzam novos valores sobre `list_price`, `final_price`, `pix_price` e `installment_value` (mantendo `MIN`/`MAX`, `ORDER BY` e comparações, necessários para "o mais barato" e "até R$ 1.000"), ou proibir expressões calculadas na lista de seleção; incluir o caso em T027 e T034.

- **D4. O conjunto de avaliação não cobre todos os tipos de pergunta da feature [desvio da Definition of Done de `workflow.md`].**
  - `workflow.md`: "O conjunto fixo de perguntas de avaliação cobre cada tipo de pergunta que a feature trata, com a ferramenta e o desfecho esperados."
  - T051 lista os casos das US1 a US4, e T056 acrescenta os de reclamação. Ficam de fora: o pedido para cancelar ou alterar um pedido (US4 cenário 4, FR-019), que também entra na meta de SC-004 ("100% das perguntas fora do escopo"); e a busca por categoria sem produto cadastrado (US2 cenário 8, S-10, sopros e cordas orquestrais).
  - Ajuste sugerido: acrescentar os dois casos à lista de T051.

- **D6. O tempo-limite da consulta não tem teste [Definition of Done de `workflow.md`, item de regra/trava testada].** plan S2-05 inclui "um tempo-limite por `progress_handler`", implementado em T034, mas nenhuma tarefa de teste o verifica (T027 cobre só a validação sintática). Ajuste sugerido: incluir em T027 ou T030 uma consulta que estoure o limite (ex.: CTE recursiva) e devolva erro em texto, sem travar a ferramenta.

- **D7. `get_policy` não tem teste da ferramenta [Definition of Done de `workflow.md`: "Toda ferramenta que o agente pode chamar tem teste da ferramenta em si, sem o modelo"].** T017 testa a extração do PDF (`data/policies.py`) em `tests/unit/test_policies.py`; T023 implementa `tools/policies.py` (`get_policy`, com `topic` restrito) e depende só de T021, sem tarefa de teste própria. Todas as outras ferramentas têm teste em `tests/tools/` (T018, T029, T030, T038, T052). Ajuste sugerido: uma tarefa de teste para `get_policy` (tópicos válidos, tópico fora da lista e notas de interpretação na saída) da qual T023 dependa, ou a indicação explícita em T017 de que o teste é feito pela ferramenta.

Decisões sem dono: nenhuma.

## 5. Contradições entre artefatos (Fase 3)

- **D2. Formato dos valores devolvidos por `query_catalog`.**
  - plan S2-02: "As ferramentas devolvem os valores já formatados", e o plan, "Resumo": "o modelo só apresenta valores que chegam formatados pelas ferramentas".
  - plan, modelo de dados de `v_products`, e T030 (`final_price <= 1000`) exigem colunas numéricas, e `query_catalog` devolve "até 20 linhas" da visão. Nenhuma coluna formatada é prevista, então o modelo recebe `2089.05` e escreve "R$ 2.089,05".
  - T046 define a ancoragem como "todo `R$` da resposta aparece numa saída de ferramenta do turno" sem dizer como "R$ 2.089,05" casa com `2089.05`. Sem essa regra, ou SC-002 reprova respostas corretas, ou a normalização fica implícita no código (princípio V).
  - Ajuste sugerido: no plan, ou acrescentar colunas formatadas à visão (ou formatar a saída de `query_catalog` na ferramenta), ou registrar que `query_catalog` devolve números e que a ancoragem normaliza os dois formatos; refletir a escolha em T035 e T046.

- **D3. A regra de S-11 não vale para os dados e T038 não tem como demonstrá-la.**
  - spec S-11: "o pedido aponta para um cliente só, então o e-mail repetido não dá acesso ao pedido do outro". T038: "o e-mail repetido dos clientes 11 e 43 não abre o pedido do outro (S-11)".
  - Nos CSVs, só o cliente 11 tem pedido (o 10); o cliente 43 não tem nenhum. Como a verificação compara o e-mail informado com o e-mail do titular do pedido (FR-011, plan D-04), `bruno.martins@jmail.com` abre o pedido 10 para quem conhece esse e-mail, inclusive o titular do cadastro 43. A verificação identifica quem tem acesso ao e-mail, não a pessoa do cadastro. O teste descrito em T038 é vazio (não há "pedido do outro" a negar) ou contraria o desenho.
  - Ajuste sugerido: reescrever S-11 com a regra real (o par pedido + e-mail é a prova aceita; e-mail compartilhado entre cadastros dá acesso aos pedidos de qualquer um deles; nos dados atuais só o 11 tem pedido, então não há exposição de terceiro) e registrar o risco nas limitações do README; ajustar T038 para testar o que é verificável (o pedido 10 abre com o e-mail compartilhado e com nenhum outro; a saída traz só o primeiro nome).

## 6. Pontos de atenção pedidos para esta rodada

- **(a) Todo FR com tarefa de teste:** atendido no nível de rastreabilidade (25/25). Qualidade: ver D5 e D7.
- **(b) Verificação de identidade e isolamento:** atendidos no desenho. O modelo não abre o arquivo de clientes (D-04, T006, T030); `get_order_status` exige pedido e e-mail em toda chamada e devolve só o primeiro nome (T038); a falha é indistinguível (T038, FR-012); verificação que falha não deixa dado no thread (T039). Pendência: D3.
- **(c) Regras de preço em código e testadas:** atendidas em `rules/pricing.py` e `rules/installments.py` (T025, T026, T028), com a não cumulatividade PIX × promoção e as faixas da seção 3.1 conferidas contra o manual (3.1 e 6.2). Pendências: D1 (conta feita pelo SQL do modelo) e D2 (formato e ancoragem).
- **(d) Travas do text-to-SQL:** somente leitura (`mode=ro`, `query_only`, T006 e T012), SELECT único, `LIMIT` ≤ 20 e só `v_products`/`v_categories` (T027, T030), mais o arquivo separado como segunda camada (D-04). Pendências: D1 (aritmética) e D6 (tempo-limite sem teste).

## 7. Observações (não bloqueantes)

- **FR-015.** A spec diz "o agente pede a verificação de novo"; o plan garante a verificação por pedido em código (ferramenta sem estado) e manda o prompt confirmar o e-mail (T038, T039). A leitura é aceitável quanto ao dado: nenhum pedido abre sem o par certo. Falta um caso de avaliação explícito "verificado no pedido A, pergunta pelo pedido B"; o item "um pedido verificado e outro não" de T051 pode ser escrito assim.
- **Data de referência da garantia legal.** O manual (8.1) conta os 90 dias "a partir da data de recebimento pelo cliente"; T037 usa a previsão de entrega, estendendo a regra de S-14, escrita para o arrependimento. A troca por defeito a partir da data do pedido segue o manual (4.2, "após a compra"). Convém citar a garantia em S-14 para o princípio V ficar explícito.
- **FR-005 ("listar só produtos disponíveis").** Em `query_catalog`, o filtro `availability = 'available'` depende do SQL do modelo; T030 testa uma consulta escrita pelo próprio teste. A garantia real vem do prompt e do caso "busca até R$ 1.000" da avaliação, o que é coerente com D-07.
- **Força bruta na verificação.** Sem limite de tentativas, registrado como limitação no plan ("Riscos") e em T058. Não contraria a spec.
- **Formatos de número de pedido.** A spec cita "nº 8" entre os casos de borda; T038 lista "#8", "pedido 8" e "8".
- **FR-016 ("dizendo que é uma estimativa").** Nenhum teste confere o aviso de estimativa; T039 pode incluí-lo na regra do prompt.
- **SC-004** é o único critério julgado por modelo (D-07, S2-11), registrado e justificado no plan.

## 8. Limitações da análise

- A análise lê os artefatos e os dados; não executa código (não há código nesta branch).
- O texto do manual foi conferido por extração automática do PDF (`pypdf`), suficiente para as seções 1, 3, 4, 6, 7 e 8; tabelas com quebra de linha não foram conferidas célula a célula.
- `constitution/governance.md` não foi lido, por escopo desta etapa.
