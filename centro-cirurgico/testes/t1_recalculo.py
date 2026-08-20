# -*- coding: utf-8 -*-
"""Teste 1 — varre o arquivo recalculado à procura de erros de fórmula."""
import sys, openpyxl
ERR = ("#REF!", "#VALUE!", "#DIV/0!", "#N/A", "#NAME?", "#NUM!", "#NULL!", "Err:")
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
bad = [(w.title, c.coordinate, c.value) for w in wb.worksheets for row in w.iter_rows()
       for c in row if isinstance(c.value, str) and any(e in c.value for e in ERR)]
print("ERROS DE FÓRMULA:", len(bad))
for b in bad[:30]:
    print("   ", b)
sys.exit(1 if bad else 0)
