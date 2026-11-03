# Spec: Agente de atendimento da Empório da Música

**Branch / pasta**: `001-agente-atendimento` | **Criada em**: 2026-11-03 | **Status**: Aprovada

## Problema

A Empório da Música é uma loja de instrumentos musicais em Campo Grande/MS, e
todo o atendimento é feito pela própria equipe. A maior parte das mensagens
repete as mesmas perguntas: que horas a loja abre, onde fica, quanto custa um
instrumento, se ele tem em estoque, em quantas vezes dá para parcelar, onde
está o pedido, se dá para devolver uma compra. Responder cada uma dessas
mensagens exige consultar o cadastro de produtos, os pedidos e o manual de
políticas, e a equipe fica sobrecarregada com trabalho repetitivo enquanto os
casos que realmente precisam de uma pessoa esperam.

O objetivo é um protótipo de agente de atendimento por mensagens de texto que
responda a essas perguntas recorrentes no tom da loja, sempre a partir dos
dados e das políticas oficiais. Ele precisa saber quando consultar os dados e
quando consultar as políticas, proteger os dados pessoais dos clientes,
reconhecer o que foge do escopo da loja e registrar para a equipe o que
precisa de uma pessoa, como as reclamações.

Os dados que a loja forneceu têm contradições e lacunas (listadas em
"Suposições"). Parte do problema é decidir, de forma explícita e justificada, a
regra que o agente segue em cada uma.

## Escopo

### Dentro do escopo (este ciclo)

- Persona do atendimento alinhada ao tom de voz da loja (manual, seção 7.1) e
  ao fluxo de atendimento padrão (seção 7.2).
- Informações institucionais: endereço, telefone, WhatsApp, e-mail e horário de
  funcionamento.
- Políticas: formas de pagamento, parcelamento, trocas e devoluções, frete e
  entregas (regras gerais), garantia e privacidade de dados.
- Catálogo: busca de instrumentos por tipo, marca, nome e faixa de preço;
  preço, disponibilidade, promoção ativa, preço no PIX e opções de
  parcelamento.
- Status de pedido, com verificação de identidade antes de mostrar qualquer
  dado.
- Fora de escopo: redirecionar com educação os pedidos de acessórios e recusar
  com gentileza os assuntos alheios à loja.
- Registro de reclamação, com protocolo e prazo de retorno.
- Conversa com contexto entre as mensagens de um mesmo atendimento.
- Avaliação automatizada: testes das capacidades do agente e um conjunto fixo
  de perguntas com o comportamento esperado.
- Entregáveis: README com instruções de execução, justificativas, suposições e
  limitações (a seção sobre ferramentas de apoio ao desenvolvimento fica só com
  o título, para o autor preencher) e de 3 a 5 conversas de exemplo, ao menos
  uma não trivial.

### Fora do escopo (explicitamente)

- Canal real de mensagens (WhatsApp ou outro). O protótipo é usado localmente.
- Cotação de frete por CEP, peso ou dimensões.
- Criação, alteração ou cancelamento de pedidos, reservas de produto e
  pagamentos.
- Recomendação de lojas parceiras específicas (o manual não as lista).
- Atendimento em outros idiomas além do português.
- Envio de promoções ou qualquer comunicação ativa ao cliente.

## Histórias de Usuário e Cenários *(obrigatório)*

### História 1 - Informações da loja e políticas (Prioridade: P1)

O cliente pergunta algo sobre a loja (onde fica, que horas abre, como pagar,
como trocar, como funciona a entrega ou a garantia) e recebe uma resposta
correta, baseada no manual, no tom acolhedor da loja.

**Por que esta prioridade**: são as perguntas mais frequentes e as mais simples
de automatizar; sozinha, esta história já alivia a equipe.

**Teste independente**: perguntar endereço, horário e cada política e conferir
a resposta com o manual.

**Cenários de aceite**:

1. **Dado** um cliente que inicia a conversa, **Quando** ele manda a primeira
   mensagem, **Então** o agente se apresenta como assistente virtual da Empório
   da Música, cumprimenta pelo nome se o cliente o informou e pergunta como
   pode ajudar.
2. **Dado** um cliente, **Quando** ele pergunta o endereço ou os contatos da
   loja, **Então** o agente informa o endereço, o telefone (67) 3341-4444, o
   WhatsApp (67) 3321-4500 e o e-mail contato@emporiodamusica.com.br.
