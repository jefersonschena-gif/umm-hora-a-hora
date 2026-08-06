#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QC-TRIMODAL — porta de qualidade mecanica do video final.

Valida, com medicao (nunca por opiniao), os seis eixos da skill
montagem-video-higgsfield:

  IMAGEM     resolucao, fps, nitidez, exposicao, barras pretas, ritmo de corte,
             abertura congelada
  AUDIO      presenca, paridade video/audio, loudness (-16 LUFS), true peak,
             clipping, silencios longos
  NARRACAO   janela de fala por bloco, ritmo (palavras/s), pausas internas,
             fidelidade do que foi dito (Whisper pt) x roteiro
  LEGENDA    sintaxe SRT, sobreposicao, CPS, linhas/caracteres, cobertura do
             roteiro, deriva temporal contra a janela de fala real, ortografia
  TRIMODAL   autonomia do audio (deixis), proposicao visual por bloco,
             variedade visual, gancho nos primeiros segundos
  THUMBNAIL  dimensao, proporcao, peso, texto (<=5 palavras, ortografia),
             contraste WCAG e legibilidade a 168 px

Roda no sandbox do Higgsfield (ffmpeg/ffprobe/PIL/faster-whisper ja instalados).

Exemplo:
  python3 qc_video.py \
    --video work/output/final.mp4 \
    --sidecar work/output/final.mp4.assembly.json \
    --srt work/output/final.srt \
    --script script_manifest.json \
    --voice-dir work/voices \
    --thumb work/output/thumb.jpg \
    --aspect 16:9 --json work/output/qc_report.json

Exit 0 = liberado (pode haver AVISO) · 1 = REPROVADO · 2 = erro de uso.
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import re
import subprocess
import sys
import unicodedata

try:
    from ptbr_lint import check_text as ptbr_check
except Exception:  # lint opcional — ausencia vira aviso
    ptbr_check = None

FAIL, WARN, OK, SKIP = "REPROVADO", "AVISO", "OK", "NAO-VERIFICADO"
R = []  # resultados


def add(area, code, status, msg, medido=None, esperado=None):
    R.append({"area": area, "code": code, "status": status, "msg": msg,
              "medido": medido, "esperado": esperado})


def sh(cmd, timeout=600):
    p = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                       text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def probe(path):
    rc, out, _ = sh(["ffprobe", "-v", "error", "-print_format", "json",
                     "-show_format", "-show_streams", path])
    if rc != 0:
        return None
    return json.loads(out)


def norm_tokens(s):
    s = unicodedata.normalize("NFD", s.casefold())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", s)


def sim(a, b):
    ta, tb = " ".join(norm_tokens(a)), " ".join(norm_tokens(b))
    if not ta and not tb:
        return 1.0
    return difflib.SequenceMatcher(None, ta, tb).ratio()


