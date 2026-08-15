"""Pixabay Vídeos — licença livre, com views/downloads públicos."""

from __future__ import annotations

from ..modelos import Video
from ..util_http import get_json
from .base import Busca, Fonte

BUSCA = "https://pixabay.com/api/videos/"


class Pixabay(Fonte):
    nome = "pixabay"
    rotulo = "Pixabay (licença livre, download liberado)"
    env_chave = "PIXABAY_API_KEY"
    url_chave = "https://pixabay.com/api/docs/"
    licenca_padrao = "pixabay"
    tem_download = True

    def buscar(self, busca: Busca) -> list[Video]:
        dados = get_json(BUSCA, {
            "key": self.chave(),
            "q": busca.tema,
            "per_page": max(3, min(200, busca.limite)),
            "order": "popular",
            "safesearch": "true",
        })
        return [self._converter(i) for i in dados.get("hits", [])]

    def _converter(self, item: dict) -> Video:
        streams = item.get("videos", {})
        melhor = {}
        for qualidade in ("large", "medium", "small", "tiny"):
            atual = streams.get(qualidade) or {}
            if atual.get("url"):
                melhor = atual
                break

        return Video(
            fonte=self.nome,
            id=str(item.get("id")),
            titulo=(item.get("tags") or f"Clipe Pixabay {item.get('id')}").strip(),
            url=item.get("pageURL", ""),
            licenca="pixabay",
            autor=item.get("user", ""),
            autor_url=f"https://pixabay.com/users/{item.get('user', '')}-{item.get('user_id', '')}/",
            views=int(item.get("views") or 0),
            likes=int(item.get("likes") or 0),
            comentarios=int(item.get("comments") or 0),
            duracao_s=int(item.get("duration") or 0),
            largura=int(melhor.get("width") or 0),
            altura=int(melhor.get("height") or 0),
            thumb=(melhor.get("thumbnail") or ""),
            tags=[t.strip() for t in (item.get("tags") or "").split(",") if t.strip()],
            download_url=melhor.get("url", ""),
            extra={"downloads": int(item.get("downloads") or 0)},
        )
