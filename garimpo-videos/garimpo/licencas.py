"""Licenças, nível de risco e texto de crédito.

Regra que orienta o programa inteiro: só entra no resultado material com
licença que **permite obra derivada e uso comercial**. Vídeo comum do
YouTube (licença padrão) nunca entra — recortar e repostar aquilo é o
caminho curto para strike de Content ID e para uma notificação de direito
autoral.
"""

from __future__ import annotations

from dataclasses import dataclass

from .modelos import Video

NIVEIS = ["BAIXO", "MEDIO", "ALTO"]


@dataclass(frozen=True)
class Licenca:
    codigo: str
    nome: str
    url: str
    exige_credito: bool
    permite_comercial: bool
    permite_derivados: bool
    risco_base: str
    observacao: str


LICENCAS: dict[str, Licenca] = {
    "cc-by": Licenca(
        "cc-by", "Creative Commons Atribuição (CC BY)",
        "https://creativecommons.org/licenses/by/4.0/",
        exige_credito=True, permite_comercial=True, permite_derivados=True,
        risco_base="MEDIO",
        observacao=(
            "Permite corte e repostagem comercial com crédito. Porém o CC-BY cobre "
            "só o que o autor tinha direito de licenciar: trilha sonora, clipes de TV "
            "e logos que apareçam no vídeo continuam de terceiros."
        ),
    ),
    "cc0": Licenca(
        "cc0", "Creative Commons Zero (domínio público voluntário)",
        "https://creativecommons.org/publicdomain/zero/1.0/",
        exige_credito=False, permite_comercial=True, permite_derivados=True,
        risco_base="BAIXO",
        observacao="Uso livre, sem exigência de crédito. Creditar mesmo assim é boa prática.",
    ),
    "dominio-publico": Licenca(
        "dominio-publico", "Domínio público",
        "https://creativecommons.org/publicdomain/mark/1.0/",
        exige_credito=False, permite_comercial=True, permite_derivados=True,
        risco_base="BAIXO",
        observacao="Sem titular de direito patrimonial. Cuidado com restaurações e trilhas novas, que podem ter direito próprio.",
    ),
    "pexels": Licenca(
        "pexels", "Licença Pexels",
        "https://www.pexels.com/license/",
        exige_credito=False, permite_comercial=True, permite_derivados=True,
        risco_base="BAIXO",
        observacao=(
            "Uso comercial livre, sem crédito obrigatório. Proibido revender o arquivo "
            "sem alteração e usar pessoas identificáveis de forma ofensiva ou como endosso."
        ),
    ),
    "pixabay": Licenca(
        "pixabay", "Licença de Conteúdo Pixabay",
        "https://pixabay.com/service/license-summary/",
        exige_credito=False, permite_comercial=True, permite_derivados=True,
        risco_base="BAIXO",
        observacao=(
            "Uso comercial livre, sem crédito obrigatório. Proibido redistribuir o arquivo "
            "original em plataforma de banco de mídia concorrente."
        ),
    ),
    "cc-by-sa": Licenca(
        "cc-by-sa", "Creative Commons Atribuição-CompartilhaIgual",
        "https://creativecommons.org/licenses/by-sa/4.0/",
        exige_credito=True, permite_comercial=True, permite_derivados=True,
        risco_base="MEDIO",
        observacao="Exige crédito E que o seu corte também saia sob CC BY-SA. Isso costuma conflitar com monetização exclusiva.",
    ),
    "cc-nc": Licenca(
        "cc-nc", "Creative Commons Não Comercial",
        "https://creativecommons.org/licenses/by-nc/4.0/",
        exige_credito=True, permite_comercial=False, permite_derivados=True,
        risco_base="ALTO",
        observacao="Proíbe uso comercial. Canal monetizado costuma ser considerado uso comercial — evite.",
    ),
    "cc-nd": Licenca(
        "cc-nd", "Creative Commons Sem Derivações",
        "https://creativecommons.org/licenses/by-nd/4.0/",
        exige_credito=True, permite_comercial=True, permite_derivados=False,
        risco_base="ALTO",
        observacao="Proíbe obra derivada. Cortar é justamente criar derivada — não serve.",
    ),
    "desconhecida": Licenca(
        "desconhecida", "Licença não declarada",
        "", exige_credito=True, permite_comercial=False, permite_derivados=False,
        risco_base="ALTO",
        observacao="Sem licença declarada, o padrão legal é 'todos os direitos reservados'.",
    ),
}


