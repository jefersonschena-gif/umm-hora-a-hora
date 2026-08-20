# -*- coding: utf-8 -*-
"""Teste 2 — reconciliação independente: recalcula tudo em Python a partir das ENTRADAS
lidas do arquivo recalculado e compara com o que as fórmulas produziram."""
import sys, openpyxl
from collections import defaultdict

wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
par, hab, esp, pos = wb["Parâmetros"], wb["Habilidades"], wb["Especialidades"], wb["Postos"]
eqp, mat, aus, cal = wb["Equipe"], wb["Matriz_Habilidades"], wb["Ausencias"], wb["Calendario_Ausencias"]
mapa, mix, esc, sug = wb["Mapa_Cirurgico"], wb["Calc_Mix"], wb["Escala_Dia"], wb["Sugestao_Tecnicos"]
jog, pai = wb["Jogo_de_Sala"], wb["Painel"]

DATA = par["B6"].value
T_INI, T_FIM, T_MIN = par["B10"].value, par["B11"].value, par["B12"].value
P_INSTR, P_CIRC = par["B22"].value, par["B23"].value
AF_META, AF_MIN = par["B25"].value, par["B26"].value
NIV_CRIT, PART_MIN = par["B27"].value, par["B28"].value
LIMPEZA, JANELA_MIN = par["B31"].value, par["B32"].value
BASE = T_INI.hour * 60 + T_INI.minute
TIPOS = [par.cell(row=38 + i, column=1).value for i in range(7)]
SIGLAS = [par.cell(row=38 + i, column=2).value for i in range(7)]

HABS = [hab.cell(row=2 + i, column=2).value for i in range(14)]
HIDX = {h: i for i, h in enumerate(HABS) if h}
ESPH = {esp.cell(row=2 + i, column=1).value: esp.cell(row=2 + i, column=2).value
        for i in range(24) if esp.cell(row=2 + i, column=1).value}
POSTOS = []
for i in range(16):
    cod = pos.cell(row=2 + i, column=1).value
    if cod:
        POSTOS.append(dict(cod=cod, nome=pos.cell(row=2 + i, column=2).value,
                           tipo=pos.cell(row=2 + i, column=3).value,
                           nec=pos.cell(row=2 + i, column=4).value,
                           hab=pos.cell(row=2 + i, column=7).value,
                           func=pos.cell(row=2 + i, column=8).value,
                           status=pos.cell(row=2 + i, column=9).value, linha=2 + i))
WD = DATA.weekday() + 1          # 1 = segunda ... 7 = domingo
def nec_hoje(p):
    if p["status"] != "Ativo":
        return 0
    fer = DATA in FERIADOS
    if p["func"] == "Seg a Sex" and (WD > 5 or fer):
        return 0
    if p["func"] == "Seg a Sáb" and (WD > 6 or fer):
        return 0
    return p["nec"]
EQ = []
for i in range(30):
    n = eqp.cell(row=2 + i, column=2).value
    if n:
        EQ.append(dict(nome=n, funcao=eqp.cell(row=2 + i, column=4).value,
                       status=eqp.cell(row=2 + i, column=5).value, linha=2 + i))
NIV = {mat.cell(row=r, column=2).value: [mat.cell(row=r, column=4 + j).value or 0 for j in range(14)]
       for r in range(2, 32) if mat.cell(row=r, column=2).value}
PERIODO_INI = par["B13"].value
FERIADOS = {par.cell(row=48 + i, column=1).value for i in range(20)
            if par.cell(row=48 + i, column=1).value}
AUS = [dict(tec=aus.cell(row=r, column=1).value, tipo=aus.cell(row=r, column=2).value,
            ini=aus.cell(row=r, column=3).value, fim=aus.cell(row=r, column=4).value)
       for r in range(2, 152) if aus.cell(row=r, column=1).value]

def situacao(t):
    if t["status"] != "Ativo":
        return t["status"]
    for a in AUS:
        if a["tec"] == t["nome"] and a["ini"] and a["fim"] and a["ini"] <= DATA <= a["fim"]:
            return a["tipo"]
    return "Disponível"

