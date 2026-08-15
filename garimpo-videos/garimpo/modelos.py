"""Estrutura única que todas as fontes preenchem."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field, asdict


@dataclass
class Video:
    # ---- identificação ----
    fonte: str                      # "youtube_cc", "pexels", "pixabay", "archive"
    id: str
    titulo: str
    url: str                        # página oficial do vídeo
    licenca: str                    # chave em licencas.LICENCAS

    # ---- autoria (necessária para o crédito) ----
    autor: str = ""
    autor_url: str = ""

    # ---- métricas de bombou ----
    views: int = 0
    likes: int = 0
    comentarios: int = 0
    publicado: dt.date | None = None

    # ---- características do material ----
    duracao_s: int = 0
    largura: int = 0
    altura: int = 0
    thumb: str = ""
    tags: list[str] = field(default_factory=list)
    download_url: str = ""          # só quando a fonte oferece download oficial

    # ---- preenchido pelo scoring/licenças ----
    score: float = 0.0
    velocidade_dia: float = 0.0
    engajamento: float = 0.0
    risco: str = "DESCONHECIDO"     # BAIXO | MEDIO | ALTO
    alertas: list[str] = field(default_factory=list)
    credito: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def idade_dias(self) -> int | None:
        if not self.publicado:
            return None
        return max((dt.date.today() - self.publicado).days, 0)

    @property
    def vertical(self) -> bool:
        return bool(self.altura and self.largura and self.altura > self.largura)

    def como_dict(self) -> dict:
        d = asdict(self)
        d["publicado"] = self.publicado.isoformat() if self.publicado else None
        d["idade_dias"] = self.idade_dias
        return d

    @staticmethod
    def de_dict(d: dict) -> "Video":
        d = dict(d)
        d.pop("idade_dias", None)
        d.pop("vertical", None)
        if d.get("publicado"):
            d["publicado"] = dt.date.fromisoformat(d["publicado"])
        campos = {f for f in Video.__dataclass_fields__}
        return Video(**{k: v for k, v in d.items() if k in campos})


def duracao_legivel(segundos: int) -> str:
    if not segundos:
        return "—"
    h, resto = divmod(int(segundos), 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def numero_curto(n: int | float) -> str:
    n = float(n or 0)
    for limite, sufixo in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if n >= limite:
            valor = n / limite
            return f"{valor:.1f}".rstrip("0").rstrip(".") + sufixo
    return str(int(n))
