# -*- coding: utf-8 -*-
"""Teste 2 — reconciliação independente: recalcula tudo em Python a partir das ENTRADAS
lidas do arquivo recalculado e compara com o que as fórmulas produziram."""
import sys, openpyxl

wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
pai, mapa, eqp, aus, cfg = (wb["Painel"], wb["Mapa_Cirurgico"], wb["Equipe"],
                            wb["Ausencias"], wb["Configuração"])
cal, sal = wb["Calc"], wb["Calc_Salas"]

N_ESP, N_POS, N_EQ, JOGO_K, DIAS = 20, 16, 30, 13, 31
ESP_R1 = 22
POS_R1 = ESP_R1 + N_ESP + 3
FER_R1 = POS_R1 + N_POS + 3
PAI_R1, JOG_R1 = 10, 28
EQH_R1 = JOG_R1 + N_POS + 2
CHK_R1 = EQH_R1 + N_EQ + 2
MIX_R1, COB_R1 = 2, 2 + N_POS + 2
XC1, CC1 = 8, 5
TOT_C, DISP_C, OCUP_C, NEC_C = CC1 + N_ESP, CC1 + N_ESP + 1, CC1 + N_ESP + 2, CC1 + N_ESP + 5

DATA = pai["B6"].value
PERIODO = cfg["B8"].value
T_INI, T_MIN = cfg["B11"].value, cfg["B13"].value
LIMPEZA, JANELA = cfg["B16"].value, cfg["B17"].value
BASE = T_INI.hour * 60 + T_INI.minute
FERIADOS = {cfg.cell(row=FER_R1 + i, column=1).value for i in range(20)
            if cfg.cell(row=FER_R1 + i, column=1).value}
ESPS = [cfg.cell(row=ESP_R1 + i, column=2).value for i in range(N_ESP)]
EIDX = {e: i for i, e in enumerate(ESPS) if e}
POSTOS = []
for i in range(N_POS):
    cod = cfg.cell(row=POS_R1 + i, column=1).value
    if cod:
        POSTOS.append(dict(cod=cod, nome=cfg.cell(row=POS_R1 + i, column=2).value,
                           tipo=cfg.cell(row=POS_R1 + i, column=3).value,
                           nec=cfg.cell(row=POS_R1 + i, column=4).value,
                           esp=cfg.cell(row=POS_R1 + i, column=7).value,
                           func=cfg.cell(row=POS_R1 + i, column=8).value,
                           status=cfg.cell(row=POS_R1 + i, column=9).value, i=i))
EQ, X = [], {}
for i in range(N_EQ):
    n = eqp.cell(row=2 + i, column=2).value
    if n:
        EQ.append(dict(nome=n, status=eqp.cell(row=2 + i, column=4).value, i=i))
        X[n] = {ESPS[j] for j in range(N_ESP)
                if str(eqp.cell(row=2 + i, column=XC1 + j).value or "").strip().upper() == "X"}
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

def nec_hoje(p, dia=None):
    dia = dia or DATA
    if p["status"] != "Ativo":
        return 0
    wd, fer = dia.weekday() + 1, dia in FERIADOS
    if p["func"] == "Seg a Sex" and (wd > 5 or fer): return 0
    if p["func"] == "Seg a Sáb" and (wd > 6 or fer): return 0
    return p["nec"]

CIRS = []
for r in range(2, 202):
    s = mapa.cell(row=r, column=2).value
    ini, fim = mapa.cell(row=r, column=3).value, mapa.cell(row=r, column=4).value
    if not s or ini is None or fim is None:
        continue
    dur = ((fim.hour * 60 + fim.minute) - (ini.hour * 60 + ini.minute)) % 1440
    st = mapa.cell(row=r, column=8).value
    ocup = 0 if (st in ("Cancelada", "Suspensa") or dur <= 0) else dur + LIMPEZA
    rel = ((ini.hour * 60 + ini.minute) - BASE) % 1440
    CIRS.append(dict(sala=s, esp=mapa.cell(row=r, column=5).value, dur=dur, ocup=ocup,
                     rel=rel, relfim=rel + dur if ocup else 0, status=st,
                     data=mapa.cell(row=r, column=1).value))

