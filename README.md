# Empório da Música — agente de atendimento

Protótipo de um agente de atendimento por mensagens de texto para a Empório da
Música, loja de instrumentos musicais em Campo Grande/MS. O agente responde às
perguntas recorrentes dos clientes (horário, endereço, políticas, preço,
disponibilidade, status de pedido) sempre a partir dos dados e do manual de
políticas da loja, protege os dados pessoais, recusa o que está fora do escopo
e registra reclamações para a equipe.

Feito em Python com LangChain e LangGraph, usando um modelo Claude pela API da
Anthropic. Toda conta de dinheiro, prazo e horário é feita em código e coberta
por testes; o modelo só apresenta os valores que as ferramentas devolvem.

- Especificação, plano e tarefas: [`specs/001-agente-atendimento/`](specs/001-agente-atendimento/)
- Constituição do projeto (princípios e regras de trabalho): [`constitution/`](constitution/)
- Validação de cada história: [`specs/001-agente-atendimento/validacao/`](specs/001-agente-atendimento/validacao/)

## Sumário

1. [Como instalar e rodar](#como-instalar-e-rodar)
2. [Como o agente funciona](#como-o-agente-funciona)
3. [Decisões técnicas e justificativas](#decisões-técnicas-e-justificativas)
4. [Suposições adotadas](#suposições-adotadas)
5. [Testes e avaliação](#testes-e-avaliação)
6. [Conversas de exemplo](#conversas-de-exemplo)
7. [Limitações e o que viria com mais tempo](#limitações-e-o-que-viria-com-mais-tempo)
8. [Estrutura do repositório](#estrutura-do-repositório)
9. [Uso de assistentes de código](#uso-de-assistentes-de-código)

## Como instalar e rodar

Pré-requisitos: Python 3.11 ou superior, [`uv`](https://docs.astral.sh/uv/) e
uma chave da API da Anthropic (só para conversar com o agente real e rodar a
avaliação; os testes não precisam dela).

1. Instale as dependências (o `uv` cria o ambiente virtual e respeita o `uv.lock`):

   ```bash
   uv sync
   ```

2. Crie o `.env` a partir do exemplo e preencha a chave:

   ```bash
   cp .env.example .env
   ```

   | Variável | Obrigatória | Padrão | Para quê |
   |---|---|---|---|
   | `ANTHROPIC_API_KEY` | sim, para conversar e avaliar | — | chave da API da Anthropic |
   | `MODEL_NAME` | não | `claude-sonnet-5-5` | modelo do agente (D-05) |
   | `JUDGE_MODEL_NAME` | não | `claude-haiku-5-5` | modelo juiz da avaliação, só para SC-004 (S2-11) |

   O `.env` está no `.gitignore` e nunca é versionado.

3. Converse com o agente pela linha de comando:

   ```bash
   uv run emporio
   ```

   Na primeira execução (ou quando um CSV de `data/` for mais novo), a carga
   gera `var/catalog.sqlite` e `var/orders.sqlite` a partir dos CSVs. Durante a
   conversa, `/nova` começa um novo atendimento e `/sair` encerra. Opções:

   - `--debug`: mostra o nome de cada ferramenta chamada;
   - `--transcricao ARQ.md`: salva a conversa em markdown.

   ```bash
   uv run emporio --debug --transcricao conversa.md
   ```

4. Rode os testes (sem rede e sem chave; o modelo é simulado):

   ```bash
   uv run pytest
   ```

5. Rode a avaliação com o modelo real (gera `evals/reports/AAAA-MM-DD.md`):

   ```bash
   uv run emporio-eval
   ```

   Para rodar só alguns casos: `uv run emporio-eval --casos preco-takamine-95,verificacao-falha`.

6. Lint e formatação:

   ```bash
   uv run ruff check .
   ```

   ```bash
   uv run ruff format --check .
   ```

## Como o agente funciona

Um único agente de LangGraph decide, a cada mensagem, qual ferramenta chamar.
O grafo é explícito: nó do modelo → nó de ferramentas → nó do modelo, até o
modelo responder sem pedir ferramenta. O prompt de sistema é montado a cada
chamada com a data e a hora de Campo Grande, e o histórico do atendimento fica
no checkpointer em memória (um thread por atendimento).

```text
cliente ─► CLI ─► grafo LangGraph ─► modelo Claude
                     │                   │
                     │                   └─► ferramentas
                     │                         get_store_info      horário e contatos
                     │                         get_policy          manual em PDF, por tópico
                     │                         find_product        ─► var/catalog.sqlite (só leitura)
                     │                         query_catalog       ─► var/catalog.sqlite (só leitura)
                     │                         get_order_status    ─► var/orders.sqlite (só leitura)
                     │                         register_complaint  ─► registros/reclamacoes.jsonl
                     │
                     └─► checkpointer em memória (contexto do atendimento)
```

| Ferramenta | O que faz | Garantia em código |
|---|---|---|
| `get_store_info` | endereço, telefone, WhatsApp, e-mail, horário, se está aberta agora e a próxima abertura | horário calculado em `rules/business_hours.py`, no fuso `America/Campo_Grande` |
| `get_policy(topic)` | seções do manual em PDF por tópico, com as notas de interpretação adotadas | tópico restrito a 9 valores; texto extraído do PDF na carga |
| `find_product(name)` | até 3 candidatos com preço de tabela, promoção, PIX, parcelas, promoções encerradas e, se indisponível, 3 alternativas | preços e parcelas de `rules/pricing.py` e `rules/installments.py` |
| `query_catalog(sql)` | consultas analíticas escritas pelo modelo sobre `v_products` e `v_categories` | `tools/sql_guard.py`: um `SELECT`, só as visões, nada de conta na saída, `LIMIT` 20, tempo-limite e conexão só leitura; valores de dinheiro formatados em R$ |
| `get_order_status(order_id, email)` | status, data, itens, total registrado, rastreio, previsão, motivo do cancelamento e prazos de pós-venda | só responde se o par pedido + e-mail bater; falha sempre igual; só o primeiro nome do titular |
| `register_complaint(...)` | registra a reclamação e devolve o protocolo e o prazo de 24 horas úteis | única escrita do agente, fora dos dados da loja |

## Decisões técnicas e justificativas

As decisões completas, com as alternativas consideradas, estão em
[`plan.md`](specs/001-agente-atendimento/plan.md).

| ID | Decisão | Por quê |
|---|---|---|
| U-01 | LangChain + LangGraph | Orquestração com ferramentas tipadas, checkpointer pronto e um grafo que se lê. |
| U-02 | Modelo Claude pela API da Anthropic | Boa escolha de ferramentas e boa escrita de SQL, com uma única dependência externa. |
| U-03 | Abordagem híbrida: SQL gerado pelo modelo só no catálogo; ferramenta tipada para pedidos | O SQL resolve bem perguntas analíticas ("violões até R$ 1.000", "o mais barato de cada categoria"); dados pessoais ficam atrás de uma ferramenta que verifica a identidade em código. |
| U-04 | Preço final calculado em código e materializado no catálogo | O modelo não faz conta de dinheiro (princípio II): o valor é auditável e testado num lugar só. |
| U-05 | Checkpointer do LangGraph e CLI | O contexto do atendimento fica no thread; a CLI é a interface mais simples de instalar e avaliar. |
| D-01 | `StateGraph` explícito em vez do `create_react_agent` pronto | Deixa visível onde o prompt é montado a cada chamada (com data e hora locais) e o fluxo legível para quem avalia. |
| D-02 | Manual por tópico numa ferramenta (`get_policy`), extraído do PDF | Com o manual inteiro no prompt não daria para medir se o agente "soube consultar as políticas" (SC-001); embeddings seriam infraestrutura sem ganho para 8 páginas. As notas de interpretação saem junto com o texto. |
| D-03 | SQL para filtros e listas, mais `find_product` com busca aproximada | O SQL falha com nome digitado errado ("takamine gd 20"); a busca por nome usa `rapidfuzz` sobre o nome normalizado. |
| D-04 | Dois arquivos SQLite: catálogo e pedidos/clientes | A conexão do SQL do modelo só abre o catálogo: mesmo uma consulta que passasse pela validação não alcançaria clientes. |
| D-05 | `claude-sonnet-5-5`, configurável por `MODEL_NAME` | Equilíbrio entre qualidade de roteamento/SQL e custo; o Haiku fica como opção barata. Os modelos atuais da família não aceitam temperatura fora do padrão da API, então ela não é fixada; a estabilidade da avaliação vem da comparação literal dos valores e das verificações de ferramenta. |
| D-06 | Checkpointer em memória (`InMemorySaver`) | A spec pede contexto dentro do atendimento, não entre execuções; persistir conversas guardaria dado pessoal sem necessidade (princípio III). |
| D-07 | Testes sem modelo + modelo simulado + avaliação real com verificações determinísticas e juiz só para SC-004 | O gate obrigatório roda sem chave nem rede; preço, roteamento e vazamento são conferidos em código; só "recusou sem inventar" precisa de julgamento de linguagem. |
| D-08 | Na lista do `SELECT` só colunas, `*`, `COUNT`, `MIN` e `MAX` | O SQL do modelo não cria valor novo de dinheiro (sem `+ - * /`, `SUM`, `AVG`, `ROUND`), nem em subconsulta ou CTE. |
| D-09 | `query_catalog` devolve o dinheiro já formatado em `R$ 1.234,56` | Todas as ferramentas formatam igual, então a ancoragem de SC-002 compara texto. |
| D-09a | Formatação pela coluna de origem, resolvida com o `sqlglot` | `MIN(final_price)`, `final_price AS preco`, `*`, `t.*`, subconsultas e CTEs saem formatados mesmo sem o nome original da coluna. |

Decisões secundárias relevantes (detalhes em `plan.md`, S2-01 a S2-12):
dinheiro em `Decimal` com `ROUND_HALF_UP` (S2-02); fuso `America/Campo_Grande`
com `tzdata` e relógio injetável nos testes (S2-03); extração do PDF com
`pypdf` no modo de layout e recorte pelos títulos numerados (S2-04);
reclamações em JSONL com protocolo `REC-AAAAMMDD-XXXX` (S2-08); carga refeita
quando um CSV é mais novo que o SQLite (S2-09).

## Suposições adotadas

Os dados e o manual da loja têm contradições e lacunas. Cada uma foi
resolvida por uma regra explícita, citada no código pelo ID e coberta por
teste.

| # | Situação encontrada | Regra adotada |
|---|---|---|
| S-01 | O telefone da capa e da seção 1.2 é (67) 3341-4444; a seção 7 diz que o WhatsApp é (67) 3321-4500. | Telefone da loja: (67) 3341-4444. WhatsApp de atendimento: (67) 3321-4500 (a seção 7 é a do canal). Os dois são informados com rótulo. |
| S-02 | O e-mail da seção 1.2 tem acento (`empóriodamusica`); o da capa, não. | Usa `contato@emporiodamusica.com.br`, sem acento. |
| S-03 | A tabela de pagamento diz "parcela mínima de R$ 100,00"; a seção 3.1 traz faixas de R$ 50, R$ 80 e R$ 100. | Valem as faixas da 3.1: até 3x com parcela mínima de R$ 50,00; 4x a 6x, R$ 80,00; 7x a 12x, R$ 100,00. |
| S-04 | Os pedidos PIX 1, 5 e 10 estão com o preço cheio, sem o desconto de 5%. | O agente informa o total registrado, sem recalcular. |
| S-05 | O total dos pedidos 3 e 20 não bate com a soma dos itens. | Vale o total registrado. |
| S-06 | O produto 130 está "em breve", com estoque 2 e já num pedido. | O status prevalece: não está à venda. O pedido existente é mostrado ao titular. |
| S-07 | O produto 136 está descontinuado, com 13 unidades. | O status prevalece: fora do catálogo. |
| S-08 | O produto 96 está ativo, com estoque zero. | Temporariamente indisponível, com alternativas. |
| S-09 | As descrições dos baixos 135 e 136 citam outros modelos (Jazz Bass, Precision). | A descrição desses produtos não é repetida. |
| S-10 | Sopros (madeiras e metais) e cordas orquestrais não têm produtos. | O agente diz que no momento não há opções e indica os contatos para encomenda. |
| S-11 | Os clientes 11 e 43 têm o mesmo e-mail. | A prova é o par número do pedido + e-mail do titular; o e-mail compartilhado abre os pedidos de qualquer um dos dois cadastros (nos dados, só o 11 tem pedido). Risco listado nas limitações. |
| S-12 | O pedido 8 está "enviado", com previsão em 28/02/2026, já vencida. | Informa status e rastreio, diz que a previsão passou e oferece registrar reclamação. |
| S-13 | As promoções não têm datas, só o indicador de ativa. | Ativa = vigente hoje; inativa = encerrada. |
| S-14 | O arrependimento vale só para compra online, e os pedidos não registram canal nem data real de entrega. | O agente pergunta o canal e usa a previsão de entrega como data de recebimento, avisando que é estimativa; a mesma data conta os 90 dias da garantia legal. A troca por defeito conta da data do pedido. |
| S-15 | O manual não traz o calendário de feriados. | O agente diz que a loja fecha nos feriados, sem afirmar se uma data é feriado; "aberta agora" considera dia da semana e hora. |
| S-16 | O manual sugere lojas parceiras para acessórios, mas não lista nenhuma. | O agente não indica lojas parceiras. |
| S-17 | O cliente 27 tem o telefone (67) 99999-0000, com cara de fictício. | Sem efeito: a verificação usa e-mail. Fica registrado como dado suspeito. |
| S-18 | O manual não diz o que acontece com a reclamação depois do registro. | O registro fica em `registros/reclamacoes.jsonl` para a equipe; não há envio nem notificação. |

### Suposições novas da implementação

Pontos que o plano não cobria, resolvidos pela opção mais conservadora e
coerente com a constituição:

| # | Situação | Regra adotada |
|---|---|---|
| N-01 | Além de 135 e 136, as descrições de 137 (cita Ibanez), 139 (Pearl), 140 (Tama), 142 (Roland) e 144 (Yamaha) citam outra marca. | A regra de S-09 vale também para elas: a descrição não é repetida; o agente usa o nome e as características. |
| N-02 | Um produto poderia ter mais de uma promoção ativa (não ocorre nos dados). | Promoções não são cumulativas (manual 6.2): vale só a de maior desconto. |
| N-03 | A seção 3.1 não diz o que acontece abaixo de R$ 50,00. | Compra abaixo de R$ 50,00 só sai em 1x. |
| N-04 | O preço de um produto indisponível poderia ser lido como oferta. | O preço de produto sem estoque, descontinuado ou em breve não é informado; o agente mostra as alternativas disponíveis com preço. |
| N-05 | D-08 e S2-05 listam o que é permitido no SQL, mas não citam literais, `CASE`, `CAST`, `UNION` e comentários. | Tudo isso é recusado; a lista de expressões permitidas é fechada. |
| N-06 | A ancoragem de SC-002 compara texto, mas o modelo pode escrever "R$2.089,05" sem espaço. | A comparação usa o número exato; só o espaço depois de "R$" é padronizado. |
| N-07 | O manual não define o formato do contato da reclamação. | O contato precisa parecer um e-mail ou um telefone (8 ou mais dígitos), para que o retorno seja possível. |
| N-08 | O plano fixava temperatura 0, mas os modelos atuais da família Claude não aceitam temperatura fora do padrão (a API recusa a chamada). | A temperatura não é definida, nem no agente nem no juiz; a estabilidade da avaliação vem da comparação literal dos valores e das verificações de ferramenta. |

## Testes e avaliação

### Testes automatizados

```bash
uv run pytest
```

Rodam sem rede e sem chave. Cobrem:

- as regras de negócio (`tests/unit/`): dinheiro, preço e PIX, parcelamento
  com as fronteiras de cada faixa, disponibilidade, horário, prazos de
  pós-venda, validação de SQL, extração do manual e as verificações da
  avaliação;
- cada ferramenta contra os SQLite gerados (`tests/tools/`), sem modelo;
- o grafo, o prompt, a CLI e o runner da avaliação com um modelo simulado e
  roteirizado (`tests/agent/`, `tests/fakes.py`);
- os entregáveis (`tests/test_deliverables.py`).

A validação de cada história, com o mapa cenário → teste, está em
[`validacao/`](specs/001-agente-atendimento/validacao/).

### Avaliação com o modelo real

```bash
uv run emporio-eval
```

Roda os 37 casos de [`evals/cases.yaml`](evals/cases.yaml) contra o agente
real, cada um num atendimento novo, e grava o relatório em
`evals/reports/AAAA-MM-DD.md`, com o resultado por caso e os totais por
critério de sucesso:

| Critério | Meta | Como é medido |
|---|---|---|
| SC-001 | ≥ 90% | a fonte esperada (dados, políticas, pedido, reclamação ou nenhuma) foi consultada |
| SC-002 | 100% | todo valor em R$ da resposta aparece, como texto, numa saída de ferramenta do mesmo turno; os valores esperados vêm das regras, não de números escritos à mão |
| SC-003 | 0 vazamentos | nenhum rastreio ou total de pedido não verificado, nenhum e-mail, telefone ou nome completo de cliente que o próprio cliente não tenha escrito |
| SC-004 | 100% | um modelo juiz (`JUDGE_MODEL_NAME`) responde SIM ou NÃO: a resposta recusou ou redirecionou sem inventar? |

**Resultado com o modelo real: pendente.** A avaliação ainda não foi rodada
com a chave da API; o comando, os casos e o relatório estão prontos e testados
com o modelo simulado. Ao rodar, registrar aqui os totais de SC-001 a SC-004 e
versionar o relatório de `evals/reports/`.

## Conversas de exemplo

**Pendente.** As conversas são geradas com o modelo real e exigem a chave da
API; não foram geradas ainda, e nenhuma conversa foi escrita à mão. Os
roteiros com as mensagens do cliente estão em
[`exemplos/roteiros/`](exemplos/roteiros/):

| Roteiro | O que mostra |
|---|---|
| `01-catalogo-e-preco` | saudação pelo nome, preço com PIX e parcelas, busca de violões até R$ 1.000 |
| `02-politicas` | horário agora, troca por defeito, frete para outra cidade |
| `03-pedido-e-arrependimento` | verificação de identidade, pedido entregue e prazo de arrependimento vencido, com as regras de defeito e garantia (a conversa não trivial) |
| `04-fora-do-escopo` | acessório, assunto alheio e tentativa de mudar as instruções |
| `05-reclamacao` | pedido 8 com previsão vencida e reclamação registrada com protocolo |

Para gerar as cinco transcrições em `exemplos/` (com o `.env` preenchido):

```bash
for roteiro in exemplos/roteiros/*.txt; do
  uv run emporio --transcricao "exemplos/$(basename "$roteiro" .txt).md" < "$roteiro"
done
```

Os roteiros usam os dados fictícios fornecidos pela loja; as transcrições
mostram ao titular verificado só o primeiro nome e os dados do próprio pedido.

## Limitações e o que viria com mais tempo

- **Sem limite de tentativas de verificação.** A spec não limita tentativas,
  então alguém pode testar e-mails em sequência para um número de pedido. Com
  mais tempo: limite por atendimento e um atraso progressivo.
- **E-mail compartilhado entre cadastros (S-11).** Quem tem acesso ao e-mail
  abre os pedidos de qualquer cadastro que o use. Nos dados atuais não há
  exposição de terceiro, mas o cadastro deveria ter e-mail único.
- **Histórico só em memória (D-06).** O contexto vale dentro do atendimento e
  some ao sair da CLI. Persistência entre execuções exigiria uma política de
  retenção de dados pessoais.
- **Sem cotação de frete.** O valor depende do CEP, peso e dimensões, que não
  estão nos dados; o agente explica as modalidades e prazos e não estima valor.
- **Sem canal real.** O protótipo roda na linha de comando; um canal como o
  WhatsApp exigiria autenticação do número, filas e monitoramento.
- **Filtro de disponibilidade no SQL depende do modelo.** Em `query_catalog`,
  filtrar `availability = 'available'` é escrito pelo modelo; o prompt manda e
  a avaliação confere, mas não há trava em código. Com mais tempo: uma visão só
  com produtos disponíveis para as listas de opções.
- **Feriados não são conhecidos (S-15).** "Aberta agora" ignora feriados;
  com o calendário da loja, a regra seria completa.
- **A avaliação real e as conversas de exemplo estão pendentes** de rodar com a
  chave da API (ver as seções acima).
- **Tom de voz** não tem métrica automática; é conferido nas conversas de
  exemplo.

## Estrutura do repositório

```text
constitution/                 princípios, stack, workflow e governança
specs/001-agente-atendimento/ spec, plano, tarefas, análise de consistência e validação por história
data/                         CSVs e manual em PDF fornecidos pela loja (nunca alterados)
src/emporio/
├── config.py                 caminhos, variáveis de ambiente e relógio no fuso de Campo Grande
├── money.py                  Decimal, arredondamento e formatação R$
├── data/                     carga dos CSVs nos SQLite, normalização de nomes e extração do manual
├── rules/                    regras de negócio puras: preço, parcelas, horário e prazos
├── tools/                    ferramentas do agente e a validação de SQL
├── agent/                    prompt de sistema e grafo do LangGraph
├── evaluation/               casos, verificações e runner do emporio-eval
└── cli.py                    linha de comando
tests/                        unit/, tools/, agent/ e entregáveis
evals/                        cases.yaml e reports/
exemplos/                     conversas de exemplo e os roteiros que as geram
```

Arquivos gerados em execução e fora do git: `var/` (os SQLite), `registros/`
(reclamações) e `.env`.

## Uso de assistentes de código

Seção a ser preenchida pelo autor.
