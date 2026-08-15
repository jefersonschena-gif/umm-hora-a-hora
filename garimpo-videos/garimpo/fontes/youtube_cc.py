"""YouTube Data API v3, filtrando apenas vídeos com licença Creative Commons.

O parâmetro `videoLicense=creativeCommon` é o coração da fonte: ele faz a
busca ignorar todo o catálogo de licença padrão, que é justamente o que não
pode ser recortado e repostado.
"""

from __future__ import annotations

import datetime as dt
import re

from ..modelos import Video
from ..util_http import get_json
from .base import Busca, Fonte

BUSCA = "https://www.googleapis.com/youtube/v3/search"
VIDEOS = "https://www.googleapis.com/youtube/v3/videos"

_DURACAO = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def iso_para_segundos(iso: str) -> int:
    m = _DURACAO.fullmatch(iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


class YouTubeCC(Fonte):
    nome = "youtube_cc"
    rotulo = "YouTube (somente Creative Commons)"
    env_chave = "YOUTUBE_API_KEY"
    url_chave = "https://console.cloud.google.com/apis/library/youtube.googleapis.com"
    licenca_padrao = "cc-by"
    tem_download = False  # baixar do YouTube fere os Termos de Uso; só a URL sai daqui

    def buscar(self, busca: Busca) -> list[Video]:
        publicado_apos = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=busca.dias)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        ids: list[str] = []
        token = None
        while len(ids) < busca.limite:
            pagina = get_json(BUSCA, {
                "key": self.chave(),
                "part": "id",
                "type": "video",
                "q": busca.tema,
                "videoLicense": "creativeCommon",   # <- o filtro que evita a dor de cabeça
                "order": "viewCount",
                "publishedAfter": publicado_apos,
                "regionCode": busca.regiao,
                "relevanceLanguage": busca.idioma,
                "maxResults": min(50, busca.limite - len(ids)),
                "pageToken": token,
            })
            novos = [i["id"]["videoId"] for i in pagina.get("items", []) if i.get("id", {}).get("videoId")]
            ids.extend(novos)
            token = pagina.get("nextPageToken")
            if not token or not novos:
                break

        return self._detalhar(ids[:busca.limite])

    def _detalhar(self, ids: list[str]) -> list[Video]:
        videos: list[Video] = []
        for i in range(0, len(ids), 50):
            lote = ids[i:i + 50]
            dados = get_json(VIDEOS, {
                "key": self.chave(),
                "part": "snippet,statistics,contentDetails,status",
                "id": ",".join(lote),
            })
            for item in dados.get("items", []):
                videos.append(self._converter(item))
        # Segunda checagem: a API de busca já filtra, mas confirmamos no detalhe
        # para nunca deixar passar um vídeo de licença padrão.
        return [v for v in videos if v.licenca == "cc-by"]

    def _converter(self, item: dict) -> Video:
        snip = item.get("snippet", {})
        stats = item.get("statistics", {})
        det = item.get("contentDetails", {})
        status = item.get("status", {})
        vid = item["id"]

        publicado = None
        if snip.get("publishedAt"):
            publicado = dt.datetime.fromisoformat(
                snip["publishedAt"].replace("Z", "+00:00")
            ).date()

        thumbs = snip.get("thumbnails", {})
        thumb = (thumbs.get("medium") or thumbs.get("default") or {}).get("url", "")

        return Video(
            fonte=self.nome,
            id=vid,
            titulo=snip.get("title", "(sem título)"),
            url=f"https://www.youtube.com/watch?v={vid}",
            licenca="cc-by" if status.get("license") == "creativeCommon" else "desconhecida",
            autor=snip.get("channelTitle", ""),
            autor_url=f"https://www.youtube.com/channel/{snip.get('channelId', '')}",
            views=int(stats.get("viewCount", 0) or 0),
            likes=int(stats.get("likeCount", 0) or 0),
            comentarios=int(stats.get("commentCount", 0) or 0),
            publicado=publicado,
            duracao_s=iso_para_segundos(det.get("duration", "")),
            thumb=thumb,
            tags=snip.get("tags", [])[:12],
            extra={
                "licensed_content": bool(det.get("licensedContent")),
                "embeddable": status.get("embeddable"),
                "definicao": det.get("definition"),
                "canal_id": snip.get("channelId"),
            },
        )