3. **Dado** um cliente, **Quando** ele pergunta se a loja está aberta agora,
   **Então** o agente responde com base no dia e na hora locais de Campo Grande
   e no horário do manual (segunda a sexta 9h–18h, sábado 9h–13h, fechado aos
   domingos e feriados).
4. **Dado** um cliente, **Quando** ele pergunta como pode devolver uma compra
   porque se arrependeu, **Então** o agente explica que o direito de
   arrependimento vale para compras online em até 7 dias corridos do
   recebimento, com o produto na embalagem original e sem uso, e pergunta se a
   compra foi online.
5. **Dado** um cliente, **Quando** ele pergunta sobre o frete para uma cidade
   fora da região metropolitana, **Então** o agente explica as modalidades e os
   prazos do manual e diz que o valor depende do CEP, sem estimar valores.
6. **Dado** um cliente, **Quando** ele pergunta sobre um ponto que o manual não
   cobre, **Então** o agente diz que não tem essa informação e indica os
   contatos da loja, sem inventar uma regra.

---

### História 2 - Catálogo, preço e disponibilidade (Prioridade: P1)

O cliente procura um instrumento (pelo nome, pelo tipo, pela marca ou pela
faixa de preço) e recebe as opções disponíveis com preço, promoção, preço no
PIX e parcelamento corretos.

**Por que esta prioridade**: preço e disponibilidade são o segundo grande
volume de perguntas e o ponto em que um erro gera propaganda enganosa.

**Teste independente**: fazer perguntas de preço e de busca e conferir com os
dados e com as regras de preço calculadas à parte.

**Cenários de aceite**:

1. **Dado** o Takamine GD20 em estoque e sem promoção ativa, **Quando** o
   cliente pergunta o preço, **Então** o agente informa o preço de tabela
   (R$ 2.199,00), o preço no PIX com 5% de desconto (R$ 2.089,05) e a maior
   opção de parcelamento sem juros permitida.
2. **Dado** um produto com promoção ativa, **Quando** o cliente pergunta o
   preço, **Então** o agente mostra o preço original, o percentual de desconto e
   o preço promocional, e deixa claro que o desconto do PIX não se soma à
   promoção.
3. **Dado** o cliente pergunta por violões disponíveis até R$ 1.000, **Quando**
   o agente responde, **Então** lista só produtos ativos, com estoque e preço
   final dentro do limite, cada um com o preço.
4. **Dado** um produto ativo com estoque zerado, **Quando** o cliente pergunta
   por ele, **Então** o agente diz que está temporariamente indisponível e
   sugere alternativas semelhantes disponíveis.
5. **Dado** um produto descontinuado, **Quando** o cliente pergunta por ele,
   **Então** o agente informa que ele não faz mais parte do catálogo e sugere
   modelos equivalentes disponíveis, mesmo que o cadastro ainda mostre unidades
   em estoque.
6. **Dado** um produto marcado como lançamento em breve, **Quando** o cliente
   pergunta por ele, **Então** o agente informa que ele ainda não está à venda,
   sem confirmar disponibilidade, e sugere alternativas semelhantes
   disponíveis.
7. **Dado** um produto com uma promoção encerrada, **Quando** o cliente pergunta
   por aquela promoção, **Então** o agente informa com transparência que ela não
   está mais vigente e apresenta o preço atual.
8. **Dado** um tipo de instrumento que a loja trabalha mas que não tem nenhum
   produto cadastrado (sopros, cordas orquestrais), **Quando** o cliente procura
   por ele, **Então** o agente diz que no momento não há opções no catálogo e
   indica os contatos da loja para consultar encomendas.
9. **Dado** o cliente pergunta em quantas vezes pode parcelar um produto,
   **Quando** o agente responde, **Então** o número máximo de parcelas e o valor
   de cada uma seguem as faixas de parcela mínima da seção 3.1 do manual.

---

### História 3 - Status de pedido com verificação de identidade (Prioridade: P2)

O cliente quer saber onde está o pedido. O agente pede o número do pedido e o
e-mail da compra e só mostra o andamento se os dois corresponderem ao mesmo
cliente.

