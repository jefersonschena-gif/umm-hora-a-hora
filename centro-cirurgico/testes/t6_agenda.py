# -*- coding: utf-8 -*-
"""Teste 6 — importação da agenda: leitura do PDF (via texto de referência), gravação no
Agenda do Dia e reconciliação independente da ocupação e das janelas de jogo de sala.

O texto de referência reproduz o leiaute do mapa do hospital com dados fictícios — nenhum
dado de paciente entra no repositório."""
import os, shutil, subprocess, sys
import openpyxl

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from abas import ABA_AGENDA, ABA_CFG, ABA_EQUIPE, ABA_FOLGAS, ABA_MAPA
from importar_agenda import ler_texto, importar

SP = os.environ.get("SAIDA", os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "Centro_Cirurgico_Escala.xlsx")
T0, TM = 7 * 60, 360

CAB = ("  Início - Término               Prontuário Paciente                        DN         Idade\n"
       "  {d} {hi} - {d} {hf} 1000000 111 - PACIENTE FICTICIO                       01/01/1980 46a\n"
       "  Cirurgião                    Anestesista   Cirurgia                                        "
       "Tipo de Atendimento Observações        Acomodação\n"
       "  {cir}                        ANESTESIA     {proc}                                          "
       "Atendimento Ambulatorial                SETOR SEM\n"
       "                                                             Equipamento:\n")

# agenda fictícia: emendas sem limpeza, janela no meio, cirurgia atravessando as 13:00
AG = [("Sala 1", "07:00", "08:00", "Dr. Fict A", "PROCEDIMENTO UM"),
      ("Sala 1", "08:00", "09:00", "Dr. Fict A", "PROCEDIMENTO DOIS"),
      ("Sala 1", "11:00", "12:00", "Dr. Fict A", "PROCEDIMENTO TRES"),
      ("Sala 2", "07:30", "09:30", "Dra. Fict B", "PROCEDIMENTO QUATRO"),
      ("Sala 2", "12:00", "14:30", "Dra. Fict B", "PROCEDIMENTO CINCO"),
      ("Sala 8", "09:00", "09:30", "Dr. Fict C", "PROCEDIMENTO SEIS"),
      ("Sala 8", "09:30", "10:00", "Dr. Fict C", "PROCEDIMENTO SETE")]

def texto():
    linhas, sala = [], None
    for s, hi, hf, cir, proc in AG:
        if s != sala:
            linhas.append("  %s" % s); sala = s
        linhas.append(CAB.format(d="21/08/26", hi=hi, hf=hf, cir=cir, proc=proc))
    return "\n".join(linhas)

def recalc(path):
    out = os.path.join(SP, "rc6"); shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    subprocess.run(["soffice", "--headless", "--norestore", "--convert-to", "xlsx",
                    "--outdir", out, path], capture_output=True)
    return os.path.join(out, os.path.basename(path))

# --- leitura
cirs = ler_texto(texto())
res, ok = [], 0
def chk(nome, esperado, obtido):
    global ok
    bate = esperado == obtido or (isinstance(esperado, float) and abs(esperado - obtido) < 0.5)
    ok += bate
    res.append("%-42s esperado %-28s obtido %-28s %s" % (nome, esperado, obtido,
                                                         "ok" if bate else "DIVERGE"))
chk("cirurgias lidas", len(AG), len(cirs))
chk("salas lidas", 3, len({c["sala"] for c in cirs}))
chk("procedimento da 1ª", "PROCEDIMENTO UM", cirs[0]["procedimento"])
chk("cirurgião da 1ª", "Dr. Fict A", cirs[0]["cirurgiao"])
chk("cirurgias por sala", [3, 2, 2], [sum(1 for c in cirs if c["sala"] == s) for s in ("Sala 1", "Sala 2", "Sala 8")])
chk("horários da última", ("12:00", "14:30"), (cirs[4]["ini"], cirs[4]["fim"]))

# --- gravação
alvo = os.path.join(SP, "t6.xlsx")
shutil.copy(SRC, alvo)
saida = importar(None, alvo, os.path.join(SP, "t6_importada.xlsx"), cirs=cirs)
rc = recalc(saida)
wb = openpyxl.load_workbook(rc, data_only=True)
mapa, cal, pai, cfg = wb[ABA_AGENDA], wb["Calc"], wb[ABA_MAPA], wb[ABA_CFG]

erros = [(w.title, c.coordinate) for w in wb.worksheets for row in w.iter_rows() for c in row
         if isinstance(c.value, str) and any(e in c.value for e in
                                             ("#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NUM!", "Err:"))]
chk("erros de fórmula após importar", 0, len(erros))
DIA = mapa["A2"].value if False else None
linhas_dia = [r for r in range(2, 202) if mapa.cell(row=r, column=2).value
              and str(mapa.cell(row=r, column=1).value).startswith("2026-08-21")]
chk("linhas importadas no mapa", len(AG), len(linhas_dia))

# --- reconciliação independente
# a limpeza que a planilha ACRESCENTA depois de cada cirurgia sai da própria Configuração:
# a agenda do hospital já reserva a limpeza dentro do horário, então ali é 0
LIMP = cfg["B16"].value or 0
mm = lambda h: int(h[:2]) * 60 + int(h[3:]) - T0
salas = {}
for s, hi, hf, _, _ in AG:
    salas.setdefault("SO-%02d" % int(s.split()[1]), []).append((mm(hi), mm(hf)))
for cod, v in sorted(salas.items()):
    v.sort()
    ocup, jan = 0, []
    for k, (a, b) in enumerate(v):
        prox = v[k + 1][0] if k + 1 < len(v) else TM
        ocup += max(0, min(b + LIMP, TM, prox) - min(a, TM))
        ini = 0 if k == 0 else min(v[k - 1][1] + LIMP, TM)
        jan.append(max(0, min(a, TM) - ini))
    jan.append(max(0, TM - min(v[-1][1] + LIMP, TM)))
    maior = max(jan)
    atraso = pico = 0
    for k, (a, b) in enumerate(v):
        prox = v[k + 1][0] if k + 1 < len(v) else TM
        if prox < TM:
            atraso = max(0, atraso + (b + LIMP) - prox)
        pico = max(pico, atraso)
    obt_o = next(cal.cell(row=r, column=4).value for r in range(2, 18)
                 if cal.cell(row=r, column=1).value == cod)
    nome = next(cfg.cell(row=r, column=2).value for r in range(45, 61)
                if cfg.cell(row=r, column=1).value == cod)
    obt_l = next(pai.cell(row=r, column=11).value for r in range(10, 26)
                 if pai.cell(row=r, column=1).value == nome)
    chk("ocupação %s (min)" % cod, ocup, obt_o)
    chk("cabe até %s (min)" % cod, max(0, maior - LIMP) or None, obt_l)
    obt_a = next(pai.cell(row=r, column=12).value for r in range(10, 26)
                 if pai.cell(row=r, column=1).value == nome)
    chk("atraso previsto %s (min)" % cod, pico, obt_a)

alertas = [mapa.cell(row=r, column=14).value for r in linhas_dia]
chk("emenda sem folga não vira alerta de erro", 0,
    sum(1 for a in alertas if a and "limpeza" in a.lower()))
chk("cirurgia fora do plantão sinalizada", 1,
    sum(1 for a in alertas if a and "Fora da janela do plantão" in a))

print("\n".join(res))
print("\nTESTE 6 (importação da agenda): %d/%d" % (ok, len(res)))
sys.exit(0 if ok == len(res) else 1)
