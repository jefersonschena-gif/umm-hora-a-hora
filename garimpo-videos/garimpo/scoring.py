"""Cálculo do 'quanto bombou'.

O score é comparável entre fontes porque cada componente é normalizado para
0..1 antes de entrar na média ponderada.
"""

from __future__ import annotations

import math

from .modelos import Video

PESOS = {
    "velocidade": 0.45,   # views por dia — o que de fato indica viral
    "engajamento": 0.25,  # (likes + comentários) / views
    "recencia": 0.15,     # assunto ainda quente rende mais no corte
    "formato": 0.15,      # duração e proporção aproveitáveis para corte
}

TETO_VELOCIDADE = 500_000   # views/dia que valem nota 1.0
TETO_ENGAJAMENTO = 0.08     # 8% de engajamento já é excelente
MEIA_VIDA_DIAS = 45         # a nota de recência cai pela metade a cada 45 dias


def _log_norm(valor: float, teto: float) -> float:
    if valor <= 0:
        return 0.0
    return min(math.log10(1 + valor) / math.log10(1 + teto), 1.0)


def _nota_formato(v: Video) -> float:
    """Material bom de cortar: nem curto demais, nem novela."""
    d = v.duracao_s
    # A faixa ideal para de 0.9, não em 1.0, para sobrar espaço ao bônus de
    # vertical logo abaixo — senão material já pronto para Shorts empataria
    # com material horizontal.
    if not d:
        nota = 0.5  # fonte não informou duração; não premia nem pune
    elif d < 10:
        nota = 0.2
    elif d < 45:
        nota = 0.7
    elif d <= 15 * 60:
        nota = 0.9          # faixa ideal: dá para tirar vários cortes
    elif d <= 40 * 60:
        nota = 0.62
    else:
        nota = 0.4
    if v.vertical:
        nota = min(nota + 0.1, 1.0)   # já nasce pronto para Shorts/Reels
    if v.altura and v.altura < 720:
        nota *= 0.7                   # baixa resolução estraga o corte
    return nota


def _nota_recencia(v: Video) -> float:
    idade = v.idade_dias
    if idade is None:
        return 0.5
    return 0.5 ** (idade / MEIA_VIDA_DIAS)


def pontuar(v: Video) -> Video:
    idade = v.idade_dias
    # Sem data de publicação (caso de banco de mídia), assume 30 dias para não
    # inflar artificialmente a velocidade.
    dias = max(idade or 30, 1)
    v.velocidade_dia = v.views / dias
    v.engajamento = ((v.likes + v.comentarios) / v.views) if v.views else 0.0

    if v.extra.get("sem_metricas"):
        # Fonte que não publica número de views (Pexels). Em vez de fingir
        # velocidade zero — o que jogaria todo o banco de mídia para o fim da
        # lista — usa a posição no ranking da própria API como proxy e
        # redistribui os pesos entre os componentes que dá para medir.
        total = max(int(v.extra.get("rank_total") or 1), 1)
        proxy = 1.0 - (int(v.extra.get("rank") or 0) / total)
        componentes = {"velocidade": proxy, "engajamento": proxy,
                       "recencia": _nota_recencia(v), "formato": _nota_formato(v)}
    else:
        componentes = {
            "velocidade": _log_norm(v.velocidade_dia, TETO_VELOCIDADE),
            "engajamento": min(v.engajamento / TETO_ENGAJAMENTO, 1.0),
            "recencia": _nota_recencia(v),
            "formato": _nota_formato(v),
        }

    v.score = round(100 * sum(PESOS[k] * n for k, n in componentes.items()), 1)
    v.extra["componentes"] = {k: round(n, 3) for k, n in componentes.items()}
    return v


def pontuar_lista(videos: list[Video]) -> list[Video]:
    return [pontuar(v) for v in videos]
