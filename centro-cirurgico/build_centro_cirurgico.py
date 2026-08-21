# -*- coding: utf-8 -*-
"""
Centro Cirúrgico — Escala Diária (versão enxuta, operada pelo Painel)

Serviço:
  8 salas x 2 técnicos + admissão x 2 + box de preparo oftalmológico x 1 +
  sala de recém-nascido x 1 = 20 vagas por dia, para 22 técnicos.
  Sala 6 exclusiva do centro obstétrico, sala 7 reservada a urgências,
  box de preparo apoia a sala 8. Limpeza de 20 min ao fim de cada cirurgia: quando a
  agenda emenda sem folga, a planilha mostra o atraso que isso gera.
  Não se realizam cirurgias cardíacas.

Habilidade: marca-se X na aba Equipe, uma coluna por especialidade.
  A planilha cruza as especialidades que passam em cada sala no dia com o X
  dos dois técnicos escalados e diz o que está coberto, o que está coberto por
  um só e o que não está coberto por ninguém.

Abas: Mapa do Dia (trabalho do dia) · Agenda do Dia · Equipe · Folgas e Férias ·
      Configuração · Calc e Calc_Salas (ocultas, só cálculo).
"""
import random
from datetime import date, time, timedelta
from abas import ABA_AGENDA, ABA_CFG, ABA_EQUIPE, ABA_FOLGAS, ABA_MAPA, ABA_PAINEL
from alocacao import alocar
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule

OUT = "/home/user/umm-hora-a-hora/centro-cirurgico/Centro_Cirurgico_Escala.xlsx"

# ---------------------------------------------------------------- dimensões
N_ESP, N_POS, N_EQ, N_MAPA, N_AUS, N_CIR = 20, 16, 30, 200, 150, 60
JOGO_K, DIAS = 13, 31
ESP_R1, ESP_R2 = 22, 21 + N_ESP          # Configuração: especialidades
POS_R1, POS_R2 = ESP_R2 + 4, ESP_R2 + 3 + N_POS
FER_R1, FER_R2 = POS_R2 + 4, POS_R2 + 3 + 20
AUS_T1, AUS_T2 = FER_R2 + 4, FER_R2 + 3 + 7
CIR_R1, CIR_R2 = AUS_T2 + 4, AUS_T2 + 3 + N_CIR   # Configuração: cirurgiões
EQ_R1, EQ_R2 = 2, 1 + N_EQ               # Equipe
XC1, XC2 = 8, 7 + N_ESP                  # Equipe: colunas H.. do X
XL1, XL2 = get_column_letter(XC1), get_column_letter(XC2)
MP_R1, MP_R2 = 2, 1 + N_MAPA             # Mapa
AU_R1, AU_R2 = 2, 1 + N_AUS              # Ausencias
CAL_C1 = 9                               # Ausencias: calendário a partir da coluna I
MIX_R1, MIX_R2 = 2, 1 + N_POS            # Calc: mix por posto
COB_R1, COB_R2 = MIX_R2 + 3, MIX_R2 + 2 + N_POS
SUG_R1, SUG_R2 = COB_R2 + 3, COB_R2 + 2 + N_EQ
N_GLOB = 4                               # ações que não são de um ambiente
ACO_R1, ACO_R2 = SUG_R2 + 3, SUG_R2 + 2 + N_GLOB + N_POS   # Calc: fila de ações
RNK_R1, RNK_R2 = ACO_R2 + 3, ACO_R2 + 2 + N_POS            # Calc: rankings do painel
N_ACOES_VISIVEIS = 8
CC1, CC2 = 5, 4 + N_ESP                  # Calc: colunas E.. das especialidades
CL1, CL2 = get_column_letter(CC1), get_column_letter(CC2)
TOT_C, DISP_C, OCUP_C = CC2 + 1, CC2 + 2, CC2 + 3
TOT_L, DISP_L, OCUP_L = (get_column_letter(c) for c in (TOT_C, DISP_C, OCUP_C))

S_PAI, S_MAP, S_EQP, S_AUS = ABA_MAPA, ABA_AGENDA, ABA_EQUIPE, ABA_FOLGAS
S_CFG, S_CAL, S_SAL = ABA_CFG, "Calc", "Calc_Salas"
S_DASH = ABA_PAINEL

def R(sheet, addr):
    return "'%s'!%s" % (sheet, addr)

# ---------------------------------------------------------------- estilo
AZ, AZ_CLR, AM, CINZA = "1F3864", "DDEBF7", "FFF2CC", "F2F2F2"
VERDE, VERDE_T, AMAR, AMAR_T, VERM, VERM_T = "C6EFCE", "006100", "FFEB9C", "9C6500", "FFC7CE", "9C0006"
F_IN   = Font(name="Calibri", size=10, color="0070C0")
F_OUT  = Font(name="Calibri", size=10)
F_REF  = Font(name="Calibri", size=10, color="006100", italic=True)
F_HEAD = Font(name="Calibri", size=10, color="FFFFFF", bold=True)
F_TIT  = Font(name="Calibri", size=14, color=AZ, bold=True)
F_SEC  = Font(name="Calibri", size=11, color=AZ, bold=True)
F_NOTA = Font(name="Calibri", size=9, color="7F7F7F", italic=True)
FILL_HEAD = PatternFill("solid", fgColor=AZ)
FILL_IN   = PatternFill("solid", fgColor=AZ_CLR)
FILL_PREM = PatternFill("solid", fgColor=AM)
FILL_CZ   = PatternFill("solid", fgColor=CINZA)
THIN = Side(style="thin", color="BFBFBF")
BORD = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CTR  = Alignment(horizontal="center", vertical="center")
CTRW = Alignment(horizontal="center", vertical="center", wrap_text=True)
LFT  = Alignment(horizontal="left", vertical="center")
LFTW = Alignment(horizontal="left", vertical="center", wrap_text=True)
ROT  = Alignment(horizontal="center", vertical="bottom", text_rotation=90)

def head(ws, row, labels, col0=1, height=30):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=col0 + i, value=t)
        c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = CTRW; c.border = BORD
    ws.row_dimensions[row].height = height

def widths(ws, m):
    for col, w in m.items():
        ws.column_dimensions[col].width = w

def sec(ws, row, texto, span=11):
    ws.cell(row=row, column=1, value=texto).font = F_SEC
    for i in range(span):
        c = ws.cell(row=row, column=1 + i)
        c.fill = FILL_CZ; c.border = BORD

# ---------------------------------------------------------------- serviço
ESPECIALIDADES = [   # (código, especialidade, tipo, duração média em min)
    ("ORT", "Ortopedia",             "Cirúrgica", 120), ("TRA", "Traumatologia",        "Cirúrgica", 90),
    ("CGE", "Cirurgia Geral",        "Cirúrgica", 90),  ("BAR", "Cirurgia Bariátrica",  "Cirúrgica", 150),
    ("PED", "Cirurgia Pediátrica",   "Cirúrgica", 75),  ("NEU", "Neurocirurgia",        "Cirúrgica", 210),
    ("CES", "Cesariana",             "Cirúrgica", 60),  ("GIN", "Ginecologia",          "Cirúrgica", 90),
    ("URO", "Urologia",              "Cirúrgica", 90),  ("OFT", "Oftalmologia",         "Cirúrgica", 45),
    ("OTO", "Otorrinolaringologia",  "Cirúrgica", 75),  ("BMF", "Buco-Maxilo-Facial",   "Cirúrgica", 120),
    ("PLA", "Cirurgia Plástica",     "Cirúrgica", 120), ("VAS", "Cirurgia Vascular",    "Cirúrgica", 150),
    ("TOR", "Cirurgia Torácica",     "Cirúrgica", 120),
    ("ADM", "Admissão",              "Apoio",     0),   ("RN",  "Sala de recém-nascido","Apoio",     0),
]
ESP_NOMES = [e[1] for e in ESPECIALIDADES]
ESP_IDX = {e[1]: i for i, e in enumerate(ESPECIALIDADES)}
ESP_DUR = {e[1]: e[3] for e in ESPECIALIDADES}

POSTOS = [  # (cód, nome, tipo, necessários, mínimo, prioridade, especialidade ref.,
            #  funciona em, aceita encaixe, obs)
    ("SO-01", "Sala 1", "Sala cirúrgica", 2, 2,  5, "Ortopedia",            "Seg a Sex",     "Sim", "Eletivas de ortopedia"),
    ("SO-02", "Sala 2", "Sala cirúrgica", 2, 2,  6, "Cirurgia Geral",       "Seg a Sex",     "Sim", "Eletivas de cirurgia geral"),
    ("SO-03", "Sala 3", "Sala cirúrgica", 2, 2,  9, "Neurocirurgia",        "Seg a Sex",     "Sim", "Eletivas de neurocirurgia"),
    ("SO-04", "Sala 4", "Sala cirúrgica", 2, 2, 10, "Cirurgia Plástica",    "Seg a Sex",     "Sim", "Plástica e vascular"),
    ("SO-05", "Sala 5", "Sala cirúrgica", 2, 2,  7, "Ginecologia",          "Seg a Sex",     "Sim", "Gineco e urologia"),
    ("SO-06", "Sala 6", "Sala cirúrgica", 2, 2,  2, "Cesariana",            "Todos os dias", "Não", "EXCLUSIVA do centro obstétrico"),
    ("SO-07", "Sala 7", "Sala cirúrgica", 2, 2,  1, "Cirurgia Geral",       "Todos os dias", "Não", "RESERVADA a urgências"),
    ("SO-08", "Sala 8", "Sala cirúrgica", 2, 2,  8, "Oftalmologia",         "Seg a Sex",     "Sim", "Oftalmologia"),
    ("ADM",   "Admissão", "Apoio", 2, 1,  4, "Admissão",                    "Todos os dias", "Não", "Recepção e preparo do paciente"),
    ("BOX",   "Box de preparo oftalmológico", "Apoio", 1, 1, 11, "Oftalmologia", "Seg a Sex", "Não", "Apoio da Sala 8"),
    ("RN",    "Sala de recém-nascido", "Apoio", 1, 1,  3, "Sala de recém-nascido", "Todos os dias", "Não", "Bloco obstétrico"),
]
TIPOS_AUS = [("Folga", "F"), ("Férias", "FR"), ("Atestado", "AT"), ("Licença", "LI"),
             ("Treinamento", "TR"), ("FH", "FH"), ("Licença gestação", "LG")]
CORES_AUS = ["DDEBF7", "FFC7CE", "FFEB9C", "E4DFEC", "D9E1F2", "E2EFDA", "FCE4D6"]
FERIADOS = [(date(2026, 1, 1), "Confraternização Universal"), (date(2026, 2, 16), "Carnaval"),
            (date(2026, 2, 17), "Carnaval"), (date(2026, 4, 3), "Sexta-feira Santa"),
            (date(2026, 4, 21), "Tiradentes"), (date(2026, 5, 1), "Dia do Trabalho"),
            (date(2026, 6, 4), "Corpus Christi"), (date(2026, 9, 7), "Independência"),
            (date(2026, 10, 12), "Nossa Senhora Aparecida"), (date(2026, 11, 2), "Finados"),
            (date(2026, 11, 15), "Proclamação da República"), (date(2026, 12, 25), "Natal")]

DIA = date(2026, 8, 20)
PERIODO_INI = date(2026, 8, 16)
TURNO_INI, TURNO_FIM, TURNO_MIN = time(7, 0), time(13, 0), 360
LIMPEZA, JANELA_MIN = 20, 30
COORDENACAO = "Coordenação de Enfermagem"

# ---------------------------------------------------------------- cadastro de demonstração
NOMES = ["Adriana Salvi","Bruna Cordeiro","Camila Bertoldi","Daiane Prestes","Elaine Mafra",
 "Fernanda Klein","Gisele Antunes","Heloísa Perin","Ismael Kanitz","Joana Belincanta",
 "Kelly Marchi","Luciano Bordin","Marcia Tonet","Nádia Fávero","Odair Bianchi",
 "Patrícia Zortéa","Rafaela Gubert","Simone Dalpra","Tatiane Bolzan","Vagner Sartori",
 "Wanessa Piccoli","Zuleide Marcon"]
random.seed(20260819)

PERFIL = [  # especialidades que cada técnico de demonstração marca com X
 ["Ortopedia","Traumatologia","Admissão"], ["Ortopedia","Traumatologia","Cirurgia Geral"],
 ["Cirurgia Geral","Cirurgia Bariátrica","Admissão"], ["Cirurgia Geral","Cirurgia Pediátrica","Admissão"],
 ["Neurocirurgia","Cirurgia Geral"], ["Neurocirurgia","Ortopedia","Admissão"],
 ["Cirurgia Plástica","Cirurgia Vascular"], ["Cirurgia Plástica","Buco-Maxilo-Facial","Admissão"],
 ["Ginecologia","Urologia","Admissão"], ["Ginecologia","Urologia","Cesariana"],
 ["Oftalmologia","Otorrinolaringologia"], ["Oftalmologia","Otorrinolaringologia","Admissão"],
 ["Cesariana","Sala de recém-nascido"], ["Cesariana","Ginecologia","Sala de recém-nascido"],
 ["Admissão","Cirurgia Geral"], ["Admissão","Ortopedia"],
 ["Sala de recém-nascido","Cesariana"], ["Cirurgia Geral","Cirurgia Bariátrica","Cirurgia Pediátrica"],
 ["Ortopedia","Cirurgia Vascular"], ["Otorrinolaringologia","Buco-Maxilo-Facial","Oftalmologia"],
 ["Oftalmologia","Cirurgia Plástica"], ["Admissão","Sala de recém-nascido","Cirurgia Geral"]]
EQUIPE = [("TEC-%03d" % (i + 1), NOMES[i], "", "Ativo") for i in range(len(NOMES))]
SKILLS = {NOMES[i]: set(PERFIL[i]) for i in range(len(NOMES))}
AUSENCIAS = [
    ("Zuleide Marcon",  "Férias",      date(2026, 8, 10), date(2026, 8, 24), "Férias programadas"),
    ("Ismael Kanitz",   "Férias",      date(2026, 8,  6), date(2026, 8, 20), "Férias programadas"),
    ("Wanessa Piccoli", "Atestado",    date(2026, 8, 19), date(2026, 8, 21), "Atestado médico"),
    ("Elaine Mafra",    "Folga",       date(2026, 8, 20), date(2026, 8, 20), ""),
    ("Adriana Salvi",   "Folga",       date(2026, 8, 12), date(2026, 8, 12), ""),
    ("Bruna Cordeiro",  "Folga",       date(2026, 8, 13), date(2026, 8, 13), ""),
    ("Camila Bertoldi", "Folga",       date(2026, 8, 17), date(2026, 8, 17), ""),
    ("Daiane Prestes",  "Folga",       date(2026, 8, 18), date(2026, 8, 18), ""),
    ("Gisele Antunes",  "Treinamento", date(2026, 8, 26), date(2026, 8, 27), "Curso de CME"),
    ("Odair Bianchi",   "Licença",     date(2026, 8, 28), date(2026, 8, 31), ""),
]
AFASTADOS = set()

