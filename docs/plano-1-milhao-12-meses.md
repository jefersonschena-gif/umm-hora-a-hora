# Plano de 12 meses: de zero a R$ 1.000.000

> Documento de trabalho. Escrito a partir do que já existe neste repositório (o app **UMM — Hora a Hora**).
> Revisar a cada 90 dias. Se um número aqui não bater com a realidade, o errado é o documento, não a realidade.

---

## 0. A verdade matemática antes de qualquer coisa

Você pediu um plano para fazer R$ 1 milhão em um ano "sem experiência nenhuma". Antes do plano, três distinções que decidem se isso é um objetivo ou uma fantasia:

**1. Faturar R$ 1 milhão ≠ ter R$ 1 milhão.**
Faturando R$ 1M em um ano, sobram no bolso algo entre R$ 300k e R$ 500k depois de impostos (Simples Nacional), comissões, salários, infraestrutura e contador. Para **ter** R$ 1M líquido em 12 meses você precisaria faturar perto de R$ 2M. Esse é um alvo diferente e muito mais difícil.

**2. Construir um ativo de R$ 1 milhão é mais viável que extrair R$ 1 milhão em caixa.**
Um SaaS B2B com R$ 600k de receita recorrente anual (ARR) e boa retenção vale, em negociação real de mercado, entre 3x e 5x ARR — ou seja, **R$ 1,8M a R$ 3M**. Chegar a R$ 50k/mês de recorrência em 12 meses é um objetivo agressivo mas defensável. Chegar a R$ 1M em caixa no bolso em 12 meses, partindo do zero, não é.

**Portanto o alvo deste plano é: sair do mês 12 com R$ 50.000/mês de receita recorrente e R$ 600k faturados no ano — o que constrói um patrimônio de sete dígitos.** O R$ 1M de faturamento no ano 1 fica como cenário esticado, e a seção 5 mostra exatamente quais alavancas precisam funcionar para ele acontecer.

**3. Probabilidade honesta.**
Qualquer caminho honesto para R$ 1M de faturamento em 12 meses partindo do zero tem probabilidade baixa — na casa de poucos por cento. O que este plano faz não é prometer o número; é **escolher a aposta com a melhor razão entre chance de acerto e capital exigido**, e transformá-la em tarefas de segunda-feira de manhã. Um plano bom não é o que promete mais, é o que falha barato e rápido quando está errado.

---

## 1. Seu ponto de partida real: você não está no zero

Você disse "sem experiência nenhuma". Olhando este repositório, isso é factualmente falso, e a diferença importa muito.

O que já existe aqui:

| Ativo | Evidência no código |
|---|---|
| Produto funcional de chão de fábrica | PWA rodando, offline-first via `localStorage`, otimizado para celular |
| Modelagem de turnos real | 3 turnos com janelas hora a hora e **paradas programadas** (`pm`) por período — refeição, ginástica laboral, reunião, troca de turno |
| Cálculo de meta e eficiência | `calcMeta`, `capH`, `eficTotal` — meta proporcional ao tempo produtivo, não ao tempo de relógio |
| Catálogo de capacidade | Centenas de part numbers com capacidade por célula (`C16:142`, `C23:130`...) |
| Apontamento de desvio | Campo de "Causa do desvio" — a semente de uma análise de perdas |
| Saída para o mundo real | Export `.xlsx` — é assim que a fábrica consome dado hoje |
| 16 células mapeadas | `C11`–`C27` |

Isso não é um projeto de estudo. É **software de MES/OEE de nicho, construído por alguém que entende o processo por dentro**. Empresas cobram de R$ 2.000 a R$ 15.000 por mês por planta para fazer o que este app já faz em versão bruta.

**Seus três ativos reais:**

1. **Conhecimento de domínio.** Você sabe o que é uma célula, um part number, uma parada programada, um turno de 455 minutos. Isso é raríssimo e não se aprende em curso — se aprende no chão de fábrica. Programador não tem. Consultor de fora não tem.
2. **Capacidade de entregar software.** Com ou sem IA, você fez o produto sair.
3. **Acesso.** Você conhece pessoas que trabalham em indústria. Esse é o canal de venda mais caro de comprar e você já tem.

