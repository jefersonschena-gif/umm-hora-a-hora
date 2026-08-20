# Centro Cirúrgico — Escala Diária de Técnicos por Posto

Planilha operacional da coordenação de enfermagem: recebe a agenda cirúrgica do dia,
distribui os técnicos disponíveis pelos postos por prioridade, classifica cada posto pela
**afinidade de habilidade** da equipe alocada e mostra onde há espaço para encaixe.

**Arquivo:** `Centro_Cirurgico_Escala_Diaria_v2.xlsx`

## O serviço modelado

| Posto | Técnicos | Observação |
|---|---|---|
| Salas 1 a 8 | 2 cada (circulante + instrumentador) | Sala 6 exclusiva do centro obstétrico · Sala 7 reservada a urgências · Sala 8 oftalmológica |
| Admissão | 2 | opera com 1 no limite |
| Box de preparo oftalmológico | 1 | apoio da Sala 8 |
| Sala de recém-nascido | 1 | bloco obstétrico |
| **Total** | **20 vagas/dia** | contra um quadro de **22 técnicos** |

Plantão da **manhã, 07:00–13:00**. Limpeza e preparação: **20 min** após cada cirurgia.
10 habilidades por técnico. Não se realizam cirurgias cardíacas.
Cada posto declara em que dias funciona (Todos os dias / Seg a Sex / Seg a Sáb); nos fins de semana
e nos feriados cadastrados os postos de dia útil não operam, e as vagas do dia caem junto — é por isso
que um domingo pede 7 técnicos e não 20.

**O déficit é a regra**, não a exceção: com férias, folgas e atestados quase nunca há 20
técnicos disponíveis. Por isso cada posto tem **prioridade de cobertura** e **mínimo
aceitável**, e o Painel mostra o déficit do dia, os postos que ficam descobertos e quantas
cirurgias precisam de remanejamento.

## Premissas adotadas (documentadas na aba Instruções)

1. A escala cobre **um plantão** — o da manhã, 07:00–13:00, como na escala em uso.
2. O ciclo da escala vai do **dia 16 ao dia 15** do mês seguinte, como na escala em uso.
3. Nas salas os dois técnicos têm papéis distintos (circulante e instrumentador), com pesos
   diferentes na afinidade; nos postos de apoio não há distinção. Quando o cadastro traz todos
   como Téc.Enf., a Função entra como "Ambos".
4. Nos feriados os postos de dia útil seguem o regime de fim de semana.

## Arquitetura

| Camada | Abas |
|---|---|
| Entrada | `Parâmetros`, `Habilidades`, `Especialidades`, `Postos`, `Equipe`, `Matriz_Habilidades`, `Ausencias`, `Mapa_Cirurgico`, colunas TÉCNICO 1/2 da `Escala_Dia` |
| Processamento | `Calc_Mix` (minutos por habilidade em cada posto), `Calc_Afinidade` (técnicos disponíveis e ainda não escalados) |
| Saída | `Escala_Dia`, `Sugestao_Tecnicos`, `Jogo_de_Sala`, `Calendario_Ausencias`, `Painel`, `Base_Historico` |

### Regra de afinidade

```
afinidade(técnico, posto) = Σ minutos(habilidade) × nível(técnico, habilidade)
                            ─────────────────────────────────────────────────
                                      Σ minutos(habilidade)

afinidade(sala)  = Peso_Circulante × circulante + Peso_Instrumentador × instrumentador
afinidade(apoio) = média simples dos técnicos do posto
```

Níveis: 0 não apto · 1 em treinamento · 2 apto · 3 referência. Postos sem agenda (admissão,
box, RN, sala de urgência sem cirurgia marcada) usam a **habilidade de referência** cadastrada
em `Postos`. Pesos, limites e demais premissas ficam em `Parâmetros` — nenhuma constante de
negócio está embutida em fórmula.

### Jogo de sala

