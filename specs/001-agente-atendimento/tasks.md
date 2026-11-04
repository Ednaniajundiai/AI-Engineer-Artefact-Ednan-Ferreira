# Tasks: Agente de atendimento da Empório da Música

**Input**: `specs/001-agente-atendimento/spec.md` e `specs/001-agente-atendimento/plan.md`

**Testes**: todo FR tem ao menos uma tarefa de teste, escrita antes da
implementação e que deve falhar até ela existir (Definition of Done de
`constitution/workflow.md`). Os testes rodam sem rede e sem chave de API; onde o
modelo é necessário, usa-se o modelo simulado de `tests/fakes.py`.

**Organização**: as tarefas são agrupadas por história de usuário, na ordem do
plan: Fundação → US1 → US2 → US3 → US4 → US6 → US5 → Polimento. Um commit por
história, ao fechar o checkpoint.

## Formato: `[ID] [P?] [História] Descrição`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência)
- **[História]**: história de usuário da tarefa (US1, US2...)

## Fase 1: Setup (Infraestrutura Compartilhada)

- [x] T001 Criar `pyproject.toml` com `uv`: Python >= 3.11; as dependências do plan (`langgraph`, `langchain-core`, `langchain-anthropic`, `pypdf`, `sqlglot`, `rapidfuzz`, `python-dotenv`, `pyyaml`, `tzdata`); `pytest` e `ruff` como dependências de desenvolvimento; os comandos `emporio` (CLI) e `emporio-eval`; e a configuração de `ruff` e `pytest`. Gerar o `uv.lock`.
- [x] T002 [P] Criar `.env.example` com `ANTHROPIC_API_KEY`, `MODEL_NAME=claude-sonnet-5-5` e `JUDGE_MODEL_NAME=claude-haiku-5-5`, e acrescentar `var/` e `registros/` ao `.gitignore`.
- [x] T003 [P] Criar o esqueleto do pacote `src/emporio/` (`__init__.py` em `data/`, `rules/`, `tools/`, `agent/` e `evaluation/`) e as pastas `tests/unit/`, `tests/tools/` e `tests/agent/` com o `conftest.py`.

## Fase 2: Fundação (Bloqueante)

**⚠️ CRÍTICO**: nenhuma história de usuário começa antes desta fase terminar.

### Testes da Fundação

- [x] T004 [P] Teste de `money` em `tests/unit/test_money.py`: arredondamento `ROUND_HALF_UP` para centavos (569,905 → 569,91) e formatação `R$ 1.234,56` (plan S2-02, base de FR-006 e FR-008).
- [x] T005 [P] Teste de `normalize` em `tests/unit/test_normalize.py`: o nome normalizado remove acento, caixa, espaços e hífens; todo produto dos CSVs recebe uma marca da lista fechada (plan S2-06 e S2-07, base de FR-005).
- [x] T006 [P] Teste da carga em `tests/tools/test_loader.py`: gera `var/catalog.sqlite` e `var/orders.sqlite` numa pasta temporária; o arquivo do catálogo não contém as tabelas `customers`, `orders` nem `order_items`; escrever pelas conexões de leitura levanta erro; os arquivos de `data/` ficam com o hash inalterado; a carga é refeita quando um CSV é mais novo que o SQLite (FR-013, plan D-04 e S2-09).
- [x] T007 [P] Teste do grafo em `tests/agent/test_graph.py` com o modelo simulado: uma chamada de ferramenta seguida da resposta final; no mesmo thread, a segunda mensagem enxerga a primeira; um thread novo começa vazio (FR-022, plan D-01 e D-06).
- [x] T008 [P] Teste da CLI em `tests/agent/test_cli.py` com o modelo simulado e entrada roteirizada: `/nova` troca o thread, `/sair` encerra, `--transcricao` grava a conversa em markdown e `--debug` mostra o nome das ferramentas chamadas (FR-022, plan S2-10).

### Implementação da Fundação