# ---------------------------------------------------------------- cadastro real (opcional, fora do git)
import json as _json, os as _os
_REAL = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "dados", "equipe_real.json")
USANDO_REAL = _os.path.exists(_REAL) and _os.environ.get("DEMO") != "1"
if USANDO_REAL:
    _d = _json.load(open(_REAL, encoding="utf-8"))
    _p = lambda x: date(*[int(v) for v in x.split("-")])
    AFASTADOS = set(_d.get("afastados", []))
    EQUIPE = [(pp.get("matricula", ""), pp["nome"], pp.get("coren", ""),
               "Afastado" if pp["nome"] in AFASTADOS else "Ativo") for pp in _d["pessoas"]]
    NOMES = [e[1] for e in EQUIPE]
    # X PROVISÓRIO: 3 especialidades por técnica, distribuídas em rodízio para que toda
    # especialidade tenha gente. É um ponto de partida para a coordenação corrigir — não
    # reflete a habilidade real de ninguém.
    _esp = [e[1] for e in ESPECIALIDADES]
    SKILLS = {n: {_esp[(i + d) % len(_esp)] for d in (0, 5, 11)} for i, n in enumerate(NOMES)}
    AUSENCIAS = [(a["tec"], a["tipo"], _p(a["ini"]), _p(a["fim"]), "") for a in _d["ausencias"]]
    if _d.get("periodo_ini"): PERIODO_INI = _p(_d["periodo_ini"])
    if _d.get("coordenacao"): COORDENACAO = _d["coordenacao"]
    OUT = OUT.replace(".xlsx", "_REAL.xlsx")
AUSENTES = {a[0] for a in AUSENCIAS if a[2] <= DIA <= a[3]}

# ---------------------------------------------------------------- agenda do dia (demonstração)
SALA_ESP = {"SO-01": ["Ortopedia", "Traumatologia"],
            "SO-02": ["Cirurgia Geral", "Cirurgia Bariátrica", "Cirurgia Pediátrica"],
            "SO-03": ["Neurocirurgia"], "SO-04": ["Cirurgia Plástica", "Cirurgia Vascular"],
            "SO-05": ["Ginecologia", "Urologia"], "SO-06": ["Cesariana"],
            "SO-07": ["Cirurgia Geral"], "SO-08": ["Oftalmologia", "Otorrinolaringologia", "Buco-Maxilo-Facial"]}
PROCS = {"Ortopedia": ["Artroplastia total de joelho", "Artroscopia de ombro"],
 "Traumatologia": ["Osteossíntese de fêmur", "Redução de fratura de rádio"],
 "Cirurgia Geral": ["Colecistectomia videolaparoscópica", "Herniorrafia inguinal", "Apendicectomia"],
 "Cirurgia Bariátrica": ["Gastroplastia em Y de Roux"], "Cirurgia Pediátrica": ["Postectomia"],
 "Neurocirurgia": ["Craniotomia para tumor", "Artrodese lombar"],
 "Cesariana": ["Cesariana", "Cesariana com laqueadura"],
 "Ginecologia": ["Histerectomia total", "Videolaparoscopia diagnóstica"],
 "Urologia": ["RTU de próstata", "Nefrolitotripsia"],
 "Oftalmologia": ["Facectomia com implante de LIO", "Pterígio", "Vitrectomia"],
 "Otorrinolaringologia": ["Amigdalectomia", "Septoplastia"], "Buco-Maxilo-Facial": ["Osteotomia mandibular"],
 "Cirurgia Plástica": ["Dermolipectomia abdominal"], "Cirurgia Vascular": ["Safenectomia"]}
CIRURGIOES = ["Dr. Almeida","Dra. Bernardes","Dr. Coelho","Dra. Delgado","Dr. Esteves",
              "Dra. Fialho","Dr. Gouveia","Dra. Hirano"]
CIR_TAB = [  # de/para cirurgião -> especialidade usado na importação da agenda
    (n, e, "") for n, e in zip(CIRURGIOES,
        ["Ortopedia", "Cirurgia Geral", "Neurocirurgia", "Cirurgia Plástica",
         "Ginecologia", "Urologia", "Oftalmologia", "Cirurgia Vascular"])]
_CIRJ = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "dados",
                     "cirurgioes_real.json")
if USANDO_REAL and _os.path.exists(_CIRJ):
    CIR_TAB = [(c["nome"], c.get("especialidade", ""), c.get("obs", ""))
               for c in _json.load(open(_CIRJ, encoding="utf-8"))]
BASE_MIN = TURNO_INI.hour * 60 + TURNO_INI.minute

def build_mapa():
    cirs = []
    plano = {"SO-01": (0.80, 0), "SO-02": (0.75, 40), "SO-03": (0.70, 0), "SO-04": (0.60, 30),
             "SO-05": (0.80, 0), "SO-06": (0.30, 0), "SO-07": (0.25, 0), "SO-08": (0.85, 0)}
    for sala, (alvo, folga) in plano.items():
        esps = SALA_ESP[sala]; decorrido = k = 0
        while decorrido < TURNO_MIN * alvo and k < 6:
            esp = esps[k % len(esps)]
            dur = int(round(ESP_DUR[esp] * random.uniform(0.8, 1.15) / 5.0) * 5)
            if decorrido + dur + LIMPEZA > TURNO_MIN:
                break
            ini = BASE_MIN + decorrido
            st = "Cancelada" if (sala == "SO-02" and k == 2) else "Agendada"
            cirs.append(dict(data=DIA, sala=sala, ini=ini, fim=ini + dur, esp=esp,
                             proc=PROCS[esp][k % len(PROCS[esp])],
                             cir=CIRURGIOES[(len(cirs) + k) % len(CIRURGIOES)], status=st, dur=dur))
            decorrido += dur + LIMPEZA + (folga if k == 1 else 0)
            k += 1
    cirs.sort(key=lambda c: (c["sala"], c["ini"]))
    return cirs
MAPA = [] if USANDO_REAL else build_mapa()   # no arquivo real a agenda vem da importação

def esp_do_posto(cod):
    """Especialidades que passam pelo posto no dia (ou a de referência, se não há agenda)."""
    p = [x for x in POSTOS if x[0] == cod][0]
    mins = {}
    if p[2] == "Sala cirúrgica":
        for c in MAPA:
            if c["sala"] == cod and c["status"] not in ("Cancelada", "Suspensa"):
                mins[c["esp"]] = mins.get(c["esp"], 0) + c["dur"] + LIMPEZA
    if not mins:
        mins = {p[6]: TURNO_MIN}
    return mins

def opera_hoje(cod):
    """O posto funciona nessa data? (dia da semana, feriado e status do cadastro)"""
    p = [x for x in POSTOS if x[0] == cod][0]
    if p[7] == "Seg a Sex" and (DIA.weekday() > 4 or DIA in FER_DATAS):
        return False
    if p[7] == "Seg a Sáb" and (DIA.weekday() > 5 or DIA in FER_DATAS):
        return False
    return True

FER_DATAS = {f[0] for f in FERIADOS}

def build_escala():
    disp = [e[1] for e in EQUIPE if e[3] == "Ativo" and e[1] not in AUSENTES]
    postos = [(p[0], p[3], p[4], p[5]) for p in POSTOS if opera_hoje(p[0])]
    esp = {cod: list(esp_do_posto(cod)) for cod, _, _, _ in postos}
    return alocar(postos, esp, disp, SKILLS)

ALOC = build_escala()   # {cod: [técnico 1, técnico 2]}

# ================================================================ WORKBOOK
wb = Workbook()
ws_dash = wb.active; ws_dash.title = S_DASH
ws_pai = wb.create_sheet(S_PAI)
ws_map = wb.create_sheet(S_MAP); ws_eqp = wb.create_sheet(S_EQP)
ws_aus = wb.create_sheet(S_AUS); ws_cfg = wb.create_sheet(S_CFG)
ws_cal = wb.create_sheet(S_CAL); ws_sal = wb.create_sheet(S_SAL)
for w in wb.worksheets:
    w.sheet_view.showGridLines = False
ws_cal.sheet_state = ws_sal.sheet_state = "hidden"

def dn(name, ref):
    wb.defined_names.add(DefinedName(name, attr_text=ref))

def fmt(ws, r1, r2, c1, c2, font=F_IN, align=None, numfmt=None, fill=None):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            cel = ws.cell(row=r, column=c)
            cel.border = BORD; cel.font = font
            if align: cel.alignment = align
            if numfmt: cel.number_format = numfmt
            if fill: cel.fill = fill

# ---------------------------------------------------------------- CONFIGURAÇÃO
ws_cfg["A1"] = "CONFIGURAÇÃO"; ws_cfg["A1"].font = F_TIT
ws_cfg["A2"] = ("Mexe-se raramente. Células amarelas são premissas; a data da escala fica no Painel.")
ws_cfg["A2"].font = F_NOTA
widths(ws_cfg, {"A": 46, "B": 16, "C": 14, "D": 14, "E": 12, "F": 13, "G": 30, "H": 14,
                "I": 11, "J": 40, "K": 14})

def prem(row, label, valor, nf=None, nota=None):
    ws_cfg.cell(row=row, column=1, value=label).font = F_OUT
    c = ws_cfg.cell(row=row, column=2, value=valor)
    c.font = F_IN; c.fill = FILL_PREM; c.border = BORD; c.alignment = CTR
    if nf: c.number_format = nf
    if nota: ws_cfg.cell(row=row, column=3, value=nota).font = F_NOTA
    return c

sec(ws_cfg, 4, "1. IDENTIFICAÇÃO", 3)
prem(5, "Unidade / Hospital", "Hospital — preencher")
prem(6, "Setor", "Centro Cirúrgico")
prem(7, "Coordenação responsável", COORDENACAO)
prem(8, "Primeiro dia do período da escala", PERIODO_INI, "DD/MM/YYYY", "Periodo_Ini")
for r in (5, 6, 7):
    ws_cfg.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    ws_cfg.cell(row=r, column=2).alignment = LFT

sec(ws_cfg, 10, "2. PLANTÃO", 3)
prem(11, "Início do plantão", TURNO_INI, "HH:MM", "Turno_Ini")
prem(12, "Fim do plantão", TURNO_FIM, "HH:MM", "Turno_Fim")
ws_cfg.cell(row=13, column=1, value="Minutos do plantão").font = F_OUT
c = ws_cfg.cell(row=13, column=2, value="=MOD(B12-B11,1)*1440")
c.border = BORD; c.alignment = CTR; c.number_format = "0"
ws_cfg.cell(row=13, column=3, value="Turno_Min").font = F_NOTA

sec(ws_cfg, 15, "3. OPERAÇÃO", 3)
prem(16, "Limpeza e preparação após cada cirurgia (min)", LIMPEZA, "0", "Limpeza_Min")
prem(17, "Janela mínima para considerar encaixe (min)", JANELA_MIN, "0", "Janela_Min")
ws_cfg.cell(row=18, column=1,
            value="A limpeza sempre acontece. Quando a agenda emenda uma cirurgia na outra, ela cabe "
                  "na folga se a cirurgia terminar antes do previsto; se a cirurgia for até o fim do "
                  "horário, a limpeza empurra a seguinte — é isso que a coluna Atraso previsto "
                  "mostra.").font = F_NOTA

sec(ws_cfg, ESP_R1 - 2, "4. ESPECIALIDADES — viram as colunas de habilidade na aba Equipe", 5)
head(ws_cfg, ESP_R1 - 1, ["Código", "Especialidade", "Tipo", "Duração média (min)", "Ativa"], height=28)
fmt(ws_cfg, ESP_R1, ESP_R2, 1, 5, align=CTR)
for i in range(N_ESP):
    r = ESP_R1 + i
    ws_cfg.cell(row=r, column=2).alignment = LFT
    if i < len(ESPECIALIDADES):
        cod, nome, tipo, dur = ESPECIALIDADES[i]
        for j, v in enumerate((cod, nome, tipo, dur, "Sim")):
            ws_cfg.cell(row=r, column=1 + j, value=v)
ws_cfg.cell(row=ESP_R2 + 1, column=1,
            value="Não se realizam cirurgias cardíacas. As duas de tipo Apoio (Admissão e Sala de "
                  "recém-nascido) não são cirurgias, mas são postos que exigem habilidade.").font = F_NOTA

sec(ws_cfg, POS_R1 - 2, "5. POSTOS", 10)
head(ws_cfg, POS_R1 - 1, ["Código", "Posto", "Tipo", "Técnicos", "Mínimo", "Prioridade",
                          "Especialidade de referência", "Funciona em", "Status", "Observação",
                          "Aceita encaixe"], height=32)
fmt(ws_cfg, POS_R1, POS_R2, 1, 11, align=CTR)
for i in range(N_POS):
    r = POS_R1 + i
    for c_ in (2, 7, 10):
        ws_cfg.cell(row=r, column=c_).alignment = LFT
    if i < len(POSTOS):
        cod, nome, tipo, nec, mini, prior, esp, func, encaixe, obs = POSTOS[i]
        for j, v in enumerate((cod, nome, tipo, nec, mini, prior, esp, func, "Ativo", obs,
                               encaixe)):
            ws_cfg.cell(row=r, column=1 + j, value=v)
ws_cfg.cell(row=POS_R2 + 1, column=1,
            value="Prioridade 1 é coberta primeiro quando falta gente. 'Funciona em' define os dias: "
                  "nos fins de semana e feriados os postos de dia útil não operam e as vagas do dia "
                  "caem junto. 'Aceita encaixe' diz se a sala entra no ranking de encaixe do "
                  "Painel — a de urgência e a do centro obstétrico ficam de fora.").font = F_NOTA

