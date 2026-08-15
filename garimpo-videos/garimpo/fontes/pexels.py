"""Pexels Vídeos — licença livre para uso comercial, com download oficial."""

from __future__ import annotations

from ..modelos import Video
from ..util_http import get_json
from .base import Busca, Fonte

BUSCA = "https://api.pexels.com/videos/search"


class Pexels(Fonte):
    nome = "pexels"
    rotulo = "Pexels (licença livre, download liberado)"
    env_chave = "PEXELS_API_KEY"
    url_chave = "https://www.pexels.com/api/"
    licenca_padrao = "pexels"
    tem_download = True

    def buscar(self, busca: Busca) -> list[Video]:
        dados = get_json(
            BUSCA,
            {"query": busca.tema, "per_page": min(80, busca.limite), "page": 1},
            headers={"Authorization": self.chave()},
        )
        itens = dados.get("videos", [])
        return [self._converter(item, pos, len(itens)) for pos, item in enumerate(itens)]

    def _converter(self, item: dict, pos: int, total: int) -> Video:
        arquivos = sorted(
            (f for f in item.get("video_files", []) if f.get("link")),
            key=lambda f: (f.get("width") or 0) * (f.get("height") or 0),
            reverse=True,
        )
        melhor = arquivos[0] if arquivos else {}
        usuario = item.get("user", {})
        return Video(
            fonte=self.nome,
            id=str(item.get("id")),
            titulo=(item.get("alt") or f"Clipe Pexels {item.get('id')}").strip(),
            url=item.get("url", ""),
            licenca="pexels",
            autor=usuario.get("name", ""),
            autor_url=usuario.get("url", ""),
            duracao_s=int(item.get("duration") or 0),
            largura=int(melhor.get("width") or item.get("width") or 0),
            altura=int(melhor.get("height") or item.get("height") or 0),
            thumb=item.get("image", ""),
            download_url=melhor.get("link", ""),
            extra={
                "sem_metricas": True,     # Pexels não publica views
                "rank": pos,
                "rank_total": max(total, 1),
                "qualidade": melhor.get("quality"),
            },
        )
