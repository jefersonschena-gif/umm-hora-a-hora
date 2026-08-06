---
name: montagem-video-higgsfield
description: Monta vídeos narrados de ponta a ponta no Higgsfield com qualidade máxima de imagem, áudio, narração (pt-BR natural, sem voz robótica nem sotaque), legenda (sem erro ortográfico e no tempo exato da fala), thumbnail que chama atenção e roteiro com contexto forte — e só entrega depois de passar num teste de qualidade que mede cada um desses pontos. Use quando pedirem para criar, montar, produzir ou melhorar um vídeo (YouTube, Shorts, Reels, TikTok, explicativo, história, documentário, infantil, canal faceless), gerar narração ou legendas para um vídeo, fazer thumbnail/capa de vídeo, ou revisar a qualidade de um vídeo já montado. Também para "vídeo sobre X", "roteiro de vídeo", "canal automático", "vídeo com IA".
---

# Montagem de vídeo com qualidade máxima (Higgsfield)

Esta skill produz **um arquivo de vídeo pronto**, com um padrão de qualidade
verificado por medição, não por opinião. Ela não substitui o motor de produção do
Higgsfield: ela **dirige** esse motor e coloca portas de qualidade antes e depois
de cada etapa cara.

## O contrato tri-modal (a razão de existir desta skill)

Todo vídeo produzido aqui tem que passar em três leituras independentes:

| Leitura | O espectador tem | Tem que entender |
|---|---|---|
| **MUDO** | só a imagem | o assunto, a virada e o desfecho |
| **SILENCIOSO** | imagem + legenda | o argumento inteiro |
| **CEGO** | só o áudio | o argumento inteiro, sem depender de nada na tela |

Consequências que valem como regra dura, não como conselho:

- **A narração nunca aponta para a imagem.** Nada de "como você pode ver", "aqui
  em cima", "nesta imagem", "à direita". A coisa é *nomeada*, nunca apontada.
  (`qc_video.py` reprova por `AUDIO_AUTONOMO`.)
- **Cada bloco declara o que a imagem afirma sozinha** — o campo
  `visual_proposition` no manifesto do roteiro. Se a imagem só ilustra a fala em
  vez de afirmar alguma coisa, o bloco está errado.
- **A legenda é a fala, palavra por palavra** — nunca um resumo, nunca uma
  reescrita.

## Motor: o workflow do Higgsfield, sem improviso

A produção (estilo, elenco de assets, clipes, voz, montagem, queima de legenda,
upscale, entrega) é do workflow **`faceless-channel-video`**. Antes de qualquer
geração:

```
get_workflow_instructions({ workflow: "faceless-channel-video" })
```

e siga as Fases 0→9 dele à risca. Para a thumbnail:

```
get_workflow_instructions({ workflow: "youtube-thumbnail-generator" })
```

**Quando as duas fontes divergirem, o workflow manda na mecânica** (quais
modelos, como montar, como cronometrar legenda, como entregar) e **esta skill
manda no padrão de qualidade** (o que precisa ser medido e o que reprova).
Onde esta skill é mais exigente, ela é mais exigente — nunca mais permissiva.

Nunca escrever ffmpeg de montagem/legenda à mão; nunca cronometrar legenda à
mão; nunca entregar sem o `.srt` e o sidecar `final.mp4.assembly.json`.

## Fluxo

### 1. Intake
Faça só as perguntas do workflow (tipo de canal, modo, estilo, duração,
proporção, legenda, tema, voz). **Não invente perguntas.** Três decisões desta
skill entram sem virar rodada extra:

- **Idioma da narração = idioma do usuário** (aqui, pt-BR) — sem perguntar.
- **Thumbnail entra por padrão** em vídeo 16:9 de canal; em Shorts/Reels
  vertical, capa 9:16. Só não faz se o usuário disser que não quer.
- **O teste de qualidade é obrigatório** e não é oferecido como opção.

### 2. Roteiro tri-modal — PORTA R
Escreva o roteiro seguindo `references/roteiro-trimodal.md` e grave
`script_manifest.json` com os campos extras desta skill
(`visual_proposition`, `key_visual`). Rode o lint **localmente, antes de gerar
qualquer coisa**:

```bash
python3 .claude/skills/montagem-video-higgsfield/scripts/ptbr_lint.py \
  --mode narracao --script script_manifest.json
```

`erro` = corrija e rode de novo. Só passe adiante com zero erros.
Isso é o que evita gastar crédito em cima de roteiro que já nasceu torto:
número em algarismo, símbolo, abreviatura, sigla, dêixis visual, frase longa
demais para o TTS respirar, acento perdido.

### 3. Voz — PORTA V
`references/narracao-ptbr.md` tem o procedimento completo. O essencial:

1. Abra o seletor de vozes (`list_voices`) — o usuário ouve as prévias e escolhe.
   Recomende 2–3 vozes e diga que a escolha vale para o vídeo inteiro.
2. **Gere só o bloco 01 primeiro.** Ele é a prova de pronúncia: transcreva a
   tomada com Whisper em `pt` e compare com a linha escrita. Similaridade
   `< 0.90` = a voz não fala português direito → volte ao seletor com outra voz
   (nunca "conserte" com `speech_rate` nem com pós-processamento).
3. Só depois gere os blocos 02..N, com o mesmo par `voice_id` + `voice_type`.
4. Sem sotaque de verdade, o caminho é voz clonada de um falante nativo
   (`create_voice`) — ofereça quando o usuário reclamar do sotaque das vozes
   prontas.

