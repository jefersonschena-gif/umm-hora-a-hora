# -*- coding: utf-8 -*-
"""Teste 12 — o arquivo visto como o Excel vê.

O LibreOffice abre coisa que o Excel recusa: quando o .xlsx foge do formato, o Excel não
avisa qual é o problema, só abre perguntando "encontramos um problema em um conteúdo, quer
que tentemos recuperar?". Este teste procura no XML de dentro do arquivo os desvios que
causam essa pergunta — o recálculo e a reconciliação não pegam nenhum deles, porque para o
LibreOffice o arquivo está bom.

Rode contra todo .xlsx que for entregue:  python3 testes/t12_excel.py arquivo.xlsx [outro.xlsx]
"""
import collections, os, re, sys, zipfile
from openpyxl.utils import column_index_from_string, range_boundaries

# ordem obrigatória dos filhos de <worksheet> (CT_Worksheet); fora dela o Excel recusa
ORDEM = ["sheetPr", "dimension", "sheetViews", "sheetFormatPr", "cols", "sheetData",
         "sheetCalcPr", "sheetProtection", "protectedRanges", "scenarios", "autoFilter",
         "sortState", "dataConsolidate", "customSheetViews", "mergeCells", "phoneticPr",
         "conditionalFormatting", "dataValidations", "hyperlinks", "printOptions",
         "pageMargins", "pageSetup", "headerFooter", "rowBreaks", "colBreaks",
         "customProperties", "cellWatches", "ignoredErrors", "smartTags", "drawing",
         "legacyDrawing", "legacyDrawingHF", "picture", "oleObjects", "controls",
         "webPublishItems", "tableParts", "extLst"]
IDX = {n: i for i, n in enumerate(ORDEM)}
LIM_FORMULA, LIM_ANINHAMENTO = 8192, 64


def filhos_da_planilha(s):
    corpo = s[s.index("<worksheet"):]
    corpo = corpo[corpo.index(">") + 1:]
    fora, prof = [], 0
    for m in re.finditer(r"<(/?)([a-zA-Z][\w]*)([^>]*?)(/?)>", corpo):
        fecha, tag, _, auto = m.groups()
        if prof == 0 and not fecha:
            fora.append(tag)
        if not fecha and not auto and tag != "worksheet":
            prof += 1
        elif fecha:
            prof -= 1
    return fora


def profundidade(f):
    d = mx = 0
    dentro = False
    for ch in f:
        if ch == '"':
            dentro = not dentro
        if dentro:
            continue
        if ch == "(":
            d += 1; mx = max(mx, d)
        elif ch == ")":
            d -= 1
    return mx


