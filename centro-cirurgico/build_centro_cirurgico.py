# -*- coding: utf-8 -*-
"""
Gerador do workbook: Centro Cirúrgico — Mapa Cirúrgico e Escala de Duplas por Sala.

Arquitetura:
  INPUT  -> Parâmetros / Especialidades / Salas / Equipe / Matriz_Habilidades / Mapa_Cirurgico
  PROC   -> Calc_Mix (mix de especialidades por sala x turno)
            Calc_Afinidade (afinidade de cada técnico com cada sala x turno)
  OUTPUT -> Escala_Duplas (alocação + validações) / Sugestao_Duplas / Painel / Base_Historico

Regra central (definida pela coordenação): afinidade de habilidade.
  afinidade(tecnico, sala, turno) = soma( minutos(esp) * nivel(tecnico, esp) ) / soma( minutos(esp) )
  afinidade(dupla)                = Peso_Circulante * afin(circulante) + Peso_Instrumentador * afin(instrumentador)
"""
import random
from datetime import date, time
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule, ColorScaleRule
from openpyxl.chart import BarChart, Reference

OUT = "/home/user/umm-hora-a-hora/centro-cirurgico/Centro_Cirurgico_Escala_Duplas_v1.xlsx"

# ---------------------------------------------------------------- dimensões
EQ_N      = 150          # capacidade de técnicos (linhas 2..151)
EQ_R1, EQ_R2 = 2, 1 + EQ_N
MAPA_N    = 300          # capacidade de cirurgias/dia (linhas 2..301)
MP_R1, MP_R2 = 2, 1 + MAPA_N
ESP_N     = 20           # capacidade de especialidades (linhas 2..21 / colunas D..W)
ESP_R1, ESP_R2 = 2, 1 + ESP_N
SALA_N    = 12           # capacidade de salas (linhas 2..13)
SL_R1, SL_R2 = 2, 1 + SALA_N
TURNOS    = ["Manhã", "Tarde", "Noite"]
COMBO_N   = SALA_N * len(TURNOS)          # 36 linhas sala x turno
CB_R1, CB_R2 = 2, 1 + COMBO_N
ESP_C1, ESP_C2 = 4, 3 + ESP_N             # colunas D..W
ESP_L1, ESP_L2 = get_column_letter(ESP_C1), get_column_letter(ESP_C2)
HIST_R2   = 2001

# ---------------------------------------------------------------- abas
S_INS, S_PAR, S_ESP, S_SAL = "Instruções", "Parâmetros", "Especialidades", "Salas"
S_EQP, S_MAT, S_MAP        = "Equipe", "Matriz_Habilidades", "Mapa_Cirurgico"
S_MIX, S_AFI               = "Calc_Mix", "Calc_Afinidade"
S_ESC, S_SUG, S_PAI, S_HIS = "Escala_Duplas", "Sugestao_Duplas", "Painel", "Base_Historico"

def R(sheet, addr):
    return "'%s'!%s" % (sheet, addr)

# ---------------------------------------------------------------- estilo
AZ_ESC = "1F3864"; AZ_MED = "2E75B6"; AZ_CLR = "DDEBF7"
AM_PRE = "FFF2CC"; CINZA = "F2F2F2"; VERDE = "C6EFCE"; VERDE_T = "006100"
AMAR = "FFEB9C"; AMAR_T = "9C6500"; VERM = "FFC7CE"; VERM_T = "9C0006"
F_ENTRADA = Font(name="Calibri", size=10, color="0070C0")
F_FORMULA = Font(name="Calibri", size=10, color="000000")
F_REF     = Font(name="Calibri", size=10, color="006100", italic=True)
F_HEAD    = Font(name="Calibri", size=10, color="FFFFFF", bold=True)
F_TIT     = Font(name="Calibri", size=14, color=AZ_ESC, bold=True)
F_SEC     = Font(name="Calibri", size=11, color=AZ_ESC, bold=True)
F_NOTA    = Font(name="Calibri", size=9, color="7F7F7F", italic=True)
FILL_HEAD = PatternFill("solid", fgColor=AZ_ESC)
FILL_SUB  = PatternFill("solid", fgColor=AZ_MED)
FILL_PREM = PatternFill("solid", fgColor=AM_PRE)
FILL_ENT  = PatternFill("solid", fgColor=AZ_CLR)
FILL_CINZ = PatternFill("solid", fgColor=CINZA)
THIN = Side(style="thin", color="BFBFBF")
BORD = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CTR  = Alignment(horizontal="center", vertical="center")
CTRW = Alignment(horizontal="center", vertical="center", wrap_text=True)
LFT  = Alignment(horizontal="left", vertical="center")

def head(ws, row, labels, col0=1, height=30):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=col0 + i, value=t)
        c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = CTRW; c.border = BORD
    ws.row_dimensions[row].height = height

def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w

def title(ws, text, sub=None, span=10):
    ws["A1"] = text; ws["A1"].font = F_TIT
    if sub:
        ws["A2"] = sub; ws["A2"].font = F_NOTA
    ws.row_dimensions[1].height = 22

# ---------------------------------------------------------------- dados de exemplo
ESPECIALIDADES = [
    ("ORT", "Ortopedia", 120), ("CGE", "Cirurgia Geral", 90), ("NEU", "Neurocirurgia", 240),
    ("CCV", "Cirurgia Cardiovascular", 300), ("URO", "Urologia", 90), ("GIN", "Ginecologia", 90),
    ("OBS", "Obstetrícia", 60), ("OFT", "Oftalmologia", 45), ("OTO", "Otorrinolaringologia", 75),
    ("PLA", "Cirurgia Plástica", 120), ("VAS", "Cirurgia Vascular", 150), ("BAR", "Cirurgia Bariátrica", 150),
    ("PED", "Cirurgia Pediátrica", 90), ("BMF", "Buco-Maxilo-Facial", 120),
]
ESP_NOMES = [e[1] for e in ESPECIALIDADES]
ESP_IDX = {e[1]: i for i, e in enumerate(ESPECIALIDADES)}

SALAS = [
    ("SO-01", "Sala 1 — Ortopedia",        ["Ortopedia"]),
    ("SO-02", "Sala 2 — Geral/Bariátrica", ["Cirurgia Geral", "Cirurgia Bariátrica"]),
    ("SO-03", "Sala 3 — Neurocirurgia",    ["Neurocirurgia"]),
    ("SO-04", "Sala 4 — Cardiovascular",   ["Cirurgia Cardiovascular", "Cirurgia Vascular"]),
    ("SO-05", "Sala 5 — Uro/Gineco",       ["Urologia", "Ginecologia"]),
    ("SO-06", "Sala 6 — Oftalmo/Otorrino", ["Oftalmologia", "Otorrinolaringologia"]),
    ("SO-07", "Sala 7 — Plástica/BMF",     ["Cirurgia Plástica", "Buco-Maxilo-Facial"]),
    ("SO-08", "Sala 8 — Pediátrica/Obst.", ["Cirurgia Pediátrica", "Obstetrícia"]),
]
TURNO_JAN = {"Manhã": (time(7, 0), time(13, 0), 360),
             "Tarde": (time(13, 0), time(19, 0), 360),
             "Noite": (time(19, 0), time(7, 0), 720)}

NOMES = ["Ana Paula Ribeiro","Bruno Tavares","Carla Menezes","Daniel Prado","Elisa Fontes","Fábio Cardoso",
 "Gabriela Nunes","Henrique Sales","Isabel Moraes","João Vitor Lima","Karina Duarte","Leandro Peixoto",
 "Marina Castro","Nelson Vieira","Olívia Ramos","Paulo Sérgio Alves","Quezia Martins","Rafael Bittencourt",
 "Simone Aguiar","Tiago Fernandes","Úrsula Campos","Vinícius Barros","Wanda Siqueira","Xavier Rocha",
 "Yara Monteiro","Zélia Braga","André Coutinho","Beatriz Salles","Caio Meireles","Débora Antunes",
 "Eduardo Pimentel","Fernanda Lacerda","Gustavo Rangel","Helena Prado","Igor Bastos","Juliana Cordeiro",
 "Kléber Amorim","Larissa Bezerra","Marcelo Quintana","Natália Ferraz","Otávio Camargo","Priscila Vasques",
 "Ricardo Andrade","Sabrina Toledo","Thales Guimarães","Vanessa Portela","William Sampaio","Yasmin Correia",
 "Adriano Mesquita","Bianca Rezende","Cristiano Padilha","Danilo Freitas","Eliane Bandeira","Felipe Norões",
 "Giovana Ferrari","Hugo Meneghetti","Ivone Salgado","Jaqueline Bonfim","Kelly Andrade","Lucas Vilarinho"]

random.seed(20260819)

def build_equipe():
    """48 técnicos-núcleo (2 por sala x turno) + 12 de apoio."""
    equipe = []   # (matricula, nome, funcao, turno_pref, status)
    skills = {}   # nome -> [niveis por especialidade]
    n = 0
    for si, (sc, snome, sesp) in enumerate(SALAS):
        for ti, turno in enumerate(TURNOS):
            for papel in ("Circulante", "Instrumentador"):
                nome = NOMES[n]; mat = "TEC-%03d" % (n + 1); n += 1
                lv = [0] * len(ESPECIALIDADES)
                for e in sesp:
                    lv[ESP_IDX[e]] = 3
                # afinidade secundária: especialidades das salas vizinhas
                viz = SALAS[(si + 1) % len(SALAS)][2] + SALAS[(si - 1) % len(SALAS)][2]
                for e in viz:
                    if lv[ESP_IDX[e]] == 0:
                        lv[ESP_IDX[e]] = 2 if random.random() < 0.55 else 1
                for i in range(len(lv)):
                    if lv[i] == 0 and random.random() < 0.30:
                        lv[i] = 1
                equipe.append((mat, nome, papel, turno, "Ativo"))
                skills[nome] = lv
    apoio_status = ["Ativo"]*9 + ["Férias", "Férias", "Afastado"]
    for k in range(12):
        nome = NOMES[n]; mat = "TEC-%03d" % (n + 1); n += 1
        lv = [1] * len(ESPECIALIDADES)
        for i in random.sample(range(len(ESPECIALIDADES)), 5):
            lv[i] = 2
        equipe.append((mat, nome, "Ambos", TURNOS[k % 3], apoio_status[k]))
        skills[nome] = lv
    return equipe, skills

EQUIPE, SKILLS = build_equipe()
NOME_BY_IDX = [e[1] for e in EQUIPE]

