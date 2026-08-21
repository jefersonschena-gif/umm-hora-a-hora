# -*- coding: utf-8 -*-
"""Teste 4 — entradas degeneradas: o comportamento tem de ser previsível e sem erro de fórmula."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from abas import ABA_AGENDA, ABA_CFG, ABA_EQUIPE, ABA_FOLGAS, ABA_MAPA
import os, openpyxl
from datetime import time, date
SAIDA = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala.xlsx")
wb = openpyxl.load_workbook(SRC)
cfg, aus, mapa, pai = wb[ABA_CFG], wb[ABA_FOLGAS], wb[ABA_AGENDA], wb[ABA_MAPA]
L = [r for r in range(2, 202) if mapa.cell(row=r, column=2).value is None][0]
d = mapa["A2"].value
casos = [
    ("duração zero",              "SO-01", time(9, 0),  time(9, 0),  "Ortopedia", "Agendada"),
    ("fim antes do início",       "SO-01", time(10, 0), time(9, 0),  "Ortopedia", "Agendada"),
    ("texto no horário",          "SO-01", "abc",       time(12, 0), "Ortopedia", "Agendada"),
    ("especialidade inexistente", "SO-01", time(8, 0),  time(9, 0),  "Cirurgia Espacial", "Agendada"),
    ("sala inexistente",          "SO-77", time(8, 0),  time(9, 0),  "Ortopedia", "Agendada"),
    ("posto de apoio como sala",  "ADM",   time(8, 0),  time(9, 0),  "Ortopedia", "Agendada"),
    ("fora da janela do plantão", "SO-01", time(3, 0),  time(4, 0),  "Ortopedia", "Agendada"),
    ("status inválido",           "SO-02", time(9, 0),  time(10, 0), "Cirurgia Geral", "Remarcada"),
    ("duração atípica",           "SO-02", time(7, 0),  time(12, 30),"Cirurgia Geral", "Agendada"),
]
for i, (nome, s, ini, fim, e, st) in enumerate(casos):
    r = L + i
    mapa.cell(row=r, column=1, value=d); mapa.cell(row=r, column=2, value=s)
    mapa.cell(row=r, column=3, value=ini); mapa.cell(row=r, column=4, value=fim)
    mapa.cell(row=r, column=5, value=e); mapa.cell(row=r, column=6, value=nome)
    mapa.cell(row=r, column=8, value=st)
la = [r for r in range(2, 152) if aus.cell(row=r, column=1).value is None][0]
aus.cell(row=la, column=1, value="Fulano Inexistente"); aus.cell(row=la, column=2, value="Folga")
aus.cell(row=la, column=3, value=date(2026, 8, 20)); aus.cell(row=la, column=4, value=date(2026, 8, 20))
aus.cell(row=la + 1, column=1, value="Adriana Salvi"); aus.cell(row=la + 1, column=2, value="Atestado")
aus.cell(row=la + 1, column=3, value=date(2026, 8, 25)); aus.cell(row=la + 1, column=4, value=date(2026, 8, 15))
aus.cell(row=la + 2, column=1, value="Zuleide Marcon"); aus.cell(row=la + 2, column=2, value="Folga")
aus.cell(row=la + 2, column=3, value=date(2026, 8, 12)); aus.cell(row=la + 2, column=4, value=date(2026, 8, 14))
POS_R1 = 22 + 20 + 3
cfg.cell(row=POS_R1 + 1, column=9, value="Inativo")          # SO-02 inativa com cirurgias
pai.cell(row=11, column=3, value=pai.cell(row=10, column=3).value)   # mesmo técnico em dois postos
pai.cell(row=12, column=4, value="Fulano Inexistente")               # não cadastrado
pai.cell(row=13, column=3, value="Zuleide Marcon")                   # técnico de férias
pai.cell(row=14, column=4, value=None)                               # posto com um técnico só
wb.save(os.path.join(SAIDA, "t4.xlsx"))
print("casos degenerados aplicados a partir da linha", L)
