"""Cliente HTTP mínimo, só com a biblioteca padrão do Python.

Todas as fontes falam com APIs oficiais e públicas — nada de raspagem de
página nem de burlar bloqueio. Isso é proposital: usar a API oficial é o
que mantém a coleta dentro dos termos de uso de cada plataforma.
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "garimpo-videos/1.0"
TIMEOUT = 30


class ErroHTTP(Exception):
    """Falha de rede ou resposta de erro da API."""

    def __init__(self, mensagem: str, status: int | None = None):
        super().__init__(mensagem)
        self.status = status


def _abrir(url: str, headers: dict | None = None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    # create_default_context respeita SSL_CERT_FILE, o que faz o script
    # funcionar também atrás de proxy corporativo com CA própria.
    return urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context())


def montar_url(base: str, params: dict) -> str:
    limpos = {k: v for k, v in params.items() if v not in (None, "", [])}
    return f"{base}?{urllib.parse.urlencode(limpos, doseq=True)}"


def get_json(base: str, params: dict | None = None, headers: dict | None = None,
             tentativas: int = 3) -> dict:
    """GET que devolve JSON, com retentativa em erro temporário."""
    url = montar_url(base, params or {}) if params else base
    espera = 2
    for tentativa in range(1, tentativas + 1):
        try:
            with _abrir(url, headers) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "replace")[:400]
            # 4xx (chave inválida, cota estourada, parâmetro errado) não melhora
            # com retentativa — falha na hora para o usuário ver o motivo.
            if e.code < 500 and e.code != 429:
                raise ErroHTTP(f"HTTP {e.code} em {base}: {corpo}", e.code) from e
            if tentativa == tentativas:
                raise ErroHTTP(f"HTTP {e.code} em {base}: {corpo}", e.code) from e
        except (urllib.error.URLError, TimeoutError, ssl.SSLError) as e:
            if tentativa == tentativas:
                raise ErroHTTP(f"Falha de rede em {base}: {e}") from e
        time.sleep(espera)
        espera *= 2
    raise ErroHTTP(f"Não consegui falar com {base}")


def baixar_arquivo(url: str, destino: str, progresso=None) -> int:
    """Baixa um arquivo para o disco. Devolve o total de bytes gravados."""
    total = 0
    with _abrir(url) as resp, open(destino, "wb") as saida:
        tamanho = int(resp.headers.get("Content-Length") or 0)
        while True:
            bloco = resp.read(64 * 1024)
            if not bloco:
                break
            saida.write(bloco)
            total += len(bloco)
            if progresso:
                progresso(total, tamanho)
    return total
