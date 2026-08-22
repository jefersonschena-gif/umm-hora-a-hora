#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o comando que instala um script desta skill dentro do sandbox.

O sandbox do Higgsfield e' descartado poucos segundos depois de cada chamada:
arquivos NAO sobrevivem de forma confiavel entre duas chamadas (medido em
2026-08-06: uma instalacao partida em duas chamadas consecutivas perdeu tudo).
Por isso cada pacote aqui e' pequeno o bastante para caber em UM UNICO comando,
junto com o trabalho que vai usa'-lo — que e' como ele deve ser chamado.

    python3 push_scripts.py --pacote qc \
        --append "python3 qc/qc_video.py --video work/output/final.mp4 --sidecar ..."

Pacotes:
    qc     qc_video.py    (medicao do video no sandbox)   ~12 000 caracteres
    lint   ptbr_lint.py   (ortografia/TTS; roda local tambem) ~7 200
    thumb  thumb_text.sh  (texto da thumbnail via ImageMagick) ~2 300
    labels screen_labels.sh (rotulo de tela sobre o clipe)   ~2 400

O empacotamento e' tar + lzma + base64 e a descompactacao usa o proprio python3
do sandbox (nao depende do binario xz).
"""
from __future__ import annotations

import argparse
import base64
import io
import lzma
import os
import sys
import tarfile
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
PACOTES = {
    "qc": ["qc_video.py"],
    "lint": ["ptbr_lint.py"],
    "thumb": ["thumb_text.sh"],
    "labels": ["screen_labels.sh"],
    "tudo": ["qc_video.py", "ptbr_lint.py", "thumb_text.sh", "screen_labels.sh"],
}


def enxuga(fonte: str, nome: str) -> bytes:
    """Tira comentarios, docstrings e linhas vazias — so' para o transporte.

    O original continua no repositorio; o que viaja e' a versao magra, porque o
    comando do sandbox tem teto de 16 000 caracteres. Se a versao magra nao
    compilar, o arquivo vai inteiro.
    """
    linhas, saida, i = fonte.splitlines(), [], 0
    while i < len(linhas):
        ln = linhas[i]
        nu = ln.strip()
        if not nu:
            i += 1
            continue
        if nu.startswith("#") and not (i < 2 and (nu.startswith("#!") or "coding" in nu)):
            i += 1
            continue
        if nome.endswith(".py") and (nu.startswith('"""') or nu.startswith("'''")):
            delim = nu[:3]
            if len(nu) > 5 and nu.endswith(delim):
                i += 1
                continue
            i += 1
            while i < len(linhas) and delim not in linhas[i]:
                i += 1
            i += 1
            continue
        saida.append(ln)
        i += 1
    magro = "\n".join(saida) + "\n"
    if nome.endswith(".py"):
        try:
            compile(magro, nome, "exec")
        except SyntaxError:
            return fonte.encode()
    return magro.encode()


def blob(arquivos) -> str:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for nome in arquivos:
            caminho = os.path.join(AQUI, nome)
            if not os.path.exists(caminho):
                print(f"# aviso: {nome} ausente", file=sys.stderr)
                continue
            dados = enxuga(open(caminho, encoding="utf-8").read(), nome)
            info = tarfile.TarInfo(nome)
            info.size = len(dados)
            info.mtime = int(time.time())
            info.mode = 0o755
            tar.addfile(info, io.BytesIO(dados))
    comprimido = lzma.compress(buf.getvalue(), preset=9 | lzma.PRESET_EXTREME)
    return base64.b64encode(comprimido).decode()


def comando(arquivos, dst: str, extra: str) -> str:
    b64 = blob(arquivos)
    desempacota = (
        "import sys,base64,lzma,io,tarfile,os;"
        f"os.makedirs('{dst}',exist_ok=True);"
        "d=lzma.decompress(base64.b64decode(sys.argv[1]));"
        f"tarfile.open(fileobj=io.BytesIO(d)).extractall('{dst}');"
        f"print('QC: scripts em {dst}/')"
    )
    cmd = f"python3 -c \"{desempacota}\" '{b64}' && chmod +x {dst}/*"
    return cmd + (" && " + extra if extra else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pacote", default="qc", choices=sorted(PACOTES))
    ap.add_argument("--dir", default="qc", help="pasta destino dentro do sandbox")
    ap.add_argument("--teto", type=int, default=16000)
    ap.add_argument("--append", default="",
                    help="comando que usa o script, colado no MESMO comando (recomendado)")
    a = ap.parse_args()
    cmd = comando(PACOTES[a.pacote], a.dir, a.append)
    if len(cmd) > a.teto:
        print(f"ERRO: o comando ficou com {len(cmd)} caracteres (teto {a.teto}).\n"
              f"Reduza o --append ou instale um pacote menor: "
              f"{' '.join(sorted(PACOTES))}", file=sys.stderr)
        return 1
    print(f"# sandbox_exec ({len(cmd)} caracteres) — UMA chamada so', "
          f"com o trabalho junto:", file=sys.stderr)
    print(cmd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