# ---------------------------------------------------------------- IMAGEM ---
def check_imagem(video, aspect, sidecar, deep):
    info = probe(video)
    if not info:
        add("IMAGEM", "ARQUIVO", FAIL, "ffprobe nao conseguiu ler o video")
        return None
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if not v:
        add("IMAGEM", "STREAM_VIDEO", FAIL, "sem stream de video")
        return None
    w, h = int(v["width"]), int(v["height"])
    dur = float(info["format"].get("duration", 0))
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0

    alvo = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}.get(aspect)
    if alvo:
        if (w, h) >= alvo:
            add("IMAGEM", "RESOLUCAO", OK, f"{w}x{h}", f"{w}x{h}", f">={alvo[0]}x{alvo[1]}")
        else:
            add("IMAGEM", "RESOLUCAO", FAIL,
                f"{w}x{h} abaixo do minimo — falta o upscale Topaz 1080p",
                f"{w}x{h}", f">={alvo[0]}x{alvo[1]}")
        ar_alvo = alvo[0] / alvo[1]
        if abs(w / h - ar_alvo) > 0.02:
            add("IMAGEM", "PROPORCAO", FAIL, f"proporcao {w}/{h} != {aspect}",
                f"{w/h:.3f}", f"{ar_alvo:.3f}")
        else:
            add("IMAGEM", "PROPORCAO", OK, f"proporcao {aspect}")
    add("IMAGEM", "FPS", OK if fps >= 23.9 else FAIL,
        f"{fps:.2f} fps", f"{fps:.2f}", ">=24")

    if not deep:
        add("IMAGEM", "QUADROS", SKIP, "analise de quadros desligada (--rapido)")
        return {"w": w, "h": h, "dur": dur, "fps": fps}

    try:
        from PIL import Image, ImageFilter, ImageStat
    except Exception:
        add("IMAGEM", "QUADROS", SKIP, "PIL indisponivel")
        return {"w": w, "h": h, "dur": dur, "fps": fps}

    tmp = "/tmp/qc_frames"
    os.makedirs(tmp, exist_ok=True)
    n = max(6, min(24, int(dur // 5)))
    escuros, borrados, barras = [], [], []
    for i in range(n):
        t = dur * (i + 0.5) / n
        fp = f"{tmp}/f{i:02d}.png"
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video,
            "-frames:v", "1", fp])
        if not os.path.exists(fp):
            continue
        im = Image.open(fp).convert("L")
        st = ImageStat.Stat(im)
        media, desvio = st.mean[0], st.stddev[0]
        nitidez = ImageStat.Stat(im.filter(ImageFilter.FIND_EDGES)).stddev[0]
        if media < 22 or media > 235 or desvio < 12:
            escuros.append((round(t, 1), round(media), round(desvio)))
        if nitidez < 6:
            borrados.append((round(t, 1), round(nitidez, 1)))
        px = im.load()
        topo = sum(px[x, 2] for x in range(0, im.width, max(1, im.width // 40)))
        base = sum(px[x, im.height - 3] for x in range(0, im.width, max(1, im.width // 40)))
        amostras = len(range(0, im.width, max(1, im.width // 40)))
        if topo / amostras < 6 and base / amostras < 6:
            barras.append(round(t, 1))

    add("IMAGEM", "EXPOSICAO", OK if not escuros else WARN,
        "quadros dentro da faixa" if not escuros
        else f"{len(escuros)}/{n} quadros chapados ou sem contraste: {escuros[:4]}")
    add("IMAGEM", "NITIDEZ", OK if not borrados else WARN,
        "sem quadros borrados" if not borrados
        else f"{len(borrados)}/{n} quadros com baixa densidade de borda: {borrados[:4]}")
    add("IMAGEM", "BARRAS_PRETAS", OK if len(barras) < 2 else FAIL,
        "sem letterbox" if len(barras) < 2 else f"barras pretas em {barras[:5]}")

    # abertura congelada: diferenca entre 0.05s e 0.9s
    for a, b in [(0.05, 0.9)]:
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a), "-i", video,
            "-frames:v", "1", f"{tmp}/a.png"])
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(b), "-i", video,
            "-frames:v", "1", f"{tmp}/b.png"])
        if os.path.exists(f"{tmp}/a.png") and os.path.exists(f"{tmp}/b.png"):
            ia = Image.open(f"{tmp}/a.png").convert("L").resize((160, 90))
            ib = Image.open(f"{tmp}/b.png").convert("L").resize((160, 90))
            d = sum(abs(x - y) for x, y in zip(ia.getdata(), ib.getdata())) / (160 * 90)
            add("IMAGEM", "ABERTURA_VIVA", OK if d > 4 else FAIL,
                f"movimento no primeiro segundo (delta {d:.1f})" if d > 4
                else f"primeiro segundo praticamente congelado (delta {d:.1f})",
                round(d, 1), ">4")

    # ritmo de corte
    rc, out, err = sh(f"ffmpeg -hide_banner -i '{video}' -filter:v "
                      f"\"select='gt(scene,0.25)',showinfo\" -f null - 2>&1 | "
                      f"grep -o 'pts_time:[0-9.]*'")
    cortes = [float(x.split(":")[1]) for x in out.split()] if out else []
    if sidecar and sidecar.get("per_block"):
        blocos = len(sidecar["per_block"])
        jan = float(sidecar.get("clip_seconds") or 10)
        fracos = [b + 1 for b in range(blocos)
                  if sum(1 for c in cortes if b * jan <= c < (b + 1) * jan) < 3]
        add("IMAGEM", "RITMO_CORTE", OK if not fracos else WARN,
            f"{len(cortes)} cortes detectados em {blocos} blocos"
            + ("" if not fracos else f"; blocos lentos (<3 cortes): {fracos}"),
            len(cortes), f">=3 por bloco de {jan:.0f}s")
    else:
        taxa = len(cortes) / dur * 60 if dur else 0
        add("IMAGEM", "RITMO_CORTE", OK if taxa >= 18 else WARN,
            f"{len(cortes)} cortes ({taxa:.0f}/min)", round(taxa), ">=18/min")
    return {"w": w, "h": h, "dur": dur, "fps": fps}


# ----------------------------------------------------------------- AUDIO ---
def check_audio(video, vdur):
    info = probe(video)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None) if info else None
    if not a:
        add("AUDIO", "STREAM_AUDIO", FAIL, "o arquivo final nao tem faixa de audio")
        return
    adur = float(a.get("duration") or info["format"].get("duration", 0))
    sr = int(a.get("sample_rate", 0))
    add("AUDIO", "TAXA_AMOSTRAGEM", OK if sr >= 44100 else WARN, f"{sr} Hz", sr, ">=44100")
    delta = abs(vdur - adur)
    add("AUDIO", "PARIDADE_AV", OK if delta <= 0.25 else FAIL,
        f"video {vdur:.2f}s x audio {adur:.2f}s (delta {delta:.2f}s)",
        round(delta, 2), "<=0.25s")

    rc, out, err = sh(["ffmpeg", "-hide_banner", "-i", video, "-af",
                       "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                       "-f", "null", "-"])
    m = re.search(r"\{[^{}]*input_i[^}]*\}", err, re.S)
    if m:
        d = json.loads(m.group(0))
        I, TP, LRA = float(d["input_i"]), float(d["input_tp"]), float(d["input_lra"])
        add("AUDIO", "LOUDNESS", OK if -17.5 <= I <= -14.5 else FAIL,
            f"{I:.1f} LUFS", round(I, 1), "-16 +-1.5 LUFS")
        add("AUDIO", "PICO_REAL", OK if TP <= -0.9 else FAIL,
            f"true peak {TP:.1f} dBTP", round(TP, 1), "<=-1.0 dBTP")
        add("AUDIO", "FAIXA_DINAMICA", OK if LRA <= 14 else WARN,
            f"LRA {LRA:.1f}", round(LRA, 1), "<=14")
    else:
        add("AUDIO", "LOUDNESS", SKIP, "loudnorm nao retornou medicao")

    rc, out, err = sh(["ffmpeg", "-hide_banner", "-i", video, "-af",
                       "silencedetect=n=-45dB:d=1.5", "-f", "null", "-"])
    ini = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", err)]
    dur = [float(x) for x in re.findall(r"silence_duration: ([0-9.]+)", err)]
    buracos = [(round(s, 1), round(d, 1)) for s, d in zip(ini, dur) if s + d < vdur - 1.0]
    add("AUDIO", "SILENCIO_LONGO", OK if not buracos else WARN,
        "sem buracos internos" if not buracos else f"silencios internos >1.5s: {buracos[:5]}")


# -------------------------------------------------------------- NARRACAO ---
def fala_metricas(wav):
    """(inicio, fim, duracao_de_fala, maior_pausa_interna) via silencedetect."""
    rc, out, err = sh(["ffmpeg", "-hide_banner", "-i", wav, "-af",
                       "silencedetect=n=-35dB:d=0.25", "-f", "null", "-"])
    info = probe(wav)
    total = float(info["format"]["duration"]) if info else 0.0
    ini = [float(x) for x in re.findall(r"silence_start: (-?[0-9.]+)", err)]
    fim = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", err)]
    trechos = list(zip(ini, fim + ([total] if len(fim) < len(ini) else [])))
    head = trechos[0][1] if trechos and trechos[0][0] <= 0.05 else 0.0
    tail = trechos[-1][0] if trechos and abs(trechos[-1][1] - total) < 0.05 else total
    internas = [f - i for i, f in trechos if i > head + 0.01 and f < tail - 0.01]
    return head, tail, max(0.0, tail - head), (max(internas) if internas else 0.0)


def check_narracao(sidecar, script_rows, voice_dir, usar_whisper):
    if not sidecar or not sidecar.get("per_block"):
        add("NARRACAO", "SIDECAR", SKIP, "sem sidecar de montagem — narracao nao verificada")
        return
    pb = sidecar["per_block"]
    jan = float(sidecar.get("clip_seconds") or 10)
    lo, hi = jan - 1.4, jan
    fora, rapidos, pausas, sumidos = [], [], [], []
    for i, b in enumerate(pb):
        fala = float(b.get("speech_s") or 0)
        if fala <= 0:
            sumidos.append(b.get("n", i + 1))
            continue
        if not (lo - 0.05 <= fala <= hi + 0.05):
            fora.append((b.get("n"), round(fala, 2)))
        linha = script_rows[i] if i < len(script_rows) else ""
        pal = len(norm_tokens(linha))
        if pal:
            ritmo = pal / fala
            if ritmo > 3.2 or ritmo < 2.0:
                rapidos.append((b.get("n"), round(ritmo, 2)))
        if int(b.get("internal_pauses") or 0) > 0:
            pausas.append(b.get("n"))
    add("NARRACAO", "PRESENCA", OK if not sumidos else FAIL,
        "todos os blocos tem fala" if not sumidos else f"blocos sem fala: {sumidos}")
    add("NARRACAO", "JANELA", OK if not fora else FAIL,
        f"todas as falas em [{lo:.1f}, {hi:.1f}]s" if not fora
        else f"falas fora da janela: {fora}", None, f"[{lo:.1f},{hi:.1f}]s")
    add("NARRACAO", "RITMO", OK if not rapidos else WARN,
        "ritmo entre 2.0 e 3.2 palavras/s" if not rapidos
        else f"blocos com ritmo fora de 2.0-3.2 pal/s: {rapidos}")
    add("NARRACAO", "PAUSAS", OK if not pausas else WARN,
        "sem pausas internas longas" if not pausas
        else f"blocos com pausa interna >=0.8s: {pausas}")

    if voice_dir and os.path.isdir(voice_dir):
        maiores = []
        for b in pb:
            wav = os.path.join(voice_dir, b.get("voice_norm") or b.get("voice") or "")
            if os.path.exists(wav):
                _, _, _, p = fala_metricas(wav)
                if p >= 0.8:
                    maiores.append((b.get("n"), round(p, 2)))
        if maiores:
            add("NARRACAO", "PAUSAS_TAKE", WARN, f"pausa interna longa nas tomadas: {maiores}")

    if not usar_whisper:
        add("NARRACAO", "FIDELIDADE", SKIP, "checagem por Whisper desligada")
        return
    try:
        from faster_whisper import WhisperModel
    except Exception:
        add("NARRACAO", "FIDELIDADE", SKIP, "faster_whisper indisponivel")
        return
    modelo = WhisperModel("tiny", device="cpu", compute_type="int8")
    ruins, sotaque = [], []
    for i, b in enumerate(pb):
        wav = os.path.join(voice_dir or "", b.get("voice_norm") or b.get("voice") or "")
        if not os.path.exists(wav):
            continue
        seg, _ = modelo.transcribe(wav, language="pt", beam_size=1)
        dito = " ".join(s.text for s in seg)
        alvo = script_rows[i] if i < len(script_rows) else ""
        if not alvo:
            continue
        s = sim(dito, alvo)
        if s < 0.90:
            ruins.append((b.get("n"), round(s, 2)))
        elif s < 0.95:
            sotaque.append((b.get("n"), round(s, 2)))
    add("NARRACAO", "FIDELIDADE", OK if not ruins else FAIL,
        "o que foi dito bate com o roteiro" if not ruins
        else f"tomadas divergentes do roteiro (bloco, similaridade): {ruins}",
        None, ">=0.90")
    add("NARRACAO", "PRONUNCIA_PTBR", OK if not sotaque else WARN,
        "pronuncia limpa em pt-BR" if not sotaque
        else f"transcricao pt-BR imprecisa (indicio de sotaque/robotizacao): {sotaque}",
        None, ">=0.95")


# --------------------------------------------------------------- LEGENDA ---
CUE = re.compile(r"(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
                 r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n(.*?)(?=\n\s*\n|\Z)", re.S)


def t2s(t):
    h, m, s = t.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_srt(path):
    txt = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    if not txt.strip().endswith("\n"):
        txt += "\n\n"
    return [{"n": int(a), "ini": t2s(b), "fim": t2s(c),
             "linhas": [l for l in d.strip().split("\n") if l.strip()],
             "texto": " ".join(l.strip() for l in d.strip().split("\n") if l.strip())}
            for a, b, c, d in CUE.findall(txt)]


def check_legenda(srt, sidecar, script_rows, vdur):
    if not srt or not os.path.exists(srt):
        add("LEGENDA", "ARQUIVO", FAIL,
            "final.srt ausente — legenda nao passou pelos scripts oficiais")
        return
    cues = parse_srt(srt)
    if not cues:
        add("LEGENDA", "SINTAXE", FAIL, "SRT vazio ou ilegivel")
        return
    add("LEGENDA", "SINTAXE", OK, f"{len(cues)} legendas lidas")

    sobrepostos, curtos, longos, cps_ruim, largura, muitas = [], [], [], [], [], []
    for i, c in enumerate(cues):
        d = c["fim"] - c["ini"]
        if i and c["ini"] < cues[i - 1]["fim"] - 0.01:
            sobrepostos.append(c["n"])
        if d < 0.6:
            curtos.append((c["n"], round(d, 2)))
        if d > 7.0:
            longos.append((c["n"], round(d, 2)))
        if d > 0 and len(c["texto"]) / d > 20:
            cps_ruim.append((c["n"], round(len(c["texto"]) / d, 1)))
        if any(len(l) > 42 for l in c["linhas"]):
            largura.append(c["n"])
        if len(c["linhas"]) > 2:
            muitas.append(c["n"])
        if c["fim"] > vdur + 0.3:
            add("LEGENDA", "ALEM_DO_FIM", FAIL,
                f"legenda {c['n']} termina em {c['fim']:.2f}s, depois do video ({vdur:.2f}s)")
    add("LEGENDA", "SOBREPOSICAO", OK if not sobrepostos else FAIL,
        "sem sobreposicao" if not sobrepostos else f"legendas sobrepostas: {sobrepostos}")
    add("LEGENDA", "DURACAO_CUE", OK if not (curtos or longos) else WARN,
        "duracoes entre 0.6s e 7s" if not (curtos or longos)
        else f"curtas demais: {curtos[:5]} · longas demais: {longos[:5]}")
    add("LEGENDA", "VELOCIDADE_LEITURA", OK if not cps_ruim else WARN,
        "<=20 caracteres/s" if not cps_ruim else f"leitura acelerada: {cps_ruim[:5]}",
        None, "<=20 cps")
    add("LEGENDA", "FORMATO_LINHA", OK if not (largura or muitas) else WARN,
        "<=2 linhas, <=42 caracteres" if not (largura or muitas)
        else f"linhas longas: {largura[:5]} · mais de 2 linhas: {muitas[:5]}")

    texto_srt = " ".join(c["texto"] for c in cues)
    if script_rows:
        roteiro = " ".join(script_rows)
        s = sim(texto_srt, roteiro)
        add("LEGENDA", "FIDELIDADE_ROTEIRO", OK if s >= 0.97 else FAIL,
            f"similaridade legenda x roteiro {s:.3f}", round(s, 3), ">=0.97")
        faltando = [w for w in set(norm_tokens(roteiro)) - set(norm_tokens(texto_srt))
                    if len(w) > 3]
        add("LEGENDA", "COBERTURA", OK if len(faltando) <= 2 else FAIL,
            "toda palavra falada aparece na legenda" if len(faltando) <= 2
            else f"{len(faltando)} palavras do roteiro faltam na legenda: {sorted(faltando)[:8]}")
        # o roteiro e' a fonte da grafia: palavra que aparece SO' na legenda foi
        # inventada pelo STT — e' exatamente assim que nasce um erro ortografico
        # na tela, ja' que ninguem revisa a legenda depois da queima.
        intrusas = [w for w in set(norm_tokens(texto_srt)) - set(norm_tokens(roteiro))
                    if len(w) > 3]
        add("LEGENDA", "PALAVRA_ESTRANHA", OK if not intrusas else FAIL,
            "nenhuma palavra fora do roteiro" if not intrusas
            else f"{len(intrusas)} palavras na legenda que nao estao no roteiro "
                 f"(grafia nao revisada): {sorted(intrusas)[:8]}")

    if sidecar and sidecar.get("per_block"):
        pb = sidecar["per_block"]
        jan = float(sidecar.get("clip_seconds") or 10)
        fora, cruzam, blocos = [], [], {}
        for c in cues:
            meio = (c["ini"] + c["fim"]) / 2
            dentro = False
            for b in pb:
                ini = float(b.get("speech_abs_s") or 0)
                fim = ini + float(b.get("speech_s") or 0)
                if ini - 0.30 <= meio <= fim + 0.30:
                    dentro = True
                    blocos.setdefault(b.get("n"), []).append(c)
                    if c["ini"] < ini - 0.45 or c["fim"] > fim + 0.60:
                        cruzam.append((c["n"], "sai da fala do bloco", round(c["ini"], 2)))
                    break
            if not dentro:
                fora.append((c["n"], round(c["ini"], 2)))
            bi, bf = int(c["ini"] // jan), int((c["fim"] - 0.02) // jan)
            if bi != bf:
                cruzam.append((c["n"], "atravessa dois blocos", bi + 1))
        add("LEGENDA", "SINCRONIA", OK if not fora else FAIL,
            "toda legenda cai dentro da fala medida" if not fora
            else f"legendas fora de qualquer janela de fala: {fora[:6]}",
            None, "+-0.30s da fala")
        add("LEGENDA", "DERIVA", OK if not cruzam else FAIL,
            "sem deriva contra a fala/imagem" if not cruzam
            else f"legendas que escapam da janela ou do bloco: {cruzam[:6]}")

        # Deriva DENTRO do bloco: as legendas de um bloco devem dividir a janela
        # de fala na proporcao do texto. Uma legenda certa na janela mas adiantada
        # dois segundos passa por todos os testes acima e ainda assim aparece antes
        # da palavra — este e' o teste que a pega.
        atraso = []
        for b in pb:
            cs = blocos.get(b.get("n")) or []
            ini = float(b.get("speech_abs_s") or 0)
            dur = float(b.get("speech_s") or 0)
            total = sum(len(c["texto"]) for c in cs)
            if not cs or total == 0 or dur <= 0:
                continue
            corrido = 0
            for c in cs:
                previsto = ini + dur * corrido / total
                if abs(c["ini"] - previsto) > 1.0:
                    atraso.append((c["n"], round(c["ini"] - previsto, 2)))
                corrido += len(c["texto"])
        add("LEGENDA", "SINCRONIA_INTERNA", OK if not atraso else FAIL,
            "cada legenda entra junto com a palavra" if not atraso
            else f"legendas adiantadas/atrasadas dentro do bloco (cue, segundos): {atraso[:6]}",
            None, "+-1.0s do previsto pelo tamanho do texto")

    if ptbr_check:
        iss = []
        for c in cues:
            iss += ptbr_check(c["texto"], "legenda", c["n"])
        erros = [i for i in iss if i["severity"] == "erro"]
        add("LEGENDA", "ORTOGRAFIA", OK if not erros else FAIL,
            "sem erro ortografico detectado" if not erros
            else f"{len(erros)} erros: " + "; ".join(
                f'#{i["line"]} {i["code"]} "{i["term"]}" -> {i["fix"]}' for i in erros[:6]))
    else:
        add("LEGENDA", "ORTOGRAFIA", SKIP, "ptbr_lint.py nao encontrado ao lado deste script")


# -------------------------------------------------------------- TRIMODAL ---
def check_trimodal(script_path, script_rows, cues_srt, vdur):
    # 1) so escutando: narracao autonoma
    if ptbr_check and script_rows:
        iss = []
        for i, l in enumerate(script_rows, 1):
            iss += ptbr_check(l, "narracao", i)
        deixis = [i for i in iss if i["code"] == "DEIXIS_VISUAL"]
        erros = [i for i in iss if i["severity"] == "erro" and i["code"] != "DEIXIS_VISUAL"]
        add("TRIMODAL", "AUDIO_AUTONOMO", OK if not deixis else FAIL,
            "narracao nao depende da imagem" if not deixis
            else "narracao aponta para a imagem: " + "; ".join(
                f'bloco {i["line"]}: "{i["term"]}"' for i in deixis[:5]))
        add("TRIMODAL", "TEXTO_FALADO", OK if not erros else FAIL,
            "roteiro pronto para TTS" if not erros
            else f"{len(erros)} problemas no texto falado: " + "; ".join(
                f'bloco {i["line"]} {i["code"]} "{i["term"]}"' for i in erros[:6]))

    # 2) so olhando: proposicao visual declarada por bloco
    dados = {}
    if script_path and os.path.exists(script_path):
        dados = json.load(open(script_path, encoding="utf-8"))
    rows = dados.get("blocks") or dados.get("beats") or []
    vps = [(r.get("visual_proposition") or "").strip() for r in rows]
    vazios = [i + 1 for i, v in enumerate(vps) if not v]
    if rows:
        add("TRIMODAL", "PROPOSICAO_VISUAL", OK if not vazios else FAIL,
            "todo bloco declara o que a imagem afirma sozinha" if not vazios
            else f"blocos sem visual_proposition no manifesto: {vazios}")
        chaves = [" ".join(sorted(set(norm_tokens(v)))) for v in vps if v]
        repetidos = [i + 1 for i in range(1, len(chaves)) if sim(chaves[i], chaves[i - 1]) > 0.85]
        add("TRIMODAL", "VARIEDADE_VISUAL", OK if not repetidos else WARN,
            "cada bloco mostra coisa nova" if not repetidos
            else f"blocos que repetem a imagem do anterior: {repetidos}")
        semkey = [i + 1 for i, r in enumerate(rows)
                  if not (r.get("key_visual") or r.get("visual_proposition"))]
        if semkey:
            add("TRIMODAL", "QUADRO_CHAVE", WARN, f"blocos sem key_visual: {semkey}")
    else:
        add("TRIMODAL", "PROPOSICAO_VISUAL", SKIP,
            "manifesto sem blocks/beats — nao da para auditar a camada visual")

    # 3) so lendo: gancho e fechamento presentes no texto
    if script_rows:
        gancho = script_rows[0]
        n = len(norm_tokens(gancho))
        add("TRIMODAL", "GANCHO", OK if n >= 8 else WARN,
            f"primeiro bloco com {n} palavras", n, ">=8")
        fecho = script_rows[-1]
        add("TRIMODAL", "FECHAMENTO", OK if len(norm_tokens(fecho)) >= 8 else WARN,
            "ultimo bloco fecha a ideia")
    if cues_srt:
        add("TRIMODAL", "LEGENDA_DESDE_O_INICIO", OK if cues_srt[0]["ini"] <= 2.5 else WARN,
            f"primeira legenda em {cues_srt[0]['ini']:.2f}s",
            round(cues_srt[0]["ini"], 2), "<=2.5s")


# ------------------------------------------------------------- THUMBNAIL ---
def luminancia(rgb):
    def c(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb[:3]
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)


def check_thumb(thumb, texto, aspect):
    if not thumb:
        add("THUMBNAIL", "ARQUIVO", FAIL, "nenhuma thumbnail entregue")
        return
    if not os.path.exists(thumb):
        add("THUMBNAIL", "ARQUIVO", FAIL, f"thumbnail nao encontrada: {thumb}")
        return
    try:
        from PIL import Image, ImageStat
    except Exception:
        add("THUMBNAIL", "ARQUIVO", SKIP, "PIL indisponivel")
        return
    im = Image.open(thumb).convert("RGB")
    w, h = im.size
    peso = os.path.getsize(thumb)
    minw, minh = (1280, 720) if aspect == "16:9" else (720, 1280)
    add("THUMBNAIL", "DIMENSAO", OK if (w >= minw and h >= minh) else FAIL,
        f"{w}x{h}", f"{w}x{h}", f">={minw}x{minh}")
    alvo = {"16:9": 16 / 9, "9:16": 9 / 16, "1:1": 1.0}.get(aspect, 16 / 9)
    add("THUMBNAIL", "PROPORCAO", OK if abs(w / h - alvo) < 0.03 else FAIL,
        f"{w/h:.3f}", round(w / h, 3), round(alvo, 3))
    add("THUMBNAIL", "PESO", OK if peso <= 2_000_000 else WARN,
        f"{peso/1e6:.2f} MB", round(peso / 1e6, 2), "<=2 MB (limite do YouTube)")

    if texto:
        if ptbr_check:
            iss = [i for i in ptbr_check(texto, "thumb", 1) if i["severity"] == "erro"]
            add("THUMBNAIL", "TEXTO", OK if not iss else FAIL,
                f'texto "{texto}" aprovado' if not iss
                else "; ".join(f'{i["code"]}: {i["msg"]}' for i in iss))
        cx = os.path.splitext(thumb)[0] + ".textbox.json"
        if os.path.exists(cx):
            box = json.load(open(cx, encoding="utf-8"))
            x0, y0, x1, y1 = box["box"]
            fundo = ImageStat.Stat(im.crop((x0, y0, x1, y1))).mean
            cor = box.get("rgb", [255, 255, 255])
            L1, L2 = luminancia(cor), luminancia(fundo)
            hi, lo = max(L1, L2), min(L1, L2)
            razao = (hi + 0.05) / (lo + 0.05)
            add("THUMBNAIL", "CONTRASTE", OK if razao >= 4.5 else FAIL,
                f"contraste texto/fundo {razao:.1f}:1", round(razao, 1), ">=4.5:1")
            altura = (y1 - y0) / h
            add("THUMBNAIL", "LEGIBILIDADE_168PX", OK if altura >= 0.09 else FAIL,
                f"altura do texto = {altura*100:.0f}% do quadro "
                f"({altura*94:.1f} px em uma miniatura de 168 px)",
                round(altura, 3), ">=0.09")
            add("THUMBNAIL", "TEXTO_COMPOSTO", OK,
                "texto aplicado no sandbox (nao gerado pelo modelo)")
        else:
            add("THUMBNAIL", "TEXTO_COMPOSTO", WARN,
                "sem .textbox.json ao lado da imagem — contraste e legibilidade nao medidos; "
                "se o texto foi gerado pelo modelo de imagem, refaca com thumb_text.sh")
    else:
        add("THUMBNAIL", "TEXTO", WARN, "nenhum texto declarado (--thumb-text)")

    peq = im.resize((168, max(1, int(168 * h / w))))
    st = ImageStat.Stat(peq.convert("L"))
    add("THUMBNAIL", "CONTRASTE_GLOBAL", OK if st.stddev[0] >= 40 else WARN,
        f"desvio de luminancia a 168 px: {st.stddev[0]:.0f}",
        round(st.stddev[0]), ">=40")


# ------------------------------------------------------------------ MAIN ---
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--sidecar")
    ap.add_argument("--srt")
    ap.add_argument("--script")
    ap.add_argument("--voice-dir")
    ap.add_argument("--thumb")
    ap.add_argument("--thumb-text")
    ap.add_argument("--aspect", default="16:9", choices=["16:9", "9:16", "1:1"])
    ap.add_argument("--sem-whisper", action="store_true")
    ap.add_argument("--rapido", action="store_true", help="pula analise de quadros e cortes")
    ap.add_argument("--json", default="qc_report.json")
    a = ap.parse_args()

    if not os.path.exists(a.video):
        print(f"video nao encontrado: {a.video}", file=sys.stderr)
        return 2

    sidecar = None
    if a.sidecar and os.path.exists(a.sidecar):
        sidecar = json.load(open(a.sidecar, encoding="utf-8"))
        if sidecar.get("script") not in ("assemble_final.sh", "assemble_slides.sh"):
            add("IMAGEM", "PROVENIENCIA", FAIL,
                "o sidecar nao veio do montador oficial — arquivo montado a mao")
        else:
            add("IMAGEM", "PROVENIENCIA", OK,
                f"montado por {sidecar['script']} ({sidecar.get('blocks')} blocos)")
    else:
        add("IMAGEM", "PROVENIENCIA", FAIL,
            "sem final.mp4.assembly.json — nao ha prova de que o corte saiu do montador")

    script_rows = []
    if a.script and os.path.exists(a.script):
        d = json.load(open(a.script, encoding="utf-8"))
        rows = d.get("blocks") or d.get("beats") or []
        script_rows = [(r.get("vo_line") or r.get("phrase") or "") for r in rows]

    v = check_imagem(a.video, a.aspect, sidecar, not a.rapido)
    vdur = v["dur"] if v else 0.0
    check_audio(a.video, vdur)
    check_narracao(sidecar, script_rows, a.voice_dir, not a.sem_whisper)
    check_legenda(a.srt, sidecar, script_rows, vdur)
    cues = parse_srt(a.srt) if (a.srt and os.path.exists(a.srt)) else []
    check_trimodal(a.script, script_rows, cues, vdur)
    check_thumb(a.thumb, a.thumb_text, a.aspect)

    reprovas = [r for r in R if r["status"] == FAIL]
    avisos = [r for r in R if r["status"] == WARN]
    pulados = [r for r in R if r["status"] == SKIP]
    veredito = "REPROVADO" if reprovas else ("APROVADO COM AVISOS" if avisos else "APROVADO")

    largura = max(len(r["code"]) for r in R) + 2
    print("\n=========== QC-TRIMODAL ===========")
    area = None
    for r in R:
        if r["area"] != area:
            area = r["area"]
            print(f"\n[{area}]")
        marca = {OK: "OK  ", FAIL: "FALHA", WARN: "AVISO", SKIP: "----"}[r["status"]]
        print(f"  {marca} {r['code']:<{largura}} {r['msg']}")
    print(f"\nVEREDITO: {veredito}  "
          f"({len(reprovas)} falhas, {len(avisos)} avisos, {len(pulados)} nao verificados)")
    if reprovas:
        print("\nCORRIJA A ENTRADA E REFACA A ETAPA — nao entregue com falha:")
        for r in reprovas:
            print(f"  - [{r['area']}/{r['code']}] {r['msg']}")

    json.dump({"veredito": veredito, "falhas": len(reprovas), "avisos": len(avisos),
               "nao_verificados": len(pulados), "checks": R},
              open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\nrelatorio: {a.json}")
    return 1 if reprovas else 0


if __name__ == "__main__":
    sys.exit(main())
