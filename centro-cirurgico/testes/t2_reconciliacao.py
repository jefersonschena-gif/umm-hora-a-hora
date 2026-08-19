# -*- coding: utf-8 -*-
"""Reconciliação independente: recalcula tudo em Python a partir das ENTRADAS
lidas do arquivo recalculado e compara com os valores produzidos pelas fórmulas."""
import sys, openpyxl
from collections import defaultdict

f = sys.argv[1]
wb = openpyxl.load_workbook(f, data_only=True)
par, esp, sal, eqp, mat = wb["Parâmetros"], wb["Especialidades"], wb["Salas"], wb["Equipe"], wb["Matriz_Habilidades"]
mapa, mix, esc, pai, sug = wb["Mapa_Cirurgico"], wb["Calc_Mix"], wb["Escala_Duplas"], wb["Painel"], wb["Sugestao_Duplas"]

# ---- premissas
P_INSTR = par["B17"].value; P_CIRC = par["B18"].value
AF_META = par["B20"].value; AF_MIN = par["B21"].value
NIV_CRIT = par["B22"].value; PART_MIN = par["B23"].value
SETUP = par["B26"].value; OC_MAX = par["B28"].value
turnos = {}
for r in range(32, 35):
    t = par.cell(row=r, column=1).value
    ini, fim = par.cell(row=r, column=2).value, par.cell(row=r, column=3).value
    mi = ini.hour*60+ini.minute; mf = fim.hour*60+fim.minute
    turnos[t] = (mi, (mf-mi) % 1440 or 1440)
ESPS = [esp.cell(row=r, column=2).value for r in range(2, 22)]
ESPI = {e: i for i, e in enumerate(ESPS) if e}
SALAS = [sal.cell(row=r, column=1).value for r in range(2, 14)]
SALAS = [s for s in SALAS if s]
eq_status = {}; eq_turno = {}; eq_func = {}
for r in range(2, 152):
    n = eqp.cell(row=r, column=2).value
    if n:
        eq_func[n] = eqp.cell(row=r, column=3).value
        eq_turno[n] = eqp.cell(row=r, column=4).value
        eq_status[n] = eqp.cell(row=r, column=5).value
niveis = {}
for r in range(2, 152):
    n = mat.cell(row=r, column=2).value
    if n:
        niveis[n] = [mat.cell(row=r, column=4+j).value or 0 for j in range(20)]

# ---- ETL independente do mapa
cirs = []
for r in range(2, 302):
    s = mapa.cell(row=r, column=2).value
    if not s: continue
    t = mapa.cell(row=r, column=3).value
    ini, fim = mapa.cell(row=r, column=4).value, mapa.cell(row=r, column=5).value
    e = mapa.cell(row=r, column=6).value; st = mapa.cell(row=r, column=10).value
    if ini is None or fim is None: continue
    dur = ((fim.hour*60+fim.minute) - (ini.hour*60+ini.minute)) % 1440
    ocup = 0 if st in ("Cancelada", "Suspensa") else dur + SETUP
    cirs.append(dict(sala=s, turno=t, esp=e, dur=dur, ocup=ocup, status=st, row=r))

mixp = defaultdict(lambda: [0.0]*20)
for c in cirs:
    if c["esp"] in ESPI:
        mixp[(c["sala"], c["turno"])][ESPI[c["esp"]]] += c["ocup"]

def afin(nome, sala, turno):
    m = mixp[(sala, turno)]; tot = sum(m)
    if tot == 0 or nome not in niveis: return None
    return sum(a*b for a, b in zip(m, niveis[nome]))/tot

res = []
def chk(nome, esperado, obtido, tol=1e-9):
    if esperado is None and (obtido is None or obtido == ""):
        ok = True
    elif esperado is None or obtido is None or obtido == "":
        ok = False
    elif isinstance(esperado, str):
        ok = str(obtido) == esperado
    else:
        ok = abs(float(obtido) - float(esperado)) <= tol
    res.append((ok, nome, esperado, obtido))

# ---- 1. Calc_Mix: total de minutos e ocupação por sala x turno
for r in range(2, 38):
    s = mix.cell(row=r, column=2).value
    if not s: continue
    t = mix.cell(row=r, column=3).value
    tot = sum(mixp[(s, t)])
    chk("Calc_Mix total %s %s" % (s, t), tot, mix.cell(row=r, column=24).value)
    chk("Calc_Mix ocup %s %s" % (s, t), tot/turnos[t][1], mix.cell(row=r, column=26).value)