# minutos que a sala fica ocupada dentro do plantão: cirurgia + limpeza, cortados no fim do
# turno e na entrada da cirurgia seguinte da mesma sala (agendas emendadas não somam duas vezes)
for c in CIRS:
    c["plant"] = 0
for chave in {(c["sala"], c["data"]) for c in CIRS}:
    fila = sorted([c for c in CIRS if (c["sala"], c["data"]) == chave and c["ocup"] > 0],
                  key=lambda c: c["rel"])
    for k, c in enumerate(fila):
        prox = fila[k + 1]["rel"] if k + 1 < len(fila) else T_MIN
        c["plant"] = max(0, min(c["rel"] + c["dur"] + LIMPEZA, T_MIN, prox) - min(c["rel"], T_MIN))

def mix(p):
    m = [0.0] * N_ESP
    if p["tipo"] == "Sala cirúrgica":
        for c in CIRS:
            if c["sala"] == p["cod"] and c["ocup"] > 0 and c["data"] == DATA:
                m[EIDX[c["esp"]]] += c["plant"]
    if sum(m) == 0:
        m = [0.0] * N_ESP
        m[EIDX[p["esp"]]] = float(T_MIN)
    return m

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

# 1. situação de cada técnico
for t in EQ:
    chk("situação %s" % t["nome"], situacao(t), eqp.cell(row=2 + t["i"], column=5).value)

# 2. Calc: mix, necessários hoje, cobertura
disp = {t["nome"] for t in EQ if situacao(t) == "Disponível"}
for p in POSTOS:
    mr, cr = MIX_R1 + p["i"], COB_R1 + p["i"]
    m = mix(p)
    chk("mix total %s" % p["cod"], sum(m), cal.cell(row=mr, column=TOT_C).value)
    chk("necessários hoje %s" % p["cod"], nec_hoje(p), cal.cell(row=mr, column=NEC_C).value)
    if p["tipo"] == "Sala cirúrgica":
        ag = sum(c["plant"] for c in CIRS if c["sala"] == p["cod"] and c["data"] == DATA)
        chk("ocupação %s" % p["cod"], ag / T_MIN, cal.cell(row=mr, column=OCUP_C).value)
    t1 = pai.cell(row=PAI_R1 + p["i"], column=7).value
    t2 = pai.cell(row=PAI_R1 + p["i"], column=8).value
    esps_dia = [j for j in range(N_ESP) if m[j] > 0]
    cob = [sum(1 for t in (t1, t2) if t and ESPS[j] in X.get(t, set())) for j in esps_dia]
    chk("nº especialidades %s" % p["cod"], len(esps_dia), cal.cell(row=cr, column=TOT_C).value)
    chk("descobertas %s" % p["cod"], sum(1 for c in cob if c == 0), cal.cell(row=cr, column=DISP_C).value)
    chk("cobertas por 1 %s" % p["cod"], sum(1 for c in cob if c == 1), cal.cell(row=cr, column=OCUP_C).value)
    # situação do posto
    nh, nal = nec_hoje(p), (1 if t1 else 0) + (1 if t2 else 0)
    sem_aval = any(t and not X.get(t) for t in (t1, t2))
    if nh == 0:      sit = "NÃO OPERA" if nal == 0 else "EXTRA"
    elif nal == 0:   sit = "SEM EQUIPE"
    elif nal < nh:   sit = "INCOMPLETO"
    elif sem_aval:   sit = "SEM AVALIAÇÃO"
    elif any(c == 0 for c in cob):                 sit = "FALTA HABILIDADE"
    elif nh >= 2 and any(c == 1 for c in cob):     sit = "ATENÇÃO"
    else:            sit = "OK"
    chk("situação %s" % p["cod"], sit, pai.cell(row=PAI_R1 + p["i"], column=9).value)

