# -*- coding: utf-8 -*-
"""Teste 3 — expansão: +1 especialidade, +1 sala, +2 técnicos, +30 cirurgias, +5 ausências."""
import os, openpyxl
from datetime import time, date
SAIDA = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "Centro_Cirurgico_Escala.xlsx")
wb = openpyxl.load_workbook(SRC)
cfg, eqp, aus, mapa, pai = (wb["Configuração"], wb["Equipe"], wb["Ausencias"],
                            wb["Mapa_Cirurgico"], wb["Painel"])
N_ESP, N_POS = 20, 16
ESP_R1 = 22; POS_R1 = ESP_R1 + N_ESP + 3
# (a) nova especialidade na primeira linha livre -> vira mais uma coluna de X na aba Equipe
r = next(x for x in range(ESP_R1, ESP_R1 + N_ESP) if cfg.cell(row=x, column=2).value is None)
ESP_NOVA_COL = 8 + (r - ESP_R1)          # coluna do X correspondente na aba Equipe
cfg.cell(row=r, column=1, value="ROB"); cfg.cell(row=r, column=2, value="Cirurgia Robótica")
cfg.cell(row=r, column=3, value="Cirúrgica"); cfg.cell(row=r, column=4, value=180)
cfg.cell(row=r, column=5, value="Sim")
# (b) nova sala na 12ª linha de postos
r = POS_R1 + 11
for c, v in enumerate(["SO-09", "Sala 9 — Robótica", "Sala cirúrgica", 2, 2, 12,
                       "Cirurgia Robótica", "Seg a Sex", "Ativo", "Sala nova"], start=1):
    cfg.cell(row=r, column=c, value=v)
# (c) dois técnicos novos, com X na especialidade nova
for i, (mt, nm) in enumerate([("TEC-023", "Ariane Fontella"), ("TEC-024", "Márcio Dalpiaz")]):
    r = 2 + 22 + i
    eqp.cell(row=r, column=1, value=mt); eqp.cell(row=r, column=2, value=nm)
    eqp.cell(row=r, column=3, value="000000"); eqp.cell(row=r, column=4, value="Ativo")
    eqp.cell(row=r, column=ESP_NOVA_COL, value="X")  # Cirurgia Robótica
    eqp.cell(row=r, column=8, value="X")           # Ortopedia
# (d) +30 cirurgias
lin = [r for r in range(2, 202) if mapa.cell(row=r, column=2).value is None][0]
data = mapa["A2"].value
novas = [("SO-09", 7 * 60 + k * 110, 7 * 60 + k * 110 + 90, "Cirurgia Robótica",
          "Lobectomia %d" % (k + 1)) for k in range(3)]
novas += [("SO-0%d" % (1 + k % 8), 7 * 60 + (k * 23) % 300, 7 * 60 + (k * 23) % 300 + 40,
           "Cirurgia Geral", "Encaixe de teste %d" % (k + 1)) for k in range(27)]
for i, (sala, ini, fim, e, proc) in enumerate(novas):
    r = lin + i
    mapa.cell(row=r, column=1, value=data); mapa.cell(row=r, column=2, value=sala)
    mapa.cell(row=r, column=3, value=time((ini // 60) % 24, ini % 60))
    mapa.cell(row=r, column=4, value=time((fim // 60) % 24, fim % 60))
    mapa.cell(row=r, column=5, value=e); mapa.cell(row=r, column=6, value=proc)
    mapa.cell(row=r, column=7, value="Dr. Teste"); mapa.cell(row=r, column=8, value="Agendada")
# (e) +5 ausências
la = [r for r in range(2, 152) if aus.cell(row=r, column=1).value is None][0]
for i, (tec, tipo, d1, d2) in enumerate([
        ("Ariane Fontella", "Folga", date(2026, 8, 22), date(2026, 8, 22)),
        ("Márcio Dalpiaz", "Folga", date(2026, 8, 23), date(2026, 8, 23)),
        ("Kelly Marchi", "Treinamento", date(2026, 8, 28), date(2026, 8, 29)),
        ("Vagner Sartori", "Folga", date(2026, 8, 30), date(2026, 8, 30)),
        ("Nádia Fávero", "Folga", date(2026, 8, 31), date(2026, 8, 31))]):
    r = la + i
    aus.cell(row=r, column=1, value=tec); aus.cell(row=r, column=2, value=tipo)
    aus.cell(row=r, column=3, value=d1); aus.cell(row=r, column=4, value=d2)
# (f) escalar a dupla da sala nova (12ª linha do bloco de escala do Painel)
pai.cell(row=10 + 11, column=7, value="Ariane Fontella")
pai.cell(row=10 + 11, column=8, value="Márcio Dalpiaz")
wb.save(os.path.join(SAIDA, "t3.xlsx"))
print("expansão aplicada: +1 especialidade, +1 sala, +2 técnicos, +%d cirurgias, +5 ausências" % len(novas))
