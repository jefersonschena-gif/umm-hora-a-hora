# -*- coding: utf-8 -*-
"""
Centro Cirúrgico — Escala Diária de Técnicos por Posto (v2)

Realidade do serviço (informada pela coordenação):
  * 8 salas cirúrgicas, 2 técnicos cada .................... 16 vagas
  * Admissão, 2 técnicos ....................................  2 vagas
  * Box de preparo oftalmológico (apoio da Sala 8), 1 técnico  1 vaga
  * Sala de recém-nascido (bloco obstétrico), 1 técnico .....  1 vaga
                                                            = 20 vagas/dia
  * 22 técnicos no quadro, com férias, folgas e atestados
  * Sala 6 exclusiva do centro obstétrico (cesarianas)
  * Sala 7 reservada a urgências (normalmente sem agenda prévia)
  * Sala 8 oftalmológica, apoiada pelo box de preparo
  * 20 min de limpeza/preparação ao fim de cada cirurgia
  * a habilidade do técnico É a especialidade da cirurgia (lista única); sem cirurgia cardíaca

Premissas adotadas (não confirmadas, documentadas na aba Instruções):
  P1. A escala do dia cobre UM plantão (07:00–19:00, parametrizável).
      22 técnicos para 20 vagas só fecha com um turno.
  P2. Nas salas os dois técnicos têm papéis distintos (circulante e
      instrumentador); nos postos de apoio não há distinção.

INPUT  -> Parâmetros, Habilidades, Especialidades, Postos, Equipe,
          Matriz_Habilidades, Ausencias, Mapa_Cirurgico, escolha dos técnicos
PROC   -> Calc_Mix (minutos por especialidade em cada posto), Calc_Afinidade
OUTPUT -> Escala_Dia, Sugestao_Tecnicos, Jogo_de_Sala, Calendario_Ausencias,
          Painel, Base_Historico
"""
import random
from datetime import date, time, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule, ColorScaleRule
from openpyxl.chart import BarChart, Reference

OUT = "/home/user/umm-hora-a-hora/centro-cirurgico/Centro_Cirurgico_Escala_Diaria_v2.xlsx"

# ---------------------------------------------------------------- dimensões
HAB_N = 20            # colunas da matriz = itens da lista de especialidades
HAB_R1, HAB_R2 = 2, 1 + HAB_N
ESP_N = HAB_N         # lista única de especialidades (a mesma da matriz)
ESP_R1, ESP_R2 = 2, 1 + ESP_N
POS_N = 16            # postos (11 em uso)
POS_R1, POS_R2 = 2, 1 + POS_N
EQ_N = 30             # técnicos (22 em uso)
EQ_R1, EQ_R2 = 2, 1 + EQ_N
MAPA_N = 200          # cirurgias por dia
MP_R1, MP_R2 = 2, 1 + MAPA_N
AUS_N = 150           # registros de ausência
AU_R1, AU_R2 = 2, 1 + AUS_N
JOGO_K = 13           # janelas livres analisadas por sala (0..12)
HIST_R2 = 2001
DIAS_MES = 31

HC1, HC2 = 6, 5 + HAB_N                      # Calc_Mix: colunas F..S das habilidades
HL1, HL2 = get_column_letter(HC1), get_column_letter(HC2)
MC1, MC2 = 4, 3 + HAB_N                      # Matriz: colunas D..Q dos níveis
ML1, ML2 = get_column_letter(MC1), get_column_letter(MC2)

S_INS, S_PAR, S_ESP = "Instruções", "Parâmetros", "Especialidades"
S_POS, S_EQP, S_MAT, S_AUS = "Postos", "Equipe", "Matriz_Habilidades", "Ausencias"
S_CAL, S_MAP, S_MIX, S_AFI = "Calendario_Ausencias", "Mapa_Cirurgico", "Calc_Mix", "Calc_Afinidade"
S_ESC, S_SUG, S_JOG = "Escala_Dia", "Sugestao_Tecnicos", "Jogo_de_Sala"
S_PAI, S_HIS = "Painel", "Base_Historico"

def R(sheet, addr):
    return "'%s'!%s" % (sheet, addr)

# ---------------------------------------------------------------- estilo
AZ_ESC, AZ_MED, AZ_CLR = "1F3864", "2E75B6", "DDEBF7"
AM_PRE, CINZA = "FFF2CC", "F2F2F2"
VERDE, VERDE_T, AMAR, AMAR_T, VERM, VERM_T = "C6EFCE", "006100", "FFEB9C", "9C6500", "FFC7CE", "9C0006"
F_ENTRADA = Font(name="Calibri", size=10, color="0070C0")
F_FORMULA = Font(name="Calibri", size=10, color="000000")
F_REF     = Font(name="Calibri", size=10, color="006100", italic=True)
F_HEAD    = Font(name="Calibri", size=10, color="FFFFFF", bold=True)
F_TIT     = Font(name="Calibri", size=14, color=AZ_ESC, bold=True)
F_SEC     = Font(name="Calibri", size=11, color=AZ_ESC, bold=True)
F_NOTA    = Font(name="Calibri", size=9, color="7F7F7F", italic=True)
FILL_HEAD = PatternFill("solid", fgColor=AZ_ESC)
FILL_PREM = PatternFill("solid", fgColor=AM_PRE)
FILL_ENT  = PatternFill("solid", fgColor=AZ_CLR)
FILL_CINZ = PatternFill("solid", fgColor=CINZA)
THIN = Side(style="thin", color="BFBFBF")
BORD = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CTR  = Alignment(horizontal="center", vertical="center")
CTRW = Alignment(horizontal="center", vertical="center", wrap_text=True)
LFT  = Alignment(horizontal="left", vertical="center")
ROT  = Alignment(horizontal="center", vertical="bottom", text_rotation=90)

def head(ws, row, labels, col0=1, height=30):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=col0 + i, value=t)
        c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = CTRW; c.border = BORD
    ws.row_dimensions[row].height = height

def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w

def title(ws, text, sub=None):
    ws["A1"] = text; ws["A1"].font = F_TIT
    if sub:
        ws["A2"] = sub; ws["A2"].font = F_NOTA
    ws.row_dimensions[1].height = 22

def fmt_range(ws, r1, r2, c1, c2, font=F_ENTRADA, align=None, numfmt=None):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = BORD; cell.font = font
            if align: cell.alignment = align
            if numfmt: cell.number_format = numfmt

# ---------------------------------------------------------------- dados do serviço
ESPECIALIDADES = [   # (código, especialidade / habilidade, tipo, duração média em min)
    ("ORT", "Ortopedia",                  "Cirúrgica", 120),
    ("TRA", "Traumatologia",              "Cirúrgica", 90),
    ("CGE", "Cirurgia Geral",             "Cirúrgica", 90),
    ("BAR", "Cirurgia Bariátrica",        "Cirúrgica", 150),
    ("PED", "Cirurgia Pediátrica",        "Cirúrgica", 75),
    ("NEU", "Neurocirurgia",              "Cirúrgica", 210),
    ("CES", "Cesariana",                  "Cirúrgica", 60),
    ("GIN", "Ginecologia",                "Cirúrgica", 90),
    ("URO", "Urologia",                   "Cirúrgica", 90),
    ("OFT", "Oftalmologia",               "Cirúrgica", 45),
    ("OTO", "Otorrinolaringologia",       "Cirúrgica", 75),
    ("BMF", "Buco-Maxilo-Facial",         "Cirúrgica", 120),
    ("PLA", "Cirurgia Plástica",          "Cirúrgica", 120),
    ("VAS", "Cirurgia Vascular",          "Cirúrgica", 150),
    ("ADM", "Admissão",                   "Apoio",     0),
    ("RN",  "Sala de recém-nascido",      "Apoio",     0),
]
HABILIDADES = [(e[0], e[1]) for e in ESPECIALIDADES]     # habilidade == especialidade
HAB_NOMES = [h[1] for h in HABILIDADES]
HAB_IDX = {h[1]: i for i, h in enumerate(HABILIDADES)}
ESP_HAB = {e[1]: e[1] for e in ESPECIALIDADES}
ESP_DUR = {e[1]: e[3] for e in ESPECIALIDADES}

POSTOS = [   # (código, nome, tipo, necessários, mínimo, prioridade, habilidade ref., funciona em, observação)
    ("SO-07", "Sala 7", "Sala cirúrgica", 2, 2,  1, "Cirurgia Geral e Videolaparoscopia", "Todos os dias", "RESERVADA a urgências — não pode ficar descoberta"),
    ("SO-06", "Sala 6", "Sala cirúrgica", 2, 2,  2, "Obstetrícia (cesariana)", "Todos os dias", "EXCLUSIVA do centro obstétrico — cesarianas"),
    ("RN",    "Sala de recém-nascido", "Apoio", 1, 1,  3, "Sala de recém-nascido", "Todos os dias", "Bloco obstétrico"),
    ("ADM",   "Admissão", "Apoio", 2, 1,  4, "Admissão", "Todos os dias", "Recepção e preparo do paciente — opera com 1 no limite"),
    ("SO-01", "Sala 1", "Sala cirúrgica", 2, 2,  5, "Ortopedia e Traumatologia", "Seg a Sex", "Eletivas de ortopedia"),
    ("SO-02", "Sala 2", "Sala cirúrgica", 2, 2,  6, "Cirurgia Geral e Videolaparoscopia", "Seg a Sex", "Eletivas de cirurgia geral"),
    ("SO-05", "Sala 5", "Sala cirúrgica", 2, 2,  7, "Ginecologia e Urologia", "Seg a Sex", "Gineco e urologia"),
    ("SO-08", "Sala 8", "Sala cirúrgica", 2, 2,  8, "Oftalmologia", "Seg a Sex", "Oftalmologia — apoiada pelo box de preparo"),
    ("SO-03", "Sala 3", "Sala cirúrgica", 2, 2,  9, "Neurocirurgia", "Seg a Sex", "Eletivas de neurocirurgia"),
    ("SO-04", "Sala 4", "Sala cirúrgica", 2, 2, 10, "Cirurgia Plástica e Vascular", "Seg a Sex", "Plástica e vascular"),
    ("BOX",   "Box de preparo oftalmológico", "Apoio", 1, 1, 11, "Oftalmologia", "Seg a Sex", "Apoio da Sala 8"),
]
POSTO_ORDEM = ["SO-01","SO-02","SO-03","SO-04","SO-05","SO-06","SO-07","SO-08","ADM","BOX","RN"]
POSTOS.sort(key=lambda p: POSTO_ORDEM.index(p[0]))   # exibição na ordem natural das salas
VAGAS_TOTAL = sum(p[3] for p in POSTOS)

TIPOS_AUS = [("Folga", "F"), ("Férias", "FR"), ("Atestado", "AT"), ("Licença", "LI"),
             ("Treinamento", "TR"), ("FH", "FH"), ("Licença gestação", "LG")]

NOMES = ["Adriana Salvi","Bruna Cordeiro","Camila Bertoldi","Daiane Prestes","Elaine Mafra",
 "Fernanda Klein","Gisele Antunes","Heloísa Perin","Ismael Kanitz","Joana Belincanta",
 "Kelly Marchi","Luciano Bordin","Marcia Tonet","Nádia Fávero","Odair Bianchi",
 "Patrícia Zortéa","Rafaela Gubert","Simone Dalpra","Tatiane Bolzan","Vagner Sartori",
 "Wanessa Piccoli","Zuleide Marcon"]
FUNCOES = (["Circulante"]*9 + ["Instrumentador"]*9 + ["Ambos"]*4)

random.seed(20260819)
DIA = date(2026, 8, 20)
TURNO_INI, TURNO_FIM, TURNO_MIN = time(7, 0), time(13, 0), 360
LIMPEZA = 20

# ---- habilidades de cada técnico (10 níveis, 0..3)
PERFIS = [   # habilidade principal de cada técnico, na ordem dos nomes
 0, 0, 1, 1, 2, 2, 7, 7, 4, 4, 5, 5, 3, 3, 8, 8, 9, 1, 0, 6, 6, 8]
def build_skills():
    sk = {}
    for i, nome in enumerate(NOMES):
        lv = [0]*len(HABILIDADES)
        p = PERFIS[i]
        lv[p] = 3
        lv[(p+1) % 10] = 2 if random.random() < 0.7 else 1
        lv[(p+2) % 10] = 2 if random.random() < 0.45 else 1
        lv[8] = max(lv[8], 2 if random.random() < 0.6 else 1)          # admissão: quase todos
        for j in range(len(lv)):
            if lv[j] == 0 and random.random() < 0.35:
                lv[j] = 1
        sk[nome] = lv
    return sk
SKILLS = build_skills()
EQUIPE = [("TEC-%03d" % (i+1), NOMES[i], "", FUNCOES[i], "Ativo") for i in range(len(NOMES))]

# ---- ausências do mês (a data do mapa cai em 20/08/2026)
AUSENCIAS = [
    ("Zuleide Marcon",   "Férias",      date(2026, 8, 10), date(2026, 8, 24), "Férias programadas"),
    ("Ismael Kanitz",    "Férias",      date(2026, 8,  6), date(2026, 8, 20), "Férias programadas"),
    ("Wanessa Piccoli",  "Atestado",    date(2026, 8, 19), date(2026, 8, 21), "Atestado médico — 3 dias"),
    ("Elaine Mafra",     "Folga",       date(2026, 8, 20), date(2026, 8, 20), "Folga da escala"),
    ("Adriana Salvi",    "Folga",       date(2026, 8, 12), date(2026, 8, 12), ""),
    ("Bruna Cordeiro",   "Folga",       date(2026, 8, 13), date(2026, 8, 13), ""),
    ("Camila Bertoldi",  "Folga",       date(2026, 8, 17), date(2026, 8, 17), ""),
    ("Daiane Prestes",   "Folga",       date(2026, 8, 18), date(2026, 8, 18), ""),
    ("Fernanda Klein",   "Folga",       date(2026, 8, 24), date(2026, 8, 24), ""),
    ("Gisele Antunes",   "Treinamento", date(2026, 8, 26), date(2026, 8, 27), "Curso de CME"),
    ("Marcia Tonet",     "Folga",       date(2026, 8, 25), date(2026, 8, 25), ""),
    ("Odair Bianchi",    "Licença",     date(2026, 8, 28), date(2026, 8, 31), "Licença nojo"),
    ("Patrícia Zortéa",  "Atestado",    date(2026, 8,  5), date(2026, 8,  6), "Atestado médico"),
]
PERIODO_INI = date(2026, 8, 16)          # a escala do serviço vai do dia 16 ao dia 15
COORDENACAO = "Coordenação de Enfermagem"
AFASTADOS = set()

# ---------------------------------------------------------------- cadastro real (opcional)
import json as _json, os as _os
_REAL = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "dados", "equipe_real.json")
USANDO_REAL = _os.path.exists(_REAL)
if USANDO_REAL:
    _d = _json.load(open(_REAL, encoding="utf-8"))
    _p = lambda x: date(*[int(v) for v in x.split("-")])
    AFASTADOS = set(_d.get("afastados", []))
    EQUIPE = [(pp.get("matricula", ""), pp["nome"], pp.get("coren", ""), "Ambos",
               "Afastado" if pp["nome"] in AFASTADOS else "Ativo") for pp in _d["pessoas"]]
    NOMES = [e[1] for e in EQUIPE]
    # sem avaliação de habilidades ainda: todos entram como "Apto" e o Painel avisa que falta calibrar
    SKILLS = {n: [2] * len(HABILIDADES) for n in NOMES}
    AUSENCIAS = [(a["tec"], a["tipo"], _p(a["ini"]), _p(a["fim"]), "") for a in _d["ausencias"]]
    if _d.get("periodo_ini"):
        PERIODO_INI = _p(_d["periodo_ini"])
    if _d.get("coordenacao"):
        COORDENACAO = _d["coordenacao"]
    OUT = OUT.replace("_v2.xlsx", "_REAL.xlsx")