def build_mapa(dia):
    """Cirurgias do dia, encaixadas na janela de cada turno, sem sobreposição."""
    cirs = []   # (data, sala, turno, ini_min, fim_min, esp, proc, cirurgiao, porte, status)
    procs = {"Ortopedia":["Artroplastia total de joelho","Osteossíntese de fêmur","Artroscopia de ombro"],
     "Cirurgia Geral":["Colecistectomia videolaparoscópica","Herniorrafia inguinal","Apendicectomia"],
     "Neurocirurgia":["Craniotomia para tumor","Artrodese lombar","Derivação ventrículo-peritoneal"],
     "Cirurgia Cardiovascular":["Revascularização do miocárdio","Troca valvar aórtica"],
     "Cirurgia Vascular":["Endarterectomia de carótida","Correção de aneurisma de aorta"],
     "Urologia":["Ressecção transuretral de próstata","Nefrolitotripsia"],
     "Ginecologia":["Histerectomia total","Videolaparoscopia diagnóstica"],
     "Obstetrícia":["Cesariana","Curetagem uterina"],
     "Oftalmologia":["Facectomia com implante de LIO","Vitrectomia posterior"],
     "Otorrinolaringologia":["Amigdalectomia","Septoplastia","Timpanoplastia"],
     "Cirurgia Plástica":["Dermolipectomia abdominal","Enxerto de pele em queimado"],
     "Cirurgia Bariátrica":["Gastroplastia em Y de Roux","Gastrectomia vertical"],
     "Cirurgia Pediátrica":["Postectomia","Correção de hérnia umbilical"],
     "Buco-Maxilo-Facial":["Osteotomia mandibular","Redução de fratura de zigoma"]}
    cirurgioes = ["Dr. Almeida","Dra. Bernardes","Dr. Coelho","Dra. Delgado","Dr. Esteves","Dra. Fialho",
                  "Dr. Gouveia","Dra. Hirano","Dr. Iglesias","Dra. Jordão"]
    setup = 30
    especiais = {(5, 2): "cancel", (1, 1): "cancel", (7, 0): "susp"}   # (sala_idx, turno_idx)
    for si, (sc, snome, sesp) in enumerate(SALAS):
        for ti, turno in enumerate(TURNOS):
            ini_t, fim_t, disp = TURNO_JAN[turno]
            base = ini_t.hour * 60 + ini_t.minute
            alvo = int(disp * random.uniform(0.60, 0.92))
            decorrido = 0
            k = 0
            while decorrido < alvo and k < 5:
                esp = sesp[k % len(sesp)]
                dur_base = dict([(e[1], e[2]) for e in ESPECIALIDADES])[esp]
                dur = int(round(dur_base * random.uniform(0.8, 1.25) / 5.0) * 5)
                if decorrido + dur + setup > disp:
                    dur = int((disp - decorrido - setup) / 5) * 5
                    if dur < 30:
                        break
                cursor = base + decorrido
                status = "Agendada"
                if especiais.get((si, ti)) == "cancel" and k == 1: status = "Cancelada"
                if especiais.get((si, ti)) == "susp" and k == 1:   status = "Suspensa"
                porte = "G" if dur >= 180 else ("M" if dur >= 90 else "P")
                cirs.append((dia, sc, turno, cursor % 1440, (cursor + dur) % 1440, esp,
                             procs[esp][k % len(procs[esp])], cirurgioes[(si * 3 + k) % len(cirurgioes)],
                             porte, status))
                decorrido += dur + setup
                k += 1
    return cirs

DIA = date(2026, 8, 20)
MAPA = build_mapa(DIA)

def afinidade(nome, sala, turno):
    """Reconciliação independente (Python) da afinidade técnico x sala x turno."""
    mins = [0.0] * len(ESPECIALIDADES)
    for (d, sc, tn, ini, fim, esp, pr, cir, porte, st) in MAPA:
        if sc == sala and tn == turno and st not in ("Cancelada", "Suspensa"):
            dur = (fim - ini) % 1440
            mins[ESP_IDX[esp]] += dur + 30
    tot = sum(mins)
    if tot == 0:
        return None
    lv = SKILLS[nome]
    return sum(m * l for m, l in zip(mins, lv)) / tot

def build_escala():
    """Alocação inicial (entrada pré-preenchida): dupla-núcleo da sala/turno,
    com dois desvios propositais para exercitar os semáforos."""
    aloc = {}
    for si, (sc, _, _) in enumerate(SALAS):
        for ti, turno in enumerate(TURNOS):
            base = (si * 3 + ti) * 2
            circ, instr = NOME_BY_IDX[base], NOME_BY_IDX[base + 1]
            aloc[(sc, turno)] = [circ, instr]
    apoio = [e[1] for e in EQUIPE if e[2] == "Ambos" and e[4] == "Ativo"]
    aloc[("SO-06", "Noite")][1] = apoio[0]     # instrumentador de apoio -> afinidade menor
    aloc[("SO-03", "Tarde")][0] = apoio[1]     # circulante de apoio     -> afinidade menor
    return aloc

ALOC = build_escala()

# ================================================================ WORKBOOK
wb = Workbook()
ws_ins = wb.active; ws_ins.title = S_INS
ws_par = wb.create_sheet(S_PAR); ws_esp = wb.create_sheet(S_ESP); ws_sal = wb.create_sheet(S_SAL)
ws_eqp = wb.create_sheet(S_EQP); ws_mat = wb.create_sheet(S_MAT); ws_map = wb.create_sheet(S_MAP)
ws_mix = wb.create_sheet(S_MIX); ws_afi = wb.create_sheet(S_AFI)
ws_esc = wb.create_sheet(S_ESC); ws_sug = wb.create_sheet(S_SUG); ws_pai = wb.create_sheet(S_PAI)
ws_his = wb.create_sheet(S_HIS)
for w in wb.worksheets:
    w.sheet_view.showGridLines = False

# ---------------------------------------------------------------- PARÂMETROS
title(ws_par, "PARÂMETROS E PREMISSAS", "Células amarelas são premissas de negócio: alterá-las recalcula toda a planilha. Nenhuma premissa está embutida em fórmula.")
widths(ws_par, {"A": 52, "B": 14, "C": 12, "D": 22, "E": 3, "F": 18, "G": 16, "H": 16, "I": 8})

def sec(ws, row, text, span=4):
    c = ws.cell(row=row, column=1, value=text); c.font = F_SEC
    for i in range(span):
        ws.cell(row=row, column=1 + i).fill = FILL_CINZ
        ws.cell(row=row, column=1 + i).border = BORD

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
prem(ws_par, 6, "Data do mapa", DIA, "DD/MM/YYYY")
prem(ws_par, 7, "Coordenação responsável", "Coordenação de Enfermagem")
for _r in (4, 5, 7):
    ws_par.merge_cells(start_row=_r, start_column=2, end_row=_r, end_column=4)
    ws_par.cell(row=_r, column=2).alignment = LFT

sec(ws_par, 9, "2. ESCALA DE HABILIDADE (usada na Matriz_Habilidades)")
head(ws_par, 10, ["Nível", "Descrição", "Pontos", "Critério operacional"], height=18)
NIVEIS = [(0, "Não apto", 0, "Não pode assumir a especialidade"),
          (1, "Em treinamento", 1, "Só atua acompanhado de técnico apto"),
          (2, "Apto", 2, "Atua com autonomia na especialidade"),
          (3, "Referência", 3, "Atua em alta complexidade e treina a equipe")]
for i, (n, d, p, crit) in enumerate(NIVEIS):
    r = 11 + i
    for j, v in enumerate((n, d, p, crit)):
        c = ws_par.cell(row=r, column=1 + j, value=v)
        c.border = BORD; c.font = F_FORMULA
        c.alignment = CTR if j in (0, 2) else LFT

sec(ws_par, 16, "3. PARÂMETROS DE AFINIDADE DA DUPLA")
prem(ws_par, 17, "Peso do INSTRUMENTADOR na afinidade da dupla", 0.60, "0.00", "Peso_Instrumentador")
prem(ws_par, 18, "Peso do CIRCULANTE na afinidade da dupla", 0.40, "0.00", "Peso_Circulante")
ws_par.cell(row=19, column=1, value="Soma dos pesos (precisa ser 1,00)").font = F_FORMULA
c = ws_par.cell(row=19, column=2, value="=B17+B18"); c.number_format = "0.00"; c.border = BORD; c.alignment = CTR
prem(ws_par, 20, "Afinidade META — dupla ADEQUADA quando ≥", 2.50, "0.00", "Afinidade_Meta")
prem(ws_par, 21, "Afinidade MÍNIMA aceitável — abaixo disto é CRÍTICA", 2.00, "0.00", "Afinidade_Min")
prem(ws_par, 22, "Nível considerado INAPTO (≤)", 1, "0", "Nivel_Critico")
prem(ws_par, 23, "Participação mínima da especialidade para alerta crítico", 0.20, "0%", "Part_Min_Critica")

sec(ws_par, 25, "4. PARÂMETROS OPERACIONAIS")
prem(ws_par, 26, "Tempo de setup / limpeza por cirurgia (min)", 30, "0", "Setup_Min")
prem(ws_par, 27, "Meta de ocupação de sala", 0.85, "0%", "Meta_Ocupacao")
prem(ws_par, 28, "Ocupação máxima admitida", 1.00, "0%", "Ocupacao_Max")

sec(ws_par, 30, "5. TURNOS")
head(ws_par, 31, ["Turno", "Início", "Fim", "Minutos disponíveis"], height=18)
for i, t in enumerate(TURNOS):
    r = 32 + i
    ini, fim, _ = TURNO_JAN[t]
    for j, v in enumerate((t, ini, fim)):
        c = ws_par.cell(row=r, column=1 + j, value=v)
        c.border = BORD; c.alignment = CTR
        c.font = F_ENTRADA if j > 0 else F_FORMULA
        if j > 0:
            c.number_format = "HH:MM"; c.fill = FILL_PREM
    c = ws_par.cell(row=r, column=4, value="=MOD(C%d-B%d,1)*1440" % (r, r))
    c.border = BORD; c.alignment = CTR; c.number_format = "0"

ws_par.cell(row=3, column=6, value="LISTAS AUXILIARES").font = F_SEC
head(ws_par, 4, ["Função", "Status equipe", "Status cirurgia", "Porte"], col0=6, height=18)
AUX = [["Circulante", "Instrumentador", "Ambos"],
       ["Ativo", "Férias", "Afastado", "Folga"],
       ["Agendada", "Realizada", "Cancelada", "Suspensa"],
       ["P", "M", "G"]]
for j, col in enumerate(AUX):
    for i, v in enumerate(col):
        c = ws_par.cell(row=5 + i, column=6 + j, value=v)
        c.border = BORD; c.alignment = CTR; c.font = F_FORMULA

# ---------------------------------------------------------------- nomes definidos
def dn(name, ref):
    wb.defined_names.add(DefinedName(name, attr_text=ref))

