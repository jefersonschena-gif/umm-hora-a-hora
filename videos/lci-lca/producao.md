# Vídeo LCI e LCA — pacote de produção

Tudo o que não depende de aprovação já está resolvido aqui. Quando as chamadas de
geração liberarem, é só executar na ordem.

**Travado no intake:** explicativo · 16:9 · 2 min (12 blocos de 10 s) · Editorial
Motion Graphics (`56fc6472-33b7-45dc-83ff-80c71d40aec6`) · legenda `clean` em
`pt` · voz Cillian `d8ba9f14-8a24-44db-932b-99e16c45bd32` / `preset` (sujeita à
prova de pronúncia no bloco 1) · tom educativo neutro.

**Porta R:** aprovada — 0 erros, 0 avisos, densidade 27–32 nos doze blocos,
`visual_proposition` e `screen_label` em 12/12.

---

## 1. Chave de estilo (Fase 1)

```
resolve_explainer_preset({ preset_id: "56fc6472-33b7-45dc-83ff-80c71d40aec6" })
```

O `media_id` que volta é a referência de estilo de **todas** as gerações. Depois,
uma imagem de chave de estilo com `seedream_v5_pro`:

> Editorial motion-graphics style key for a financial explainer: cut-paper and
> halftone collage, muted paper texture, one saturated accent colour, clean
> off-white background, geometric shapes and simple icons, no lettering
> anywhere, no logos, flat editorial illustration, 16:9.

## 2. Elenco de assets (Fase 2, `seedream_v5_pro`, 12 itens)

Objetos recorrentes, todos sobre o mesmo fundo off-white do estilo, **sem
nenhuma palavra no quadro**: pote de moedas · escudo translúcido · prédio em
construção · esteira de moedas · lavoura com trator · balança do estado · casa
pequena · prato de comida · disco de lucro fatiado · ampulheta · duas colunas de
moedas · etiqueta de vitrine · cofre com cadeado · calendário · folha de título ·
prédio do banco com contrato · guarda-chuva · três engrenagens.

## 3. Clipes (Fase 4, `gemini_omni`, 12 itens, `aspect_ratio: "16:9"`)

Cada prompt = **um bloco de 10 s com cinco cortes duros de ~2 s**, variando
tamanho e ângulo a cada corte, movimento desde o primeiro quadro, nenhum texto no
quadro, nenhuma pessoa falando.

| # | Prompt (cinco cortes) |
|---|---|
| 1 | WIDE pote de moedas cheio girando · MEDIUM nota de imposto descendo em direção ao pote · CU a nota bate num escudo translúcido e curva · MACRO as moedas continuam intactas, nenhuma sai · ALTO o escudo brilha e a nota desliza para fora do quadro |
| 2 | ALTO moedas entram por uma calha na base de uma obra · MEDIUM as moedas viram tijolos empilhando · WIDE o prédio sobe andar por andar · CU um fio dourado sai da obra e volta pela calha · BAIXO o prédio completo com o fio pulsando |
| 3 | WIDE a esteira de moedas se bifurca antes do prédio · MEDIUM o ramo novo desce até terra lavrada · MACRO uma semente cai e brota em segundos · LATERAL a lavoura preenche o campo · ALTO um trator arranca e começa a colher |
| 4 | MEDIUM uma balança com casa num prato e prato de comida no outro · CU um carimbo desce e retira um bloco de peso · WIDE os dois pratos sobem juntos · MACRO o bloco removido se dissolve · ALTO a balança estabilizada mais leve |
| 5 | WIDE um disco de lucro girando inteiro · MEDIUM uma lâmina corta uma fatia · CU a fatia é levada para fora do quadro · LATERAL uma ampulheta ao lado começa a esvaziar · MACRO a fatia cortada encolhe conforme a areia desce |
| 6 | WIDE duas colunas de moedas lado a lado, a da esquerda mais alta · MEDIUM um bloco se solta do topo da coluna alta · CU o bloco cai fora · ALTO agora a coluna baixa está mais alta que a outra · MACRO o topo das duas comparado |
| 7 | MEDIUM uma etiqueta enorme pendurada numa vitrine · CU uma mão ergue a etiqueta · MACRO atrás dela há outra etiqueta bem menor · WIDE a etiqueta menor é a que segue para a sacola · LATERAL a etiqueta grande cai vazia |
| 8 | MEDIUM a porta de um cofre se fechando · CU o cadeado engata · LATERAL um calendário ao lado vira seis folhas sozinho · MACRO a chave pendurada longe, balançando · WIDE o cofre fechado com o calendário parado |
| 9 | MEDIUM uma folha de título passando de uma mão para outra · CU um pedaço da folha se desprende no meio do caminho · MACRO o pedaço caindo e pousando · ALTO a folha chega menor do lado oposto · WIDE as duas mãos afastando-se |
| 10 | WIDE prédio do banco em primeiro plano segurando um contrato · MEDIUM o contrato aberto com carimbo · ALTO ao fundo um imóvel e uma lavoura pequenos e desfocados · MACRO o selo do contrato · BAIXO o prédio ocupando o quadro inteiro |
| 11 | WIDE um guarda-chuva aberto sobre pilhas de moedas · MEDIUM chuva batendo na cúpula · CU a linha onde a proteção termina · MACRO moedas acima da linha recebendo chuva · ALTO a divisão entre protegido e exposto |
| 12 | MACRO três engrenagens de tamanhos diferentes se aproximando · MEDIUM os dentes se encaixam · WIDE as três giram juntas · CU um ponteiro começa a subir numa escala · ALTO o ponteiro trava no alto e as engrenagens seguem girando |

