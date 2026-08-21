# Centro Cirúrgico — Escala Diária

Planilha operacional da coordenação de enfermagem. **Tudo do dia acontece na aba Mapa do Dia**,
e ela já chega preenchida: cada ambiente com a sua dupla, as especialidades que passam ali, a
ocupação e o tempo em que a sala fica vaga. As outras abas são cadastro.

**Arquivo:** `Centro_Cirurgico_Escala.xlsx` (demonstração) · `..._REAL.xlsx` quando há cadastro real.

## O serviço

| Posto | Técnicos | Observação |
|---|---|---|
| Salas 1 a 8 | 2 cada | Sala 6 exclusiva do centro obstétrico · Sala 7 reservada a urgências · Sala 8 oftalmológica |
| Admissão | 2 | opera com 1 no limite |
| Box de preparo oftalmológico | 1 | apoio da Sala 8 |
| Sala de recém-nascido | 1 | bloco obstétrico |
| **Total** | **20 vagas/dia** | para um quadro de **22 técnicos** |

Plantão da manhã, 07:00–13:00. A agenda do hospital **já reserva a limpeza dentro do horário de
cada cirurgia** — o término é a sala liberada, e por isso a premissa *Limpeza a acrescentar* fica em
**0** na aba Configuração. Se um dia a agenda passar a trazer só o tempo cirúrgico, basta pôr 20 ali
que todas as contas voltam a somar.
Não se realizam cirurgias cardíacas. Cada posto declara em que dias funciona; nos fins de semana e
feriados os postos de dia útil não operam e as vagas do dia caem junto.

## Habilidade: um X por especialidade

Na aba **Equipe**, uma coluna por especialidade. Marque **X** onde o técnico faz aquela cirurgia;
deixe em branco onde não faz. As colunas vêm da lista de especialidades da aba Configuração.

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
   seguintes.

Depois roda um passe de trocas: qualquer troca entre dois postos que aumente a cobertura total é
aceita, até não haver mais ganho. Com a matriz de habilidades ainda em branco a distribuição
acontece do mesmo jeito, e a Situação de cada posto fica em SEM AVALIAÇÃO até o X ser marcado.

Trocar a data na planilha **não** redistribui — para redistribuir, importe a agenda de novo.

## Jogo de sala

Na mesma linha de cada ambiente: ocupação, a **maior janela livre com horário** ("11:00 → 13:00"),
quantos minutos ela tem e quantas outras janelas passam do mínimo. Como a limpeza já vem dentro do
horário de cada cirurgia, a janela inteira é aproveitável para um encaixe. A aba `Agenda do Dia`
traz o mesmo cirurgia a cirurgia.

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

Duas coisas que a agenda do hospital costuma trazer e a planilha sinaliza na aba `Agenda do Dia`:

* **Fora da janela do plantão** — cirurgia que começa ou termina depois das 13:00. Ela entra no
  mapa, mas só os minutos dentro do plantão contam na ocupação.
* **Sem intervalo para limpeza** — só aparece se a premissa *Limpeza a acrescentar* for maior que
  zero e a agenda emendar a cirurgia seguinte antes desse tempo.

## Ausências

A aba **Folgas e Férias** guarda os períodos (folga, férias, atestado, licença, treinamento e os códigos
próprios do serviço). Ao lado dos registros fica o calendário do período (16 a 15), com o rodapé
**funcionários na data · vagas necessárias · déficit** dia a dia.

## Abas

| Aba | Para quê |
|---|---|
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
```

| Teste | Resultado |
|---|---|
| Recálculo (LibreOffice) | 0 erros de fórmula |
| Reconciliação independente | 255 verificações, 0 divergências |
| Expansão (+1 especialidade, +1 sala, +2 técnicos, +30 cirurgias, +5 ausências) | 0 erros · 299 verificações, 0 divergências |
| Entradas degeneradas (9 na agenda, 3 em ausências, 5 na escala) | todas tratadas, 0 erros |
| Sensibilidade (domingo, feriado, limpeza, janela mínima) | aprovado, original inalterado |
| Importação da agenda (leitura, gravação, ocupação, janelas, alertas) | 16 verificações, 0 divergências |
| Distribuição (regras da alocação + conferência no arquivo) | 15 verificações, 0 divergências |

## Cadastro real

O gerador usa `dados/equipe_real.json` e `dados/cirurgioes_real.json` quando existem, gravando
`..._REAL.xlsx`. Esses arquivos e os `.xlsx` gerados a partir deles estão no `.gitignore`: **o
repositório é público e não recebe nome, COREN ou matrícula de ninguém — nem da equipe, nem dos
cirurgiões, nem de pacientes.** Rode `DEMO=1 python3 build_centro_cirurgico.py` para gerar a versão
de demonstração mesmo com o cadastro real presente.

## Limitações

* Só SUMIFS, COUNTIFS, SUMPRODUCT, INDEX, MATCH, LARGE, IF e IFERROR — compatível com Excel e
  LibreOffice. Sem macros, Power Query ou matrizes dinâmicas.
* Capacidades: 16 postos, 20 especialidades, 30 técnicos, 200 cirurgias/dia, 150 registros de
  ausência, 20 feriados, 60 cirurgiões, 13 janelas por sala.
* A importação lê o PDF com o `pypdf` (ou `pdftotext`, se o pypdf não estiver instalado) e depende
  do leiaute atual do relatório do hospital; nomes de procedimento longos já vêm cortados no
  próprio PDF.
* Uma escala por vez: para guardar o dia fechado, salve uma cópia do arquivo.