O que você **não** tem: experiência comercial, estrutura jurídica, processo de venda, e caixa. O plano é todo sobre construir essas quatro coisas em cima dos três ativos acima.

---

## 2. Aviso jurídico que precisa vir antes do plano de negócio

**Leia isto antes de qualquer outra coisa. Ele pode matar o plano inteiro se ignorado.**

Este repositório contém dados que aparentam ser operacionais e reais: part numbers específicos, capacidades por célula, estrutura de turnos com horários exatos. Se esses dados vieram de uma empresa onde você trabalha ou trabalhou:

- **Os dados não são seus.** Catálogo de peças, capacidades produtivas e estrutura de células são informação confidencial da empresa.
- **O código pode não ser seu.** Depende do seu contrato de trabalho. Cláusulas de propriedade intelectual e invenção frequentemente atribuem ao empregador o que foi desenvolvido durante o vínculo, usando conhecimento ou recursos da empresa, ou dentro do escopo da função.
- **Pode haver cláusula de não concorrência.**

**Ações obrigatórias antes da semana 1:**

1. Ler o contrato de trabalho e o regulamento interno inteiros, procurando: propriedade intelectual, invenções, confidencialidade, não concorrência, exclusividade.
2. **Zerar todos os dados reais do produto comercial.** O catálogo vira vazio, com importação por planilha feita pelo cliente. Células, turnos e capacidades viram configuráveis. Nada de dado de terceiro embarcado no código.
3. Consultar **uma vez** um advogado trabalhista/empresarial (R$ 400–1.000 por uma consulta). É o melhor dinheiro que você gasta neste plano inteiro.
4. Se o produto for construído para vender à indústria em que você trabalha, isso é uma conversa a ter **com a empresa**, formalmente — não uma coisa a fazer por fora. Pode virar seu primeiro contrato em vez do seu primeiro processo.

Um produto limpo, genérico e configurável não é só segurança jurídica: é o que torna ele vendável para 20 clientes em vez de 1.

---

## 3. Escolha do caminho

Três caminhos plausíveis para você especificamente. Todos partem do que você já tem.

### Caminho A — Micro-SaaS industrial (RECOMENDADO)
Transformar o UMM em produto vendido por assinatura + implantação para pequenas e médias indústrias.

- **Por que é o certo para você:** usa os três ativos (domínio, produto, acesso). Ticket alto. Receita recorrente, que é o que constrói patrimônio. Capital inicial quase zero.
- **Contra:** ciclo de venda industrial é longo (60–120 dias). Você vai ter que aprender a vender, e vai ser desconfortável.
- **Teto realista ano 1:** R$ 500k–700k faturados, R$ 40k–55k de MRR na saída.

### Caminho B — Serviço de eficiência com ganho compartilhado
Vender melhoria de OEE, cobrando fixo + percentual do ganho comprovado. O app é a ferramenta de medição, não o produto.

- **Prós:** tickets muito altos (R$ 15k–60k por projeto), sem precisar de produto maduro, caixa entra rápido.
- **Contra:** você troca tempo por dinheiro, não escala, e depende de credibilidade que você ainda não construiu. Ganho compartilhado exige baseline auditável e negociação sofisticada.
- **Uso correto:** como **acelerador de caixa no semestre 1**, não como negócio principal.

### Caminho C — Software sob demanda para indústria
Desenvolver sistemas pontuais para fábricas.

- **Prós:** caixa mais rápido de todos, aprende venda e requisitos.
- **Contra:** não constrói ativo. Você vira uma agência de uma pessoa só. Sem recorrência, o ano 2 recomeça do zero.
- **Uso correto:** financiar o Caminho A nos primeiros 4 meses.

### A decisão
**Caminho A é o negócio. B e C são financiamento.** Nos primeiros 6 meses você aceita trabalho de B e C para pagar as contas e comprar conversas com fábricas — mas todo projeto de B/C tem que gerar um caso de uso, um contato ou um pedaço de produto para o A. Se não gerar, recuse.

---

## 4. O produto: o que o UMM precisa virar