- [x] T009 [P] Implementar `src/emporio/money.py` (depende de T004).
- [x] T010 [P] Implementar `src/emporio/data/normalize.py` (depende de T005).
- [x] T011 Implementar `src/emporio/config.py`: caminhos (`data/`, `var/`, `registros/`, `evals/`), leitura do `.env`, `MODEL_NAME` e um relógio injetável no fuso `America/Campo_Grande` (plan S2-03).
- [x] T012 Implementar `src/emporio/data/loader.py` com as tabelas-base dos dois SQLite, os índices e as funções de conexão só leitura (`mode=ro` e `PRAGMA query_only=ON`) (depende de T006, T010 e T011).
- [x] T013 [P] Implementar `tests/fakes.py`: um modelo de chat simulado, roteirizado por uma lista de `AIMessage` (com ou sem `tool_calls`), compatível com `bind_tools`.
- [x] T014 Implementar `src/emporio/agent/prompt.py` (bloco de persona e bloco de data/hora local) e `src/emporio/agent/graph.py` (`StateGraph` modelo → `ToolNode` → modelo com `tools_condition`, `InMemorySaver`, registro de ferramentas e modelo injetável), conferindo os nomes da API na versão instalada (depende de T007, T011 e T013).
- [x] T015 Implementar `src/emporio/cli.py` com o laço de conversa, `/nova`, `/sair`, `--debug` e `--transcricao` (depende de T008 e T014).

**Checkpoint**: a carga gera os dois bancos e a CLI conversa com o modelo simulado. Commit da Fundação.

## Fase 3: História de Usuário 1 - Informações da loja e políticas (Prioridade: P1) 🎯 MVP

**Objetivo**: responder endereço, contatos, horário (inclusive "está aberto agora?") e cada política do manual, no tom da loja.

**Teste Independente**: com o relógio fixo, perguntar endereço, horário e cada tópico de política e conferir com o manual.

### Testes para a História 1 ⚠️

- [x] T016 [P] [US1] Teste de `business_hours` em `tests/unit/test_business_hours.py`: aberto e fechado em dias úteis (8h59, 9h, 17h59, 18h), sábado (12h59 e 13h), domingo fechado e a próxima abertura a partir de sexta à noite, sábado à tarde e domingo, no fuso de Campo Grande (FR-003, FR-021, FR-024).
- [x] T017 [P] [US1] Teste de `policies` em `tests/unit/test_policies.py`: a extração do PDF gera todos os tópicos do plan; cada tópico contém os fatos-chave (horário 09:00 às 18:00; faixas de R$ 50, R$ 80 e R$ 100; 7 dias para arrependimento, 30 para defeito e 90 de garantia legal; frete grátis acima de R$ 500,00; prazo de 24 horas úteis); as notas S-03, S-14, S-15 e S-16 aparecem nos tópicos certos; um tópico desconhecido devolve erro claro (FR-002, FR-016).
- [x] T018 [P] [US1] Teste de `get_store_info` em `tests/tools/test_store.py`: telefone (67) 3341-4444 e WhatsApp (67) 3321-4500 com rótulo (S-01); e-mail `contato@emporiodamusica.com.br`, sem acento (S-02); "aberta agora" e a próxima abertura com o relógio fixo; o aviso de que a loja fecha nos feriados, sem afirmar datas (S-15) (FR-002, FR-003, FR-021).
- [x] T019 [P] [US1] Teste do prompt em `tests/agent/test_prompt.py`: o prompt montado contém a persona em português (informal, mas profissional), o fluxo saudação → entendimento → consulta → resposta → fechamento, a apresentação como assistente virtual, o cumprimento pelo nome quando o cliente o informa, a data e a hora locais e a regra de dizer "não tenho essa informação" e indicar os contatos quando o manual não cobre o assunto (FR-001, FR-002).
- [x] T065 [P] [US1] Teste da ferramenta `get_policy` em `tests/tools/test_policy_tool.py`, sem o modelo: cada tópico válido devolve o texto das seções certas e as notas de interpretação desse tópico (S-03 em parcelamento, S-14 em trocas_devolucoes e garantia, S-16 em atendimento); um tópico fora da lista é recusado com mensagem clara; a saída de sobre_loja traz o e-mail sem acento e os dois telefones com rótulo, e não o e-mail acentuado da seção 1.2 (S-01, S-02) (FR-002, FR-008, FR-016).

