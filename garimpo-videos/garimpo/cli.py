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
        fonte = REGISTRO.get(v.fonte)
        if not fonte or not fonte.tem_download:
            # Caso do YouTube: mesmo com licença CC, baixar o arquivo pelo
            # navegador/ripper fere os Termos de Uso da plataforma. A licença
            # do vídeo e o contrato de uso do site são coisas separadas.
            print(f"[bloqueado] {v.titulo[:60]}")
            print(f"            {v.fonte} não oferece download oficial. Use o material "
                  f"pelo editor do próprio YouTube ou peça o arquivo ao autor: {v.url}")
            bloqueados += 1
            continue

        url = v.download_url
        if not url and v.fonte == "archive":
            try:
                url = ArchiveOrg.resolver_download(v.id)
            except ErroHTTP as e:
                print(f"[erro] {v.id}: {e}")
                falhas += 1
                continue
        if not url:
            print(f"[sem arquivo] {v.titulo[:60]}")
            falhas += 1
            continue

        extensao = os.path.splitext(url.split("?")[0])[1] or ".mp4"
        destino = os.path.join(pasta, f"{v.fonte}-{nome_arquivo_seguro(v.titulo)}-{v.id}{extensao}")
        print(f"[baixando] {os.path.basename(destino)}")
        try:
            total = baixar_arquivo(url, destino)
        except ErroHTTP as e:
            print(f"[erro] {e}")
            falhas += 1
            continue
        print(f"           {total / 1_048_576:.1f} MB")

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
