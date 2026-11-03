# Constituição do Projeto: Agente de Atendimento da Empório da Música

Protótipo de um agente de atendimento por mensagens de texto para a Empório da
Música, loja de instrumentos musicais em Campo Grande/MS. Ele responde às
perguntas recorrentes dos clientes (horário, status de pedido, preço e
disponibilidade) com base nos dados e no manual de políticas da loja, para
aliviar a equipe de atendimento.

## Princípios de Arquitetura

### I. Fato vem da fonte (INEGOCIÁVEL)

Preço, estoque, promoção, prazo, status de pedido e qualquer regra da loja só
chegam ao cliente depois de uma consulta aos dados ou ao manual de políticas.
Nunca vêm do conhecimento prévio do modelo. Se a fonte não responde, o agente
diz que não tem a informação e indica o contato da loja.

**Por quê:** o manual (seção 7.1) proíbe informar preço, estoque ou prazo sem
consultar o sistema, porque informação errada pode configurar propaganda
enganosa.

**Ao violar:** não há exceção. Uma resposta sem fonte é defeito.

### II. Regra de negócio em código (INEGOCIÁVEL)

Preço final, desconto do PIX, aplicação de promoção, parcelamento e qualquer
outra conta de dinheiro são calculados de forma determinística em código e
cobertos por testes. O modelo apresenta o resultado; ele não faz a conta.

**Por quê:** aritmética feita pelo modelo pode variar entre execuções e não dá
para auditar. Já uma regra em código pode ser testada e corrigida num lugar só.

**Ao violar:** não há exceção. Se uma regra ainda não tem implementação, o
agente informa a regra do manual sem calcular o valor.

### III. Dado pessoal mínimo (INEGOCIÁVEL)

O modelo nunca tem acesso direto à tabela de clientes. Dados de um pedido só
são revelados depois que o cliente comprova a identidade, e a resposta traz o
mínimo necessário para atendê-lo. Dados de um cliente nunca aparecem para
outro.

**Por quê:** é o que diz a LGPD (manual, seção 9), e o risco de vazamento num
agente conversacional vem justamente de deixar o modelo ver mais do que precisa.

**Ao violar:** não há exceção. Qualquer novo uso de dado pessoal tem de passar
por uma ferramenta que aplique a verificação.

### IV. Dados da loja só para leitura (INEGOCIÁVEL)

O agente não altera pedidos, estoque, clientes, produtos nem promoções. A única
escrita permitida é o registro de atendimento que a própria loja pede
(reclamação), e ela vai para um destino separado dos dados operacionais.

**Por quê:** um protótipo que conversa com clientes não pode corromper a
operação, e o acesso só de leitura reduz o estrago possível de uma consulta mal
formada.

**Ao violar:** uma feature que precise escrever dados operacionais exige emenda
desta constituição antes do plano.

### V. Suposição documentada (INEGOCIÁVEL)

Toda inconsistência ou lacuna nos dados ou no manual (dois telefones, regras de
parcelamento contraditórias, totais que não batem, status incoerente com o
estoque) é resolvida por uma regra explícita, registrada na spec da feature e
no README. Nunca em silêncio, nem só no código.

**Por quê:** os dados reais da loja têm contradições, e quem avalia o protótipo
precisa enxergar que regra foi adotada e por quê.

**Ao violar:** não há exceção. Uma regra que está só no código é uma suposição
oculta e deve ser documentada.

### VI. Comportamento avaliável

Todo comportamento do agente tem uma verificação automatizada: testes das
ferramentas e das regras e um conjunto fixo de perguntas com a ferramenta e o
desfecho esperados. Sempre que possível, a verificação roda sem chamar o modelo
real.

**Por quê:** o comportamento de um LLM muda com o prompt e com o modelo. Sem um
conjunto fixo não há como saber se uma mudança melhorou ou piorou o agente.

**Ao violar:** registre no plano da feature por que o comportamento não tem
verificação automática e como ele será conferido.

### VII. Protótipo simples

Nada de infraestrutura que o problema não pede: sem banco servidor, fila,
deploy ou interface web nesta fase. Cada componente a mais precisa de uma
justificativa no plano.

**Por quê:** o objetivo é demonstrar as decisões do agente, e cada componente
extra é mais uma coisa para o avaliador instalar e entender.

**Ao violar:** registre a exceção no plano da feature, com o ganho concreto que
o componente traz.

## Processo de Exceção

Qualquer desvio desta constituição numa feature específica deve ser registrado
explicitamente no `spec.md` (ou no `plan.md`) daquela feature, na seção
"Exceções à Constituição", com a justificativa. Um desvio não documentado é
considerado um erro, não uma decisão. Os princípios marcados como INEGOCIÁVEL
não admitem exceção por feature, só por emenda (ver `governance.md`).

## Partes desta constituição

| Arquivo | Conteúdo | Usado em |
|---|---|---|
| `constitution.md` (este) | princípios e processo de exceção | plano, tarefas e análise de consistência |
| `stack.md` | stack de referência e restrições técnicas | plano |
| `workflow.md` | critério de pronto, segurança, commits e gates de PR | tarefas, implementação e análise |
| `governance.md` | governança e histórico de emendas | emendas à constituição |

A spec de cada feature não depende da constituição, de propósito: ela descreve
o comportamento, sem tecnologia.

**Versão**: 1.0.0 | **Ratificada em**: 2026-11-03 | **Última alteração**: 2026-11-03