Hoje é um app de uma pessoa. Para virar produto vendável, precisa de exatamente isto — **e nada além disto no ano 1**:

**Obrigatório (mês 1–3)**
- Multiempresa (multi-tenant): cada cliente com seus dados isolados. Isso muda a arquitetura, é o item mais pesado da lista.
- Login com perfis: operador (só lança), líder (lança e edita), gestor (só vê e configura).
- Backend com banco de verdade + sincronização. `localStorage` é ótimo para o chão de fábrica offline, mas o dado precisa subir. Mantenha offline-first: **a fábrica cai a rede e o apontamento não pode parar.**
- Cadastro de células, turnos, paradas programadas e catálogo **pelo cliente**, via tela e importação de planilha.
- **Painel de TV para o chão de fábrica.** Uma tela grande, meta vs. realizado, verde/vermelho. Item barato de fazer e é o que faz o gestor comprar — ele quer ver a fábrica da sala dele.
- Relatório de perdas por causa de desvio: Pareto das paradas. É a resposta para "por que perdemos produção ontem?".

**Depois de 3 clientes pagantes (mês 4–8)**
- OEE completo: disponibilidade × performance × qualidade.
- Comparativo entre turnos e entre células.
- Relatório automático por e-mail no fim de cada turno.
- API/CSV para o ERP do cliente (TOTVS, Senior, SAP B1 — pergunte qual, sempre).

**Não faça no ano 1:** app nativo, integração direta com CLP/IoT, manutenção preditiva, IA, aplicativo para o operador com gamificação, e qualquer coisa que um cliente pediu mas não quis pagar por.

**Regra de produto:** só construa o que um cliente já pagou ou o que 3 prospects diferentes pediram na mesma semana.

---

## 5. O modelo de receita: os números por trás do alvo

### Estrutura de preço

| Item | Preço | Papel |
|---|---|---|
| Piloto pago (30 dias, 1 linha) | **R$ 4.900** | Remove o risco do cliente e qualifica de verdade. Nunca faça piloto grátis. |
| Implantação (setup, cadastro, treinamento) | **R$ 12.000 – 25.000** | Paga seu tempo e ancora o valor. |
| Assinatura até 10 células | **R$ 2.500/mês** | O ativo. |
| Assinatura 11–25 células | **R$ 4.500/mês** | |
| Multiplanta (enterprise) | **R$ 8.000+/mês** | Onde mora o cenário esticado. |
| Hora de consultoria de OEE | **R$ 350/h** | Caixa de curto prazo. |

**Como justificar o preço (decore isto):** uma linha parada custa à fábrica, entre mão de obra, rateio e margem perdida, tipicamente R$ 800 a R$ 3.000 por hora. *"A mensalidade custa menos do que uma hora de linha parada por mês. Se o sistema evitar uma única parada não identificada por mês, ele já se pagou."* Peça ao cliente o número dele e faça a conta na frente dele — nunca use o seu número.

### Cenário base (o que este plano persegue)

Fechamentos: 0 nos meses 1–3, depois 1, 1, 2, 2, 2, 3, 3, 3, 3 → **20 clientes no ano.**

| Linha | Cálculo | Total |
|---|---|---|
| Implantações | 20 × R$ 18.000 (médio) | R$ 360.000 |
| Assinaturas | 83 client-meses × R$ 2.500 | R$ 207.500 |
| Pilotos não convertidos | 10 × R$ 4.900 | R$ 49.000 |
| **Faturamento ano 1** | | **≈ R$ 616.000** |
| **MRR na saída** | 20 × R$ 2.500 | **R$ 50.000/mês (R$ 600k ARR)** |
| **Valor do ativo construído** | 3–5× ARR | **R$ 1,8M – R$ 3M** |

### Cenário esticado (R$ 1M faturado no ano 1)

Não acontece por esforço. Acontece se — e só se — **três alavancas específicas** funcionarem:

1. **Ticket médio de implantação sobe para R$ 28.000** (vendendo para plantas maiores, não mais plantas pequenas).
2. **Duas contas multiplanta** a R$ 8.000/mês entram até o mês 7.
3. **Um vendedor entra no mês 5** (comissionado, 15% do primeiro ano) e **um implantador no mês 7** — porque com 24 clientes você fisicamente não implanta sozinho.