sec(ws_cfg, FER_R1 - 2, "6. FERIADOS — nesses dias os postos de dia útil não operam", 3)
head(ws_cfg, FER_R1 - 1, ["Data", "Feriado", ""], height=18)
fmt(ws_cfg, FER_R1, FER_R2, 1, 2, align=CTR, fill=FILL_PREM)
for i in range(20):
    r = FER_R1 + i
    ws_cfg.cell(row=r, column=1).number_format = "DD/MM/YYYY"
    ws_cfg.cell(row=r, column=2).alignment = LFT
    if i < len(FERIADOS):
        ws_cfg.cell(row=r, column=1, value=FERIADOS[i][0])
        ws_cfg.cell(row=r, column=2, value=FERIADOS[i][1])

sec(ws_cfg, AUS_T1 - 2, "7. TIPOS DE AUSÊNCIA", 3)
head(ws_cfg, AUS_T1 - 1, ["Tipo", "Sigla", "Cor"], height=18)
fmt(ws_cfg, AUS_T1, AUS_T2, 1, 3, font=F_OUT, align=CTR)
for i, (tp, sg) in enumerate(TIPOS_AUS):
    r = AUS_T1 + i
    ws_cfg.cell(row=r, column=1, value=tp).alignment = LFT
    ws_cfg.cell(row=r, column=2, value=sg)
    ws_cfg.cell(row=r, column=3).fill = PatternFill("solid", fgColor=CORES_AUS[i])

sec(ws_cfg, CIR_R1 - 2, "8. CIRURGIÕES — de/para usado ao importar a agenda do dia", 3)
head(ws_cfg, CIR_R1 - 1, ["Cirurgião (como sai na agenda)", "Especialidade", "Observação"], height=28)
fmt(ws_cfg, CIR_R1, CIR_R2, 1, 3, align=CTR, fill=FILL_PREM)
for i in range(N_CIR):
    r = CIR_R1 + i
    for c_ in (1, 2, 3):
        ws_cfg.cell(row=r, column=c_).alignment = LFT
    if i < len(CIR_TAB):
        for j, v in enumerate(CIR_TAB[i]):
            ws_cfg.cell(row=r, column=1 + j, value=v)
ws_cfg.cell(row=CIR_R2 + 1, column=1,
            value="A agenda do hospital não traz a especialidade da cirurgia, traz o cirurgião. "
                  "Preencha a especialidade de cada cirurgião uma única vez: a importação da agenda "
                  "passa a preencher a coluna Especialidade do Mapa sozinha e acrescenta aqui, em "
                  "branco, todo cirurgião novo que aparecer.").font = F_NOTA

ws_cfg.cell(row=4, column=7, value="LISTAS AUXILIARES").font = F_SEC
head(ws_cfg, 5, ["Status cadastral", "Status da cirurgia", "Tipo de posto"], col0=7, height=28)
for j, col in enumerate((["Ativo", "Afastado", "Desligado"],
                         ["Agendada", "Realizada", "Cancelada", "Suspensa"],
                         ["Sala cirúrgica", "Apoio"])):
    for i, v in enumerate(col):
        cc = ws_cfg.cell(row=6 + i, column=7 + j, value=v)
        cc.border = BORD; cc.alignment = CTR; cc.font = F_OUT

dn("Periodo_Ini", R(S_CFG, "$B$8")); dn("Turno_Ini", R(S_CFG, "$B$11"))
dn("Turno_Fim", R(S_CFG, "$B$12")); dn("Turno_Min", R(S_CFG, "$B$13"))
dn("Limpeza_Min", R(S_CFG, "$B$16")); dn("Janela_Min", R(S_CFG, "$B$17"))
dn("Data_Mapa", R(S_PAI, "$A$6"))
for nm, col in (("Esp_Cod", "A"), ("Esp_Nome", "B"), ("Esp_Tipo", "C"), ("Esp_Dur", "D")):
    dn(nm, R(S_CFG, "$%s$%d:$%s$%d" % (col, ESP_R1, col, ESP_R2)))
for nm, col in (("Postos_Cod", "A"), ("Postos_Nome", "B"), ("Postos_Tipo", "C"), ("Postos_Nec", "D"),
                ("Postos_Min", "E"), ("Postos_Prior", "F"), ("Postos_Esp", "G"),
                ("Postos_Func", "H"), ("Postos_Status", "I"), ("Postos_Encaixe", "K")):
    dn(nm, R(S_CFG, "$%s$%d:$%s$%d" % (col, POS_R1, col, POS_R2)))
dn("Feriados", R(S_CFG, "$A$%d:$A$%d" % (FER_R1, FER_R2)))
dn("Aus_Tipos", R(S_CFG, "$A$%d:$A$%d" % (AUS_T1, AUS_T2)))
dn("Aus_Siglas", R(S_CFG, "$B$%d:$B$%d" % (AUS_T1, AUS_T2)))
for nm, col in (("Cir_Nome", "A"), ("Cir_Esp", "B")):
    dn(nm, R(S_CFG, "$%s$%d:$%s$%d" % (col, CIR_R1, col, CIR_R2)))
dn("Lista_StatusCad", R(S_CFG, "$G$6:$G$8"))
dn("Lista_StatusCir", R(S_CFG, "$H$6:$H$9"))
dn("Lista_TipoPosto", R(S_CFG, "$I$6:$I$7"))
dn("Lista_Especialidades", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (
    R(S_CFG, "$B$%d" % ESP_R1), R(S_CFG, "$B$%d:$B$%d" % (ESP_R1, ESP_R2))))
dn("Lista_Postos", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (
    R(S_CFG, "$A$%d" % POS_R1), R(S_CFG, "$A$%d:$A$%d" % (POS_R1, POS_R2))))

# ---------------------------------------------------------------- EQUIPE (cadastro + habilidades em X)
head(ws_eqp, 1, ["Matrícula", "Nome do técnico", "COREN", "Status", "SITUAÇÃO NA DATA",
                 "Ausente até", "Observação"] + [""] * N_ESP + ["Nº de especialidades"], height=170)
