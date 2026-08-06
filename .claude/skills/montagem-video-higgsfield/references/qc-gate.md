# QC-TRIMODAL — a porta antes da entrega

Duas metades: o que a **máquina mede** e as três **leituras** que só um leitor
faz. As duas são obrigatórias. Nenhuma substitui a outra.

## Parte 1 — medição

O sandbox é descartado poucos segundos depois de cada chamada, e uma instalação
partida em duas chamadas **perde tudo** (medido em 06/08/2026). Por isso o
pacote de QC cabe num comando só, junto com o trabalho:

```bash
python3 scripts/push_scripts.py --pacote qc --append "python3 qc/qc_video.py \
  --video work/output/final.mp4 \
  --sidecar work/output/final.mp4.assembly.json \
  --srt work/output/final.srt \
  --script script_manifest.json \
  --voice-dir work/voices \
  --thumb work/output/thumb.jpg --thumb-text 'TEXTO DA CAPA' \
  --aspect 16:9 --json work/output/qc_report.json"
```

A saída é o `command` de **um** `sandbox_exec`. Se os arquivos já tiverem sido
reciclados, rebaixe-os no mesmo comando (`[ -s arquivo ] || curl -fL ... -o
arquivo`) antes da chamada do QC — nunca em duas chamadas.

Flags úteis: `--sem-whisper` (pula a checagem de fidelidade da narração, mais
rápido), `--rapido` (pula análise de quadros e contagem de cortes),
`--aspect 9:16`.

### O que ele mede

| Eixo | Checagens |
|---|---|
| **IMAGEM** | proveniência (saiu do montador), resolução, proporção, fps, exposição, nitidez, barras pretas, abertura viva, ritmo de corte por bloco |
| **ÁUDIO** | faixa presente, paridade vídeo×áudio, −16 LUFS, pico real, faixa dinâmica, silêncio interno longo |
| **NARRAÇÃO** | fala em todos os blocos, janela por bloco, ritmo em palavras/s, pausas internas, o que foi dito × roteiro (Whisper pt), indício de sotaque |
| **LEGENDA** | sintaxe SRT, sobreposição, duração, velocidade de leitura, formato de linha, fidelidade ao roteiro, cobertura, palavra estranha, sincronia, deriva, sincronia interna, ortografia |
| **TRI-MODAL** | dêixis visual, texto pronto para TTS, proposição visual por bloco, variedade visual, gancho, fechamento, legenda desde o início |
| **THUMBNAIL** | dimensão, proporção, peso, texto (≤5 palavras, ortografia), contraste WCAG, legibilidade a 168 px, contraste global |

Saída: tabela por eixo + `qc_report.json`. **Código de saída 1 = reprovado.**

### Como reagir

- `REPROVADO` → **conserte a entrada que o relatório nomeou** e refaça a etapa:
  reescreva a linha e regenere a tomada; regenere o bloco; recomponha a capa;
  rode de novo o passo de legenda. Nunca contorne o script, nunca edite o
  arquivo final à mão, nunca entregue explicando a falha.
- `AVISO` → decida caso a caso e **diga ao usuário** o que ficou assim.
- `NAO-VERIFICADO` → diga que não foi verificado e por quê. Não conte como
  aprovado.

O lint de legenda fecha a parte mecânica, com o `.srt` em mãos:

```bash
python3 scripts/ptbr_lint.py --mode legenda --srt final.srt
```

## Parte 2 — as três leituras

Escreva o veredito de cada uma, em uma frase. "Passou" sem frase não conta.

### Leitura MUDA (só imagem)
Percorra os blocos pela `visual_proposition` do manifesto e pelos quadros do
vídeo. Pergunta: *um espectador sem som e sem legenda sai sabendo do que se
trata, qual é a virada e como termina?*

Leitor independente, quando disponível — é o mais próximo de um olho de fora:

```
video_analysis_create({ /* o vídeo entregue */ })
```

Compare a descrição que volta com a proposição visual de cada bloco. Bloco cuja
descrição não menciona o conceito **não está afirmando nada na imagem**: refaça o
bloco. (Se a ferramenta não estiver disponível, diga que essa leitura foi feita
só pela proposição declarada.)

### Leitura SILENCIOSA (imagem + legenda)
Leia o `.srt` inteiro, do começo ao fim, como se fosse um texto. Pergunta:
*o argumento fecha? A legenda entra junto com a imagem que ela comenta?*
Sinais de reprovação: legenda que explica o que já se vê e nada mais; legenda
que chega depois do corte a que se refere; texto que só faz sentido com o áudio.

### Leitura CEGA (só áudio)
Leia as `vo_line` em sequência, sem olhar imagem nenhuma. Pergunta: *entende-se
tudo?* Qualquer "isso", "aqui", "assim" que precise da tela é reprovação — e o
lint já pega os casos claros.

## Ficha de qualidade (vai junto com a entrega)

```
IMAGEM      1920x1080, 30 fps, abertura com movimento, sem barras
ÁUDIO       -16,2 LUFS, pico -1,4 dBTP, vídeo 120,04s / áudio 120,03s
NARRAÇÃO    12 blocos, fala 8,7-9,8s, ritmo 2,4-3,0 pal/s, fidelidade 0,97
LEGENDA     .srt presente, fidelidade 0,99, sincronia dentro da fala, 0 erros
TRI-MODAL   muda: OK · silenciosa: OK · cega: OK
THUMBNAIL   1920x1080, 3 palavras, contraste 12,4:1, texto com 11% do quadro
AVISOS      bloco 7 com 3 cortes (ritmo mais lento que o resto)
```

## Autoteste do QC

Para conferir que a medição funciona no sandbox atual, sem gastar crédito de
geração — ele monta um vídeo sintético de 3 blocos, escreve manifesto, sidecar e
`.srt` e roda o QC em cima:

```bash
python3 scripts/push_scripts.py --pacote qc \
  --append "$(cat scripts/selftest_sandbox.sh)"
```

Rode a saída em **um** `sandbox_exec` com `background: true` e depois
`tail -n 120 <log_path>` na chamada seguinte (a montagem passa dos 120 s de
comando em primeiro plano).