### 4. Produção e montagem
Fases 1→7 do workflow, sem desvio. Legenda: `--subs clean` (ou `paper` em conto
de fadas), sempre com `--script script_manifest.json` e `--language pt`.

### 5. Thumbnail — PORTA T
`references/thumbnail.md`. Regra que não se negocia: **o texto da thumbnail é
composto no sandbox com `thumb_text.sh`, nunca gerado pelo modelo de imagem** —
modelo de imagem erra letra e acento, e o erro fica na capa do vídeo para
sempre. A imagem de fundo é gerada em 4K sem nenhum texto.

### 6. QC-TRIMODAL — PORTA Q (a última antes de entregar)
`references/qc-gate.md` tem o procedimento e a tabela de limites.

O sandbox é descartado entre chamadas, então **instalação e execução vão no
MESMO comando**. Gere o comando aqui:

```bash
python3 .claude/skills/montagem-video-higgsfield/scripts/push_scripts.py \
  --pacote qc --append "python3 qc/qc_video.py --video work/output/final.mp4 \
  --sidecar work/output/final.mp4.assembly.json --srt work/output/final.srt \
  --script script_manifest.json --voice-dir work/voices \
  --thumb work/output/thumb.jpg --thumb-text 'TEXTO DA CAPA' \
  --aspect 16:9 --json work/output/qc_report.json; cat work/output/final.srt"
```

e passe a saída como `command` de **um** `sandbox_exec`. Se o comando passar de
16 000 caracteres, tire o `cat` e busque o `.srt` depois.

Depois, com o `.srt` em mãos, o lint de legenda roda local:

```bash
python3 .claude/skills/montagem-video-higgsfield/scripts/ptbr_lint.py \
  --mode legenda --srt final.srt
```

**Qualquer `REPROVADO` bloqueia a entrega.** Conserte a *entrada* que o
relatório apontou (reescreva a linha, regenere o bloco, regenere a tomada,
recomponha a capa) e rode a etapa de novo — nunca contorne o script, nunca
"ajuste" o arquivo final à mão.

Além do que a máquina mede, faça as **três leituras** de `references/qc-gate.md`
(mudo / silencioso / cego) e escreva o veredito de cada uma. Quando disponível,
use `video_analysis_create` no vídeo entregue como leitor independente da camada
visual: se a descrição que volta não contém o assunto do bloco, a imagem não
está afirmando nada.

### 7. Entrega
Entregue o link confirmado + a **ficha de qualidade**: veredito das três
leituras, e do relatório do QC as linhas de imagem, áudio, narração, legenda e
thumbnail. Diga em uma linha o que ficou como `AVISO` e o que não deu para
verificar. Nunca apresente arquivo parcial nem remendado como resultado.

## Limites que reprovam

| Eixo | Medida | Limite |
|---|---|---|
| Imagem | resolução | ≥ 1920×1080 (ou 1080×1920) |
| Imagem | primeiro segundo | tem movimento |
| Imagem | barras pretas | nenhuma |
| Áudio | vídeo × áudio | Δ ≤ 0,25 s |
| Áudio | loudness | −16 LUFS ± 1,5 |
| Áudio | pico real | ≤ −1,0 dBTP |
| Narração | fala por bloco | dentro da janela do montador |
| Narração | o que foi dito × roteiro | similaridade ≥ 0,90 |
| Narração | ritmo | 2,0–3,2 palavras/s |
| Legenda | texto × roteiro | similaridade ≥ 0,97 |
| Legenda | palavra fora do roteiro | nenhuma |
| Legenda | posição na fala | dentro da janela, ±1,0 s do previsto |
| Legenda | ortografia | zero erros no lint |
| Tri-modal | dêixis visual na narração | nenhuma |
| Tri-modal | `visual_proposition` | em todos os blocos |
| Thumbnail | texto | ≤ 5 palavras, composto no sandbox |
| Thumbnail | contraste texto/fundo | ≥ 4,5:1 |
| Thumbnail | altura do texto | ≥ 9% do quadro |

## Arquivos

- `references/roteiro-trimodal.md` — como escrever o roteiro e o manifesto
- `references/narracao-ptbr.md` — voz, pronúncia pt-BR, texto que o TTS lê bem
- `references/legendas-ptbr.md` — o que garante legenda certa e no tempo
- `references/thumbnail.md` — capa que chama atenção sem erro de escrita
- `references/qc-gate.md` — a porta de qualidade, limites e as três leituras
- `scripts/ptbr_lint.py` — lint pt-BR (roda local e no sandbox)
- `scripts/qc_video.py` — medição do vídeo final (roda no sandbox)
- `scripts/thumb_text.sh` — texto da thumbnail por composição
- `scripts/push_scripts.py` — empacota os scripts num único comando de sandbox
- `scripts/selftest_sandbox.sh` — autoteste do QC com vídeo sintético

## Nunca

- Entregar com qualquer `REPROVADO` em aberto, ou "explicar" a falha em vez de
  corrigi-la.
- Escrever `.srt` à mão, cronometrar legenda pelo roteiro, ou queimar legenda
  com ffmpeg próprio.
- Acelerar/desacelerar áudio (`atempo`), cortar silêncio dentro da tomada, ou
  encurtar o vídeo para caber num áudio curto — reescreva a linha e regenere.
- Deixar o modelo de imagem escrever texto na thumbnail ou nos quadros.
- Expor mecânica ao usuário: nome de modelo, nome de fase, id de job, caminho de
  sandbox, URL pré-assinada.