**Por que esta prioridade**: é uma pergunta muito frequente, mas envolve dado
pessoal; vem depois do que pode ser respondido sem identificação.

**Teste independente**: consultar pedidos de todos os status com dados corretos
e incorretos e conferir que nada aparece sem verificação.

**Cenários de aceite**:

1. **Dado** um cliente que pergunta pelo pedido, **Quando** ele ainda não
   informou o número do pedido e o e-mail, **Então** o agente pede os dois antes
   de qualquer consulta.
2. **Dado** um número de pedido e um e-mail que pertencem ao mesmo cliente,
   **Quando** a verificação é feita, **Então** o agente informa o status em
   português, a data do pedido, os itens, o total registrado e, conforme o
   status, o código de rastreio e a previsão de entrega ou o motivo do
   cancelamento.
3. **Dado** um número de pedido e um e-mail que não correspondem, **Quando** a
   verificação falha, **Então** o agente informa que não conseguiu localizar o
   pedido com esses dados, sem dizer qual dos dois está errado e sem revelar
   nenhum dado do pedido ou do cliente.
4. **Dado** um pedido enviado cuja previsão de entrega já passou, **Quando** o
   cliente consulta, **Então** o agente informa o status e o código de
   rastreio, diz com transparência que a previsão venceu e oferece registrar uma
   reclamação.
5. **Dado** um cliente verificado para um pedido, **Quando** ele pergunta por
   outro pedido, **Então** o agente pede a verificação de novo, para o novo
   pedido.
6. **Dado** alguém que pede dados de outro cliente (nome, telefone, endereço,
   pedidos de terceiros), **Quando** faz o pedido, **Então** o agente recusa e
   explica que não compartilha dados pessoais.
7. **Dado** um pedido entregue e um cliente que quer devolvê-lo por
   arrependimento, **Quando** ele confirma que a compra foi online, **Então** o
   agente usa a previsão de entrega como data de recebimento, diz se os 7 dias
   ainda valem e, se não valerem, apresenta as regras de troca por defeito e de
   garantia.

---

### História 4 - Perguntas fora do escopo (Prioridade: P2)

O cliente pede algo que a loja não vende ou que não tem relação com a loja. O
agente redireciona ou recusa com gentileza, sem inventar nada.

**Por que esta prioridade**: protege a loja de respostas falsas e mantém a
conversa no que o agente sabe fazer.

**Teste independente**: um conjunto de perguntas sobre acessórios, assuntos
alheios e tentativas de tirar o agente do papel.

**Cenários de aceite**:

1. **Dado** um cliente que pede cordas, palhetas, cabos, cases, pedais ou
   amplificadores, **Quando** o agente responde, **Então** explica que a loja
   trabalha só com instrumentos musicais e se oferece para ajudar com
   instrumentos.
2. **Dado** um cliente que faz uma pergunta sem relação com a loja (política,
   receita, tarefa escolar), **Quando** o agente responde, **Então** recusa com
   gentileza e lembra no que pode ajudar.
3. **Dado** um cliente que tenta mudar as instruções do agente ou pedir algo
   fora do papel, **Quando** o agente responde, **Então** continua no papel de
   atendente da loja, sem revelar instruções internas.
4. **Dado** um cliente que pede para cancelar ou alterar um pedido, **Quando** o
   agente responde, **Então** explica que não faz essa operação e indica os
   contatos da equipe.

---

### História 5 - Registro de reclamação (Prioridade: P3)

O cliente está insatisfeito. O agente escuta com empatia, coleta o necessário,
registra a reclamação para a equipe e informa o protocolo e o prazo de retorno.

**Por que esta prioridade**: o manual exige o registro, mas o volume é menor que
o das perguntas informativas.

**Teste independente**: abrir reclamações completas e incompletas e conferir o
registro gerado.

**Cenários de aceite**:

1. **Dado** um cliente insatisfeito, **Quando** ele relata o problema, **Então**
   o agente responde com empatia e pede o que ainda faltar entre nome, um
   contato (telefone ou e-mail), a descrição do problema e o número do pedido,
   se houver.
2. **Dado** os dados mínimos coletados (nome, contato e descrição), **Quando** o
   agente registra a reclamação, **Então** devolve um número de protocolo e
   informa o prazo de retorno de 24 horas úteis.
