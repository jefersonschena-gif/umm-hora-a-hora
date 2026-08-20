# -*- coding: utf-8 -*-
"""Teste 4 — entradas degeneradas: o comportamento tem de ser previsível e sem erro de fórmula."""
import os, openpyxl
from datetime import time, date
SAIDA = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala_Diaria_v2.xlsx")
wb = openpyxl.load_workbook(SRC)
pos, eqp, aus, mapa, esc = wb["Postos"], wb["Equipe"], wb["Ausencias"], wb["Mapa_Cirurgico"], wb["Escala_Dia"]
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
    ("status inválido",           "SO-02", time(15, 0), time(16, 0), "Cirurgia Geral", "Remarcada"),
    ("duração atípica",           "SO-02", time(13, 0), time(23, 0), "Cirurgia Geral", "Agendada"),
]
for i, (nome, s, ini, fim, e, st) in enumerate(casos):
    r = L + i
    mapa.cell(row=r, column=1, value=d); mapa.cell(row=r, column=2, value=s)
    mapa.cell(row=r, column=3, value=ini); mapa.cell(row=r, column=4, value=fim)
    mapa.cell(row=r, column=5, value=e); mapa.cell(row=r, column=7, value=nome)
    mapa.cell(row=r, column=10, value=st)
# ausências degeneradas
la = [r for r in range(2, 152) if aus.cell(row=r, column=1).value is None][0]
aus.cell(row=la, column=1, value="Fulano Inexistente"); aus.cell(row=la, column=2, value="Folga")
aus.cell(row=la, column=3, value=date(2026, 8, 20)); aus.cell(row=la, column=4, value=date(2026, 8, 20))
aus.cell(row=la + 1, column=1, value="Adriana Salvi"); aus.cell(row=la + 1, column=2, value="Atestado")
aus.cell(row=la + 1, column=3, value=date(2026, 8, 25)); aus.cell(row=la + 1, column=4, value=date(2026, 8, 15))
aus.cell(row=la + 2, column=1, value="Zuleide Marcon"); aus.cell(row=la + 2, column=2, value="Folga")
aus.cell(row=la + 2, column=3, value=date(2026, 8, 12)); aus.cell(row=la + 2, column=4, value=date(2026, 8, 14))
# sala bloqueada e escala degenerada
pos["H3"] = "Inativo"                                  # SO-02 inativa com cirurgias
esc["J3"] = esc["J2"].value                            # mesmo técnico em dois postos
esc["M4"] = "Fulano Inexistente"                       # não cadastrado
esc["J6"] = "Zuleide Marcon"                           # técnico de férias
esc["M8"] = ""                                         # posto com um técnico só
wb.save(os.path.join(SAIDA, "t4.xlsx"))
print("casos degenerados aplicados a partir da linha", L)
