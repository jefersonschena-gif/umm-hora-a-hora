# -*- coding: utf-8 -*-
"""Teste 5 — sensibilidade: alterar premissas percorre INPUT -> PROCESSAMENTO -> OUTPUT."""
import os, subprocess, shutil, openpyxl
from datetime import date
SP = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala.xlsx")
PAI_R1, N_POS, JOG_R1 = 10, 16, 28

def recalc(path):
    out = os.path.join(SP, "rc5"); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    subprocess.run(["soffice", "--headless", "--norestore", "--convert-to", "xlsx",
                    "--outdir", out, path], capture_output=True)
    return openpyxl.load_workbook(os.path.join(out, os.path.basename(path)), data_only=True)

def cenario(tag, muda_cfg=None, data=None):
    wb = openpyxl.load_workbook(SRC)
    for cel, v in (muda_cfg or {}).items():
        wb["Configuração"][cel] = v
    if data:
        wb["Painel"]["B6"] = data
    f = os.path.join(SP, "t5_%s.xlsx" % tag); wb.save(f)
    return recalc(f)

def snap(wb):
    p = wb["Painel"]
    return dict(kpi=[p.cell(row=6, column=c).value for c in range(4, 12)],
                sit=[p.cell(row=PAI_R1 + i, column=9).value for i in range(N_POS)],
                ocup=[p.cell(row=PAI_R1 + i, column=5).value for i in range(N_POS)],
                livre=[p.cell(row=JOG_R1 + i, column=3).value for i in range(N_POS)],
                janelas=[p.cell(row=JOG_R1 + i, column=8).value for i in range(N_POS)])

base = snap(recalc(SRC)); falhas = []
print("BASE  indicadores:", base["kpi"])

s = snap(cenario("domingo", data=date(2026, 8, 23)))
opera = sum(1 for x in s["sit"] if x not in (None, "", "NÃO OPERA"))
print("1) data -> domingo 23/08: vagas do dia %s (base %s), postos operando %d"
      % (s["kpi"][3], base["kpi"][3], opera),
      "OK" if s["kpi"][3] < base["kpi"][3] else "FALHOU")
if not s["kpi"][3] < base["kpi"][3]: falhas.append("domingo")

s = snap(cenario("feriado", data=date(2026, 9, 7)))
print("2) data -> feriado 07/09: vagas do dia %s" % s["kpi"][3],
      "OK" if s["kpi"][3] == 7 else "FALHOU (esperado 7)")
if s["kpi"][3] != 7: falhas.append("feriado")

s = snap(cenario("limpeza", {"B16": 40}))
pior = [i for i in range(N_POS)
        if isinstance(base["ocup"][i], float) and isinstance(s["ocup"][i], float)
        and s["ocup"][i] < base["ocup"][i] - 1e-9]
print("3) limpeza 20->40 min: ocupação sobe em toda sala com cirurgia:",
      "OK" if not pior else "FALHOU %s" % pior)
falhas += pior

s = snap(cenario("janela", {"B17": 120}))
print("4) janela mínima 30->120 min: janelas aproveitáveis %s (base %s)"
      % (sum(x for x in s["janelas"] if isinstance(x, int)),
         sum(x for x in base["janelas"] if isinstance(x, int))),
      "OK" if sum(x for x in s["janelas"] if isinstance(x, int)) <=
              sum(x for x in base["janelas"] if isinstance(x, int)) else "FALHOU")

s = snap(recalc(SRC))
igual = s["kpi"] == base["kpi"] and s["sit"] == base["sit"]
print("5) arquivo original inalterado após os testes:", "OK" if igual else "FALHOU")
print("\nRESULTADO TESTE 5:", "APROVADO" if not falhas and igual else "REPROVADO")
