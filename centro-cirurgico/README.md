# Centro Cirúrgico — Escala Diária

Planilha operacional da coordenação de enfermagem. A aba **Painel** responde de bate-pronto o que
fazer hoje; a aba **Mapa do Dia** é onde se trabalha, e já chega preenchida: cada ambiente com a
sua dupla, as especialidades que passam ali, a ocupação e o tempo em que a sala fica vaga. As
outras abas são cadastro.

## Painel

Uma tela, quatro blocos, tudo por fórmula — nada para preencher ali:

* **A faixa do dia** — AÇÃO NECESSÁRIA / ATENÇÃO / QUASE PRONTO / DIA FECHADO, pela pendência mais
  grave que existir.
* **Os números** — cirurgias, ambientes abertos, prontos, com pendência, disponíveis, déficit e o
  maior atraso previsto.
* **O dia inteiro** — uma linha por ambiente: o nome pintado pela Situação (verde, amarelo,
  vermelho, cinza), a dupla em nome curto e a **linha do tempo do plantão** — 36 colunas de 10 min
  cobrindo 07:00–13:00. Barra cheia é sala ocupada, barra clara é a limpeza, vazio é sala livre. É
  a gestão visual: dá para ver o buraco de cada sala sem ler um número.

  A coluna vale **10 minutos** porque a limpeza dura 20: assim ela ocupa dois quadradinhos exatos.
  Com colunas de 15 min, 20 min de limpeza pintavam 30 — a barra amarela mentia sobre a própria
  duração.

  Cada célula da barra vale 2 (cirurgia), 1 (limpeza) ou 0, escondida por formato `;;;` e pintada
  pela formatação condicional. O valor sai de dois SUMPRODUCT que testam sobreposição entre o
  intervalo da cirurgia e a fatia de 10 min. Por causa disso a aba inteira usa uma grade de 57
  colunas estreitas e iguais, e todo bloco maior é montado mesclando essas colunas.
* **O que fazer agora** — as 8 pendências mais urgentes, em ordem, já com o ambiente e o motivo.
  Cada pendência recebe uma gravidade (sem equipe com cirurgia marcada = 900, falta habilidade =
  800, gente demais = 700, incompleto = 650, atenção = 400…), e as quatro que não são de um
  ambiente — matriz de habilidades vazia, agenda não importada, cirurgião sem especialidade,
  déficit — entram acima de todas.
* **Onde encaixar** e **Risco de atraso** — os três maiores de cada, com horário e minutos.

O ranking de encaixe só considera salas com **Aceita encaixe = Sim** na aba Configuração: a de
urgência e a do centro obstétrico ficam de fora.

**Arquivo:** `Centro_Cirurgico_Escala.xlsx` (demonstração) · `..._REAL.xlsx` quando há cadastro real.

## O serviço

| Posto | Técnicos | Observação |
|---|---|---|
| Salas 1 a 8 | 2 cada | Sala 6 exclusiva do centro obstétrico · Sala 7 reservada a urgências · Sala 8 oftalmológica |
| Admissão | 2 | opera com 1 no limite |
| Box de preparo oftalmológico | 1 | apoio da Sala 8 |
| Sala de recém-nascido | 1 | bloco obstétrico |
| **Total** | **20 vagas/dia** | para um quadro de **22 técnicos** |

Plantão da manhã, 07:00–13:00. **20 min** de limpeza e preparação após cada cirurgia — sempre
acontecem. A agenda do hospital emenda uma cirurgia na outra sem reservar esse tempo: quando a
cirurgia termina antes do previsto a limpeza cabe na folga, e quando vai até o fim do horário a
limpeza empurra a seguinte. É esse empurrão que a coluna **Atraso previsto** mede.
Não se realizam cirurgias cardíacas. Cada posto declara em que dias funciona; nos fins de semana e
feriados os postos de dia útil não operam e as vagas do dia caem junto.

## Habilidade: um X por especialidade

Na aba **Equipe**, uma coluna por especialidade. Marque **X** onde o técnico faz aquela cirurgia;
deixe em branco onde não faz. As colunas vêm da lista de especialidades da aba Configuração.

