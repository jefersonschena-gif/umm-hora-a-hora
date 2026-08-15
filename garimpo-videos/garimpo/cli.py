"""Linha de comando do garimpo."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

from . import __version__
from .fontes import REGISTRO, TODAS, Busca
from .fontes.archive_org import ArchiveOrg
from .licencas import LICENCAS, NIVEIS, licenca_de, resumo_licencas, texto_credito
from .modelos import Video, duracao_legivel, numero_curto
from .montagem import (AJUDA_INSTALACAO, ClipeBroll, ErroFFmpeg, escrever_creditos,
                       ffmpeg_disponivel, montar_insercao, montar_split,
                       planejar_insercoes, sondar)
from .relatorio import (carregar_json, garantir_pasta, imprimir_tabela,
                        salvar_csv, salvar_html, salvar_json)
from .scoring import pontuar_lista
from .util_http import ErroHTTP, baixar_arquivo, get_json
from . import licencas as mod_licencas


# --------------------------------------------------------------------------- #
# apoio
# --------------------------------------------------------------------------- #

def carregar_env() -> None:
    """Lê um .env simples (CHAVE=valor) do diretório atual ou do projeto."""
    candidatos = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    ]
    for caminho in candidatos:
        if not os.path.isfile(caminho):
            continue
        with open(caminho, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))
        return


def nome_arquivo_seguro(texto: str) -> str:
    limpo = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", limpo)[:60] or "busca"


def extrair_id_youtube(entrada: str) -> str:
    padroes = [r"v=([A-Za-z0-9_-]{11})", r"youtu\.be/([A-Za-z0-9_-]{11})",
               r"shorts/([A-Za-z0-9_-]{11})", r"embed/([A-Za-z0-9_-]{11})"]
    for p in padroes:
        m = re.search(p, entrada)
        if m:
            return m.group(1)
    return entrada.strip()


# --------------------------------------------------------------------------- #
# comandos
# --------------------------------------------------------------------------- #

def cmd_fontes(args) -> int:
    print(f"\nGarimpo de vídeos v{__version__} — fontes disponíveis\n")
    for nome, fonte in REGISTRO.items():
        status = "pronta" if fonte.disponivel() else f"FALTA {fonte.env_chave}"
        print(f"  {nome:<12} {fonte.rotulo}")
        print(f"  {'':<12} licença padrão: {LICENCAS[fonte.licenca_padrao].nome}")
        print(f"  {'':<12} download oficial: {'sim' if fonte.tem_download else 'não'}")
        print(f"  {'':<12} status: {status}"
              + (f"  → chave em {fonte.url_chave}" if not fonte.disponivel() else ""))
        print()
    print("Licenças reconhecidas:\n")
    print(resumo_licencas())
    print("\nColoque as chaves num arquivo .env ao lado do garimpar.py (veja exemplo.env).\n")
    return 0


def cmd_buscar(args) -> int:
    fontes_pedidas = [f.strip() for f in args.fontes.split(",") if f.strip()]
    desconhecidas = [f for f in fontes_pedidas if f not in REGISTRO]
    if desconhecidas:
        print(f"Fonte desconhecida: {', '.join(desconhecidas)}. Use: {', '.join(TODAS)}")
        return 2

    temas = args.tema
    coletados: list[Video] = []
    vistos: set[tuple[str, str]] = set()

    for nome in fontes_pedidas:
        fonte = REGISTRO[nome]
        if not fonte.disponivel():
            print(f"[pulando] {nome}: falta a variável {fonte.env_chave} "
                  f"(chave em {fonte.url_chave})")
            continue
        for tema in temas:
            print(f"[buscando] {nome} ← \"{tema}\"")
            try:
                achados = fonte.buscar(Busca(tema=tema, dias=args.dias, limite=args.limite,
                                             regiao=args.regiao, idioma=args.idioma))
            except ErroHTTP as e:
                print(f"[erro] {nome}: {e}")
                continue
            except RuntimeError as e:
                print(f"[erro] {nome}: {e}")
                continue
            novos = 0
            for v in achados:
                chave = (v.fonte, v.id)
                if chave in vistos:
                    continue
                vistos.add(chave)
                v.extra["tema_buscado"] = tema
                coletados.append(v)
                novos += 1
            print(f"           {novos} novos (de {len(achados)} retornados)")

    if not coletados:
        print("\nNada coletado. Confira as chaves de API com: python garimpar.py fontes")
        return 1

    pontuar_lista(coletados)
    for v in coletados:
        mod_licencas.avaliar(v)

    teto_risco = NIVEIS.index(args.risco_max)
    filtrados = [
        v for v in coletados
        if v.score >= args.min_score
        and NIVEIS.index(v.risco) <= teto_risco
        and (not args.dur_min or v.duracao_s >= args.dur_min)
        and (not args.dur_max or v.duracao_s <= args.dur_max or not v.duracao_s)
        and (not args.so_vertical or v.vertical)
    ]
    filtrados.sort(key=lambda v: v.score, reverse=True)

    descartados = len(coletados) - len(filtrados)
    print(f"\n{len(coletados)} vídeos coletados · {len(filtrados)} passaram nos filtros "
          f"({descartados} descartados por score, risco ou formato)")

    imprimir_tabela(filtrados, limite=args.mostrar)

    pasta = garantir_pasta(args.saida)
    base = os.path.join(pasta, f"{dt.date.today():%Y-%m-%d}-{nome_arquivo_seguro(temas[0])}")
    salvar_json(filtrados, base + ".json")
    salvar_csv(filtrados, base + ".csv")
    salvar_html(filtrados, base + ".html", tema=" / ".join(temas))
    print(f"\nArquivos gerados:\n  {base}.html   ← abra este no navegador\n"
          f"  {base}.csv\n  {base}.json   ← use com os comandos baixar e creditos\n")
    return 0


class DownloadBloqueado(Exception):
    """A fonte não oferece download oficial (caso do YouTube)."""


def baixar_video(v: Video, pasta: str, reaproveitar: bool = True) -> str:
    """Baixa um vídeo e devolve o caminho local. Usado por `baixar` e `montar`."""
    fonte = REGISTRO.get(v.fonte)
    if not fonte or not fonte.tem_download:
        # Caso do YouTube: mesmo com licença CC, baixar o arquivo pelo
        # navegador/ripper fere os Termos de Uso da plataforma. A licença
        # do vídeo e o contrato de uso do site são coisas separadas.
        raise DownloadBloqueado(
            f"{v.fonte} não oferece download oficial. Use o material pelo editor "
            f"do próprio YouTube ou peça o arquivo ao autor: {v.url}"
        )

    url = v.download_url
    if not url and v.fonte == "archive":
        url = ArchiveOrg.resolver_download(v.id)
    if not url:
        raise ErroHTTP(f"Sem arquivo disponível para {v.id}")

    extensao = os.path.splitext(url.split("?")[0])[1] or ".mp4"
    destino = os.path.join(pasta, f"{v.fonte}-{nome_arquivo_seguro(v.titulo)}-{v.id}{extensao}")
    if reaproveitar and os.path.isfile(destino) and os.path.getsize(destino) > 0:
        return destino
    baixar_arquivo(url, destino)
    return destino


def cmd_baixar(args) -> int:
    videos = carregar_json(args.arquivo)
    if args.ids:
        alvo = set(args.ids)
        videos = [v for v in videos if v.id in alvo]
    else:
        videos = videos[:args.top]

    pasta = garantir_pasta(args.destino)
    baixados = bloqueados = falhas = 0

    for v in videos:
        try:
            destino = baixar_video(v, pasta)
        except DownloadBloqueado as e:
            print(f"[bloqueado] {v.titulo[:60]}")
            print(f"            {e}")
            bloqueados += 1
            continue
        except ErroHTTP as e:
            print(f"[erro] {v.id}: {e}")
            falhas += 1
            continue

        tamanho = os.path.getsize(destino) / 1_048_576
        print(f"[baixado] {os.path.basename(destino)} ({tamanho:.1f} MB)")

        with open(destino + ".credito.txt", "w", encoding="utf-8") as f:
            f.write(texto_credito(v, editor=args.editor) + "\n")
            if v.alertas:
                f.write("\nAtenção antes de publicar:\n")
                for a in v.alertas:
                    f.write(f"- {a}\n")
        baixados += 1

    print(f"\n{baixados} baixados · {bloqueados} bloqueados por termos de uso · {falhas} falhas")
    if baixados:
        print("Cada arquivo saiu com um .credito.txt ao lado. "
              "Não jogue fora — é a sua prova de origem.")
    return 0 if baixados or not videos else 1


def cmd_creditos(args) -> int:
    videos = carregar_json(args.arquivo)
    if args.ids:
        alvo = set(args.ids)
        videos = [v for v in videos if v.id in alvo]
    else:
        videos = videos[:args.top]
    for v in videos:
        print(texto_credito(v, editor=args.editor))
    return 0


def _clipes_de_json(arquivo: str, cache: str, maximo: int, editor: str) -> list[ClipeBroll]:
    """Escolhe, baixa e sonda o B-roll a partir de um resultado do garimpo."""
    candidatos = [
        v for v in carregar_json(arquivo)
        if v.risco != "ALTO"
        and licenca_de(v).permite_derivados
        and licenca_de(v).permite_comercial
        and (REGISTRO.get(v.fonte).tem_download if REGISTRO.get(v.fonte) else False)
    ]
    candidatos.sort(key=lambda v: v.score, reverse=True)
    if not candidatos:
        print("Nenhum clipe do arquivo serve como B-roll: ou o risco é ALTO, ou a fonte "
              "não permite download oficial. Rode o buscar com --fontes pexels,pixabay,archive")
        return []

    pasta = garantir_pasta(cache)
    clipes: list[ClipeBroll] = []
    for v in candidatos:
        if len(clipes) >= maximo:
            break
        try:
            caminho = baixar_video(v, pasta)
        except (DownloadBloqueado, ErroHTTP) as e:
            print(f"[pulando] {v.titulo[:50]}: {e}")
            continue
        try:
            midia = sondar(caminho)
        except ErroFFmpeg as e:
            print(f"[pulando] {v.titulo[:50]}: {e}")
            continue
        if midia.duracao < 1.0:
            print(f"[pulando] {v.titulo[:50]}: clipe curto demais ({midia.duracao:.1f}s)")
            continue
        print(f"[b-roll] {os.path.basename(caminho)} ({midia.duracao:.1f}s, "
              f"{midia.largura}x{midia.altura})")
        clipes.append(ClipeBroll(caminho=caminho, duracao=midia.duracao,
                                 credito=texto_credito(v, editor=""), titulo=v.titulo))
    return clipes


def _clipes_de_pasta(pasta: str) -> list[ClipeBroll]:
    extensoes = (".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi")
    clipes = []
    for nome in sorted(os.listdir(pasta)):
        if not nome.lower().endswith(extensoes):
            continue
        caminho = os.path.join(pasta, nome)
        try:
            midia = sondar(caminho)
        except ErroFFmpeg as e:
            print(f"[pulando] {nome}: {e}")
            continue
        credito = ""
        arquivo_credito = caminho + ".credito.txt"
        if os.path.isfile(arquivo_credito):
            with open(arquivo_credito, encoding="utf-8") as f:
                credito = f.readline().strip()
        clipes.append(ClipeBroll(caminho=caminho, duracao=midia.duracao,
                                 credito=credito, titulo=nome))
    return clipes


def cmd_montar(args) -> int:
    if not ffmpeg_disponivel():
        print(AJUDA_INSTALACAO)
        return 2
    if not os.path.isfile(args.base):
        print(f"Vídeo base não encontrado: {args.base}")
        return 2
    if not args.broll and not args.broll_dir:
        print("Informe --broll (o .json do garimpo) ou --broll-dir (pasta com arquivos).")
        return 2

    base = sondar(args.base)
    print(f"[base] {os.path.basename(args.base)} · {base.duracao:.1f}s · "
          f"{base.largura}x{base.altura} · {base.fps:g}fps · "
          f"{'com áudio' if base.tem_audio else 'SEM áudio'}")

    if args.broll_dir:
        clipes = _clipes_de_pasta(args.broll_dir)
    else:
        cache = args.cache or os.path.join(os.path.dirname(os.path.abspath(args.broll)),
                                           "broll-cache")
        clipes = _clipes_de_json(args.broll, cache, args.max_clipes, args.editor)

    if not clipes:
        print("Sem B-roll utilizável — nada a montar.")
        return 1

    largura, altura = 0, 0
    if args.resolucao:
        try:
            largura, altura = (int(x) for x in args.resolucao.lower().split("x"))
        except ValueError:
            print("Formato de --resolucao inválido. Use por exemplo 1080x1920.")
            return 2
    elif args.vertical:
        largura, altura = 1080, 1920

    try:
        if args.modo == "split":
            resultado = montar_split(
                args.base, clipes, args.saida,
                largura=largura or 1080, altura=altura or 1920,
                fps=args.fps or min(base.fps or 30, 60), crf=args.crf,
                preset=args.preset, proporcao_topo=args.proporcao_topo)
        else:
            insercoes = planejar_insercoes(
                base.duracao, clipes, intervalo=args.intervalo, duracao=args.duracao,
                primeiro=args.primeiro, maximo=args.max_insercoes, semente=args.semente)
            if not insercoes:
                print(f"\nO corte tem {base.duracao:.1f}s — curto demais para inserir a cada "
                      f"{args.intervalo:g}s. Diminua o --intervalo ou use --modo split.")
                return 1
            print(f"\n[plano] {len(insercoes)} inserções de {args.duracao:g}s:")
            for ins in insercoes:
                print(f"         {ins.inicio:6.1f}s → {ins.fim:5.1f}s  "
                      f"{os.path.basename(ins.clipe.caminho)[:44]}")
            print("\n[codificando] isso leva um tempo proporcional à duração do corte...")
            resultado = montar_insercao(
                args.base, insercoes, args.saida,
                largura=largura, altura=altura, fps=args.fps,
                crf=args.crf, preset=args.preset)
    except ErroFFmpeg as e:
        print(f"\nErro na montagem: {e}")
        return 1

    creditos = escrever_creditos(resultado, args.saida + ".credito.txt",
                                 credito_base=args.credito_base, editor=args.editor)
    final = sondar(resultado.saida)
    print(f"\nPronto: {resultado.saida}")
    print(f"  {final.duracao:.1f}s · {final.largura}x{final.altura} · "
          f"{os.path.getsize(resultado.saida) / 1_048_576:.1f} MB · "
          f"{len(resultado.clipes_usados)} clipes de B-roll")
    print(f"  Créditos em {creditos} — cole na descrição antes de publicar.")
    if abs(final.duracao - base.duracao) > 0.5:
        print(f"  Atenção: a duração mudou ({base.duracao:.1f}s → {final.duracao:.1f}s).")
    return 0


def cmd_checar(args) -> int:
    """Checa a licença de um vídeo específico do YouTube antes de cortar."""
    carregar_env()
    chave = os.environ.get("YOUTUBE_API_KEY")
    if not chave:
        print("Defina YOUTUBE_API_KEY para usar o comando checar.")
        return 2

    vid = extrair_id_youtube(args.url)
    dados = get_json("https://www.googleapis.com/youtube/v3/videos", {
        "key": chave, "id": vid,
        "part": "snippet,statistics,contentDetails,status",
    })
    itens = dados.get("items", [])
    if not itens:
        print(f"Vídeo {vid} não encontrado (ou privado/removido).")
        return 1

    from .fontes.youtube_cc import YouTubeCC
    v = YouTubeCC()._converter(itens[0])
    pontuar_lista([v])
    mod_licencas.avaliar(v)
    lic = licenca_de(v)

    print(f"\n{v.titulo}")
    print(f"  canal ......... {v.autor}")
    print(f"  publicado ..... {v.publicado} ({v.idade_dias} dias)")
    print(f"  números ....... {numero_curto(v.views)} views · "
          f"{numero_curto(v.velocidade_dia)}/dia · {v.engajamento * 100:.2f}% engajamento")
    print(f"  duração ....... {duracao_legivel(v.duracao_s)}")
    print(f"  score ......... {v.score:.1f}/100")
    print(f"\n  LICENÇA ....... {lic.nome}")
    print(f"  RISCO ......... {v.risco}")
    print(f"  {lic.observacao}")

    if v.licenca != "cc-by":
        print("\n  >> Licença padrão do YouTube: TODOS OS DIREITOS RESERVADOS.")
        print("     Cortar e repostar sem autorização escrita do autor gera")
        print("     reivindicação de Content ID e pode virar strike. Não use.")
    else:
        print("\n  >> Licença Creative Commons: pode cortar, editar e monetizar,")
        print("     desde que credite o autor. Confira a trilha sonora à parte.")

    if v.alertas:
        print("\n  Alertas:")
        for a in v.alertas:
            print(f"   - {a}")
    print(f"\n  Crédito pronto:\n  {v.credito}\n")
    return 0


# --------------------------------------------------------------------------- #
# parser
# --------------------------------------------------------------------------- #

def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="garimpar",
        description="Garimpa vídeos que bombaram E que a licença permite recortar e repostar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""exemplos:
  python garimpar.py fontes
  python garimpar.py buscar --tema "receita fitness" --dias 30
  python garimpar.py buscar --tema "drone praia" --tema "surf" --fontes pexels,pixabay --limite 40
  python garimpar.py checar --url https://youtu.be/XXXXXXXXXXX
  python garimpar.py baixar --arquivo saida/2026-08-15-surf.json --top 5
  python garimpar.py creditos --arquivo saida/2026-08-15-surf.json --editor "Seu Canal"
  python garimpar.py montar --base corte.mp4 --broll saida/2026-08-15-surf.json \\
                            --modo insercao --intervalo 8 --duracao 2
  python garimpar.py montar --base corte.mp4 --broll saida/2026-08-15-surf.json \\
                            --modo split --vertical
""")
    p.add_argument("--version", action="version", version=f"garimpo-videos {__version__}")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("fontes", help="lista fontes, chaves necessárias e licenças").set_defaults(func=cmd_fontes)

    b = sub.add_parser("buscar", help="garimpa vídeos e gera o relatório")
    b.add_argument("--tema", action="append", required=True, help="assunto (pode repetir)")
    b.add_argument("--fontes", default=",".join(TODAS), help=f"padrão: {','.join(TODAS)}")
    b.add_argument("--dias", type=int, default=30, help="janela de publicação (padrão 30)")
    b.add_argument("--limite", type=int, default=25, help="resultados por fonte/tema (padrão 25)")
    b.add_argument("--min-score", type=float, default=0.0, dest="min_score")
    b.add_argument("--risco-max", choices=NIVEIS, default="MEDIO", dest="risco_max",
                   help="descarta o que estiver acima deste risco (padrão MEDIO)")
    b.add_argument("--dur-min", type=int, default=0, dest="dur_min", help="duração mínima em segundos")
    b.add_argument("--dur-max", type=int, default=0, dest="dur_max", help="duração máxima em segundos")
    b.add_argument("--so-vertical", action="store_true", dest="so_vertical",
                   help="só material vertical, pronto para Shorts/Reels/TikTok")
    b.add_argument("--regiao", default="BR")
    b.add_argument("--idioma", default="pt")
    b.add_argument("--mostrar", type=int, default=20, help="quantos imprimir no terminal")
    b.add_argument("--saida", default="saida", help="pasta dos relatórios (padrão: saida)")
    b.set_defaults(func=cmd_buscar)

    d = sub.add_parser("baixar", help="baixa os arquivos das fontes que permitem download")
    d.add_argument("--arquivo", required=True, help="o .json gerado pelo buscar")
    d.add_argument("--ids", nargs="*", default=[], help="ids específicos; sem isso usa o --top")
    d.add_argument("--top", type=int, default=5)
    d.add_argument("--destino", default="downloads")
    d.add_argument("--editor", default="", help="seu nome/canal, para entrar no crédito")
    d.set_defaults(func=cmd_baixar)

    c = sub.add_parser("creditos", help="imprime os créditos prontos para a descrição")
    c.add_argument("--arquivo", required=True)
    c.add_argument("--ids", nargs="*", default=[])
    c.add_argument("--top", type=int, default=10)
    c.add_argument("--editor", default="")
    c.set_defaults(func=cmd_creditos)

    m = sub.add_parser("montar", help="monta o corte com B-roll licenciado (precisa de ffmpeg)")
    m.add_argument("--base", required=True, help="seu corte já editado")
    m.add_argument("--broll", help="o .json do garimpo — os clipes são baixados sozinhos")
    m.add_argument("--broll-dir", dest="broll_dir", help="ou uma pasta com clipes locais")
    m.add_argument("--modo", choices=["insercao", "split"], default="insercao")
    m.add_argument("--intervalo", type=float, default=8.0,
                   help="segundos de vídeo base entre uma inserção e a próxima")
    m.add_argument("--duracao", type=float, default=2.0, help="duração de cada inserção")
    m.add_argument("--primeiro", type=float, default=None,
                   help="segundo da primeira inserção (padrão: um intervalo, poupando o gancho)")
    m.add_argument("--max-insercoes", type=int, default=40, dest="max_insercoes")
    m.add_argument("--max-clipes", type=int, default=8, dest="max_clipes",
                   help="quantos clipes de B-roll baixar")
    m.add_argument("--proporcao-topo", type=float, default=0.5, dest="proporcao_topo",
                   help="no modo split, fração da altura para o vídeo base")
    m.add_argument("--vertical", action="store_true", help="força saída 1080x1920")
    m.add_argument("--resolucao", help="ex.: 1080x1920 (padrão: a do vídeo base)")
    m.add_argument("--fps", type=float, default=0)
    m.add_argument("--crf", type=int, default=20, help="qualidade: menor = melhor (padrão 20)")
    m.add_argument("--preset", default="medium")
    m.add_argument("--semente", type=int, default=None,
                   help="fixa o sorteio dos clipes, para repetir a mesma montagem")
    m.add_argument("--cache", help="pasta do B-roll baixado (padrão: broll-cache ao lado do json)")
    m.add_argument("--credito-base", default="", dest="credito_base",
                   help="crédito do corte base, para entrar no arquivo de créditos")
    m.add_argument("--editor", default="", help="seu nome/canal")
    m.add_argument("--saida", default="montagem.mp4")
    m.set_defaults(func=cmd_montar)

    k = sub.add_parser("checar", help="checa a licença de um vídeo do YouTube")
    k.add_argument("--url", required=True, help="URL ou id do vídeo")
    k.set_defaults(func=cmd_checar)

    return p


def main(argv: list[str] | None = None) -> int:
    carregar_env()
    args = construir_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrompido.")
        return 130
    except ErroHTTP as e:
        print(f"\nErro de rede/API: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
