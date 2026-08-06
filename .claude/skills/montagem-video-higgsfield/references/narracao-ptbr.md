# Narração pt-BR — natural, sem voz robótica e sem sotaque

Três coisas fazem uma narração soar de máquina, e só uma delas é a voz:

1. **o texto** — número em algarismo, símbolo, sigla, abreviatura, frase
   comprida sem vírgula: o TTS lê tudo isso errado ou sem ar;
2. **a voz** — timbre que não fala português nativo devolve sotaque;
3. **o pós-processamento** — acelerar, cortar silêncio, mudar tom: é isso que
   deixa a narração picotada.

Esta skill fecha as três.

## 1. Texto que o TTS lê como gente

Reprovado pelo lint (`--mode narracao`), sem exceção:

| Escreva assim | Não escreva |
|---|---|
| mil novecentos e noventa | 1990 |
| trinta e sete por cento | 37% |
| dois milhões de reais | R$ 2 milhões |
| doutor Silva | Dr. Silva |
| e assim por diante | etc. |
| oitenta quilômetros por hora | 80 km/h |
| a Onu decidiu | a ONU decidiu |
| primeiro de janeiro | 01/01 |

Mais:

- **Vírgula é respiração.** Linha longa sem vírgula sai numa lengalenga só.
- **Frase de até ~28 palavras.** Depois disso a prosódia do modelo desmonta.
- Nada de parênteses, colchetes, markdown, emoji ou CAIXA ALTA no texto falado.
- Nada de dêixis visual (`references/roteiro-trimodal.md`) — quebra a leitura
  cega e é reprovação no QC.
- Palavra estrangeira: escreva como se pronuncia em português quando o modelo
  tropeça (`design` costuma sair bem; `queue`, `sync`, `cache` não).

## 2. Escolha da voz — o usuário ouve, não você

- Abra o **seletor de vozes** (`list_voices`) numa chamada só. Ele já traz
  prévias tocáveis; o usuário ouve e escolhe. **Nunca substitua o seletor por
  uma lista de nomes**, e nunca gere amostras de áudio para "testar voz" — isso
  queima crédito à toa.
- Ao lado, recomende 2–3 vozes em texto simples, dizendo o tom de cada uma.
- A escolha volta com `voice_id` + `voice_type`. **Grave o par num arquivo e
  releia dele antes de cada geração de áudio** — voz resolvida por nome no meio
  da produção é a causa clássica de timbre diferente em cada bloco.
- Uma voz para o vídeo inteiro. Sem exceção.

## 3. Porta V — a prova de pronúncia (custa um bloco)

As vozes prontas não trazem idioma declarado, então a pronúncia é **medida**, não
suposta:

1. Gere **só o bloco 01** com a voz escolhida.
2. Transcreva a tomada com Whisper em `pt` e compare com a linha escrita:

```
python3 $HF_WORKFLOWS/faceless-channel-video/scripts/verify_takes.py \
  --script script_manifest.json --voice-dir work/voices
```

3. Leitura do resultado:

| Similaridade | O que significa | O que fazer |
|---|---|---|
| ≥ 0,95 | pronúncia limpa | siga para os blocos 02..N |
| 0,90–0,95 | sotaque ou fonema arrastado | ouça com o usuário antes de seguir |
| < 0,90 | a voz não fala português direito | volte ao seletor e troque a voz |

4. **Nunca "conserte" pronúncia** com `speech_rate`, com equalização ou com
   corte de silêncio. Os únicos ajustes legítimos são: outra voz, ou outras
   palavras.

**Sotaque zero de verdade** só vem de voz nativa clonada: peça 30–60 s de áudio
limpo de um falante brasileiro e crie a voz (`create_voice`). Ofereça esse
caminho sempre que o usuário reclamar do sotaque das vozes prontas — é a única
solução real, e vale dizer isso com todas as letras em vez de prometer que a
próxima voz da lista resolve.

## 4. Janela, ritmo e pausa

- Uma linha por bloco, com a fala dentro da janela que o montador exige
  (tipicamente 8,6–10,0 s num bloco de 10 s).
- **Ritmo entre 2,0 e 3,2 palavras por segundo.** Acima disso soa afobado;
  abaixo, arrastado.
- Nenhuma pausa interna ≥ 0,8 s dentro de uma tomada.
- Meça sempre com o script do workflow:

```
bash $HF_WORKFLOWS/faceless-channel-video/scripts/narrator/speech_metrics.sh \
  --text 'a linha exatamente como falada' work/voices/voice01.wav
```

- Fora da janela ou `RUSHED`: **reescreva a linha** (±1 a 2 palavras já muda o
  resultado; desmembrar lista de vírgulas numa frase corrida também) e regenere
  só aquela linha. Nunca `atempo`, nunca corte de borda, nunca silêncio inserido.
- Tomada aprovada é imutável: retentativa é só para as linhas reprovadas.

## 5. Mistura

- Voz sempre em primeiro plano; trilha ~14 dB abaixo da fala e com abaixamento
  automático sob a voz.
- Mistura final normalizada em −16 LUFS, pico real ≤ −1,0 dBTP (o QC mede).
- Nada de efeito na voz: sem reverb, sem "rádio", sem compressão extra.
