# Garimpo de vídeos — bombados **e** livres de direitos

Ferramenta de linha de comando que procura vídeos com muita audiência **cuja
licença permite recortar, editar, monetizar e repostar**. Ela devolve o
material já com nota de "quanto bombou", nível de risco jurídico e o texto de
crédito pronto para colar na descrição.

A regra central: **material de licença padrão nunca entra no resultado.** É
justamente esse material que gera reivindicação de Content ID e strike de
direito autoral. Pegar vídeo viral qualquer, cortar e repostar é o caminho
curto para o canal ser derrubado — a ferramenta foi feita para você não
precisar aprender isso na prática.

---

## Instalação

Não tem dependência nenhuma. Só Python 3.9 ou mais novo.

```bash
cd garimpo-videos
python3 garimpar.py fontes
```

### Chaves de API (todas gratuitas, nenhuma obrigatória)

```bash
cp exemplo.env .env   # e preencha o que quiser usar
```

| Fonte | Chave | Onde pegar |
|---|---|---|
| `archive` | nenhuma | funciona de cara |
| `youtube_cc` | `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com) — 10.000 unidades/dia grátis |
| `pexels` | `PEXELS_API_KEY` | [pexels.com/api](https://www.pexels.com/api/) |
| `pixabay` | `PIXABAY_API_KEY` | [pixabay.com/api/docs](https://pixabay.com/api/docs/) |

---

## Uso

### Garimpar

```bash
python3 garimpar.py buscar --tema "receita fitness" --dias 30
python3 garimpar.py buscar --tema "drone praia" --tema "surf" \
        --fontes pexels,pixabay --limite 40 --so-vertical
python3 garimpar.py buscar --tema "história do brasil" \
        --fontes archive,youtube_cc --risco-max BAIXO --min-score 40
```

Sai um `.html` (painel com filtros e botão de copiar crédito), um `.csv` para
abrir no Excel e um `.json` que alimenta os outros comandos.

Opções úteis:

| Opção | O que faz |
|---|---|
| `--tema` | assunto; pode repetir para várias buscas na mesma rodada |
| `--fontes` | quais fontes usar (padrão: todas) |
| `--dias` | janela de publicação (padrão 30) |
| `--limite` | resultados por fonte/tema |
| `--risco-max` | descarta acima do nível: `BAIXO`, `MEDIO` ou `ALTO` (padrão `MEDIO`) |
| `--min-score` | corta o que pontuou pouco |
| `--so-vertical` | só material já pronto para Shorts/Reels/TikTok |
| `--dur-min` / `--dur-max` | faixa de duração em segundos |

### Checar um vídeo específico antes de cortar

```bash
python3 garimpar.py checar --url https://youtu.be/XXXXXXXXXXX
```

Diz a licença, o risco e se o YouTube marcou o vídeo como reivindicado por
parceiro de conteúdo. Use isso **antes** de gastar tempo editando.

### Baixar e gerar créditos

```bash
python3 garimpar.py baixar --arquivo saida/2026-08-15-surf.json --top 5 \
        --editor "Seu Canal"