### Implementação da História 1

- [x] T020 [P] [US1] Implementar `src/emporio/rules/business_hours.py` (depende de T016).
- [x] T021 [P] [US1] Implementar `src/emporio/data/policies.py`: extração com `pypdf`, recorte pelos títulos `N.` e `N.N`, mapeamento das seções para os tópicos e as notas de interpretação (depende de T017).
- [x] T022 [US1] Implementar `src/emporio/tools/store.py` (`get_store_info`) (depende de T018 e T020).
- [x] T023 [US1] Implementar `src/emporio/tools/policies.py` (`get_policy`, com `topic` restrito aos valores do plan) (depende de T021 e T065).
- [x] T024 [US1] Completar os blocos 1, 2 e 4 do prompt em `src/emporio/agent/prompt.py` e registrar `get_store_info` e `get_policy` em `src/emporio/agent/graph.py` (depende de T019, T022 e T023).

**Checkpoint**: a História 1 funciona sozinha pela CLI. Rodar os gates e commitar a US1.

---

## Fase 4: História de Usuário 2 - Catálogo, preço e disponibilidade (Prioridade: P1)

**Objetivo**: busca de instrumentos por nome, tipo, marca e preço, com preço de tabela, promoção, PIX, parcelamento e disponibilidade corretos.

**Teste Independente**: conferir as ferramentas de catálogo contra os valores calculados pelas regras, sem o modelo.

### Testes para a História 2 ⚠️

- [x] T025 [P] [US2] Teste de `pricing` em `tests/unit/test_pricing.py`: com promoção ativa, o preço final é o de tabela menos o percentual e o PIX não se soma; sem promoção, o PIX é o de tabela − 5%; promoção inativa é ignorada (S-13); disponibilidade nos quatro estados, incluindo os produtos 130 (`coming_soon` com estoque, S-06), 136 (`discontinued` com estoque, S-07) e 96 (ativo sem estoque, S-08) (FR-006, FR-007, FR-009, FR-010, FR-024).
- [x] T026 [P] [US2] Teste de `installments` em `tests/unit/test_installments.py`: faixas da seção 3.1 (S-03); R$ 599,00 → máximo de 6x de R$ 99,83; R$ 2.199,00 → 12x de R$ 183,25; os valores na fronteira de cada faixa; o cálculo sobre o preço promocional quando houver promoção ativa; a lista de opções de 1x até o máximo (FR-008, FR-024).
- [x] T027 [P] [US2] Teste de `sql_guard` em `tests/unit/test_sql_guard.py`: aceita `SELECT` em `v_products` e `v_categories`; recusa `INSERT`, `UPDATE`, `DELETE`, `DROP`, `PRAGMA`, `ATTACH`, várias instruções, comentários que escondem uma segunda instrução, tabelas fora da lista (`products`, `customers`, `sqlite_master`) e funções fora da lista; recusa na lista do `SELECT`, inclusive em subconsulta e CTE, qualquer operador aritmético (`final_price / 10`, `list_price * 0.85`, `pix_price - 50`), `SUM`, `AVG`, `ROUND` e outras funções, com ou sem alias (plan D-08); aceita colunas puras, `*`, `COUNT`, `MIN(final_price)`, `MAX(final_price)`, comparações no `WHERE`/`ORDER BY` (`final_price <= 1000`) e as funções `lower`, `upper` e `trim` no `WHERE` (`lower(brand) = 'yamaha'`, `trim(category) LIKE 'Viol%'`); impõe `LIMIT` de no máximo 20, reduzindo um limite maior (FR-004, FR-006, FR-008, FR-013).
- [x] T028 [US2] Teste da tabela materializada em `tests/tools/test_catalog_view.py`: para todo produto, `final_price`, `pix_price`, `max_installments` e `installment_value` são iguais aos das regras; `availability` bate com `pricing`; `description` é nula para 135 e 136 (S-09); `v_categories` traz 0 produtos disponíveis para sopros e cordas orquestrais (S-10) (FR-006, FR-008, FR-009) (depende de T025 e T026).
- [x] T029 [US2] Teste de `find_product` em `tests/tools/test_find_product.py`: "takamine gd 20" encontra o produto 95, com R$ 2.199,00, PIX R$ 2.089,05 e 12x de R$ 183,25, e lista a promoção encerrada "Oferta Especial" (FR-010); o produto 90 mostra o preço original, 18% e o preço promocional, com o PIX igual ao promocional (FR-007); os produtos 96 (sem estoque), 136 (descontinuado com estoque, S-07) e 130 (em breve com estoque, S-06) aparecem como indisponíveis, cada um com o motivo próprio (temporariamente sem estoque, fora do catálogo, ainda não à venda) e com 3 alternativas disponíveis da mesma categoria, nenhuma delas indisponível; um nome sem correspondência devolve lista vazia, sem inventar (FR-005, FR-006, FR-007, FR-009, FR-010).
- [x] T030 [US2] Teste de `query_catalog` em `tests/tools/test_query_catalog.py`: a consulta de violões disponíveis até R$ 1.000 devolve só produtos com `availability = 'available'` e `final_price <= 1000`; na saída, todo valor cuja coluna de origem seja `list_price`, `final_price`, `pix_price` ou `installment_value` vem formatado em `R$` pela mesma função de `money`, e as demais colunas ficam como estão (plan D-09 e D-09a); `SELECT category, MIN(final_price) FROM v_products GROUP BY category` devolve o mínimo de cada categoria formatado em `R$`, igual ao menor `final_price` da categoria calculado pelas regras (para violões, R$ 429,90, do produto 83); `SELECT name, final_price AS preco FROM v_products` devolve `preco` formatado em `R$`; `SELECT *` formata as quatro colunas de dinheiro; `COUNT(*)` e `stock` continuam numéricos; um SQL inválido volta como texto de erro, sem exceção; com o tempo-limite configurado bem baixo, uma consulta válida e pesada (junção da visão consigo mesma) é interrompida e volta como texto de erro, e a ferramenta continua respondendo à consulta seguinte (plan S2-05); uma tentativa de ler `customers` falha na validação e também na conexão (o arquivo não tem a tabela) (FR-004, FR-005, FR-013).