# ---- 2. Escala: afinidades, classificação, ocupação, nº cirurgias
for r in range(2, 38):
    s = esc.cell(row=r, column=2).value
    if not s: continue
    t = esc.cell(row=r, column=3).value
    circ, instr = esc.cell(row=r, column=8).value, esc.cell(row=r, column=10).value
    ac, ai = afin(circ, s, t), afin(instr, s, t)
    chk("afin circ %s %s" % (s, t), ac, esc.cell(row=r, column=12).value)
    chk("afin instr %s %s" % (s, t), ai, esc.cell(row=r, column=13).value)
    dupla = None if (ac is None or ai is None) else P_CIRC*ac + P_INSTR*ai
    chk("afin dupla %s %s" % (s, t), dupla, esc.cell(row=r, column=14).value)
    ncir = sum(1 for c in cirs if c["sala"] == s and c["turno"] == t and c["ocup"] > 0)
    chk("n cirurgias %s %s" % (s, t), ncir, esc.cell(row=r, column=4).value)
    tot = sum(mixp[(s, t)])
    chk("ocupação %s %s" % (s, t), tot/turnos[t][1] if turnos[t][1] else None, esc.cell(row=r, column=7).value)
    if ncir == 0: cls = "SEM CIRURGIA"
    elif dupla is None: cls = "SEM DUPLA"
    elif dupla >= AF_META: cls = "ADEQUADA"
    elif dupla >= AF_MIN: cls = "ATENÇÃO"
    else: cls = "CRÍTICA"
    chk("classificação %s %s" % (s, t), cls, esc.cell(row=r, column=15).value)
    # alerta de inaptidão
    m = mixp[(s, t)]; tt = sum(m)
    inapt = False
    if tt > 0:
        for nome in (circ, instr):
            if nome in niveis:
                inapt = inapt or any(m[i]/tt >= PART_MIN and niveis[nome][i] <= NIV_CRIT for i in range(20))
    chk("chk inaptidão %s %s" % (s, t), "Inaptidão em especialidade relevante" if inapt else "OK",
        esc.cell(row=r, column=19).value)

# ---- 3. Painel: KPIs
chk("KPI cirurgias", sum(1 for c in cirs if c["ocup"] > 0), pai["B6"].value)
chk("KPI canceladas/suspensas", sum(1 for c in cirs if c["status"] in ("Cancelada", "Suspensa")), pai["C6"].value)
chk("KPI horas cirúrgicas", sum(c["dur"] for c in cirs if c["ocup"] > 0)/60, pai["D6"].value)
tot_oc = sum(sum(mixp[(s, t)]) for s in SALAS for t in turnos)
tot_disp = sum(turnos[t][1] for s in SALAS for t in turnos)
chk("KPI ocupação média", tot_oc/tot_disp, pai["E6"].value)
num = den = 0.0
for r in range(2, 38):
    s = esc.cell(row=r, column=2).value
    if not s: continue
    t = esc.cell(row=r, column=3).value
    a = esc.cell(row=r, column=14).value
    if isinstance(a, (int, float)):
        w = sum(mixp[(s, t)]); num += a*w; den += w
chk("KPI afinidade média", num/den, pai["F6"].value)
alocados = set()
for r in range(2, 38):
    for c in (8, 10):
        v = esc.cell(row=r, column=c).value
        if v: alocados.add(v)
chk("KPI técnicos escalados", len(alocados), pai["H6"].value)

# ---- 4. Painel por sala e por especialidade
for i, s in enumerate(SALAS):
    r = 10+i
    oc = sum(sum(mixp[(s, t)]) for t in turnos); dp = sum(turnos[t][1] for t in turnos)
    chk("painel sala %s horas" % s, oc/60, pai.cell(row=r, column=4).value)
    chk("painel sala %s ocupação" % s, oc/dp, pai.cell(row=r, column=5).value)
tot_h = sum(c["dur"] for c in cirs if c["ocup"] > 0)/60
for i, e in enumerate(ESPS):
    if not e: continue
    r = 31+i
    h = sum(c["dur"] for c in cirs if c["ocup"] > 0 and c["esp"] == e)/60
    n = sum(1 for c in cirs if c["ocup"] > 0 and c["esp"] == e)
    chk("painel esp %s horas" % e, h, pai.cell(row=r, column=3).value)
    chk("painel esp %s nº" % e, n, pai.cell(row=r, column=2).value)
    chk("painel esp %s %% horas" % e, h/tot_h, pai.cell(row=r, column=4).value)
    aptos = sum(1 for nm in niveis if eq_status.get(nm) == "Ativo" and niveis[nm][i] >= 2)
    chk("painel esp %s aptos" % e, aptos, pai.cell(row=r, column=5).value)

# ---- 5. Sugestão: melhor técnico livre por sala x turno
for r in range(2, 38):
    s = sug.cell(row=r, column=1).value
    if not s: continue
    t = sug.cell(row=r, column=2).value
    cands = []
    for nm in niveis:
        if eq_status.get(nm) != "Ativo" or eq_turno.get(nm) != t: continue
        if nm in alocados and any(esc.cell(row=rr, column=3).value == t and
           (esc.cell(row=rr, column=8).value == nm or esc.cell(row=rr, column=10).value == nm)
           for rr in range(2, 38)): continue
        a = afin(nm, s, t)
        if a: cands.append((a, nm))   # afinidade zero não é sugerida
    if cands:
        best = max(cands)
        chk("sugestão 1ª %s %s (afinidade)" % (s, t), round(best[0], 2), sug.cell(row=r, column=7).value, tol=0.011)

ok = sum(1 for r in res if r[0])
print("RECONCILIAÇÃO: %d verificações · %d OK · %d divergências" % (len(res), ok, len(res)-ok))
for r in res:
    if not r[0]:
        print("   DIVERGÊNCIA:", r[1], "esperado=", r[2], "planilha=", r[3])
