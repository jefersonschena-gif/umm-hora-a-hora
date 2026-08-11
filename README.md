# umm-hora-a-hora

Duas ferramentas independentes, ambas estáticas: abre no navegador e pronto.

## Hora a Hora

`index.html` — acompanhamento de produção hora a hora por célula e turno.

## UMM Studio — criador de vídeos

[`criador-de-video/`](criador-de-video/) — cria vídeos verticais faceless com
estética fintech premium clara, texto grande em português e cenas concretas.

O padrão é verificado enquanto você escreve: o vídeo precisa se entender sem
áudio, e o áudio precisa se entender sem vídeo. Narração e exportação são
gratuitas e rodam no próprio navegador.

```sh
python3 -m http.server 8000
# http://localhost:8000/criador-de-video/
```

Detalhes em [`criador-de-video/README.md`](criador-de-video/README.md).