def problemas(path):
    z = zipfile.ZipFile(path)
    p = collections.Counter()
    partes = z.namelist()
    tipos = z.read("[Content_Types].xml").decode("utf-8")
    for n in partes:                                    # toda parte declarada em [Content_Types]
        if (n.endswith(".xml") and not n.startswith(("_rels", "[")) and "/_rels/" not in n
                and ("/" + n) not in tipos):
            p["parte sem Content_Type"] += 1
    for n in partes:
        if "worksheets/sheet" not in n:
            continue
        s = z.read(n).decode("utf-8")
        # célula marcada como texto e sem o texto dentro: o desvio que trava o Excel
        p["texto vazio (t=inlineStr sem <is>)"] += len(re.findall(r'<c\b[^>]*t="inlineStr"[^>]*/>', s))
        if "xl/sharedStrings.xml" not in partes:
            p["t=s sem sharedStrings"] += len(re.findall(r'<c\b[^>]*t="s"', s))
        p["<is> sem <t>"] += len([1 for m in re.findall(r"<is>(.*?)</is>", s, re.S) if "<t" not in m])
        p["<f> vazia"] += len(re.findall(r"<f></f>|<f/>", s))
        p["caractere de controle"] += len([c for c in s if ord(c) < 32 and c not in "\t\n\r"])
        pos = [IDX.get(f, -1) for f in filhos_da_planilha(s)]
        p["elemento fora de ordem"] += (pos != sorted(pos)) or (-1 in pos)
        for m in re.finditer(r'<mergeCells count="(\d+)">(.*?)</mergeCells>', s, re.S):
            refs = re.findall(r'ref="([^"]+)"', m.group(2))
            p["mergeCells com contagem errada"] += int(m.group(1)) != len(refs)
            p["merge de uma célula só"] += sum(
                1 for r in refs if range_boundaries(r)[0] == range_boundaries(r)[2]
                and range_boundaries(r)[1] == range_boundaries(r)[3])
            caixas = [range_boundaries(r) for r in refs]
            for i in range(len(caixas)):
                for j in range(i + 1, len(caixas)):
                    a, b = caixas[i], caixas[j]
                    p["merges sobrepostos"] += (a[0] <= b[2] and b[0] <= a[2]
                                                and a[1] <= b[3] and b[1] <= a[3])
        prio = [int(x) for x in re.findall(r'priority="(\d+)"', s)]
        p["prioridade repetida"] += len(prio) - len(set(prio))
        linhas = [int(x) for x in re.findall(r'<row[^>]*r="(\d+)"', s)]
        p["linhas fora de ordem"] += linhas != sorted(linhas) or len(linhas) != len(set(linhas))
        for m in re.finditer(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', s, re.S):
            refs = re.findall(r'<c\b[^>]*?r="([A-Z]+)(\d+)"', m.group(2))
            cols = [column_index_from_string(c) for c, _ in refs]
            p["células fora de ordem"] += cols != sorted(cols)
            p["células repetidas"] += len(cols) != len(set(cols))
            p["célula na linha errada"] += bool({int(x) for _, x in refs} - {int(m.group(1))})
        for f in re.findall(r"<f>(.*?)</f>", s, re.S):
            p["fórmula longa demais"] += len(f) > LIM_FORMULA
            p["fórmula aninhada demais"] += profundidade(f) > LIM_ANINHAMENTO
    st = z.read("xl/styles.xml").decode("utf-8")
    ndx = int(re.search(r'<dxfs count="(\d+)"', st).group(1))
    for n in partes:
        if "worksheets/sheet" in n:
            s = z.read(n).decode("utf-8")
            p["dxfId inexistente"] += sum(1 for x in re.findall(r'dxfId="(\d+)"', s) if int(x) >= ndx)
    decl = set()
    if "<numFmts" in st:
        decl = {int(x) for x in re.findall(r'numFmtId="(\d+)"',
                                           re.search(r"<numFmts.*?</numFmts>", st, re.S).group(0))}
    usados = {int(x) for x in re.findall(r'numFmtId="(\d+)"',
                                         re.search(r"<cellXfs.*?</cellXfs>", st, re.S).group(0))}
    p["numFmt usado sem declarar"] += len({u for u in usados if u >= 164} - decl)
    wbx = z.read("xl/workbook.xml").decode("utf-8")
    nomes = re.findall(r'<definedName name="([^"]+)"[^>]*>([^<]*)</definedName>', wbx)
    p["nome definido quebrado"] += sum(1 for _, v in nomes if not v or "#REF" in v)
    simples = [n for n, _ in nomes if not n.startswith("_xlnm")]
    p["nome definido repetido"] += len(simples) - len(set(simples))
    return {k: v for k, v in p.items() if v}


RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
alvos = sys.argv[1:] or [os.path.join(RAIZ, "Centro_Cirurgico_Escala.xlsx")]
res, ok = [], 0
for arq in alvos:
    ruim = problemas(arq)
    ok += not ruim
    res.append("%-44s %s" % (os.path.basename(arq)[:44], "ok" if not ruim else "DESVIO %s" % ruim))
print("\n".join(res))
print("\nTESTE 12 (o arquivo como o Excel vê): %d/%d" % (ok, len(alvos)))
sys.exit(0 if ok == len(alvos) else 1)