### Implementação da História 2

- [x] T031 [P] [US2] Implementar `src/emporio/rules/pricing.py` (depende de T009 e T025).
- [x] T032 [P] [US2] Implementar `src/emporio/rules/installments.py` (depende de T009 e T026).
- [x] T033 [US2] Acrescentar em `src/emporio/data/loader.py` a tabela `catalog_products` e as visões `v_products` e `v_categories`, como no modelo de dados do plan (depende de T012, T028, T031 e T032).
- [x] T034 [P] [US2] Implementar `src/emporio/tools/sql_guard.py` com `sqlglot`, a lista de visões permitidas, a regra da lista do `SELECT` (só colunas, `*`, `COUNT`, `MIN` e `MAX`, plan D-08), as expressões permitidas no `WHERE`/`ORDER BY`/`GROUP BY`, o `LIMIT` imposto e o tempo-limite configurável por `progress_handler` (depende de T027).
- [x] T035 [US2] Implementar `src/emporio/tools/catalog.py` (`find_product` com `rapidfuzz` e alternativas para todo indisponível; `query_catalog` com o esquema das visões e a regra de D-08 na descrição da ferramenta, e os valores de dinheiro da saída formatados em `R$` pela coluna de origem, resolvida com o `sqlglot` através de apelidos, `MIN`/`MAX`, subconsultas, CTEs e `*`, plan D-09 e D-09a) (depende de T029, T030, T033 e T034).
- [x] T036 [US2] Acrescentar ao prompt o guia das ferramentas de catálogo e a regra de copiar os valores sem recalcular; registrar `find_product` e `query_catalog` no grafo (depende de T035).

**Checkpoint**: as Histórias 1 e 2 funcionam pela CLI. Rodar os gates e commitar a US2.

---

## Fase 5: História de Usuário 3 - Status de pedido com verificação de identidade (Prioridade: P2)

**Objetivo**: mostrar o andamento do pedido só quando o número e o e-mail pertencem ao mesmo cliente, com os prazos de troca e arrependimento calculados em código.