AUSENTES_NA_DATA = {a[0] for a in AUSENCIAS if a[2] <= DIA <= a[3]}

# ---------------------------------------------------------------- agenda do dia
SALA_ESP = {
    "SO-01": ["Ortopedia", "Traumatologia"],
    "SO-02": ["Cirurgia Geral", "Cirurgia Bariátrica", "Cirurgia Pediátrica"],
    "SO-03": ["Neurocirurgia"],
    "SO-04": ["Cirurgia Plástica", "Cirurgia Vascular"],
    "SO-05": ["Ginecologia", "Urologia"],
    "SO-06": ["Cesariana"],
    "SO-07": ["Cirurgia Geral"],
    "SO-08": ["Oftalmologia", "Otorrinolaringologia", "Buco-Maxilo-Facial"],
}
PROCEDIMENTOS = {
 "Ortopedia": ["Artroplastia total de joelho", "Artroplastia total de quadril", "Artroscopia de ombro"],
 "Traumatologia": ["Osteossíntese de fêmur", "Redução de fratura de rádio"],
 "Cirurgia Geral": ["Colecistectomia videolaparoscópica", "Herniorrafia inguinal", "Apendicectomia"],
 "Cirurgia Bariátrica": ["Gastroplastia em Y de Roux", "Gastrectomia vertical"],
 "Cirurgia Pediátrica": ["Postectomia", "Correção de hérnia umbilical"],
 "Neurocirurgia": ["Craniotomia para tumor", "Artrodese lombar"],
 "Cesariana": ["Cesariana", "Cesariana com laqueadura"],
 "Ginecologia": ["Histerectomia total", "Videolaparoscopia diagnóstica"],
 "Urologia": ["Ressecção transuretral de próstata", "Nefrolitotripsia"],
 "Oftalmologia": ["Facectomia com implante de LIO", "Vitrectomia posterior", "Pterígio"],
 "Otorrinolaringologia": ["Amigdalectomia", "Septoplastia"],
 "Buco-Maxilo-Facial": ["Osteotomia mandibular"],
 "Cirurgia Plástica": ["Dermolipectomia abdominal", "Enxerto de pele em queimado"],
 "Cirurgia Vascular": ["Safenectomia", "Confecção de fístula arteriovenosa"],
}
CIRURGIOES = ["Dr. Almeida","Dra. Bernardes","Dr. Coelho","Dra. Delgado","Dr. Esteves",
              "Dra. Fialho","Dr. Gouveia","Dra. Hirano","Dr. Iglesias","Dra. Jordão"]
BASE_MIN = TURNO_INI.hour * 60 + TURNO_INI.minute

def build_mapa():
    """Agenda do dia. Deixa intervalos livres propositais em algumas salas
    para o Jogo_de_Sala ter o que mostrar."""
    cirs = []
    plano = {"SO-01": (0.80, 0), "SO-02": (0.75, 40), "SO-03": (0.70, 0), "SO-04": (0.65, 30),
             "SO-05": (0.80, 0), "SO-06": (0.30, 0), "SO-07": (0.25, 0), "SO-08": (0.85, 0)}
    for sala, (alvo, folga_extra) in plano.items():
        esps = SALA_ESP[sala]
        decorrido, k = 0, 0
        limite = int(TURNO_MIN * alvo)
        while decorrido < limite and k < 6:
            esp = esps[k % len(esps)]
            dur = int(round(ESP_DUR[esp] * random.uniform(0.8, 1.2) / 5.0) * 5)
            if decorrido + dur + LIMPEZA > TURNO_MIN:
                break
            ini = BASE_MIN + decorrido
            status = "Agendada"
            if sala == "SO-02" and k == 2:
                status = "Cancelada"
            porte = "G" if dur >= 180 else ("M" if dur >= 90 else "P")
            cirs.append(dict(data=DIA, sala=sala, ini=ini, fim=ini + dur, esp=esp,
                             proc=PROCEDIMENTOS[esp][k % len(PROCEDIMENTOS[esp])],
                             cir=CIRURGIOES[(hash(sala) + k) % len(CIRURGIOES)],
                             porte=porte, status=status, dur=dur))
            decorrido += dur + LIMPEZA
            if folga_extra and k == 1:
                decorrido += folga_extra          # intervalo livre proposital
            k += 1
    cirs.sort(key=lambda c: (c["sala"], c["ini"]))
    return cirs
MAPA = build_mapa()

def mix_do_posto(cod):
    """Minutos de ocupação por especialidade no posto (ETL independente, em Python)."""
    m = [0.0] * len(HABILIDADES)
    for c in MAPA:
        if c["sala"] == cod and c["status"] not in ("Cancelada", "Suspensa"):
            m[HAB_IDX[ESP_HAB[c["esp"]]]] += c["dur"] + LIMPEZA
    return m

def mix_efetivo(cod):
    """Mix usado para afinidade: a agenda; sem agenda, a especialidade de referência do posto."""
    p = [x for x in POSTOS if x[0] == cod][0]
    m = mix_do_posto(cod) if p[2] == "Sala cirúrgica" else [0.0] * len(HABILIDADES)
    if sum(m) == 0:
        m = [0.0] * len(HABILIDADES)
        m[HAB_IDX[p[6]]] = float(TURNO_MIN)
    return m

def afin(nome, cod):
    m = mix_efetivo(cod); tot = sum(m)
    return sum(a * b for a, b in zip(m, SKILLS[nome])) / tot if tot else None

# ---------------------------------------------------------------- alocação de exemplo
def build_escala():
    """Duas etapas: (1) prioridade decide QUAIS postos são cobertos com o pessoal
    disponível; (2) entre as vagas cobertas, a designação maximiza a afinidade global,
    respeitando circulante/instrumentador."""
    disp = [n for (_, n, _, _, st) in EQUIPE if n not in AUSENTES_NA_DATA and st == "Ativo"]
    func = {e[1]: e[3] for e in EQUIPE}
    vagas, restantes = [], len(disp)
    for cod, nome, tipo, nec, minimo, prior, hab, dias, obs in sorted(POSTOS, key=lambda p: p[5]):
        if restantes < minimo:
            continue
        alvo = nec if restantes >= nec else minimo
        for i in range(alvo):
            papel = ("Circulante" if i == 0 else "Instrumentador") if tipo == "Sala cirúrgica" else "Técnico"
            vagas.append((cod, i + 1, papel))
        restantes -= alvo
    def elegivel(n, papel):
        return papel == "Técnico" or func[n] == papel or func[n] == "Ambos"
    prio = {p[0]: p[5] for p in POSTOS}
    aloc, usados, feitas = {}, set(), set()
    pendentes = list(vagas)
    while pendentes:                       # vaga mais restrita primeiro (menos gente apta)
        melhor, escolha = None, None
        for (cod, slot, papel) in pendentes:
            cands = [n for n in disp if n not in usados and elegivel(n, papel)]
            if not cands:
                continue
            aptos = sum(1 for n in cands if (afin(n, cod) or 0) >= 2)
            top = max(cands, key=lambda n: (afin(n, cod) or 0))
            chave = (aptos if aptos else 99, prio[cod], -(afin(top, cod) or 0), cod, slot)
            if melhor is None or chave < melhor:
                melhor, escolha = chave, (cod, slot, top)
        if escolha is None:
            break
        cod, slot, n = escolha
        aloc.setdefault(cod, {})[slot] = n
        usados.add(n); feitas.add((cod, slot))
        pendentes = [v for v in pendentes if (v[0], v[1]) != (cod, slot)]
    for cod, slot, papel in vagas:                      # sobras sem função compatível
        if (cod, slot) in feitas:
            continue
        livres = [n for n in disp if n not in usados]
        if livres:
            best = max(livres, key=lambda n: (afin(n, cod) or 0))
            aloc.setdefault(cod, {})[slot] = best
            usados.add(best); feitas.add((cod, slot))
    return aloc
ALOC = build_escala()

# ================================================================ WORKBOOK
wb = Workbook()
ws_ins = wb.active; ws_ins.title = S_INS
ws_par = wb.create_sheet(S_PAR); ws_esp = wb.create_sheet(S_ESP)
ws_pos = wb.create_sheet(S_POS); ws_eqp = wb.create_sheet(S_EQP); ws_mat = wb.create_sheet(S_MAT)
ws_aus = wb.create_sheet(S_AUS); ws_cal = wb.create_sheet(S_CAL); ws_map = wb.create_sheet(S_MAP)
ws_mix = wb.create_sheet(S_MIX); ws_afi = wb.create_sheet(S_AFI); ws_esc = wb.create_sheet(S_ESC)
ws_sug = wb.create_sheet(S_SUG); ws_jog = wb.create_sheet(S_JOG); ws_pai = wb.create_sheet(S_PAI)
ws_his = wb.create_sheet(S_HIS)
for w in wb.worksheets:
    w.sheet_view.showGridLines = False

def dn(name, ref):
    wb.defined_names.add(DefinedName(name, attr_text=ref))

# ---------------------------------------------------------------- PARÂMETROS
title(ws_par, "PARÂMETROS E PREMISSAS",
      "Células amarelas são premissas de negócio. Alterá-las recalcula toda a planilha — nenhuma premissa está embutida em fórmula.")
widths(ws_par, {"A": 50, "B": 14, "C": 12, "D": 24, "E": 3, "F": 16, "G": 16, "H": 16, "I": 7, "J": 16})

def sec(ws, row, text, span=4):
    ws.cell(row=row, column=1, value=text).font = F_SEC
    for i in range(span):
        c = ws.cell(row=row, column=1 + i); c.fill = FILL_CINZ; c.border = BORD

def prem(ws, row, label, value, fmt=None, nota=None):
    ws.cell(row=row, column=1, value=label).font = F_FORMULA
    c = ws.cell(row=row, column=2, value=value)
    c.font = F_ENTRADA; c.fill = FILL_PREM; c.border = BORD; c.alignment = CTR
    if fmt: c.number_format = fmt
    if nota: ws.cell(row=row, column=4, value=nota).font = F_NOTA
    return c

sec(ws_par, 3, "1. IDENTIFICAÇÃO")
prem(ws_par, 4, "Unidade / Hospital", "Hospital — preencher")
prem(ws_par, 5, "Setor", "Centro Cirúrgico")
prem(ws_par, 6, "Data da escala", DIA, "DD/MM/YYYY", "Data_Mapa")
prem(ws_par, 7, "Coordenação responsável", COORDENACAO)
for _r in (4, 5, 7):
    ws_par.merge_cells(start_row=_r, start_column=2, end_row=_r, end_column=4)
    ws_par.cell(row=_r, column=2).alignment = LFT

sec(ws_par, 9, "2. PLANTÃO (a escala do dia cobre um plantão)")
prem(ws_par, 10, "Início do plantão", TURNO_INI, "HH:MM", "Turno_Ini")
prem(ws_par, 11, "Fim do plantão", TURNO_FIM, "HH:MM", "Turno_Fim")
prem(ws_par, 13, "Primeiro dia do período da escala", PERIODO_INI, "DD/MM/YYYY", "Periodo_Ini")
ws_par.cell(row=12, column=1, value="Minutos do plantão").font = F_FORMULA
c = ws_par.cell(row=12, column=2, value="=MOD(B11-B10,1)*1440")
c.border = BORD; c.alignment = CTR; c.number_format = "0"
ws_par.cell(row=12, column=4, value="Turno_Min").font = F_NOTA

ws_par.cell(row=13, column=1).font = F_FORMULA
sec(ws_par, 14, "3. NÍVEIS DE HABILIDADE (usados na Matriz_Habilidades)")
head(ws_par, 15, ["Nível", "Descrição", "Pontos", "Critério operacional"], height=18)
for i, (n, d, pt, crit) in enumerate([
        (0, "Não apto", 0, "Não pode assumir o posto"),
        (1, "Em treinamento", 1, "Só atua acompanhado de técnico apto"),
        (2, "Apto", 2, "Atua com autonomia"),
        (3, "Referência", 3, "Atua em alta complexidade e treina a equipe")]):
    r = 16 + i
    for j, v in enumerate((n, d, pt, crit)):
        cc = ws_par.cell(row=r, column=1 + j, value=v)
        cc.border = BORD; cc.font = F_FORMULA; cc.alignment = CTR if j in (0, 2) else LFT

sec(ws_par, 21, "4. PARÂMETROS DE AFINIDADE")
prem(ws_par, 22, "Peso do INSTRUMENTADOR na afinidade da dupla", 0.60, "0.00", "Peso_Instrumentador")
prem(ws_par, 23, "Peso do CIRCULANTE na afinidade da dupla", 0.40, "0.00", "Peso_Circulante")
ws_par.cell(row=24, column=1, value="Soma dos pesos (precisa ser 1,00)").font = F_FORMULA
c = ws_par.cell(row=24, column=2, value="=B22+B23"); c.number_format = "0.00"; c.border = BORD; c.alignment = CTR
prem(ws_par, 25, "Afinidade META — posto ADEQUADO quando ≥", 2.50, "0.00", "Afinidade_Meta")
prem(ws_par, 26, "Afinidade MÍNIMA aceitável — abaixo é CRÍTICO", 2.00, "0.00", "Afinidade_Min")
prem(ws_par, 27, "Nível considerado INAPTO (≤)", 1, "0", "Nivel_Critico")
prem(ws_par, 28, "Participação mínima da especialidade para alerta crítico", 0.20, "0%", "Part_Min_Critica")

sec(ws_par, 30, "5. PARÂMETROS OPERACIONAIS")
prem(ws_par, 31, "Limpeza e preparação após cada cirurgia (min)", LIMPEZA, "0", "Limpeza_Min")
prem(ws_par, 32, "Janela mínima para considerar encaixe (min)", 30, "0", "Janela_Min")
prem(ws_par, 33, "Meta de ocupação de sala", 0.85, "0%", "Meta_Ocupacao")
prem(ws_par, 34, "Ocupação máxima admitida", 1.00, "0%", "Ocupacao_Max")

sec(ws_par, 36, "6. TIPOS DE AUSÊNCIA")
head(ws_par, 37, ["Tipo", "Sigla", "Cor no calendário", ""], height=18)
CORES_AUS = ["DDEBF7", "FFC7CE", "FFEB9C", "E4DFEC", "D9E1F2", "E2EFDA", "FCE4D6"]
for i, (t, sig) in enumerate(TIPOS_AUS):
    r = 38 + i
    for j, v in enumerate((t, sig)):
        cc = ws_par.cell(row=r, column=1 + j, value=v)
        cc.border = BORD; cc.font = F_FORMULA; cc.alignment = LFT if j == 0 else CTR
    cc = ws_par.cell(row=r, column=3); cc.fill = PatternFill("solid", fgColor=CORES_AUS[i]); cc.border = BORD

sec(ws_par, 46, "7. FERIADOS (nesses dias os postos de dia útil não operam)")
head(ws_par, 47, ["Data", "Feriado", "", ""], height=18)
FERIADOS = [(date(2026, 1, 1), "Confraternização Universal"), (date(2026, 2, 16), "Carnaval"),
            (date(2026, 2, 17), "Carnaval"), (date(2026, 4, 3), "Sexta-feira Santa"),
            (date(2026, 4, 21), "Tiradentes"), (date(2026, 5, 1), "Dia do Trabalho"),
            (date(2026, 6, 4), "Corpus Christi"), (date(2026, 9, 7), "Independência"),
            (date(2026, 10, 12), "Nossa Senhora Aparecida"), (date(2026, 11, 2), "Finados"),
            (date(2026, 11, 15), "Proclamação da República"), (date(2026, 12, 25), "Natal")]