CIRS = []
for r in range(2, 202):
    s = mapa.cell(row=r, column=2).value
    ini, fim = mapa.cell(row=r, column=3).value, mapa.cell(row=r, column=4).value
    if not s or ini is None or fim is None:
        continue
    dur = ((fim.hour * 60 + fim.minute) - (ini.hour * 60 + ini.minute)) % 1440
    st = mapa.cell(row=r, column=10).value
    ocup = 0 if (st in ("Cancelada", "Suspensa") or dur <= 0) else dur + LIMPEZA
    rel = ((ini.hour * 60 + ini.minute) - BASE) % 1440
    CIRS.append(dict(sala=s, esp=mapa.cell(row=r, column=5).value, dur=dur, ocup=ocup,
                     status=st, rel=rel, relfim=rel + dur if ocup else 0,
                     data=mapa.cell(row=r, column=1).value))

def mix_posto(p):
    m = [0.0] * 14
    if p["tipo"] == "Sala cirúrgica":
        for c in CIRS:
            if c["sala"] == p["cod"] and c["ocup"] > 0 and c["data"] == DATA:
                m[HIDX[ESPH[c["esp"]]]] += c["ocup"]
    if sum(m) == 0:
        m = [0.0] * 14
        m[HIDX[p["hab"]]] = float(T_MIN)
    return m

def afin(nome, p):
    m = mix_posto(p); tot = sum(m)
    if not tot or nome not in NIV:
        return None
    return sum(a * b for a, b in zip(m, NIV[nome])) / tot

B3_R1 = 14
B4_R1 = B3_R1 + len(TIPOS) + 3
B5_R1 = B4_R1 + 16 + 3
B6_R1 = B5_R1 + 14 + 3

res = []
def chk(nome, esp_, obt, tol=1e-9):
    if esp_ is None and (obt is None or obt == ""):
        ok = True
    elif esp_ is None or obt is None or obt == "":
        ok = False
    elif isinstance(esp_, str):
        ok = str(obt) == esp_
    else:
        ok = abs(float(obt) - float(esp_)) <= tol
    res.append((ok, nome, esp_, obt))

# 1. situação de cada técnico na data
for t in EQ:
    chk("situação %s" % t["nome"], situacao(t), eqp.cell(row=t["linha"], column=6).value)

# 2. Calc_Mix e ocupação por posto
for p in POSTOS:
    m = mix_posto(p); r = p["linha"]
    chk("mix total %s" % p["cod"], sum(m), mix.cell(row=r, column=20).value)
    agendado = sum(c["ocup"] for c in CIRS if c["sala"] == p["cod"] and c["data"] == DATA)
    chk("min. agendados %s" % p["cod"], agendado if p["tipo"] == "Sala cirúrgica" else 0,
        mix.cell(row=r, column=5).value)
    if p["tipo"] == "Sala cirúrgica":
        chk("ocupação %s" % p["cod"], agendado / T_MIN, mix.cell(row=r, column=22).value)

