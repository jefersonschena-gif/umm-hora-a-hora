# Roteiro tri-modal — contexto forte, três camadas

O roteiro é o único lugar onde as três leituras (mudo / silencioso / cego) podem
ser garantidas. Depois que os clipes existem, corrigir custa crédito.

## 1. Antes de escrever: a promessa

Escreva em uma frase, para você mesmo, três coisas. Se não couber em uma frase
cada, o tema ainda não está pronto:

- **PROMESSA** — o que o espectador leva embora.
- **TENSÃO** — a pergunta que segura ele até o fim.
- **PROVA** — o fato, a cena ou o número concreto que fecha a promessa.

Vídeo sem tensão vira lista de curiosidades: o espectador sai no bloco 3.

## 2. Arco por duração

| Duração | Blocos (10 s) | Arco |
|---|---|---|
| 30 s | 3 | gancho → virada → fecho |
| 60 s | 6 | gancho → contexto → conflito → virada → prova → fecho |
| 2 min | 12 | gancho → 2 de contexto → 3 de conflito → virada → 3 de prova → 2 de fecho |
| 5 min+ | 30+ | abertura fria → capítulos de 3–4 blocos, cada um com sua micro-virada |

**Os primeiros 10 segundos** carregam: uma afirmação concreta que o espectador
não esperava, e a pergunta que ela abre. Sem "neste vídeo você vai aprender",
sem apresentação, sem aquecimento.

**O último bloco** fecha a tensão do gancho. Se ele pudesse ser trocado pelo
bloco de qualquer outro vídeo, o roteiro não tem fecho — tem parada.

## 3. A linha de cada bloco

Uma linha de narração por bloco de 10 s:

- **27–32 palavras densas** (infantil: 24–28). Densidade é conteúdo: um
  qualificador por coisa, um concreto novo por linha, zero enchimento.
- Uma ideia por bloco. Duas ideias numa linha = o espectador perde as duas.
- Frase de no máximo ~28 palavras, com vírgula onde o narrador respira.
- Números por extenso, símbolos por extenso, siglas grafadas como se fala
  (`references/narracao-ptbr.md`).
- **Zero dêixis visual.** "Como você vê", "aqui", "acima", "nesta imagem" são
  reprovação automática: quebram a leitura cega.

## 4. A camada visual: `visual_proposition`

Para cada bloco, escreva o que a **imagem afirma sozinha**, sem a narração.
Teste: mostre a proposição a alguém que não ouviu nada — ela diz algo, ou é só
decoração?

| Ruim (ilustra) | Bom (afirma) |
|---|---|
| "cidade bonita ao entardecer" | "o relógio da torre parado às 3h07 enquanto a cidade se move ao redor" |
| "pessoa pensando" | "a relojoeira olha a engrenagem quebrada na palma da mão e fecha os olhos" |
| "gráfico subindo" | "a pilha de cartas não entregues cresce até tapar a janela" |

Regras da camada visual:

- **Nada de texto gerado dentro do quadro.** Modelo de imagem erra letra e
  acento. Palavra na tela é papel da legenda.
- **Cada bloco mostra coisa nova.** Repetir o enquadramento do bloco anterior é
  aviso no QC (`VARIEDADE_VISUAL`); repetir a proposição é erro de roteiro.
- **Movimento desde o primeiro quadro** de cada bloco — nada de imagem que
  "começa a andar" um segundo depois.
- Máximo ~20 s (2 blocos) no mesmo cenário/distância; depois troque cenário,
  ângulo ou escala.

## 4b. O rótulo de tela: o que salva a leitura muda

Metáfora não carrega fato. Quem assiste sem som entende *"é sobre dinheiro,
prazo e proteção"* e sai sem saber o número que importa. Então cada bloco declara
um `screen_label`: o fato daquele bloco, em até seis palavras, que aparece na
tela.

- **Composto, nunca gerado.** `scripts/screen_labels.sh` renderiza o texto com a
  fonte da casa e sobrepõe no clipe. Modelo de imagem erra letra; composição não.
- **No clipe, antes da montagem.** Nunca no `final.mp4` — assim o montador e o
  passo de legenda continuam intocados.
- **Terço superior.** A legenda ocupa os doze por cento de baixo. Nunca colidem.
- **Progride.** Rótulo que repete o do bloco anterior trava a leitura muda e é
  reprovação.
- **Sigla vive aqui.** O que o TTS soletraria errado ("LCI", "FGC", "CDB") tem
  lugar na tela, não na fala.

O teste é ler os rótulos em sequência, sem áudio e sem legenda:

> IMPOSTO ZERO → CRÉDITO IMOBILIÁRIO → CRÉDITO DO AGRONEGÓCIO → POR QUE O GOVERNO
> ISENTA → CDB: 22,5% A 15% DE IR → 90% ISENTO VENCE 100% TRIBUTADO → COMPARE
> SEMPRE O LÍQUIDO → CARÊNCIA MÍNIMA: 6 MESES → SAIR ANTES CUSTA DESÁGIO → QUEM
> DEVE É O BANCO → FGC: R$ 250 MIL POR CPF → PRAZO + TAXA LÍQUIDA + BANCO

Se essa sequência sozinha não conta o vídeo, a camada muda não está pronta.

## 5. `script_manifest.json`

O manifesto é lido pelo montador, pelo passo de legenda e pelo QC. O nome dos
campos `blocks[].vo_line` (ou `beats[].phrase`) é fixo — os scripts do workflow
dependem dele. Os campos desta skill entram junto:

```json
{
  "blocks": [
    {
      "n": 1,
      "vo_line": "Existe um relógio parado no centro da cidade, e ninguém lembra quem cuidava dele.",
      "visual_proposition": "o relógio da torre parado às três e sete enquanto a rua se move embaixo",
      "key_visual": "torre do relógio, ponteiros congelados",
      "screen_label": "O RELÓGIO PAROU"
    }
  ],
  "sources": ["https://..."]
}
```

- `visual_proposition` — obrigatório em todos os blocos (o QC reprova se faltar).
- `screen_label` — obrigatório, até seis palavras, sem repetir o bloco anterior.
- `key_visual` — a imagem que resume o bloco; vira insumo de thumbnail.
- `sources` — obrigatório em vídeo factual (explicativo, história). Pesquisa
  serve ao **tema**, nunca vai colada para dentro da narração.

**Se uma linha for reescrita para caber na janela de fala, atualize o manifesto.**
A legenda é gerada a partir dele: manifesto desatualizado = legenda diferente do
que foi dito, e o QC reprova por `FIDELIDADE_ROTEIRO`.

## 6. Porta R (antes de gerar qualquer coisa)

```bash
python3 scripts/ptbr_lint.py --mode narracao --script script_manifest.json
```

Zero `erro`. Avisos: leia um a um e decida — muleta e clichê quase sempre valem
o corte, porque é exatamente o que faz um roteiro soar genérico.