python3 garimpar.py creditos --arquivo saida/2026-08-15-surf.json --editor "Seu Canal"
```

Cada arquivo baixado sai com um `.credito.txt` do lado — guarde, é a sua prova
de origem se alguém contestar.

---

## Como o score é calculado

Nota de 0 a 100, comparável entre fontes:

| Componente | Peso | O que mede |
|---|---|---|
| velocidade | 45% | views por dia desde a publicação — o sinal real de viral |
| engajamento | 25% | (curtidas + comentários) ÷ views |
| recência | 15% | decai pela metade a cada 45 dias |
| formato | 15% | duração aproveitável para corte, com bônus para vertical |

Vídeo antigo com muitas views perde para vídeo novo subindo rápido, que é
exatamente o que interessa para cortes.

Duas ressalvas de honestidade: o Pexels não publica número de views, então a
posição no ranking da própria API entra como aproximação; e no Internet
Archive o número exibido é de **downloads do item**, não de visualizações.

---

## Níveis de risco

| Nível | Significa |
|---|---|
| **BAIXO** | domínio público, CC0, Pexels, Pixabay — pode cortar e monetizar |
| **MÉDIO** | CC BY / CC BY-SA — pode, **desde que credite** e confira a trilha sonora |
| **ALTO** | CC NC (proíbe comercial), CC ND (proíbe derivada), licença não declarada, ou vídeo reivindicado por parceiro — **não use** |

O filtro padrão já corta tudo que for `ALTO`.

---

## O que a licença **não** cobre

É aqui que a maioria dos canais de corte toma strike mesmo usando material CC:

1. **Trilha sonora.** O autor licenciou em CC a imagem *dele*. A música de
   fundo continua sendo da gravadora, e o Content ID identifica a faixa em
   segundos. Na dúvida, mute e ponha áudio livre.
2. **Trechos de terceiros dentro do vídeo.** Clipe de novela, jogo de futebol,
   trecho de filme — o uploader não podia licenciar aquilo, então a marcação
   como CC não vale para esses trechos.
3. **Imagem das pessoas.** Direito de imagem é separado do direito autoral. Um
   clipe de banco de mídia é livre para uso, mas não autoriza sugerir que a
   pessoa endossa o seu produto, nem colocá-la em contexto sensível.
4. **Marcas e logos** que apareçam em cena.
5. **Termos de uso da plataforma.** Baixar arquivo do YouTube fere os Termos de
   Uso mesmo com licença CC — são coisas diferentes. Por isso o comando
   `baixar` recusa a fonte `youtube_cc` e manda usar o editor do próprio
   YouTube ou pedir o arquivo ao autor.

**Rotina antes de publicar cada corte:**

- [ ] Confirmar a licença na página original (ela pode mudar depois da coleta)
- [ ] Salvar print da página com a licença e a data
- [ ] Colar o crédito na descrição, e na tela quando a licença exigir
- [ ] Trocar a trilha sonora por música livre
- [ ] Acrescentar conteúdo seu: narração, comentário, corte editorial

O último item não é só jurídico. Repostagem crua tem alcance pequeno nas
plataformas e não caracteriza obra transformativa em lugar nenhum.

---

## Testes

```bash
python3 -m unittest discover -s testes -v
```

28 testes cobrindo conversão de cada API, cálculo de score, classificação de
licença e geração dos relatórios. Rodam offline, sem bater em rede.

---

## Estrutura

```
garimpo-videos/
├── garimpar.py            ponto de entrada
├── exemplo.env            modelo das chaves
├── garimpo/
│   ├── cli.py             comandos: fontes, buscar, checar, baixar, creditos
│   ├── modelos.py         estrutura Video, comum a todas as fontes
│   ├── scoring.py         cálculo do "quanto bombou"
│   ├── licencas.py        licenças, nível de risco e texto de crédito
│   ├── relatorio.py       saída em JSON, CSV e painel HTML
│   ├── util_http.py       cliente HTTP com retentativa
│   └── fontes/
│       ├── base.py        contrato das fontes
│       ├── youtube_cc.py  YouTube filtrado por videoLicense=creativeCommon
│       ├── pexels.py
│       ├── pixabay.py
│       └── archive_org.py Internet Archive, sem chave
└── testes/
```

Para acrescentar uma fonte: herde de `Fonte`, implemente `buscar()` devolvendo
uma lista de `Video` e registre em `garimpo/fontes/__init__.py`.

Todas as fontes usam API oficial e pública — nada de raspar página ou contornar
bloqueio. É isso que mantém a coleta dentro dos termos de uso de cada
plataforma.

---

Isto é apoio operacional para reduzir risco, não parecer jurídico. Para
operação comercial em escala, vale passar as regras por um advogado.