# 3. Escala do dia
disp = {t["nome"] for t in EQ if situacao(t) == "Disponível"}
for p in POSTOS:
    r = p["linha"]
    t1, t2 = esc.cell(row=r, column=10).value, esc.cell(row=r, column=13).value
    a1, a2 = (afin(t1, p) if t1 else None), (afin(t2, p) if t2 else None)
    chk("afinidade 1 %s" % p["cod"], a1, esc.cell(row=r, column=12).value)
    chk("afinidade 2 %s" % p["cod"], a2, esc.cell(row=r, column=15).value)
    if a1 is None and a2 is None:
        ap = None
    elif a2 is None:
        ap = a1
    elif a1 is None:
        ap = a2
    else:
        ap = (P_CIRC * a1 + P_INSTR * a2) if p["tipo"] == "Sala cirúrgica" else (a1 + a2) / 2
    chk("afinidade do posto %s" % p["cod"], ap, esc.cell(row=r, column=16).value)
    nal = (1 if t1 else 0) + (1 if t2 else 0)
    nh = nec_hoje(p)
    chk("necessários hoje %s" % p["cod"], nh, esc.cell(row=r, column=6).value)
    if nh == 0:
        cob = "NÃO OPERA HOJE" if nal == 0 else "EXTRA — não opera hoje"
    else:
        cob = "DESCOBERTO" if nal == 0 else ("COMPLETO" if nal >= nh else
                                             "INCOMPLETO (%d de %d)" % (nal, nh))
    chk("cobertura %s" % p["cod"], cob, esc.cell(row=r, column=17).value)
    cls = ("—" if cob == "NÃO OPERA HOJE" else "SEM EQUIPE" if cob == "DESCOBERTO" else
           "—" if ap is None else
           "ADEQUADO" if ap >= AF_META else "ATENÇÃO" if ap >= AF_MIN else "CRÍTICO")
    chk("classificação %s" % p["cod"], cls, esc.cell(row=r, column=18).value)
    if p["tipo"] == "Sala cirúrgica":
        n = sum(1 for c in CIRS if c["sala"] == p["cod"] and c["ocup"] > 0 and c["data"] == DATA)
        chk("nº cirurgias %s" % p["cod"], n, esc.cell(row=r, column=7).value)
    # alerta de inaptidão
    m = mix_posto(p); tot = sum(m)
    inapt = False
    for nome in (t1, t2):
        if nome in NIV:
            inapt = inapt or any(m[i] / tot >= PART_MIN and NIV[nome][i] <= NIV_CRIT for i in range(14))
    chk("chk inaptidão %s" % p["cod"],
        "Inaptidão em habilidade relevante" if inapt else "OK", esc.cell(row=r, column=22).value)

# 4. Painel — indicadores e cobertura de pessoal
chk("KPI cirurgias", sum(1 for c in CIRS if c["ocup"] > 0 and c["data"] == DATA), pai["B6"].value)
chk("KPI canceladas", sum(1 for c in CIRS if c["status"] in ("Cancelada", "Suspensa") and c["data"] == DATA),
    pai["C6"].value)
chk("KPI horas", sum(c["dur"] for c in CIRS if c["ocup"] > 0 and c["data"] == DATA) / 60, pai["D6"].value)
salas = [p for p in POSTOS if p["tipo"] == "Sala cirúrgica"]
chk("KPI ocupação média",
    sum(c["ocup"] for c in CIRS if c["data"] == DATA) / (len(salas) * T_MIN), pai["E6"].value)
chk("KPI vagas cobertas",
    sum(1 for p in POSTOS for col in (10, 13) if esc.cell(row=p["linha"], column=col).value), pai["H6"].value)
chk("quadro", len([t for t in EQ if t["status"] == "Ativo"]), pai["A10"].value)
chk("ausentes hoje", len([t for t in EQ if t["status"] == "Ativo" and situacao(t) != "Disponível"]), pai["B10"].value)
chk("disponíveis", len(disp), pai["C10"].value)
chk("vagas necessárias", sum(nec_hoje(p) for p in POSTOS), pai["D10"].value)
chk("déficit", max(0, sum(nec_hoje(p) for p in POSTOS) - len(disp)), pai["E10"].value)
desc = [p for p in POSTOS if not esc.cell(row=p["linha"], column=10).value
        and not esc.cell(row=p["linha"], column=13).value]
chk("postos descobertos", len(desc), pai["F10"].value)
chk("cirurgias a remanejar",
    sum(1 for c in CIRS if c["ocup"] > 0 and c["data"] == DATA and c["sala"] in {p["cod"] for p in desc}),
    pai["G10"].value)
escalados = {esc.cell(row=p["linha"], column=col).value for p in POSTOS for col in (10, 13)} - {None}
chk("reserva", len(disp - escalados), pai["H10"].value)

