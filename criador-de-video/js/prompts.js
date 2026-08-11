/* UMM Studio — prompts para geradores de vídeo

   O Studio já tem o roteiro verificado: estrutura, texto grande, narração
   autossuficiente, didática, curva. Falta transformar isso em prompt para o
   gerador de filmagem (Higgsfield, Sora, Runway, Kling, o que for).

   Duas formas, porque são dois jeitos de produzir:

   1. POR CENA   — um prompt por cena, cada um virando um clipe. Controle fino,
                   mais caro, e é como se monta vídeo longo.
   2. INTEIRO    — um prompt só, com o áudio da narração como referência de
                   tempo. Mais barato e coeso, menos previsível.

   Regra que vale nas duas: a filmagem sai SEM TEXTO LEGÍVEL. O texto grande, a
   legenda e a marca entram depois, aqui no Studio, onde o verificador cobra que
   o vídeo se entenda no mudo. Deixar o gerador escrever é abrir mão disso — e
   gerador de vídeo erra ortografia em português com frequência. */

(function (U) {
  'use strict';

  const P = {};
  U.Prompts = P;

  /* ---------------------------------------------------------------
     Direção de arte por clima, no vocabulário que os modelos entendem
     --------------------------------------------------------------- */
  P.ESTILOS = {
    claro:
      'bright premium fintech aesthetic, not dark overall. Clean warm white, soft gray and graphite, ' +
      'glass and brushed metal surfaces, subtle green and gold accents, strong studio lighting, ' +
      'crisp shadows, elegant reflections, high-end banking app and investment platform feeling',
    grafite:
      'premium graphite studio aesthetic: warm charcoal field, closed and cinematic, with the product ' +
      'lit as the hero. Realistic macro product lighting, glass and brushed metal surfaces, ' +
      'subtle green and gold accents, hard key light from the upper right, deep crisp shadows, ' +
      'elegant reflections on a dark seamless surface',
    escuro:
      'premium dark financial aesthetic, near black seamless background, realistic macro product ' +
      'lighting, glass and metal surfaces, restrained gold and green accents, heavy contrast, ' +
      'tense and editorial'
  };

  P.NEGATIVO =
    'no people, no characters, no faces, no hands holding products, no logos, no brand names, ' +
    'no readable text, no letters, no numbers rendered as graphics, no captions, no subtitles, ' +
    'no watermark, no UI mockups with legible labels, no cartoon style, no stock-footage look';

  P.RITMO = 'editorial motion graphics, fast Brazilian finance social-video pacing, one clear idea per shot';

  /* Um mergulho escuro pontual dentro de um vídeo claro. */
  P.TOM_ESCURO =
    'for this shot only, shift into a darker warning mood: light drops, shadows deepen, ' +
    'the palette cools toward graphite and a single warm accent survives';

  /* ---------------------------------------------------------------
     Cada cena concreta do Studio vira uma descrição de imagem
     --------------------------------------------------------------- */
  P.VISUAL = {
    numero:
      'a single large figure resolving in mid-air over a clean surface, counting up, ' +
      'shallow depth of field, the number treated as a physical object of light',
    linha:
      'a rising line chart drawing itself across a glass panel, soft area fill beneath it, ' +
      'a bright point travelling along the curve',
    barras:
      'horizontal bars growing across a glass panel, one clearly longer than the others, ' +
      'thin metallic rules separating them',
    comparativo:
      'two panels side by side on a seamless surface, one plain and one lit and raised, ' +
      'the raised one clearly the better choice',
    cartao:
      'a premium credit card in macro on a clean surface, brushed metal chip catching the key light, ' +
      'a slow specular sweep crossing the plastic, a short mirror reflection beneath',
    pix:
      'a phone standing on a clean surface showing a payment confirmation, a square code pattern ' +
      'and a check mark resolving, soft glass reflections',
    boleto:
      'a printed invoice sheet on a surface, a barcode strip, a rubber stamp landing hard on it ' +
      'with a small puff of ink, paper fibre visible in macro',
    extrato:
      'a bank statement panel with rows of transactions appearing one by one, negative rows ' +
      'catching a warm red accent, thin dividing rules',
    notificacao:
      'a phone on a dark surface, a push notification card sliding down from the top edge with a ' +
      'soft bounce, screen glow spilling onto the surface',
    checklist:
      'three floating cards stacking in sequence, a check mark drawing itself into each one, ' +
      'soft contact shadows underneath',
    juros:
      'a row of columns growing from left to right, the last one dramatically taller, ' +
      'light raking across their tops',
    cofre:
      'a heavy vault door in macro, the dial turning, gold light leaking from the seam',
    alerta:
      'a shield form on a surface with a warning mark, hard rim light, tense mood',
    fluxo:
      'money flowing as light along curved paths from one node into three smaller nodes, ' +
      'clean and diagrammatic, no labels',
    calendario:
      'a calendar grid on a glass panel with a single day marked by a glowing disc',
    contrato:
      'a contract document in macro, a highlighter sweep passing over one hidden clause, ' +
      'shallow depth of field, paper texture',
    carteira:
      'an investment app panel floating on a dark surface, a balance figure and a small rising ' +
      'chart, glass and soft glow',
    moedas:
      'stacks of coins growing on a seamless surface, macro, warm metallic reflections',
    citacao:
      'an empty premium surface with a single shaft of key light and slow floating dust',
    chamada:
      'a solid accent-colored panel rising into frame on a clean surface, calm and final',
    midia:
      'the reference footage supplied by the author',
    pergunta:
      'an empty lit stage with a single object waiting, a ring of light closing slowly, ' +
      'a held beat of anticipation',
    definicao:
      'a single term card resting on a clean surface, lit from the side, a thin accent bar ' +
      'along its left edge, nothing else competing',
    conta:
      'a ledger panel where rows of figures land one by one, each with a soft snap, ' +
      'then a rule is drawn and the final figure settles below it',
    erroComum:
      'two stacked panels, the upper one marked with a cross in warm red, the lower one marked ' +
      'with a check in green, hard studio light',
    recapitulacao:
      'three numbered cards settling into place one after another, large numerals lit from behind'
  };

  /* ---------------------------------------------------------------
     Onde a filmagem gerada ajuda, e onde ela atrapalha

     Gerador de vídeo não escreve número certo. Cena cujo sentido ESTÁ no
     número — a conta, o extrato, o gráfico, a recapitulação — fica melhor
     desenhada aqui no Studio, onde o valor é exato e a fonte é legível.
     A filmagem gerada rende nas cenas de OBJETO: cartão, cofre, boleto,
     celular, contrato. O Studio avisa a diferença em vez de deixar você
     descobrir depois de gastar crédito.
     --------------------------------------------------------------- */
  P.RENDE_FILMADO = ['cartao', 'cofre', 'moedas', 'contrato', 'boleto', 'notificacao',
    'pix', 'calendario', 'alerta', 'citacao', 'pergunta', 'fluxo', 'chamada', 'midia'];

  P.melhorDesenhado = function (visual) {
    return P.RENDE_FILMADO.indexOf(visual) < 0;
  };

  P.diagnostico = function (projeto) {
    const desenhar = [], filmar = [];
    projeto.cenas.forEach(function (c, i) {
      (P.melhorDesenhado(c.visual) ? desenhar : filmar).push(i + 1);
    });
    return { desenhar: desenhar, filmar: filmar };
  };

  /* ---------------------------------------------------------------
     Utilidades
     --------------------------------------------------------------- */
  const PROPORCAO = { '9x16': '9:16 vertical', '4x5': '4:5 vertical', '1x1': '1:1 square', '16x9': '16:9 horizontal' };

  /* Geradores costumam aceitar só algumas durações. */
  P.duracaoAceita = function (s) {
    const opcoes = [5, 10, 15];
    return opcoes.reduce(function (a, b) {
      return Math.abs(b - s) < Math.abs(a - s) ? b : a;
    });
  };

  /* Traz os números e rótulos da cena para dentro do prompt, para a filmagem
     falar do mesmo assunto que o texto. Sem pedir que ela ESCREVA os números. */
  function conteudoDaCena(cena, dados) {
    const partes = [];
    if (dados.valor) partes.push('The figure at stake is around ' + dados.valor);
    if (dados.resultado) partes.push('It resolves to around ' + dados.resultado);
    if (dados.termo) partes.push('The subject is the concept of "' + dados.termo + '"');
    if (dados.pergunta) partes.push('The open question is "' + dados.pergunta + '"');
    if (dados.errado) partes.push('The wrong habit is "' + dados.errado + '"');
    if (dados.certo) partes.push('The right move is "' + dados.certo + '"');
    if ((dados.itens || []).length) {
      partes.push('The elements are: ' + dados.itens.slice(0, 4).map(function (i) {
        return i.rotulo + (i.valor ? ' (' + i.valor + ')' : '');
      }).join('; '));
    }
    return partes.join('. ');
  }

  P.estiloDe = function (projeto) {
    return P.ESTILOS[projeto.clima] || P.ESTILOS.claro;
  };

  /* ---------------------------------------------------------------
     1. Um prompt por cena
     --------------------------------------------------------------- */
  P.porCena = function (projeto, motor, i) {
    const cena = projeto.cenas[i];
    const dados = U.lerDados(cena.dados);
    const total = projeto.cenas.length;
    const dur = motor ? motor.duracoes[i] : 5;
    const visual = P.VISUAL[cena.visual] || P.VISUAL.citacao;

    const linhas = [];
    linhas.push('Create shot ' + (i + 1) + ' of ' + total + ' of a faceless Brazilian personal-finance ' +
      'explainer, ' + (PROPORCAO[projeto.formato] || '9:16 vertical') + ', ' +
      P.duracaoAceita(dur) + ' seconds, no audio.');
    linhas.push('');
    linhas.push('STYLE: ' + P.estiloDe(projeto) + '. ' + P.RITMO + '.');
    if (cena.tom === 'escuro') linhas.push('MOOD: ' + P.TOM_ESCURO + '.');
    linhas.push('');
    linhas.push('SHOT: ' + visual + '.');
    const conteudo = conteudoDaCena(cena, dados);
    if (conteudo) {
      linhas.push('CONTEXT — this is what the shot is about. Use it to choose composition and mood. ' +
        'Do NOT render any of it as readable text or figures: ' + conteudo + '.');
    }
    linhas.push('');
    linhas.push('The narration over this shot will be: "' + (cena.narracao || '—') + '" — ' +
      'match its length and its emotional beat, but generate no voice and no on-screen text.');
    linhas.push('');
    linhas.push('NEGATIVE: ' + P.NEGATIVO + '.');
    return linhas.join('\n');
  };

  /* ---------------------------------------------------------------
     2. Um prompt para o vídeo inteiro, com o áudio como referência
     --------------------------------------------------------------- */
  P.videoInteiro = function (projeto, motor) {
    const cenas = projeto.cenas;
    const dur = motor ? Math.round(motor.duracao) : 0;
    const linhas = [];

    linhas.push('Create a ' + (PROPORCAO[projeto.formato] || '9:16 vertical') + ' faceless Brazilian ' +
      'personal-finance explainer video, about ' + dur + ' seconds, synchronized to the provided ' +
      'audio narration. Use the uploaded audio as the timing and narration reference; do not create ' +
      'a new voice. No people, no characters, no faces.');
    linhas.push('');
    linhas.push('VISUAL DIRECTION: ' + P.estiloDe(projeto) + '. ' + P.RITMO + '.');

    const temEscuro = cenas.some(function (c) { return c.tom === 'escuro'; });
    if (temEscuro) {
      linhas.push('');
      linhas.push('When the narration reaches bills, interest, due dates or debt, briefly shift into a ' +
        'darker warning mood, then return to the base look for control, investing and results. ' +
        'The dark passage is punctuation, not the mood of the film.');
    }

    linhas.push('');
    linhas.push('SHOT LIST, in order:');
    cenas.forEach(function (c, i) {
      const dados = U.lerDados(c.dados);
      const t0 = motor ? motor.inicios[i] : 0;
      const t1 = t0 + (motor ? motor.duracoes[i] : 0);
      const conteudo = conteudoDaCena(c, dados);
      linhas.push('  ' + (i + 1) + '. ' + t0.toFixed(1) + 's–' + t1.toFixed(1) + 's — ' +
        (P.VISUAL[c.visual] || P.VISUAL.citacao) +
        (c.tom === 'escuro' ? ' (darker warning mood)' : '') +
        (conteudo ? '. ' + conteudo : '') + '.');
    });

    linhas.push('');
    linhas.push('NEGATIVE: ' + P.NEGATIVO + '.');
    linhas.push('');
    linhas.push('Note: all on-screen text, captions and branding are added afterwards in editing. ' +
      'Leave clean space in the upper third of the frame for a large headline and in the lower ' +
      'third for a caption.');
    return linhas.join('\n');
  };

  /* ---------------------------------------------------------------
     3. Imagem de referência do projeto
     --------------------------------------------------------------- */
  P.imagemBase = function (projeto) {
    return [
      'A single still frame that defines the look of a faceless Brazilian personal-finance video series, ' +
        (PROPORCAO[projeto.formato] || '9:16 vertical') + '.',
      '',
      'STYLE: ' + P.estiloDe(projeto) + '.',
      '',
      'SUBJECT: a premium credit card resting on a seamless surface, brushed metal chip, ' +
        'macro product photography, a short mirror reflection beneath, one warm accent highlight.',
      '',
      'Use this frame as the style reference for every shot of the series: same surface, same key ' +
        'light, same palette, same lens character.',
      '',
      'NEGATIVE: ' + P.NEGATIVO + '.'
    ].join('\n');
  };

  /* ---------------------------------------------------------------
     Documento completo
     --------------------------------------------------------------- */
  P.documento = function (projeto, motor) {
    const out = [];
    out.push('# Prompts — ' + (projeto.titulo || 'vídeo'));
    out.push('');
    out.push('Clima: ' + (projeto.clima || 'claro') + '  ·  Modo: ' + (projeto.modo || 'retencao') +
      '  ·  Formato: ' + projeto.formato + '  ·  Duração: ' + (motor ? motor.duracao.toFixed(1) : '?') + 's');
    out.push('');
    out.push('> A filmagem sai **sem texto legível**. O texto grande, a legenda e a marca entram');
    out.push('> depois, no UMM Studio, onde o verificador cobra que o vídeo se entenda no mudo.');
    out.push('> Traga o arquivo gerado de volta pelo botão "imagem ou vídeo…" de cada cena.');
    out.push('');
    const diag = P.diagnostico(projeto);
    if (diag.filmar.length) {
      out.push('**Vale gerar filmagem** para as cenas ' + diag.filmar.join(', ') +
        ' — o sentido delas está no objeto.');
    }
    if (diag.desenhar.length) {
      out.push('**Melhor deixar desenhado** no Studio as cenas ' + diag.desenhar.join(', ') +
        ' — o sentido delas está no número, e gerador de vídeo não escreve número certo.');
    }
    out.push('');
    out.push('---');
    out.push('');
    out.push('## Imagem de referência do estilo');
    out.push('');
    out.push('```');
    out.push(P.imagemBase(projeto));
    out.push('```');
    out.push('');
    out.push('## Vídeo inteiro, com o áudio da narração');
    out.push('');
    out.push('```');
    out.push(P.videoInteiro(projeto, motor));
    out.push('```');
    out.push('');
    out.push('## Cena a cena');
    projeto.cenas.forEach(function (c, i) {
      out.push('');
      out.push('### Cena ' + (i + 1) + ' — ' + (c.titulo || 'sem título'));
      out.push('');
      out.push('```');
      out.push(P.porCena(projeto, motor, i));
      out.push('```');
    });
    return out.join('\n');
  };

})(window.UMM);