No arquivo com cadastro real o X vem **provisório**: 3 especialidades por técnica, distribuídas em
rodízio (`{_esp[(i+d) % len(_esp)] for d in (0, 5, 11)}`), o que dá 4 a 5 pessoas por
especialidade. Serve só para a planilha sair do lugar — a coordenação corrige linha por linha, e a
própria aba Equipe traz o aviso.

A coluna **Técnicos** do Mapa do Dia diz quantos aquele ambiente pede naquele dia: 2 nas salas
cirúrgicas e na admissão, **1** no box de preparo oftalmológico e na sala de recém-nascido, 0 quando
o ambiente não opera. Onde é uma pessoa só, a coluna TÉCNICO 2 aparece cinza em vez de azul.

A planilha cruza as especialidades que passam em cada ambiente no dia com o X dos técnicos
escalados e devolve a **Situação**:

| Situação | Significa |
|---|---|
| **OK** | os dois técnicos cobrem todas as especialidades do dia |
| **ATENÇÃO** | alguma especialidade é coberta por um só dos dois |
| **FALTA HABILIDADE** | alguma especialidade do dia não é coberta por ninguém da dupla (o alerta diz qual) |
| **INCOMPLETO** | falta técnico no ambiente |
| **GENTE DEMAIS** | há mais gente do que o ambiente pede (o box de preparo e a sala de recém-nascido são de uma pessoa só) |
| **DUPLA VETADA** | os dois escalados estão sem X na matriz de afinidade da aba Equipe |
| **INDISPONÍVEL** | alguém escalado ali está de folga, férias ou atestado na data (o alerta diz o nome e o motivo) |
| **SEM EQUIPE** | ninguém escalado — o alerta diz quantas cirurgias precisam ser remanejadas |
| **NÃO OPERA** | posto fechado nesse dia da semana |
| **SEM AVALIAÇÃO** | algum técnico escalado ainda não tem X marcado |

## Distribuição automática dos técnicos

A importação da agenda também distribui a equipe (`alocacao.py`), e o resultado já vem escrito nas
colunas TÉCNICO 1 e TÉCNICO 2 — que continuam sendo células comuns, com lista suspensa, para a
coordenação trocar quem quiser. As regras, nesta ordem:

1. só entra quem está disponível (ativo e sem folga, férias ou atestado na data);
2. ninguém em dois lugares — a dupla (ou a pessoa, onde é uma só) fica o turno inteiro no mesmo
   ambiente;
3. déficit é a regra: primeiro cada posto recebe o **mínimo aceitável**, na ordem de prioridade, e
   só depois os que sobram completam as duplas;
4. dentro do posto, prefere quem marca **X** nas especialidades que passam ali no dia;
5. no empate, prefere quem tem menos habilidades, guardando os polivalentes para os postos
   seguintes;
6. **duas pessoas vetadas uma para a outra nunca dividem o mesmo posto** — nem na distribuição
   inicial, nem nas trocas que o passe de melhoria tentaria fazer.

Depois roda um passe de trocas: qualquer troca entre dois postos que aumente a cobertura total é
aceita, até não haver mais ganho. Com a matriz de habilidades ainda em branco a distribuição
acontece do mesmo jeito, e a Situação de cada posto fica em SEM AVALIAÇÃO até o X ser marcado.

Trocar a data na planilha **não** redistribui — para redistribuir, importe a agenda de novo.

## Jogo de sala

Na mesma linha de cada ambiente: ocupação, a **maior janela livre com horário**
("11:20 → 13:00 (100 min)" — já depois da limpeza da cirurgia anterior), de quanto cabe um encaixe
descontada a limpeza dele próprio, e o **atraso previsto** da sala. A aba `Agenda do Dia` traz o
mesmo cirurgia a cirurgia.

### Atraso previsto

Quando a agenda emenda duas cirurgias com menos de 20 min entre elas, a limpeza não cabe e a
seguinte começa atrasada. O atraso **se acumula** ao longo do dia e só some quando aparece uma
folga grande o bastante para absorvê-lo:

```
atraso(k) = MAX(0; atraso(k-1) + fim(k) + limpeza - início(k+1))
```

A coluna mostra o **pico** do dia naquela sala, e o cabeçalho mostra o maior de todas. Transições
para cirurgias que começam depois das 13:00 não entram na conta — esse atraso é do outro turno.
Na agenda real de 21/08: Sala 8 acumula 120 min (sete cirurgias emendadas), Sala 1, 3 e 4 acumulam
60, Sala 2 acumula 40.

## Importar a agenda do hospital

A agenda diária chega em PDF (mapa do centro cirúrgico do sistema do hospital). O
`importar_agenda.py` lê esse PDF e escreve as cirurgias direto na aba `Agenda do Dia`:

```bash
pip install openpyxl "pypdf[crypto]"
python3 importar_agenda.py AGENDA_21.08.pdf Centro_Cirurgico_Escala.xlsx
# -> Centro_Cirurgico_Escala_2026-08-21.xlsx (o arquivo de entrada nunca é sobrescrito;
#    reimportar o mesmo dia gera _v2, _v3...)
```

Sem argumentos (`python3 importar_agenda.py`), ele usa o PDF mais recente e a planilha mais recente
da própria pasta — é assim que os atalhos do Windows funcionam.

O que entra: sala, hora de início, hora de término, procedimento e cirurgião. Os dados de paciente
do PDF (nome, prontuário, nascimento, convênio, leito) **não são lidos nem gravados**.

### Instalar na máquina da coordenação (Windows)

A pasta `windows/` traz os dois atalhos. Monte uma pasta única com `importar_agenda.py`, a
planilha, `instalar_uma_vez.bat`, `Importar agenda.bat` e `LEIA-ME.txt`. Na primeira vez, duplo
clique em **instalar_uma_vez.bat** (acha o Python, instala `openpyxl` e `pypdf`, e explica como
instalar o Python se faltar — marcando *Add python.exe to PATH*). No dia a dia: salvar o PDF na
pasta e dar duplo clique em **Importar agenda.bat** (ou arrastar o PDF em cima dele). A planilha do
dia abre sozinha.

O PDF não traz a especialidade da cirurgia, traz o cirurgião. A seção **8. CIRURGIÕES** da aba
Configuração faz o de/para: preenchida uma vez, a importação passa a preencher a coluna
Especialidade sozinha; todo cirurgião novo é acrescentado ali em branco para a coordenação
classificar.

A importação substitui apenas as linhas da data importada — outras datas no mapa ficam intactas —
e aponta a DATA do Mapa do Dia para o dia importado.

O que a planilha sinaliza na aba `Agenda do Dia`:

* **Fora da janela do plantão** — cirurgia que começa ou termina depois das 13:00. Ela entra no
  mapa, mas só os minutos dentro do plantão contam na ocupação.
A emenda sem folga **não** é sinalizada como erro na coluna Alerta: ela é a regra nessa agenda, e
vira número na coluna Atraso previsto do Mapa do Dia.

## Afinidade — quem pode trabalhar com quem

Na aba **Equipe**, à direita do X de habilidade, há uma matriz que cruza os nomes: os mesmos
técnicos na vertical e na horizontal, **X onde a dupla pode dividir o mesmo posto**. Mesma mecânica
do X de especialidade, aplicada a pessoas em vez de procedimentos.

A matriz **nasce toda marcada** — inclusive as linhas e colunas ainda sem nome, para que quem for
cadastrado depois já entre podendo trabalhar com todo mundo. A coordenação **apaga** o X das duplas
que não podem. Basta apagar de um lado: a planilha lê as duas células e proíbe a dupla se faltar X
em qualquer uma delas, e a formatação condicional pinta as duas de vermelho, para o veto aparecer
espelhado. A diagonal (a pessoa com ela mesma) vem em cinza, com um travessão.

A distribuição respeita: ao escolher a segunda pessoa de um ambiente, quem está sem X com a primeira
sai da lista de candidatos, e o passe de trocas desfaz qualquer troca que formaria um par proibido.
Se a coordenação montar a dupla à mão mesmo assim, a Situação do ambiente vira **DUPLA VETADA** e o
alerta nomeia as duas pessoas.