for _i in range(20):
    _r = 48 + _i
    _d = ws_par.cell(row=_r, column=1); _n = ws_par.cell(row=_r, column=2)
    for _c in (_d, _n):
        _c.border = BORD; _c.font = F_ENTRADA; _c.fill = FILL_PREM
    _d.alignment = CTR; _d.number_format = "DD/MM/YYYY"; _n.alignment = LFT
    if _i < len(FERIADOS):
        _d.value, _n.value = FERIADOS[_i]
ws_par.cell(row=69, column=1, value="Acrescente os feriados municipais e os pontos facultativos em que o "
            "centro cirúrgico opera em regime de fim de semana.").font = F_NOTA

ws_par.cell(row=3, column=6, value="LISTAS AUXILIARES").font = F_SEC
head(ws_par, 4, ["Função", "Status cadastral", "Status da cirurgia", "Porte", "Tipo de posto"], col0=6, height=30)
AUX = [["Circulante", "Instrumentador", "Ambos"],
       ["Ativo", "Afastado", "Desligado"],
       ["Agendada", "Realizada", "Cancelada", "Suspensa"],
       ["P", "M", "G"],
       ["Sala cirúrgica", "Apoio"]]
for j, col in enumerate(AUX):
    for i, v in enumerate(col):
        cc = ws_par.cell(row=5 + i, column=6 + j, value=v)
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA

dn("Data_Mapa", R(S_PAR, "$B$6")); dn("Turno_Ini", R(S_PAR, "$B$10"))
dn("Periodo_Ini", R(S_PAR, "$B$13"))
dn("Feriados", R(S_PAR, "$A$48:$A$67"))
dn("Turno_Fim", R(S_PAR, "$B$11")); dn("Turno_Min", R(S_PAR, "$B$12"))
dn("Peso_Instrumentador", R(S_PAR, "$B$22")); dn("Peso_Circulante", R(S_PAR, "$B$23"))
dn("Afinidade_Meta", R(S_PAR, "$B$25")); dn("Afinidade_Min", R(S_PAR, "$B$26"))
dn("Nivel_Critico", R(S_PAR, "$B$27")); dn("Part_Min_Critica", R(S_PAR, "$B$28"))
dn("Limpeza_Min", R(S_PAR, "$B$31")); dn("Janela_Min", R(S_PAR, "$B$32"))
dn("Meta_Ocupacao", R(S_PAR, "$B$33")); dn("Ocupacao_Max", R(S_PAR, "$B$34"))
dn("Aus_Tipos", R(S_PAR, "$A$38:$A$44")); dn("Aus_Siglas", R(S_PAR, "$B$38:$B$44"))
dn("Lista_Funcoes", R(S_PAR, "$F$5:$F$7")); dn("Lista_StatusCad", R(S_PAR, "$G$5:$G$7"))
dn("Lista_StatusCirurgia", R(S_PAR, "$H$5:$H$8")); dn("Lista_Porte", R(S_PAR, "$I$5:$I$7"))
dn("Lista_TipoPosto", R(S_PAR, "$J$5:$J$6")); dn("Lista_TiposAusencia", R(S_PAR, "$A$38:$A$44"))

# ---------------------------------------------------------------- ESPECIALIDADES (= HABILIDADES)
head(ws_esp, 1, ["Código", "Especialidade / habilidade", "Tipo", "Duração média (min)",
                 "Ativa", "Observação"])
widths(ws_esp, {"A": 10, "B": 34, "C": 14, "D": 18, "E": 9, "F": 40})
fmt_range(ws_esp, ESP_R1, ESP_R2, 1, 6, align=LFT)
for i in range(ESP_N):
    r = ESP_R1 + i
    for c in (1, 3, 4, 5):
        ws_esp.cell(row=r, column=c).alignment = CTR
    if i < len(ESPECIALIDADES):
        cod, nome, tipo, dur = ESPECIALIDADES[i]
        ws_esp.cell(row=r, column=1, value=cod); ws_esp.cell(row=r, column=2, value=nome)
        ws_esp.cell(row=r, column=3, value=tipo); ws_esp.cell(row=r, column=4, value=dur)
        ws_esp.cell(row=r, column=5, value="Sim")
ws_esp.cell(row=ESP_R2 + 2, column=1,
            value="Esta é a lista ÚNICA do serviço: é ela que aparece na agenda do Mapa_Cirurgico e é ela "
                  "que vira as colunas da Matriz_Habilidades — a habilidade do técnico é a própria "
                  "especialidade da cirurgia.").font = F_NOTA
ws_esp.cell(row=ESP_R2 + 3, column=1,
            value="As duas linhas de tipo 'Apoio' (Admissão e Sala de recém-nascido) existem porque esses "
                  "postos também exigem competência, mas não são cirurgias. Não se realizam cirurgias "
                  "cardíacas nesta unidade — ajuste a lista ao que o serviço faz. Há %d posições; %d em uso."
                  % (ESP_N, len(ESPECIALIDADES))).font = F_NOTA
ws_esp.freeze_panes = "A2"; ws_esp.auto_filter.ref = "A1:F%d" % ESP_R2

# ---------------------------------------------------------------- POSTOS
head(ws_pos, 1, ["Código", "Posto", "Tipo", "Técnicos necessários", "Mínimo aceitável",
                 "Prioridade de cobertura", "Especialidade de referência", "Funciona em",
                 "Status", "Observação"], height=44)
widths(ws_pos, {"A": 9, "B": 28, "C": 15, "D": 13, "E": 12, "F": 13, "G": 34, "H": 14,
                "I": 12, "J": 46})
fmt_range(ws_pos, POS_R1, POS_R2, 1, 10, align=CTR)
for i in range(POS_N):
    r = POS_R1 + i
    for c in (2, 7, 10):
        ws_pos.cell(row=r, column=c).alignment = LFT
    if i < len(POSTOS):
        cod, nome, tipo, nec, mini, prior, hab, func, obs = POSTOS[i]
        for j, v in enumerate((cod, nome, tipo, nec, mini, prior, hab, func, "Ativo", obs)):
            ws_pos.cell(row=r, column=1 + j, value=v)
ws_pos.cell(row=POS_R2 + 2, column=1,
            value="Prioridade 1 é coberta primeiro quando falta pessoal. 'Mínimo aceitável' é o número de técnicos "
                  "com que o posto ainda pode abrir; abaixo disso o posto fica descoberto.").font = F_NOTA
ws_pos.freeze_panes = "B2"; ws_pos.auto_filter.ref = "A1:J%d" % POS_R2

# ---------------------------------------------------------------- EQUIPE
head(ws_eqp, 1, ["Matrícula", "Nome do técnico", "COREN", "Função", "Status cadastral",
                 "SITUAÇÃO NA DATA", "Ausente até", "Observação"], height=32)
widths(ws_eqp, {"A": 12, "B": 30, "C": 12, "D": 15, "E": 15, "F": 18, "G": 13, "H": 28})
fmt_range(ws_eqp, EQ_R1, EQ_R2, 1, 8, align=CTR)
for i in range(EQ_N):
    r = EQ_R1 + i
    ws_eqp.cell(row=r, column=2).alignment = LFT; ws_eqp.cell(row=r, column=8).alignment = LFT
    if i < len(EQUIPE):
        for j, v in enumerate(EQUIPE[i]):
            ws_eqp.cell(row=r, column=1 + j, value=v)
    e = ws_eqp.cell(row=r, column=6, value=(
        '=IF($B{r}="","",IF($E{r}<>"Ativo",$E{r},'
        'IFERROR(INDEX(Aus_Tipo,MATCH($B{r},Aus_Ativa,0)),"Disponível")))').format(r=r))
    f = ws_eqp.cell(row=r, column=7, value=(
        '=IF(OR($B{r}="",$F{r}="Disponível"),"",IFERROR(INDEX(Aus_Fim,MATCH($B{r},Aus_Ativa,0)),""))').format(r=r))
    e.font = F_FORMULA; f.font = F_FORMULA; f.number_format = "DD/MM"
ws_eqp.freeze_panes = "C2"; ws_eqp.auto_filter.ref = "A1:H%d" % EQ_R2

# ---------------------------------------------------------------- MATRIZ DE HABILIDADES
head(ws_mat, 1, ["Matrícula", "Nome do técnico", "Função"] + [""] * HAB_N +
     ["Nível médio (geral)", "Nº especialidades aptas (≥2)"], height=176)
