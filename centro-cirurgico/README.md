# Centro Cirúrgico — Escala Diária

Planilha operacional da coordenação de enfermagem. **Tudo do dia acontece no Painel**: a data,
os indicadores, a escala dos técnicos por posto, o jogo de sala e quem está disponível. As outras
abas são cadastro.

**Arquivo:** `Centro_Cirurgico_Escala.xlsx` (demonstração) · `..._REAL.xlsx` quando há cadastro real.

## O serviço

| Posto | Técnicos | Observação |
|---|---|---|
| Salas 1 a 8 | 2 cada | Sala 6 exclusiva do centro obstétrico · Sala 7 reservada a urgências · Sala 8 oftalmológica |
| Admissão | 2 | opera com 1 no limite |
| Box de preparo oftalmológico | 1 | apoio da Sala 8 |
| Sala de recém-nascido | 1 | bloco obstétrico |
| **Total** | **20 vagas/dia** | para um quadro de **22 técnicos** |

Plantão da manhã, 07:00–13:00. **20 min** de limpeza e preparação após cada cirurgia.
Não se realizam cirurgias cardíacas. Cada posto declara em que dias funciona; nos fins de semana e
feriados os postos de dia útil não operam e as vagas do dia caem junto.

## Habilidade: um X por especialidade

Na aba **Equipe**, uma coluna por especialidade. Marque **X** onde o técnico faz aquela cirurgia;
deixe em branco onde não faz. As colunas vêm da lista de especialidades da aba Configuração.

A planilha cruza as especialidades que passam em cada sala no dia com o X dos dois técnicos
escalados e devolve a **Situação** do posto:

| Situação | Significa |
|---|---|
| **OK** | os dois técnicos cobrem todas as especialidades do dia |
| **ATENÇÃO** | alguma especialidade é coberta por um só dos dois |
| **FALTA HABILIDADE** | alguma especialidade do dia não é coberta por ninguém da dupla (o alerta diz qual) |
| **INCOMPLETO** | falta técnico no posto |
| **SEM EQUIPE** | ninguém escalado — o alerta diz quantas cirurgias precisam ser remanejadas |
| **NÃO OPERA** | posto fechado nesse dia da semana |
| **SEM AVALIAÇÃO** | algum técnico escalado ainda não tem X marcado |

## Jogo de sala

O bloco 3 do Painel mostra, para cada sala: ocupação, total de minutos livres, a **maior janela
livre com horário** ("11:05 → 13:00 (115 min)"), de quanto cabe um encaixe já descontada a limpeza,
a segunda maior janela e quantas janelas passam do mínimo. O `Mapa_Cirurgico` traz o mesmo em linha,
cirurgia a cirurgia.

## Importar a agenda do hospital

A agenda diária chega em PDF (mapa do centro cirúrgico do sistema do hospital). O
`importar_agenda.py` lê esse PDF e escreve as cirurgias direto no `Mapa_Cirurgico`:

```bash
python3 importar_agenda.py AGENDA_21.08.pdf Centro_Cirurgico_Escala.xlsx
# -> Centro_Cirurgico_Escala_2026-08-21.xlsx (o arquivo de entrada nunca é sobrescrito)
```

O que entra: sala, hora de início, hora de término, procedimento e cirurgião. Os dados de paciente
do PDF (nome, prontuário, nascimento, convênio, leito) **não são lidos nem gravados**.

O PDF não traz a especialidade da cirurgia, traz o cirurgião. A seção **8. CIRURGIÕES** da aba
Configuração faz o de/para: preenchida uma vez, a importação passa a preencher a coluna
Especialidade sozinha; todo cirurgião novo é acrescentado ali em branco para a coordenação
classificar.

A importação substitui apenas as linhas da data importada — outras datas no mapa ficam intactas —
e aponta a DATA DA ESCALA do Painel para o dia importado.

Duas coisas que a agenda do hospital costuma trazer e a planilha sinaliza no `Mapa_Cirurgico`:

* **Fora da janela do plantão** — cirurgia que começa ou termina depois das 13:00. Ela entra no
  mapa, mas só os minutos dentro do plantão contam na ocupação.
* **Sem intervalo para limpeza** — a agenda emenda a próxima cirurgia antes dos 20 min de limpeza.

## Ausências

A aba **Ausencias** guarda os períodos (folga, férias, atestado, licença, treinamento e os códigos
próprios do serviço). Ao lado dos registros fica o calendário do período (16 a 15), com o rodapé
**funcionários na data · vagas necessárias · déficit** dia a dia.

## Abas

| Aba | Para quê |
|---|---|
| `Painel` | o dia inteiro: indicadores, escala, jogo de sala, equipe de hoje, verificações |
| `Mapa_Cirurgico` | a agenda que chega todo dia |
| `Equipe` | cadastro + o X de habilidade por especialidade |
| `Ausencias` | períodos de ausência + calendário do período |
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
```

| Teste | Resultado |
|---|---|
| Recálculo (LibreOffice) | 0 erros de fórmula |
| Reconciliação independente | 246 verificações, 0 divergências |
| Expansão (+1 especialidade, +1 sala, +2 técnicos, +30 cirurgias, +5 ausências) | 0 erros · 289 verificações, 0 divergências |
| Entradas degeneradas (9 no mapa, 3 em ausências, 4 na escala) | todas tratadas, 0 erros |
| Sensibilidade (domingo, feriado, limpeza, janela mínima) | aprovado, original inalterado |
| Importação da agenda (leitura, gravação, ocupação, janelas, alertas) | 16 verificações, 0 divergências |

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
* A importação depende do `pdftotext` (poppler-utils) e do leiaute atual do relatório do
  hospital; nomes de procedimento longos já vêm cortados no próprio PDF.
* Uma escala por vez: para guardar o dia fechado, salve uma cópia do arquivo.
