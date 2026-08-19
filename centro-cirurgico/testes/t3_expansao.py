# -*- coding: utf-8 -*-
"""Teste 3 — expansão multidimensional: +20 cirurgias, +1 especialidade, +1 sala, +2 técnicos."""
import os, openpyxl, random
from datetime import time
SAIDA = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Centro_Cirurgico_Escala_Duplas_v1.xlsx")
wb=openpyxl.load_workbook(SRC)
esp,sal,eqp,mat,mapa,esc = wb["Especialidades"],wb["Salas"],wb["Equipe"],wb["Matriz_Habilidades"],wb["Mapa_Cirurgico"],wb["Escala_Duplas"]

# (a) nova especialidade na linha 16 (posição 15 -> coluna R da matriz)
esp["A16"]="TOR"; esp["B16"]="Cirurgia Torácica"; esp["C16"]=180; esp["D16"]="Sim"
# (b) nova sala SO-09 na linha 10
sal["A10"]="SO-09"; sal["B10"]="Sala 9 — Torácica"; sal["C10"]="Ativa"; sal["D10"]="Cirurgia Torácica"
# (c) dois técnicos novos nas linhas 62 e 63 da Equipe
for i,(mt,nm,fn,tn) in enumerate([("TEC-061","Renata Vilela","Circulante","Manhã"),
                                  ("TEC-062","Sérgio Lustosa","Instrumentador","Manhã")]):
    r=62+i
    eqp.cell(row=r,column=1,value=mt); eqp.cell(row=r,column=2,value=nm)
    eqp.cell(row=r,column=3,value=fn); eqp.cell(row=r,column=4,value=tn); eqp.cell(row=r,column=5,value="Ativo")
    mat.cell(row=r,column=4+14,value=3)   # nível 3 na nova especialidade (coluna R = índice 14)
    mat.cell(row=r,column=4,value=1)
# (d) +20 cirurgias: 6 na sala nova, 14 distribuídas nas salas existentes
lin=[r for r in range(2,302) if mapa.cell(row=r,column=2).value is None][0]
novas=[]
plano=[("SO-09","Manhã",7*60,3),("SO-09","Tarde",13*60,3)]
for sala,turno,base,n in plano:
    cur=base
    for k in range(n):
        dur=90
        novas.append(("SO-09" if sala=="SO-09" else sala,turno,cur,cur+dur,"Cirurgia Torácica","Lobectomia pulmonar","Dr. Novaes","M","Agendada"))
        cur+=dur+30
extras=[("SO-01","Manhã",11*60+40,90,"Ortopedia"),("SO-04","Tarde",17*60,60,"Cirurgia Vascular"),
        ("SO-07","Manhã",11*60,60,"Cirurgia Plástica"),("SO-08","Tarde",17*60+30,60,"Obstetrícia")]
for sala,turno,ini,dur,e in extras:
    novas.append((sala,turno,ini,ini+dur,e,"Procedimento adicional","Dra. Teste","M","Agendada"))
for i in range(10):
    novas.append(("SO-05","Noite",(19*60+i*70)%1440,(19*60+i*70+50)%1440,"Urologia","RTU adicional","Dr. Extra","P","Agendada"))
data=mapa["A2"].value
for i,(sala,turno,ini,fim,e,proc,cir,porte,st) in enumerate(novas):
    r=lin+i
    mapa.cell(row=r,column=1,value=data); mapa.cell(row=r,column=2,value=sala); mapa.cell(row=r,column=3,value=turno)
    mapa.cell(row=r,column=4,value=time((ini//60)%24,ini%60)); mapa.cell(row=r,column=5,value=time((fim//60)%24,fim%60))
    mapa.cell(row=r,column=6,value=e); mapa.cell(row=r,column=7,value=proc); mapa.cell(row=r,column=8,value=cir)
    mapa.cell(row=r,column=9,value=porte); mapa.cell(row=r,column=10,value=st)
print("cirurgias acrescentadas:",len(novas),"a partir da linha",lin)
# (e) escalar a dupla da sala nova (linhas 26 e 27 da Escala = SO-09 Manhã/Tarde)
esc["H26"]="Renata Vilela"; esc["J26"]="Sérgio Lustosa"
wb.save(os.path.join(SAIDA, "t3.xlsx"))
print("salvo t3.xlsx")
