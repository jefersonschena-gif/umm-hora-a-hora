"""Internet Archive — acervo em domínio público e Creative Commons.

Não exige chave de API, então é a fonte que funciona de cara.
"""

from __future__ import annotations

import datetime as dt

from ..modelos import Video
from ..util_http import get_json
from .base import Busca, Fonte

BUSCA = "https://archive.org/advancedsearch.php"
METADADOS = "https://archive.org/metadata/"

# Só licenças que permitem cortar e monetizar entram na consulta.
FILTRO_LICENCA = (
    "(licenseurl:*creativecommons.org\\/licenses\\/by\\/* OR "
    "licenseurl:*creativecommons.org\\/licenses\\/by-sa\\/* OR "
    "licenseurl:*creativecommons.org\\/publicdomain\\/zero\\/* OR "
    "licenseurl:*creativecommons.org\\/publicdomain\\/mark\\/*)"
)

EXTENSOES_VIDEO = (".mp4", ".webm", ".mov", ".mkv", ".ogv", ".avi")


def licenca_da_url(url: str) -> str:
    u = (url or "").lower()
    if "publicdomain/zero" in u:
        return "cc0"
    if "publicdomain" in u:
        return "dominio-publico"
    if "/by-nc" in u:
        return "cc-nc"
    if "/by-nd" in u:
        return "cc-nd"
    if "/by-sa" in u:
        return "cc-by-sa"
    if "/by/" in u or u.endswith("/by"):
        return "cc-by"
    return "desconhecida"


class ArchiveOrg(Fonte):
    nome = "archive"
    rotulo = "Internet Archive (domínio público / CC) — sem chave"
    env_chave = ""
    url_chave = ""
    licenca_padrao = "dominio-publico"
    tem_download = True

    def buscar(self, busca: Busca) -> list[Video]:
        consulta = f'({busca.tema}) AND mediatype:(movies) AND {FILTRO_LICENCA}'
        dados = get_json(BUSCA, {
            "q": consulta,
            "fl[]": ["identifier", "title", "creator", "downloads", "licenseurl",
                     "publicdate", "subject", "avg_rating", "num_reviews"],
            "rows": min(100, busca.limite),
            "page": 1,
            "sort[]": "downloads desc",
            "output": "json",
        })
        docs = dados.get("response", {}).get("docs", [])
        videos = [self._converter(d) for d in docs]
        # descarta o que a licença não permite recortar
        return [v for v in videos if v.licenca not in ("desconhecida", "cc-nc", "cc-nd")]

    def _converter(self, doc: dict) -> Video:
        ident = doc.get("identifier", "")
        publicado = None
        if doc.get("publicdate"):
            try:
                publicado = dt.datetime.fromisoformat(
                    doc["publicdate"].replace("Z", "+00:00")
                ).date()
            except ValueError:
                publicado = None

        criador = doc.get("creator")
        if isinstance(criador, list):
            criador = ", ".join(criador)

        assuntos = doc.get("subject") or []
        if isinstance(assuntos, str):
            assuntos = [assuntos]

        return Video(
            fonte=self.nome,
            id=ident,
            titulo=doc.get("title") or ident,
            url=f"https://archive.org/details/{ident}",
            licenca=licenca_da_url(doc.get("licenseurl", "")),
            autor=criador or "Internet Archive",
            autor_url=f"https://archive.org/details/{ident}",
            # `downloads` é o único sinal de popularidade do acervo; entra no
            # lugar de views, e o relatório deixa isso explícito.
            views=int(doc.get("downloads") or 0),
            publicado=publicado,
            thumb=f"https://archive.org/services/img/{ident}",
            tags=[str(s) for s in assuntos][:12],
            extra={
                "metrica_views": "downloads do item",
                "licenseurl": doc.get("licenseurl", ""),
                "metadata_url": f"{METADADOS}{ident}",
            },
        )

    @staticmethod
    def resolver_download(identificador: str) -> str:
        """Descobre o maior arquivo de vídeo do item (usado no comando baixar)."""
        meta = get_json(f"{METADADOS}{identificador}")
        servidor = meta.get("server") or "archive.org"
        diretorio = meta.get("dir", "")
        candidatos = [
            f for f in meta.get("files", [])
            if (f.get("name", "").lower().endswith(EXTENSOES_VIDEO))
        ]
        if not candidatos:
            return ""
        melhor = max(candidatos, key=lambda f: int(f.get("size") or 0))
        return f"https://{servidor}{diretorio}/{melhor['name']}"