**Ladeira de retentativa:** `nsfw`/`failed` → reenviar o mesmo prompt com semente
nova (2×) → reescrever removendo tokens de risco → mudar o enquadramento.
Nunca deixar bloco vazio.

## 4. Narração (Fase 5) — PORTA V primeiro

1. `generate_audio_batch` com **apenas o índice 1**, `model: "seed_audio"`,
   `voice_id: "d8ba9f14-8a24-44db-932b-99e16c45bd32"`, `voice_type: "preset"`.
2. Medir e transcrever antes de gastar o resto:

```
bash $HF_WORKFLOWS/faceless-channel-video/scripts/narrator/speech_metrics.sh \
  --text '<linha 1 exata>' work/voices/voice01.wav
python3 $HF_WORKFLOWS/faceless-channel-video/scripts/verify_takes.py \
  --script script_manifest.json --voice-dir work/voices
```

Similaridade < 0,90 = a voz não fala português direito → trocar de voz, nunca
ajustar velocidade. Só então gerar os blocos 2–12 com o mesmo par.

## 5. Rótulos de tela (esta skill) — antes de montar

Um comando só, com o pacote junto:

```bash
python3 .claude/skills/montagem-video-higgsfield/scripts/push_scripts.py \
  --pacote labels --append "<baixar clipes> && for i in 01..12; do \
  bash qc/screen_labels.sh --in work/blocks/block\$i.mp4 \
  --out work/blocks/block\${i}_lab.mp4 --text \"\$ROTULO\"; done"
```

Rótulos, na ordem: IMPOSTO ZERO · CRÉDITO IMOBILIÁRIO · CRÉDITO DO AGRONEGÓCIO ·
POR QUE O GOVERNO ISENTA · CDB: 22,5% A 15% DE IR · 90% ISENTO VENCE 100%
TRIBUTADO · COMPARE SEMPRE O LÍQUIDO · CARÊNCIA MÍNIMA: 6 MESES · SAIR ANTES
CUSTA DESÁGIO · QUEM DEVE É O BANCO · FGC: R$ 250 MIL POR CPF · PRAZO + TAXA
LÍQUIDA + BANCO

## 6. Montagem + legenda (Fases 6+7)

```
bash $HF_WORKFLOWS/faceless-channel-video/scripts/finish_video.sh \
  --blocks 12 --clips-file clips.txt --voices-file voices.txt \
  --script script_manifest.json --subs clean --language pt
```

Os `clips.txt` apontam para os `*_lab.mp4`. Depois, upscale Topaz 1080p.

## 7. Capa (Porta T)

Fundo 4K sem nenhuma palavra, e o texto composto:

```bash
bash qc/thumb_text.sh --in fundo.jpg --out thumb.jpg \
  --text 'LCI E LCA\nSEM IMPOSTO' --pos left --color '#FFE100'
```

## 8. QC (Porta Q) — um comando só

```bash
python3 .claude/skills/montagem-video-higgsfield/scripts/push_scripts.py \
  --pacote qc --append "python3 qc/qc_video.py --video work/output/final.mp4 \
  --sidecar work/output/final.mp4.assembly.json --srt work/output/final.srt \
  --script script_manifest.json --voice-dir work/voices \
  --thumb work/output/thumb.jpg --thumb-text 'LCI E LCA SEM IMPOSTO' \
  --labels-dir work/blocks --aspect 16:9 --json work/output/qc_report.json"
```

Qualquer `REPROVADO` bloqueia a entrega. Depois, o lint da legenda local e as
três leituras (muda pelos rótulos, silenciosa pelo `.srt`, cega pelas `vo_line`).

---

## Checagem factual (feita em 06/08/2026)

- Isenção de IR para pessoa física **segue valendo em 2026** — a MP 1.303/2025
  caducou.
- Carência mínima: **6 meses** para papéis não corrigidos por índice de preços
  (o CMN reduziu de 9/12 meses em maio de 2025); **12 meses** quando corrigidos
  por índice de preços.
- FGC: R$ 250 mil por CPF e por instituição, teto de R$ 1 milhão a cada 4 anos.

Fontes no `script_manifest.json`. **Se este vídeo for produzido meses depois,
reconfira os prazos antes de gerar** — foi exatamente aqui que os blogs se
contradisseram.
