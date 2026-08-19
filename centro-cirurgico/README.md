# Centro Cirúrgico — Mapa Cirúrgico e Escala de Duplas por Sala

Planilha operacional para a coordenação de enfermagem do centro cirúrgico:
lança o mapa cirúrgico do dia, escala a **dupla fixa por sala no turno**
(circulante + instrumentador) e classifica cada dupla por **afinidade de habilidade**
com o mix de especialidades daquela sala naquele turno.

**Arquivo entregue:** `Centro_Cirurgico_Escala_Duplas_v1.xlsx` (8 salas, 3 turnos, 14 especialidades,
60 técnicos de exemplo — substituir pelos dados reais do serviço).

## Arquitetura

| Camada | Abas |
|---|---|
| Entrada | `Parâmetros`, `Especialidades`, `Salas`, `Equipe`, `Matriz_Habilidades`, `Mapa_Cirurgico`, colunas CIRCULANTE/INSTRUMENTADOR de `Escala_Duplas` |
| Processamento | `Calc_Mix` (minutos por especialidade em cada sala × turno), `Calc_Afinidade` (afinidade dos técnicos elegíveis) |
| Saída | `Escala_Duplas`, `Sugestao_Duplas`, `Painel`, `Base_Historico` |

### Regra de afinidade

```
afinidade(técnico, sala, turno) = Σ minutos(especialidade) × nível(técnico, especialidade)
                                  ─────────────────────────────────────────────────────
                                            Σ minutos(especialidade)

afinidade(dupla) = Peso_Circulante × afin(circulante) + Peso_Instrumentador × afin(instrumentador)
```

Níveis: 0 não apto · 1 em treinamento · 2 apto · 3 referência.
Limites (`Afinidade_Meta`, `Afinidade_Min`), pesos e demais premissas ficam em `Parâmetros` —
nenhuma constante de negócio está embutida em fórmula.

## Regerar a planilha

```bash
pip install openpyxl
python3 build_centro_cirurgico.py            # gera o .xlsx
VISUAL=1 python3 build_centro_cirurgico.py   # gera também a variante com áreas de impressão reduzidas
```

## Rodar a validação

Requer LibreOffice Calc (`soffice`) para recalcular o arquivo.

```bash
soffice --headless --convert-to xlsx --outdir /tmp/rc Centro_Cirurgico_Escala_Duplas_v1.xlsx
python3 testes/t1_recalculo.py      /tmp/rc/Centro_Cirurgico_Escala_Duplas_v1.xlsx   # erros de fórmula
python3 testes/t2_reconciliacao.py  /tmp/rc/Centro_Cirurgico_Escala_Duplas_v1.xlsx   # recálculo independente
SAIDA=/tmp python3 testes/t3_expansao.py       # +20 cirurgias, +1 especialidade, +1 sala, +2 técnicos
SAIDA=/tmp python3 testes/t4_degenerado.py     # entradas inválidas
SAIDA=/tmp python3 testes/t5_sensibilidade.py  # propagação das premissas
```

## Resultado da validação (última execução)

| Teste | Resultado |
|---|---|
| Recálculo completo (LibreOffice) | 0 erros de fórmula |
| Reconciliação independente em Python | 318 verificações, 0 divergências |
| Expansão multidimensional | 0 erros · 351 verificações, 0 divergências |
| Entradas degeneradas (8 casos) | 8/8 tratadas, 0 erros de fórmula |
| Sensibilidade das premissas | aprovado, arquivo original inalterado |

## Limitações

* Compatibilidade deliberada com Excel e LibreOffice: só SUMIFS, COUNTIFS, SUMPRODUCT,
  INDEX, MATCH, LARGE, IF e IFERROR. Sem macros, Power Query, Power Pivot ou matrizes dinâmicas.
* Capacidades pré-dimensionadas: 12 salas, 20 especialidades, 150 técnicos, 300 cirurgias/dia,
  2000 linhas de histórico. Acima disso é preciso estender os intervalos.
* `Base_Historico` é alimentada por cópia/colagem de valores no fechamento do dia (materialização
  intencional: histórico não deve se recalcular quando o mapa do dia seguinte for lançado).
