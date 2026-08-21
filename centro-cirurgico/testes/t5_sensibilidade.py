# -*- coding: utf-8 -*-
"""Teste 5 — sensibilidade: alterar premissas percorre INPUT -> PROCESSAMENTO -> OUTPUT."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from abas import ABA_AGENDA, ABA_CFG, ABA_EQUIPE, ABA_FOLGAS, ABA_MAPA
import os, subprocess, shutil, openpyxl
from datetime import date
SP = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala.xlsx")
PAI_R1, N_POS, JOGO_K = 10, 16, 13

def recalc(path):
    out = os.path.join(SP, "rc5"); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    subprocess.run(["soffice", "--headless", "--norestore", "--convert-to", "xlsx",
                    "--outdir", out, path], capture_output=True)
    return openpyxl.load_workbook(os.path.join(out, os.path.basename(path)), data_only=True)

def cenario(tag, muda_cfg=None, data=None):
    wb = openpyxl.load_workbook(SRC)
    for cel, v in (muda_cfg or {}).items():
        wb[ABA_CFG][cel] = v
    if data:
        wb[ABA_MAPA]["A6"] = data
    f = os.path.join(SP, "t5_%s.xlsx" % tag); wb.save(f)
    return recalc(f)

def snap(wb):
    p = wb[ABA_MAPA]
    return dict(kpi=[p.cell(row=6, column=c).value for c in range(1, 9)],   # A..H
                vagas=p["F6"].value,
                sit=[p.cell(row=PAI_R1 + i, column=6).value for i in range(N_POS)],
                ocup=[p.cell(row=PAI_R1 + i, column=9).value for i in range(N_POS)],
                cabe=[p.cell(row=PAI_R1 + i, column=11).value for i in range(N_POS)],
                atraso=[p.cell(row=PAI_R1 + i, column=12).value for i in range(N_POS)],
                janelas=janelas_uteis(wb))


def janelas_uteis(wb):
    """Quantas janelas de cada sala passam do mínimo (lido direto do Calc_Salas)."""
    sal, minimo = wb["Calc_Salas"], wb[ABA_CFG]["B17"].value or 0
    return [sum(1 for k in range(JOGO_K)
                if isinstance(sal.cell(row=2 + i * JOGO_K + k, column=5).value, (int, float))
                and sal.cell(row=2 + i * JOGO_K + k, column=5).value >= minimo)
            for i in range(N_POS)]

base = snap(recalc(SRC)); falhas = []
print("BASE  indicadores:", base["kpi"][1:])

s = snap(cenario("domingo", data=date(2026, 8, 23)))
opera = sum(1 for x in s["sit"] if x not in (None, "", "NÃO OPERA"))
print("1) data -> domingo 23/08: vagas do dia %s (base %s), postos operando %d"
      % (s["vagas"], base["vagas"], opera),
      "OK" if s["vagas"] < base["vagas"] else "FALHOU")
if not s["vagas"] < base["vagas"]: falhas.append("domingo")

s = snap(cenario("feriado", data=date(2026, 9, 7)))
print("2) data -> feriado 07/09: vagas do dia %s" % s["vagas"],
      "OK" if s["vagas"] == 7 else "FALHOU (esperado 7)")
if s["vagas"] != 7: falhas.append("feriado")

LIMP_BASE = recalc(SRC)[ABA_CFG]["B16"].value or 0
s = snap(cenario("limpeza", {"B16": 40}))
pior = [i for i in range(N_POS)
        if isinstance(base["ocup"][i], float) and isinstance(s["ocup"][i], float)
        and s["ocup"][i] < base["ocup"][i] - 1e-9]
print("3) limpeza %s->40 min: ocupação sobe em toda sala com cirurgia:" % LIMP_BASE,
      "OK" if not pior else "FALHOU %s" % pior)
falhas += pior

soma = lambda d: sum(x for x in d["atraso"] if isinstance(x, (int, float)))
print("3b) limpeza %s->40 min: atraso previsto sobe de %s para %s min"
      % (LIMP_BASE, soma(base), soma(s)),
      "OK" if soma(s) > soma(base) else "FALHOU")
if soma(s) <= soma(base): falhas.append("atraso")

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
