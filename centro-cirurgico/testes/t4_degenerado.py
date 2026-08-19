# -*- coding: utf-8 -*-
"""Teste 4 — entradas degeneradas."""
import os, openpyxl
from datetime import time
SAIDA = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "Centro_Cirurgico_Escala_Duplas_v1.xlsx")
wb=openpyxl.load_workbook(SRC)
sal,eqp,mapa,esc,mat = wb["Salas"],wb["Equipe"],wb["Mapa_Cirurgico"],wb["Escala_Duplas"],wb["Matriz_Habilidades"]
L=[r for r in range(2,302) if mapa.cell(row=r,column=2).value is None][0]
d=mapa["A2"].value
casos=[
 ("duração zero",      ("SO-01","Manhã",time(9,0),time(9,0),"Ortopedia","Agendada")),
 ("fim antes do início",("SO-01","Manhã",time(10,0),time(9,0),"Ortopedia","Agendada")),
 ("texto no horário",  ("SO-01","Manhã","abc",time(12,0),"Ortopedia","Agendada")),
 ("especialidade inexistente",("SO-01","Manhã",time(8,0),time(9,0),"Cirurgia Espacial","Agendada")),
 ("sala inexistente",  ("SO-77","Manhã",time(8,0),time(9,0),"Ortopedia","Agendada")),
 ("início fora do turno",("SO-01","Manhã",time(2,0),time(3,0),"Ortopedia","Agendada")),
 ("status inválido",   ("SO-01","Tarde",time(15,0),time(16,0),"Ortopedia","Remarcada")),
 ("duração atípica",   ("SO-01","Tarde",time(13,0),time(23,0),"Ortopedia","Agendada")),
]
for i,(nome,(s,t,ini,fim,e,st)) in enumerate(casos):
    r=L+i
    mapa.cell(row=r,column=1,value=d); mapa.cell(row=r,column=2,value=s); mapa.cell(row=r,column=3,value=t)
    mapa.cell(row=r,column=4,value=ini); mapa.cell(row=r,column=5,value=fim)
    mapa.cell(row=r,column=6,value=e); mapa.cell(row=r,column=7,value=nome); mapa.cell(row=r,column=10,value=st)
# sala bloqueada
sal["C3"]="Bloqueada"                       # SO-02
# escala degenerada
esc["H2"]="Zélia Braga"                     # técnico já escalado em SO-05 Manhã -> duplicidade
esc["H5"]="Fábio Cardoso"                   # instrumentador colocado como circulante? (função Instrumentador)
esc["J8"]="Fulano Inexistente"              # não cadastrado
esc["H11"]="Cristiano Padilha"              # técnico de apoio (status Ativo) fora do turno
eqp["E19"]="Férias"                         # Simone Aguiar (SO-04 Manhã circulante) -> escalado de férias
esc["H26"]="Ana Paula Ribeiro"              # dupla em sala sem cirurgia (SO-09 não existe -> linha vazia)
wb.save(os.path.join(SAIDA, "t4.xlsx"))
print("linhas de teste a partir de",L)
