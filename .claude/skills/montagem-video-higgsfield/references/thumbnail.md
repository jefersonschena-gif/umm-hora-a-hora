# Thumbnail — chama atenção e não erra uma letra

A miniatura é lida em ~0,3 segundo, num retângulo de ~168 px de largura no
celular. Tudo aqui decorre disso.

## A regra que não se negocia

**O fundo é gerado pelo modelo, sem nenhum texto. O texto é composto depois, no
sandbox, com `thumb_text.sh`.**

Modelo de imagem erra letra e acento — e o erro fica na capa do vídeo para
sempre, onde mais gente vê. Composição por ImageMagick escreve exatamente o que
foi digitado, com acento certo, e ainda devolve a caixa do texto para o QC medir
contraste e legibilidade.

## 1. Conceito (antes de gerar)

Carregue `get_workflow_instructions({ workflow: "youtube-thumbnail-generator" })`
e use os enquadramentos de lá. Antes disso, decida três coisas:

- **A tensão em uma imagem.** A capa mostra o *conflito* do vídeo, não o assunto.
  "Relógio parado com a cidade correndo em volta" > "torre de relógio bonita".
- **Um sujeito só**, grande, com emoção legível no rosto (ou, sem gente, um
  objeto único com escala clara). Duas coisas competindo = ninguém entende.
- **A relação com o gancho.** A capa faz a pergunta; os 10 primeiros segundos
  respondem que ela vale a pena. Capa que promete o que o vídeo não entrega
  derruba retenção — e retenção é o que o algoritmo lê.

Composição que funciona a 168 px: sujeito ocupando 40–60% do quadro, fundo com
profundidade mas sem detalhe fino, cor de destaque única e saturada, contraste
alto entre sujeito e fundo, um lado do quadro deliberadamente vazio para o texto.

## 2. Geração do fundo

- 16:9 para vídeo de canal (3840×2160 ou 1920×1080); 9:16 para vertical.
- **Prompt sem nenhuma palavra a ser escrita na imagem** — nada de "com o texto
  X", nem placa, nem cartaz, nem legenda dentro do quadro.
- Rosto consistente com o vídeo, quando houver personagem: use a mesma
  referência de personagem da produção.
- Se sair em 1080p, suba para 4K com `upscale_image` antes de compor o texto.

## 3. Texto

```bash
bash qc/thumb_text.sh --in fundo.jpg --out thumb.jpg \
  --text 'O RELÓGIO\nQUE PAROU' --pos left --color '#FFE100'
```

- **Máximo 5 palavras** (o script recusa mais que isso). Três é melhor.
- O texto **não repete o título** — ele completa. Título e capa juntos contam
  mais do que cada um sozinho.
- Altura do texto ≥ 9% do quadro (a ~10 px na miniatura pequena).
- Contorno preto + sombra: o texto tem que sobreviver a qualquer fundo.
- Margem de segurança de ~5,5% nas bordas; no canto inferior direito não põe
  nada (o selo de duração do YouTube cobre).
- Amarelo/branco sobre fundo escuro é o par mais seguro; o QC exige ≥ 4,5:1.

O script grava `thumb.textbox.json` ao lado da imagem — é ele que permite ao
`qc_video.py` medir contraste e legibilidade. Thumbnail sem esse arquivo entra
como aviso: ou o texto foi gerado pelo modelo (proibido), ou não deu para medir.

## 4. Porta T

| Checagem | Limite |
|---|---|
| dimensão | ≥ 1280×720 (ideal 1920×1080+) |
| proporção | bate com a do vídeo |
| peso | ≤ 2 MB (limite do YouTube) |
| palavras | ≤ 5 |
| ortografia do texto | zero erros no lint `--mode thumb` |
| contraste texto/fundo | ≥ 4,5:1 |
| altura do texto | ≥ 9% do quadro |
| contraste global a 168 px | desvio de luminância ≥ 40 |

Antes de fechar, olhe a capa reduzida a 168 px. Se você não consegue dizer o
assunto nesse tamanho, ela não está pronta — e nenhum ajuste de cor conserta
composição errada.
