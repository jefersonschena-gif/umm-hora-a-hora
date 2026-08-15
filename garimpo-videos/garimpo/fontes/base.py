"""Contrato que toda fonte precisa cumprir."""

from __future__ import annotations

import os
from dataclasses import dataclass

from ..modelos import Video


@dataclass
class Busca:
    tema: str
    dias: int = 30          # janela de publicação (quando a fonte suporta)
    limite: int = 25        # quantos resultados pedir por fonte
    regiao: str = "BR"
    idioma: str = "pt"


class Fonte:
    nome = "base"
    rotulo = "Fonte base"
    env_chave = ""              # variável de ambiente com a API key, se precisar
    url_chave = ""              # onde obter a chave
    licenca_padrao = "desconhecida"
    tem_download = False        # a fonte entrega URL de arquivo oficialmente?

    def disponivel(self) -> bool:
        return not self.env_chave or bool(os.environ.get(self.env_chave))

    def chave(self) -> str:
        valor = os.environ.get(self.env_chave, "")
        if self.env_chave and not valor:
            raise RuntimeError(
                f"Falta a variável {self.env_chave} para usar a fonte '{self.nome}'. "
                f"Pegue a chave em {self.url_chave}"
            )
        return valor

    def buscar(self, busca: Busca) -> list[Video]:
        raise NotImplementedError
