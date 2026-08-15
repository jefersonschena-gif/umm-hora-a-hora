"""Registro de fontes. Para adicionar uma nova, herde de Fonte e registre aqui."""

from .archive_org import ArchiveOrg
from .base import Busca, Fonte
from .pexels import Pexels
from .pixabay import Pixabay
from .youtube_cc import YouTubeCC

REGISTRO: dict[str, Fonte] = {
    f.nome: f for f in (YouTubeCC(), Pixabay(), Pexels(), ArchiveOrg())
}

TODAS = list(REGISTRO)

__all__ = ["REGISTRO", "TODAS", "Busca", "Fonte",
           "YouTubeCC", "Pexels", "Pixabay", "ArchiveOrg"]