Com isso: 24 clientes × R$ 28k = R$ 672k de implantação + ~R$ 400k de assinaturas ≈ **R$ 1,07M**. Fatura R$ 1M, e o lucro fica em torno de R$ 400k depois de comissões, salários e impostos.

**A conclusão prática: o R$ 1M no ano 1 não é uma questão de trabalhar mais. É uma questão de vender para clientes maiores e contratar antes de se sentir confortável.** Se em vez disso você vender bem para 20 clientes pequenos e sair com R$ 50k de MRR, você fez algo melhor a longo prazo do que bater o R$ 1M.

---

## 6. O plano em quatro ciclos de 90 dias

### Ciclo 1 — Dias 1–90: Provar que alguém paga
**Objetivo único: 3 pilotos pagos de R$ 4.900. Nada mais conta.**

- Resolver a questão jurídica (seção 2). Produto limpo, sem dado de terceiros.
- Abrir CNPJ (seção 8).
- Listar **150 indústrias** num raio de 200 km com 50 a 500 funcionários (metalúrgica, autopeças, plástico, alimentos, embalagem).
- **40 conversas de descoberta.** Não é venda: é entender como eles medem produção hoje. Aposta: 70% usam planilha e quadro branco.
- Multi-tenant + login + painel de TV. Só isso.
- Fechar 3 pilotos pagos.
- Manter o emprego. Nada de largar o emprego neste ciclo.

**Critério de kill:** 40 conversas e zero disposição de pagar R$ 4.900 → o problema é o ICP ou a oferta. Pare de programar e refaça a seção 3. Não construa mais produto.

### Ciclo 2 — Dias 91–180: Provar que o piloto vira contrato
**Objetivo: 6 clientes pagando assinatura, R$ 15k de MRR.**

- Converter pilotos em contrato anual (12 meses, reajuste IPCA, 30 dias de aviso).
- Transformar o primeiro cliente feliz em **caso documentado com número**: "reduziu 11% de parada não identificada em 60 dias". Um número real vale mais que qualquer material de marketing.
- Padronizar a implantação: checklist, vídeos de treinamento, planilha modelo de importação. **Meta: implantar em 5 dias úteis, não 5 semanas.**
- Entrar na associação industrial da sua região (FIESC/FIEP/CIESP/sindicato metalúrgico patronal). É onde os compradores estão juntos.
- Ao chegar em R$ 15k de MRR + 2 meses de reserva no caixa: **avaliar sair do emprego.** Não antes.

### Ciclo 3 — Dias 181–270: Tirar você do gargalo
**Objetivo: 12 clientes, R$ 30k de MRR, e você não sendo mais o único que vende e implanta.**

- Contratar vendedor comissionado (indústria: procure alguém que já vendeu automação, EPI, ferramentas ou serviço de manutenção — ele já tem a agenda).
- Contratar implantador/suporte (pode ser meio período no início).
- Suporte com SLA definido. Fábrica de 3 turnos vai te ligar às 2h da manhã — decida antes o que você responde e o que não.
- Buscar 1 ou 2 integradores/revendas de automação para vender junto (comissão 20–30%).

### Ciclo 4 — Dias 271–365: Escalar e travar
**Objetivo: 20 clientes, R$ 50k de MRR, churn abaixo de 5% ao ano.**

- Buscar as contas multiplanta (é aqui que o cenário esticado se decide).
- Cobrar reajuste e vender upgrade de faixa para quem cresceu.
- Fechar o ano com dado limpo: MRR, churn, CAC, margem. É isso que dá valor ao ativo.

---

## 7. As primeiras quatro semanas, dia a dia

Plano sem primeira semana concreta é desejo. Aqui está a sua.