dn("Data_Mapa", R(S_PAR, "$B$6"))
dn("Peso_Instrumentador", R(S_PAR, "$B$17")); dn("Peso_Circulante", R(S_PAR, "$B$18"))
dn("Afinidade_Meta", R(S_PAR, "$B$20"));      dn("Afinidade_Min", R(S_PAR, "$B$21"))
dn("Nivel_Critico", R(S_PAR, "$B$22"));       dn("Part_Min_Critica", R(S_PAR, "$B$23"))
dn("Setup_Min", R(S_PAR, "$B$26"));           dn("Meta_Ocupacao", R(S_PAR, "$B$27"))
dn("Ocupacao_Max", R(S_PAR, "$B$28"))
dn("Turnos_Nome", R(S_PAR, "$A$32:$A$34")); dn("Turnos_Min", R(S_PAR, "$D$32:$D$34"))
dn("Lista_Turnos", R(S_PAR, "$A$32:$A$34"))
dn("Lista_Funcoes", R(S_PAR, "$F$5:$F$7")); dn("Lista_StatusEquipe", R(S_PAR, "$G$5:$G$8"))
dn("Lista_StatusCirurgia", R(S_PAR, "$H$5:$H$8")); dn("Lista_Porte", R(S_PAR, "$I$5:$I$7"))
dn("Lista_Salas", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (R(S_SAL, "$A$2"), R(S_SAL, "$A$%d:$A$%d" % (SL_R1, SL_R2))))
dn("Lista_Especialidades", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (R(S_ESP, "$B$2"), R(S_ESP, "$B$%d:$B$%d" % (ESP_R1, ESP_R2))))
dn("Lista_Tecnicos", "OFFSET(%s,0,0,MAX(1,COUNTA(%s)),1)" % (R(S_EQP, "$B$2"), R(S_EQP, "$B$%d:$B$%d" % (EQ_R1, EQ_R2))))

# ---------------------------------------------------------------- nomes de intervalos de dados
dn("Turnos_Ini", R(S_PAR, "$B$32:$B$34")); dn("Turnos_Fim", R(S_PAR, "$C$32:$C$34"))
dn("Salas_Cod",    R(S_SAL, "$A$%d:$A$%d" % (SL_R1, SL_R2)))
dn("Salas_Status", R(S_SAL, "$C$%d:$C$%d" % (SL_R1, SL_R2)))
dn("Esp_Nome", R(S_ESP, "$B$%d:$B$%d" % (ESP_R1, ESP_R2)))
dn("Esp_Dur",  R(S_ESP, "$C$%d:$C$%d" % (ESP_R1, ESP_R2)))
dn("Equipe_Nome",   R(S_EQP, "$B$%d:$B$%d" % (EQ_R1, EQ_R2)))
dn("Equipe_Funcao", R(S_EQP, "$C$%d:$C$%d" % (EQ_R1, EQ_R2)))
dn("Equipe_Status", R(S_EQP, "$E$%d:$E$%d" % (EQ_R1, EQ_R2)))
dn("Matriz_Nome",   R(S_MAT, "$B$%d:$B$%d" % (EQ_R1, EQ_R2)))
dn("Matriz_Niveis", R(S_MAT, "$%s$%d:$%s$%d" % (ESP_L1, EQ_R1, ESP_L2, EQ_R2)))
dn("Matriz_Esp",    R(S_MAT, "$%s$1:$%s$1" % (ESP_L1, ESP_L2)))
dn("Mix_Esp",       R(S_MIX, "$%s$1:$%s$1" % (ESP_L1, ESP_L2)))
for nm, col in (("Mapa_Data", "A"), ("Mapa_Sala", "B"), ("Mapa_Turno", "C"), ("Mapa_Ini", "D"),
                ("Mapa_Fim", "E"), ("Mapa_Esp", "F"), ("Mapa_Status", "J"), ("Mapa_Dur", "K"),
                ("Mapa_MinOcup", "L"), ("Mapa_Alerta", "M"),
                ("Mapa_IniNum", "O"), ("Mapa_FimNum", "P")):
    dn(nm, R(S_MAP, "$%s$%d:$%s$%d" % (col, MP_R1, col, MP_R2)))
for nm, col in (("Esc_Sala", "B"), ("Esc_Turno", "C"), ("Esc_NCir", "D"), ("Esc_MinOcup", "E"),
                ("Esc_MinTurno", "F"), ("Esc_Circ", "H"), ("Esc_Instr", "J"), ("Esc_Afin", "N"),
                ("Esc_Class", "O"), ("Esc_AfinNum", "V"), ("Esc_Peso", "W")):
    dn(nm, R(S_ESC, "$%s$%d:$%s$%d" % (col, CB_R1, col, CB_R2)))

def fmt_range(ws, r1, r2, c1, c2, font=F_ENTRADA, align=None, numfmt=None, fill=None):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = BORD; cell.font = font
            if align: cell.alignment = align
            if numfmt: cell.number_format = numfmt
            if fill: cell.fill = fill

# ---------------------------------------------------------------- ESPECIALIDADES
head(ws_esp, 1, ["Código", "Especialidade", "Duração média (min)", "Ativa", "Observação"])
widths(ws_esp, {"A": 10, "B": 32, "C": 20, "D": 10, "E": 40})
fmt_range(ws_esp, ESP_R1, ESP_R2, 1, 5, align=LFT)
for i in range(ESP_N):
    r = ESP_R1 + i
    for c in (1, 3, 4):
        ws_esp.cell(row=r, column=c).alignment = CTR
    if i < len(ESPECIALIDADES):
        cod, nome, dur = ESPECIALIDADES[i]
        ws_esp.cell(row=r, column=1, value=cod); ws_esp.cell(row=r, column=2, value=nome)
        ws_esp.cell(row=r, column=3, value=dur);  ws_esp.cell(row=r, column=4, value="Sim")
ws_esp.freeze_panes = "A2"; ws_esp.auto_filter.ref = "A1:E%d" % ESP_R2

# ---------------------------------------------------------------- SALAS
head(ws_sal, 1, ["Sala", "Descrição", "Status", "Especialidades do perfil", "Observação"])
widths(ws_sal, {"A": 10, "B": 30, "C": 12, "D": 42, "E": 30})
fmt_range(ws_sal, SL_R1, SL_R2, 1, 5, align=LFT)
for i in range(SALA_N):
    r = SL_R1 + i
    ws_sal.cell(row=r, column=1).alignment = CTR; ws_sal.cell(row=r, column=3).alignment = CTR
    if i < len(SALAS):
        cod, desc, esps = SALAS[i]
        ws_sal.cell(row=r, column=1, value=cod); ws_sal.cell(row=r, column=2, value=desc)
        ws_sal.cell(row=r, column=3, value="Ativa"); ws_sal.cell(row=r, column=4, value=", ".join(esps))
ws_sal.freeze_panes = "A2"; ws_sal.auto_filter.ref = "A1:E%d" % SL_R2

# ---------------------------------------------------------------- EQUIPE
head(ws_eqp, 1, ["Matrícula", "Nome do técnico", "Função", "Turno preferencial", "Status", "Observação"])
widths(ws_eqp, {"A": 12, "B": 26, "C": 16, "D": 18, "E": 12, "F": 30})
fmt_range(ws_eqp, EQ_R1, EQ_R2, 1, 6, align=LFT)
for i in range(EQ_N):
    r = EQ_R1 + i
    for c in (1, 3, 4, 5):
        ws_eqp.cell(row=r, column=c).alignment = CTR
    if i < len(EQUIPE):
        for j, v in enumerate(EQUIPE[i]):
            ws_eqp.cell(row=r, column=1 + j, value=v)
ws_eqp.freeze_panes = "B2"; ws_eqp.auto_filter.ref = "A1:F%d" % EQ_R2