**Teste Independente**: consultar pedidos de todos os status com dados corretos e incorretos e conferir que nada aparece sem verificação.

### Testes para a História 3 ⚠️

- [x] T037 [P] [US3] Teste de `deadlines` em `tests/unit/test_deadlines.py`: arrependimento de 7 dias corridos a partir da previsão de entrega (S-14), troca por defeito de 30 dias a partir da data do pedido, garantia legal de 90 dias a partir da previsão de entrega, o limite exato de cada prazo e a data de referência injetada (FR-016, FR-024).
- [x] T038 [US3] Teste de `get_order_status` em `tests/tools/test_orders.py`: número e e-mail corretos devolvem status em português, data, itens, total registrado e rastreio; o e-mail é comparado sem diferenciar caixa e sem espaços; "#8", "nº 8", "pedido 8" e "8" são aceitos; e-mail errado e pedido inexistente devolvem a mesma resposta `not_found`, sem detalhe (FR-012); o e-mail compartilhado `bruno.martins@jmail.com` (clientes 11 e 43) abre o pedido 10, do cliente 11, e nenhum outro pedido, e a saída traz só o primeiro nome do titular do pedido (S-11); o pedido 8 vem com `forecast_overdue` (S-12); um cancelado traz o motivo; os pedidos 1, 3, 5, 10 e 20 trazem o total registrado sem recálculo (S-04, S-05); a saída nunca contém e-mail, telefone, cidade nem nome completo; cada chamada verifica de novo (FR-011, FR-012, FR-013, FR-014, FR-015, FR-016) (depende de T037).
- [x] T039 [US3] Teste do prompt e do grafo em `tests/agent/test_orders_flow.py`: o prompt contém a regra de pedir o número e o e-mail antes da consulta, de confirmar o e-mail para outro pedido, de nunca revelar dados de terceiros, de perguntar o canal de compra no caso de arrependimento e de avisar que a data de recebimento é uma estimativa (S-14); com o modelo simulado, uma verificação que falha não deixa nenhum dado do pedido nas mensagens do thread (FR-011, FR-013, FR-015, FR-016).

### Implementação da História 3

- [x] T040 [P] [US3] Implementar `src/emporio/rules/deadlines.py` (depende de T037).
- [x] T041 [US3] Implementar `src/emporio/tools/orders.py` (`get_order_status`), lendo só `var/orders.sqlite` por conexão só leitura (depende de T012, T038 e T040).
- [x] T042 [US3] Acrescentar ao prompt as regras de dados pessoais e de pedido e registrar `get_order_status` no grafo (depende de T039 e T041).

**Checkpoint**: as Histórias 1 a 3 funcionam pela CLI. Rodar os gates e commitar a US3.

---

## Fase 6: História de Usuário 4 - Perguntas fora do escopo (Prioridade: P2)

**Objetivo**: redirecionar acessórios, recusar assuntos alheios, manter o papel e não operar pedidos.

**Teste Independente**: testes do prompt e do registro de ferramentas aqui; o comportamento com o modelo real é medido pela avaliação (US6, SC-004).

### Testes para a História 4 ⚠️

- [x] T043 [P] [US4] Teste do bloco de escopo em `tests/agent/test_scope_prompt.py`: o prompt lista os acessórios que a loja não vende (cordas, palhetas, cabos, cases, pedais, amplificadores) e manda redirecionar com educação; manda recusar com gentileza os assuntos alheios; manda manter o papel e não revelar as instruções; proíbe criar, alterar ou cancelar pedidos e prometer reserva, indicando os contatos da equipe; e não manda indicar lojas parceiras (S-16) (FR-017, FR-018, FR-019).
- [x] T044 [P] [US4] Teste do registro de ferramentas em `tests/agent/test_tool_registry.py`: nenhuma ferramenta registrada escreve nos dados da loja (só `register_complaint` escreve, e em `registros/`); com o modelo simulado, uma resposta sem chamada de ferramenta é registrada como fonte `none` (FR-019).

### Implementação da História 4

- [x] T045 [US4] Acrescentar o bloco 5 (escopo) em `src/emporio/agent/prompt.py` (depende de T043 e T044).