# 5. Painel por habilidade
for i, h in enumerate(HABS):
    if not h:
        continue
    r = B5_R1 + i
    n = sum(1 for c in CIRS if c["ocup"] > 0 and c["data"] == DATA and ESPH.get(c["esp"]) == h)
    hs = sum(c["dur"] for c in CIRS if c["ocup"] > 0 and c["data"] == DATA and ESPH.get(c["esp"]) == h) / 60
    chk("habilidade %s nº" % h, n, pai.cell(row=r, column=2).value)
    chk("habilidade %s horas" % h, hs, pai.cell(row=r, column=3).value)
    chk("habilidade %s aptos no quadro" % h,
        sum(1 for t in EQ if t["status"] == "Ativo" and NIV[t["nome"]][i] >= 2), pai.cell(row=r, column=5).value)
    chk("habilidade %s aptos disponíveis" % h,
        sum(1 for t in EQ if situacao(t) == "Disponível" and NIV[t["nome"]][i] >= 2),
        pai.cell(row=r, column=6).value)

# 6. Jogo de sala — janelas livres recalculadas do zero
for pi, p in enumerate(POSTOS):
    if p["tipo"] != "Sala cirúrgica":
        continue
    ag = sorted([c for c in CIRS if c["sala"] == p["cod"] and c["ocup"] > 0 and c["data"] == DATA],
                key=lambda c: c["rel"])
    janelas = []
    janelas.append(max(0, (ag[0]["rel"] if ag else T_MIN) - 0))
    for k, c in enumerate(ag):
        ini = c["relfim"] + LIMPEZA
        fim = ag[k + 1]["rel"] if k + 1 < len(ag) else T_MIN
        janelas.append(max(0, fim - ini))
    for k, dur in enumerate(janelas):
        r = 2 + pi * 13 + k
        chk("janela %s#%d" % (p["cod"], k), dur, jog.cell(row=r, column=5).value)
    r0 = B6_R1 + pi
    chk("painel livre total %s" % p["cod"], sum(janelas), pai.cell(row=r0, column=2).value)
    chk("painel maior janela %s" % p["cod"], max(janelas), pai.cell(row=r0, column=3).value)
    chk("painel janelas aproveitáveis %s" % p["cod"],
        sum(1 for d in janelas if d >= JANELA_MIN), pai.cell(row=r0, column=5).value)

# 7. Calendário de ausências — dias por tipo no mês
for i, (tipo, sig) in enumerate(zip(TIPOS, SIGLAS)):
    dias = 0
    for a in AUS:
        if a["tipo"] != tipo or not a["ini"] or not a["fim"]:
            continue
        for d in range(31):
            dia = cal.cell(row=2, column=3 + d).value
            if dia and a["ini"] <= dia <= a["fim"] and a["tec"] in NIV:
                dias += 1
    chk("calendário dias de %s" % tipo, dias, pai.cell(row=B3_R1 + i, column=3).value)

# 8. rodapé do calendário — funcionários, vagas e déficit dia a dia
CAL_FIM = 3 + 30
for d in range(31):
    dia = cal.cell(row=2, column=3 + d).value
    if not dia:
        continue
    disp_d = sum(1 for t in EQ if t["status"] == "Ativo" and not any(
        a["tec"] == t["nome"] and a["ini"] and a["fim"] and a["ini"] <= dia <= a["fim"] for a in AUS))
    wd = dia.weekday() + 1
    ferd = dia in FERIADOS
    vagas_d = sum(p["nec"] for p in POSTOS if p["status"] == "Ativo" and not (
        (p["func"] == "Seg a Sex" and (wd > 5 or ferd)) or
        (p["func"] == "Seg a Sáb" and (wd > 6 or ferd))))
    chk("calendário %s funcionários" % dia.strftime("%d/%m"), disp_d, cal.cell(row=CAL_FIM + 2, column=3 + d).value)
    chk("calendário %s vagas" % dia.strftime("%d/%m"), vagas_d, cal.cell(row=CAL_FIM + 3, column=3 + d).value)
    chk("calendário %s déficit" % dia.strftime("%d/%m"), max(0, vagas_d - disp_d),
        cal.cell(row=CAL_FIM + 4, column=3 + d).value)

ok = sum(1 for r in res if r[0])
print("RECONCILIAÇÃO: %d verificações · %d OK · %d divergências" % (len(res), ok, len(res) - ok))
for r in res:
    if not r[0]:
        print("   DIVERGÊNCIA:", r[1], "| esperado =", r[2], "| planilha =", r[3])
sys.exit(1 if ok != len(res) else 0)
