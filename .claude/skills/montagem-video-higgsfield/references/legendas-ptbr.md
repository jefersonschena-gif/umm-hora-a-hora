# Legenda — sem erro ortográfico, no tempo exato da fala

## De onde vem cada coisa

Legenda correta é a combinação de duas fontes, e trocar uma pela outra é o que
gera todo defeito conhecido:

| O quê | Vem de | Nunca vem de |
|---|---|---|
| **as palavras** | `script_manifest.json` (o texto autoral) | da transcrição |
| **o tempo** | timestamps de palavra do Whisper, nas tomadas limpas | do roteiro, "estimado" |

Por isso:

- **A transcrição é relógio, não texto.** Se as palavras viessem do Whisper,
  nome próprio, número e acento sairiam do jeito que o modelo achou — e é assim
  que nasce erro ortográfico na tela.
- **Transcreva as tomadas limpas** (`work/voices/voiceNN.wav`), nunca o vídeo
  misturado: música e efeito fazem o STT engolir palavra. Essa é a causa número
  um de "a legenda não bate com o áudio".
- O deslocamento para o tempo do vídeo final sai do sidecar do montador
  (`speech_abs_s`, `lead_silence_s`) — não se calcula à mão.

## Execução

Quem faz é o workflow: `finish_video.sh --subs clean --script script_manifest.json
--language pt` (ou `paper` em conto de fadas). Ele busca fonte, cronometra, queima
e devolve o `.srt` ao lado do `final.mp4`.

**São falhas graves, não atalhos:** escrever `.srt` à mão, cronometrar pelo
roteiro, montar filtro `subtitles=`/`ass=`/`drawtext=` próprio, ou "melhorar" o
visual queimando por cima. Se a legenda saiu errada, o defeito está na entrada
(tomada suja, sidecar errado, manifesto desatualizado) — conserte a entrada e
rode o script de novo.

## Forma (o que deixa legível no celular)

- No máximo 2 linhas, ~42 caracteres por linha.
- Velocidade de leitura ≤ 20 caracteres por segundo.
- Cada legenda entre 0,6 s e 7 s.
- Nenhuma legenda atravessa a fronteira de dois blocos — cada fala vive dentro
  do seu bloco, então a legenda também.
- A primeira legenda entra até 2,5 s do começo (senão o vídeo abre mudo para
  quem assiste sem som).
- Sem placa/caixa atrás do texto por conta própria: o estilo é do workflow.

## O que o QC mede

| Checagem | Reprova quando |
|---|---|
| `FIDELIDADE_ROTEIRO` | similaridade legenda × roteiro < 0,97 |
| `COBERTURA` | palavra falada que não aparece na legenda |
| `PALAVRA_ESTRANHA` | palavra na legenda que não existe no roteiro — é palavra que ninguém revisou, e é onde mora o erro de grafia |
| `SINCRONIA` | legenda fora de qualquer janela de fala medida |
| `DERIVA` | legenda que escapa da fala do bloco ou atravessa dois blocos |
| `SINCRONIA_INTERNA` | legenda mais de 1,0 s adiantada/atrasada dentro do bloco |
| `ORTOGRAFIA` | qualquer `erro` do lint pt-BR |
| `ALEM_DO_FIM` | legenda que termina depois do vídeo |

O lint de legenda roda com o `.srt` em mãos:

```bash
python3 scripts/ptbr_lint.py --mode legenda --srt final.srt
```

Ele pega acento perdido, erro ortográfico conhecido, espaço duplo, pontuação
solta e palavra repetida. **Ele não é um dicionário completo** — a garantia
principal de grafia é o texto vir do roteiro (`FIDELIDADE_ROTEIRO` +
`PALAVRA_ESTRANHA`), e o roteiro já ter passado pela porta R.

## Quando o Whisper não estiver disponível

Entregue o vídeo **sem legenda** e diga isso em uma linha. Legenda com tempo
chutado é pior que legenda nenhuma: sai da boca do narrador e destrói a leitura
silenciosa. Falta de legenda não é falha da produção — legenda inventada é.