Quando alguém está sem X com todo mundo que sobrou, o ambiente fica com uma pessoa só (INCOMPLETO)
em vez de formar a dupla proibida — a planilha prefere mostrar o problema a escondê-lo. E se uma
linha inteira ficar sem X, a verificação **Técnicos sem afinidade com ninguém** e a fila de ações do
Painel avisam: quem está assim não forma dupla com pessoa alguma.

## Ausências

A aba **Folgas e Férias** guarda os períodos (folga, férias, atestado, licença, treinamento e os códigos
próprios do serviço). Ao lado dos registros fica o calendário do período (16 a 15), com o rodapé
**funcionários na data · vagas necessárias · déficit** dia a dia.

### Trocar a escala de folgas

Uma linha por período: técnico, tipo, data início, data fim. Um dia só = mesma data nas duas
colunas. O primeiro dia do período fica em **Configuração → seção 1 → Primeiro dia do período da
escala** (`Periodo_Ini`); trocar essa data move o calendário inteiro.

Lançar uma folga recalcula na hora **disponíveis**, **déficit** e a situação de cada técnico, mas
**não redistribui**: a dupla de cada ambiente é valor gravado, não fórmula. Enquanto a agenda não for
importada de novo, quem ficou de folga e continuou escalado aparece em **INDISPONÍVEL**, o alerta
nomeia a pessoa e o motivo, e a pendência sobe na fila de ações do Painel — logo abaixo de sala sem
equipe. Para redistribuir, é só importar a agenda do dia outra vez.

## Abas

| Aba | Para quê |
|---|---|
| `Painel` | a primeira tela: faixa do dia, números, o dia inteiro na linha do tempo, o que fazer agora, onde encaixar, risco de atraso |
| `Mapa do Dia` | o dia inteiro numa tabela: ambiente, dupla, situação, ocupação, sala vaga |
| `Agenda do Dia` | as cirurgias, vindas do PDF do hospital |
| `Equipe` | cadastro + o X de habilidade por especialidade |
| `Folgas e Férias` | períodos de ausência + calendário do período |
| `Configuração` | plantão, especialidades, postos, feriados, cirurgiões |
| `Calc`, `Calc_Salas` | ocultas — só cálculo |

## Regerar e validar

```bash
pip install openpyxl
python3 build_centro_cirurgico.py            # gera o .xlsx
soffice --headless --convert-to xlsx --outdir /tmp/rc Centro_Cirurgico_Escala.xlsx
python3 testes/t1_recalculo.py     /tmp/rc/Centro_Cirurgico_Escala.xlsx
python3 testes/t2_reconciliacao.py /tmp/rc/Centro_Cirurgico_Escala.xlsx
SAIDA=/tmp python3 testes/t3_expansao.py
SAIDA=/tmp python3 testes/t4_degenerado.py
SAIDA=/tmp python3 testes/t5_sensibilidade.py
SAIDA=/tmp python3 testes/t6_agenda.py
python3 testes/t7_distribuicao.py
python3 testes/t8_painel.py /tmp/rc/Centro_Cirurgico_Escala.xlsx
python3 testes/t9_estilo.py
python3 testes/t10_afinidade.py
python3 testes/t11_folgas.py
python3 testes/t12_excel.py Centro_Cirurgico_Escala.xlsx
```