# ---------------------------------------------------------------- MATRIZ DE HABILIDADES
hdr = ["Matrícula", "Nome do técnico", "Função"] + [""] * ESP_N + ["Nível médio (geral)", "Nº especialidades aptas (≥2)"]
head(ws_mat, 1, hdr, height=146)
for i in range(ESP_N):
    c = ws_mat.cell(row=1, column=ESP_C1 + i, value="=IF(%s=\"\",\"\",%s)" % (
        R(S_ESP, "$B$%d" % (ESP_R1 + i)), R(S_ESP, "$B$%d" % (ESP_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD; c.alignment = Alignment(horizontal="center", vertical="bottom", text_rotation=90)
widths(ws_mat, {"A": 11, "B": 26, "C": 15})
for i in range(ESP_N):
    ws_mat.column_dimensions[get_column_letter(ESP_C1 + i)].width = 5.5
ws_mat.column_dimensions[get_column_letter(ESP_C2 + 1)].width = 12
ws_mat.column_dimensions[get_column_letter(ESP_C2 + 2)].width = 14
for i in range(EQ_N):
    r = EQ_R1 + i
    for col, src in ((1, "A"), (2, "B"), (3, "C")):
        c = ws_mat.cell(row=r, column=col, value="=IF(%s=\"\",\"\",%s)" % (
            R(S_EQP, "%s%d" % (src, r)), R(S_EQP, "%s%d" % (src, r))))
        c.font = F_REF; c.border = BORD; c.alignment = CTR if col != 2 else LFT
    nome = EQUIPE[i][1] if i < len(EQUIPE) else None
    for j in range(ESP_N):
        c = ws_mat.cell(row=r, column=ESP_C1 + j)
        c.border = BORD; c.font = F_ENTRADA; c.alignment = CTR; c.number_format = "0"
        if nome and j < len(ESPECIALIDADES):
            c.value = SKILLS[nome][j]
    med = ws_mat.cell(row=r, column=ESP_C2 + 1, value=(
        "=IF($B%d=\"\",\"\",IFERROR(SUMPRODUCT((Matriz_Esp<>\"\")*${l1}%d:${l2}%d)/SUMPRODUCT(--(Matriz_Esp<>\"\")),\"\"))"
        % (r, r, r)).replace("${l1}", ESP_L1).replace("${l2}", ESP_L2))
    med.number_format = "0.00"; med.border = BORD; med.alignment = CTR
    apt = ws_mat.cell(row=r, column=ESP_C2 + 2, value=(
        "=IF($B%d=\"\",\"\",SUMPRODUCT((Matriz_Esp<>\"\")*(${l1}%d:${l2}%d>=2)))" % (r, r, r)
    ).replace("${l1}", ESP_L1).replace("${l2}", ESP_L2))
    apt.number_format = "0"; apt.border = BORD; apt.alignment = CTR
ws_mat.freeze_panes = "D2"

# ---------------------------------------------------------------- MAPA CIRÚRGICO
head(ws_map, 1, ["Data", "Sala", "Turno", "Hora início", "Hora fim", "Especialidade", "Procedimento",
                 "Cirurgião", "Porte", "Status", "Duração (min)", "Min. ocupação (dur+setup)",
                 "Alerta", "aux_concat", "aux_ini", "aux_fim"])
widths(ws_map, {"A": 12, "B": 9, "C": 10, "D": 11, "E": 11, "F": 24, "G": 34, "H": 16, "I": 7,
                "J": 12, "K": 13, "L": 20, "M": 34, "N": 10})
for _c in ("N", "O", "P"):
    ws_map.column_dimensions[_c].hidden = True
fmt_range(ws_map, MP_R1, MP_R2, 1, 10, align=CTR)
for i in range(MAPA_N):
    r = MP_R1 + i
    ws_map.cell(row=r, column=1).number_format = "DD/MM/YYYY"
    ws_map.cell(row=r, column=4).number_format = "HH:MM"
    ws_map.cell(row=r, column=5).number_format = "HH:MM"
    ws_map.cell(row=r, column=6).alignment = LFT
    ws_map.cell(row=r, column=7).alignment = LFT
    ws_map.cell(row=r, column=8).alignment = LFT
    if i < len(MAPA):
        d, sala, turno, ini, fim, esp, proc, cir, porte, status = MAPA[i]
        ws_map.cell(row=r, column=1, value=d)
        ws_map.cell(row=r, column=2, value=sala); ws_map.cell(row=r, column=3, value=turno)
        ws_map.cell(row=r, column=4, value=time(ini // 60, ini % 60))
        ws_map.cell(row=r, column=5, value=time(fim // 60, fim % 60))
        ws_map.cell(row=r, column=6, value=esp); ws_map.cell(row=r, column=7, value=proc)
        ws_map.cell(row=r, column=8, value=cir); ws_map.cell(row=r, column=9, value=porte)
        ws_map.cell(row=r, column=10, value=status)
    k = ws_map.cell(row=r, column=11, value=(
        '=IF(OR($B{r}="",NOT(ISNUMBER($D{r})),NOT(ISNUMBER($E{r}))),"",'
        'ROUND(MOD($E{r}-$D{r},1)*1440,0))').format(r=r))
    k.number_format = "0"; k.border = BORD; k.alignment = CTR; k.font = F_FORMULA
    l = ws_map.cell(row=r, column=12, value=(
        '=IF(NOT(ISNUMBER($K{r})),0,IF(OR($K{r}<=0,$J{r}="Cancelada",$J{r}="Suspensa"),0,$K{r}+Setup_Min))').format(r=r))
    for cc, ccol, src in ((None, 15, "D"), (None, 16, "E")):
        h = ws_map.cell(row=r, column=ccol, value='=IF(ISNUMBER(${s}{r}),${s}{r},0)'.format(s=src, r=r))
        h.font = F_FORMULA
    l.number_format = "0"; l.border = BORD; l.alignment = CTR; l.font = F_FORMULA
    aux = (
        '=IF($B{r}="","",'
        'IF(COUNTIF(Salas_Cod,$B{r})=0,"Sala não cadastrada | ","")&'
        'IF(AND(COUNTIF(Salas_Cod,$B{r})>0,IFERROR(INDEX(Salas_Status,MATCH($B{r},Salas_Cod,0)),"")<>"Ativa"),"Sala bloqueada | ","")&'
        'IF(COUNTIF(Turnos_Nome,$C{r})=0,"Turno inválido | ","")&'
        'IF(COUNTIF(Esp_Nome,$F{r})=0,"Especialidade não cadastrada | ","")&'
        'IF(COUNTIF(Lista_StatusCirurgia,$J{r})=0,"Status inválido | ","")&'
        'IF(OR(NOT(ISNUMBER($D{r})),NOT(ISNUMBER($E{r}))),"Horário inválido | ","")&'
        'IFERROR(IF(AND(ISNUMBER($D{r}),ISNUMBER($E{r}),MOD($E{r}-$D{r},1)*1440<=0),"Duração nula ou negativa | ",""),"")&'
        'IFERROR(IF(AND(ISNUMBER($D{r}),COUNTIF(Turnos_Nome,$C{r})>0,'
        'MOD($D{r}-INDEX(Turnos_Ini,MATCH($C{r},Turnos_Nome,0)),1)*1440>=INDEX(Turnos_Min,MATCH($C{r},Turnos_Nome,0))),'
        '"Início fora da janela do turno | ",""),"")&'
        'IFERROR(IF(AND($L{r}>0,SUMPRODUCT((Mapa_Sala=$B{r})*(Mapa_Data=$A{r})*(Mapa_MinOcup>0)*'
        '(((MOD(Mapa_IniNum-$O{r},1)<MOD($P{r}-$O{r},1))+(MOD($O{r}-Mapa_IniNum,1)<MOD(Mapa_FimNum-Mapa_IniNum,1)))>0))>1),'
        '"Sobreposição de horário na sala | ",""),"")&'
        'IFERROR(IF(AND(ISNUMBER($K{r}),$K{r}>0,COUNTIF(Esp_Nome,$F{r})>0,'
        '$K{r}>3*INDEX(Esp_Dur,MATCH($F{r},Esp_Nome,0))),"Duração atípica (>3x a média) | ",""),""))'
    ).format(r=r)
    a = ws_map.cell(row=r, column=14, value=aux); a.font = F_FORMULA
    m = ws_map.cell(row=r, column=13, value='=IF($B{r}="","",IF($N{r}="","OK",LEFT($N{r},LEN($N{r})-3)))'.format(r=r))
    m.border = BORD; m.alignment = LFT; m.font = F_FORMULA
ws_map.freeze_panes = "C2"; ws_map.auto_filter.ref = "A1:M%d" % MP_R2

# ---------------------------------------------------------------- CALC_MIX
head(ws_mix, 1, ["Chave", "Sala", "Turno"] + [""] * ESP_N +
     ["Total min. ocupação", "Min. disponíveis", "Ocupação %"], height=146)
for i in range(ESP_N):
    c = ws_mix.cell(row=1, column=ESP_C1 + i, value='=IF(%s="","",%s)' % (
        R(S_ESP, "$B$%d" % (ESP_R1 + i)), R(S_ESP, "$B$%d" % (ESP_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD
    c.alignment = Alignment(horizontal="center", vertical="bottom", text_rotation=90)
widths(ws_mix, {"A": 18, "B": 9, "C": 10})
for i in range(ESP_N):
    ws_mix.column_dimensions[get_column_letter(ESP_C1 + i)].width = 6
ws_mix.column_dimensions[get_column_letter(ESP_C2 + 1)].width = 12
ws_mix.column_dimensions[get_column_letter(ESP_C2 + 2)].width = 12
ws_mix.column_dimensions[get_column_letter(ESP_C2 + 3)].width = 11
for i in range(COMBO_N):
    r = CB_R1 + i
    sala_r = SL_R1 + i // len(TURNOS)
    turno_r = 32 + i % len(TURNOS)
    b = ws_mix.cell(row=r, column=2, value='=IF(%s="","",%s)' % (
        R(S_SAL, "$A$%d" % sala_r), R(S_SAL, "$A$%d" % sala_r)))
    c = ws_mix.cell(row=r, column=3, value='=IF($B%d="","",%s)' % (r, R(S_PAR, "$A$%d" % turno_r)))
    a = ws_mix.cell(row=r, column=1, value='=IF($B{r}="","",$B{r}&" | "&$C{r})'.format(r=r))
    for cc in (a, b, c):
        cc.border = BORD; cc.alignment = CTR; cc.font = F_REF
    for j in range(ESP_N):
        col = get_column_letter(ESP_C1 + j)
        f = ('=IF(OR($B{r}="",{col}$1=""),0,SUMIFS(Mapa_MinOcup,Mapa_Sala,$B{r},Mapa_Turno,$C{r},'
             'Mapa_Esp,{col}$1))').format(r=r, col=col)
        cell = ws_mix.cell(row=r, column=ESP_C1 + j, value=f)
        cell.border = BORD; cell.alignment = CTR; cell.number_format = "0"; cell.font = F_FORMULA
    x = ws_mix.cell(row=r, column=ESP_C2 + 1, value='=IF($B{r}="",0,SUM({l1}{r}:{l2}{r}))'.format(
        r=r, l1=ESP_L1, l2=ESP_L2))
    y = ws_mix.cell(row=r, column=ESP_C2 + 2, value=(
        '=IF($B{r}="",0,IFERROR(INDEX(Turnos_Min,MATCH($C{r},Turnos_Nome,0)),0))').format(r=r))
    z = ws_mix.cell(row=r, column=ESP_C2 + 3, value=(
        '=IF(OR($B{r}="",{cy}{r}=0),"",{cx}{r}/{cy}{r})').format(
        r=r, cx=get_column_letter(ESP_C2 + 1), cy=get_column_letter(ESP_C2 + 2)))
    for cc, nf in ((x, "0"), (y, "0"), (z, "0.0%")):
        cc.border = BORD; cc.alignment = CTR; cc.number_format = nf; cc.font = F_FORMULA
ws_mix.freeze_panes = "D2"

# ---------------------------------------------------------------- CALC_AFINIDADE
head(ws_afi, 1, ["Matrícula", "Nome do técnico", "Status", "Turno preferencial"] + [""] * COMBO_N, height=96)
for i in range(COMBO_N):
    c = ws_afi.cell(row=1, column=5 + i, value='=IF(%s="","",%s)' % (
        R(S_MIX, "$A$%d" % (CB_R1 + i)), R(S_MIX, "$A$%d" % (CB_R1 + i))))
    c.font = F_HEAD; c.fill = FILL_HEAD
    c.alignment = Alignment(horizontal="center", vertical="bottom", text_rotation=90)
widths(ws_afi, {"A": 11, "B": 26, "C": 11, "D": 14})
for i in range(COMBO_N):
    ws_afi.column_dimensions[get_column_letter(5 + i)].width = 7
for i in range(EQ_N):
    r = EQ_R1 + i
    a = ws_afi.cell(row=r, column=1, value='=IF(%s="","",%s)' % (R(S_MAT, "A%d" % r), R(S_MAT, "A%d" % r)))
    b = ws_afi.cell(row=r, column=2, value='=IF(%s="","",%s)' % (R(S_MAT, "B%d" % r), R(S_MAT, "B%d" % r)))
    c = ws_afi.cell(row=r, column=3, value=(
        '=IF($A{r}="","",IFERROR(INDEX(Equipe_Status,MATCH($B{r},Equipe_Nome,0)),"?"))').format(r=r))
    d = ws_afi.cell(row=r, column=4, value=(
        '=IF($A{r}="","",IFERROR(INDEX(Equipe_Turno,MATCH($B{r},Equipe_Nome,0)),"?"))').format(r=r))
    for cc in (a, b, c, d):
        cc.border = BORD; cc.font = F_REF; cc.alignment = CTR
    b.alignment = LFT
    for j in range(COMBO_N):
        mixr = CB_R1 + j
        f = ('=IF(OR($B{r}="",$C{r}<>"Ativo",$D{r}<>{tn},{mx}=0,'
             'COUNTIFS(Esc_Turno,{tn},Esc_Circ,$B{r})+COUNTIFS(Esc_Turno,{tn},Esc_Instr,$B{r})>0),"",'
             'IF(SUMPRODUCT({mixrow},{matrow})=0,"",SUMPRODUCT({mixrow},{matrow})/{mx}+ROW()*0.000001))').format(
            r=r, tn=R(S_MIX, "$C$%d" % mixr),
            mx=R(S_MIX, "$%s$%d" % (get_column_letter(ESP_C2 + 1), mixr)),
            mixrow=R(S_MIX, "$%s$%d:$%s$%d" % (ESP_L1, mixr, ESP_L2, mixr)),
            matrow=R(S_MAT, "$%s%d:$%s%d" % (ESP_L1, r, ESP_L2, r)))
        cell = ws_afi.cell(row=r, column=5 + j, value=f)
        cell.border = BORD; cell.alignment = CTR; cell.number_format = "0.00"; cell.font = F_FORMULA
ws_afi.freeze_panes = "E2"

# ---------------------------------------------------------------- ESCALA DE DUPLAS
ESC_HDR = ["Data", "Sala", "Turno", "Nº cirurgias", "Min. ocupação", "Min. do turno", "Ocupação %",
           "CIRCULANTE (escalar)", "Cadastro do circulante", "INSTRUMENTADOR (escalar)",
           "Cadastro do instrumentador", "Afinidade circulante", "Afinidade instrumentador",
           "AFINIDADE DA DUPLA", "Classificação", "Chk duplicidade", "Chk status", "Chk função",
           "Chk inaptidão", "ALERTAS", "aux_concat", "aux_afin", "aux_peso"]
head(ws_esc, 1, ESC_HDR, height=46)
widths(ws_esc, {"A": 11, "B": 9, "C": 10, "D": 9, "E": 11, "F": 11, "G": 11, "H": 25, "I": 21,
                "J": 25, "K": 21, "L": 11, "M": 12, "N": 12, "O": 14, "P": 20, "Q": 20, "R": 20,
                "S": 34, "T": 62, "U": 8, "V": 8, "W": 8})
for col in ("U", "V", "W"):
    ws_esc.column_dimensions[col].hidden = True

for i in range(COMBO_N):
    r = CB_R1 + i
    sala_idx, turno_idx = i // len(TURNOS), i % len(TURNOS)
    f = {}
    f["A"] = '=IF($B{r}="","",Data_Mapa)'.format(r=r)
    f["B"] = '=IF(%s="","",%s)' % (R(S_MIX, "$B%d" % r), R(S_MIX, "$B%d" % r))
    f["C"] = '=IF($B{r}="","",{c})'.format(r=r, c=R(S_MIX, "$C%d" % r))
    f["D"] = ('=IF($B{r}="","",COUNTIFS(Mapa_Sala,$B{r},Mapa_Turno,$C{r},Mapa_MinOcup,">0"))').format(r=r)
    f["E"] = '=IF($B{r}="","",{c})'.format(r=r, c=R(S_MIX, "$%s%d" % (get_column_letter(ESP_C2 + 1), r)))
    f["F"] = '=IF($B{r}="","",{c})'.format(r=r, c=R(S_MIX, "$%s%d" % (get_column_letter(ESP_C2 + 2), r)))
    f["G"] = '=IF(OR($B{r}="",$F{r}=0),"",$E{r}/$F{r})'.format(r=r)
    f["I"] = ('=IF($H{r}="","",IFERROR(INDEX(Equipe_Funcao,MATCH($H{r},Equipe_Nome,0))&" · "&'
              'INDEX(Equipe_Status,MATCH($H{r},Equipe_Nome,0)),"NÃO CADASTRADO"))').format(r=r)
    f["K"] = ('=IF($J{r}="","",IFERROR(INDEX(Equipe_Funcao,MATCH($J{r},Equipe_Nome,0))&" · "&'
              'INDEX(Equipe_Status,MATCH($J{r},Equipe_Nome,0)),"NÃO CADASTRADO"))').format(r=r)
    for tgt, key in (("L", "H"), ("M", "J")):
        f[tgt] = ('=IF(OR($B{r}="",${k}{r}="",$E{r}=0),"",IFERROR(SUMPRODUCT({mixrow},'
                  'INDEX(Matriz_Niveis,MATCH(${k}{r},Matriz_Nome,0),0))/{mx},""))').format(
            r=r, k=key, mixrow=R(S_MIX, "$%s%d:$%s%d" % (ESP_L1, r, ESP_L2, r)),
            mx=R(S_MIX, "$%s%d" % (get_column_letter(ESP_C2 + 1), r)))
    f["N"] = ('=IF(OR($L{r}="",$M{r}=""),"",Peso_Circulante*$L{r}+Peso_Instrumentador*$M{r})').format(r=r)
    f["O"] = ('=IF($B{r}="","",IF($D{r}=0,"SEM CIRURGIA",IF($N{r}="","SEM DUPLA",'
              'IF($N{r}>=Afinidade_Meta,"ADEQUADA",IF($N{r}>=Afinidade_Min,"ATENÇÃO","CRÍTICA")))))').format(r=r)
    f["P"] = ('=IF($B{r}="","",IF(AND($H{r}="",$J{r}=""),"OK",IF(OR('
              'AND($H{r}<>"",SUMPRODUCT((Esc_Turno=$C{r})*(Esc_Circ=$H{r}))+SUMPRODUCT((Esc_Turno=$C{r})*(Esc_Instr=$H{r}))>1),'
              'AND($J{r}<>"",SUMPRODUCT((Esc_Turno=$C{r})*(Esc_Circ=$J{r}))+SUMPRODUCT((Esc_Turno=$C{r})*(Esc_Instr=$J{r}))>1)),'
              '"Técnico em duas salas no mesmo turno","OK")))').format(r=r)
    f["Q"] = ('=IF($B{r}="","",IF(AND($H{r}="",$J{r}=""),"OK",IF(OR('
              'AND($H{r}<>"",IFERROR(INDEX(Equipe_Status,MATCH($H{r},Equipe_Nome,0)),"?")<>"Ativo"),'
              'AND($J{r}<>"",IFERROR(INDEX(Equipe_Status,MATCH($J{r},Equipe_Nome,0)),"?")<>"Ativo")),'
              '"Técnico não ativo ou não cadastrado","OK")))').format(r=r)
    f["R"] = ('=IF($B{r}="","",IF(AND($H{r}="",$J{r}=""),"OK",IF(OR('
              'AND($H{r}<>"",IFERROR(INDEX(Equipe_Funcao,MATCH($H{r},Equipe_Nome,0)),"")="Instrumentador"),'
              'AND($J{r}<>"",IFERROR(INDEX(Equipe_Funcao,MATCH($J{r},Equipe_Nome,0)),"")="Circulante")),'
              '"Função incompatível com o posto","OK")))').format(r=r)
    f["S"] = ('=IF($B{r}="","",IF(OR($E{r}=0,AND($H{r}="",$J{r}="")),"OK",IF('
              'IFERROR(SUMPRODUCT(({mixrow}/{mx}>=Part_Min_Critica)*'
              '(INDEX(Matriz_Niveis,MATCH($H{r},Matriz_Nome,0),0)<=Nivel_Critico)),0)+'
              'IFERROR(SUMPRODUCT(({mixrow}/{mx}>=Part_Min_Critica)*'
              '(INDEX(Matriz_Niveis,MATCH($J{r},Matriz_Nome,0),0)<=Nivel_Critico)),0)>0,'
              '"Inaptidão em especialidade relevante","OK")))').format(
        r=r, mixrow=R(S_MIX, "$%s%d:$%s%d" % (ESP_L1, r, ESP_L2, r)),
        mx=R(S_MIX, "$%s%d" % (get_column_letter(ESP_C2 + 1), r)))
    f["U"] = ('=IF($B{r}="","",'
              'IF(AND($D{r}>0,$H{r}=""),"Sem circulante | ","")&'
              'IF(AND($D{r}>0,$J{r}=""),"Sem instrumentador | ","")&'
              'IF(AND($D{r}=0,OR($H{r}<>"",$J{r}<>"")),"Dupla escalada em sala sem cirurgia | ","")&'
              'IF($P{r}<>"OK",$P{r}&" | ","")&IF($Q{r}<>"OK",$Q{r}&" | ","")&'
              'IF($R{r}<>"OK",$R{r}&" | ","")&IF($S{r}<>"OK",$S{r}&" | ","")&'
              'IF(AND($N{r}<>"",$N{r}<Afinidade_Min),"Afinidade abaixo do mínimo | ","")&'
              'IF(AND($G{r}<>"",$G{r}>Ocupacao_Max),"Ocupação acima do limite | ","")&'
              'IF(OR(AND($H{r}<>"",IFERROR(INDEX(Equipe_Turno,MATCH($H{r},Equipe_Nome,0)),$C{r})<>$C{r}),'
              'AND($J{r}<>"",IFERROR(INDEX(Equipe_Turno,MATCH($J{r},Equipe_Nome,0)),$C{r})<>$C{r})),'
              '"Técnico fora do turno preferencial | ","")&'
              'IF(AND($D{r}>0,IFERROR(INDEX(Salas_Status,MATCH($B{r},Salas_Cod,0)),"")<>"Ativa"),'
              '"Sala não ativa com cirurgia | ",""))').format(r=r)
    f["T"] = ('=IF($B{r}="",IF(OR($H{r}<>"",$J{r}<>""),'
              '"Linha sem sala cadastrada — remova a dupla",""),'
              'IF($U{r}="","OK",LEFT($U{r},LEN($U{r})-3)))').format(r=r)
    f["V"] = '=IF($N{r}="",0,$N{r})'.format(r=r)
    f["W"] = '=IF($N{r}="",0,$E{r})'.format(r=r)

    for col, formula in f.items():
        cell = ws_esc[col + str(r)]
        cell.value = formula; cell.border = BORD; cell.font = F_FORMULA
        cell.alignment = CTR
    for col in ("I", "K", "P", "Q", "R", "S"):
        ws_esc[col + str(r)].alignment = LFT
    ws_esc["T" + str(r)].alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    ws_esc["A%d" % r].number_format = "DD/MM/YYYY"
    ws_esc["G%d" % r].number_format = "0.0%"
    for col in ("L", "M", "N", "V"):
        ws_esc[col + str(r)].number_format = "0.00"
    for col in ("D", "E", "F", "W"):
        ws_esc[col + str(r)].number_format = "0"
    ws_esc["I%d" % r].font = F_REF; ws_esc["K%d" % r].font = F_REF
    for col in ("H", "J"):
        c = ws_esc[col + str(r)]
        c.font = F_ENTRADA; c.fill = FILL_ENT; c.alignment = LFT
    if sala_idx < len(SALAS):
        key = (SALAS[sala_idx][0], TURNOS[turno_idx])
        if key in ALOC:
            ws_esc["H%d" % r] = ALOC[key][0]
            ws_esc["J%d" % r] = ALOC[key][1]
ws_esc.freeze_panes = "D2"; ws_esc.auto_filter.ref = "A1:T%d" % CB_R2

# ---------------------------------------------------------------- SUGESTÃO DE DUPLAS
SUG_HDR = ["Sala", "Turno", "Especialidade predominante", "Min. ocupação"]
for k in range(1, 5):
    SUG_HDR += ["%dª opção (técnico livre)" % k, "Função · Turno", "Afinidade"]
head(ws_sug, 1, SUG_HDR, height=32)
ws_sug.cell(row=1, column=1).comment = None
widths(ws_sug, {"A": 9, "B": 10, "C": 26, "D": 12, "E": 24, "F": 22, "G": 10, "H": 24, "I": 22,
                "J": 10, "K": 24, "L": 22, "M": 10, "N": 24, "O": 22, "P": 10})
for i in range(COMBO_N):
    r = CB_R1 + i
    afi_col = get_column_letter(5 + i)
    rng = R(S_AFI, "%s$%d:%s$%d" % (afi_col, EQ_R1, afi_col, EQ_R2))
    vals = {
        "A": '=IF(%s="","",%s)' % (R(S_ESC, "$B%d" % r), R(S_ESC, "$B%d" % r)),
        "B": '=IF($A{r}="","",{c})'.format(r=r, c=R(S_ESC, "$C%d" % r)),
        "C": ('=IF($A{r}="","",IF({mx}=0,"—",IFERROR(INDEX(Mix_Esp,MATCH(MAX({mixrow}),{mixrow},0)),"—")))').format(
            r=r, mx=R(S_MIX, "$%s%d" % (get_column_letter(ESP_C2 + 1), r)),
            mixrow=R(S_MIX, "$%s%d:$%s%d" % (ESP_L1, r, ESP_L2, r))),
        "D": '=IF($A{r}="","",{c})'.format(r=r, c=R(S_MIX, "$%s%d" % (get_column_letter(ESP_C2 + 1), r))),
    }
    for k in range(4):
        cn, cf, ca = get_column_letter(5 + k * 3), get_column_letter(6 + k * 3), get_column_letter(7 + k * 3)
        vals[cn] = ('=IF($A{r}="","",IFERROR(INDEX({nomes},MATCH(LARGE({rng},{k}),{rng},0)),"—"))').format(
            r=r, nomes=R(S_AFI, "$B$%d:$B$%d" % (EQ_R1, EQ_R2)), rng=rng, k=k + 1)
        vals[cf] = ('=IF({cn}{r}="—","",IFERROR(INDEX(Equipe_Funcao,MATCH({cn}{r},Equipe_Nome,0))&" · "&'
                    'INDEX({tp},MATCH({cn}{r},Equipe_Nome,0)),""))').format(
            cn=cn, r=r, tp=R(S_EQP, "$D$%d:$D$%d" % (EQ_R1, EQ_R2)))
        vals[ca] = '=IF($A{r}="","",IFERROR(ROUND(LARGE({rng},{k}),2),""))'.format(r=r, rng=rng, k=k + 1)
    for col, formula in vals.items():
        cell = ws_sug[col + str(r)]
        cell.value = formula; cell.border = BORD; cell.font = F_FORMULA; cell.alignment = CTR
    for col in ("C", "E", "F", "H", "I", "K", "L", "N", "O"):
        ws_sug[col + str(r)].alignment = LFT
        ws_sug[col + str(r)].font = F_REF
    ws_sug["D%d" % r].number_format = "0"
    for k in range(4):
        ws_sug[get_column_letter(7 + k * 3) + str(r)].number_format = "0.00"
ws_sug.freeze_panes = "C2"; ws_sug.auto_filter.ref = "A1:P%d" % CB_R2

dn("Esc_Alertas", R(S_ESC, "$T$%d:$T$%d" % (CB_R1, CB_R2)))
dn("Equipe_Turno", R(S_EQP, "$D$%d:$D$%d" % (EQ_R1, EQ_R2)))

# ---------------------------------------------------------------- PAINEL
title(ws_pai, "PAINEL DO CENTRO CIRÚRGICO",
      "Camada executiva. Todos os números vêm de fórmulas vivas sobre Mapa_Cirurgico e Escala_Duplas — altere qualquer entrada e este painel se atualiza.")
widths(ws_pai, {"A": 26, "B": 30, "C": 15, "D": 15, "E": 15, "F": 15, "G": 15, "H": 15, "I": 3})

def bloco(row, texto):
    c = ws_pai.cell(row=row, column=1, value=texto); c.font = F_SEC

bloco(4, "1. INDICADORES DO DIA")
head(ws_pai, 5, ["Data do mapa", "Cirurgias programadas", "Canceladas / suspensas",
                 "Horas cirúrgicas", "Ocupação média das salas", "Afinidade média das duplas",
                 "Duplas com alerta", "Técnicos escalados"], height=32)
kpis = ["=Data_Mapa",
        '=COUNTIFS(Mapa_MinOcup,">0")',
        '=COUNTIF(Mapa_Status,"Cancelada")+COUNTIF(Mapa_Status,"Suspensa")',
        '=SUMIFS(Mapa_Dur,Mapa_MinOcup,">0")/60',
        '=IFERROR(SUM(Esc_MinOcup)/SUM(Esc_MinTurno),"")',
        '=IFERROR(SUMPRODUCT(Esc_AfinNum,Esc_Peso)/SUM(Esc_Peso),"")',
        '=SUMPRODUCT((Esc_Alertas<>"OK")*(Esc_Alertas<>""))',
        '=SUMPRODUCT((Equipe_Nome<>"")*((COUNTIF(Esc_Circ,Equipe_Nome)+COUNTIF(Esc_Instr,Equipe_Nome))>0))']
fmts = ["DD/MM/YYYY", "0", "0", "0.0", "0.0%", "0.00", "0", "0"]
for j, (v, nf) in enumerate(zip(kpis, fmts)):
    c = ws_pai.cell(row=6, column=1 + j, value=v)
    c.number_format = nf; c.border = BORD; c.alignment = CTR
    c.font = Font(name="Calibri", size=12, bold=True, color=AZ_ESC); c.fill = FILL_ENT
ws_pai.row_dimensions[6].height = 26

bloco(8, "2. DESEMPENHO POR SALA")
head(ws_pai, 9, ["Sala", "Descrição", "Nº cirurgias", "Horas de ocupação", "Ocupação média",
                 "Afinidade média", "Duplas críticas", "Duplas com alerta"], height=30)
for i in range(SALA_N):
    r, sr = 10 + i, SL_R1 + i
    fs = {
        1: '=IF(%s="","",%s)' % (R(S_SAL, "$A$%d" % sr), R(S_SAL, "$A$%d" % sr)),
        2: '=IF($A{r}="","",{c})'.format(r=r, c=R(S_SAL, "$B$%d" % sr)),
        3: '=IF($A{r}="","",SUMIFS(Esc_NCir,Esc_Sala,$A{r}))'.format(r=r),
        4: '=IF($A{r}="","",SUMIFS(Esc_MinOcup,Esc_Sala,$A{r})/60)'.format(r=r),
        5: '=IF(OR($A{r}="",SUMIFS(Esc_MinTurno,Esc_Sala,$A{r})=0),"",SUMIFS(Esc_MinOcup,Esc_Sala,$A{r})/SUMIFS(Esc_MinTurno,Esc_Sala,$A{r}))'.format(r=r),
        6: '=IF($A{r}="","",IFERROR(SUMPRODUCT((Esc_Sala=$A{r})*Esc_AfinNum*Esc_Peso)/SUMPRODUCT((Esc_Sala=$A{r})*Esc_Peso),""))'.format(r=r),
        7: '=IF($A{r}="","",COUNTIFS(Esc_Sala,$A{r},Esc_Class,"CRÍTICA")+COUNTIFS(Esc_Sala,$A{r},Esc_Class,"SEM DUPLA"))'.format(r=r),
        8: '=IF($A{r}="","",SUMPRODUCT((Esc_Sala=$A{r})*(Esc_Alertas<>"OK")*(Esc_Alertas<>"")))'.format(r=r),
    }
    for col, v in fs.items():
        c = ws_pai.cell(row=r, column=col, value=v); c.border = BORD; c.alignment = CTR
        c.font = F_FORMULA
    ws_pai.cell(row=r, column=2).alignment = LFT
    ws_pai.cell(row=r, column=4).number_format = "0.0"
    ws_pai.cell(row=r, column=5).number_format = "0.0%"
    ws_pai.cell(row=r, column=6).number_format = "0.00"

bloco(23, "3. DESEMPENHO POR TURNO")
head(ws_pai, 24, ["Turno", "Nº cirurgias", "Horas de ocupação", "Ocupação média",
                  "Afinidade média", "Duplas com alerta"], height=30)
for i in range(len(TURNOS)):
    r, pr = 25 + i, 32 + i
    fs = {
        1: '=%s' % R(S_PAR, "$A$%d" % pr),
        2: '=SUMIFS(Esc_NCir,Esc_Turno,$A{r})'.format(r=r),
        3: '=SUMIFS(Esc_MinOcup,Esc_Turno,$A{r})/60'.format(r=r),
        4: '=IFERROR(SUMIFS(Esc_MinOcup,Esc_Turno,$A{r})/SUMIFS(Esc_MinTurno,Esc_Turno,$A{r}),"")'.format(r=r),
        5: '=IFERROR(SUMPRODUCT((Esc_Turno=$A{r})*Esc_AfinNum*Esc_Peso)/SUMPRODUCT((Esc_Turno=$A{r})*Esc_Peso),"")'.format(r=r),
        6: '=SUMPRODUCT((Esc_Turno=$A{r})*(Esc_Alertas<>"OK")*(Esc_Alertas<>""))'.format(r=r),
    }
    for col, v in fs.items():
        c = ws_pai.cell(row=r, column=col, value=v); c.border = BORD; c.alignment = CTR; c.font = F_FORMULA
    ws_pai.cell(row=r, column=3).number_format = "0.0"
    ws_pai.cell(row=r, column=4).number_format = "0.0%"
    ws_pai.cell(row=r, column=5).number_format = "0.00"

bloco(29, "4. DEMANDA × CAPACIDADE POR ESPECIALIDADE")
head(ws_pai, 30, ["Especialidade", "Nº cirurgias", "Horas cirúrgicas", "% das horas",
                  "Técnicos aptos (nível ≥ 2)", "Técnicos referência (nível 3)",
                  "Cobertura mínima (≥ 6 aptos)"], height=42)
for i in range(ESP_N):
    r, er = 31 + i, ESP_R1 + i
    mcol = get_column_letter(ESP_C1 + i)
    mrng = R(S_MAT, "$%s$%d:$%s$%d" % (mcol, EQ_R1, mcol, EQ_R2))
    fs = {
        1: '=IF(%s="","",%s)' % (R(S_ESP, "$B$%d" % er), R(S_ESP, "$B$%d" % er)),
        2: '=IF($A{r}="","",COUNTIFS(Mapa_Esp,$A{r},Mapa_MinOcup,">0"))'.format(r=r),
        3: '=IF($A{r}="","",SUMIFS(Mapa_Dur,Mapa_Esp,$A{r},Mapa_MinOcup,">0")/60)'.format(r=r),
        4: '=IF(OR($A{r}="",SUM($C$31:$C${last})=0),"",$C{r}/SUM($C$31:$C${last}))'.format(r=r, last=30 + ESP_N),
        5: '=IF($A{r}="","",SUMPRODUCT((Equipe_Status="Ativo")*({m}>=2)))'.format(r=r, m=mrng),
        6: '=IF($A{r}="","",SUMPRODUCT((Equipe_Status="Ativo")*({m}=3)))'.format(r=r, m=mrng),
        7: '=IF($A{r}="","",IF($E{r}>=6,"OK","ATENÇÃO"))'.format(r=r),
    }
    for col, v in fs.items():
        c = ws_pai.cell(row=r, column=col, value=v); c.border = BORD; c.alignment = CTR; c.font = F_FORMULA
    ws_pai.cell(row=r, column=1).alignment = LFT
    ws_pai.cell(row=r, column=3).number_format = "0.0"
    ws_pai.cell(row=r, column=4).number_format = "0.0%"

CHECK_ROW = 31 + ESP_N + 1
bloco(CHECK_ROW, "5. VERIFICAÇÕES DE INTEGRIDADE")
head(ws_pai, CHECK_ROW + 1, ["Verificação", "Resultado", "", "", "", "", "", ""], height=20)
CHECKS = [
    ("Soma dos pesos de afinidade = 1,00",
     '=IF(ROUND(Peso_Circulante+Peso_Instrumentador,6)=1,"OK","ERRO: os pesos não somam 1,00")'),
    ("Colunas de especialidade alinhadas (Matriz × Calc_Mix)",
     '=IF(SUMPRODUCT(--(Matriz_Esp=Mix_Esp))={n},"OK","ERRO: colunas desalinhadas")'.format(n=ESP_N)),
    ("Nomes duplicados no cadastro da equipe",
     '=IF(SUMPRODUCT((Equipe_Nome<>"")*1)-SUMPRODUCT((Equipe_Nome<>"")/COUNTIF(Equipe_Nome,Equipe_Nome&""))>0.0001,'
     '"ERRO: há nomes repetidos na aba Equipe","OK")'),
    ("Cirurgias com alerta no mapa", '=SUMPRODUCT((Mapa_Alerta<>"OK")*(Mapa_Alerta<>""))'),
    ("Salas/turnos com cirurgia e sem dupla escalada", '=COUNTIF(Esc_Class,"SEM DUPLA")'),
    ("Duplas classificadas como CRÍTICA", '=COUNTIF(Esc_Class,"CRÍTICA")'),
    ("Duplas classificadas como ATENÇÃO", '=COUNTIF(Esc_Class,"ATENÇÃO")'),
    ("Técnicos ativos sem escala no dia",
     '=SUMPRODUCT((Equipe_Nome<>"")*(Equipe_Status="Ativo")*((COUNTIF(Esc_Circ,Equipe_Nome)+COUNTIF(Esc_Instr,Equipe_Nome))=0))'),
    ("Técnicos escalados fora do turno preferencial",
     '=SUMPRODUCT((Esc_Circ<>"")*(1-COUNTIFS(Equipe_Nome,Esc_Circ,Equipe_Turno,Esc_Turno)))'
     '+SUMPRODUCT((Esc_Instr<>"")*(1-COUNTIFS(Equipe_Nome,Esc_Instr,Equipe_Turno,Esc_Turno)))'),
    ("Salas cadastradas / especialidades cadastradas",
     '=COUNTA(Salas_Cod)&" / "&COUNTA(Esp_Nome)'),
]
for i, (lbl, f) in enumerate(CHECKS):
    r = CHECK_ROW + 2 + i
    c1 = ws_pai.cell(row=r, column=1, value=lbl); c1.border = BORD; c1.alignment = LFT; c1.font = F_FORMULA
    ws_pai.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    c2 = ws_pai.cell(row=r, column=3, value=f); c2.border = BORD; c2.alignment = CTR; c2.font = F_FORMULA
CHECK_LAST = CHECK_ROW + 1 + len(CHECKS)

# corrige cabeçalho do bloco 5 (rótulo mesclado em A:B, resultado em C)
ws_pai.cell(row=CHECK_ROW + 1, column=2, value="")
ws_pai.cell(row=CHECK_ROW + 1, column=3, value="Resultado")

# ---------------------------------------------------------------- BASE HISTÓRICO
head(ws_his, 1, ["Data", "Sala", "Turno", "Circulante", "Instrumentador", "Afinidade da dupla",
                 "Nº cirurgias", "Min. ocupação", "Ocupação %", "Classificação", "Alertas"])
widths(ws_his, {"A": 12, "B": 9, "C": 10, "D": 25, "E": 25, "F": 14, "G": 12, "H": 13, "I": 12,
                "J": 14, "K": 46, "M": 26, "N": 14})
fmt_range(ws_his, 2, 201, 1, 11, font=F_FORMULA, align=CTR)
for r in range(2, 202):
    ws_his.cell(row=r, column=1).number_format = "DD/MM/YYYY"
    ws_his.cell(row=r, column=6).number_format = "0.00"
    ws_his.cell(row=r, column=9).number_format = "0.0%"
    for c in (4, 5, 11):
        ws_his.cell(row=r, column=c).alignment = LFT
ws_his.freeze_panes = "A2"; ws_his.auto_filter.ref = "A1:K%d" % HIST_R2
ws_his.cell(row=1, column=13, value="RESUMO DO HISTÓRICO").font = F_SEC
resumo = [("Registros acumulados", '=COUNTA($A$2:$A$%d)' % HIST_R2, "0"),
          ("Afinidade média", '=IFERROR(AVERAGE($F$2:$F$%d),"")' % HIST_R2, "0.00"),
          ("Ocupação média", '=IFERROR(AVERAGE($I$2:$I$%d),"")' % HIST_R2, "0.0%"),
          ("Duplas críticas registradas", '=COUNTIF($J$2:$J$%d,"CRÍTICA")' % HIST_R2, "0")]
for i, (lbl, f, nf) in enumerate(resumo):
    r = 2 + i
    a = ws_his.cell(row=r, column=13, value=lbl); a.font = F_FORMULA; a.border = BORD; a.alignment = LFT
    b = ws_his.cell(row=r, column=14, value=f); b.font = F_FORMULA; b.border = BORD
    b.alignment = CTR; b.number_format = nf; b.fill = FILL_ENT

# ---------------------------------------------------------------- VALIDAÇÕES DE DADOS
def add_dv(ws, formula, ranges, allow_blank=True, kind="list", **kw):
    dv = DataValidation(type=kind, formula1=formula, allow_blank=allow_blank, showErrorMessage=True, **kw)
    ws.add_data_validation(dv)
    for rg in ranges:
        dv.add(rg)
    return dv

add_dv(ws_esp, '"Sim,Não"', ["D%d:D%d" % (ESP_R1, ESP_R2)])
add_dv(ws_sal, '"Ativa,Bloqueada,Manutenção"', ["C%d:C%d" % (SL_R1, SL_R2)])
add_dv(ws_eqp, "=Lista_Funcoes", ["C%d:C%d" % (EQ_R1, EQ_R2)])
add_dv(ws_eqp, "=Lista_Turnos", ["D%d:D%d" % (EQ_R1, EQ_R2)])
add_dv(ws_eqp, "=Lista_StatusEquipe", ["E%d:E%d" % (EQ_R1, EQ_R2)])
dvn = add_dv(ws_mat, "0", ["%s%d:%s%d" % (ESP_L1, EQ_R1, ESP_L2, EQ_R2)],
             kind="whole", operator="between", formula2="3")
dvn.errorTitle = "Nível inválido"
dvn.error = "Use apenas 0 (não apto), 1 (em treinamento), 2 (apto) ou 3 (referência)."
add_dv(ws_map, "=Lista_Salas", ["B%d:B%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_Turnos", ["C%d:C%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_Especialidades", ["F%d:F%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_Porte", ["I%d:I%d" % (MP_R1, MP_R2)])
add_dv(ws_map, "=Lista_StatusCirurgia", ["J%d:J%d" % (MP_R1, MP_R2)])
dvt = add_dv(ws_map, "TIME(0,0,0)", ["D%d:E%d" % (MP_R1, MP_R2)], kind="time",
             operator="between", formula2="TIME(23,59,0)")
dvt.errorTitle = "Horário inválido"; dvt.error = "Informe um horário válido no formato HH:MM."
dve = add_dv(ws_esc, "=Lista_Tecnicos", ["H%d:H%d" % (CB_R1, CB_R2), "J%d:J%d" % (CB_R1, CB_R2)])
dve.errorTitle = "Técnico não cadastrado"
dve.error = "Escolha um técnico já cadastrado na aba Equipe."

# ---------------------------------------------------------------- FORMATAÇÃO CONDICIONAL
def fill_of(bg, fg): return (PatternFill("solid", fgColor=bg), Font(color=fg, bold=True))

fv, fvt = fill_of(VERDE, VERDE_T); fa, fat = fill_of(AMAR, AMAR_T); fr, frt = fill_of(VERM, VERM_T)
rng_class = "O%d:O%d" % (CB_R1, CB_R2)
ws_esc.conditional_formatting.add(rng_class, CellIsRule(operator="equal", formula=['"ADEQUADA"'], fill=fv, font=fvt))
ws_esc.conditional_formatting.add(rng_class, CellIsRule(operator="equal", formula=['"ATENÇÃO"'], fill=fa, font=fat))
ws_esc.conditional_formatting.add(rng_class, CellIsRule(operator="equal", formula=['"CRÍTICA"'], fill=fr, font=frt))
ws_esc.conditional_formatting.add(rng_class, CellIsRule(operator="equal", formula=['"SEM DUPLA"'], fill=fr, font=frt))
ws_esc.conditional_formatting.add("T%d:T%d" % (CB_R1, CB_R2),
    FormulaRule(formula=['AND($T2<>"",$T2<>"OK")'], fill=fr, font=frt))
ws_esc.conditional_formatting.add("G%d:G%d" % (CB_R1, CB_R2),
    FormulaRule(formula=['AND($G2<>"",$G2>Ocupacao_Max)'], fill=fr, font=frt, stopIfTrue=True))
ws_esc.conditional_formatting.add("G%d:G%d" % (CB_R1, CB_R2),
    FormulaRule(formula=['AND($G2<>"",$G2>=Meta_Ocupacao)'], fill=fv, font=fvt))
ws_esc.conditional_formatting.add("N%d:N%d" % (CB_R1, CB_R2),
    ColorScaleRule(start_type="num", start_value=0, start_color="F8696B",
                   mid_type="num", mid_value=2, mid_color="FFEB84",
                   end_type="num", end_value=3, end_color="63BE7B"))
for col in ("P", "Q", "R", "S"):
    ws_esc.conditional_formatting.add("%s%d:%s%d" % (col, CB_R1, col, CB_R2),
        FormulaRule(formula=['AND(${c}2<>"",${c}2<>"OK")'.replace("${c}", col)], fill=fr, font=frt))
ws_mat.conditional_formatting.add("%s%d:%s%d" % (ESP_L1, EQ_R1, ESP_L2, EQ_R2),
    ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                   mid_type="num", mid_value=1.5, mid_color="D9E9D2",
                   end_type="num", end_value=3, end_color="4CAF50"))
ws_map.conditional_formatting.add("M%d:M%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['AND($M2<>"",$M2<>"OK")'], fill=fr, font=frt))
ws_map.conditional_formatting.add("J%d:J%d" % (MP_R1, MP_R2),
    FormulaRule(formula=['OR($J2="Cancelada",$J2="Suspensa")'], fill=FILL_CINZ,
                font=Font(color="808080", italic=True)))
ws_pai.conditional_formatting.add("C%d:C%d" % (CHECK_ROW + 2, CHECK_LAST),
    FormulaRule(formula=['LEFT($C%d,4)="ERRO"' % (CHECK_ROW + 2)], fill=fr, font=frt))
ws_pai.conditional_formatting.add("C%d:C%d" % (CHECK_ROW + 2, CHECK_LAST),
    FormulaRule(formula=['$C%d="OK"' % (CHECK_ROW + 2)], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("G31:G%d" % (30 + ESP_N),
    CellIsRule(operator="equal", formula=['"ATENÇÃO"'], fill=fa, font=fat))
ws_pai.conditional_formatting.add("G31:G%d" % (30 + ESP_N),
    CellIsRule(operator="equal", formula=['"OK"'], fill=fv, font=fvt))
ws_pai.conditional_formatting.add("E10:E21",
    FormulaRule(formula=['AND($E10<>"",$E10>Ocupacao_Max)'], fill=fr, font=frt, stopIfTrue=True))
ws_par.conditional_formatting.add("B19", FormulaRule(formula=['ROUND($B$19,6)<>1'], fill=fr, font=frt))
ws_pai.conditional_formatting.add("G10:G21",
    CellIsRule(operator="greaterThan", formula=["0"], fill=fr, font=frt))

# ---------------------------------------------------------------- GRÁFICOS
ch1 = BarChart(); ch1.type = "col"; ch1.title = "Ocupação por sala"
ch1.y_axis.title = "% de ocupação"; ch1.height = 7.5; ch1.width = 16
ch1.add_data(Reference(ws_pai, min_col=5, min_row=9, max_row=21), titles_from_data=True)
ch1.set_categories(Reference(ws_pai, min_col=1, min_row=10, max_row=21))
ch1.y_axis.numFmt = "0%"; ch1.legend = None
ws_pai.add_chart(ch1, "J8")

ch2 = BarChart(); ch2.type = "bar"; ch2.title = "Horas cirúrgicas por especialidade"
ch2.x_axis.title = "Horas"; ch2.height = 11; ch2.width = 16
ch2.add_data(Reference(ws_pai, min_col=3, min_row=30, max_row=30 + ESP_N), titles_from_data=True)
ch2.set_categories(Reference(ws_pai, min_col=1, min_row=31, max_row=30 + ESP_N))
ch2.legend = None
ws_pai.add_chart(ch2, "J30")

# ---------------------------------------------------------------- IMPRESSÃO
for ws, area in ((ws_esc, "A1:T%d" % CB_R2), (ws_map, "A1:M%d" % (MP_R1 + len(MAPA) - 1)),
                 (ws_sug, "A1:P%d" % CB_R2)):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = "1:1"
    ws.print_area = area
ws_pai.page_setup.orientation = "portrait"
ws_pai.print_area = "A1:R%d" % CHECK_LAST

# ---------------------------------------------------------------- INSTRUÇÕES
widths(ws_ins, {"A": 4, "B": 46, "C": 96})
title(ws_ins, "CENTRO CIRÚRGICO — MAPA CIRÚRGICO E ESCALA DE DUPLAS POR SALA",
      "Ferramenta operacional da coordenação de enfermagem. Modelo de alocação: DUPLA FIXA POR SALA NO TURNO, classificada por AFINIDADE DE HABILIDADE.")
LINHAS = [
 ("S", "1. COMO A PLANILHA ESTÁ ORGANIZADA", ""),
 ("H", "ENTRADAS (o que se digita)", "Parâmetros · Especialidades · Salas · Equipe · Matriz_Habilidades · Mapa_Cirurgico · colunas CIRCULANTE/INSTRUMENTADOR da Escala_Duplas"),
 ("H", "PROCESSAMENTO (não digitar)", "Calc_Mix (minutos por especialidade em cada sala × turno) e Calc_Afinidade (afinidade dos técnicos ELEGÍVEIS — ativos, do turno e ainda não escalados — com cada sala × turno). São abas de cálculo, ficam visíveis para auditoria."),
 ("H", "SAÍDAS", "Escala_Duplas (alocação validada) · Sugestao_Duplas (ranking de quem tem mais afinidade) · Painel (visão executiva) · Base_Historico (acúmulo dia a dia)"),
 ("S", "2. A REGRA DE AFINIDADE", ""),
 ("H", "Afinidade do técnico com a sala/turno", "Média dos níveis de habilidade do técnico nas especialidades daquela sala, PONDERADA PELOS MINUTOS de cada especialidade no turno. Especialidade que ocupa mais tempo pesa mais."),
 ("H", "Afinidade da dupla", "Peso_Circulante × afinidade do circulante + Peso_Instrumentador × afinidade do instrumentador. Os dois pesos ficam em Parâmetros (padrão 0,40 / 0,60) e podem ser alterados."),
 ("H", "Classificação", "ADEQUADA quando ≥ Afinidade_Meta (2,50) · ATENÇÃO entre a meta e a mínima · CRÍTICA abaixo de Afinidade_Min (2,00). Os dois limites estão em Parâmetros."),
 ("H", "Alerta de inaptidão", "Se qualquer especialidade responder por ≥ Part_Min_Critica (20%) do tempo da sala e algum membro da dupla tiver nível ≤ Nivel_Critico (1) nela, a linha é sinalizada mesmo que a média esteja boa."),
 ("S", "3. ROTINA DO DIA", ""),
 ("H", "Passo 1", "Em Parâmetros, ajuste a Data do mapa."),
 ("H", "Passo 2", "Lance as cirurgias em Mapa_Cirurgico (sala, turno, horários, especialidade, status). A coluna Alerta aponta sobreposição de horário, sala bloqueada, duração inválida e horário fora da janela do turno."),
 ("H", "Passo 3", "Em Escala_Duplas, escolha o CIRCULANTE e o INSTRUMENTADOR de cada sala/turno nas listas suspensas (células azuis). A aba Sugestao_Duplas mostra, para cada sala/turno, os técnicos AINDA LIVRES daquele turno em ordem de afinidade — a lista se atualiza a cada nome que você escala."),
 ("H", "Passo 4", "Confira a coluna ALERTAS e o Painel. Resolva as linhas CRÍTICA / SEM DUPLA antes de publicar a escala."),
 ("H", "Passo 5 (fechamento)", "Copie as linhas de Escala_Duplas e cole COMO VALORES em Base_Historico para manter o histórico do dia."),
 ("S", "4. CONVENÇÕES VISUAIS", ""),
 ("H", "Azul", "Célula de entrada — pode digitar."),
 ("H", "Amarelo", "Premissa de negócio (Parâmetros). Alterar aqui recalcula toda a planilha."),
 ("H", "Preto", "Resultado de fórmula — não digitar por cima."),
 ("H", "Verde itálico", "Valor trazido de outra aba por fórmula."),
 ("H", "Vermelho / âmbar / verde", "Semáforo de afinidade, ocupação e alertas."),
 ("S", "5. COMO EXPANDIR", ""),
 ("H", "Novo técnico", "Acrescente a linha em Equipe (até 150). A Matriz_Habilidades, o Calc_Afinidade e as listas suspensas acompanham automaticamente — basta preencher os níveis na Matriz."),
 ("H", "Nova especialidade", "Acrescente a linha em Especialidades (até 20 posições). As colunas da Matriz_Habilidades e do Calc_Mix pegam o nome automaticamente."),
 ("H", "Nova sala", "Acrescente a linha em Salas (até 12). As três linhas de turno correspondentes já existem em Calc_Mix, Escala_Duplas e Sugestao_Duplas e passam a funcionar sozinhas."),
 ("H", "Mais cirurgias", "O Mapa_Cirurgico comporta 300 cirurgias por dia; todas as fórmulas já cobrem esse intervalo."),
 ("S", "6. OBSERVAÇÕES TÉCNICAS", ""),
 ("H", "Dados de exemplo", "Equipe, matriz de habilidades e mapa cirúrgico vêm preenchidos com um dia de exemplo para demonstração. Substitua pelos dados reais do serviço."),
 ("H", "Ocupação da sala", "Cada cirurgia consome sua duração + o tempo de setup/limpeza definido em Parâmetros. Cirurgias Canceladas ou Suspensas não entram na ocupação nem no cálculo de afinidade."),
 ("H", "Colunas auxiliares ocultas", "Mapa_Cirurgico colunas N, O e P e Escala_Duplas colunas U, V e W guardam cálculos intermediários (texto de alerta, horários numéricos e ponderação da afinidade). Não excluir."),
 ("H", "Desempate na Sugestao_Duplas", "O Calc_Afinidade soma 0,000001 × número da linha para evitar empates no ranking; o efeito é invisível nas duas casas decimais exibidas."),
 ("H", "Funções utilizadas", "SUMIFS, COUNTIFS, SUMPRODUCT, INDEX, MATCH, LARGE, IF e IFERROR — compatíveis com Excel e LibreOffice. Não há macros, Power Query nem matrizes dinâmicas."),
]
r = 4
for kind, a, b in LINHAS:
    if kind == "S":
        c = ws_ins.cell(row=r, column=2, value=a); c.font = F_SEC
        ws_ins.cell(row=r, column=2).fill = FILL_CINZ; ws_ins.cell(row=r, column=3).fill = FILL_CINZ
        r += 1
    else:
        c1 = ws_ins.cell(row=r, column=2, value=a)
        c1.font = Font(name="Calibri", size=10, bold=True); c1.alignment = Alignment(vertical="top", wrap_text=True)
        c2 = ws_ins.cell(row=r, column=3, value=b)
        c2.font = F_FORMULA; c2.alignment = Alignment(vertical="top", wrap_text=True)
        ws_ins.row_dimensions[r].height = max(16, 13.5 * (len(b) // 118 + 1))
        r += 1
ws_ins.sheet_view.showGridLines = False

wb.save(OUT)
print("salvo:", OUT)

# ---------------------------------------------------------------- variante de inspeção visual
import os as _os
if _os.environ.get("VISUAL") == "1":
    areas = {S_INS: "A1:C42", S_PAR: "A1:I36", S_ESP: "A1:E22", S_SAL: "A1:E14",
             S_EQP: "A1:F32", S_MAT: "A1:Y26", S_MAP: "A1:M32", S_MIX: "A1:Z26",
             S_AFI: "A1:N26", S_ESC: "A1:T26", S_SUG: "A1:P26",
             S_PAI: "A1:R%d" % CHECK_LAST, S_HIS: "A1:N12"}
    for nome, area in areas.items():
        w = wb[nome]
        w.page_setup.orientation = "landscape"
        w.page_setup.fitToWidth = 1; w.page_setup.fitToHeight = 1
        w.sheet_properties.pageSetUpPr.fitToPage = True
        w.print_area = area
    wb.save(OUT.replace(".xlsx", "_VISUAL.xlsx"))
    print("visual:", OUT.replace(".xlsx", "_VISUAL.xlsx"))
