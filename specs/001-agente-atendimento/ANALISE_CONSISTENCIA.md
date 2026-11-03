# Análise de consistência — 001-agente-atendimento (rodada 2)

**Data**: 2026-11-03 | **Base**: commit `1e1422e` da branch `001-agente-atendimento` ("Corrige divergências da análise de consistência")
**Artefatos**: `spec.md` (25 FRs, 6 histórias, S-01 a S-18), `plan.md` (U-01 a U-05, D-01 a D-09, S2-01 a S2-12), `tasks.md` (T001 a T065), `constitution/constitution.md`, `constitution/stack.md` e `constitution/workflow.md`.
**Rodada anterior**: rodada 1, sobre o commit `be3e991`, com veredito BLOQUEADO e 7 divergências (D1 a D7).

## 1. Veredito

**BLOQUEADO: 1 divergência.**

As 7 divergências da rodada 1 foram resolvidas. A rastreabilidade mecânica continua limpa: 25 FRs, 65 tarefas e 0 achados objetivos (sem FR sem tarefa ou sem teste, ID duplicado, dependência inválida, história sem fase, clarificação aberta nem decisão sem dono). Resta uma divergência nova (N1), que nasce do encontro de duas correções desta rodada (D-08 e D-09) e se resolve com um ajuste pontual no `plan.md` e em T030/T035.

## 2. Situação das divergências da rodada 1

| # | Divergência | Situação | Evidência da correção |
|---|---|---|---|
| D1 | SQL do modelo podia fazer conta de dinheiro (princípio II) | **Resolvida** | Decisão D-08 (decidida pelo usuário): na lista do `SELECT`, inclusive em subconsultas e CTEs, só colunas puras, `*`, `COUNT`, `MIN` e `MAX`. S2-05 define as expressões permitidas no `WHERE`/`ORDER BY`/`GROUP BY`, sem aritmética. T027 recusa `final_price / 10`, `list_price * 0.85`, `pix_price - 50`, `SUM`, `AVG` e `ROUND`, com ou sem alias. T034 implementa a regra. A "Checagem de Constituição" do princípio II cita D-08. |
| D2 | Formato dos valores de `query_catalog` e ancoragem | **Resolvida**, com a ressalva de N1 | Decisão D-09: o SQL continua numérico e a ferramenta formata as colunas de dinheiro da saída. S2-02, a tabela de ferramentas, SC-002 (comparação literal, sem normalização), T030, T035 e T046 estão alinhados. |
| D3 | S-11 não valia para os dados | **Resolvida** | S-11 reescrita (o par pedido + e-mail é a prova; e-mail compartilhado dá acesso aos pedidos dos dois cadastros; nos dados só o 11 tem pedido). T038 testa o que dá para verificar (o e-mail compartilhado abre o pedido 10 e nenhum outro, com só o primeiro nome). O risco consta em "Riscos" no plan e nas limitações de T058. |
| D4 | Conjunto de avaliação incompleto | **Resolvida** | T051 passa a ter pelo menos um caso por tipo de pergunta, incluindo a categoria sem produtos (S-10, US2 cenário 8), o pedido de cancelar ou alterar um pedido (US4 cenário 4, FR-019, SC-004) e o caso pedido A → pedido B (FR-015). |
| D5 | Alternativas do descontinuado sem teste | **Resolvida** | FR-009 e US2 cenário 6 deixam explícito que todo indisponível (sem estoque, descontinuado ou em breve) recebe alternativas. A tabela de ferramentas do plan acompanha a mudança. T029 exige motivo próprio e 3 alternativas disponíveis para 96, 136 e 130. |
| D6 | Tempo-limite sem teste | **Resolvida** | S2-05 torna o limite configurável. T030 interrompe uma consulta pesada com o limite baixo, exige erro em texto e que a ferramenta continue respondendo. |
| D7 | `get_policy` sem teste da ferramenta | **Resolvida** | T065 (`tests/tools/test_policy_tool.py`) testa tópicos válidos, tópico fora da lista, notas S-03/S-14/S-16 e os contatos de `sobre_loja` (S-01, S-02). T023 passa a depender de T065. |

As observações da rodada 1 também foram tratadas: a garantia legal entrou em S-14, junto com a base da troca por defeito (manual 4.2 e 8.1); "nº 8" entrou em T038; o aviso de estimativa entrou em T039; o caso pedido A → pedido B entrou em T051.

## 3. Requisitos sem cobertura (Fases 1.1 e 1.3)

Nenhum. Todo FR tem tarefa e tarefa de teste. Na amostragem de qualidade, os cenários alterados nesta rodada (FR-009 e US2 cenários 5 e 6; FR-015; FR-019; S-10; S-11) têm teste que cobre o Dado/Quando/Então, e não só a citação do ID.

## 4. Tarefas órfãs (Fase 1.2)

