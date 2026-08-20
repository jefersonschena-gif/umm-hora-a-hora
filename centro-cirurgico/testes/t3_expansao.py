# -*- coding: utf-8 -*-
"""Teste 3 — expansão: +1 técnico, +1 habilidade, +1 especialidade, +1 sala, +40 cirurgias, +5 ausências."""
import os, openpyxl
from datetime import time, date
SAIDA = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala_Diaria_v2.xlsx")
wb = openpyxl.load_workbook(SRC)
hab, esp, pos, eqp, mat, aus, mapa, esc = (wb["Habilidades"], wb["Especialidades"], wb["Postos"],
                                           wb["Equipe"], wb["Matriz_Habilidades"], wb["Ausencias"],
                                           wb["Mapa_Cirurgico"], wb["Escala_Dia"])
# (a) nova habilidade na linha 12 -> coluna O da Matriz (índice 11)
hab["A12"], hab["B12"], hab["C12"] = "H11", "Cirurgia Torácica", "Cirúrgica"
# (b) nova especialidade apontando para ela
esp["A16"], esp["B16"], esp["C16"], esp["D16"] = "Cirurgia Torácica", "Cirurgia Torácica", 180, "Sim"
# (c) nova sala na linha 13 de Postos
pos["A13"], pos["B13"], pos["C13"] = "SO-09", "Sala 9 — Torácica", "Sala cirúrgica"
pos["D13"], pos["E13"], pos["F13"] = 2, 2, 12
pos["G13"], pos["H13"] = "Cirurgia Torácica", "Ativo"
# (d) dois técnicos novos
for i, (mt, nm, fn) in enumerate([("TEC-023", "Ariane Fontella", "Circulante"),
                                  ("TEC-024", "Márcio Dalpiaz", "Instrumentador")]):
    r = 24 + i
    eqp.cell(row=r, column=1, value=mt); eqp.cell(row=r, column=2, value=nm)
    eqp.cell(row=r, column=3, value=fn); eqp.cell(row=r, column=4, value="Ativo")
    mat.cell(row=r, column=4 + 11, value=3)     # nível 3 na nova habilidade
    mat.cell(row=r, column=4, value=1)
# (e) +40 cirurgias (6 na sala nova, 34 espalhadas)
lin = [r for r in range(2, 202) if mapa.cell(row=r, column=2).value is None][0]
data = mapa["A2"].value
novas = []
cur = 7 * 60
for k in range(6):
    novas.append(("SO-09", cur, cur + 100, "Cirurgia Torácica", "Lobectomia pulmonar"))
    cur += 120
for k in range(34):
    sala = "SO-0%d" % (1 + k % 8)
    ini = 7 * 60 + (k * 37) % 600
    novas.append((sala, ini, ini + 45, "Cirurgia Geral", "Encaixe de teste %d" % (k + 1)))
for i, (sala, ini, fim, e, proc) in enumerate(novas):
    r = lin + i
    mapa.cell(row=r, column=1, value=data); mapa.cell(row=r, column=2, value=sala)
    mapa.cell(row=r, column=3, value=time((ini // 60) % 24, ini % 60))
    mapa.cell(row=r, column=4, value=time((fim // 60) % 24, fim % 60))
    mapa.cell(row=r, column=5, value=e); mapa.cell(row=r, column=7, value=proc)
    mapa.cell(row=r, column=8, value="Dr. Teste"); mapa.cell(row=r, column=9, value="M")
    mapa.cell(row=r, column=10, value="Agendada")
# (f) +5 ausências
la = [r for r in range(2, 152) if aus.cell(row=r, column=1).value is None][0]
for i, (tec, tipo, d1, d2) in enumerate([
        ("Ariane Fontella", "Folga", date(2026, 8, 22), date(2026, 8, 22)),
        ("Márcio Dalpiaz", "Folga", date(2026, 8, 23), date(2026, 8, 23)),
        ("Tatiane Bolzan", "Treinamento", date(2026, 8, 28), date(2026, 8, 29)),
        ("Vagner Sartori", "Folga", date(2026, 8, 30), date(2026, 8, 30)),
        ("Kelly Marchi", "Folga", date(2026, 8, 31), date(2026, 8, 31))]):
    r = la + i
    aus.cell(row=r, column=1, value=tec); aus.cell(row=r, column=2, value=tipo)
    aus.cell(row=r, column=3, value=d1); aus.cell(row=r, column=4, value=d2)
# (g) escalar a dupla da sala nova (linha 13 da Escala_Dia)
esc["J13"], esc["M13"] = "Ariane Fontella", "Márcio Dalpiaz"
wb.save(os.path.join(SAIDA, "t3.xlsx"))
print("expansão aplicada: +2 técnicos, +1 habilidade, +1 especialidade, +1 sala, +%d cirurgias, +5 ausências" % len(novas))