for i in range(HAB_N):
    c = ws_mat.cell(row=1, column=MC1 + i, value='=IF(%s="","",%s)' % (
        R(S_ESP, "$B$%d" % (ESP_R1 + i)), R(S_ESP, "$B$%d" % (ESP_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = ROT
widths(ws_mat, {"A": 11, "B": 24, "C": 15})
for i in range(HAB_N):
    ws_mat.column_dimensions[get_column_letter(MC1 + i)].width = 5.5
ws_mat.column_dimensions[get_column_letter(MC2 + 1)].width = 12
ws_mat.column_dimensions[get_column_letter(MC2 + 2)].width = 13
for i in range(EQ_N):
    r = EQ_R1 + i
    for col, src in ((1, "A"), (2, "B"), (3, "D")):
        c = ws_mat.cell(row=r, column=col, value='=IF(%s="","",%s)' % (
            R(S_EQP, "%s%d" % (src, r)), R(S_EQP, "%s%d" % (src, r))))
        c.font = F_REF; c.border = BORD; c.alignment = LFT if col == 2 else CTR
    nome = EQUIPE[i][1] if i < len(EQUIPE) else None
    for j in range(HAB_N):
        c = ws_mat.cell(row=r, column=MC1 + j)
        c.border = BORD; c.font = F_ENTRADA; c.alignment = CTR; c.number_format = "0"
        if nome and j < len(HABILIDADES):
            c.value = SKILLS[nome][j]
    med = ws_mat.cell(row=r, column=MC2 + 1, value=(
        '=IF($B{r}="","",IFERROR(SUMPRODUCT((Matriz_Esp<>"")*${a}{r}:${b}{r})/'
        'SUMPRODUCT(--(Matriz_Esp<>"")),""))').format(r=r, a=ML1, b=ML2))
    apt = ws_mat.cell(row=r, column=MC2 + 2, value=(
        '=IF($B{r}="","",SUMPRODUCT((Matriz_Esp<>"")*(${a}{r}:${b}{r}>=2)))').format(r=r, a=ML1, b=ML2))
    med.number_format = "0.00"; apt.number_format = "0"
    for cc in (med, apt):
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
ws_mat.freeze_panes = "D2"

# ---------------------------------------------------------------- AUSÊNCIAS
head(ws_aus, 1, ["Técnico", "Tipo", "Data início", "Data fim", "Dias", "Observação",
                 "aux_ativa", "aux_cod"], height=22)
widths(ws_aus, {"A": 24, "B": 15, "C": 13, "D": 13, "E": 8, "F": 34, "G": 10, "H": 8})
for c in ("G", "H"):
    ws_aus.column_dimensions[c].hidden = True
fmt_range(ws_aus, AU_R1, AU_R2, 1, 6, align=CTR)
for i in range(AUS_N):
    r = AU_R1 + i
    ws_aus.cell(row=r, column=1).alignment = LFT; ws_aus.cell(row=r, column=6).alignment = LFT
    ws_aus.cell(row=r, column=3).number_format = "DD/MM/YYYY"
    ws_aus.cell(row=r, column=4).number_format = "DD/MM/YYYY"
    if i < len(AUSENCIAS):
        tec, tipo, ini, fim, obs = AUSENCIAS[i]
        for j, v in enumerate((tec, tipo, ini, fim)):
            ws_aus.cell(row=r, column=1 + j, value=v)
        ws_aus.cell(row=r, column=6, value=obs)
    d = ws_aus.cell(row=r, column=5, value=(
        '=IF(OR($A{r}="",NOT(ISNUMBER($C{r})),NOT(ISNUMBER($D{r}))),"",$D{r}-$C{r}+1)').format(r=r))
    d.border = BORD; d.alignment = CTR; d.number_format = "0"; d.font = F_FORMULA
    g = ws_aus.cell(row=r, column=7, value=(
        '=IF(AND($A{r}<>"",ISNUMBER($C{r}),ISNUMBER($D{r}),$C{r}<=Data_Mapa,$D{r}>=Data_Mapa),$A{r},"")').format(r=r))
    h = ws_aus.cell(row=r, column=8, value=(
        '=IF($A{r}="",0,IFERROR(MATCH($B{r},Aus_Tipos,0),0))').format(r=r))
    for cc in (g, h):
        cc.font = F_FORMULA
ws_aus.freeze_panes = "B2"; ws_aus.auto_filter.ref = "A1:F%d" % AU_R2

dn("Esp_Nome", R(S_ESP, "$B$%d:$B$%d" % (ESP_R1, ESP_R2)))
dn("Esp_Tipo", R(S_ESP, "$C$%d:$C$%d" % (ESP_R1, ESP_R2)))
dn("Esp_Dur",  R(S_ESP, "$D$%d:$D$%d" % (ESP_R1, ESP_R2)))
for nm, col in (("Postos_Cod", "A"), ("Postos_Nome", "B"), ("Postos_Tipo", "C"), ("Postos_Nec", "D"),
                ("Postos_Min", "E"), ("Postos_Prior", "F"), ("Postos_Hab", "G"),
                ("Postos_Func", "H"), ("Postos_Status", "I")):
    dn(nm, R(S_POS, "$%s$%d:$%s$%d" % (col, POS_R1, col, POS_R2)))
for nm, col in (("Equipe_Mat", "A"), ("Equipe_Nome", "B"), ("Equipe_Coren", "C"),
                ("Equipe_Funcao", "D"), ("Equipe_StatusCad", "E"), ("Equipe_Situacao", "F")):
    dn(nm, R(S_EQP, "$%s$%d:$%s$%d" % (col, EQ_R1, col, EQ_R2)))
dn("Matriz_Nome",   R(S_MAT, "$B$%d:$B$%d" % (EQ_R1, EQ_R2)))
dn("Matriz_Niveis", R(S_MAT, "$%s$%d:$%s$%d" % (ML1, EQ_R1, ML2, EQ_R2)))
dn("Matriz_Esp",    R(S_MAT, "$%s$1:$%s$1" % (ML1, ML2)))
for nm, col in (("Aus_Tec", "A"), ("Aus_Tipo", "B"), ("Aus_Ini", "C"), ("Aus_Fim", "D"),
                ("Aus_Ativa", "G"), ("Aus_Cod", "H")):
    dn(nm, R(S_AUS, "$%s$%d:$%s$%d" % (col, AU_R1, col, AU_R2)))

# ---------------------------------------------------------------- CALENDÁRIO DE AUSÊNCIAS
ws_cal["A1"] = "CALENDÁRIO DE AUSÊNCIAS"; ws_cal["A1"].font = F_TIT
c = ws_cal.cell(row=1, column=3, value='=TEXT(Periodo_Ini,"DD/MM/YYYY")&"  a  "&TEXT(Periodo_Ini+%d,"DD/MM/YYYY")' % (DIAS_MES - 1))
c.font = F_SEC; c.alignment = LFT
ws_cal.merge_cells(start_row=1, start_column=3, end_row=1, end_column=10)
ws_cal.cell(row=1, column=12, value=" · ".join("%s = %s" % (sg, tp) for tp, sg in TIPOS_AUS) +
            " · ! = registros sobrepostos").font = F_NOTA
RESUMO_CAL = [("Folgas", "Folga"), ("Férias", "Férias"), ("Atestados", "Atestado")]
SIG = dict(TIPOS_AUS)
head(ws_cal, 2, ["Matrícula", "Nome do técnico"] + [""] * DIAS_MES +
     [r[0] for r in RESUMO_CAL] + ["Dias ausente"], height=26)
widths(ws_cal, {"A": 11, "B": 24})
for d in range(DIAS_MES):
    col = get_column_letter(3 + d)
    ws_cal.column_dimensions[col].width = 4.4
    f = "=Periodo_Ini" if d == 0 else "=%s2+1" % get_column_letter(2 + d)
    cc = ws_cal.cell(row=2, column=3 + d, value=f)
    cc.font = F_HEAD; cc.fill = FILL_HEAD; cc.alignment = CTR; cc.number_format = "D"; cc.border = BORD
    ws_cal.cell(row=3, column=3 + d, value=(
        '=IF({c}2="","",CHOOSE(WEEKDAY({c}2),"dom","seg","ter","qua","qui","sex","sáb"))').format(c=col)
    ).alignment = CTR
    ws_cal.cell(row=3, column=3 + d).font = F_NOTA
for i in range(4):
    ws_cal.column_dimensions[get_column_letter(3 + DIAS_MES + i)].width = 9
DIA1, DIAF = get_column_letter(3), get_column_letter(2 + DIAS_MES)
for i in range(EQ_N):
    r = 4 + i
    for col, src in ((1, "A"), (2, "B")):
        cc = ws_cal.cell(row=r, column=col, value='=IF(%s="","",%s)' % (
            R(S_EQP, "%s%d" % (src, EQ_R1 + i)), R(S_EQP, "%s%d" % (src, EQ_R1 + i))))
        cc.font = F_REF; cc.border = BORD; cc.alignment = LFT if col == 2 else CTR
    for d in range(DIAS_MES):
        col = get_column_letter(3 + d)
        base = '(Aus_Tec=$B{r})*(Aus_Ini<={c}$2)*(Aus_Fim>={c}$2)'.format(r=r, c=col)
        cod = 'SUMPRODUCT(%s*Aus_Cod)' % base
        qtd = 'SUMPRODUCT(%s*(Aus_Cod>0))' % base
        cc = ws_cal.cell(row=r, column=3 + d, value=(
            '=IF(OR($B{r}="",{c}$2=""),"",IF({q}=0,"",IF({q}>1,"!",IFERROR(INDEX(Aus_Siglas,{cod}),"!"))))'
        ).format(r=r, c=col, q=qtd, cod=cod))
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
    for j, sig in enumerate([SIG[t[1]] for t in RESUMO_CAL]):
        cc = ws_cal.cell(row=r, column=3 + DIAS_MES + j, value=(
            '=IF($B{r}="","",COUNTIF(${a}{r}:${b}{r},"{s}"))').format(r=r, a=DIA1, b=DIAF, s=sig))
        cc.border = BORD; cc.alignment = CTR; cc.number_format = "0"; cc.font = F_FORMULA
    cc = ws_cal.cell(row=r, column=3 + DIAS_MES + 3, value=(
        '=IF($B{r}="","",SUMPRODUCT((${a}{r}:${b}{r}<>"")*1))').format(r=r, a=DIA1, b=DIAF))
    cc.border = BORD; cc.alignment = CTR; cc.number_format = "0"; cc.font = F_FORMULA
CAL_FIM = 3 + EQ_N
for j, (rot, nf) in enumerate((("Funcionários na data", "0"), ("Vagas necessárias no dia", "0"),
                               ("Déficit do dia", "0"))):
    r = CAL_FIM + 2 + j
    a = ws_cal.cell(row=r, column=1, value=rot)
    a.font = F_SEC if j == 0 else F_FORMULA; a.alignment = LFT
    ws_cal.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    for d in range(DIAS_MES):
        col = get_column_letter(3 + d)
        if j == 0:
            f = ('=IF({c}$2="","",SUMPRODUCT((Equipe_Nome<>"")*(Equipe_StatusCad="Ativo")*'
                 '(COUNTIFS(Aus_Tec,Equipe_Nome,Aus_Ini,"<="&{c}$2,Aus_Fim,">="&{c}$2)=0)))').format(c=col)
        elif j == 1:
            f = ('=IF({c}$2="","",SUMPRODUCT((Postos_Cod<>"")*(Postos_Status="Ativo")*Postos_Nec*'
                 '((Postos_Func="Todos os dias")+'
                 '((Postos_Func="Seg a Sex")*(WEEKDAY({c}$2,2)<=5)*(COUNTIF(Feriados,{c}$2)=0))+'
                 '((Postos_Func="Seg a Sáb")*(WEEKDAY({c}$2,2)<=6)*(COUNTIF(Feriados,{c}$2)=0)))))').format(c=col)
        else:
            f = '=IF({c}$2="","",MAX(0,{c}{r1}-{c}{r0}))'.format(c=col, r0=CAL_FIM + 2, r1=CAL_FIM + 3)
        cc = ws_cal.cell(row=r, column=3 + d, value=f)
        cc.border = BORD; cc.alignment = CTR; cc.number_format = nf
        cc.font = Font(name="Calibri", size=9, bold=(j != 1))
ws_cal.freeze_panes = "C4"

# ---------------------------------------------------------------- MAPA CIRÚRGICO
head(ws_map, 1, ["Data", "Sala", "Hora início", "Hora fim", "Especialidade", "Tipo",
                 "Procedimento", "Cirurgião", "Porte", "Status", "Duração (min)",
                 "Min. ocupação (dur+limpeza)", "Ordem na sala", "Sala liberada às",
                 "Livre até a próxima (min)", "Alerta",
                 "aux_concat", "aux_relIni", "aux_relFim", "aux_chave", "aux_row"], height=44)
widths(ws_map, {"A": 12, "B": 9, "C": 11, "D": 11, "E": 26, "F": 13, "G": 34, "H": 15, "I": 7,
                "J": 12, "K": 12, "L": 17, "M": 11, "N": 13, "O": 15, "P": 40})
for c in ("Q", "R", "S", "T", "U"):
    ws_map.column_dimensions[c].hidden = True
fmt_range(ws_map, MP_R1, MP_R2, 1, 10, align=CTR)
for i in range(MAPA_N):
    r = MP_R1 + i
    ws_map.cell(row=r, column=1).number_format = "DD/MM/YYYY"
    for c in (3, 4):
        ws_map.cell(row=r, column=c).number_format = "HH:MM"
    for c in (5, 7, 8):
        ws_map.cell(row=r, column=c).alignment = LFT
    if i < len(MAPA):
        m = MAPA[i]
        ws_map.cell(row=r, column=1, value=m["data"]); ws_map.cell(row=r, column=2, value=m["sala"])
        ws_map.cell(row=r, column=3, value=time((m["ini"] // 60) % 24, m["ini"] % 60))
        ws_map.cell(row=r, column=4, value=time((m["fim"] // 60) % 24, m["fim"] % 60))
        ws_map.cell(row=r, column=5, value=m["esp"]); ws_map.cell(row=r, column=7, value=m["proc"])
        ws_map.cell(row=r, column=8, value=m["cir"]); ws_map.cell(row=r, column=9, value=m["porte"])
        ws_map.cell(row=r, column=10, value=m["status"])
    calc = {
        6:  '=IF($E{r}="","",IFERROR(INDEX(Esp_Tipo,MATCH($E{r},Esp_Nome,0)),"—"))',
        11: '=IF(OR($B{r}="",NOT(ISNUMBER($C{r})),NOT(ISNUMBER($D{r}))),"",ROUND(MOD($D{r}-$C{r},1)*1440,0))',
        12: '=IF(NOT(ISNUMBER($K{r})),0,IF(OR($K{r}<=0,$J{r}="Cancelada",$J{r}="Suspensa"),0,$K{r}+Limpeza_Min))',
        18: '=IF(NOT(ISNUMBER($C{r})),0,ROUND(MOD($C{r}-Turno_Ini,1)*1440,0))',
        19: '=IF($L{r}<=0,0,$R{r}+$K{r})',
        21: '=ROW()',
        13: ('=IF($L{r}<=0,"",SUMPRODUCT((Mapa_Sala=$B{r})*(Mapa_Data=$A{r})*(Mapa_MinOcup>0)*'
             '((Mapa_RelIni<$R{r})+((Mapa_RelIni=$R{r})*(Mapa_Row<=$U{r})))))'),
        20: '=IF($M{r}="","",$B{r}&"#"&$M{r})',
        14: '=IF($L{r}<=0,"",MOD(Turno_Ini+($S{r}+Limpeza_Min)/1440,1))',
        15: ('=IF($L{r}<=0,"",MAX(0,IFERROR(INDEX(Mapa_RelIni,MATCH($B{r}&"#"&($M{r}+1),Mapa_Chave,0)),'
             'Turno_Min)-($S{r}+Limpeza_Min)))'),
    }
    for col, f in calc.items():
        cc = ws_map.cell(row=r, column=col, value=f.format(r=r))
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
    ws_map.cell(row=r, column=6).alignment = LFT; ws_map.cell(row=r, column=6).font = F_REF
    for col, nf in ((11, "0"), (12, "0"), (13, "0"), (14, "HH:MM"), (15, "0")):
        ws_map.cell(row=r, column=col).number_format = nf
    aux = (
        '=IF($B{r}="","",'
        'IF(COUNTIF(Postos_Cod,$B{r})=0,"Sala não cadastrada | ","")&'
        'IF(AND(COUNTIF(Postos_Cod,$B{r})>0,IFERROR(INDEX(Postos_Tipo,MATCH($B{r},Postos_Cod,0)),"")<>"Sala cirúrgica"),'
        '"Posto não é sala cirúrgica | ","")&'
        'IF(AND(COUNTIF(Postos_Cod,$B{r})>0,IFERROR(INDEX(Postos_Status,MATCH($B{r},Postos_Cod,0)),"")<>"Ativo"),'
        '"Sala não ativa | ","")&'
        'IF(COUNTIF(Esp_Nome,$E{r})=0,"Especialidade não cadastrada | ","")&'
        'IF(COUNTIF(Lista_StatusCirurgia,$J{r})=0,"Status inválido | ","")&'
        'IF(OR(NOT(ISNUMBER($C{r})),NOT(ISNUMBER($D{r}))),"Horário inválido | ","")&'
        'IFERROR(IF(AND(ISNUMBER($C{r}),ISNUMBER($D{r}),MOD($D{r}-$C{r},1)*1440<=0),"Duração nula ou negativa | ",""),"")&'
        'IF(AND($L{r}>0,OR($R{r}>=Turno_Min,$S{r}>Turno_Min)),"Fora da janela do plantão | ","")&'
        'IF(AND($L{r}>0,SUMPRODUCT((Mapa_Sala=$B{r})*(Mapa_Data=$A{r})*(Mapa_MinOcup>0)*'
        '(Mapa_RelIni<$S{r})*(Mapa_RelFim>$R{r}))>1),"Sobreposição de horário na sala | ","")&'
        'IFERROR(IF(AND(ISNUMBER($K{r}),$K{r}>0,COUNTIF(Esp_Nome,$E{r})>0,'
        '$K{r}>3*INDEX(Esp_Dur,MATCH($E{r},Esp_Nome,0))),"Duração atípica (>3x a média) | ",""),""))'
    ).format(r=r)
    ws_map.cell(row=r, column=17, value=aux).font = F_FORMULA
    pa = ws_map.cell(row=r, column=16, value=(
        '=IF($B{r}="","",IF($Q{r}="","OK",LEFT($Q{r},LEN($Q{r})-3)))').format(r=r))
    pa.border = BORD; pa.alignment = LFT; pa.font = F_FORMULA
ws_map.freeze_panes = "C2"; ws_map.auto_filter.ref = "A1:P%d" % MP_R2

for nm, col in (("Mapa_Data", "A"), ("Mapa_Sala", "B"), ("Mapa_Ini", "C"), ("Mapa_Fim", "D"),
                ("Mapa_Esp", "E"), ("Mapa_Hab", "E"), ("Mapa_Status", "J"), ("Mapa_Dur", "K"),
                ("Mapa_MinOcup", "L"), ("Mapa_Ordem", "M"), ("Mapa_Livre", "O"), ("Mapa_Alerta", "P"),
                ("Mapa_RelIni", "R"), ("Mapa_RelFim", "S"), ("Mapa_Chave", "T"), ("Mapa_Row", "U")):
    dn(nm, R(S_MAP, "$%s$%d:$%s$%d" % (col, MP_R1, col, MP_R2)))

# ---------------------------------------------------------------- CALC_MIX
TOT_C, DISP_C, OCUP_C = HC2 + 1, HC2 + 2, HC2 + 3
TOT_L, DISP_L, OCUP_L = get_column_letter(TOT_C), get_column_letter(DISP_C), get_column_letter(OCUP_C)
head(ws_mix, 1, ["Chave", "Posto", "Tipo", "Habilidade de referência", "Min. agendados"] + [""] * HAB_N +
     ["Total do mix", "Min. do plantão", "Ocupação %"], height=176)
for i in range(HAB_N):
    c = ws_mix.cell(row=1, column=HC1 + i, value='=IF(%s="","",%s)' % (
        R(S_ESP, "$B$%d" % (ESP_R1 + i)), R(S_ESP, "$B$%d" % (ESP_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = ROT
widths(ws_mix, {"A": 10, "B": 9, "C": 15, "D": 32, "E": 12})
for i in range(HAB_N):
    ws_mix.column_dimensions[get_column_letter(HC1 + i)].width = 5.5
for col, w in ((TOT_L, 11), (DISP_L, 12), (OCUP_L, 11)):
    ws_mix.column_dimensions[col].width = w
for i in range(POS_N):
    r = POS_R1 + i
    pr = POS_R1 + i
    vals = {
        1: '=IF($B{r}="","",$B{r})',
        2: '=IF(%s="","",%s)' % (R(S_POS, "$A$%d" % pr), R(S_POS, "$A$%d" % pr)),
        3: '=IF($B{r}="","",IFERROR(INDEX(Postos_Tipo,MATCH($B{r},Postos_Cod,0)),""))',
        4: '=IF($B{r}="","",IFERROR(INDEX(Postos_Hab,MATCH($B{r},Postos_Cod,0)),""))',
        5: ('=IF(OR($B{r}="",$C{r}<>"Sala cirúrgica"),0,'
            'SUMIFS(Mapa_MinOcup,Mapa_Sala,$B{r},Mapa_Data,Data_Mapa))'),
    }
    for col, f in vals.items():
        cc = ws_mix.cell(row=r, column=col, value=f.format(r=r))
        cc.border = BORD; cc.alignment = CTR if col != 4 else LFT; cc.font = F_REF
    ws_mix.cell(row=r, column=5).font = F_FORMULA; ws_mix.cell(row=r, column=5).number_format = "0"
    for j in range(HAB_N):
        col = get_column_letter(HC1 + j)
        f = ('=IF($B{r}="",0,IF(OR($C{r}<>"Sala cirúrgica",$E{r}=0),'
             'IF(AND({c}$1<>"",{c}$1=$D{r}),Turno_Min,0),'
             'IF({c}$1="",0,SUMIFS(Mapa_MinOcup,Mapa_Sala,$B{r},Mapa_Data,Data_Mapa,Mapa_Hab,{c}$1))))'
             ).format(r=r, c=col)
        cc = ws_mix.cell(row=r, column=HC1 + j, value=f)
        cc.border = BORD; cc.alignment = CTR; cc.number_format = "0"; cc.font = F_FORMULA
    for col, f, nf in ((TOT_C, '=IF($B{r}="",0,SUM({a}{r}:{b}{r}))'.format(r=r, a=HL1, b=HL2), "0"),
                       (DISP_C, '=IF($B{r}="",0,Turno_Min)'.format(r=r), "0"),
                       (OCUP_C, '=IF(OR($B{r}="",$C{r}<>"Sala cirúrgica"),"",$E{r}/Turno_Min)'.format(r=r), "0.0%")):
        cc = ws_mix.cell(row=r, column=col, value=f)
        cc.border = BORD; cc.alignment = CTR; cc.number_format = nf; cc.font = F_FORMULA
ws_mix.freeze_panes = "F2"
dn("Mix_Esp", R(S_MIX, "$%s$1:$%s$1" % (HL1, HL2)))

# ---------------------------------------------------------------- CALC_AFINIDADE
head(ws_afi, 1, ["Matrícula", "Nome do técnico", "Situação na data"] + [""] * POS_N, height=96)
for i in range(POS_N):
    c = ws_afi.cell(row=1, column=4 + i, value='=IF(%s="","",%s)' % (
        R(S_MIX, "$B$%d" % (POS_R1 + i)), R(S_MIX, "$B$%d" % (POS_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = ROT
widths(ws_afi, {"A": 11, "B": 24, "C": 16})
for i in range(POS_N):
    ws_afi.column_dimensions[get_column_letter(4 + i)].width = 7
for i in range(EQ_N):
    r = EQ_R1 + i
    a = ws_afi.cell(row=r, column=1, value='=IF(%s="","",%s)' % (R(S_MAT, "A%d" % r), R(S_MAT, "A%d" % r)))
    b = ws_afi.cell(row=r, column=2, value='=IF(%s="","",%s)' % (R(S_MAT, "B%d" % r), R(S_MAT, "B%d" % r)))
    c = ws_afi.cell(row=r, column=3, value=(
        '=IF($A{r}="","",IFERROR(INDEX(Equipe_Situacao,MATCH($B{r},Equipe_Nome,0)),"?"))').format(r=r))
    for cc in (a, b, c):
        cc.border = BORD; cc.font = F_REF; cc.alignment = CTR
    b.alignment = LFT
    for j in range(POS_N):
        mr = POS_R1 + j
        mixrow = R(S_MIX, "$%s$%d:$%s$%d" % (HL1, mr, HL2, mr))
        matrow = R(S_MAT, "$%s%d:$%s%d" % (ML1, r, ML2, r))
        tot = R(S_MIX, "$%s$%d" % (TOT_L, mr))
        f = ('=IF(OR($B{r}="",$C{r}<>"Disponível",{t}=0,'
             'COUNTIF(Esc_Tec1,$B{r})+COUNTIF(Esc_Tec2,$B{r})>0,SUMPRODUCT({mx},{mt})=0),"",'
             'SUMPRODUCT({mx},{mt})/{t}+ROW()*0.000001)').format(r=r, t=tot, mx=mixrow, mt=matrow)
        cc = ws_afi.cell(row=r, column=4 + j, value=f)
        cc.border = BORD; cc.alignment = CTR; cc.number_format = "0.00"; cc.font = F_FORMULA
ws_afi.freeze_panes = "D2"

# ---------------------------------------------------------------- ESCALA DO DIA
ESC_HDR = ["Data", "Posto", "Nome do posto", "Tipo", "Prioridade", "Necessários hoje",
           "Nº cirurgias", "Min. ocupação", "Ocupação %", "TÉCNICO 1 (circulante)",
           "Cadastro / situação", "Afinidade 1", "TÉCNICO 2 (instrumentador)",
           "Cadastro / situação", "Afinidade 2", "AFINIDADE DO POSTO", "Cobertura",
           "Classificação", "Chk duplicidade", "Chk disponibilidade", "Chk função",
           "Chk inaptidão", "ALERTAS", "aux_concat", "aux_afin", "aux_peso"]
head(ws_esc, 1, ESC_HDR, height=52)
widths(ws_esc, {"A": 11, "B": 9, "C": 26, "D": 15, "E": 10, "F": 11, "G": 12, "H": 12, "I": 11,
                "J": 24, "K": 24, "L": 11, "M": 24, "N": 24, "O": 11, "P": 13, "Q": 20, "R": 14,
                "S": 26, "T": 28, "U": 24, "V": 26, "W": 58, "X": 8, "Y": 8, "Z": 8})
for col in ("S", "T", "U", "V", "X", "Y", "Z"):
    ws_esc.column_dimensions[col].hidden = True
for i in range(POS_N):
    r = POS_R1 + i
    mixrow = R(S_MIX, "$%s%d:$%s%d" % (HL1, r, HL2, r))
    tot = R(S_MIX, "$%s%d" % (TOT_L, r))
    nal = '(--($J{r}<>"")+--($M{r}<>""))'.format(r=r)
    f = {
        "A": '=IF($B{r}="","",Data_Mapa)',
        "B": '=IF(%s="","",%s)' % (R(S_MIX, "$B%d" % r), R(S_MIX, "$B%d" % r)),
        "C": '=IF($B{r}="","",IFERROR(INDEX(Postos_Nome,MATCH($B{r},Postos_Cod,0)),""))',
        "D": '=IF($B{r}="","",%s)' % R(S_MIX, "$C%d" % r),
        "E": '=IF($B{r}="","",IFERROR(INDEX(Postos_Prior,MATCH($B{r},Postos_Cod,0)),""))',
        "F": ('=IF($B{r}="","",IF(OR(IFERROR(INDEX(Postos_Status,MATCH($B{r},Postos_Cod,0)),"")<>"Ativo",'
              'AND(IFERROR(INDEX(Postos_Func,MATCH($B{r},Postos_Cod,0)),"")="Seg a Sex",'
              'OR(WEEKDAY(Data_Mapa,2)>5,COUNTIF(Feriados,Data_Mapa)>0)),'
              'AND(IFERROR(INDEX(Postos_Func,MATCH($B{r},Postos_Cod,0)),"")="Seg a Sáb",'
              'OR(WEEKDAY(Data_Mapa,2)>6,COUNTIF(Feriados,Data_Mapa)>0))),0,'
              'IFERROR(INDEX(Postos_Nec,MATCH($B{r},Postos_Cod,0)),0)))'),
        "G": ('=IF(OR($B{r}="",$D{r}<>"Sala cirúrgica"),"",'
              'COUNTIFS(Mapa_Sala,$B{r},Mapa_Data,Data_Mapa,Mapa_MinOcup,">0"))'),
        "H": '=IF(OR($B{r}="",$D{r}<>"Sala cirúrgica"),"",%s)' % R(S_MIX, "$E%d" % r),
        "I": '=IF(OR($B{r}="",$D{r}<>"Sala cirúrgica"),"",%s)' % R(S_MIX, "$%s%d" % (OCUP_L, r)),
        "K": ('=IF($J{r}="","",IFERROR(INDEX(Equipe_Funcao,MATCH($J{r},Equipe_Nome,0))&" · "&'
              'INDEX(Equipe_Situacao,MATCH($J{r},Equipe_Nome,0)),"NÃO CADASTRADO"))'),
        "N": ('=IF($M{r}="","",IFERROR(INDEX(Equipe_Funcao,MATCH($M{r},Equipe_Nome,0))&" · "&'
              'INDEX(Equipe_Situacao,MATCH($M{r},Equipe_Nome,0)),"NÃO CADASTRADO"))'),
        # ramifica pela AFINIDADE (e não pelo nome): técnico não cadastrado devolve afinidade vazia
        "P": ('=IF(OR($B{r}="",AND($L{r}="",$O{r}="")),"",IF($O{r}="",$L{r},IF($L{r}="",$O{r},'
              'IF($D{r}="Sala cirúrgica",Peso_Circulante*$L{r}+Peso_Instrumentador*$O{r},($L{r}+$O{r})/2))))'),
        "Q": ('=IF($B{r}="","",IF($F{r}=0,IF({n}=0,"NÃO OPERA HOJE","EXTRA — não opera hoje"),'
              'IF({n}=0,"DESCOBERTO",IF({n}>=$F{r},"COMPLETO",'
              '"INCOMPLETO ("&{n}&" de "&$F{r}&")"))))').replace("{n}", nal),
        "R": ('=IF($B{r}="","",IF($Q{r}="NÃO OPERA HOJE","—",IF($Q{r}="DESCOBERTO","SEM EQUIPE",'
              'IF($P{r}="","—",IF($P{r}>=Afinidade_Meta,"ADEQUADO",'
              'IF($P{r}>=Afinidade_Min,"ATENÇÃO","CRÍTICO"))))))'),
        "S": ('=IF($B{r}="","",IF(OR(AND($J{r}<>"",COUNTIF(Esc_Tec1,$J{r})+COUNTIF(Esc_Tec2,$J{r})>1),'
              'AND($M{r}<>"",COUNTIF(Esc_Tec1,$M{r})+COUNTIF(Esc_Tec2,$M{r})>1)),'
              '"Técnico escalado em mais de um posto","OK"))'),
        "T": ('=IF($B{r}="","",IF(OR(AND($J{r}<>"",IFERROR(INDEX(Equipe_Situacao,MATCH($J{r},Equipe_Nome,0)),"?")<>"Disponível"),'
              'AND($M{r}<>"",IFERROR(INDEX(Equipe_Situacao,MATCH($M{r},Equipe_Nome,0)),"?")<>"Disponível")),'
              '"Técnico indisponível ou não cadastrado","OK"))'),
        "U": ('=IF($B{r}="","",IF($D{r}<>"Sala cirúrgica","OK",'
              'IF(OR(AND($J{r}<>"",IFERROR(INDEX(Equipe_Funcao,MATCH($J{r},Equipe_Nome,0)),"")="Instrumentador"),'
              'AND($M{r}<>"",IFERROR(INDEX(Equipe_Funcao,MATCH($M{r},Equipe_Nome,0)),"")="Circulante")),'
              '"Função incompatível com o posto","OK")))'),
        "V": ('=IF($B{r}="","",IF(OR({t}=0,AND($J{r}="",$M{r}="")),"OK",'
              'IF(IF($J{r}="",0,IFERROR(SUMPRODUCT(({mx}/{t}>=Part_Min_Critica)*'
              '(INDEX(Matriz_Niveis,MATCH($J{r},Matriz_Nome,0),0)<=Nivel_Critico)),0))+'
              'IF($M{r}="",0,IFERROR(SUMPRODUCT(({mx}/{t}>=Part_Min_Critica)*'
              '(INDEX(Matriz_Niveis,MATCH($M{r},Matriz_Nome,0),0)<=Nivel_Critico)),0))>0,'
              '"Inaptidão em especialidade relevante","OK")))').replace("{mx}", mixrow).replace("{t}", tot),
        "X": ('=IF($B{r}="","",'
              'IF($Q{r}="DESCOBERTO",IF(N($G{r})>0,"POSTO DESCOBERTO — "&$G{r}&" cirurgia(s) a remanejar | ",'
              '"POSTO DESCOBERTO | "),"")&'
              'IF(AND($Q{r}="NÃO OPERA HOJE",N($G{r})>0),"Posto não opera hoje e tem "&$G{r}&" cirurgia(s) | ","")&'
              'IF(LEFT($Q{r},5)="EXTRA","Técnico escalado em posto que não opera hoje | ","")&'
              'IF(LEFT($Q{r},10)="INCOMPLETO","Equipe incompleta para o posto | ","")&'
              'IF($S{r}<>"OK",$S{r}&" | ","")&IF($T{r}<>"OK",$T{r}&" | ","")&'
              'IF($U{r}<>"OK",$U{r}&" | ","")&IF($V{r}<>"OK",$V{r}&" | ","")&'
              'IF(AND($P{r}<>"",$P{r}<Afinidade_Min),"Afinidade abaixo do mínimo | ","")&'
              'IF(AND($I{r}<>"",$I{r}>Ocupacao_Max),"Ocupação acima do limite | ","")&'
              'IF(AND($D{r}="Sala cirúrgica",IFERROR(INDEX(Postos_Status,MATCH($B{r},Postos_Cod,0)),"")<>"Ativo",'
              'N($G{r})>0),"Sala inativa com cirurgia | ",""))'),
        "W": '=IF($B{r}="","",IF($X{r}="","OK",LEFT($X{r},LEN($X{r})-3)))',
        "Y": '=IF($P{r}="",0,$P{r})',
        "Z": '=IF($P{r}="",0,1)',
    }
    for tgt, key in (("L", "J"), ("O", "M")):
        f[tgt] = ('=IF(OR($B{r}="",${k}{r}=""),"",IFERROR(SUMPRODUCT({mx},'
                  'INDEX(Matriz_Niveis,MATCH(${k}{r},Matriz_Nome,0),0))/{t},""))').format(
            r=r, k=key, mx=mixrow, t=tot)
    for col, formula in f.items():
        cell = ws_esc[col + str(r)]
        cell.value = formula.format(r=r) if "{r}" in formula else formula
        cell.border = BORD; cell.font = F_FORMULA; cell.alignment = CTR
    for col in ("C", "K", "N", "Q", "S", "T", "U", "V"):
        ws_esc[col + str(r)].alignment = LFT
    ws_esc["W" + str(r)].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_esc.row_dimensions[r].height = 28
    ws_esc["A%d" % r].number_format = "DD/MM/YYYY"
    ws_esc["I%d" % r].number_format = "0.0%"
    for col in ("L", "O", "P", "Y"):
        ws_esc[col + str(r)].number_format = "0.00"
    for col in ("E", "F", "G", "H", "Z"):
        ws_esc[col + str(r)].number_format = "0"
    for col in ("C", "D", "K", "N"):
        ws_esc[col + str(r)].font = F_REF
    for col in ("J", "M"):
        cc = ws_esc[col + str(r)]
        cc.font = F_ENTRADA; cc.fill = FILL_ENT; cc.alignment = LFT
    if i < len(POSTOS):
        cod = POSTOS[i][0]
        if cod in ALOC:
            if 1 in ALOC[cod]: ws_esc["J%d" % r] = ALOC[cod][1]
            if 2 in ALOC[cod]: ws_esc["M%d" % r] = ALOC[cod][2]
ws_esc.freeze_panes = "D2"; ws_esc.auto_filter.ref = "A1:W%d" % POS_R2

for nm, col in (("Esc_Posto", "B"), ("Esc_Tipo", "D"), ("Esc_Nec", "F"), ("Esc_NCir", "G"),
                ("Esc_MinOcup", "H"), ("Esc_Ocup", "I"), ("Esc_Tec1", "J"), ("Esc_Tec2", "M"),
                ("Esc_Afin", "P"), ("Esc_Cobertura", "Q"), ("Esc_Class", "R"),
                ("Esc_Alertas", "W"), ("Esc_AfinNum", "Y"), ("Esc_Peso", "Z")):
    dn(nm, R(S_ESC, "$%s$%d:$%s$%d" % (col, POS_R1, col, POS_R2)))

# ---------------------------------------------------------------- SUGESTÃO DE TÉCNICOS
SUG_HDR = ["Posto", "Nome do posto", "Especialidade predominante", "Cobertura atual"]
for k in range(1, 5):
    SUG_HDR += ["%dª opção (técnico livre)" % k, "Cadastro / situação", "Afinidade"]
head(ws_sug, 1, SUG_HDR, height=32)
widths(ws_sug, {"A": 9, "B": 26, "C": 32, "D": 20, "E": 22, "F": 22, "G": 10, "H": 22, "I": 22,
                "J": 10, "K": 22, "L": 22, "M": 10, "N": 22, "O": 22, "P": 10})
for i in range(POS_N):
    r = POS_R1 + i
    afi_col = get_column_letter(4 + i)
    rng = R(S_AFI, "%s$%d:%s$%d" % (afi_col, EQ_R1, afi_col, EQ_R2))
    mixrow = R(S_MIX, "$%s%d:$%s%d" % (HL1, r, HL2, r))
    tot = R(S_MIX, "$%s%d" % (TOT_L, r))
    vals = {
        "A": '=IF(%s="","",%s)' % (R(S_ESC, "$B%d" % r), R(S_ESC, "$B%d" % r)),
        "B": '=IF($A{r}="","",%s)' % R(S_ESC, "$C%d" % r),
        "C": ('=IF($A{r}="","",IF({t}=0,"—",IFERROR(INDEX(Mix_Esp,MATCH(MAX({mx}),{mx},0)),"—")))'
              ).replace("{mx}", mixrow).replace("{t}", tot),
        "D": '=IF($A{r}="","",%s)' % R(S_ESC, "$Q%d" % r),
    }
    for k in range(4):
        cn, cf, ca = get_column_letter(5 + k*3), get_column_letter(6 + k*3), get_column_letter(7 + k*3)
        vals[cn] = ('=IF($A{r}="","",IFERROR(INDEX({nomes},MATCH(LARGE({rng},{k}),{rng},0)),"—"))').format(
            r=r, nomes=R(S_AFI, "$B$%d:$B$%d" % (EQ_R1, EQ_R2)), rng=rng, k=k+1)
        vals[cf] = ('=IF(OR($A{r}="",{cn}{r}="—"),"",IFERROR(INDEX(Equipe_Funcao,MATCH({cn}{r},Equipe_Nome,0))&" · "&'
                    'INDEX(Equipe_Situacao,MATCH({cn}{r},Equipe_Nome,0)),""))').format(cn=cn, r=r)
        vals[ca] = '=IF($A{r}="","",IFERROR(ROUND(LARGE({rng},{k}),2),""))'.format(r=r, rng=rng, k=k+1)
    for col, formula in vals.items():
        cell = ws_sug[col + str(r)]
        cell.value = formula.format(r=r) if "{r}" in formula else formula
        cell.border = BORD; cell.font = F_FORMULA; cell.alignment = CTR
    for col in ("B", "C", "D", "E", "F", "H", "I", "K", "L", "N", "O"):
        ws_sug[col + str(r)].alignment = LFT; ws_sug[col + str(r)].font = F_REF
    for k in range(4):
        ws_sug[get_column_letter(7 + k*3) + str(r)].number_format = "0.00"
ws_sug.freeze_panes = "C2"; ws_sug.auto_filter.ref = "A1:P%d" % POS_R2

# ---------------------------------------------------------------- JOGO DE SALA
head(ws_jog, 1, ["Sala", "Janela nº", "Livre a partir de", "Livre até", "Duração (min)",
                 "Cabe cirurgia de até (min)", "Situação", "aux_ini", "aux_fim"], height=32)
widths(ws_jog, {"A": 9, "B": 10, "C": 16, "D": 14, "E": 13, "F": 20, "G": 24, "H": 9, "I": 9})
for c in ("H", "I"):
    ws_jog.column_dimensions[c].hidden = True
JOG_R1 = 2
for pi in range(POS_N):
    pr = POS_R1 + pi
    for k in range(JOGO_K):
        r = JOG_R1 + pi * JOGO_K + k
        a = ws_jog.cell(row=r, column=1, value=(
            '=IF(OR({b}="",{t}<>"Sala cirúrgica"),"",{b})').format(
            b=R(S_MIX, "$B%d" % pr), t=R(S_MIX, "$C%d" % pr)))
        ws_jog.cell(row=r, column=2, value=k)
        if k == 0:
            h = '=IF($A{r}="","",0)'.format(r=r)
        else:
            h = ('=IF(OR($A{r}="",ISERROR(MATCH($A{r}&"#{k}",Mapa_Chave,0))),"",'
                 'INDEX(Mapa_RelFim,MATCH($A{r}&"#{k}",Mapa_Chave,0))+Limpeza_Min)').format(r=r, k=k)
        ws_jog.cell(row=r, column=8, value=h)
        ws_jog.cell(row=r, column=9, value=(
            '=IF($H{r}="","",IFERROR(INDEX(Mapa_RelIni,MATCH($A{r}&"#{k1}",Mapa_Chave,0)),Turno_Min))'
        ).format(r=r, k1=k+1))
        vals = {
            5: '=IF($H{r}="","",MAX(0,$I{r}-$H{r}))',
            3: '=IF(OR($E{r}="",$E{r}=0),"",MOD(Turno_Ini+$H{r}/1440,1))',
            4: '=IF(OR($E{r}="",$E{r}=0),"",MOD(Turno_Ini+$I{r}/1440,1))',
            6: '=IF(OR($E{r}="",$E{r}=0),"",MAX(0,$E{r}-Limpeza_Min))',
            7: ('=IF($E{r}="","",IF($E{r}=0,"Sem intervalo",IF($E{r}>=Janela_Min,'
                '"Janela aproveitável","Janela curta")))'),
        }
        for col, f in vals.items():
            cc = ws_jog.cell(row=r, column=col, value=f.format(r=r))
            cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
        for col, nf in ((3, "HH:MM"), (4, "HH:MM"), (5, "0"), (6, "0")):
            ws_jog.cell(row=r, column=col).number_format = nf
        ws_jog.cell(row=r, column=7).alignment = LFT
        for col in (1, 2):
            cc = ws_jog.cell(row=r, column=col); cc.border = BORD; cc.alignment = CTR; cc.font = F_REF
JOG_R2 = JOG_R1 + POS_N * JOGO_K - 1
ws_jog.freeze_panes = "A2"; ws_jog.auto_filter.ref = "A1:G%d" % JOG_R2
ws_jog.cell(row=JOG_R2 + 2, column=1,
            value="Janela 0 é o tempo livre antes da primeira cirurgia; as demais são o intervalo entre a liberação "
                  "de uma cirurgia (fim + limpeza) e o início da seguinte; a última vai até o fim do plantão. "
                  "'Cabe cirurgia de até' já desconta a limpeza do encaixe. Use o filtro da coluna Situação para ver "
                  "só as janelas aproveitáveis.").font = F_NOTA
dn("Jogo_Sala", R(S_JOG, "$A$%d:$A$%d" % (JOG_R1, JOG_R2)))
dn("Jogo_Dur",  R(S_JOG, "$E$%d:$E$%d" % (JOG_R1, JOG_R2)))
dn("Jogo_Cabe", R(S_JOG, "$F$%d:$F$%d" % (JOG_R1, JOG_R2)))

# ---------------------------------------------------------------- PAINEL
title(ws_pai, "PAINEL DO CENTRO CIRÚRGICO — ESCALA DIÁRIA",
      "Camada executiva. Tudo vem de fórmulas vivas sobre Mapa_Cirurgico, Ausencias e Escala_Dia.")
widths(ws_pai, {"A": 30, "B": 26, "C": 15, "D": 15, "E": 15, "F": 15, "G": 16, "H": 44, "I": 3})

def bloco(row, texto):
    ws_pai.cell(row=row, column=1, value=texto).font = F_SEC

def kpi_row(row, valores, formatos, fill=True):
    for j, (v, nf) in enumerate(zip(valores, formatos)):
        c = ws_pai.cell(row=row, column=1 + j, value=v)
        c.number_format = nf; c.border = BORD; c.alignment = CTR
        c.font = Font(name="Calibri", size=12, bold=True, color=AZ_ESC)
        if fill: c.fill = FILL_ENT
    ws_pai.row_dimensions[row].height = 26

bloco(4, "1. INDICADORES DO DIA")
head(ws_pai, 5, ["Data da escala", "Cirurgias programadas", "Canceladas / suspensas",
                 "Horas cirúrgicas", "Ocupação média das salas", "Afinidade média dos postos",
                 "Postos com alerta", "Vagas cobertas"], height=32)
kpi_row(6, ["=Data_Mapa",
            '=COUNTIFS(Mapa_MinOcup,">0",Mapa_Data,Data_Mapa)',
            '=COUNTIFS(Mapa_Status,"Cancelada",Mapa_Data,Data_Mapa)+COUNTIFS(Mapa_Status,"Suspensa",Mapa_Data,Data_Mapa)',
            '=SUMIFS(Mapa_Dur,Mapa_MinOcup,">0",Mapa_Data,Data_Mapa)/60',
            '=IFERROR(SUMIFS(Esc_MinOcup,Esc_Tipo,"Sala cirúrgica")/(COUNTIF(Esc_Tipo,"Sala cirúrgica")*Turno_Min),"")',
            '=IFERROR(SUMPRODUCT(Esc_AfinNum,Esc_Peso)/SUM(Esc_Peso),"")',
            '=SUMPRODUCT((Esc_Alertas<>"OK")*(Esc_Alertas<>""))',
            '=SUMPRODUCT((Esc_Tec1<>"")*1)+SUMPRODUCT((Esc_Tec2<>"")*1)'],
        ["DD/MM/YYYY", "0", "0", "0.0", "0.0%", "0.00", "0", "0"])

bloco(8, "2. COBERTURA DE PESSOAL — o déficit do dia")
head(ws_pai, 9, ["Técnicos no quadro", "Ausentes hoje", "DISPONÍVEIS hoje", "Vagas necessárias",
                 "DÉFICIT DE TÉCNICOS", "Postos descobertos", "Cirurgias a remanejar",
                 "Reserva (disponíveis sem posto)"], height=32)
kpi_row(10, ['=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_StatusCad="Ativo"))',
             '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_StatusCad="Ativo")*(Equipe_Situacao<>"Disponível"))',
             '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Situacao="Disponível"))',
             '=SUM(Esc_Nec)',
             '=MAX(0,$D$10-$C$10)',
             '=COUNTIF(Esc_Cobertura,"DESCOBERTO")',
             '=SUMIFS(Esc_NCir,Esc_Cobertura,"DESCOBERTO")',
             '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Situacao="Disponível")*'
             '((COUNTIF(Esc_Tec1,Equipe_Nome)+COUNTIF(Esc_Tec2,Equipe_Nome))=0))'],
        ["0", "0", "0", "0", "0", "0", "0", "0"])

B3_R1 = 14
B4_LBL = B3_R1 + len(TIPOS_AUS) + 1
B4_R1 = B4_LBL + 2
B5_LBL = B4_R1 + POS_N + 1
B5_R1 = B5_LBL + 2
B6_LBL = B5_R1 + HAB_N + 1
B6_R1 = B6_LBL + 2
bloco(12, "3. AUSÊNCIAS")
head(ws_pai, 13, ["Tipo", "Técnicos ausentes hoje", "Dias no mês"], height=20)
for i, (tipo, sig) in enumerate(TIPOS_AUS):
    r = B3_R1 + i
    a = ws_pai.cell(row=r, column=1, value="=%s" % R(S_PAR, "$A$%d" % (38 + i)))
    b = ws_pai.cell(row=r, column=2, value='=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Situacao=$A%d))' % r)
    c = ws_pai.cell(row=r, column=3, value='=COUNTIF(%s,%s)' % (
        R(S_CAL, "$C$4:$%s$%d" % (get_column_letter(2 + DIAS_MES), 3 + EQ_N)),
        R(S_PAR, "$B$%d" % (38 + i))))
    for cc in (a, b, c):
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
    a.alignment = LFT
    b.number_format = "0"; c.number_format = "0"

bloco(B4_LBL, "4. SITUAÇÃO POR POSTO")
head(ws_pai, B4_LBL + 1, ["Posto", "Nome do posto", "Nº cirurgias", "Ocupação", "Cobertura",
                  "Afinidade", "Classificação", "Alertas"], height=30)
for i in range(POS_N):
    r, er = B4_R1 + i, POS_R1 + i
    for col, src, nf in ((1, "B", None), (2, "C", None), (3, "G", "0"), (4, "I", "0.0%"),
                         (5, "Q", None), (6, "P", "0.00"), (7, "R", None), (8, "W", None)):
        cc = ws_pai.cell(row=r, column=col, value='=IF(%s="","",%s)' % (
            R(S_ESC, "$%s%d" % (src, er)), R(S_ESC, "$%s%d" % (src, er))))
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
        if nf: cc.number_format = nf
    for col in (2, 5, 8):
        ws_pai.cell(row=r, column=col).alignment = LFT

bloco(B5_LBL, "5. DEMANDA × CAPACIDADE POR ESPECIALIDADE")
head(ws_pai, B5_LBL + 1, ["Especialidade", "Nº cirurgias", "Horas cirúrgicas", "% das horas",
                  "Aptos no quadro (≥2)", "APTOS DISPONÍVEIS hoje", "Cobertura"], height=32)
for i in range(HAB_N):
    r, hr = B5_R1 + i, ESP_R1 + i
    mcol = get_column_letter(MC1 + i)
    mrng = R(S_MAT, "$%s$%d:$%s$%d" % (mcol, EQ_R1, mcol, EQ_R2))
    fs = {
        1: '=IF(%s="","",%s)' % (R(S_ESP, "$B$%d" % hr), R(S_ESP, "$B$%d" % hr)),
        2: '=IF($A{r}="","",COUNTIFS(Mapa_Hab,$A{r},Mapa_MinOcup,">0",Mapa_Data,Data_Mapa))'.format(r=r),
        3: '=IF($A{r}="","",SUMIFS(Mapa_Dur,Mapa_Hab,$A{r},Mapa_MinOcup,">0",Mapa_Data,Data_Mapa)/60)'.format(r=r),
        4: '=IF(OR($A{r}="",SUM($C${p1}:$C${last})=0),"",$C{r}/SUM($C${p1}:$C${last}))'.format(r=r, p1=B5_R1, last=B5_R1 + HAB_N - 1),
        5: '=IF($A{r}="","",SUMPRODUCT((Equipe_StatusCad="Ativo")*({m}>=2)))'.format(r=r, m=mrng),
        6: '=IF($A{r}="","",SUMPRODUCT((Equipe_Situacao="Disponível")*({m}>=2)))'.format(r=r, m=mrng),
        7: '=IF($A{r}="","",IF($F{r}>=2,"OK",IF($F{r}=1,"LIMITE","SEM COBERTURA")))'.format(r=r),
    }
    for col, v in fs.items():
        cc = ws_pai.cell(row=r, column=col, value=v)
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
    ws_pai.cell(row=r, column=1).alignment = LFT
    ws_pai.cell(row=r, column=3).number_format = "0.0"
    ws_pai.cell(row=r, column=4).number_format = "0.0%"

bloco(B6_LBL, "6. JOGO DE SALA — espaço para encaixe")
head(ws_pai, B6_LBL + 1, ["Sala", "Minutos livres no plantão", "Maior janela livre (min)",
                  "Cabe cirurgia de até (min)", "Janelas aproveitáveis", "Ocupação"], height=32)
for i in range(POS_N):
    r, er = B6_R1 + i, POS_R1 + i
    j1, j2 = JOG_R1 + i * JOGO_K, JOG_R1 + i * JOGO_K + JOGO_K - 1
    blocoE = R(S_JOG, "$E$%d:$E$%d" % (j1, j2))
    blocoF = R(S_JOG, "$F$%d:$F$%d" % (j1, j2))
    blocoG = R(S_JOG, "$G$%d:$G$%d" % (j1, j2))
    fs = {
        1: '=IF(%s="","",%s)' % (R(S_JOG, "$A$%d" % j1), R(S_JOG, "$A$%d" % j1)),
        2: '=IF($A{r}="","",SUM({e}))'.format(r=r, e=blocoE),
        3: '=IF($A{r}="","",MAX({e}))'.format(r=r, e=blocoE),
        4: '=IF($A{r}="","",MAX({f}))'.format(r=r, f=blocoF),
        5: '=IF($A{r}="","",COUNTIF({g},"Janela aproveitável"))'.format(r=r, g=blocoG),
        6: '=IF($A{r}="","",%s)' % R(S_ESC, "$I%d" % er),
    }
    for col, v in fs.items():
        cc = ws_pai.cell(row=r, column=col, value=v.format(r=r) if "{r}" in v else v)
        cc.border = BORD; cc.alignment = CTR; cc.font = F_FORMULA
        if col in (2, 3, 4, 5): cc.number_format = "0"
    ws_pai.cell(row=r, column=6).number_format = "0.0%"

CHECK_ROW = B6_R1 + POS_N + 1
bloco(CHECK_ROW, "7. VERIFICAÇÕES DE INTEGRIDADE")
head(ws_pai, CHECK_ROW + 1, ["Verificação", "", "Resultado", "", "", "", "", ""], height=20)
CHECKS = [
    ("Soma dos pesos de afinidade = 1,00",
     '=IF(ROUND(Peso_Circulante+Peso_Instrumentador,6)=1,"OK","ERRO: os pesos não somam 1,00")'),
    ("Colunas de especialidade alinhadas (Matriz × Calc_Mix)",
     '=IF(SUMPRODUCT(--(Matriz_Esp=Mix_Esp))=%d,"OK","ERRO: colunas desalinhadas")' % HAB_N),
    ("Nomes duplicados no cadastro da equipe",
     '=IF(SUMPRODUCT((Equipe_Nome<>"")*1)-SUMPRODUCT((Equipe_Nome<>"")/COUNTIF(Equipe_Nome,Equipe_Nome&""))>0.0001,'
     '"ERRO: há nomes repetidos na aba Equipe","OK")'),
    ("Registros de ausência sobrepostos (marcados com ! no calendário)",
     '=COUNTIF(%s,"!")' % R(S_CAL, "$C$4:$%s$%d" % (get_column_letter(2 + DIAS_MES), 3 + EQ_N))),
    ("Ausências com técnico fora do cadastro",
     '=SUMPRODUCT((Aus_Tec<>"")*(COUNTIF(Equipe_Nome,Aus_Tec)=0))'),
    ("Ausências com data fim anterior ao início",
     '=SUMPRODUCT((Aus_Tec<>"")*(Aus_Fim<Aus_Ini))'),
    ("Cirurgias com alerta no mapa", '=SUMPRODUCT((Mapa_Alerta<>"OK")*(Mapa_Alerta<>""))'),
    ("Postos descobertos", '=COUNTIF(Esc_Cobertura,"DESCOBERTO")'),
    ("Postos com equipe incompleta", '=SUMPRODUCT((LEFT(Esc_Cobertura,10)="INCOMPLETO")*1)'),
    ("Postos classificados como CRÍTICO", '=COUNTIF(Esc_Class,"CRÍTICO")'),
    ("Técnicos escalados em mais de um posto",
     '=SUMPRODUCT((Esc_Tec1<>"")*(COUNTIF(Esc_Tec1,Esc_Tec1)+COUNTIF(Esc_Tec2,Esc_Tec1)>1))'),
    ("Matriz de habilidades calibrada (níveis diferentes entre si)",
     '=IF(COUNT(Matriz_Niveis)=0,"PENDENTE: matriz vazia",'
     'IF(MAX(Matriz_Niveis)=MIN(Matriz_Niveis),'
     '"PENDENTE: todos com o mesmo nível — preencher a Matriz_Habilidades","OK"))'),
    ("Postos / especialidades / técnicos no quadro",
     '=COUNTA(Postos_Cod)&" / "&COUNTA(Esp_Nome)&" / "&COUNTA(Equipe_Nome)'),
]
for i, (lbl, f) in enumerate(CHECKS):
    r = CHECK_ROW + 2 + i
    c1 = ws_pai.cell(row=r, column=1, value=lbl); c1.border = BORD; c1.alignment = LFT; c1.font = F_FORMULA
    ws_pai.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    c2 = ws_pai.cell(row=r, column=3, value=f); c2.border = BORD; c2.font = F_FORMULA
    c2.alignment = Alignment(horizontal="left", vertical="center", indent=1)
CHECK_LAST = CHECK_ROW + 1 + len(CHECKS)

# ---------------------------------------------------------------- BASE HISTÓRICO
head(ws_his, 1, ["Data", "Posto", "Nome do posto", "Técnico 1", "Técnico 2", "Afinidade",
                 "Cobertura", "Nº cirurgias", "Min. ocupação", "Ocupação %", "Classificação",
                 "Alertas", "Déficit do dia"])
widths(ws_his, {"A": 12, "B": 9, "C": 26, "D": 24, "E": 24, "F": 11, "G": 20, "H": 11, "I": 13,
                "J": 11, "K": 14, "L": 50, "M": 12, "O": 28, "P": 14})
fmt_range(ws_his, 2, 201, 1, 13, font=F_FORMULA, align=CTR)
for r in range(2, 202):
    ws_his.cell(row=r, column=1).number_format = "DD/MM/YYYY"
    ws_his.cell(row=r, column=6).number_format = "0.00"
    ws_his.cell(row=r, column=10).number_format = "0.0%"
    for c in (3, 4, 5, 7, 12):
        ws_his.cell(row=r, column=c).alignment = LFT
ws_his.freeze_panes = "A2"; ws_his.auto_filter.ref = "A1:M%d" % HIST_R2
ws_his.cell(row=1, column=15, value="RESUMO DO HISTÓRICO").font = F_SEC
for i, (lbl, f, nf) in enumerate([
        ("Registros acumulados", '=COUNTA($A$2:$A$%d)' % HIST_R2, "0"),
        ("Afinidade média", '=IFERROR(AVERAGE($F$2:$F$%d),"")' % HIST_R2, "0.00"),
        ("Ocupação média das salas", '=IFERROR(AVERAGE($J$2:$J$%d),"")' % HIST_R2, "0.0%"),
        ("Postos descobertos acumulados", '=COUNTIF($G$2:$G$%d,"DESCOBERTO")' % HIST_R2, "0"),
        ("Déficit médio por dia", '=IFERROR(AVERAGE($M$2:$M$%d),"")' % HIST_R2, "0.0")]):
    r = 2 + i
    a = ws_his.cell(row=r, column=15, value=lbl); a.font = F_FORMULA; a.border = BORD; a.alignment = LFT
    b = ws_his.cell(row=r, column=16, value=f); b.font = F_FORMULA; b.border = BORD
    b.alignment = CTR; b.number_format = nf; b.fill = FILL_ENT

# ---------------------------------------------------------------- LISTAS DINÂMICAS
dn("Lista_Especialidades", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (
    R(S_ESP, "$B$2"), R(S_ESP, "$B$%d:$B$%d" % (ESP_R1, ESP_R2))))
dn("Lista_Postos", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (
    R(S_POS, "$A$2"), R(S_POS, "$A$%d:$A$%d" % (POS_R1, POS_R2))))
dn("Lista_Tecnicos", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (
    R(S_EQP, "$B$2"), R(S_EQP, "$B$%d:$B$%d" % (EQ_R1, EQ_R2))))

def add_dv(ws, formula, ranges, kind="list", **kw):
    dv = DataValidation(type=kind, formula1=formula, allow_blank=True, showErrorMessage=True, **kw)
    ws.add_data_validation(dv)
    for rg in ranges:
        dv.add(rg)
    return dv

add_dv(ws_esp, '"Cirúrgica,Apoio"', ["C%d:C%d" % (ESP_R1, ESP_R2)])
add_dv(ws_esp, '"Sim,Não"', ["E%d:E%d" % (ESP_R1, ESP_R2)])
add_dv(ws_pos, "=Lista_TipoPosto", ["C%d:C%d" % (POS_R1, POS_R2)])
add_dv(ws_pos, "1", ["D%d:E%d" % (POS_R1, POS_R2)], kind="whole", operator="between", formula2="4")
add_dv(ws_pos, "=Lista_Especialidades", ["G%d:G%d" % (POS_R1, POS_R2)])
add_dv(ws_pos, '"Todos os dias,Seg a Sex,Seg a Sáb"', ["H%d:H%d" % (POS_R1, POS_R2)])
add_dv(ws_pos, '"Ativo,Inativo"', ["I%d:I%d" % (POS_R1, POS_R2)])
add_dv(ws_eqp, "=Lista_Funcoes", ["D%d:D%d" % (EQ_R1, EQ_R2)])
add_dv(ws_eqp, "=Lista_StatusCad", ["E%d:E%d" % (EQ_R1, EQ_R2)])
dvn = add_dv(ws_mat, "0", ["%s%d:%s%d" % (ML1, EQ_R1, ML2, EQ_R2)],
             kind="whole", operator="between", formula2="3")
dvn.errorTitle = "Nível inválido"
dvn.error = "Use 0 (não apto), 1 (em treinamento), 2 (apto) ou 3 (referência)."
add_dv(ws_aus, "=Lista_Tecnicos", ["A%d:A%d" % (AU_R1, AU_R2)])
add_dv(ws_aus, "=Lista_TiposAusencia", ["B%d:B%d" % (AU_R1, AU_R2)])
dvd = add_dv(ws_aus, "DATE(2000,1,1)", ["C%d:D%d" % (AU_R1, AU_R2)], kind="date",
             operator="between", formula2="DATE(2100,12,31)")
dvd.errorTitle = "Data inválida"; dvd.error = "Informe uma data válida."
add_dv(ws_map, "=Lista_Postos", ["B%d:B%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_Especialidades", ["E%d:E%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_Porte", ["I%d:I%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_StatusCirurgia", ["J%d:J%d" % (MP_R1, MP_R2)])
dvt = add_dv(ws_map, "TIME(0,0,0)", ["C%d:D%d" % (MP_R1, MP_R2)], kind="time",
             operator="between", formula2="TIME(23,59,0)")
dvt.errorTitle = "Horário inválido"; dvt.error = "Informe um horário no formato HH:MM."
dve = add_dv(ws_esc, "=Lista_Tecnicos", ["J%d:J%d" % (POS_R1, POS_R2), "M%d:M%d" % (POS_R1, POS_R2)])
dve.errorTitle = "Técnico não cadastrado"; dve.error = "Escolha um técnico cadastrado na aba Equipe."

# ---------------------------------------------------------------- FORMATAÇÃO CONDICIONAL
fv, fvt = PatternFill("solid", fgColor=VERDE), Font(color=VERDE_T, bold=True)
fa, fat = PatternFill("solid", fgColor=AMAR), Font(color=AMAR_T, bold=True)
fr, frt = PatternFill("solid", fgColor=VERM), Font(color=VERM_T, bold=True)

rng = lambda col: "%s%d:%s%d" % (col, POS_R1, col, POS_R2)
for txt, fill, font in (("ADEQUADO", fv, fvt), ("ATENÇÃO", fa, fat),
                        ("CRÍTICO", fr, frt), ("SEM EQUIPE", fr, frt)):
    ws_esc.conditional_formatting.add(rng("R"), CellIsRule(operator="equal", formula=['"%s"' % txt],
                                                           fill=fill, font=font))
ws_esc.conditional_formatting.add(rng("Q"), CellIsRule(operator="equal", formula=['"DESCOBERTO"'], fill=fr, font=frt))
ws_esc.conditional_formatting.add(rng("Q"), CellIsRule(operator="equal", formula=['"COMPLETO"'], fill=fv, font=fvt))
ws_esc.conditional_formatting.add(rng("Q"), FormulaRule(formula=['LEFT($Q%d,10)="INCOMPLETO"' % POS_R1], fill=fa, font=fat))
ws_esc.conditional_formatting.add(rng("W"), FormulaRule(formula=['AND($W%d<>"",$W%d<>"OK")' % (POS_R1, POS_R1)], fill=fr, font=frt))
ws_esc.conditional_formatting.add(rng("I"), FormulaRule(formula=['AND($I%d<>"",$I%d>Ocupacao_Max)' % (POS_R1, POS_R1)], fill=fr, font=frt, stopIfTrue=True))
ws_esc.conditional_formatting.add(rng("I"), FormulaRule(formula=['AND($I%d<>"",$I%d>=Meta_Ocupacao)' % (POS_R1, POS_R1)], fill=fv, font=fvt))
ws_esc.conditional_formatting.add(rng("P"), ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                                                           mid_type="num", mid_value=2, mid_color="FFEB84",
                                                           end_type="num", end_value=3, end_color="63BE7B"))
for col in ("S", "T", "U", "V"):
    ws_esc.conditional_formatting.add(rng(col), FormulaRule(
        formula=['AND(${c}%d<>"",${c}%d<>"OK")'.replace("${c}", col) % (POS_R1, POS_R1)], fill=fr, font=frt))
ws_mat.conditional_formatting.add("%s%d:%s%d" % (ML1, EQ_R1, ML2, EQ_R2),
    ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                   mid_type="num", mid_value=1.5, mid_color="D9E9D2",
                   end_type="num", end_value=3, end_color="4CAF50"))
ws_map.conditional_formatting.add("P%d:P%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['AND($P%d<>"",$P%d<>"OK")' % (MP_R1, MP_R1)], fill=fr, font=frt))
ws_map.conditional_formatting.add("J%d:J%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['OR($J%d="Cancelada",$J%d="Suspensa")' % (MP_R1, MP_R1)],
                fill=FILL_CINZ, font=Font(color="808080", italic=True)))
ws_map.conditional_formatting.add("O%d:O%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['AND($O%d<>"",$O%d>=Janela_Min)' % (MP_R1, MP_R1)], fill=fv, font=fvt))
ws_eqp.conditional_formatting.add("F%d:F%d" % (EQ_R1, EQ_R2),
    CellIsRule(operator="equal", formula=['"Disponível"'], fill=fv, font=fvt))
ws_eqp.conditional_formatting.add("F%d:F%d" % (EQ_R1, EQ_R2),
    FormulaRule(formula=['AND($F%d<>"",$F%d<>"Disponível")' % (EQ_R1, EQ_R1)], fill=fa, font=fat))
ws_jog.conditional_formatting.add("G%d:G%d" % (JOG_R1, JOG_R2),
    CellIsRule(operator="equal", formula=['"Janela aproveitável"'], fill=fv, font=fvt))
CAL_RNG = "C4:%s%d" % (get_column_letter(2 + DIAS_MES), 3 + EQ_N)
for i, (tipo, sig) in enumerate(TIPOS_AUS):
    ws_cal.conditional_formatting.add(CAL_RNG, CellIsRule(
        operator="equal", formula=['"%s"' % sig],
        fill=PatternFill("solid", fgColor=CORES_AUS[i]), font=Font(bold=True, size=9)))
ws_cal.conditional_formatting.add(CAL_RNG, CellIsRule(operator="equal", formula=['"!"'], fill=fr, font=frt))
ws_cal.conditional_formatting.add("C%d:%s%d" % (CAL_FIM + 4, get_column_letter(2 + DIAS_MES), CAL_FIM + 4),
    CellIsRule(operator="greaterThan", formula=["0"], fill=fr, font=frt))
ws_cal.conditional_formatting.add(CAL_RNG, FormulaRule(
    formula=['C$2=Data_Mapa'], fill=PatternFill("solid", fgColor="FFF2CC"), stopIfTrue=False))
ws_cal.conditional_formatting.add(CAL_RNG, FormulaRule(
    formula=['AND(C$2<>"",OR(WEEKDAY(C$2)=1,WEEKDAY(C$2)=7,COUNTIF(Feriados,C$2)>0))'],
    fill=PatternFill("solid", fgColor="EDEDED")))
ws_pai.conditional_formatting.add("E10", FormulaRule(formula=['$E$10>0'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("F10", FormulaRule(formula=['$F$10>0'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("G10", FormulaRule(formula=['$G$10>0'], fill=fa, font=fat))
ws_pai.conditional_formatting.add("C10", FormulaRule(formula=['$C$10>=$D$10'], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("E%d:E%d" % (B4_R1, B4_R1 + POS_N - 1), CellIsRule(operator="equal", formula=['"DESCOBERTO"'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("E%d:E%d" % (B4_R1, B4_R1 + POS_N - 1), CellIsRule(operator="equal", formula=['"COMPLETO"'], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("G%d:G%d" % (B4_R1, B4_R1 + POS_N - 1), CellIsRule(operator="equal", formula=['"CRÍTICO"'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("G%d:G%d" % (B4_R1, B4_R1 + POS_N - 1), CellIsRule(operator="equal", formula=['"SEM EQUIPE"'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("G%d:G%d" % (B5_R1, B5_R1 + HAB_N - 1), CellIsRule(operator="equal", formula=['"OK"'], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("G%d:G%d" % (B5_R1, B5_R1 + HAB_N - 1), CellIsRule(operator="equal", formula=['"LIMITE"'], fill=fa, font=fat))
ws_pai.conditional_formatting.add("G%d:G%d" % (B5_R1, B5_R1 + HAB_N - 1), CellIsRule(operator="equal", formula=['"SEM COBERTURA"'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("C%d:C%d" % (CHECK_ROW + 2, CHECK_LAST),
    FormulaRule(formula=['OR(LEFT($C%d,4)="ERRO",LEFT($C%d,8)="PENDENTE")' % (CHECK_ROW + 2, CHECK_ROW + 2)],
                fill=fr, font=frt))
ws_pai.conditional_formatting.add("C%d:C%d" % (CHECK_ROW + 2, CHECK_LAST),
    FormulaRule(formula=['$C%d="OK"' % (CHECK_ROW + 2)], fill=fv, font=fvt))
ws_aus.conditional_formatting.add("E%d:E%d" % (AU_R1, AU_R2),
    FormulaRule(formula=['AND($E%d<>"",$E%d<=0)' % (AU_R1, AU_R1)], fill=fr, font=frt))
ws_par.conditional_formatting.add("B24", FormulaRule(formula=['ROUND($B$24,6)<>1'], fill=fr, font=frt))

# ---------------------------------------------------------------- GRÁFICOS
ch1 = BarChart(); ch1.type = "col"; ch1.title = "Ocupação por sala"
ch1.y_axis.title = "% de ocupação"; ch1.height = 7.5; ch1.width = 15
ch1.add_data(Reference(ws_pai, min_col=4, min_row=B4_R1 - 1, max_row=B4_R1 + POS_N - 1), titles_from_data=True)
ch1.set_categories(Reference(ws_pai, min_col=1, min_row=B4_R1, max_row=B4_R1 + POS_N - 1))
ch1.y_axis.numFmt = "0%"; ch1.legend = None
ws_pai.add_chart(ch1, "J%d" % B4_LBL)

ch2 = BarChart(); ch2.type = "bar"; ch2.title = "Horas cirúrgicas por especialidade"
ch2.x_axis.title = "Horas"; ch2.height = 9.5; ch2.width = 15
ch2.add_data(Reference(ws_pai, min_col=3, min_row=B5_R1 - 1, max_row=B5_R1 + HAB_N - 1), titles_from_data=True)
ch2.set_categories(Reference(ws_pai, min_col=1, min_row=B5_R1, max_row=B5_R1 + HAB_N - 1))
ch2.legend = None
ws_pai.add_chart(ch2, "J%d" % B5_LBL)

ch3 = BarChart(); ch3.type = "col"; ch3.title = "Minutos livres por sala (espaço para encaixe)"
ch3.y_axis.title = "Minutos"; ch3.height = 7.5; ch3.width = 15
ch3.add_data(Reference(ws_pai, min_col=2, min_row=B6_R1 - 1, max_row=B6_R1 + POS_N - 1), titles_from_data=True)
ch3.set_categories(Reference(ws_pai, min_col=1, min_row=B6_R1, max_row=B6_R1 + POS_N - 1))
ch3.legend = None
ws_pai.add_chart(ch3, "J%d" % B6_LBL)

# ---------------------------------------------------------------- IMPRESSÃO
for ws, area in ((ws_esc, "A1:W%d" % POS_R2), (ws_map, "A1:P%d" % (MP_R1 + len(MAPA) - 1)),
                 (ws_sug, "A1:P%d" % POS_R2), (ws_jog, "A1:G%d" % JOG_R2),
                 (ws_cal, "A1:%s%d" % (get_column_letter(6 + DIAS_MES), 3 + EQ_N))):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    ws.print_area = area
ws_pai.page_setup.orientation = "portrait"
ws_pai.print_area = "A1:R%d" % CHECK_LAST

# ---------------------------------------------------------------- INSTRUÇÕES
widths(ws_ins, {"A": 3, "B": 42, "C": 104})
title(ws_ins, "CENTRO CIRÚRGICO — ESCALA DIÁRIA DE TÉCNICOS POR POSTO",
      "8 salas (2 técnicos cada) + admissão (2) + box de preparo oftalmológico (1) + sala de recém-nascido (1) = 20 vagas, "
      "para um quadro de 22 técnicos com férias, folgas e atestados. Plantão da manhã, 07:00–13:00.")
LINHAS = [
 ("S", "1. PREMISSAS ADOTADAS — confira antes de usar", ""),
 ("H", "Um plantão por dia", "A escala cobre o plantão da MANHÃ, 07:00–13:00, como na escala atual do serviço. O horário fica em Parâmetros; se outro turno for escalado nesta mesma planilha, troque a janela antes de lançar o dia."),
 ("H", "Período da escala", "O ciclo vai do dia 16 ao dia 15 do mês seguinte, como na escala atual. O primeiro dia do período fica em Parâmetros e é ele que comanda as 31 colunas do Calendario_Ausencias."),
 ("H", "Dias de funcionamento", "Cada posto tem um campo 'Funciona em': Todos os dias, Seg a Sex ou Seg a Sáb. Nos fins de semana e nos feriados listados em Parâmetros os postos de dia útil não operam, e as vagas necessárias do dia caem junto — é por isso que o domingo pede 7 técnicos e não 20."),
 ("H", "Papéis nas salas", "Nas salas cirúrgicas o Técnico 1 é o CIRCULANTE e o Técnico 2 é o INSTRUMENTADOR, com pesos diferentes na afinidade. Nos postos de apoio (admissão, box, RN) não há distinção. Se no cadastro do serviço todos constam como Téc.Enf., a Função vem como 'Ambos' — ajuste quem só circula ou só instrumenta."),
 ("H", "Matriz de habilidades", "Uma coluna por especialidade da lista única: o nível de cada técnico em cada especialidade que o serviço faz, mais Admissão e Sala de recém-nascido. Quando o cadastro é importado sem avaliação, todos entram com nível 2 (apto) em tudo — só um ponto de partida; enquanto não for calibrada, a verificação do Painel fica como PENDENTE."),
 ("H", "Déficit é o normal", "Como quase nunca há 20 técnicos disponíveis, a planilha trabalha com PRIORIDADE DE COBERTURA: cada posto tem uma prioridade e um mínimo aceitável, e o Painel mostra o déficit, os postos descobertos e quantas cirurgias precisam ser remanejadas."),
 ("H", "Dados de exemplo", "Equipe, habilidades, ausências e agenda vêm preenchidos com um dia de demonstração (18 disponíveis para 20 vagas). Substitua pelos dados reais."),
 ("S", "2. COMO A PLANILHA ESTÁ ORGANIZADA", ""),
 ("H", "ENTRADAS (o que se digita)", "Parâmetros · Habilidades · Especialidades · Postos · Equipe · Matriz_Habilidades · Ausencias · Mapa_Cirurgico · colunas TÉCNICO 1 e TÉCNICO 2 da Escala_Dia"),
 ("H", "PROCESSAMENTO (não digitar)", "Calc_Mix (minutos por especialidade em cada posto) e Calc_Afinidade (afinidade dos técnicos disponíveis e ainda não escalados). Ficam visíveis para auditoria."),
 ("H", "SAÍDAS", "Escala_Dia · Sugestao_Tecnicos · Jogo_de_Sala · Calendario_Ausencias · Painel · Base_Historico"),
 ("S", "3. A REGRA DE AFINIDADE", ""),
 ("H", "Afinidade do técnico com o posto", "Média dos níveis do técnico nas especialidades que passam pelo posto, PONDERADA PELOS MINUTOS de cada uma na agenda daquela sala. Especialidade que ocupa mais tempo pesa mais."),
 ("H", "Postos sem agenda", "Admissão, box e sala de RN — e qualquer sala sem cirurgia marcada, como a de urgência — usam a ESPECIALIDADE DE REFERÊNCIA cadastrada na aba Postos."),
 ("H", "Afinidade do posto", "Sala: Peso_Circulante × técnico 1 + Peso_Instrumentador × técnico 2. Apoio: média simples. Com um só técnico, é a afinidade dele."),
 ("H", "Classificação", "ADEQUADO ≥ Afinidade_Meta (2,50) · ATENÇÃO entre a meta e a mínima · CRÍTICO abaixo de Afinidade_Min (2,00) · SEM EQUIPE quando o posto está descoberto."),
 ("H", "Alerta de inaptidão", "Se uma especialidade responder por ≥ Part_Min_Critica (20%) do tempo da sala e algum técnico da dupla tiver nível ≤ Nivel_Critico (1) nela, a linha é sinalizada mesmo com média boa."),
 ("S", "4. ROTINA DO DIA", ""),
 ("H", "Passo 1 — data", "Em Parâmetros, ajuste a Data da escala. Toda a planilha passa a olhar para esse dia."),
 ("H", "Passo 2 — ausências", "Lance férias, folgas, atestados, licenças e treinamentos em Ausencias (período de/até). A aba Equipe mostra na hora quem está disponível; o Calendario_Ausencias mostra o período inteiro por técnico e, no rodapé, quantos funcionários há em cada data, quantas vagas o dia pede e o déficit — o mesmo indicador da escala atual, agora calculado por fórmula."),
 ("H", "Passo 3 — agenda", "Lance as cirurgias em Mapa_Cirurgico. A coluna Alerta aponta sobreposição de horário, sala não cadastrada, duração inválida e horário fora da janela do plantão."),
 ("H", "Passo 4 — escala", "Em Escala_Dia, escolha os técnicos de cada posto nas listas suspensas (células azuis), na ordem de prioridade dos postos. A aba Sugestao_Tecnicos mostra, para cada posto, quem ainda está livre em ordem de afinidade — a lista se atualiza a cada nome escalado."),
 ("H", "Passo 5 — o que ficou descoberto", "O Painel (bloco 2) mostra o déficit, os postos descobertos e quantas cirurgias precisam ser remanejadas. Use o Jogo_de_Sala para achar em qual sala e em que horário elas cabem."),
 ("H", "Passo 6 — fechamento", "Copie as linhas de Escala_Dia e cole COMO VALORES em Base_Historico para guardar o histórico do dia."),
 ("S", "5. JOGO DE SALA (encaixes)", ""),
 ("H", "O que é cada janela", "Janela 0 é o tempo livre antes da primeira cirurgia. As demais são o intervalo entre a liberação de uma cirurgia (fim + limpeza) e o início da seguinte. A última vai até o fim do plantão."),
 ("H", "Cabe cirurgia de até", "É a duração da janela menos o tempo de limpeza — ou seja, o tamanho real do encaixe possível. A coluna Situação separa as janelas aproveitáveis (≥ Janela_Min, 30 min) das curtas."),
 ("H", "No Mapa_Cirurgico", "As colunas 'Sala liberada às' e 'Livre até a próxima (min)' mostram o mesmo em linha, cirurgia a cirurgia; a célula fica verde quando o intervalo comporta um encaixe."),
 ("S", "6. CONVENÇÕES VISUAIS", ""),
 ("H", "Azul", "Célula de entrada — pode digitar."),
 ("H", "Amarelo", "Premissa de negócio (Parâmetros). Alterar aqui recalcula toda a planilha."),
 ("H", "Preto", "Resultado de fórmula — não digitar por cima."),
 ("H", "Verde itálico", "Valor trazido de outra aba por fórmula."),
 ("H", "Vermelho / âmbar / verde", "Semáforo de cobertura, afinidade, ocupação e alertas."),
 ("S", "7. COMO EXPANDIR", ""),
 ("H", "Novo técnico", "Acrescente a linha em Equipe (até 30), com matrícula, nome e COREN. Matriz_Habilidades, Calc_Afinidade, Calendario_Ausencias e as listas suspensas acompanham sozinhos — só preencha os níveis na Matriz."),
 ("H", "Nova especialidade", "Acrescente a linha em Especialidades (até 20 posições). É uma lista só: ela alimenta a agenda do Mapa_Cirurgico E as colunas da Matriz_Habilidades e do Calc_Mix, que pegam o nome automaticamente."),
 ("H", "Novo posto ou nova sala", "Acrescente a linha em Postos (até 16). As linhas correspondentes já existem em Calc_Mix, Escala_Dia, Sugestao_Tecnicos e Jogo_de_Sala e passam a funcionar sozinhas."),
 ("H", "Mais cirurgias / ausências", "O Mapa_Cirurgico comporta 200 cirurgias por dia e a aba Ausencias 150 registros; as fórmulas já cobrem esse intervalo."),
 ("H", "Feriados", "A lista em Parâmetros já traz os feriados nacionais de 2026. Acrescente os municipais e os pontos facultativos: em cada um deles os postos de dia útil deixam de operar."),
 ("S", "8. OBSERVAÇÕES TÉCNICAS", ""),
 ("H", "Ocupação da sala", "Cada cirurgia consome sua duração + o tempo de limpeza definido em Parâmetros (20 min). Cirurgias Canceladas ou Suspensas não entram na ocupação nem no cálculo de afinidade."),
 ("H", "Colunas auxiliares ocultas", "Mapa_Cirurgico colunas Q a U, Escala_Dia X a Z, Ausencias G e H e Jogo_de_Sala H e I guardam cálculos intermediários. Na Escala_Dia as colunas S a V (Chk duplicidade, disponibilidade, função e inaptidão) também estão ocultas — o resultado delas aparece consolidado em ALERTAS; exiba-as se quiser auditar cada teste em separado. Não excluir nenhuma delas."),
 ("H", "Desempate na sugestão", "O Calc_Afinidade soma 0,000001 × número da linha para evitar empates no ranking; o efeito é invisível nas duas casas exibidas."),
 ("H", "Funções utilizadas", "SUMIFS, COUNTIFS, SUMPRODUCT, INDEX, MATCH, LARGE, IF e IFERROR — compatíveis com Excel e LibreOffice. Não há macros, Power Query nem matrizes dinâmicas."),
 ("H", "Não se fazem cirurgias cardíacas", "A lista de especialidades da aba Especialidades reflete isso; inclua ou remova linhas conforme o serviço."),
]
r = 4
for kind, a, b in LINHAS:
    if kind == "S":
        cc = ws_ins.cell(row=r, column=2, value=a); cc.font = F_SEC
        ws_ins.cell(row=r, column=2).fill = FILL_CINZ; ws_ins.cell(row=r, column=3).fill = FILL_CINZ
        ws_ins.row_dimensions[r].height = 18
    else:
        c1 = ws_ins.cell(row=r, column=2, value=a)
        c1.font = Font(name="Calibri", size=10, bold=True)
        c1.alignment = Alignment(vertical="top", wrap_text=True)
        c2 = ws_ins.cell(row=r, column=3, value=b)
        c2.font = F_FORMULA; c2.alignment = Alignment(vertical="top", wrap_text=True)
        ws_ins.row_dimensions[r].height = max(16, 13.5 * (len(b) // 125 + 1))
    r += 1

wb.save(OUT)
print("salvo:", OUT)

# ---------------------------------------------------------------- variante para inspeção visual
import os as _os
if _os.environ.get("VISUAL") == "1":
    areas = {S_INS: "A1:C%d" % (r - 1), S_PAR: "A1:J69", S_ESP: "A1:F26",
             S_POS: "A1:J20", S_EQP: "A1:H30", S_MAT: "A1:%s30" % get_column_letter(MC2 + 2),
             S_AUS: "A1:F20", S_CAL: "A1:%s%d" % (get_column_letter(6 + DIAS_MES), 3 + EQ_N + 4),
             S_MAP: "A1:P38", S_MIX: "A1:%s20" % OCUP_L, S_AFI: "A1:S30",
             S_ESC: "A1:W18", S_SUG: "A1:P18", S_JOG: "A1:G40",
             S_PAI: "A1:R%d" % CHECK_LAST, S_HIS: "A1:P12"}
    for nome, area in areas.items():
        w = wb[nome]
        w.page_setup.orientation = "landscape"
        w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 1
        w.sheet_properties.pageSetUpPr.fitToPage = True
        w.print_area = area
    wb.save(OUT.replace(".xlsx", "_VISUAL.xlsx"))
    print("visual:", OUT.replace(".xlsx", "_VISUAL.xlsx"))