| Teste | Resultado |
|---|---|
| Recálculo (LibreOffice) | 0 erros de fórmula |
| Reconciliação independente | 255 verificações, 0 divergências |
| Expansão (+1 especialidade, +1 sala, +2 técnicos, +30 cirurgias, +5 ausências) | 0 erros · 299 verificações, 0 divergências |
| Entradas degeneradas (9 na agenda, 3 em ausências, 6 na escala) | todas tratadas, 0 erros |
| Sensibilidade (domingo, feriado, limpeza, atraso, janela mínima) | aprovado, original inalterado |
| Importação da agenda (leitura, gravação, ocupação, janelas, atraso, alertas) | 19 verificações, 0 divergências |
| Distribuição (regras da alocação, vetos + conferência no arquivo) | 25 verificações, 0 divergências |
| Painel (números, linha do tempo, fila de ações, rankings) | 56 verificações, 0 divergências |
| Estilo (o XML que o Excel lê) | 6 verificações, 0 divergências |
| Afinidade (matriz da aba Equipe, leitura, distribuição e fórmula) | 19 verificações, 0 divergências |
| Troca da escala de folgas (folga após a importação, redistribuição, período) | 13 verificações, 0 divergências |
| O arquivo como o Excel vê (XML de dentro do .xlsx) | 6 arquivos, 0 desvios |

## O arquivo como o Excel vê

O LibreOffice — que é quem recalcula a planilha nos testes — abre coisa que o Excel recusa. Quando
o `.xlsx` foge do formato, o Excel não diz onde está o erro: abre perguntando *"encontramos um
problema em um conteúdo, quer que tentemos recuperar?"*. Nenhum dos outros testes pega isso, porque
para o LibreOffice o arquivo está bom.

Foi o que aconteceu com uma célula de texto vazio: `ws.cell(..., value="")` vira, no XML,
`<c t="inlineStr"/>` — uma célula que se declara texto e não traz texto nenhum, o que o formato não
permite. `sem_texto_vazio(wb)` (em `abas.py`) troca esses `""` por célula vazia antes de cada
gravação, tanto no gerador quanto na importação da agenda.

O `testes/t12_excel.py` varre o XML de dentro do arquivo atrás desses desvios — texto vazio,
elementos fora da ordem exigida, merges sobrepostos, prioridades repetidas, `dxfId` e `numFmt`
apontando para o vazio, células fora de ordem, fórmula longa ou aninhada além do limite do Excel.
Rode contra todo `.xlsx` que for entregue.

## Cadastro real

O gerador usa `dados/equipe_real.json` e `dados/cirurgioes_real.json` quando existem, gravando
`..._REAL.xlsx`. Esses arquivos e os `.xlsx` gerados a partir deles estão no `.gitignore`: **o
repositório é público e não recebe nome, COREN ou matrícula de ninguém — nem da equipe, nem dos
cirurgiões, nem de pacientes.** Rode `DEMO=1 python3 build_centro_cirurgico.py` para gerar a versão
de demonstração mesmo com o cadastro real presente.

## Formatação condicional: bgColor, não fgColor

Num **dxf** — o formato diferencial que a formatação condicional usa — o Excel pinta o fundo com
`bgColor` e ignora um `fgColor` sozinho. O LibreOffice aceita os dois. Como a validação recalcula
no LibreOffice, uma planilha inteira de regras pode passar em todos os testes de valor e chegar
sem cor nenhuma no Excel: foi exatamente o que aconteceu com a linha do tempo e com os alertas dos
indicadores.

Por isso todo preenchimento de regra passa por `cf_fill()`, que devolve `PatternFill(bgColor=...)`,
e o `t9_estilo.py` abre o `.xlsx` como zip e confere no `xl/styles.xml` que nenhum dxf de
preenchimento voltou a usar `fgColor`. Os preenchimentos fixos (cabeçalho, células de entrada)
continuam com `fgColor`, que é o correto fora do dxf.

## Limitações

* Só SUMIFS, COUNTIFS, SUMPRODUCT, INDEX, MATCH, LARGE, IF e IFERROR — compatível com Excel e
  LibreOffice. Sem macros, Power Query ou matrizes dinâmicas.
* Capacidades: 16 postos, 20 especialidades, 30 técnicos, 200 cirurgias/dia, 150 registros de
  ausência, 20 feriados, 60 cirurgiões, 13 janelas por sala, 8 ações visíveis no Painel.
* A importação lê o PDF com o `pypdf` (ou `pdftotext`, se o pypdf não estiver instalado) e depende
  do leiaute atual do relatório do hospital; nomes de procedimento longos já vêm cortados no
  próprio PDF.
* Uma escala por vez: para guardar o dia fechado, salve uma cópia do arquivo.