for i in range(N_ESP):
    c = ws_eqp.cell(row=1, column=XC1 + i, value='=IF(%s="","",%s)' % (
        R(S_CFG, "$B$%d" % (ESP_R1 + i)), R(S_CFG, "$B$%d" % (ESP_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = ROT
widths(ws_eqp, {"A": 12, "B": 30, "C": 11, "D": 11, "E": 17, "F": 12, "G": 24})
for i in range(N_ESP):
    ws_eqp.column_dimensions[get_column_letter(XC1 + i)].width = 4.6
ws_eqp.column_dimensions[get_column_letter(XC2 + 1)].width = 10
fmt(ws_eqp, EQ_R1, EQ_R2, 1, 7, align=CTR)
ws_eqp.cell(row=EQ_R2 + 1, column=1, value=(
    "X PROVISÓRIO: cada técnica veio com 3 especialidades marcadas em rodízio, só para a "
    "planilha sair do lugar. Corrija linha por linha — é este X que decide quem vai para "
    "cada sala." if USANDO_REAL else
    "Marque X na especialidade que a técnica faz; deixe em branco onde não faz.")).font = F_NOTA

for i in range(N_EQ):
    r = EQ_R1 + i
    ws_eqp.cell(row=r, column=2).alignment = LFT; ws_eqp.cell(row=r, column=7).alignment = LFT
    if i < len(EQUIPE):
        for j, v in enumerate(EQUIPE[i]):
            ws_eqp.cell(row=r, column=1 + j, value=v)
    e = ws_eqp.cell(row=r, column=5, value=(
        '=IF($B{r}="","",IF($D{r}<>"Ativo",$D{r},'
        'IFERROR(INDEX(Aus_Tipo,MATCH($B{r},Aus_Ativa,0)),"Disponível")))').format(r=r))
    f = ws_eqp.cell(row=r, column=6, value=(
        '=IF(OR($B{r}="",$E{r}="Disponível"),"",IFERROR(INDEX(Aus_Fim,MATCH($B{r},Aus_Ativa,0)),""))').format(r=r))
    e.font = F_OUT; f.font = F_OUT; f.number_format = "DD/MM"
    nome = EQUIPE[i][1] if i < len(EQUIPE) else None
    for j in range(N_ESP):
        cel = ws_eqp.cell(row=r, column=XC1 + j)
        cel.border = BORD; cel.font = Font(name="Calibri", size=10, color="0070C0", bold=True)
        cel.alignment = CTR
        if nome and j < len(ESPECIALIDADES) and ESPECIALIDADES[j][1] in SKILLS.get(nome, set()):
            cel.value = "X"
    n = ws_eqp.cell(row=r, column=XC2 + 1, value='=IF($B{r}="","",COUNTIF(${a}{r}:${b}{r},"X"))'.format(
        r=r, a=XL1, b=XL2))
    n.border = BORD; n.alignment = CTR; n.font = F_OUT; n.number_format = "0"
ws_eqp.freeze_panes = "H2"; ws_eqp.auto_filter.ref = "A1:G%d" % EQ_R2
ws_eqp.cell(row=EQ_R2 + 2, column=1,
            value="Marque X na especialidade que o técnico faz. Célula em branco = não faz (ou ainda não "
                  "avaliado). As colunas vêm da lista de especialidades da aba Configuração.").font = F_NOTA
for nm, col in (("Equipe_Mat", "A"), ("Equipe_Nome", "B"), ("Equipe_Status", "D"), ("Equipe_Situacao", "E")):
    dn(nm, R(S_EQP, "$%s$%d:$%s$%d" % (col, EQ_R1, col, EQ_R2)))
dn("Equipe_X", R(S_EQP, "$%s$%d:$%s$%d" % (XL1, EQ_R1, XL2, EQ_R2)))
dn("Equipe_NEsp", R(S_EQP, "$%s$%d:$%s$%d" % (get_column_letter(XC2 + 1), EQ_R1, get_column_letter(XC2 + 1), EQ_R2)))
dn("Lista_Tecnicos", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (
    R(S_EQP, "$B$2"), R(S_EQP, "$B$%d:$B$%d" % (EQ_R1, EQ_R2))))

# ---------------------------------------------------------------- AUSÊNCIAS (+ calendário do período)
head(ws_aus, 1, ["Técnico", "Tipo", "Data início", "Data fim", "Dias", "Observação",
                 "aux_ativa", "aux_cod"], height=22)
widths(ws_aus, {"A": 30, "B": 15, "C": 12, "D": 12, "E": 7, "F": 26, "G": 9, "H": 8})
for c_ in ("G", "H"):
    ws_aus.column_dimensions[c_].hidden = True
fmt(ws_aus, AU_R1, AU_R2, 1, 6, align=CTR)
for i in range(N_AUS):
    r = AU_R1 + i
    ws_aus.cell(row=r, column=1).alignment = LFT; ws_aus.cell(row=r, column=6).alignment = LFT
    for c_ in (3, 4):
        ws_aus.cell(row=r, column=c_).number_format = "DD/MM/YYYY"
    if i < len(AUSENCIAS):
        tec, tipo, ini, fim, obs = AUSENCIAS[i]
        for j, v in enumerate((tec, tipo, ini, fim)):
            ws_aus.cell(row=r, column=1 + j, value=v)
        ws_aus.cell(row=r, column=6, value=obs)
    d = ws_aus.cell(row=r, column=5, value=(
        '=IF(OR($A{r}="",NOT(ISNUMBER($C{r})),NOT(ISNUMBER($D{r}))),"",$D{r}-$C{r}+1)').format(r=r))
    d.border = BORD; d.alignment = CTR; d.number_format = "0"; d.font = F_OUT
    ws_aus.cell(row=r, column=7, value=(
        '=IF(AND($A{r}<>"",ISNUMBER($C{r}),ISNUMBER($D{r}),$C{r}<=Data_Mapa,$D{r}>=Data_Mapa),$A{r},"")'
    ).format(r=r)).font = F_OUT
    ws_aus.cell(row=r, column=8, value=(
        '=IF($A{r}="",0,IFERROR(MATCH($B{r},Aus_Tipos,0),0))').format(r=r)).font = F_OUT
ws_aus.freeze_panes = "B2"; ws_aus.auto_filter.ref = "A1:F%d" % AU_R2
for nm, col in (("Aus_Tec", "A"), ("Aus_Tipo", "B"), ("Aus_Ini", "C"), ("Aus_Fim", "D"),
                ("Aus_Ativa", "G"), ("Aus_Cod", "H")):
    dn(nm, R(S_AUS, "$%s$%d:$%s$%d" % (col, AU_R1, col, AU_R2)))

# calendário do período, ao lado dos registros
CAL_L = get_column_letter(CAL_C1)
ws_aus.cell(row=1, column=CAL_C1, value="Técnico").font = F_HEAD
ws_aus.cell(row=1, column=CAL_C1).fill = FILL_HEAD
ws_aus.cell(row=1, column=CAL_C1).alignment = CTR
ws_aus.cell(row=1, column=CAL_C1).border = BORD
ws_aus.column_dimensions[CAL_L].width = 30
D1C, D2C = CAL_C1 + 1, CAL_C1 + DIAS
for d in range(DIAS):
    col = get_column_letter(D1C + d)
    ws_aus.column_dimensions[col].width = 4.4
    f = "=Periodo_Ini" if d == 0 else "=%s1+1" % get_column_letter(D1C + d - 1)
    c = ws_aus.cell(row=1, column=D1C + d, value=f)
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = CTR; c.number_format = "D"; c.border = BORD
    w = ws_aus.cell(row=2, column=D1C + d, value=(
        '=IF({c}1="","",CHOOSE(WEEKDAY({c}1),"dom","seg","ter","qua","qui","sex","sáb"))').format(c=col))
    w.font = F_NOTA; w.alignment = CTR
CAL_R1 = 3
for i in range(N_EQ):
    r = CAL_R1 + i
    n = ws_aus.cell(row=r, column=CAL_C1, value='=IF(%s="","",%s)' % (
        R(S_EQP, "$B$%d" % (EQ_R1 + i)), R(S_EQP, "$B$%d" % (EQ_R1 + i))))
    n.font = F_REF; n.border = BORD; n.alignment = LFT
    for d in range(DIAS):
        col = get_column_letter(D1C + d)
        base = '(Aus_Tec=${cl}{r})*(Aus_Ini<={c}$1)*(Aus_Fim>={c}$1)'.format(cl=CAL_L, r=r, c=col)
        cel = ws_aus.cell(row=r, column=D1C + d, value=(
            '=IF(OR(${cl}{r}="",{c}$1=""),"",IF(SUMPRODUCT({b}*(Aus_Cod>0))=0,"",'
            'IF(SUMPRODUCT({b}*(Aus_Cod>0))>1,"!",IFERROR(INDEX(Aus_Siglas,SUMPRODUCT({b}*Aus_Cod)),"!"))))'
        ).format(cl=CAL_L, r=r, c=col, b=base))
        cel.border = BORD; cel.alignment = CTR
        cel.font = Font(name="Calibri", size=9, bold=True)
CAL_R2 = CAL_R1 + N_EQ - 1
for j, rot in enumerate(("Funcionários na data", "Vagas necessárias no dia", "Déficit do dia")):
    r = CAL_R2 + 2 + j
    a = ws_aus.cell(row=r, column=CAL_C1, value=rot)
    a.font = F_SEC if j == 0 else F_OUT; a.alignment = LFT
    for d in range(DIAS):
        col = get_column_letter(D1C + d)
        if j == 0:
            f = ('=IF({c}$1="","",SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Status="Ativo")*'
                 '(COUNTIFS(Aus_Tec,Equipe_Nome,Aus_Ini,"<="&{c}$1,Aus_Fim,">="&{c}$1)=0)))').format(c=col)
        elif j == 1:
            f = ('=IF({c}$1="","",SUMPRODUCT((Postos_Cod<>"")*(Postos_Status="Ativo")*Postos_Nec*'
                 '((Postos_Func="Todos os dias")+'
                 '((Postos_Func="Seg a Sex")*(WEEKDAY({c}$1,2)<=5)*(COUNTIF(Feriados,{c}$1)=0))+'
                 '((Postos_Func="Seg a Sáb")*(WEEKDAY({c}$1,2)<=6)*(COUNTIF(Feriados,{c}$1)=0)))))').format(c=col)
        else:
            f = '=IF({c}$1="","",MAX(0,{c}{r1}-{c}{r0}))'.format(c=col, r0=CAL_R2 + 2, r1=CAL_R2 + 3)
        cel = ws_aus.cell(row=r, column=D1C + d, value=f)
        cel.border = BORD; cel.alignment = CTR; cel.number_format = "0"
        cel.font = Font(name="Calibri", size=9, bold=(j != 1))
ws_aus.cell(row=CAL_R2 + 6, column=CAL_C1,
            value=" · ".join("%s = %s" % (sg, tp) for tp, sg in TIPOS_AUS) +
                  " · ! = registros sobrepostos").font = F_NOTA

# ---------------------------------------------------------------- MAPA CIRÚRGICO
head(ws_map, 1, ["Data", "Sala", "Hora início", "Hora fim", "Especialidade", "Procedimento",
                 "Cirurgião", "Status", "Duração (min)", "Min. ocupação", "Ordem na sala",
                 "Sala liberada às", "Livre até a próxima (min)", "Alerta",
                 "aux", "aux", "aux", "aux", "aux", "aux"], height=42)
widths(ws_map, {"A": 12, "B": 9, "C": 11, "D": 11, "E": 26, "F": 34, "G": 15, "H": 12, "I": 12,
                "J": 13, "K": 11, "L": 13, "M": 15, "N": 38})
for c_ in ("O", "P", "Q", "R", "S", "T"):
    ws_map.column_dimensions[c_].hidden = True
fmt(ws_map, MP_R1, MP_R2, 1, 8, align=CTR)
for i in range(N_MAPA):
    r = MP_R1 + i
    ws_map.cell(row=r, column=1).number_format = "DD/MM/YYYY"
    for c_ in (3, 4):
        ws_map.cell(row=r, column=c_).number_format = "HH:MM"
    for c_ in (5, 6, 7):
        ws_map.cell(row=r, column=c_).alignment = LFT
    if i < len(MAPA):
        m = MAPA[i]
        ws_map.cell(row=r, column=1, value=m["data"]); ws_map.cell(row=r, column=2, value=m["sala"])
        ws_map.cell(row=r, column=3, value=time((m["ini"] // 60) % 24, m["ini"] % 60))
        ws_map.cell(row=r, column=4, value=time((m["fim"] // 60) % 24, m["fim"] % 60))
        ws_map.cell(row=r, column=5, value=m["esp"]); ws_map.cell(row=r, column=6, value=m["proc"])
        ws_map.cell(row=r, column=7, value=m["cir"]); ws_map.cell(row=r, column=8, value=m["status"])
    calc = {
        9:  '=IF(OR($B{r}="",NOT(ISNUMBER($C{r})),NOT(ISNUMBER($D{r}))),"",ROUND(MOD($D{r}-$C{r},1)*1440,0))',
        10: '=IF(NOT(ISNUMBER($I{r})),0,IF(OR($I{r}<=0,$H{r}="Cancelada",$H{r}="Suspensa"),0,$I{r}+Limpeza_Min))',
        16: '=IF(NOT(ISNUMBER($C{r})),0,ROUND(MOD($C{r}-Turno_Ini,1)*1440,0))',
        17: '=IF($J{r}<=0,0,$P{r}+$I{r})',
        19: '=ROW()',
        # minutos em que a sala fica de fato ocupada dentro do plantão: a cirurgia mais a
        # limpeza, cortada no fim do turno e na entrada da cirurgia seguinte — a agenda do
        # hospital emenda uma na outra, e sem esse corte a ocupação passaria de 100%
        20: ('=IF($J{r}<=0,0,MAX(0,MIN($P{r}+$I{r}+Limpeza_Min,Turno_Min,'
             'IFERROR(INDEX(Mapa_RelIni,MATCH($B{r}&"#"&$A{r}&"#"&($K{r}+1),Mapa_Chave,0)),Turno_Min))'
             '-MIN($P{r},Turno_Min)))'),
        11: ('=IF($J{r}<=0,"",SUMPRODUCT((Mapa_Sala=$B{r})*(Mapa_Data=$A{r})*(Mapa_MinOcup>0)*'
             '((Mapa_RelIni<$P{r})+((Mapa_RelIni=$P{r})*(Mapa_Row<=$S{r})))))'),
        18: '=IF($K{r}="","",$B{r}&"#"&$A{r}&"#"&$K{r})',
        12: '=IF($J{r}<=0,"",MOD(Turno_Ini+($Q{r}+Limpeza_Min)/1440,1))',
        13: ('=IF($J{r}<=0,"",MAX(0,IFERROR(INDEX(Mapa_RelIni,MATCH($B{r}&"#"&$A{r}&"#"&($K{r}+1),Mapa_Chave,0)),'
             'Turno_Min)-($Q{r}+Limpeza_Min)))'),
    }
    for col, f in calc.items():
        cel = ws_map.cell(row=r, column=col, value=f.format(r=r))
        cel.border = BORD; cel.alignment = CTR; cel.font = F_OUT
    for col, nf in ((9, "0"), (10, "0"), (11, "0"), (12, "HH:MM"), (13, "0")):
        ws_map.cell(row=r, column=col).number_format = nf
    aux = (
        '=IF($B{r}="","",'
        'IF(COUNTIF(Postos_Cod,$B{r})=0,"Sala não cadastrada | ","")&'
        'IF(AND(COUNTIF(Postos_Cod,$B{r})>0,IFERROR(INDEX(Postos_Tipo,MATCH($B{r},Postos_Cod,0)),"")<>"Sala cirúrgica"),'
        '"Posto não é sala cirúrgica | ","")&'
        'IF(COUNTIF(Esp_Nome,$E{r})=0,"Especialidade não cadastrada | ","")&'
        'IF(COUNTIF(Lista_StatusCir,$H{r})=0,"Status inválido | ","")&'
        'IF(OR(NOT(ISNUMBER($C{r})),NOT(ISNUMBER($D{r}))),"Horário inválido | ","")&'
        'IFERROR(IF(AND(ISNUMBER($C{r}),ISNUMBER($D{r}),MOD($D{r}-$C{r},1)*1440<=0),"Duração nula ou negativa | ",""),"")&'
        'IF(AND($J{r}>0,OR($P{r}>=Turno_Min,$Q{r}>Turno_Min)),"Fora da janela do plantão | ","")&'
        'IF(AND($J{r}>0,SUMPRODUCT((Mapa_Sala=$B{r})*(Mapa_Data=$A{r})*(Mapa_MinOcup>0)*'
        '(Mapa_RelIni<$Q{r})*(Mapa_RelFim>$P{r}))>1),"Sobreposição de horário na sala | ","")&'
        'IFERROR(IF(AND(ISNUMBER($I{r}),$I{r}>0,COUNTIF(Esp_Nome,$E{r})>0,'
        '$I{r}>3*INDEX(Esp_Dur,MATCH($E{r},Esp_Nome,0))),"Duração atípica (>3x a média) | ",""),""))'
    ).format(r=r)
    ws_map.cell(row=r, column=15, value=aux).font = F_OUT
    al = ws_map.cell(row=r, column=14, value=(
        '=IF($B{r}="","",IF($O{r}="","OK",LEFT($O{r},LEN($O{r})-3)))').format(r=r))
    al.border = BORD; al.alignment = LFT; al.font = F_OUT
ws_map.freeze_panes = "C2"; ws_map.auto_filter.ref = "A1:N%d" % MP_R2
for nm, col in (("Mapa_Data", "A"), ("Mapa_Sala", "B"), ("Mapa_Esp", "E"), ("Mapa_Status", "H"),
                ("Mapa_Dur", "I"), ("Mapa_MinOcup", "J"), ("Mapa_Alerta", "N"),
                ("Mapa_RelIni", "P"), ("Mapa_RelFim", "Q"), ("Mapa_Chave", "R"), ("Mapa_Row", "S"),
                ("Mapa_MinPlantao", "T")):
    dn(nm, R(S_MAP, "$%s$%d:$%s$%d" % (col, MP_R1, col, MP_R2)))

# ---------------------------------------------------------------- CALC (oculta)
head(ws_cal, 1, ["Posto", "Tipo", "Especialidade de referência", "Min. agendados"] + [""] * N_ESP +
     ["Total", "Min. do plantão", "Ocupação"], height=40)
for i in range(N_ESP):
    c = ws_cal.cell(row=1, column=CC1 + i, value='=IF(%s="","",%s)' % (
        R(S_CFG, "$B$%d" % (ESP_R1 + i)), R(S_CFG, "$B$%d" % (ESP_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = ROT
for i in range(N_POS):
    r, pr = MIX_R1 + i, POS_R1 + i
    vals = {
        1: '=IF(%s="","",%s)' % (R(S_CFG, "$A$%d" % pr), R(S_CFG, "$A$%d" % pr)),
        2: '=IF($A{r}="","",IFERROR(INDEX(Postos_Tipo,MATCH($A{r},Postos_Cod,0)),""))',
        3: '=IF($A{r}="","",IFERROR(INDEX(Postos_Esp,MATCH($A{r},Postos_Cod,0)),""))',
        4: ('=IF(OR($A{r}="",$B{r}<>"Sala cirúrgica"),0,'
            'SUMIFS(Mapa_MinPlantao,Mapa_Sala,$A{r},Mapa_Data,Data_Mapa))'),
    }
    for col, f in vals.items():
        ws_cal.cell(row=r, column=col, value=f.format(r=r) if "{r}" in f else f)
    for j in range(N_ESP):
        col = get_column_letter(CC1 + j)
        ws_cal.cell(row=r, column=CC1 + j, value=(
            '=IF($A{r}="",0,IF(OR($B{r}<>"Sala cirúrgica",$D{r}=0),'
            'IF(AND({c}$1<>"",{c}$1=$C{r}),Turno_Min,0),'
            'IF({c}$1="",0,SUMIFS(Mapa_MinPlantao,Mapa_Sala,$A{r},Mapa_Data,Data_Mapa,Mapa_Esp,{c}$1))))'
        ).format(r=r, c=col))
    ws_cal.cell(row=r, column=TOT_C, value='=IF($A{r}="",0,SUM({a}{r}:{b}{r}))'.format(r=r, a=CL1, b=CL2))
    ws_cal.cell(row=r, column=DISP_C, value='=IF($A{r}="",0,Turno_Min)'.format(r=r))
    ws_cal.cell(row=r, column=OCUP_C, value=(
        '=IF(OR($A{r}="",$B{r}<>"Sala cirúrgica"),"",$D{r}/Turno_Min)').format(r=r))
dn("Mix_Esp", R(S_CAL, "$%s$1:$%s$1" % (CL1, CL2)))

# posição do bloco de escala dentro do Painel (usada pelas fórmulas de apoio)
PAI_R1 = 10
PAI_R2 = PAI_R1 + N_POS - 1
dn("Pai_Tec1", R(S_PAI, "$D$%d:$D$%d" % (PAI_R1, PAI_R2)))
dn("Pai_Tec2", R(S_PAI, "$E$%d:$E$%d" % (PAI_R1, PAI_R2)))

# --- cobertura: quantos dos dois técnicos escalados marcam X em cada especialidade do dia
head(ws_cal, COB_R1 - 1, ["Posto", "", "", ""] + [""] * N_ESP +
     ["Nº especialidades do dia", "Descobertas", "Cobertas por 1 só", "Especialidades do dia",
      "Especialidades descobertas"], height=40)
for i in range(N_ESP):
    c = ws_cal.cell(row=COB_R1 - 1, column=CC1 + i, value='={c}$1'.format(c=get_column_letter(CC1 + i)))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = ROT
for i in range(N_POS):
    r, mr, pr = COB_R1 + i, MIX_R1 + i, PAI_R1 + i
    ws_cal.cell(row=r, column=1, value='=IF($A{mr}="","",$A{mr})'.format(mr=mr))
    t1, t2 = R(S_PAI, "$D%d" % pr), R(S_PAI, "$E%d" % pr)
    for j in range(N_ESP):
        col = get_column_letter(CC1 + j)
        ws_cal.cell(row=r, column=CC1 + j, value=(
            '=IF({c}{mr}=0,"",'
            'IF({t1}="",0,--(IFERROR(INDEX(Equipe_X,MATCH({t1},Equipe_Nome,0),{j}),"")="X"))+'
            'IF({t2}="",0,--(IFERROR(INDEX(Equipe_X,MATCH({t2},Equipe_Nome,0),{j}),"")="X")))'
        ).format(c=col, mr=mr, t1=t1, t2=t2, j=j + 1))
    ws_cal.cell(row=r, column=TOT_C, value='=COUNTIF({a}{mr}:{b}{mr},">0")'.format(a=CL1, b=CL2, mr=mr))
    ws_cal.cell(row=r, column=DISP_C, value='=COUNTIF({a}{r}:{b}{r},0)'.format(a=CL1, b=CL2, r=r))
    ws_cal.cell(row=r, column=OCUP_C, value='=COUNTIF({a}{r}:{b}{r},1)'.format(a=CL1, b=CL2, r=r))
    txt_dia = "&".join('IF(%s%d>0,%s$1&" · ","")' % (get_column_letter(CC1 + j), mr,
                                                     get_column_letter(CC1 + j)) for j in range(N_ESP))
    txt_desc = "&".join('IF(AND(%s%d>0,%s%d=0),%s$1&" · ","")' % (
        get_column_letter(CC1 + j), mr, get_column_letter(CC1 + j), r,
        get_column_letter(CC1 + j)) for j in range(N_ESP))
    ws_cal.cell(row=r, column=CC2 + 4, value='=IF($A{r}="","",{t})'.format(r=r, t=txt_dia))
    ws_cal.cell(row=r, column=CC2 + 5, value='=IF($A{r}="","",{t})'.format(r=r, t=txt_desc))

# --- sugestão: pontuação de cada técnico livre para cada posto
head(ws_cal, SUG_R1 - 1, ["Técnico", "Situação", "", ""] + ["P%d" % (i + 1) for i in range(N_POS)], height=20)
for i in range(N_EQ):
    r = SUG_R1 + i
    ws_cal.cell(row=r, column=1, value='=IF(%s="","",%s)' % (
        R(S_EQP, "$B$%d" % (EQ_R1 + i)), R(S_EQP, "$B$%d" % (EQ_R1 + i))))
    ws_cal.cell(row=r, column=2, value='=IF($A{r}="","",IFERROR(INDEX(Equipe_Situacao,MATCH($A{r},Equipe_Nome,0)),""))'.format(r=r))
    for j in range(N_POS):
        mr = MIX_R1 + j
        ws_cal.cell(row=r, column=CC1 + j, value=(
            '=IF(OR($A{r}="",$B{r}<>"Disponível",'
            'COUNTIF(Pai_Tec1,$A{r})+COUNTIF(Pai_Tec2,$A{r})>0),"",'
            'SUMPRODUCT(({a}{mr}:{b}{mr}>0)*(INDEX(Equipe_X,MATCH($A{r},Equipe_Nome,0),0)="X"))'
            '+ROW()*0.0001)').format(r=r, mr=mr, a=CL1, b=CL2))
dn("Sug_Nome", R(S_CAL, "$A$%d:$A$%d" % (SUG_R1, SUG_R2)))

# --- fila de ações do Painel: cada linha é uma pendência com a sua gravidade
# A gravidade ordena a fila; a fração desempata (prioridade do ambiente), para que o
# LARGE/MATCH do Painel nunca pegue duas linhas com a mesma nota.
head(ws_cal, ACO_R1 - 1, ["Gravidade", "O que fazer"], height=20)
M = R(S_PAI, "$%s%d")          # atalho para as colunas do Mapa do Dia
GLOBAIS = [
    ('=IF(COUNTIF(Equipe_X,"X")=0,1000,0)',
     '"Marque o X de cada técnica na aba Equipe — sem isso a planilha não avalia as duplas"'),
    ('=IF(COUNTIFS(Mapa_Data,Data_Mapa,Mapa_Sala,"<>")=0,990,0)',
     '"Nenhuma cirurgia lançada nesta data — importe a agenda do dia"'),
    ('=IF(SUMPRODUCT((Cir_Nome<>"")*(Cir_Esp=""))>0,980,0)',
     '"Cadastre a especialidade de "&SUMPRODUCT((Cir_Nome<>"")*(Cir_Esp=""))&'
     '" cirurgião(ões) na aba Configuração, seção 8"'),
    ('=IF(%s>0,970,0)' % R(S_DASH, "$G$9"),
     '"Falta"&IF(%s=1,"","m")&" "&%s&" técnico"&IF(%s=1,"","s")&'
     '" para cobrir todas as vagas de hoje — veja o Mapa do Dia"'
     % (R(S_DASH, "$G$9"), R(S_DASH, "$G$9"), R(S_DASH, "$G$9"))),
]
for i, (nota, texto) in enumerate(GLOBAIS):
    r = ACO_R1 + i
    ws_cal.cell(row=r, column=1, value=nota)
    ws_cal.cell(row=r, column=2, value='=IF($A{r}=0,"",{t})'.format(r=r, t=texto))
for i in range(N_POS):
    r, pr, mr = ACO_R1 + N_GLOB + i, PAI_R1 + i, MIX_R1 + i
    sit, nome, alerta = M % ("F", pr), M % ("A", pr), M % ("G", pr)
    cir = M % ("H", pr)
    ws_cal.cell(row=r, column=1, value=(
        '=IF({n}="",0,IF({s}="SEM EQUIPE",IF(N({c})>0,900,850),'
        'IF({s}="FALTA HABILIDADE",800,IF({s}="GENTE DEMAIS",700,IF({s}="INCOMPLETO",650,'
        'IF({s}="EXTRA",600,IF({s}="ATENÇÃO",400,'
        'IF(AND({s}="SEM AVALIAÇÃO",COUNTIF(Equipe_X,"X")>0),300,0))))))))'
        '+IF({n}="",0,(20-IFERROR(INDEX(Postos_Prior,MATCH({cod},Postos_Cod,0)),20))/100)'
    ).format(n=nome, s=sit, c=cir, cod=M % ("N", pr)))
    ws_cal.cell(row=r, column=2, value=(
        '=IF(OR({n}="",$A{r}<1),"",{n}&" · "&{a})').format(r=r, n=nome, a=alerta))
dn("Aco_Nota", R(S_CAL, "$A$%d:$A$%d" % (ACO_R1, ACO_R2)))
dn("Aco_Texto", R(S_CAL, "$B$%d:$B$%d" % (ACO_R1, ACO_R2)))

# --- rankings do Painel: onde encaixar e onde o dia atrasa
head(ws_cal, RNK_R1 - 1, ["Ambiente", "Cabe até", "chave", "Atraso", "chave"], height=20)
for i in range(N_POS):
    r, pr = RNK_R1 + i, PAI_R1 + i
    nome, cabe, atraso = M % ("A", pr), M % ("K", pr), M % ("L", pr)
    ws_cal.cell(row=r, column=1, value='=IF({n}="","",{n})'.format(n=nome))
    ws_cal.cell(row=r, column=2, value='=IF(OR({n}="",NOT(ISNUMBER({c}))),"",{c})'.format(n=nome, c=cabe))
    ws_cal.cell(row=r, column=3, value=(
        '=IF(OR($B{r}="",IFERROR(INDEX(Postos_Encaixe,MATCH({cod},Postos_Cod,0)),"")<>"Sim"),0,'
        '$B{r}+(1000-ROW())*0.0001)').format(r=r, cod=M % ("N", PAI_R1 + i)))
    ws_cal.cell(row=r, column=4, value='=IF(OR({n}="",NOT(ISNUMBER({a}))),"",{a})'.format(n=nome, a=atraso))
    ws_cal.cell(row=r, column=5, value=(
        '=IF(OR($D{r}="",$D{r}<=0),0,$D{r}+(1000-ROW())*0.0001)').format(r=r))
dn("Rnk_Nome", R(S_CAL, "$A$%d:$A$%d" % (RNK_R1, RNK_R2)))
dn("Rnk_Cabe", R(S_CAL, "$C$%d:$C$%d" % (RNK_R1, RNK_R2)))
dn("Rnk_Atraso", R(S_CAL, "$E$%d:$E$%d" % (RNK_R1, RNK_R2)))

# ---------------------------------------------------------------- CALC_SALAS (oculta): janelas livres
head(ws_sal, 1, ["Sala", "Janela", "iniRel", "fimRel", "Duração (min)", "Cabe até (min)",
                 "Atraso acumulado (min)"], height=20)
SAL_R1 = 2
for i in range(N_POS):
    mr = MIX_R1 + i
    for k in range(JOGO_K):
        r = SAL_R1 + i * JOGO_K + k
        ws_sal.cell(row=r, column=1, value=(
            '=IF(OR({a}="",{b}<>"Sala cirúrgica"),"",{a})').format(
            a=R(S_CAL, "$A%d" % mr), b=R(S_CAL, "$B%d" % mr)))
        ws_sal.cell(row=r, column=2, value=k)
        if k == 0:
            f = '=IF($A{r}="","",0)'.format(r=r)
        else:
            f = ('=IF(OR($A{r}="",ISERROR(MATCH($A{r}&"#"&Data_Mapa&"#{k}",Mapa_Chave,0))),"",'
                 'INDEX(Mapa_RelFim,MATCH($A{r}&"#"&Data_Mapa&"#{k}",Mapa_Chave,0))+Limpeza_Min)').format(r=r, k=k)
        ws_sal.cell(row=r, column=3, value=f)
        ws_sal.cell(row=r, column=4, value=(
            '=IF($C{r}="","",IFERROR(INDEX(Mapa_RelIni,MATCH($A{r}&"#"&Data_Mapa&"#{k1}",Mapa_Chave,0)),Turno_Min))'
        ).format(r=r, k1=k + 1))
        ws_sal.cell(row=r, column=5, value='=IF($C{r}="","",MAX(0,$D{r}-$C{r}))'.format(r=r))
        ws_sal.cell(row=r, column=6, value='=IF($E{r}="","",MAX(0,$E{r}-Limpeza_Min))'.format(r=r))
        # atraso represado: a limpeza que não coube na folga empurra a cirurgia seguinte, e o
        # atraso só some quando aparece uma folga grande o bastante para absorvê-lo. Só conta
        # quando a cirurgia seguinte começa dentro do plantão — depois disso o atraso é do
        # outro turno, não deste.
        atraso = ('=IF($C{r}="","",0)'.format(r=r) if k == 0 else
                  ('=IF($C{r}="","",IF($D{r}>=Turno_Min,N($G{p}),'
                   'MAX(0,N($G{p})+$C{r}-$D{r})))').format(r=r, p=r - 1))
        ws_sal.cell(row=r, column=7, value=atraso)
SAL_R2 = SAL_R1 + N_POS * JOGO_K - 1

# --- necessários HOJE por posto (considera dia da semana, feriado e status) — coluna AD do Calc
NEC_C = CC2 + 6
NEC_L = get_column_letter(NEC_C)
ws_cal.cell(row=1, column=NEC_C, value="Necessários hoje").font = F_HEAD
ws_cal.cell(row=1, column=NEC_C).fill = FILL_HEAD
for i in range(N_POS):
    r, pr = MIX_R1 + i, POS_R1 + i
    ws_cal.cell(row=r, column=NEC_C, value=(
        '=IF($A{r}="",0,IF(OR(IFERROR(INDEX(Postos_Status,MATCH($A{r},Postos_Cod,0)),"")<>"Ativo",'
        'AND(IFERROR(INDEX(Postos_Func,MATCH($A{r},Postos_Cod,0)),"")="Seg a Sex",'
        'OR(WEEKDAY(Data_Mapa,2)>5,COUNTIF(Feriados,Data_Mapa)>0)),'
        'AND(IFERROR(INDEX(Postos_Func,MATCH($A{r},Postos_Cod,0)),"")="Seg a Sáb",'
        'OR(WEEKDAY(Data_Mapa,2)>6,COUNTIF(Feriados,Data_Mapa)>0))),0,'
        'IFERROR(INDEX(Postos_Nec,MATCH($A{r},Postos_Cod,0)),0)))').format(r=r))

# ================================================================ PAINEL — MAPA DO DIA
ws_pai["A1"] = "CENTRO CIRÚRGICO — MAPA DO DIA"; ws_pai["A1"].font = F_TIT
ws_pai["A2"] = ("Esta aba já vem preenchida: cada ambiente com a sua dupla, as especialidades que "
                "passam ali e o tempo em que a sala fica vaga. Para trocar alguém, escolha outro "
                "nome nas células azuis.")
ws_pai["A2"].font = F_NOTA
widths(ws_pai, {"A": 26, "B": 10, "C": 34, "D": 26, "E": 26, "F": 17, "G": 40, "H": 10,
                "I": 11, "J": 24, "K": 11, "L": 12, "M": 30, "N": 8, "O": 8})
for c_ in ("N", "O"):
    ws_pai.column_dimensions[c_].hidden = True

sec(ws_pai, 4, "1. O DIA")
head(ws_pai, 5, ["DATA", "Dia", "No quadro", "Ausentes", "DISPONÍVEIS", "Vagas do dia",
                 "DÉFICIT", "Postos sem equipe", "Maior atraso previsto (min)", "", "", ""],
     height=34)
kpis = {
    1: None,
    2: ('=IF($A$6="","",CHOOSE(WEEKDAY($A$6),"domingo","segunda","terça","quarta","quinta","sexta","sábado")'
        '&IF(COUNTIF(Feriados,$A$6)>0," · feriado",""))'),
    3: '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Status="Ativo"))',
    4: '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Status="Ativo")*(Equipe_Situacao<>"Disponível"))',
    5: '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Situacao="Disponível"))',
    6: '=SUM(%s)' % R(S_CAL, "$%s$%d:$%s$%d" % (NEC_L, MIX_R1, NEC_L, MIX_R2)),
    7: '=MAX(0,$F$6-$E$6)',
    8: '=COUNTIF($F$%d:$F$%d,"SEM EQUIPE")' % (PAI_R1, PAI_R2),
    9: '=MAX(0,$L$%d:$L$%d)' % (PAI_R1, PAI_R2),
}
for col, f in kpis.items():
    c = ws_pai.cell(row=6, column=col)
    c.border = BORD; c.alignment = CTR
    c.font = Font(name="Calibri", size=12, bold=True, color=AZ)
    if col == 1:
        c.value = DIA; c.number_format = "DD/MM/YYYY"; c.fill = FILL_PREM
        c.font = Font(name="Calibri", size=12, bold=True, color="0070C0")
    else:
        c.value = f; c.fill = FILL_IN
        c.number_format = "0" if col >= 3 else "General"
ws_pai.row_dimensions[6].height = 26

sec(ws_pai, 8, "2. O MAPA — quem fica em cada lugar hoje")
head(ws_pai, 9, ["Ambiente", "Técnicos", "Especialidades do dia", "TÉCNICO 1", "TÉCNICO 2",
                 "Situação", "Alertas", "Cirurgias", "Ocupação", "Sala vaga (maior janela)",
                 "Cabe até (min)", "Atraso previsto (min)", "Quem está livre e cobre mais", "", ""],
     height=38)
for i in range(N_POS):
    r, mr, cr = PAI_R1 + i, MIX_R1 + i, COB_R1 + i
    j1, j2 = SAL_R1 + i * JOGO_K, SAL_R1 + i * JOGO_K + JOGO_K - 1
    bC = R(S_SAL, "$C$%d:$C$%d" % (j1, j2)); bD = R(S_SAL, "$D$%d:$D$%d" % (j1, j2))
    bE = R(S_SAL, "$E$%d:$E$%d" % (j1, j2)); bF = R(S_SAL, "$F$%d:$F$%d" % (j1, j2))
    bG = R(S_SAL, "$G$%d:$G$%d" % (j1, j2))
    sug_col = get_column_letter(CC1 + i)
    sug_rng = R(S_CAL, "%s$%d:%s$%d" % (sug_col, SUG_R1, sug_col, SUG_R2))
    nesp = 'IFERROR(INDEX(Equipe_NEsp,MATCH(%s,Equipe_Nome,0)),0)'
    janela1 = ('IFERROR(TEXT(MOD(Turno_Ini+INDEX({c},MATCH(LARGE({e},1),{e},0))/1440,1),"HH:MM")&" → "&'
               'TEXT(MOD(Turno_Ini+INDEX({d},MATCH(LARGE({e},1),{e},0))/1440,1),"HH:MM")&'
               '" ("&LARGE({e},1)&" min)","—")').format(c=bC, d=bD, e=bE)
    f = {
        "N": '=IF(%s="","",%s)' % (R(S_CAL, "$A%d" % mr), R(S_CAL, "$A%d" % mr)),
        "A": '=IF($N{r}="","",IFERROR(INDEX(Postos_Nome,MATCH($N{r},Postos_Cod,0)),$N{r}))',
        "B": '=IF($N{r}="","",{nec})'.replace("{nec}", R(S_CAL, "$%s%d" % (NEC_L, mr))),
        "C": '=IF(OR($N{r}="",{x}=""),"",LEFT({x},LEN({x})-3))'.replace(
            "{x}", R(S_CAL, "$%s%d" % (get_column_letter(CC2 + 4), cr))),
        "F": ('=IF($N{r}="","",IF($B{r}=0,IF(AND($D{r}="",$E{r}=""),"NÃO OPERA","EXTRA"),'
              'IF(AND($D{r}="",$E{r}=""),"SEM EQUIPE",'
              'IF((--($D{r}<>"")+--($E{r}<>""))<$B{r},"INCOMPLETO",'
              'IF((--($D{r}<>"")+--($E{r}<>""))>$B{r},"GENTE DEMAIS",'
              'IF(OR(AND($D{r}<>"",{n1}=0),AND($E{r}<>"",{n2}=0)),"SEM AVALIAÇÃO",'
              'IF({desc}>0,"FALTA HABILIDADE",IF(AND($B{r}>=2,{um}>0),"ATENÇÃO","OK"))))))))'
              ).replace("{n1}", nesp % "$D{r}").replace("{n2}", nesp % "$E{r}")
                .replace("{desc}", R(S_CAL, "$%s%d" % (DISP_L, cr)))
                .replace("{um}", R(S_CAL, "$%s%d" % (OCUP_L, cr))),
        "O": ('=IF($N{r}="","",'
              'IF(AND($F{r}="SEM EQUIPE",N($H{r})>0),"Sem equipe — "&$H{r}&" cirurgia(s) a remanejar | ","")&'
              'IF($F{r}="SEM EQUIPE",IF(N($H{r})>0,"","Ambiente sem equipe | "),"")&'
              'IF($F{r}="INCOMPLETO","Falta "&($B{r}-(--($D{r}<>"")+--($E{r}<>"")))&IF($B{r}-(--($D{r}<>"")+--($E{r}<>""))=1," técnico"," técnicos")&" neste ambiente | ","")&'
              'IF($F{r}="GENTE DEMAIS","Este ambiente é de "&$B{r}&IF($B{r}=1," técnico só"," técnicos")&": tire o excedente | ","")&'
              'IF($F{r}="EXTRA","Técnico escalado em ambiente que não opera hoje | ","")&'
              'IF(AND($F{r}="NÃO OPERA",N($H{r})>0),"Ambiente não opera hoje e tem cirurgia | ","")&'
              'IF($F{r}="SEM AVALIAÇÃO","Técnico sem habilidade marcada na aba Equipe | ","")&'
              'IF($F{r}="ATENÇÃO","Especialidade coberta por uma técnica só — se ela sair, a sala para | ","")&'
              'IF(AND($F{r}<>"SEM AVALIAÇÃO",{dtxt}<>""),"Ninguém cobre: "&LEFT({dtxt},LEN({dtxt})-3)&" | ","")&'
              'IF(AND($D{r}<>"",IFERROR(INDEX(Equipe_Situacao,MATCH($D{r},Equipe_Nome,0)),"?")<>"Disponível"),'
              '"Técnico 1 indisponível | ","")&'
              'IF(AND($E{r}<>"",IFERROR(INDEX(Equipe_Situacao,MATCH($E{r},Equipe_Nome,0)),"?")<>"Disponível"),'
              '"Técnico 2 indisponível | ","")&'
              'IF(OR(AND($D{r}<>"",COUNTIF(Pai_Tec1,$D{r})+COUNTIF(Pai_Tec2,$D{r})>1),'
              'AND($E{r}<>"",COUNTIF(Pai_Tec1,$E{r})+COUNTIF(Pai_Tec2,$E{r})>1)),'
              '"Técnico escalado em dois ambientes | ","")&'
              'IF(AND($I{r}<>"",$I{r}>1),"Ocupação acima do plantão | ",""))'
              ).replace("{dtxt}", R(S_CAL, "$%s%d" % (get_column_letter(CC2 + 5), cr))),
        "G": '=IF($N{r}="","",IF($O{r}="","OK",LEFT($O{r},LEN($O{r})-3)))',
        "H": ('=IF(OR($N{r}="",{t}<>"Sala cirúrgica"),"",'
              'COUNTIFS(Mapa_Sala,$N{r},Mapa_Data,Data_Mapa,Mapa_MinOcup,">0"))'
              ).replace("{t}", R(S_CAL, "$B%d" % mr)),
        "I": '=IF(OR($N{r}="",{t}<>"Sala cirúrgica"),"",{o})'.replace(
            "{t}", R(S_CAL, "$B%d" % mr)).replace("{o}", R(S_CAL, "$%s%d" % (OCUP_L, mr))),
        "J": '=IF($N{r}="","",IF(MAX(<E>)=0,"—",<J1>))'.replace("<E>", bE).replace("<J1>", janela1),
        "K": '=IF(OR($N{r}="",MAX(<E>)=0),"",MAX(<F>))'.replace("<E>", bE).replace("<F>", bF),
        "L": '=IF(OR($N{r}="",{t}<>"Sala cirúrgica"),"",MAX(<G>))'.replace("<G>", bG).replace(
            "{t}", R(S_CAL, "$B%d" % mr)),
        "M": ('=IF($N{r}="","",IFERROR(INDEX(Sug_Nome,MATCH(LARGE({s},1),{s},0)),"—")'
              '&IFERROR(" · "&INDEX(Sug_Nome,MATCH(LARGE({s},2),{s},0)),"")'
              '&IFERROR(" · "&INDEX(Sug_Nome,MATCH(LARGE({s},3),{s},0)),""))').replace("{s}", sug_rng),
    }
    for col, formula in f.items():
        cel = ws_pai[col + str(r)]
        cel.value = formula.format(r=r); cel.border = BORD; cel.font = F_OUT; cel.alignment = CTR
    for col in ("A", "C", "G", "J", "M"):
        ws_pai[col + str(r)].alignment = LFTW
    ws_pai["I%d" % r].number_format = "0.0%"
    for col in ("B", "H", "K", "L"):
        ws_pai[col + str(r)].number_format = "0"
    for col in ("D", "E"):
        cel = ws_pai[col + str(r)]
        cel.font = F_IN; cel.fill = FILL_IN; cel.alignment = LFT
        if i < len(POSTOS):
            escalados = ALOC.get(POSTOS[i][0], [])
            k = 0 if col == "D" else 1
            if k < len(escalados):
                cel.value = escalados[k]
    ws_pai.row_dimensions[r].height = 30

# --- bloco 3: equipe hoje
EQH_R1 = PAI_R2 + 4
sec(ws_pai, EQH_R1 - 2, "3. EQUIPE HOJE — quem está disponível e onde está")
head(ws_pai, EQH_R1 - 1, ["Técnico", "Situação", "Ausente até", "Escalado em",
                          "Nº de especialidades", "", "", "", "", "", "", ""], height=24)
for i in range(N_EQ):
    r, er = EQH_R1 + i, EQ_R1 + i
    f = {
        "A": '=IF(%s="","",%s)' % (R(S_EQP, "$B$%d" % er), R(S_EQP, "$B$%d" % er)),
        "B": '=IF($A{r}="","",%s)' % R(S_EQP, "$E$%d" % er),
        "C": '=IF($A{r}="","",%s)' % R(S_EQP, "$F$%d" % er),
        "D": ('=IF($A{r}="","",IFERROR(INDEX($A$%d:$A$%d,MATCH($A{r},$D$%d:$D$%d,0)),'
              'IFERROR(INDEX($A$%d:$A$%d,MATCH($A{r},$E$%d:$E$%d,0)),"—")))'
              % (PAI_R1, PAI_R2, PAI_R1, PAI_R2, PAI_R1, PAI_R2, PAI_R1, PAI_R2)),
        "E": '=IF($A{r}="","",%s)' % R(S_EQP, "$%s$%d" % (get_column_letter(XC2 + 1), er)),
    }
    for col, formula in f.items():
        cel = ws_pai[col + str(r)]
        cel.value = formula.format(r=r); cel.border = BORD; cel.font = F_OUT; cel.alignment = CTR
    ws_pai["A%d" % r].alignment = LFT
    ws_pai["C%d" % r].number_format = "DD/MM"
    ws_pai["E%d" % r].number_format = "0"

# --- bloco 4: verificações
CHK_R1 = EQH_R1 + N_EQ + 2
sec(ws_pai, CHK_R1 - 2, "4. VERIFICAÇÕES")
head(ws_pai, CHK_R1 - 1, ["Verificação", "Resultado", "", "", "", "", "", "", "", "", "", ""],
     height=20)
CHECKS = [
    ("Habilidades marcadas na aba Equipe",
     '=IF(COUNTIF(Equipe_X,"X")=0,"PENDENTE: marque o X de cada técnico na aba Equipe","OK")'),
    ("Postos sem equipe", '=COUNTIF($F$%d:$F$%d,"SEM EQUIPE")' % (PAI_R1, PAI_R2)),
    ("Postos com equipe incompleta", '=COUNTIF($F$%d:$F$%d,"INCOMPLETO")' % (PAI_R1, PAI_R2)),
    ("Postos com especialidade sem ninguém que faça",
     '=COUNTIF($F$%d:$F$%d,"FALTA HABILIDADE")' % (PAI_R1, PAI_R2)),
    ("Ambientes com técnico a mais", '=COUNTIF($F$%d:$F$%d,"GENTE DEMAIS")' % (PAI_R1, PAI_R2)),
    ("Técnicos escalados em mais de um posto",
     '=SUMPRODUCT((Pai_Tec1<>"")*(COUNTIF(Pai_Tec1,Pai_Tec1)+COUNTIF(Pai_Tec2,Pai_Tec1)>1))'),
    ("Cirurgias com alerta no mapa", '=SUMPRODUCT((Mapa_Alerta<>"OK")*(Mapa_Alerta<>""))'),
    ("Ausências com técnico fora do cadastro",
     '=SUMPRODUCT((Aus_Tec<>"")*(COUNTIF(Equipe_Nome,Aus_Tec)=0))'),
    ("Ausências com data fim anterior ao início", '=SUMPRODUCT((Aus_Tec<>"")*(Aus_Fim<Aus_Ini))'),
    ("Nomes repetidos no cadastro da equipe",
     '=IF(SUMPRODUCT((Equipe_Nome<>"")*1)-SUMPRODUCT((Equipe_Nome<>"")/COUNTIF(Equipe_Nome,Equipe_Nome&""))'
     '>0.0001,"ERRO: há nomes repetidos","OK")'),
    ("Postos / especialidades / técnicos no quadro",
     '=COUNTA(Postos_Cod)&" / "&COUNTA(Esp_Nome)&" / "&COUNTA(Equipe_Nome)'),
]
for i, (lbl, f) in enumerate(CHECKS):
    r = CHK_R1 + i
    c1 = ws_pai.cell(row=r, column=1, value=lbl)
    c1.border = BORD; c1.alignment = LFT; c1.font = F_OUT
    c2 = ws_pai.cell(row=r, column=2, value=f)
    c2.border = BORD; c2.font = F_OUT
    c2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
CHK_R2 = CHK_R1 + len(CHECKS) - 1

# --- rodapé: como usar
GUIA_R = CHK_R2 + 3
sec(ws_pai, GUIA_R - 1, "COMO USAR")
GUIA = [
    ("O mapa já vem pronto", "A importação da agenda distribui os técnicos pelos ambientes: "
     "quem está disponível no dia, respeitando o X de habilidade e a prioridade de cada posto. "
     "A dupla fica o turno inteiro no mesmo lugar."),
    ("Para trocar alguém", "Escolha outro nome nas células azuis (TÉCNICO 1 / TÉCNICO 2). "
     "A coluna Situação e a coluna Alertas reagem na hora; a última coluna mostra quem está "
     "livre e cobre mais aquele ambiente."),
    ("Nem todo lugar é dupla", "A coluna Técnicos diz quantos o ambiente pede hoje. Onde é uma "
     "pessoa só — box de preparo, sala de recém-nascido — a coluna TÉCNICO 2 aparece cinza e "
     "fica vazia; se alguém for posto ali, a Situação avisa GENTE DEMAIS."),
    ("Jogo de sala", "Sala vaga mostra o maior intervalo livre da sala, com horário, e Minutos "
     "livres diz o tamanho dele. Como a agenda do hospital já reserva a limpeza dentro do horário "
     "de cada cirurgia, o intervalo inteiro é aproveitável para um encaixe."),
    ("Trocar a data", "Troque a DATA aqui em cima: ausentes, vagas necessárias e agenda do dia "
     "se ajustam sozinhos. A distribuição dos técnicos, não — para redistribuir, importe a "
     "agenda de novo."),
    ("Habilidade", "Na aba Equipe, marque X na especialidade que a técnica faz. Sem X marcado, "
     "a Situação fica SEM AVALIAÇÃO."),
    ("Folgas e férias", "Vão para a aba Ausencias, por período. O calendário ao lado mostra o "
     "período inteiro e quantos faltam em cada dia."),
    ("Situação", "OK = os dois cobrem tudo · ATENÇÃO = alguma especialidade coberta por um só · "
     "FALTA HABILIDADE = alguma especialidade sem ninguém · INCOMPLETO = falta técnico · "
     "SEM EQUIPE = ninguém escalado · NÃO OPERA = ambiente fechado nesse dia."),
]
for i, (a, b) in enumerate(GUIA):
    r = GUIA_R + i
    ca = ws_pai.cell(row=r, column=1, value=a)
    ca.font = Font(name="Calibri", size=10, bold=True); ca.alignment = Alignment(vertical="top")
    cb = ws_pai.cell(row=r, column=2, value=b)
    cb.font = F_NOTA; cb.alignment = Alignment(vertical="top", wrap_text=True)
    ws_pai.merge_cells(start_row=r, start_column=2, end_row=r, end_column=13)
    ws_pai.row_dimensions[r].height = 26 if len(b) < 150 else 40

ws_pai.freeze_panes = "B10"

# ================================================================ PAINEL (a primeira tela)
ws_dash["A1"] = "CENTRO CIRÚRGICO — PAINEL DO DIA"; ws_dash["A1"].font = F_TIT
ws_dash["A2"] = ("Bateu o olho, já sabe o que fazer. Esta aba só mostra — quem escala e quem troca "
                 "é a aba Mapa do Dia.")
ws_dash["A2"].font = F_NOTA
widths(ws_dash, {"A": 7, "B": 30, "C": 20, "D": 18, "E": 16, "F": 16, "G": 14, "H": 18, "I": 8})
ws_dash.column_dimensions["I"].hidden = True

ws_dash["A4"] = "DATA DO MAPA"; ws_dash["A4"].font = F_OUT
ws_dash.merge_cells("A4:B4")
c = ws_dash["C4"]; c.value = "=Data_Mapa"; c.number_format = "DD/MM/YYYY"
c.font = Font(name="Calibri", size=14, bold=True, color="0070C0"); c.alignment = LFT
ws_dash["D4"] = ('=IF(Data_Mapa="","",CHOOSE(WEEKDAY(Data_Mapa),"domingo","segunda","terça",'
                 '"quarta","quinta","sexta","sábado")&IF(COUNTIF(Feriados,Data_Mapa)>0," · feriado",""))')
ws_dash["D4"].font = F_OUT; ws_dash["D4"].alignment = LFT

# --- faixa de situação do dia
ws_dash.merge_cells("A6:H6")
b = ws_dash["A6"]
b.value = ('=IF(MAX(Aco_Nota)>=900,"AÇÃO NECESSÁRIA",IF(MAX(Aco_Nota)>=600,"ATENÇÃO",'
           'IF(MAX(Aco_Nota)>=1,"QUASE PRONTO","DIA FECHADO — nada pendente")))')
b.font = Font(name="Calibri", size=20, bold=True)
b.alignment = Alignment(horizontal="center", vertical="center")
b.border = BORD
ws_dash.row_dimensions[6].height = 42

# --- números do dia
NUM = [
    ("Cirurgias hoje", '=COUNTIFS(Mapa_Data,Data_Mapa,Mapa_MinOcup,">0")', "0"),
    ("Ambientes abertos", '=COUNTIF(%s,">0")' % R(S_PAI, "$B$%d:$B$%d" % (PAI_R1, PAI_R2)), "0"),
    ("Prontos", '=COUNTIF(%s,"OK")' % R(S_PAI, "$F$%d:$F$%d" % (PAI_R1, PAI_R2)), "0"),
    ("Com pendência", '=SUMPRODUCT(({f}<>"")*({f}<>"OK")*({f}<>"NÃO OPERA"))'.replace(
        "{f}", R(S_PAI, "$F$%d:$F$%d" % (PAI_R1, PAI_R2))), "0"),
    ("Disponíveis", '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Situacao="Disponível"))', "0"),
    ("Déficit", '=MAX(0,SUM(%s)-$F$9)' % R(S_CAL, "$%s$%d:$%s$%d" % (NEC_L, MIX_R1, NEC_L, MIX_R2)), "0"),
    ("Maior atraso (min)", '=MAX(0,%s)' % R(S_PAI, "$L$%d:$L$%d" % (PAI_R1, PAI_R2)), "0"),
]
head(ws_dash, 8, [""] + [n for n, _, _ in NUM], height=30)
for i, (_, f, nf) in enumerate(NUM):
    c = ws_dash.cell(row=9, column=2 + i, value=f)
    c.border = BORD; c.alignment = CTR; c.number_format = nf
    c.font = Font(name="Calibri", size=14, bold=True, color=AZ)
    c.fill = FILL_IN
ws_dash.row_dimensions[9].height = 30

# --- quadro das salas: gestão visual, um bloco por ambiente
QUA_R1 = 12
sec(ws_dash, QUA_R1 - 1, "AS SALAS AGORA — a cor é a situação de cada ambiente", 8)
for b in range(3):
    base = QUA_R1 + b * 6            # 4 linhas de conteúdo + 1 auxiliar oculta + 1 de respiro
    for k in range(4):
        i = b * 4 + k
        if i >= N_POS:
            break
        pr, c1 = PAI_R1 + i, 1 + k * 2
        nome, sit = R(S_PAI, "$A%d" % pr), R(S_PAI, "$F%d" % pr)
        esp, ocup = R(S_PAI, "$C%d" % pr), R(S_PAI, "$I%d" % pr)
        t1, t2 = R(S_PAI, "$D%d" % pr), R(S_PAI, "$E%d" % pr)
        pede = R(S_PAI, "$B%d" % pr)
        linhas = [
            '=IF({n}="","",{n})'.format(n=nome),
            ('=IF({n}="","",IF({e}="","sem cirurgia hoje",{e})'
             '&IF(ISNUMBER({o})," · "&TEXT({o},"0%")&" ocupada",""))').format(n=nome, e=esp, o=ocup),
            '=IF({n}="","",IF({t}="","(falta escalar)",{t}))'.format(n=nome, t=t1),
            '=IF({n}="","",IF({p}<2,"—",IF({t}="","(falta escalar)",{t})))'.format(n=nome, p=pede, t=t2),
        ]
        for j, f in enumerate(linhas):
            r = base + j
            ws_dash.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c1 + 1)
            c = ws_dash.cell(row=r, column=c1, value=f)
            c.border = BORD
            c.alignment = Alignment(horizontal="center", vertical="center")
            if j == 0:
                c.font = Font(name="Calibri", size=13, bold=True, color=AZ)
            elif j == 1:
                c.font = Font(name="Calibri", size=9, italic=True, color="595959")
            else:
                c.font = F_OUT
        # a situação vai para a linha auxiliar, nas DUAS colunas do bloco: a formatação
        # condicional lê a célula da mesma coluna, e assim cada bloco tem a sua cor
        for c in (c1, c1 + 1):
            ws_dash.cell(row=base + 4, column=c, value='=IF({n}="","",{s})'.format(n=nome, s=sit))
    ws_dash.row_dimensions[base].height = 24
    for j in (1, 2, 3):
        ws_dash.row_dimensions[base + j].height = 18
    ws_dash.row_dimensions[base + 4].hidden = True
    ws_dash.row_dimensions[base + 5].height = 8
QUA_R2 = QUA_R1 + 17

# --- o que fazer agora
ACO_P1 = QUA_R2 + 3
sec(ws_dash, ACO_P1 - 2, "O QUE FAZER AGORA — em ordem de urgência", 8)
for i in range(N_ACOES_VISIVEIS):
    r, n = ACO_P1 + i, i + 1
    cn = ws_dash.cell(row=r, column=1, value='=IF($B%d="","",%d)' % (r, n))
    cn.font = Font(name="Calibri", size=13, bold=True, color=AZ)
    cn.alignment = CTR; cn.border = BORD
    txt = ('IFERROR(IF(LARGE(Aco_Nota,{n})<1,"",'
           'INDEX(Aco_Texto,MATCH(LARGE(Aco_Nota,{n}),Aco_Nota,0))),"")').format(n=n)
    valor = ('=IF(MAX(Aco_Nota)<1,%s,%s)' % (
        '"Nada pendente — o dia está fechado."' if n == 1 else '""', txt))
    ct = ws_dash.cell(row=r, column=2, value=valor)
    ct.font = F_OUT; ct.alignment = LFTW; ct.border = BORD
    ws_dash.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    ws_dash.cell(row=r, column=9, value=(
        '=IFERROR(IF(LARGE(Aco_Nota,%d)<1,0,LARGE(Aco_Nota,%d)),0)' % (n, n))).font = F_OUT
    ws_dash.row_dimensions[r].height = 24
ACO_P2 = ACO_P1 + N_ACOES_VISIVEIS - 1

# --- onde encaixar
ENC_P1 = ACO_P2 + 3
sec(ws_dash, ENC_P1 - 2, "ONDE ENCAIXAR HOJE — maiores janelas nas salas que aceitam encaixe", 4)
head(ws_dash, ENC_P1 - 1, ["", "Ambiente", "Sala vaga", "Cabe até (min)"], height=22)
for i in range(3):
    r, n = ENC_P1 + i, i + 1
    pos = 'MATCH(LARGE(Rnk_Cabe,{n}),Rnk_Cabe,0)'.format(n=n)
    guarda = 'IFERROR(LARGE(Rnk_Cabe,{n}),0)<Janela_Min'.format(n=n)
    f = {
        1: '=IF(%s,"",%d)' % (guarda, n),
        2: '=IF(%s,"",INDEX(Rnk_Nome,%s))' % (guarda, pos),
        3: '=IF(%s,"",INDEX(%s,%s))' % (guarda, R(S_PAI, "$J$%d:$J$%d" % (PAI_R1, PAI_R2)), pos),
        4: '=IF(%s,"",INDEX(%s,%s))' % (guarda, R(S_PAI, "$K$%d:$K$%d" % (PAI_R1, PAI_R2)), pos),
    }
    for col, formula in f.items():
        c = ws_dash.cell(row=r, column=col, value=formula)
        c.border = BORD; c.font = F_OUT; c.alignment = CTR if col != 2 else LFT
    ws_dash.cell(row=r, column=4).number_format = "0"

# --- risco de atraso
ATR_P1 = ENC_P1 + 5
sec(ws_dash, ATR_P1 - 2, "RISCO DE ATRASO — salas onde a limpeza não cabe entre as cirurgias", 4)
head(ws_dash, ATR_P1 - 1, ["", "Ambiente", "Atraso previsto (min)", "Cirurgias"], height=22)
for i in range(3):
    r, n = ATR_P1 + i, i + 1
    pos = 'MATCH(LARGE(Rnk_Atraso,{n}),Rnk_Atraso,0)'.format(n=n)
    guarda = 'IFERROR(LARGE(Rnk_Atraso,{n}),0)<=0'.format(n=n)
    f = {
        1: '=IF(%s,"",%d)' % (guarda, n),
        2: '=IF(%s,"",INDEX(Rnk_Nome,%s))' % (guarda, pos),
        3: '=IF(%s,"",INDEX(%s,%s))' % (guarda, R(S_PAI, "$L$%d:$L$%d" % (PAI_R1, PAI_R2)), pos),
        4: '=IF(%s,"",INDEX(%s,%s))' % (guarda, R(S_PAI, "$H$%d:$H$%d" % (PAI_R1, PAI_R2)), pos),
    }
    for col, formula in f.items():
        c = ws_dash.cell(row=r, column=col, value=formula)
        c.border = BORD; c.font = F_OUT; c.alignment = CTR if col != 2 else LFT
    for col in (3, 4):
        ws_dash.cell(row=r, column=col).number_format = "0"
ws_dash.cell(row=ATR_P1 + 3, column=1,
             value="Sem atraso previsto quer dizer que a agenda deixou os 20 min de limpeza entre "
                   "as cirurgias.").font = F_NOTA
ws_dash.print_area = "A1:H%d" % (ATR_P1 + 3)
ws_dash.page_setup.orientation = "landscape"
ws_dash.page_setup.fitToWidth = 1; ws_dash.page_setup.fitToHeight = 1
ws_dash.sheet_properties.pageSetUpPr.fitToPage = True
ws_dash.sheet_properties.tabColor = AZ

# --- formatação condicional do Painel
_fv, _fvt = PatternFill("solid", fgColor=VERDE), Font(name="Calibri", size=20, bold=True, color=VERDE_T)
_fa, _fat = PatternFill("solid", fgColor=AMAR), Font(name="Calibri", size=20, bold=True, color=AMAR_T)
_fr, _frt = PatternFill("solid", fgColor=VERM), Font(name="Calibri", size=20, bold=True, color=VERM_T)
ws_dash.conditional_formatting.add("A6", CellIsRule(operator="equal", formula=['"AÇÃO NECESSÁRIA"'],
                                                    fill=_fr, font=_frt))
ws_dash.conditional_formatting.add("A6", CellIsRule(operator="equal", formula=['"ATENÇÃO"'],
                                                    fill=_fa, font=_fat))
ws_dash.conditional_formatting.add("A6", CellIsRule(operator="equal", formula=['"QUASE PRONTO"'],
                                                    fill=_fa, font=_fat))
ws_dash.conditional_formatting.add("A6", FormulaRule(formula=['LEFT($A$6,11)="DIA FECHADO"'],
                                                     fill=_fv, font=_fvt))
for _b in range(3):
    _base, _aux = QUA_R1 + _b * 6, QUA_R1 + _b * 6 + 4
    for _cond, _cor, _txt in (
            ('A${a}="OK"'.format(a=_aux), VERDE, VERDE_T),
            ('OR(A${a}="ATENÇÃO",A${a}="SEM AVALIAÇÃO",A${a}="INCOMPLETO")'.format(a=_aux), AMAR, AMAR_T),
            ('OR(A${a}="SEM EQUIPE",A${a}="FALTA HABILIDADE",A${a}="GENTE DEMAIS",A${a}="EXTRA")'.format(a=_aux),
             VERM, VERM_T),
            ('A${a}="NÃO OPERA"'.format(a=_aux), CINZA, "808080")):
        ws_dash.conditional_formatting.add(
            "A%d:H%d" % (_base, _base),
            FormulaRule(formula=[_cond], fill=PatternFill("solid", fgColor=_cor),
                        font=Font(name="Calibri", size=13, bold=True, color=_txt)))

_lr = Font(color=VERM_T, bold=True)
_la = Font(color=AMAR_T, bold=True)
ws_dash.conditional_formatting.add("B%d:B%d" % (ACO_P1, ACO_P2),
    FormulaRule(formula=['$I%d>=900' % ACO_P1], fill=PatternFill("solid", fgColor=VERM), font=_lr))
ws_dash.conditional_formatting.add("B%d:B%d" % (ACO_P1, ACO_P2),
    FormulaRule(formula=['AND($I%d>=600,$I%d<900)' % (ACO_P1, ACO_P1)],
                fill=PatternFill("solid", fgColor=AMAR), font=_la))
ws_dash.conditional_formatting.add("D9", CellIsRule(operator="greaterThan", formula=["0"],
    fill=PatternFill("solid", fgColor=VERDE), font=Font(name="Calibri", size=14, bold=True, color=VERDE_T)))
for cel, cor, fonte in (("E9", VERM, VERM_T), ("G9", VERM, VERM_T), ("H9", AMAR, AMAR_T)):
    ws_dash.conditional_formatting.add(cel, CellIsRule(operator="greaterThan", formula=["0"],
        fill=PatternFill("solid", fgColor=cor),
        font=Font(name="Calibri", size=14, bold=True, color=fonte)))


# ---------------------------------------------------------------- VALIDAÇÕES
def add_dv(ws, formula, ranges, kind="list", **kw):
    dv = DataValidation(type=kind, formula1=formula, allow_blank=True, showErrorMessage=True, **kw)
    ws.add_data_validation(dv)
    for rg in ranges:
        dv.add(rg)
    return dv

dvx = add_dv(ws_eqp, '"X"', ["%s%d:%s%d" % (XL1, EQ_R1, XL2, EQ_R2)])
dvx.errorTitle = "Marque apenas X"
dvx.error = "Use X para indicar que o técnico faz essa especialidade; deixe em branco se não faz."
add_dv(ws_eqp, "=Lista_StatusCad", ["D%d:D%d" % (EQ_R1, EQ_R2)])
add_dv(ws_cfg, '"Cirúrgica,Apoio"', ["C%d:C%d" % (ESP_R1, ESP_R2)])
add_dv(ws_cfg, '"Sim,Não"', ["E%d:E%d" % (ESP_R1, ESP_R2)])
add_dv(ws_cfg, "=Lista_TipoPosto", ["C%d:C%d" % (POS_R1, POS_R2)])
add_dv(ws_cfg, "=Lista_Especialidades", ["G%d:G%d" % (POS_R1, POS_R2)])
add_dv(ws_cfg, '"Todos os dias,Seg a Sex,Seg a Sáb"', ["H%d:H%d" % (POS_R1, POS_R2)])
add_dv(ws_cfg, '"Ativo,Inativo"', ["I%d:I%d" % (POS_R1, POS_R2)])
add_dv(ws_cfg, '"Sim,Não"', ["K%d:K%d" % (POS_R1, POS_R2)])
add_dv(ws_cfg, "1", ["D%d:E%d" % (POS_R1, POS_R2)], kind="whole", operator="between", formula2="4")
add_dv(ws_cfg, "=Lista_Especialidades", ["B%d:B%d" % (CIR_R1, CIR_R2)])
add_dv(ws_aus, "=Lista_Tecnicos", ["A%d:A%d" % (AU_R1, AU_R2)])
add_dv(ws_aus, "=Aus_Tipos", ["B%d:B%d" % (AU_R1, AU_R2)])
dvd = add_dv(ws_aus, "DATE(2000,1,1)", ["C%d:D%d" % (AU_R1, AU_R2)], kind="date",
             operator="between", formula2="DATE(2100,12,31)")
dvd.errorTitle = "Data inválida"; dvd.error = "Informe uma data válida."
add_dv(ws_map, "=Lista_Postos", ["B%d:B%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_Especialidades", ["E%d:E%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_StatusCir", ["H%d:H%d" % (MP_R1, MP_R2)])
dvt = add_dv(ws_map, "TIME(0,0,0)", ["C%d:D%d" % (MP_R1, MP_R2)], kind="time",
             operator="between", formula2="TIME(23,59,0)")
dvt.errorTitle = "Horário inválido"; dvt.error = "Informe um horário no formato HH:MM."
dve = add_dv(ws_pai, "=Lista_Tecnicos", ["D%d:D%d" % (PAI_R1, PAI_R2), "E%d:E%d" % (PAI_R1, PAI_R2)])
dve.errorTitle = "Técnico não cadastrado"; dve.error = "Escolha um técnico da aba Equipe."

# ---------------------------------------------------------------- FORMATAÇÃO CONDICIONAL
fv, fvt = PatternFill("solid", fgColor=VERDE), Font(color=VERDE_T, bold=True)
fa, fat = PatternFill("solid", fgColor=AMAR), Font(color=AMAR_T, bold=True)
fr, frt = PatternFill("solid", fgColor=VERM), Font(color=VERM_T, bold=True)
fc = PatternFill("solid", fgColor=CINZA)

sit = "F%d:F%d" % (PAI_R1, PAI_R2)
for txt, fill, font in (("OK", fv, fvt), ("ATENÇÃO", fa, fat), ("FALTA HABILIDADE", fr, frt),
                        ("SEM EQUIPE", fr, frt), ("INCOMPLETO", fa, fat), ("EXTRA", fa, fat),
                        ("GENTE DEMAIS", fr, frt),
                        ("SEM AVALIAÇÃO", fa, fat)):
    ws_pai.conditional_formatting.add(sit, CellIsRule(operator="equal", formula=['"%s"' % txt],
                                                      fill=fill, font=font))
ws_pai.conditional_formatting.add(sit, CellIsRule(operator="equal", formula=['"NÃO OPERA"'],
                                                  fill=fc, font=Font(color="808080", italic=True)))
# a sala em evidência: a coluna Ambiente recebe a mesma cor da Situação
_amb = "A%d:B%d" % (PAI_R1, PAI_R2)
for _cond, _fill, _cor in (
        ('$F{r}="OK"'.format(r=PAI_R1), fv, VERDE_T),
        ('OR($F{r}="ATENÇÃO",$F{r}="SEM AVALIAÇÃO",$F{r}="INCOMPLETO")'.format(r=PAI_R1), fa, AMAR_T),
        ('OR($F{r}="SEM EQUIPE",$F{r}="FALTA HABILIDADE",$F{r}="GENTE DEMAIS",$F{r}="EXTRA")'.format(r=PAI_R1),
         fr, VERM_T),
        ('$F{r}="NÃO OPERA"'.format(r=PAI_R1), fc, "808080")):
    ws_pai.conditional_formatting.add(_amb, FormulaRule(
        formula=[_cond], fill=_fill, font=Font(name="Calibri", size=12, bold=True, color=_cor)))
ws_pai.conditional_formatting.add("G%d:G%d" % (PAI_R1, PAI_R2),
    FormulaRule(formula=['AND($G%d<>"",$G%d<>"OK")' % (PAI_R1, PAI_R1)], fill=fr, font=frt))
ws_pai.conditional_formatting.add("I%d:I%d" % (PAI_R1, PAI_R2),
    FormulaRule(formula=['AND($I%d<>"",$I%d>1)' % (PAI_R1, PAI_R1)], fill=fr, font=frt))
ws_pai.conditional_formatting.add("J%d:J%d" % (PAI_R1, PAI_R2),
    FormulaRule(formula=['AND($J%d<>"",$J%d<>"—")' % (PAI_R1, PAI_R1)], fill=fv, font=fvt))
# ambiente de uma pessoa só: a segunda coluna deixa de ser azul
ws_pai.conditional_formatting.add("E%d:E%d" % (PAI_R1, PAI_R2),
    FormulaRule(formula=['AND($A%d<>"",$B%d<2)' % (PAI_R1, PAI_R1)], fill=fc,
                font=Font(color="808080", italic=True)))
ws_pai.conditional_formatting.add("G6", FormulaRule(formula=['$G$6>0'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("I6", FormulaRule(formula=['$I$6>0'], fill=fa, font=fat))
ws_pai.conditional_formatting.add("L%d:L%d" % (PAI_R1, PAI_R2),
    FormulaRule(formula=['AND($L%d<>"",$L%d>0)' % (PAI_R1, PAI_R1)], fill=fa, font=fat))
ws_pai.conditional_formatting.add("H6", FormulaRule(formula=['$H$6>0'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("E6", FormulaRule(formula=['$E$6>=$F$6'], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("B%d:B%d" % (EQH_R1, EQH_R1 + N_EQ - 1),
    CellIsRule(operator="equal", formula=['"Disponível"'], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("B%d:B%d" % (EQH_R1, EQH_R1 + N_EQ - 1),
    FormulaRule(formula=['AND($B%d<>"",$B%d<>"Disponível")' % (EQH_R1, EQH_R1)], fill=fa, font=fat))
ws_pai.conditional_formatting.add("D%d:D%d" % (EQH_R1, EQH_R1 + N_EQ - 1),
    CellIsRule(operator="equal", formula=['"—"'], fill=fc, font=Font(color="808080")))
ws_pai.conditional_formatting.add("B%d:B%d" % (CHK_R1, CHK_R2),
    FormulaRule(formula=['OR(LEFT($B%d,4)="ERRO",LEFT($B%d,8)="PENDENTE")' % (CHK_R1, CHK_R1)],
                fill=fr, font=frt))
ws_pai.conditional_formatting.add("B%d:B%d" % (CHK_R1, CHK_R2),
    CellIsRule(operator="equal", formula=['"OK"'], fill=fv, font=fvt))
ws_eqp.conditional_formatting.add("%s%d:%s%d" % (XL1, EQ_R1, XL2, EQ_R2),
    CellIsRule(operator="equal", formula=['"X"'], fill=fv, font=Font(color=VERDE_T, bold=True)))
ws_eqp.conditional_formatting.add("E%d:E%d" % (EQ_R1, EQ_R2),
    CellIsRule(operator="equal", formula=['"Disponível"'], fill=fv, font=fvt))
ws_eqp.conditional_formatting.add("E%d:E%d" % (EQ_R1, EQ_R2),
    FormulaRule(formula=['AND($E%d<>"",$E%d<>"Disponível")' % (EQ_R1, EQ_R1)], fill=fa, font=fat))
ws_map.conditional_formatting.add("N%d:N%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['AND($N%d<>"",$N%d<>"OK")' % (MP_R1, MP_R1)], fill=fr, font=frt))
ws_map.conditional_formatting.add("H%d:H%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['OR($H%d="Cancelada",$H%d="Suspensa")' % (MP_R1, MP_R1)],
                fill=fc, font=Font(color="808080", italic=True)))
ws_map.conditional_formatting.add("M%d:M%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['AND($M%d<>"",$M%d>=Janela_Min)' % (MP_R1, MP_R1)], fill=fv, font=fvt))
ws_aus.conditional_formatting.add("E%d:E%d" % (AU_R1, AU_R2),
    FormulaRule(formula=['AND($E%d<>"",$E%d<=0)' % (AU_R1, AU_R1)], fill=fr, font=frt))
CAL_RNG = "%s%d:%s%d" % (get_column_letter(D1C), CAL_R1, get_column_letter(D2C), CAL_R2)
for i, (tp, sg) in enumerate(TIPOS_AUS):
    ws_aus.conditional_formatting.add(CAL_RNG, CellIsRule(
        operator="equal", formula=['"%s"' % sg],
        fill=PatternFill("solid", fgColor=CORES_AUS[i]), font=Font(bold=True, size=9)))
ws_aus.conditional_formatting.add(CAL_RNG, CellIsRule(operator="equal", formula=['"!"'], fill=fr, font=frt))
ws_aus.conditional_formatting.add(CAL_RNG, FormulaRule(
    formula=['%s$1=Data_Mapa' % get_column_letter(D1C)],
    fill=PatternFill("solid", fgColor=AM)))
ws_aus.conditional_formatting.add(CAL_RNG, FormulaRule(
    formula=['AND(%s$1<>"",OR(WEEKDAY(%s$1)=1,WEEKDAY(%s$1)=7,COUNTIF(Feriados,%s$1)>0))'
             % tuple([get_column_letter(D1C)] * 4)],
    fill=PatternFill("solid", fgColor="EDEDED")))
ws_aus.conditional_formatting.add("%s%d:%s%d" % (get_column_letter(D1C), CAL_R2 + 4,
                                                 get_column_letter(D2C), CAL_R2 + 4),
    CellIsRule(operator="greaterThan", formula=["0"], fill=fr, font=frt))

# ---------------------------------------------------------------- IMPRESSÃO
ws_pai.page_setup.orientation = "landscape"
ws_pai.page_setup.fitToWidth = 1; ws_pai.page_setup.fitToHeight = 0
ws_pai.sheet_properties.pageSetUpPr.fitToPage = True
ws_pai.print_area = "A1:M%d" % (CHK_R2 + 1)
for ws, area in ((ws_map, "A1:N%d" % (MP_R1 + max(1, len(MAPA)) - 1)),
                 (ws_eqp, "A1:%s%d" % (get_column_letter(XC2 + 1), EQ_R2))):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"; ws.print_area = area

wb.save(OUT)
print("salvo:", OUT)

import os as _o
if _o.environ.get("VISUAL") == "1":
    for nome, area in {S_PAI: "A1:M%d" % (CHK_R2 + 1),
                       S_MAP: "A1:N24", S_EQP: "A1:%s28" % get_column_letter(XC2 + 1),
                       S_AUS: "A1:%s%d" % (get_column_letter(D2C + 4), CAL_R2 + 4),
                       S_CFG: "A1:K%d" % (CIR_R1 + 12)}.items():
        w = wb[nome]
        w.page_setup.orientation = "landscape"
        w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 1
        w.sheet_properties.pageSetUpPr.fitToPage = True
        w.print_area = area
    wb.save(OUT.replace(".xlsx", "_VISUAL.xlsx"))
    print("visual:", OUT.replace(".xlsx", "_VISUAL.xlsx"))