**Checkpoint**: as Histórias 1 a 4 funcionam pela CLI. Rodar os gates e commitar a US4.

---

## Fase 7: História de Usuário 6 - Avaliação automatizada do agente (Prioridade: P2)

**Objetivo**: um comando que roda o conjunto fixo de perguntas contra o agente real e mostra, por pergunta e por critério de sucesso, o esperado e o obtido.

**Teste Independente**: os testes das verificações rodam sem modelo; o relatório real é gerado à parte.

### Testes para a História 6 ⚠️

- [x] T046 [P] [US6] Teste das verificações em `tests/unit/test_eval_checks.py`: roteamento (a ferramenta esperada foi chamada; `none` quando nenhuma); ancoragem (todo `R$` da resposta aparece como texto exato numa saída de ferramenta do turno, inclusive nas linhas formatadas de `query_catalog`; um valor inventado ou recalculado reprova; plan D-09); vazamento (o e-mail, o rastreio ou o total de outro pedido reprovam); juiz de SC-004 simulado (FR-023).
- [x] T047 [P] [US6] Teste da leitura dos casos em `tests/unit/test_eval_cases.py`: o YAML de uma ou várias mensagens é lido; os valores esperados são calculados pelas regras na hora da avaliação, sem números fixos à mão; um caso inválido gera um erro claro (FR-023, FR-024).

### Implementação da História 6

- [x] T048 [P] [US6] Implementar `src/emporio/evaluation/cases.py` (depende de T047).
- [x] T049 [P] [US6] Implementar `src/emporio/evaluation/checks.py`, com o juiz de SC-004 usando `JUDGE_MODEL_NAME` e uma rubrica de sim/não (depende de T046).
- [x] T050 [US6] Implementar `src/emporio/evaluation/runner.py` e o comando `emporio-eval`: roda cada caso num thread novo, junta as chamadas de ferramenta e as respostas e grava `evals/reports/AAAA-MM-DD.md` com o resultado por caso e os totais de SC-001 a SC-004 (depende de T048 e T049).
- [x] T051 [US6] Escrever `evals/cases.yaml` com cerca de 30 casos, ao menos um por tipo de pergunta das US1 a US4: horário, endereço, cada política e o arrependimento; os preços de 95, 90 e 96; a busca até R$ 1.000; o 136 e o 130, com alternativas; uma promoção encerrada; a busca por uma categoria sem produtos (sopros ou cordas orquestrais, S-10, US2 cenário 8); um pedido verificado; uma verificação que falha; o cliente verificado no pedido A que pergunta pelo pedido B (FR-015); dados de outro cliente; um pedido para cancelar ou alterar um pedido (US4 cenário 4, FR-019, conta para SC-004); uma tentativa de mudar as instruções; acessórios; e um assunto alheio (FR-005, FR-015, FR-019) (depende de T050).

**Checkpoint**: `emporio-eval` roda de ponta a ponta. Rodar os gates e commitar a US6.

---

## Fase 8: História de Usuário 5 - Registro de reclamação (Prioridade: P3)

**Objetivo**: registrar a reclamação com protocolo e prazo de retorno, avisando quando a equipe volta se estiver fora do expediente.

**Teste Independente**: abrir reclamações completas e incompletas e conferir o arquivo gerado.

### Testes para a História 5 ⚠️

- [ ] T052 [P] [US5] Teste de `register_complaint` em `tests/tools/test_complaints.py`: protocolo no formato `REC-AAAAMMDD-XXXX`; uma linha JSONL por reclamação, gravada só em `registros/reclamacoes.jsonl`; recusa sem nome, contato ou descrição, informando o que falta; prazo de 24 horas úteis na resposta; fora do expediente (relógio fixo), a resposta traz quando a equipe volta (FR-020, FR-021).
- [ ] T053 [P] [US5] Teste do prompt em `tests/agent/test_complaint_prompt.py`: o prompt manda responder com empatia e pedir só o que falta entre nome, contato, descrição e número do pedido; com o modelo simulado, a reclamação registrada devolve o protocolo na resposta (FR-020).

### Implementação da História 5