def licenca_de(video: Video) -> Licenca:
    return LICENCAS.get(video.licenca, LICENCAS["desconhecida"])


def _pior(a: str, b: str) -> str:
    return a if NIVEIS.index(a) >= NIVEIS.index(b) else b


def avaliar(video: Video) -> Video:
    """Define video.risco e video.alertas, e monta o texto de crédito."""
    lic = licenca_de(video)
    risco = lic.risco_base
    alertas: list[str] = []

    if not lic.permite_derivados:
        risco = "ALTO"
        alertas.append("A licença proíbe obra derivada — corte não é permitido.")
    if not lic.permite_comercial:
        risco = "ALTO"
        alertas.append("A licença proíbe uso comercial — não use em canal monetizado.")

    # O YouTube marca licensedContent quando o material está reivindicado por um
    # parceiro de conteúdo. Mesmo com a caixinha de CC marcada pelo uploader, o
    # Content ID vai bater. É o alerta mais importante da ferramenta.
    if video.extra.get("licensed_content"):
        risco = "ALTO"
        alertas.append(
            "O YouTube marca este vídeo como conteúdo reivindicado por parceiro "
            "(licensedContent). Content ID deve reclamar mesmo estando como CC."
        )

    if video.fonte == "youtube_cc":
        alertas.append(
            "CC-BY do YouTube cobre a imagem do autor, não a trilha sonora. "
            "Confira a música antes de publicar e, na dúvida, troque por áudio livre."
        )
        if video.extra.get("embeddable") is False:
            risco = _pior(risco, "MEDIO")
            alertas.append("O autor bloqueou incorporação — sinal de que não quer redistribuição.")

    if video.fonte in ("pexels", "pixabay"):
        alertas.append(
            "Pessoas identificáveis: não use o corte para sugerir endosso, nem em "
            "contexto sensível (saúde, política, adulto). Não há model release para isso."
        )

    if video.fonte == "archive":
        alertas.append(
            "Acervo enviado por usuários: confirme a licença na própria página do item "
            "antes de publicar — o campo de licença nem sempre reflete a obra toda."
        )

    if not video.autor and lic.exige_credito:
        risco = _pior(risco, "MEDIO")
        alertas.append("Sem autor identificado e a licença exige crédito.")

    video.risco = risco
    video.alertas = alertas
    video.credito = texto_credito(video)
    return video


def texto_credito(video: Video, editor: str = "") -> str:
    """Linha de crédito pronta para colar na descrição do corte."""
    lic = licenca_de(video)
    if not lic.exige_credito:
        base = f'"{video.titulo}"'
        if video.autor:
            base += f" por {video.autor}"
        base += f" — {lic.nome} ({video.url})"
    else:
        autor = video.autor or "autor não identificado"
        base = f'"{video.titulo}" por {autor}'
        if video.autor_url:
            base += f" ({video.autor_url})"
        base += f", licenciado sob {lic.nome} — {lic.url}. Fonte: {video.url}."
    if editor:
        base += f" Corte e edição: {editor}."
    else:
        base += " Trecho recortado do original."
    return base


def resumo_licencas() -> str:
    linhas = []
    for lic in LICENCAS.values():
        marcas = []
        marcas.append("derivada OK" if lic.permite_derivados else "derivada PROIBIDA")
        marcas.append("comercial OK" if lic.permite_comercial else "comercial PROIBIDO")
        marcas.append("crédito obrigatório" if lic.exige_credito else "crédito opcional")
        linhas.append(f"  {lic.codigo:<16} {lic.nome}\n      {' · '.join(marcas)} · risco base {lic.risco_base}\n      {lic.observacao}")
    return "\n".join(linhas)
