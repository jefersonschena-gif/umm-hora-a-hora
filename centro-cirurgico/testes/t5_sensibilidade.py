# -*- coding: utf-8 -*-
"""Teste 5 — sensibilidade: alterar premissas percorre INPUT -> PROCESSAMENTO -> OUTPUT."""
import os, subprocess, shutil, openpyxl
from datetime import date
SP = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala_Diaria_v2.xlsx")

def recalc(path):
    out = os.path.join(SP, "rc5"); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    subprocess.run(["soffice", "--headless", "--norestore", "--convert-to", "xlsx",
                    "--outdir", out, path], capture_output=True)
    return openpyxl.load_workbook(os.path.join(out, os.path.basename(path)), data_only=True)

def cenario(tag, muda):
    wb = openpyxl.load_workbook(SRC)
    for cel, v in muda.items():
        wb["Parâmetros"][cel] = v
    f = os.path.join(SP, "t5_%s.xlsx" % tag); wb.save(f)
    return recalc(f)

def snap(wb):
    e, p, j = wb["Escala_Dia"], wb["Painel"], wb["Jogo_de_Sala"]
    return dict(
        afin={e.cell(row=r, column=2).value: e.cell(row=r, column=16).value
              for r in range(2, 18) if e.cell(row=r, column=2).value},
        a2={e.cell(row=r, column=2).value: e.cell(row=r, column=15).value
            for r in range(2, 18) if e.cell(row=r, column=2).value},
        ocup={e.cell(row=r, column=2).value: e.cell(row=r, column=9).value
              for r in range(2, 18) if e.cell(row=r, column=2).value},
        classe=[e.cell(row=r, column=18).value for r in range(2, 18)],
        kpi=[p.cell(row=6, column=c).value for c in range(2, 9)],
        cob=[p.cell(row=10, column=c).value for c in range(1, 9)],
        janelas=[j.cell(row=r, column=5).value for r in range(2, 210)],
        aprov=sum(1 for r in range(2, 210) if j.cell(row=r, column=7).value == "Janela aproveitável"))

base = snap(recalc(SRC)); falhas = []
print("BASE  cobertura:", base["cob"], "| janelas aproveitáveis:", base["aprov"])

s = snap(cenario("pesos", {"B22": 1.0, "B23": 0.0}))
d = [k for k in s["afin"] if isinstance(s["afin"][k], (int, float)) and isinstance(s["a2"][k], (int, float))
     and abs(s["afin"][k] - s["a2"][k]) > 1e-9]
print("1) pesos 1,00/0,00 -> afinidade do posto = do instrumentador:", "OK" if not d else "FALHOU %s" % d[:3])
falhas += d

for meta, minimo in ((3.50, 2.90), (1.00, 0.50)):
    s = snap(cenario("meta%s" % meta, {"B25": meta, "B26": minimo}))
    vals = [v for v in base["afin"].values() if isinstance(v, (int, float))]
    esp = (sum(1 for v in vals if v >= meta), sum(1 for v in vals if minimo <= v < meta),
           sum(1 for v in vals if v < minimo))
    obt = (s["classe"].count("ADEQUADO"), s["classe"].count("ATENÇÃO"), s["classe"].count("CRÍTICO"))
    ok = obt == esp
    print("2) meta=%.2f min=%.2f -> ADEQUADO/ATENÇÃO/CRÍTICO %s (esperado %s)" % (meta, minimo, obt, esp),
          "OK" if ok else "FALHOU")
    if not ok: falhas.append("meta%s" % meta)

s = snap(cenario("limpeza", {"B31": 40}))
ruim = []
for k, v in base["ocup"].items():
    if not isinstance(v, (int, float)):
        continue
    if not (s["ocup"][k] > v - 1e-9):
        ruim.append((k, v, s["ocup"][k]))
print("3) limpeza 20->40 min -> ocupação sobe em toda sala com cirurgia:",
      "OK" if not ruim else "FALHOU %s" % ruim[:2])
falhas += ruim

s = snap(cenario("janela", {"B32": 90}))
print("4) janela mínima 30->90 min -> janelas aproveitáveis: %d (base %d)" % (s["aprov"], base["aprov"]),
      "OK" if s["aprov"] <= base["aprov"] else "FALHOU")
if s["aprov"] > base["aprov"]: falhas.append("janela")

s = snap(cenario("data", {"B6": date(2026, 8, 21)}))
print("5) data 20/08 -> 21/08 -> cobertura recalculada pelas ausências:", s["cob"][:5],
      "(base %s)" % base["cob"][:5], "OK" if s["cob"] != base["cob"] else "FALHOU: não mudou")
if s["cob"] == base["cob"]: falhas.append("data")

s = snap(recalc(SRC))
igual = s["afin"] == base["afin"] and s["cob"] == base["cob"]
print("6) arquivo original inalterado após os testes:", "OK" if igual else "FALHOU")
print("\nRESULTADO TESTE 5:", "APROVADO" if not falhas and igual else "REPROVADO")