**Semana 1 — Limpar e mirar**
- Seg: ler contrato de trabalho inteiro. Agendar advogado.
- Ter: remover do repositório todo dado real. Catálogo vazio + importação por planilha.
- Qua: definir o ICP em uma frase. Exemplo: *"Indústria metalmecânica de 80 a 400 funcionários, 2 ou 3 turnos, que hoje controla produção em planilha e quadro branco."*
- Qui/Sex: montar a lista de 150 empresas (Google Maps + LinkedIn + site da associação industrial). Colunas: empresa, cidade, porte, nome do gerente de produção, contato, status.
- Escreva a promessa em uma frase: *"Seu líder de produção sabe, a cada hora, se a linha vai bater a meta — e por que não bateu."*

**Semana 2 — Falar com gente**
- 10 conversas de 20 minutos com gerentes/coordenadores de produção. Peça 20 minutos, não uma reunião.
- Roteiro fixo, seis perguntas, **e você fala menos de 30% do tempo**:
  1. Como vocês acompanham a produção hoje, hora a hora?
  2. Quando uma hora não bate a meta, quem descobre e quando?
  3. Onde esse dado vai parar? Quem olha?
  4. Quanto tempo o líder gasta por turno consolidando isso?
  5. Qual foi a última parada grande que vocês só entenderam depois?
  6. Se existisse uma tela mostrando isso em tempo real, quem na empresa decidiria comprar?
- **Não venda nesta semana.** Você está comprando informação, e a última pergunta te dá o nome de quem assina.

**Semana 3 — Construir só o que a semana 2 pediu**
- Multi-tenant, login com 3 perfis, painel de TV, cadastro pelo cliente. Nada mais.
- Grave um vídeo de 4 minutos mostrando o app rodando com dados de uma fábrica fictícia.

**Semana 4 — Pedir dinheiro**
- Volte às 10 pessoas da semana 2 com: *"Construí em cima do que você me falou. Quer rodar 30 dias em uma linha? São R$ 4.900, eu configuro tudo, e se não gerar valor você não segue."*
- Meta: 3 sim. Realidade provável: 1. **Um sim já valida a tese.**
- Nas semanas seguintes, mantenha um piso: **10 conversas novas por semana, todas as semanas, o ano inteiro.** É o único hábito que não pode falhar.

---

## 8. Estrutura legal e tributária

- **MEI não serve.** O limite é R$ 81k/ano e você quer faturar múltiplos disso. Abrir MEI agora é criar retrabalho.
- Abra **ME no Simples Nacional**. CNAE: 6202-3/00 (desenvolvimento e licenciamento de software customizável) e 6209-1/00 (suporte técnico). Custo de abertura: R$ 300–1.500.
- **Anexo III (alíquota inicial ~6%) em vez do Anexo V (~15,5%)** depende do **Fator R**: a folha (incluindo pró-labore e encargos) precisa ser ≥ 28% da receita bruta dos últimos 12 meses. Em software isso normalmente se resolve calibrando o pró-labore — **essa única decisão vale dezenas de milhares de reais no ano.** Trate como prioridade e decida com o contador antes do primeiro faturamento relevante.
- **Contador especializado em tecnologia**, R$ 300–600/mês. Não faça você mesmo; o custo do erro é maior que o honorário.
- **Contrato de licença de software** com: escopo, SLA, prazo de 12 meses, reajuste por IPCA, limitação de responsabilidade, propriedade intelectual sua, e cláusula de que o dado de produção é do cliente. Modelo com advogado: R$ 1.500–3.000, uma vez, usado para sempre.
- **LGPD:** o dado é de produção, mas nomes de operadores e apontamentos por matrícula são dado pessoal. Tenha política de privacidade e cláusula de tratamento de dados no contrato.
- Emita nota fiscal desde o primeiro real. Indústria não paga sem NF.

**Capital inicial necessário: R$ 3.000 a R$ 8.000** (abertura, contador, advogado, domínio, hospedagem). Não é preciso investidor. Não pegue empréstimo para isto.

---

## 9. Painel de controle: números que você olha toda semana

| Métrica | Como medir | Alvo mês 12 |
|---|---|---|
| Conversas novas | por semana | ≥ 10, sempre |
| Pilotos pagos vendidos | por mês | 3/mês a partir do mês 6 |
| Conversão piloto → contrato | % | ≥ 60% |
| MRR | soma das assinaturas | R$ 50.000 |
| Churn | clientes perdidos / base | < 5% ao ano |
| Ticket médio de implantação | média | ≥ R$ 18.000 |
| Tempo de implantação | dias úteis | ≤ 5 |
| Caixa | meses de sobrevivência | ≥ 4 |