Para cada sala, a aba `Jogo_de_Sala` lista os intervalos livres: antes da primeira cirurgia,
entre a liberação de uma (fim + limpeza) e o início da seguinte, e da última até o fim do
plantão. Mostra início, fim, duração e **de quanto cabe um encaixe** (duração menos a limpeza),
marcando em verde as janelas ≥ `Janela_Min`. O `Mapa_Cirurgico` traz o mesmo em linha
("Sala liberada às" e "Livre até a próxima").

### Gestão de ausências

`Ausencias` guarda os períodos (folga, férias, atestado, licença, treinamento e os códigos próprios
do serviço). A aba `Equipe` mostra a situação de cada técnico na data da escala e o
`Calendario_Ausencias` dá a visão do período inteiro por técnico, com totais, destaque de registros
sobrepostos e, no rodapé, **funcionários na data · vagas necessárias · déficit** dia a dia — o mesmo
indicador da escala em uso, agora calculado por fórmula.

### Cadastro real

O gerador usa `dados/equipe_real.json` quando esse arquivo existe, gravando
`Centro_Cirurgico_Escala_Diaria_REAL.xlsx`. Esse arquivo e o `.xlsx` gerado a partir dele estão no
`.gitignore`: **o repositório é público e não recebe nome, COREN ou matrícula de ninguém.** Sem ele,
o gerador produz a versão de demonstração com cadastro fictício.

## Regerar a planilha

```bash
pip install openpyxl
python3 build_centro_cirurgico.py            # gera o .xlsx
VISUAL=1 python3 build_centro_cirurgico.py   # gera também a variante com áreas de impressão reduzidas
```

## Rodar a validação

Requer LibreOffice Calc (`soffice`) para recalcular o arquivo.

```bash
soffice --headless --convert-to xlsx --outdir /tmp/rc Centro_Cirurgico_Escala_Diaria_v2.xlsx
python3 testes/t1_recalculo.py      /tmp/rc/Centro_Cirurgico_Escala_Diaria_v2.xlsx
python3 testes/t2_reconciliacao.py  /tmp/rc/Centro_Cirurgico_Escala_Diaria_v2.xlsx
SAIDA=/tmp python3 testes/t3_expansao.py
SAIDA=/tmp python3 testes/t4_degenerado.py
SAIDA=/tmp python3 testes/t5_sensibilidade.py
```

## Resultado da validação (última execução)

| Teste | Resultado |
|---|---|
| Recálculo completo (LibreOffice) | 0 erros de fórmula |
| Reconciliação independente em Python | 338 verificações, 0 divergências |
| Expansão (+2 técnicos, +1 habilidade, +1 especialidade, +1 sala, +40 cirurgias, +5 ausências) | 0 erros · 399 verificações, 0 divergências |
| Entradas degeneradas (9 casos no mapa + 3 em ausências + 4 na escala) | todas tratadas, 0 erros de fórmula |
| Sensibilidade (pesos, meta, limpeza, janela mínima, data da escala) | aprovado, arquivo original inalterado |

## Limitações

* Compatibilidade deliberada com Excel e LibreOffice: só SUMIFS, COUNTIFS, SUMPRODUCT,
  INDEX, MATCH, LARGE, IF e IFERROR. Sem macros, Power Query, Power Pivot ou matrizes dinâmicas.
* Capacidades pré-dimensionadas: 16 postos, 14 habilidades, 24 especialidades, 30 técnicos,
  200 cirurgias/dia, 150 registros de ausência, 20 feriados, 31 dias de calendário, 13 janelas por
  sala, 2000 linhas de histórico.
* `Base_Historico` é alimentada por cópia/colagem de valores no fechamento do dia
  (materialização intencional: o histórico não deve se recalcular quando o mapa do dia
  seguinte for lançado).
* Equipe, habilidades, ausências e agenda são **dados de exemplo** — um dia com 18 técnicos
  disponíveis para 20 vagas — e precisam ser substituídos pelos dados reais do serviço.