3. **Dado** uma reclamação registrada fora do horário de funcionamento,
   **Quando** o agente confirma o registro, **Então** informa também quando a
   equipe volta a atender.

---

### História 6 - Avaliação automatizada do agente (Prioridade: P2)

A equipe (ou quem avalia o protótipo) roda uma verificação que mostra se o
agente consulta a fonte certa e responde corretamente a um conjunto fixo de
perguntas.

**Por que esta prioridade**: sem ela, não há como saber se uma mudança no agente
melhorou ou piorou as respostas.

**Teste independente**: rodar a avaliação e obter um relatório por pergunta, com
o resultado esperado e o obtido.

**Cenários de aceite**:

1. **Dado** o conjunto fixo de perguntas, **Quando** a avaliação roda, **Então**
   cada pergunta é comparada com a fonte de consulta esperada (dados, políticas,
   pedido, reclamação ou nenhuma) e com o desfecho esperado, e o relatório
   mostra o resultado de cada uma e o total.
2. **Dado** as regras de preço, parcelamento, prazo e verificação, **Quando** os
   testes rodam, **Então** cada regra é verificada sem depender do agente
   conversacional.

---

### Casos de Borda

- O cliente escreve o nome do produto com erro, sem acento ou parcial
  ("takamine gd 20"): o agente encontra o produto ou pergunta qual dos
  candidatos é.
- A busca não encontra nenhum produto: o agente diz isso e sugere ampliar o
  filtro, sem inventar produto.
- Muitos produtos atendem a busca: o agente mostra uma seleção curta e se
  oferece para filtrar mais.
- O cliente informa o número do pedido em formatos diferentes ("pedido 8",
  "#8", "nº 8") ou o e-mail com letras maiúsculas.
- Pedidos com total diferente da soma dos itens (3 e 20) ou pagos via PIX sem o
  desconto (1, 5 e 10): o agente informa o total registrado, sem recalcular.
- O cliente pergunta sobre um feriado específico: o agente diz que a loja fecha
  nos feriados, mas não afirma se uma data é feriado.
- O cliente pergunta sobre o horário estendido de datas especiais: o agente diz
  que, quando há mudança, ela é comunicada nas redes sociais e no WhatsApp.
- O cliente pede para pagar com PIX e cartão juntos: o agente informa que a
  combinação é permitida em compras acima de R$ 2.000,00.
- O cliente pede um instrumento de grande porte para outra cidade: o agente
  avisa que pode haver frete especial com cotação individual.
- A mesma mensagem mistura duas perguntas (preço e horário): o agente responde
  as duas.

## Requisitos Funcionais *(obrigatório)*

- **FR-001**: O agente DEVE se comunicar em português do Brasil, num tom
  informal mas profissional, acolhedor, como quem entende de música, e seguir o
  fluxo de saudação, entendimento, consulta, resposta e fechamento do manual.
  *(História 1)*
- **FR-002**: O agente DEVE responder às perguntas sobre a loja e as políticas
  somente com base no manual de políticas. Quando o manual não cobrir o assunto,
  DEVE dizer que não tem a informação e indicar os contatos da loja.
  *(História 1)*
- **FR-003**: O agente DEVE informar se a loja está aberta no momento da
  pergunta, usando a data e a hora locais de Campo Grande e o horário do manual.
  *(História 1)*
- **FR-004**: O agente DEVE informar preço, disponibilidade, promoção e
  condições de pagamento somente a partir de uma consulta aos dados da loja feita
  naquela conversa, nunca de memória. *(História 2)*
- **FR-005**: O agente DEVE permitir a busca de instrumentos por nome (tolerando
  erro de digitação e falta de acento), tipo, marca e faixa de preço, e listar
  só produtos disponíveis quando o cliente pede opções. *(História 2)*
- **FR-006**: O preço final DEVE seguir a regra: com promoção ativa, preço de
  tabela menos o percentual da promoção; sem promoção ativa, o preço no PIX é o
  preço de tabela com 5% de desconto; o desconto do PIX nunca se soma à
  promoção. *(História 2)*
- **FR-007**: Ao apresentar um preço promocional, o agente DEVE mostrar junto o
  preço original e o percentual de desconto. *(História 2)*