Nenhuma. T065 tem `[US1]` e FRs citados. As tarefas de setup, fundação e polimento continuam rastreando a decisões do plan, ao FR-025, ao SC-005 ou aos gates de `constitution/workflow.md`.

## 5. Divergências de constituição e decisões sem dono (Fase 2)

Nenhuma. D-08 e D-09 estão na tabela "Decisões técnicas" com "Decidida por: usuário", e o cabeçalho do plan registra a revisão. A stack segue `constitution/stack.md`, a spec continua sem exceções, e o princípio II está agora garantido também para o SQL gerado.

## 6. Contradições entre artefatos (Fase 3)

- **N1. Valores de `MIN`/`MAX` e colunas com alias ficam sem formatação, e a ancoragem literal de SC-002 passa a reprovar respostas corretas.**
  - plan D-08 e S2-05 permitem `MIN` e `MAX` na lista do `SELECT`, e T027 aceita `MIN(final_price)` e `MAX(final_price)`. O próprio plan usa esse caso para justificar o SQL (D-03: "o mais barato de cada categoria"). D-08 também não proíbe alias em coluna pura (T027 trata alias só nas expressões recusadas).
  - plan S2-02 e T030 formatam a saída pelo nome da coluna: "formata as colunas `list_price`, `final_price`, `pix_price` e `installment_value` da saída" e "as demais colunas ficam como estão". Uma coluna de resultado chamada `MIN(final_price)`, `cheapest` ou `preco` (`SELECT final_price AS preco`) não tem um desses nomes e volta como número cru, por exemplo `1967.18`.
  - plan SC-002 diz que "todas as ferramentas formatam o dinheiro da mesma forma (S2-02, D-09)" e que "a comparação é literal, sem normalização"; T046 exige texto exato. Diante de um número cru, o modelo formata o valor por conta própria ("R$ 1.967,18"), o que contraria S2-02 ("Todas as ferramentas devolvem os valores já formatados"), e a ancoragem reprova uma resposta correta.
  - Ajuste sugerido (uma das opções, a registrar no plan): (a) formatar pela coluna de origem, e não pelo nome do resultado, o que cobre `MIN`/`MAX` sobre colunas de dinheiro e alias (o `sqlglot` permite resolver a origem de cada expressão do `SELECT`); ou (b) proibir alias sobre colunas de dinheiro e exigir que `MIN`/`MAX` de dinheiro usem alias igual ao nome da coluna. Nos dois casos, incluir em T030 uma consulta com `MIN(final_price)` agrupada por categoria e uma com alias, conferindo a saída formatada.

## 7. Pontos de atenção pedidos para esta feature

- **(a) Todo FR com tarefa de teste:** atendido (25/25), com a qualidade dos testes revisada nas tarefas alteradas.
- **(b) Verificação de identidade e isolamento dos dados de clientes:** atendidos. O arquivo de clientes não é aberto pela conexão do SQL (D-04, T006, T030). `get_order_status` exige pedido e e-mail em toda chamada e devolve só o primeiro nome (T038). A falha é indistinguível (FR-012, T038). Uma verificação que falha não deixa dado no thread (T039). O limite do e-mail compartilhado está documentado (S-11).
- **(c) Regras de preço em código e testadas:** atendidas em `rules/pricing.py` e `rules/installments.py` (T025, T026, T028), e o SQL do modelo não gera valor novo (D-08, T027). Ressalva de apresentação: N1.
- **(d) Travas do text-to-SQL:** atendidas. Somente leitura (`mode=ro`, `query_only`, T006, T012), uma única instrução `SELECT`, `LIMIT` de no máximo 20, só `v_products` e `v_categories`, lista fechada de expressões, tempo-limite testado (T027, T030) e arquivo separado como segunda camada (D-04).

## 8. Observações (não bloqueantes)

- **FR-005 ("listar só produtos disponíveis").** Em `query_catalog`, o filtro `availability = 'available'` continua dependendo do SQL do modelo. A garantia vem do prompt e dos casos de busca da avaliação (T051), o que é coerente com D-07.
- **Força bruta na verificação** e **e-mail compartilhado (S-11)**: limitações registradas no plan ("Riscos") e em T058. Não contrariam a spec.
- **Funções permitidas no `WHERE`** (`lower`, `upper`, `trim`): T027 testa as recusas na lista do `SELECT`, mas não que essas três funções sejam aceitas no `WHERE`. Vale incluir um caso ao implementar T027.
- **SC-004** continua sendo o único critério julgado por modelo (D-07, S2-11), registrado e justificado no plan.

## 9. Limitações da análise

- A análise lê os artefatos e os dados; não executa código (não há código nesta branch).
- O texto do manual foi conferido por extração automática do PDF (`pypdf`) nas seções 1, 3, 4, 6, 7 e 8; tabelas com quebra de linha não foram conferidas célula a célula.
- `constitution/governance.md` não foi lido, por escopo desta etapa.
