# -*- coding: utf-8 -*-
"""Teste 8 — Painel: os números, a fila de ações e os dois rankings, recalculados por fora
a partir do Mapa do Dia e comparados com o que o Painel mostra."""
import os
import sys

import openpyxl

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from abas import ABA_CFG, ABA_EQUIPE, ABA_MAPA, ABA_PAINEL

ARQ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "Centro_Cirurgico_Escala.xlsx")
wb = openpyxl.load_workbook(ARQ, data_only=True)
pai, mapa, cfg, eqp = wb[ABA_PAINEL], wb[ABA_MAPA], wb[ABA_CFG], wb[ABA_EQUIPE]

PAI_R1, N_POS, POS_R1 = 10, 16, 45
ACO_P1, ENC_P1, ATR_P1 = 12, 22, 27
JANELA = cfg["B17"].value or 0

N = lambda v: v if isinstance(v, (int, float)) else 0   # célula vazia ou texto conta como 0

res, ok = [], 0
def chk(nome, esperado, obtido):
    global ok
    bate = esperado == obtido
    ok += bate
    res.append("%-46s esperado %-30s obtido %-30s %s"
               % (nome, esperado, obtido, "ok" if bate else "DIVERGE"))

# --- o que o Mapa do Dia diz, lido linha a linha
LIN = []
for i in range(N_POS):
    r = PAI_R1 + i
    nome = mapa.cell(row=r, column=1).value
    if not nome:
        continue
    LIN.append(dict(nome=nome, pede=mapa.cell(row=r, column=2).value,
                    sit=mapa.cell(row=r, column=6).value,
                    alerta=mapa.cell(row=r, column=7).value,
                    cir=mapa.cell(row=r, column=8).value,
                    janela=mapa.cell(row=r, column=10).value,
                    cabe=mapa.cell(row=r, column=11).value,
                    atraso=mapa.cell(row=r, column=12).value,
                    encaixe=next(cfg.cell(row=x, column=11).value for x in range(POS_R1, POS_R1 + N_POS)
                                 if cfg.cell(row=x, column=2).value == nome)))

# --- 1. números do dia
num = lambda col: pai.cell(row=9, column=col).value
chk("ambientes abertos", sum(1 for l in LIN if N(l["pede"]) > 0), num(3))
chk("prontos", sum(1 for l in LIN if l["sit"] == "OK"), num(4))
chk("com pendência", sum(1 for l in LIN if l["sit"] not in (None, "", "OK", "NÃO OPERA")), num(5))
chk("disponíveis", sum(1 for r in range(2, 32)
                       if eqp.cell(row=r, column=5).value == "Disponível"), num(6))
chk("maior atraso", max([N(l["atraso"]) for l in LIN] + [0]), num(8))

# --- 2. fila de ações
GRAV = {"SEM EQUIPE": 900, "FALTA HABILIDADE": 800, "GENTE DEMAIS": 700, "INCOMPLETO": 650,
        "EXTRA": 600, "ATENÇÃO": 400, "SEM AVALIAÇÃO": 300}
matriz_vazia = sum(1 for r in range(2, 32) for c in range(8, 28)
                   if str(eqp.cell(row=r, column=c).value or "").strip().upper() == "X") == 0
esperadas = []
for l in LIN:
    g = GRAV.get(l["sit"], 0)
    if l["sit"] == "SEM EQUIPE" and N(l["cir"]) <= 0:
        g = 850
    if l["sit"] == "SEM AVALIAÇÃO" and matriz_vazia:
        g = 0
    if g:
        esperadas.append((g, "%s · %s" % (l["nome"], l["alerta"])))
globais = sum(1 for r in range(ACO_P1, ACO_P1 + 8)
              if pai.cell(row=r, column=9).value and pai.cell(row=r, column=9).value >= 970)
mostradas = [pai.cell(row=r, column=2).value for r in range(ACO_P1, ACO_P1 + 8)
             if pai.cell(row=r, column=2).value]
notas = [pai.cell(row=r, column=9).value for r in range(ACO_P1, ACO_P1 + 8)
         if pai.cell(row=r, column=2).value]

chk("fila em ordem decrescente de gravidade", True, notas == sorted(notas, reverse=True))
chk("ações de ambiente listadas", min(len(esperadas), 8 - globais), len(mostradas) - globais)
chk("primeira ação de ambiente confere",
    sorted(esperadas, reverse=True)[0][1] if esperadas else None,
    mostradas[globais] if len(mostradas) > globais else None)
chk("nenhum ambiente OK na fila", [],
    [t for t in mostradas for l in LIN if l["sit"] == "OK" and t.startswith(l["nome"] + " ·")])

banner = pai["A6"].value
maior = max(notas) if notas else 0
chk("faixa do dia", ("AÇÃO NECESSÁRIA" if maior >= 900 else "ATENÇÃO" if maior >= 600
                     else "QUASE PRONTO" if maior >= 1 else "DIA FECHADO — nada pendente"), banner)

# --- 3. onde encaixar: só salas que aceitam encaixe, em ordem
cand = sorted([l for l in LIN if l["encaixe"] == "Sim" and isinstance(l["cabe"], (int, float))
               and l["cabe"] >= JANELA], key=lambda l: -l["cabe"])[:3]
for i in range(3):
    r = ENC_P1 + i
    chk("encaixe %d ambiente" % (i + 1), cand[i]["nome"] if i < len(cand) else None,
        pai.cell(row=r, column=2).value)
    chk("encaixe %d cabe até" % (i + 1), cand[i]["cabe"] if i < len(cand) else None,
        pai.cell(row=r, column=4).value)
chk("nenhuma sala que não aceita encaixe no ranking", [],
    [pai.cell(row=ENC_P1 + i, column=2).value for i in range(3)
     for l in LIN if l["encaixe"] != "Sim" and l["nome"] == pai.cell(row=ENC_P1 + i, column=2).value])

# --- 4. risco de atraso
atr = sorted([l for l in LIN if isinstance(l["atraso"], (int, float)) and l["atraso"] > 0],
             key=lambda l: -l["atraso"])[:3]
for i in range(3):
    r = ATR_P1 + i
    chk("atraso %d ambiente" % (i + 1), atr[i]["nome"] if i < len(atr) else None,
        pai.cell(row=r, column=2).value)
    chk("atraso %d minutos" % (i + 1), atr[i]["atraso"] if i < len(atr) else None,
        pai.cell(row=r, column=3).value)

print("\n".join(res))
print("\nTESTE 8 (painel): %d/%d" % (ok, len(res)))
sys.exit(0 if ok == len(res) else 1)
