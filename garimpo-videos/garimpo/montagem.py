"""Montagem de cortes com B-roll: inserção periódica e tela dividida.

Duas decisões que valem explicação, porque mudam o resultado:

1. **O áudio do corte base nunca é interrompido.** A inserção troca só a
   imagem durante a janela; a fala continua por baixo. É assim que corte
   com cutaway funciona de verdade — se o áudio picotasse junto, a frase
   quebraria no meio.

2. **O áudio do B-roll é sempre descartado.** Ele entra como recheio visual,
   e trilha de terceiros é a maior fonte de reivindicação de Content ID.
   Menos uma coisa para dar errado.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from dataclasses import dataclass, field


class ErroFFmpeg(Exception):
    pass


AJUDA_INSTALACAO = (
    "ffmpeg não encontrado. Instale com:\n"
    "  Ubuntu/Debian: sudo apt install ffmpeg\n"
    "  macOS:         brew install ffmpeg\n"
    "  Windows:       winget install Gyan.FFmpeg"
)


def achar_binario(nome: str) -> str:
    caminho = shutil.which(nome)
    if caminho:
        return caminho
    if nome == "ffmpeg":
        try:  # pacote opcional que traz um ffmpeg estático
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    raise ErroFFmpeg(AJUDA_INSTALACAO)


def ffmpeg_disponivel() -> bool:
    try:
        achar_binario("ffmpeg")
        achar_binario("ffprobe")
        return True
    except ErroFFmpeg:
        return False


# --------------------------------------------------------------------------- #
# sondagem
# --------------------------------------------------------------------------- #

@dataclass
class Midia:
    caminho: str
    duracao: float
    largura: int
    altura: int
    fps: float
    tem_audio: bool

    @property
    def vertical(self) -> bool:
        return self.altura > self.largura


def _fracao(texto: str) -> float:
    try:
        if "/" in texto:
            n, d = texto.split("/")
            return float(n) / float(d) if float(d) else 0.0
        return float(texto)
    except (ValueError, ZeroDivisionError):
        return 0.0


def sondar(caminho: str) -> Midia:
    if not os.path.isfile(caminho):
        raise ErroFFmpeg(f"Arquivo não encontrado: {caminho}")
    saida = subprocess.run(
        [achar_binario("ffprobe"), "-v", "error", "-show_streams", "-show_format",
         "-of", "json", caminho],
        capture_output=True, text=True,
    )
    if saida.returncode != 0:
        raise ErroFFmpeg(f"ffprobe falhou em {caminho}: {saida.stderr.strip()[:300]}")

    dados = json.loads(saida.stdout or "{}")
    video = next((s for s in dados.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        raise ErroFFmpeg(f"{caminho} não tem faixa de vídeo.")

    duracao = float(dados.get("format", {}).get("duration") or video.get("duration") or 0)
    fps = _fracao(video.get("avg_frame_rate") or "0") or _fracao(video.get("r_frame_rate") or "0")
    return Midia(
        caminho=caminho,
        duracao=duracao,
        largura=int(video.get("width") or 0),
        altura=int(video.get("height") or 0),
        fps=round(fps, 3) if fps else 30.0,
        tem_audio=any(s.get("codec_type") == "audio" for s in dados.get("streams", [])),
    )


# --------------------------------------------------------------------------- #
# planejamento (puro — testável sem tocar em ffmpeg)
# --------------------------------------------------------------------------- #

@dataclass
class ClipeBroll:
    caminho: str
    duracao: float
    credito: str = ""
    titulo: str = ""


@dataclass
class Insercao:
    inicio: float          # segundo do corte final onde a cena entra
    clipe: ClipeBroll
    offset: float          # de que ponto do clipe o trecho é tirado
    duracao: float

    @property
    def fim(self) -> float:
        return self.inicio + self.duracao


def planejar_insercoes(duracao_base: float, clipes: list[ClipeBroll],
                       intervalo: float = 8.0, duracao: float = 2.0,
                       primeiro: float | None = None, margem_final: float = 1.5,
                       maximo: int = 40, semente: int | None = None) -> list[Insercao]:
    """Distribui as cenas ao longo do corte.

    `intervalo` é o tempo de vídeo base entre uma inserção e a seguinte, então
    o passo real na linha do tempo é intervalo + duracao.
    """
    if not clipes or duracao_base <= 0 or duracao <= 0:
        return []

    rng = random.Random(semente)
    ordem = list(range(len(clipes)))
    rng.shuffle(ordem)

    # A primeira inserção nunca cai no gancho: os primeiros segundos decidem a
    # retenção e não podem ser interrompidos por cena aleatória.
    momento = primeiro if primeiro is not None else intervalo
    limite = duracao_base - margem_final

    insercoes: list[Insercao] = []
    passo_ordem = 0
    while momento + duracao <= limite and len(insercoes) < maximo:
        clipe = clipes[ordem[passo_ordem % len(ordem)]]
        passo_ordem += 1

        dur_efetiva = min(duracao, clipe.duracao) if clipe.duracao else duracao
        folga = (clipe.duracao - dur_efetiva) if clipe.duracao else 0
        offset = round(rng.uniform(0, folga), 2) if folga > 0.2 else 0.0

        insercoes.append(Insercao(round(momento, 3), clipe, offset, round(dur_efetiva, 3)))
        momento += intervalo + dur_efetiva

    return insercoes


# --------------------------------------------------------------------------- #
# execução
# --------------------------------------------------------------------------- #

def _rodar(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        cauda = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise ErroFFmpeg(f"ffmpeg falhou:\n{cauda}")


def _preencher(largura: int, altura: int, fps: float) -> str:
    """Escala cobrindo o quadro e corta o excesso — sem tarja preta."""
    return (f"scale={largura}:{altura}:force_original_aspect_ratio=increase,"
            f"crop={largura}:{altura},setsar=1,fps={fps}")


@dataclass
class Resultado:
    saida: str
    modo: str
    insercoes: list[Insercao] = field(default_factory=list)
    clipes_usados: list[ClipeBroll] = field(default_factory=list)
    duracao: float = 0.0


def montar_insercao(base: str, insercoes: list[Insercao], saida: str,
                    largura: int = 0, altura: int = 0, fps: float = 0,
                    crf: int = 20, preset: str = "medium") -> Resultado:
    midia = sondar(base)
    largura = largura or midia.largura
    altura = altura or midia.altura
    fps = fps or min(midia.fps or 30, 60)

    if not insercoes:
        raise ErroFFmpeg("Nenhuma inserção planejada — corte curto demais para o intervalo pedido.")

    entradas = ["-i", base]
    partes = [f"[0:v]{_preencher(largura, altura, fps)}[v0]"]
    rotulo = "v0"

    for i, ins in enumerate(insercoes, start=1):
        entradas += ["-i", ins.clipe.caminho]
        partes.append(
            f"[{i}:v]trim=start={ins.offset}:duration={ins.duracao},"
            f"setpts=PTS-STARTPTS+{ins.inicio}/TB,{_preencher(largura, altura, fps)}[c{i}]"
        )
        # `enable` acende a sobreposição só na janela; `eof_action=pass` deixa o
        # vídeo base seguir quando o clipe acaba.
        partes.append(
            f"[{rotulo}][c{i}]overlay=0:0:enable='between(t,{ins.inicio},{ins.fim})'"
            f":eof_action=pass:shortest=0[v{i}]"
        )
        rotulo = f"v{i}"

    args = [achar_binario("ffmpeg"), "-y", "-loglevel", "error", *entradas,
            "-filter_complex", ";".join(partes), "-map", f"[{rotulo}]"]
    if midia.tem_audio:
        args += ["-map", "0:a", "-c:a", "aac", "-b:a", "160k"]
    args += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida]
    _rodar(args)

    vistos, usados = set(), []
    for ins in insercoes:
        if ins.clipe.caminho not in vistos:
            vistos.add(ins.clipe.caminho)
            usados.append(ins.clipe)

    return Resultado(saida=saida, modo="insercao", insercoes=insercoes,
                     clipes_usados=usados, duracao=sondar(saida).duracao)


def montar_split(base: str, clipes: list[ClipeBroll], saida: str,
                 largura: int = 1080, altura: int = 1920, fps: float = 30,
                 crf: int = 20, preset: str = "medium",
                 proporcao_topo: float = 0.5, temporario: str = "") -> Resultado:
    if not clipes:
        raise ErroFFmpeg("Nenhum clipe de B-roll para a faixa de baixo.")

    midia = sondar(base)
    # vstack exige a mesma largura nas duas metades, e a altura precisa ser par.
    altura_topo = int(altura * proporcao_topo) // 2 * 2
    altura_baixo = altura - altura_topo

    ffmpeg = achar_binario("ffmpeg")
    temporario = temporario or os.path.join(os.path.dirname(os.path.abspath(saida)) or ".",
                                            ".faixa-broll.mp4")

    # Passo 1: emenda os clipes numa faixa única já no tamanho de baixo.
    entradas, partes, rotulos = [], [], []
    for i, clipe in enumerate(clipes):
        entradas += ["-i", clipe.caminho]
        partes.append(f"[{i}:v]{_preencher(largura, altura_baixo, fps)}[f{i}]")
        rotulos.append(f"[f{i}]")
    partes.append(f"{''.join(rotulos)}concat=n={len(clipes)}:v=1:a=0[faixa]")
    _rodar([ffmpeg, "-y", "-loglevel", "error", *entradas,
            "-filter_complex", ";".join(partes), "-map", "[faixa]",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-pix_fmt", "yuv420p", temporario])

    # Passo 2: empilha. -stream_loop repete a faixa até cobrir o corte inteiro.
    args = [ffmpeg, "-y", "-loglevel", "error", "-i", base,
            "-stream_loop", "-1", "-i", temporario,
            "-filter_complex",
            f"[0:v]{_preencher(largura, altura_topo, fps)}[topo];"
            f"[1:v]{_preencher(largura, altura_baixo, fps)}[baixo];"
            f"[topo][baixo]vstack=inputs=2[v]",
            "-map", "[v]"]
    if midia.tem_audio:
        args += ["-map", "0:a", "-c:a", "aac", "-b:a", "160k"]
    args += ["-t", f"{midia.duracao:.3f}", "-c:v", "libx264", "-preset", preset,
             "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", saida]
    _rodar(args)

    try:
        os.remove(temporario)
    except OSError:
        pass

    return Resultado(saida=saida, modo="split", clipes_usados=list(clipes),
                     duracao=sondar(saida).duracao)


# --------------------------------------------------------------------------- #
# créditos da montagem
# --------------------------------------------------------------------------- #

def escrever_creditos(resultado: Resultado, caminho: str, credito_base: str = "",
                      editor: str = "") -> str:
    linhas = ["CRÉDITOS DA MONTAGEM", "=" * 60, ""]
    if credito_base:
        linhas += ["Vídeo base:", f"  {credito_base}", ""]
    else:
        linhas += ["Vídeo base:",
                   "  [preencha aqui o crédito do corte base — use o comando 'creditos']", ""]

    if resultado.clipes_usados:
        linhas.append(f"B-roll ({len(resultado.clipes_usados)} clipes):")
        for clipe in resultado.clipes_usados:
            linhas.append(f"  {clipe.credito or clipe.titulo or clipe.caminho}")
            if resultado.insercoes:
                momentos = [f"{i.inicio:.1f}s" for i in resultado.insercoes
                            if i.clipe.caminho == clipe.caminho]
                if momentos:
                    linhas.append(f"      aparece em: {', '.join(momentos)}")
        linhas.append("")

    if editor:
        linhas += [f"Corte, montagem e edição: {editor}", ""]

    linhas += [
        "Observações:",
        "  - O áudio dos clipes de B-roll foi descartado na montagem.",
        "  - Cole este bloco na descrição da publicação.",
        "  - Guarde este arquivo: é a sua prova de origem de cada cena usada.",
        "",
    ]
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    return caminho
