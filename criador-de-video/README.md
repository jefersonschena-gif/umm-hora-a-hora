# UMM Studio — criador de vídeos fintech

Cria vídeos verticais **faceless** com estética **fintech premium clara**, texto
grande em português e cenas concretas. Roda inteiro no navegador: nenhum
servidor, nenhuma conta, nenhuma assinatura, nenhum arquivo enviado para lugar
nenhum.

**Direção de arte:** vidro, metal escovado e luz de estúdio, com **verde e
dourado** como únicos acentos. O projeto escolhe um **clima** e cada cena pode
mergulhar no escuro.

| Clima | Como é | Quando usar |
|---|---|---|
| **Claro** | branco quente, luz alta, sombra nítida | conteúdo de organização, controle, investimento |
| **Grafite** | campo de carvão quente, painel de vidro, cartão em aço escovado como objeto iluminado | quando você quer peso e produto — é o meio-termo entre claro e escuro |
| **Escuro** | quase preto, clima de alerta | vídeo inteiro sobre dívida ou golpe |

Independente do clima, uma cena pode ter **tom escuro**: ela mergulha para o
quase preto e volta. É a pontuação da dívida, do juro e do vencimento — o
verificador reclama se passar de um terço do vídeo.

![formato](https://img.shields.io/badge/9%3A16-1080x1920-0B7A4B) ![custo](https://img.shields.io/badge/custo-R%24%200-0B7A4B)

---

## O padrão, e como ele é cobrado

O que o Studio produz obedece a seis regras. Elas não são texto de manual: um
verificador as checa a cada tecla e mostra a nota na lateral direita.

| Regra | Como o Studio cobra |
|---|---|
| **O vídeo se entende sem áudio** | Toda cena precisa de texto grande. O verificador mede a fonte depois do ajuste automático e reclama abaixo de ~73 px em 1080. O painel "teste do mudo" lista só o que aparece escrito, na ordem — se essa lista já conta a história, o vídeo funciona no silencioso. |
| **O áudio se entende sem vídeo** | A narração não pode apontar para a imagem. "na tela", "acima", "ao lado", "isso aqui" viram **erro**; "veja", "repare", "olha só" viram aviso. Se a cena mostra um número que a narração não fala, avisa. O painel "teste do cego" junta só a narração, para você ler de olhos fechados. |
| **Estética fintech premium** | Três climas fechados (claro, grafite, escuro), um acento por cena (dourado para dado, verde para ação, vermelho só para alerta). Mais de uma cena vermelha vira aviso. |
| **Faceless** | Nenhum visual tem gente. A biblioteca é de objetos: cartão, extrato, boleto, celular, cofre, gráfico. A narração que pressupõe alguém na câmera é sinalizada. |
| **Texto grande em português** | Título com mais de 9 palavras vira aviso, porque obriga a fonte a encolher. Estrangeirismo evitável também. |
| **Cenas concretas** | Cada cena escolhe um visual desenhado (ou uma mídia sua). Passar de uma cena "só tipografia" vira aviso, e o visual de mídia sem arquivo também. |
| **O escuro é pontuação** | Passando de um terço das cenas em mergulho escuro, vira aviso — aí é caso de trocar o clima do projeto, não de escurecer cena a cena. |

Nota 100 quer dizer: nenhum erro, nenhum aviso.

---

## Como abrir

```sh
# a partir da raiz do repositório
python3 -m http.server 8000
# depois abra http://localhost:8000/criador-de-video/
```

Abrir o `index.html` com duplo clique também funciona para escrever, pré-visualizar
e exportar. Só a narração do Piper precisa de `http://` — o navegador não deixa
guardar o modelo de voz numa página aberta como arquivo local.

Também funciona publicado no GitHub Pages, sem nenhuma adaptação.

**Navegador:** Chrome, Edge ou Opera para a exportação exata (WebCodecs).
Firefox e Safari funcionam com o botão "Gravar".

---

## Fluxo de trabalho

1. **Escolha um modelo** no alto da tela. Vêm quatro roteiros prontos em pt-BR,
   todos com nota 100 — servem de régua para o que você escrever depois.
2. **Escolha o clima** no alto da tela e o **tom** de cada cena: tom do projeto
   por padrão, escuro nas cenas de dívida, juros e vencimento.
3. **Escreva cena a cena.** Cada cena tem duas colunas de conteúdo:
   *texto grande na tela* (o que se lê) e *narração* (o que se ouve). Escreva
   como se cada um fosse o único canal.
4. **Escolha a cena concreta** e preencha os dados. O botão *usar exemplo*
   preenche o formato certo.
5. **Olhe a nota.** Clique num aviso para pular direto para a cena.
6. **Gere a narração** (opcional) na aba Voz.
7. **Exporte** na aba Exportar.

A duração de cada cena é calculada da narração (2,55 palavras por segundo) ou
da duração real do áudio, quando houver. Dá para travar no campo *duração*.

---

## Narração: as rotas gratuitas

| Rota | Custo | Precisa de internet? | Qualidade | Entra no arquivo? |
|---|---|---|---|---|
| **Piper no navegador** (`@diffusionstudio/vits-web`, modelos Rhasspy, MIT) | R$ 0 | só no primeiro uso (~60 MB) | boa, um pouco robótica | sim |
| **Edge TTS** via `ferramentas/tts-edge.mjs` | R$ 0 | sim | muito boa, neural | sim, subindo os arquivos |
| **Sua própria voz** (celular, Audacity) | R$ 0 | não | a melhor | sim, subindo os arquivos |
| **Voz do sistema** (`speechSynthesis`) | R$ 0 | não | varia | **não** — serve só para conferir o ritmo |
| **Sem narração** | R$ 0 | não | — | vídeo mudo com legenda gravada |

A voz do sistema não entra no arquivo porque o navegador não expõe esse áudio
para captura. O Studio deixa isso explícito na interface em vez de gerar um
vídeo mudo sem avisar.

Para a rota Edge:

```sh
# 1. salve o projeto no Studio (aba Exportar → "Projeto (.json)")
node ferramentas/tts-edge.mjs meu-video.json --voz pt-BR-FranciscaNeural
node ferramentas/tts-edge.mjs --vozes          # lista as vozes em português
# 2. no Studio: aba Voz → "Subir meus áudios por cena" → botão "áudio…" em cada cena
```

---

## Exportação

| Botão | O que sai | Quando usar |
|---|---|---|
| **Exportar exato** | `.webm` VP9 + Opus, quadro a quadro | padrão. Mais rápido que o tempo real, sem engasgo, qualidade alta. Chrome/Edge/Opera. |
| **Gravar em tempo real** | `.mp4` ou `.webm`, conforme o navegador | quando não há WebCodecs. Leva o tempo do vídeo e a aba precisa ficar visível. |
| **Quadros PNG (.zip)** | um PNG por quadro + `montar.sh` | qualidade máxima, para montar com ffmpeg. |
| **Legendas (.srt)** | legenda sincronizada | acessibilidade e upload nas plataformas. |
| **Roteiro (.md)** | tela e narração lado a lado | revisão, aprovação, gravar com a própria voz. |
| **Projeto (.json)** | o projeto inteiro | versionar, compartilhar, alimentar o `tts-edge.mjs`. |

O empacotador WebM está em `js/webm.js`, escrito neste repositório: a exportação
exata não depende de CDN nem de instalação e funciona offline.

O YouTube aceita WebM direto. Para Instagram e TikTok, converta:

```sh
./ferramentas/montar-mp4.sh video.webm
# ou, na mão:
ffmpeg -i video.webm -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac video.mp4
```

---

## Cenas concretas disponíveis

`numero` · `linha` · `barras` · `comparativo` · `cartao` · `pix` · `boleto` ·
`extrato` · `notificacao` · `checklist` · `juros` · `cofre` · `alerta` ·
`fluxo` · `calendario` · `contrato` · `carteira` · `moedas` · `citacao` ·
`chamada` · `midia`

Todas menos `midia` são desenhadas em código — nada de banco de imagens, nada
de licença, nada de crédito a dar. Os dados vêm de um campo de texto simples:

```
valor: R$ 1.240,00
rotulo: em tarifas esquecidas
itens: Poupança=6,2 | CDB=11,4 | Tesouro=10,9
```

`itens` aceita `rótulo=valor` separados por `|`, ou só valores.

---

## Mídia própria: usar filmagem gerada fora do Studio

As cenas desenhadas em código não viram foto. Quando você quiser produto
fotorrealista — cartão em macro, vidro, metal, dashboard renderizado — gere a
filmagem onde preferir e traga para dentro:

1. Na cena, clique em **imagem ou vídeo…** e escolha o arquivo (PNG, JPG, WEBP,
   MP4, WEBM — qualquer coisa que o seu navegador toque).
2. A cena passa para o visual **Mídia própria**: o arquivo vira o palco, dentro
   da moldura, com sombra de contato e fio de luz na borda.
3. Marque **usar a mídia no quadro inteiro** para ela ocupar todo o quadro. Aí
   ela entra desfocada e sob véu, e o texto grande continua sendo o que se lê.

O texto grande, a legenda sincronizada e o verificador continuam funcionando por
cima — é o que garante que o vídeo siga se entendendo no mudo. Na exportação
exata, cada quadro é buscado no vídeo antes de ser codificado, então o resultado
fica sincronizado mesmo em máquina lenta.

Os arquivos ficam só na memória da aba: não são enviados a lugar nenhum e não
entram no `.json` do projeto. Ao reabrir um projeto, recarregue as mídias.

## Formatos

`9:16` (1080×1920) · `4:5` (1080×1350) · `1:1` (1080×1080) · `16:9` (1920×1080)

Cada um pode sair em **2K** (1440×2560 no vertical), na aba Exportar.

A opção **área segura** encolhe o conteúdo para a faixa que o Instagram não
cobre com a própria interface. Marque "guias" na prévia para enxergar os
limites.

---

## Arquivos

```
criador-de-video/
  index.html      interface
  estilo.css      a interface usa a mesma linguagem visual do vídeo
  js/base.js      tokens do tema, utilidades, primitivas de canvas
  js/visuais.js   biblioteca de cenas concretas
  js/motor.js     layout, composição do quadro, legendas, SRT, roteiro
  js/padrao.js    o verificador das seis regras
  js/voz.js       Piper, upload de áudio, prévia pelo sistema, WAV
  js/webm.js      empacotador WebM (VP9 + Opus) próprio, sem dependências
  js/exportar.js  WebCodecs, MediaRecorder, quadros PNG, zip
  js/modelos.js   três roteiros prontos
  js/app.js       amarração de tudo
ferramentas/
  tts-edge.mjs    narração neural gratuita via Edge (Node 22+)
  montar-mp4.sh   conversão final com ffmpeg
```

Sem build, sem `npm install`, sem dependência em tempo de execução.