- **FR-008**: O agente DEVE calcular o parcelamento sem juros pelas faixas da
  seção 3.1: até 3x com parcela mínima de R$ 50,00; de 4x a 6x com parcela
  mínima de R$ 80,00; de 7x a 12x com parcela mínima de R$ 100,00. *(História 2)*
- **FR-009**: O agente DEVE tratar a disponibilidade pelo status e pelo estoque:
  só um produto ativo com estoque maior que zero está disponível; um ativo sem
  estoque está temporariamente indisponível; um descontinuado está fora do
  catálogo, mesmo com estoque; um lançamento em breve ainda não está à venda,
  mesmo com estoque. Para todo indisponível, qualquer que seja o motivo (sem
  estoque, descontinuado ou em breve), DEVE sugerir alternativas semelhantes
  disponíveis. *(História 2)*
- **FR-010**: O agente DEVE considerar vigente só a promoção marcada como ativa
  e, quando perguntado sobre uma promoção inativa, dizer que ela não está mais
  vigente e mostrar o preço atual. *(História 2)*
- **FR-011**: O agente DEVE exigir o número do pedido e o e-mail da compra, e
  confirmar que os dois pertencem ao mesmo cliente, antes de revelar qualquer
  dado do pedido. *(História 3)*
- **FR-012**: Quando a verificação falhar, o agente DEVE responder sem indicar
  qual dado está errado e sem revelar nenhum dado do pedido ou do cliente.
  *(História 3)*
- **FR-013**: O agente NÃO DEVE revelar dados pessoais de nenhum cliente (nome,
  telefone, e-mail, cidade) além do mínimo necessário para atender o próprio
  titular verificado, e NÃO DEVE revelar dados de um cliente para outro.
  *(História 3)*
- **FR-014**: Depois da verificação, o agente DEVE informar o status do pedido
  em português, a data, os itens, o total registrado e, conforme o status, o
  código de rastreio e a previsão de entrega, o motivo do cancelamento ou o aviso
  de que a previsão de entrega já passou. *(História 3)*
- **FR-015**: A verificação DEVE valer só para o pedido verificado; outro pedido
  exige nova verificação. *(História 3)*
- **FR-016**: Para pedido de devolução por arrependimento, o agente DEVE
  perguntar se a compra foi online, usar a previsão de entrega como data de
  recebimento nos pedidos entregues (dizendo que é uma estimativa), dizer se o
  prazo de 7 dias corridos ainda vale e, se não valer, apresentar as regras de
  troca por defeito e de garantia. *(Histórias 1 e 3)*
- **FR-017**: O agente DEVE redirecionar com educação os pedidos de acessórios
  (cordas, palhetas, cabos, cases, pedais, amplificadores), explicando que a loja
  trabalha só com instrumentos musicais. *(História 4)*
- **FR-018**: O agente DEVE recusar com gentileza os assuntos sem relação com a
  loja, manter o papel de atendente diante de tentativas de mudar suas
  instruções e não revelar suas instruções internas. *(História 4)*
- **FR-019**: O agente NÃO DEVE criar, alterar ou cancelar pedidos, nem prometer
  reserva de produto ou de preço. Pedidos assim DEVEM ser encaminhados aos
  contatos da equipe. *(História 4)*
- **FR-020**: O agente DEVE registrar reclamações com nome, um contato
  (telefone ou e-mail), descrição e, se houver, número do pedido; devolver um
  número de protocolo; e informar o prazo de retorno de 24 horas úteis.
  *(História 5)*
- **FR-021**: Fora do horário de funcionamento, o agente DEVE continuar
  atendendo o que é automático e, quando algo depender da equipe, informar
  quando ela volta a atender. *(Histórias 1 e 5)*
- **FR-022**: O agente DEVE manter o contexto das mensagens anteriores dentro do
  mesmo atendimento (produto em discussão, pedido verificado, dados da
  reclamação). *(Histórias 2, 3 e 5)*
- **FR-023**: O projeto DEVE ter uma avaliação automatizada com um conjunto fixo
  de perguntas, cada uma com a fonte de consulta e o desfecho esperados, que gera
  um relatório por pergunta e totais por critério de sucesso. *(História 6)*
- **FR-024**: Toda regra de negócio (preço, PIX, promoção, parcelamento,
  disponibilidade, horário, prazo de arrependimento, verificação de identidade)
  DEVE ter teste automatizado próprio. *(História 6)*