# 3. Painel — indicadores do dia
chk("no quadro", len([t for t in EQ if t["status"] == "Ativo"]), pai["D6"].value)
chk("ausentes", len([t for t in EQ if t["status"] == "Ativo" and situacao(t) != "Disponível"]), pai["E6"].value)
chk("disponíveis", len(disp), pai["F6"].value)
chk("vagas do dia", sum(nec_hoje(p) for p in POSTOS), pai["G6"].value)
chk("déficit", max(0, sum(nec_hoje(p) for p in POSTOS) - len(disp)), pai["H6"].value)
sem_eq = [p for p in POSTOS if pai.cell(row=PAI_R1 + p["i"], column=9).value == "SEM EQUIPE"]
chk("postos descobertos", len(sem_eq), pai["I6"].value)
chk("cirurgias a remanejar",
    sum(1 for c in CIRS if c["ocup"] > 0 and c["data"] == DATA
        and c["sala"] in {p["cod"] for p in sem_eq}), pai["J6"].value)
escalados = {pai.cell(row=PAI_R1 + p["i"], column=c).value for p in POSTOS for c in (7, 8)} - {None}
chk("reserva", len(disp - escalados), pai["K6"].value)

# 4. jogo de sala — janelas recalculadas do zero
for p in POSTOS:
    if p["tipo"] != "Sala cirúrgica":
        continue
    ag = sorted([c for c in CIRS if c["sala"] == p["cod"] and c["ocup"] > 0 and c["data"] == DATA],
                key=lambda c: c["rel"])
    jan = [max(0, (ag[0]["rel"] if ag else T_MIN))]
    for k, c in enumerate(ag):
        jan.append(max(0, (ag[k + 1]["rel"] if k + 1 < len(ag) else T_MIN) - (c["relfim"] + LIMPEZA)))
    for k, d in enumerate(jan):
        chk("janela %s#%d" % (p["cod"], k), d, sal.cell(row=2 + p["i"] * JOGO_K + k, column=5).value)
    r = JOG_R1 + p["i"]
    chk("painel livre total %s" % p["cod"], sum(jan), pai.cell(row=r, column=3).value)
    chk("painel cabe até %s" % p["cod"], max(0, max(jan) - LIMPEZA) if max(jan) else None,
        pai.cell(row=r, column=5).value)
    chk("painel janelas %s" % p["cod"], sum(1 for d in jan if d >= JANELA), pai.cell(row=r, column=8).value)

# 5. calendário do período — funcionários, vagas e déficit dia a dia
CAL_C1, CAL_R1 = 9, 3
for d in range(DIAS):
    dia = aus.cell(row=1, column=CAL_C1 + 1 + d).value
    if not dia:
        continue
    dsp = sum(1 for t in EQ if t["status"] == "Ativo" and not any(
        a["tec"] == t["nome"] and a["ini"] and a["fim"] and a["ini"] <= dia <= a["fim"] for a in AUS))
    vag = sum(nec_hoje(p, dia) for p in POSTOS)
    base = CAL_R1 + N_EQ - 1
    chk("cal %s funcionários" % dia.strftime("%d/%m"), dsp, aus.cell(row=base + 2, column=CAL_C1 + 1 + d).value)
    chk("cal %s vagas" % dia.strftime("%d/%m"), vag, aus.cell(row=base + 3, column=CAL_C1 + 1 + d).value)
    chk("cal %s déficit" % dia.strftime("%d/%m"), max(0, vag - dsp),
        aus.cell(row=base + 4, column=CAL_C1 + 1 + d).value)

ok = sum(1 for r in res if r[0])
print("RECONCILIAÇÃO: %d verificações · %d OK · %d divergências" % (len(res), ok, len(res) - ok))
for r in res:
    if not r[0]:
        print("   DIVERGÊNCIA:", r[1], "| esperado =", r[2], "| planilha =", r[3])
sys.exit(1 if ok != len(res) else 0)