- [ ] T054 [US5] Implementar `src/emporio/tools/complaints.py` (`register_complaint`) (depende de T020 e T052).
- [ ] T055 [US5] Acrescentar ao prompt o guia de reclamação e registrar `register_complaint` no grafo (depende de T053 e T054).
- [ ] T056 [US5] Acrescentar a `evals/cases.yaml` os casos de reclamação, um deles com o pedido 8 atrasado (S-12) (depende de T051 e T055).

**Checkpoint**: todas as histórias funcionam pela CLI. Rodar os gates e commitar a US5.

---

## Fase 9: Polimento e Preocupações Transversais

- [ ] T057 Teste dos entregáveis em `tests/test_deliverables.py`: o `README.md` tem as seções de instruções, decisões, suposições, limitações e uso de assistentes de código; `exemplos/` tem de 3 a 5 arquivos `.md`; o `.env.example` lista todas as variáveis lidas em `config.py` (FR-025).
- [ ] T058 Escrever o `README.md`: como instalar e rodar (`uv sync`, `.env`, `uv run emporio`, `uv run emporio-eval`, `uv run pytest`); as justificativas das decisões U-01 a U-05 e D-01 a D-09; a tabela de suposições S-01 a S-18; e as limitações e o que viria com mais tempo (sem limite de tentativas de verificação, e-mail compartilhado entre cadastros dá acesso aos pedidos de ambos (S-11), histórico só em memória, sem cotação de frete, sem canal real). A seção "Uso de assistentes de código" fica só com o título, para o autor preencher (depende de T057).
- [ ] T059 Gerar de 3 a 5 conversas reais com `uv run emporio --transcricao` e salvá-las em `exemplos/`: uma de catálogo e preço, uma de políticas, uma de pedido com verificação e arrependimento (a não trivial), uma de fora do escopo e uma de reclamação; conferir que nenhuma expõe dado pessoal além do necessário (depende de T055).
- [ ] T060 Rodar `uv run emporio-eval` com o modelo real, versionar o relatório em `evals/reports/` e registrar no `README.md` o resultado de SC-001 a SC-004 (depende de T056 e T058).
- [ ] T061 Revisar a cobertura: cada FR-001 a FR-025 do `spec.md` tem um teste rastreável, e cada S-01 a S-18 aparece no código (comentário com o ID), em teste e no README.
- [ ] T062 Checagem de segurança (`constitution/workflow.md`): nenhum segredo versionado; `.env`, `var/` e `registros/` ignorados; nenhum dado pessoal em logs, no modo `--debug` sem necessidade ou nos exemplos; as conexões dos dados da loja só para leitura.
- [ ] T063 Conferir SC-005: clonar o repositório numa pasta limpa e seguir só o README até conversar com o agente, corrigindo o README onde travar (depende de T058).
- [ ] T064 Rodar os gates de `constitution/workflow.md`: `uv run ruff check .`, `uv run ruff format --check .` e `uv run pytest` (sem rede e sem chave); nenhum `print()` de depuração; toda variável de ambiente documentada no `.env.example` e no README.

## Dependências e Ordem de Execução

- **Setup (Fase 1)**: sem dependências.
- **Fundação (Fase 2)**: depende do Setup e bloqueia todas as histórias.
- **US1 (Fase 3) e US2 (Fase 4)**: dependem da Fundação; a US2 usa `money` e a carga, mas não depende da US1.
- **US3 (Fase 5)**: depende da Fundação.
- **US4 (Fase 6)**: depende das ferramentas registradas nas US1 a US3, para o teste do registro.
- **US6 (Fase 7)**: depende das US1 a US4 para escrever os casos.
- **US5 (Fase 8)**: depende da Fundação e de `business_hours` (US1); acrescenta os casos à avaliação da US6.
- **Polimento (Fase 9)**: depende de todas as histórias.

## Notas

- [P] = arquivos diferentes, sem dependência entre si.
- Todo teste cita o FR que cobre; toda regra que aplica uma suposição cita o ID (S-xx) num comentário.
- Pare em cada checkpoint para validar a história sozinha antes de seguir.
- Nenhuma história é dada como concluída com teste quebrado.
