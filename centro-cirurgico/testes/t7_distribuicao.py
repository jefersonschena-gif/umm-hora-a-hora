# -*- coding: utf-8 -*-
"""Teste 7 — distribuição dos técnicos: regras da alocação e conferência no arquivo gerado."""
import os
import sys
from datetime import datetime

import openpyxl

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from abas import ABA_AGENDA, ABA_CFG, ABA_EQUIPE, ABA_FOLGAS, ABA_MAPA
from alocacao import alocar

res, ok = [], 0
def chk(nome, esperado, obtido):
    global ok
    bate = esperado == obtido
    ok += bate
    res.append("%-52s esperado %-22s obtido %-22s %s" % (nome, esperado, obtido,
                                                         "ok" if bate else "DIVERGE"))

# ---------------------------------------------------------------- regras da alocação
POSTOS = [("S1", 2, 2, 5), ("S2", 2, 2, 6), ("S3", 2, 2, 9), ("ADM", 2, 1, 4), ("RN", 1, 1, 3)]
ESP = {"S1": ["Ortopedia"], "S2": ["Cirurgia Geral"], "S3": ["Neurocirurgia"],
       "ADM": ["Admissão"], "RN": ["Sala de recém-nascido"]}
SK = {"Ana": {"Ortopedia"}, "Bia": {"Ortopedia", "Cirurgia Geral"}, "Cris": {"Cirurgia Geral"},
      "Dai": {"Admissão"}, "Edu": {"Admissão", "Sala de recém-nascido"},
      "Fabi": {"Neurocirurgia"}, "Gi": {"Sala de recém-nascido"}, "Hel": {"Neurocirurgia"},
      "Ivo": set()}
TODOS = sorted(SK)

a = alocar(POSTOS, ESP, TODOS, SK)
escalados = [n for v in a.values() for n in v]
chk("ninguém escalado em dois lugares", len(escalados), len(set(escalados)))
chk("só entra quem está na lista", True, set(escalados) <= set(TODOS))
chk("nenhum posto passa do necessário", True,
    all(len(a[c]) <= nec for c, nec, _, _ in POSTOS))
chk("com gente sobrando, todos os postos completos", 9, len(escalados))
chk("quem só faz neuro foi para a neuro", True, set(a["S3"]) == {"Fabi", "Hel"})
chk("quem só faz RN foi para o RN", ["Gi"], a["RN"])

# falta gente: 5 pessoas para 9 vagas
a2 = alocar(POSTOS, ESP, ["Ana", "Cris", "Dai", "Fabi", "Gi"], SK)
esc2 = [n for v in a2.values() for n in v]
chk("com déficit, ninguém repetido", len(esc2), len(set(esc2)))
chk("com déficit, todos os 5 são usados", 5, len(esc2))
prio = {c: p for c, _, _, p in POSTOS}
minimo = {c: m for c, _, m, _ in POSTOS}
faltou = [c for c in a2 if len(a2[c]) < minimo[c]]
depois = [c for c in a2 if faltou and prio[c] > min(prio[f] for f in faltou)]
chk("abaixo do mínimo só nos postos de prioridade mais baixa", True,
    all(len(a2[c]) == 0 or len(a2[c]) < minimo[c] for c in depois))

chk("sem ninguém disponível, nenhum posto recebe", 0,
    len([n for v in alocar(POSTOS, ESP, [], SK).values() for n in v]))
chk("matriz de habilidades em branco ainda distribui", 9,
    len([n for v in alocar(POSTOS, ESP, TODOS, {n: set() for n in TODOS}).values() for n in v]))
chk("resultado é estável entre execuções", alocar(POSTOS, ESP, TODOS, SK), a)

# ---------------------------------------------------------------- conferência no arquivo
ARQ = os.environ.get("ARQ", os.path.join(RAIZ, "Centro_Cirurgico_Escala.xlsx"))
wb = openpyxl.load_workbook(ARQ)
pai, eqp, aus, cfg = wb[ABA_MAPA], wb[ABA_EQUIPE], wb[ABA_FOLGAS], wb[ABA_CFG]
dia = pai["A6"].value
dia = dia.date() if isinstance(dia, datetime) else dia

dupla = [(pai.cell(row=r, column=4).value, pai.cell(row=r, column=5).value)
         for r in range(10, 26)]
nomes = [n for d in dupla for n in d if n]
chk("arquivo: ninguém em dois ambientes", len(nomes), len(set(nomes)))

status = {eqp.cell(row=r, column=2).value: eqp.cell(row=r, column=4).value
          for r in range(2, 32) if eqp.cell(row=r, column=2).value}
chk("arquivo: ninguém inativo escalado", [],
    [n for n in nomes if status.get(n) != "Ativo"])

fora = []
for r in range(2, 152):
    t = aus.cell(row=r, column=1).value
    ini, fim = aus.cell(row=r, column=3).value, aus.cell(row=r, column=4).value
    if t and ini and fim:
        i = ini.date() if isinstance(ini, datetime) else ini
        f = fim.date() if isinstance(fim, datetime) else fim
        if i <= dia <= f and t in nomes:
            fora.append(t)
chk("arquivo: ninguém de folga/férias/atestado escalado", [], sorted(set(fora)))

print("\n".join(res))
print("\nTESTE 7 (distribuição): %d/%d" % (ok, len(res)))
sys.exit(0 if ok == len(res) else 1)
