# -*- coding: utf-8 -*-
"""Teste 9 — estilo do arquivo: confere no XML o que o openpyxl grava e o Excel lê.

Existe porque a formatação condicional funcionava no LibreOffice e não no Excel: num dxf
o Excel pinta o fundo com bgColor e ignora fgColor sozinho. Nenhum teste de valor pega
isso — só olhando o XML."""
import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARQ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "Centro_Cirurgico_Escala.xlsx")

res, ok = [], 0
def chk(nome, esperado, obtido):
    global ok
    bate = esperado == obtido
    ok += bate
    res.append("%-52s esperado %-16s obtido %-16s %s"
               % (nome, esperado, obtido, "ok" if bate else "DIVERGE"))

z = zipfile.ZipFile(ARQ)
estilos = z.read("xl/styles.xml").decode("utf-8")
dxfs = re.findall(r"<dxf>.*?</dxf>", re.search(r"<dxfs[^>]*>(.*?)</dxfs>", estilos, re.S).group(1), re.S)

com_fill = [d for d in dxfs if "<fill>" in d]
chk("há regras condicionais com preenchimento", True, len(com_fill) > 0)
chk("nenhum preenchimento de regra usa fgColor", [],
    [i for i, d in enumerate(com_fill) if "fgColor" in d])
chk("todo preenchimento de regra usa bgColor", [],
    [i for i, d in enumerate(com_fill) if "bgColor" not in d])

# toda regra aponta para um dxf que existe
usados, faltando = set(), []
for nome in [n for n in z.namelist() if n.startswith("xl/worksheets/sheet")]:
    xml = z.read(nome).decode("utf-8")
    for d in re.findall(r'<cfRule[^>]*dxfId="(\d+)"', xml):
        usados.add(int(d))
        if int(d) >= len(dxfs):
            faltando.append((nome, d))
chk("toda regra aponta para um estilo existente", [], faltando)
chk("há regras condicionais nas abas", True, len(usados) > 0)

# os preenchimentos fixos (cabeçalho, células de entrada) continuam com fgColor
fills = re.search(r"<fills[^>]*>(.*?)</fills>", estilos, re.S).group(1)
chk("preenchimentos fixos usam fgColor", True, fills.count("fgColor") >= 3)

print("\n".join(res))
print("\nTESTE 9 (estilo): %d/%d" % (ok, len(res)))
sys.exit(0 if ok == len(res) else 1)