**Regra dos 90 dias:** ao fim de cada ciclo, se a meta principal não foi atingida, uma das três coisas muda — o cliente-alvo, a oferta, ou o preço. Nunca "a mesma coisa com mais esforço".

---

## 10. Riscos, na ordem em que podem te matar

| # | Risco | Como mata | Mitigação |
|---|---|---|---|
| 1 | **IP e dados do empregador** | Processo, liminar, plano encerrado no mês 3 | Seção 2, feita antes de tudo |
| 2 | **Ninguém paga** | 6 meses programando para zero cliente | Piloto pago na semana 4. Dinheiro na mesa é o único teste |
| 3 | **Ciclo de venda longo** | Caixa acaba antes do primeiro contrato | Manter emprego até R$ 15k de MRR. Caminho C paga as contas |
| 4 | **Você é o gargalo** | 8 clientes e o produto para de evoluir | Padronizar implantação no ciclo 2, contratar no ciclo 3 |
| 5 | **Concorrência (Tractian, Nicolet, MES grandes)** | Perde para marca conhecida | Ganhe por nicho, preço e velocidade: implanta em 5 dias, eles em 5 meses. Não compita em feature list |
| 6 | **Cliente único** | Um cliente vira 40% da receita e sai | Nenhum cliente acima de 30% da receita a partir do mês 8 |
| 7 | **Fábrica não adota** | Operador não lança, dado morre, cliente cancela | O produto vive ou morre na tela do operador: 3 toques por apontamento, funciona offline, funciona com luva. Isso é mais importante que qualquer relatório |
| 8 | **Burnout** | Emprego + negócio + família por 12 meses | Ritmo de maratona. Um dia por semana totalmente fora. Sério |

---

## 11. O que não fazer

- **Não largue o emprego agora.** Largue com R$ 15k de MRR e 4 meses de reserva. Emprego é o seu investidor-anjo sem diluição.
- **Não persiga R$ 1M por day trade, cripto, apostas, dropshipping ou "renda passiva".** Estatisticamente, o resultado esperado é negativo, e nenhum deles usa o que você tem de raro.
- **Não compre curso de "como faturar 1 milhão".** Quem sabe fazer, faz. Compre, no máximo, um livro de vendas B2B e um mentor que já vendeu software para indústria.
- **Não construa mais produto para evitar a conversa de vendas.** Esse é o modo de fracasso mais comum de gente técnica, e é confortável exatamente por isso.
- **Não venda barato para "pegar o primeiro cliente".** Preço baixo atrai o cliente que mais dá trabalho e ancora o preço de todos os próximos.
- **Não aceite piloto grátis.** Piloto grátis não é testado, não é adotado e não vira contrato. Ele só consome o seu mês.
- **Não pegue empréstimo.** Este negócio não precisa de capital, precisa de conversas.

---

## 12. Resumo em cinco linhas

1. Você tem um produto B2B real e conhecimento de chão de fábrica — isso é o ativo, não a ideia de ganhar um milhão.
2. Resolva a questão de propriedade intelectual **antes** de qualquer coisa; ela é a única que mata o plano de forma irreversível.
3. Venda um piloto pago de R$ 4.900 nos próximos 30 dias. Um cliente pagante vale mais que seis meses de código.
4. O alvo do ano é R$ 50k/mês de recorrência e ~R$ 600k faturados — o que constrói um ativo de R$ 1,8M a R$ 3M. R$ 1M faturado no ano 1 exige clientes maiores e contratar cedo, não trabalhar mais.
5. Dez conversas novas por semana, todas as semanas. Se só uma linha deste documento sobreviver, que seja esta.

---

*Este documento é um plano de negócio, não aconselhamento jurídico, contábil ou de investimento. As decisões de propriedade intelectual (seção 2) e de enquadramento tributário (seção 8) devem ser validadas com advogado e contador antes de executadas.*