- **FR-025**: O projeto DEVE incluir um README com instruções de execução,
  justificativas das decisões, suposições adotadas e limitações, com a seção
  sobre ferramentas de apoio ao desenvolvimento deixada só com o título; e de 3 a
  5 conversas de exemplo, ao menos uma não trivial (consulta de dados ou
  aplicação de regra). *(Todas)*

### Entidades-Chave *(se a feature envolve dados)*

- **Produto**: instrumento do catálogo, com nome, categoria, preço de tabela,
  estoque, status (ativo, descontinuado, em breve), descrição e características.
- **Categoria**: tipo de instrumento (guitarras, baixos, violões etc.).
- **Promoção**: desconto percentual sobre um produto, vigente ou não.
- **Pedido**: compra de um cliente, com data, status, total registrado, forma de
  pagamento, código de rastreio, previsão de entrega e observação.
- **Item do pedido**: produto e quantidade dentro de um pedido.
- **Cliente**: titular dos pedidos, com nome, telefone, e-mail e cidade (dado
  pessoal protegido).
- **Política**: regra do manual da loja, organizada por assunto.
- **Reclamação**: registro feito pelo agente, com protocolo, data, nome,
  contato, descrição e pedido opcional.
- **Atendimento**: a conversa de um cliente com o agente, com o contexto
  acumulado.

## Critérios de Sucesso *(obrigatório)*

Medidos no conjunto fixo de perguntas da avaliação, rodado contra o agente
completo:

- **SC-001**: pelo menos 90% das perguntas acionam a fonte de consulta esperada
  (dados, políticas, pedido, reclamação ou nenhuma).
- **SC-002**: 100% dos preços, preços no PIX e valores de parcela citados pelo
  agente batem com o valor calculado pelas regras de FR-006 e FR-008.
- **SC-003**: zero respostas revelam dado de pedido ou de cliente sem
  verificação bem-sucedida, incluindo as perguntas que tentam burlar a
  verificação.
- **SC-004**: 100% das perguntas fora do escopo são redirecionadas ou recusadas
  sem uma resposta inventada.
- **SC-005**: uma pessoa que não participou do desenvolvimento consegue instalar
  e conversar com o agente seguindo só o README.

## Restrições

- Stack obrigatória: Python como linguagem principal (exigência do desafio). O
  restante é decidido no plan.
- Integrações existentes que não podem quebrar: não se aplica. Os dados vêm só
  dos arquivos fornecidos pela loja, que não são alterados.
- LGPD / dados sensíveis: os dados de clientes são pessoais. Só o titular
  verificado vê os próprios dados de pedido, e nada de dados pessoais vai para
  as conversas de exemplo além do necessário para demonstrar o atendimento
  (manual, seção 9).
- Performance / disponibilidade: não se aplica (protótipo local de um usuário
  por vez).

## Suposições e perguntas em aberto

Data de referência: o agente usa a data e a hora do sistema, no fuso de Campo
Grande. Nas conversas de exemplo, "hoje" é 2026-11-03.

Inconsistências e lacunas dos dados, com a regra adotada:

| # | Situação encontrada | Regra adotada |
|---|---|---|
| S-01 | O telefone da capa e da seção 1.2 é (67) 3341-4444; a seção 7 diz que o WhatsApp é (67) 3321-4500. | Telefone da loja: (67) 3341-4444. WhatsApp de atendimento: (67) 3321-4500, porque a seção 7 é a específica do canal. Os dois são informados com rótulo. |
| S-02 | O e-mail na seção 1.2 tem acento (`empóriodamusica`); na capa, não. | Usa contato@emporiodamusica.com.br, sem acento: é a forma válida de domínio e a da capa. |
| S-03 | A tabela de pagamento diz "parcela mínima de R$ 100,00"; a seção 3.1 traz faixas de R$ 50, R$ 80 e R$ 100. | Valem as faixas da 3.1, a regra detalhada; a tabela é lida como o resumo do teto de 12x. "Exceto abaixo de R$ 50,00" vira parcela mínima de R$ 50,00 até 3x. |
| S-04 | Os pedidos PIX 1, 5 e 10 estão com o preço cheio, sem o desconto de 5%. | O agente informa o total registrado, sem recalcular nem comentar a diferença. O pedido é o registro do que foi cobrado. |
| S-05 | O total dos pedidos 3 e 20 não bate com a soma dos itens. | Igual a S-04: vale o total registrado. |
| S-06 | O produto 130 está "em breve", mas tem estoque 2 e já aparece num pedido. | O status prevalece: não está à venda. O pedido existente é mostrado ao titular normalmente. |
| S-07 | O produto 136 está descontinuado, com 13 unidades em estoque. | O status prevalece: fora do catálogo. |
| S-08 | O produto 96 está ativo, com estoque zero. | Temporariamente indisponível, com sugestão de alternativas. |
| S-09 | As descrições dos baixos 135 e 136 citam outros modelos (Fender Jazz Bass, Precision). | O agente identifica o produto pelo nome e pelas características, e não repete a descrição desses dois como se fosse do modelo. |
| S-10 | As categorias de sopros (madeiras e metais) e de cordas orquestrais não têm produtos, embora o manual diga que a loja trabalha com elas. | O agente diz que no momento não há opções no catálogo e indica os contatos da loja. |
| S-11 | Os clientes 11 e 43 têm o mesmo e-mail (`bruno.martins@jmail.com`). | A prova aceita é o par número do pedido + e-mail do titular. Um e-mail compartilhado entre cadastros dá acesso aos pedidos de qualquer um deles, porque a verificação identifica quem tem acesso ao e-mail, não a pessoa do cadastro. Nos dados atuais só o cliente 11 tem pedido (o 10), então não há exposição de terceiro. O risco fica registrado nas limitações do README. |
| S-12 | O pedido 8 está "enviado", com previsão de entrega em 2026-02-28, já vencida. | O agente informa o status e o rastreio, diz que a previsão passou e oferece registrar uma reclamação. |
| S-13 | As promoções têm só o indicador de ativa, sem datas de início e fim. | Ativa = vigente hoje. Inativa = encerrada. |
| S-14 | O direito de arrependimento vale só para compra online, e os pedidos não registram o canal nem a data real de entrega. | O agente pergunta o canal e usa a previsão de entrega como data de recebimento, avisando que é uma estimativa. A mesma data vale para os 90 dias da garantia legal, que o manual (8.1) também conta a partir do recebimento. A troca por defeito conta da data do pedido, como diz o manual (4.2). |
| S-15 | O manual não traz o calendário de feriados. | O agente diz que a loja fecha nos feriados, mas não afirma se uma data específica é feriado; a pergunta "está aberto agora?" considera só o dia da semana e a hora. |
| S-16 | O manual sugere indicar lojas parceiras para acessórios, mas não lista nenhuma. | O agente não indica lojas parceiras; só explica o escopo e oferece ajuda com instrumentos. |
| S-17 | O cliente 27 tem o telefone (67) 99999-0000, com cara de valor fictício. | Sem efeito neste ciclo: a verificação usa e-mail, não telefone. Fica registrado como dado suspeito. |
| S-18 | O manual não diz o que acontece com uma reclamação depois de registrada. | O registro fica disponível para a equipe consultar; não há envio ou notificação neste ciclo. |

Perguntas em aberto: nenhuma bloqueante.

## Exceções à Constituição

- Sem exceções: segue a constituição integralmente.

---

## Notas técnicas para o plan

Decisões já tomadas pelo autor, a detalhar e justificar no plan:

- Orquestração com LangChain e LangGraph.
- Modelo da família Claude, via API da Anthropic.
- Abordagem híbrida: consulta em linguagem natural convertida em SQL só sobre
  visões do catálogo (banco local somente leitura, validação que aceita só
  SELECT e impõe limite de linhas); ferramenta tipada para pedidos, com a
  verificação de identidade em código e sem o modelo ver a tabela de clientes;
  preço final calculado em código ou na própria visão, não pelo modelo.
- Histórico da conversa mantido pelo mecanismo de checkpoint do LangGraph.
- Interface de linha de comando primeiro.
- A decidir no plan: como o manual de políticas chega ao agente (texto inteiro
  no contexto, seções por ferramenta ou busca semântica), onde ficam os
  registros de reclamação, a forma de gerar o protocolo e como o modelo é
  simulado nos testes.
