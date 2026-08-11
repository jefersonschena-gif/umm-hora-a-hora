/* UMM Studio — base
   Tokens do tema, formatos, utilidades e primitivas de desenho em canvas.
   Tudo em coordenadas reais do vídeo (ex.: 1080x1920). */

window.UMM = window.UMM || {};

(function (U) {
  'use strict';

  /* ---------------------------------------------------------------
     TEMA — fintech premium claro
     Direção de arte: branco quente limpo, cinza suave, grafite, vidro e metal
     escovado, com verde e dourado como únicos acentos. Luz de estúdio, sombra
     nítida, reflexo elegante. Nada de azul: a paleta é quente.

     U.TEMA é MUTÁVEL de propósito. Cenas de tom escuro trocam os valores no
     mesmo objeto (U.aplicarTom), então todo visual desenha na paleta certa sem
     precisar receber cor por parâmetro.
     --------------------------------------------------------------- */
  U.PALETA_CLARA = {
    tom:         'claro',
    fundo:       '#F5F2ED',
    fundoTopo:   '#FFFFFF',
    fundoBase:   '#EBE6DE',
    cartao:      '#FFFFFF',
    cartaoSuave: '#F2EEE7',
    tinta:       '#22262B',
    tinta2:      '#5C626A',
    tinta3:      '#9BA0A7',
    linha:       '#E5E0D8',
    linhaForte:  '#CCC5BA',
    acento:      '#0E7A50',
    acentoSuave: '#E3F0E9',
    dado:        '#9A7524',
    dadoSuave:   '#F5EDDC',
    alerta:      '#A8391F',
    alertaSuave: '#F7E7E1',
    ouro:        '#B8912F',
    ouroClaro:   '#E3C979',
    metal:       '#C8CCD1',
    metalEscuro: '#8E949B',
    sombra:      'rgba(34,38,43,0.13)',
    sombraForte: 'rgba(34,38,43,0.26)',
    vidro:       'rgba(255,255,255,0.55)',
    fonte: 'Inter, "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'
  };

  /* Tom escuro: usado só nas cenas de dívida, juros e vencimento. É pontuação,
     não o clima do vídeo — o verificador reclama se passar de um terço das cenas. */
  U.PALETA_ESCURA = {
    tom:         'escuro',
    fundo:       '#1C1F23',
    fundoTopo:   '#2A2E34',
    fundoBase:   '#131518',
    cartao:      '#262A30',
    cartaoSuave: '#2E333A',
    tinta:       '#F4F1EC',
    tinta2:      '#B4B9C0',
    tinta3:      '#7C828A',
    linha:       '#383D45',
    linhaForte:  '#4C525B',
    acento:      '#3FBE87',
    acentoSuave: '#1E3A2E',
    dado:        '#E3C979',
    dadoSuave:   '#3A3222',
    alerta:      '#E4674A',
    alertaSuave: '#3A2019',
    ouro:        '#E3C979',
    ouroClaro:   '#F3E2AE',
    metal:       '#8E949B',
    metalEscuro: '#5B6169',
    sombra:      'rgba(0,0,0,0.45)',
    sombraForte: 'rgba(0,0,0,0.62)',
    vidro:       'rgba(255,255,255,0.10)',
    fonte: 'Inter, "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'
  };

  /* Estúdio grafite — o meio-termo entre a versão clara e a escura.
     Campo de carvão quente com luz de estúdio forte, painéis de vidro mais
     claros e quentes que os do tom escuro, e o dourado como acento principal.
     É o clima de fotografia de produto: fundo fechado, objeto iluminado. */
  U.PALETA_GRAFITE = {
    tom:         'grafite',
    fundo:       '#24282D',
    fundoTopo:   '#373D45',
    fundoBase:   '#181B1F',
    cartao:      '#2E343B',
    cartaoSuave: '#373E46',
    tinta:       '#F7F4EE',
    tinta2:      '#C2C7CE',
    tinta3:      '#8B929A',
    linha:       '#434A53',
    linhaForte:  '#5C646E',
    acento:      '#38C085',
    acentoSuave: '#1F4034',
    dado:        '#DEC684',
    dadoSuave:   '#3D3524',
    alerta:      '#E4674A',
    alertaSuave: '#3D211A',
    ouro:        '#DEC684',
    ouroClaro:   '#F2E3B4',
    metal:       '#B3B9C0',
    metalEscuro: '#6D747C',
    sombra:      'rgba(0,0,0,0.48)',
    sombraForte: 'rgba(0,0,0,0.66)',
    vidro:       'rgba(255,255,255,0.14)',
    fonte: 'Inter, "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'
  };

  U.CLIMAS = {
    claro:   { rotulo: 'Claro — branco quente e luz alta', paleta: 'PALETA_CLARA' },
    grafite: { rotulo: 'Grafite — estúdio fechado, objeto iluminado', paleta: 'PALETA_GRAFITE' },
    escuro:  { rotulo: 'Escuro — quase preto, clima de alerta', paleta: 'PALETA_ESCURA' }
  };

  U.TEMA = Object.assign({}, U.PALETA_CLARA);

  /* O clima é do projeto; o tom é da cena. Uma cena em tom escuro sempre
     mergulha para a paleta mais fechada, seja qual for o clima. */
  U.aplicarTom = function (clima, tomCena) {
    const base = U[(U.CLIMAS[clima] || U.CLIMAS.claro).paleta] || U.PALETA_CLARA;
    Object.assign(U.TEMA, tomCena === 'escuro' ? U.PALETA_ESCURA : base);
    return U.TEMA;
  };

  /* Acento por tipo de cena — só verde e dourado, como manda a direção. */
  U.ACENTO_POR_TIPO = {
    gancho:      'ouro',
    contexto:    'tinta',
    dado:        'ouro',
    passo:       'acento',
    comparativo: 'ouro',
    alerta:      'alerta',
    cta:         'acento',
    /* papéis de aula */
    pergunta:      'ouro',
    conceito:      'tinta',
    exemplo:       'ouro',
    erro:          'alerta',
    recapitulacao: 'acento',
    /* papéis da interseção */
    previsao:      'ouro',
    surpresa:      'ouro',
    resgate:       'acento'
  };

  /* Papéis de cena por modo. Em aula a história é outra: pergunta, conceito,
     exemplo, erro comum, recapitulação — e não gancho, dado, chamada. */
  U.TIPOS = {
    retencao:  ['gancho', 'contexto', 'dado', 'passo', 'comparativo', 'alerta', 'cta'],
    aula:      ['pergunta', 'conceito', 'exemplo', 'dado', 'erro', 'passo', 'recapitulacao', 'cta'],
    intersecao: ['pergunta', 'previsao', 'conceito', 'exemplo', 'surpresa', 'dado',
                 'erro', 'passo', 'resgate', 'recapitulacao', 'cta']
  };

  U.MODOS = {
    retencao:   { rotulo: 'Retenção — prender e converter', pps: 2.55, respiro: 0.0, min: 15, max: 95 },
    aula:       { rotulo: 'Aula — ensinar e fixar',         pps: 2.30, respiro: 0.6, min: 45, max: 240 },
    intersecao: { rotulo: 'Interseção — ensinar segurando', pps: 2.42, respiro: 0.3, min: 40, max: 150 }
  };

  /* Os recursos que servem aos dois lados ao mesmo tempo. É esta lista que o
     modo interseção persegue — e que a curva do vídeo mede. */
  U.RECURSOS_INTERSECAO = [
    { chave: 'lacuna',   nome: 'Pergunta que abre lacuna', retencao: 'é o gancho',            aprendizado: 'é organizador prévio' },
    { chave: 'previsao', nome: 'Previsão antes da revelação', retencao: 'cria suspense',      aprendizado: 'é efeito de geração' },
    { chave: 'surpresa', nome: 'Expectativa quebrada',      retencao: 'segura no susto',      aprendizado: 'fixa a memória' },
    { chave: 'conta',    nome: 'Conta revelada linha a linha', retencao: 'micro-suspense',    aprendizado: 'é exemplo trabalhado' },
    { chave: 'resgate',  nome: 'Resgate no meio',           retencao: 'reengaja',             aprendizado: 'é prática de recuperação' },
    { chave: 'laco',     nome: 'Laço fechado no fim',       retencao: 'entrega o prometido',  aprendizado: 'consolida' }
  ];

  /* ---------------------------------------------------------------
     FORMATOS
     --------------------------------------------------------------- */
  U.FORMATOS = {
    '9x16': { rotulo: 'Reels / TikTok / Shorts (9:16)', w: 1080, h: 1920, orientacao: 'v' },
    '4x5':  { rotulo: 'Feed Instagram (4:5)',           w: 1080, h: 1350, orientacao: 'v' },
    '1x1':  { rotulo: 'Feed quadrado (1:1)',            w: 1080, h: 1080, orientacao: 'v' },
    '16x9': { rotulo: 'YouTube / LinkedIn (16:9)',      w: 1920, h: 1080, orientacao: 'h' }
  };

  /* ---------------------------------------------------------------
     UTILIDADES
     --------------------------------------------------------------- */
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp  = (a, b, t) => a + (b - a) * t;
  const faixa = (v, a, b) => clamp((v - a) / (b - a || 1), 0, 1);

  U.clamp = clamp;
  U.lerp  = lerp;
  U.faixa = faixa;

  /* Curvas de animação. Nada de bounce exagerado: fintech é sóbrio. */
  U.ease = {
    saida:    t => 1 - Math.pow(1 - t, 3),
    saida4:   t => 1 - Math.pow(1 - t, 4),
    entrada:  t => t * t * t,
    suave:    t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
    linear:   t => t,
    /* leve overshoot, quase imperceptível */
    firme:    t => { const c = 1.24; const u = t - 1; return 1 + (c + 1) * u * u * u + c * u * u; }
  };

  /* Entrada padrão de um elemento dentro da cena: aparece em `ini`, leva `dur`. */
  U.aparecer = (p, ini, dur) => U.ease.saida(faixa(p, ini, ini + (dur || 0.18)));

  U.numeroBR = (n, casas) => {
    const d = casas == null ? (Math.abs(n) < 10 && n % 1 !== 0 ? 1 : 0) : casas;
    return n.toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  };

  U.moedaBR = n => n.toLocaleString('pt-BR', {
    style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 2
  });

  /* Lê "1.240,50" ou "R$ 1.240,50" ou "12,5%" e devolve {prefixo, valor, sufixo, casas}. */
  U.lerNumero = function (txt) {
    const s = String(txt == null ? '' : txt);
    const m = s.match(/-?\d[\d.\s]*(?:,\d+)?/);
    if (!m) return null;
    const bruto = m[0];
    const limpo = bruto.replace(/[.\s]/g, '').replace(',', '.');
    const valor = parseFloat(limpo);
    if (isNaN(valor)) return null;
    const virg = bruto.indexOf(',');
    return {
      prefixo: s.slice(0, m.index),
      sufixo:  s.slice(m.index + bruto.length),
      valor:   valor,
      casas:   virg === -1 ? 0 : bruto.length - virg - 1
    };
  };

  /* Anima um número escrito ("R$ 1.240,00") de 0 até o valor, preservando o formato. */
  U.animarNumero = function (txt, k) {
    const n = U.lerNumero(txt);
    if (!n) return String(txt == null ? '' : txt);
    return n.prefixo + U.numeroBR(n.valor * k, n.casas) + n.sufixo;
  };

  U.semAcento = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  U.normalizar = s => U.semAcento(s).toLowerCase().replace(/\s+/g, ' ').trim();
  U.palavras = s => U.normalizar(s).split(/[^a-z0-9%$.,:-]+/).filter(Boolean);

  U.id = () => 'c' + Math.random().toString(36).slice(2, 9);

  /* ---------------------------------------------------------------
     PRIMITIVAS DE DESENHO
     --------------------------------------------------------------- */

  U.caminhoArredondado = function (ctx, x, y, w, h, r) {
    const rr = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + rr, y);
    ctx.lineTo(x + w - rr, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + rr);
    ctx.lineTo(x + w, y + h - rr);
    ctx.quadraticCurveTo(x + w, y + h, x + w - rr, y + h);
    ctx.lineTo(x + rr, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - rr);
    ctx.lineTo(x, y + rr);
    ctx.quadraticCurveTo(x, y, x + rr, y);
    ctx.closePath();
  };

  /* Cartão branco com sombra baixa — a unidade visual do tema. */
  U.cartao = function (ctx, x, y, w, h, r, op) {
    op = op || {};
    ctx.save();
    if (op.sombra !== false) {
      ctx.shadowColor = op.corSombra || U.TEMA.sombra;
      ctx.shadowBlur = op.blur == null ? 48 : op.blur;
      ctx.shadowOffsetY = op.dy == null ? 18 : op.dy;
    }
    ctx.fillStyle = op.fundo || U.TEMA.cartao;
    U.caminhoArredondado(ctx, x, y, w, h, r);
    ctx.fill();
    ctx.restore();
    if (op.borda) {
      ctx.save();
      ctx.strokeStyle = op.borda === true ? U.TEMA.linha : op.borda;
      ctx.lineWidth = op.bordaLargura || 2;
      U.caminhoArredondado(ctx, x, y, w, h, r);
      ctx.stroke();
      ctx.restore();
    }
  };

  U.pilula = function (ctx, x, y, texto, op) {
    op = op || {};
    const alt = op.altura || 56;
    const tam = op.tamanho || Math.round(alt * 0.46);
    ctx.save();
    ctx.font = pesoFonte(op.peso || 600, tam);
    const larg = ctx.measureText(texto).width + alt * 0.9;
    const px = op.align === 'right' ? x - larg : op.align === 'center' ? x - larg / 2 : x;
    U.caminhoArredondado(ctx, px, y, larg, alt, alt / 2);
    ctx.fillStyle = op.fundo || U.TEMA.acentoSuave;
    ctx.fill();
    if (op.borda) { ctx.strokeStyle = op.borda; ctx.lineWidth = 2; ctx.stroke(); }
    ctx.fillStyle = op.cor || U.TEMA.acento;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(texto, px + alt * 0.45, y + alt / 2 + 1);
    ctx.restore();
    return { largura: larg, altura: alt };
  };

  function pesoFonte(peso, tam) {
    return peso + ' ' + tam + 'px ' + U.TEMA.fonte;
  }
  U.pesoFonte = pesoFonte;

  /* Quebra texto em linhas respeitando a largura máxima. */
  U.quebrar = function (ctx, texto, maxW) {
    const linhas = [];
    String(texto || '').split('\n').forEach(function (paragrafo) {
      const termos = paragrafo.split(/\s+/).filter(Boolean);
      if (!termos.length) { linhas.push(''); return; }
      let atual = termos[0];
      for (let i = 1; i < termos.length; i++) {
        const tentativa = atual + ' ' + termos[i];
        if (ctx.measureText(tentativa).width <= maxW) atual = tentativa;
        else { linhas.push(atual); atual = termos[i]; }
      }
      linhas.push(atual);
    });
    return linhas;
  };

  /* Auto-ajuste: encolhe a fonte até caber em maxW x maxLinhas.
     Devolve {tamanho, linhas, altura} — nunca abaixo de `min`. */
  U.ajustar = function (ctx, texto, op) {
    const max = op.max, min = op.min || 40, peso = op.peso || 700;
    const lh = op.entrelinha || 1.08;
    let tam = max, linhas;
    for (;;) {
      ctx.font = pesoFonte(peso, tam);
      linhas = U.quebrar(ctx, texto, op.maxLargura);
      const cabe = linhas.length <= (op.maxLinhas || 3) &&
                   (!op.maxAltura || linhas.length * tam * lh <= op.maxAltura);
      if (cabe || tam <= min) break;
      tam -= 2;
    }
    ctx.font = pesoFonte(peso, tam);
    return { tamanho: tam, linhas: linhas, altura: linhas.length * tam * lh, entrelinha: lh };
  };

  /* Desenha um bloco de linhas já ajustado, com animação de entrada por linha. */
  U.blocoTexto = function (ctx, ajuste, x, y, op) {
    op = op || {};
    const lh = ajuste.tamanho * ajuste.entrelinha;
    ctx.save();
    if ('letterSpacing' in ctx) ctx.letterSpacing = (op.tracking || 0) + 'px';
    ctx.font = pesoFonte(op.peso || 700, ajuste.tamanho);
    ctx.textAlign = op.align || 'left';
    ctx.textBaseline = 'top';
    for (let i = 0; i < ajuste.linhas.length; i++) {
      const k = op.progresso == null ? 1 : U.aparecer(op.progresso, (op.atraso || 0) + i * 0.05, 0.26);
      if (k <= 0) continue;
      ctx.globalAlpha = k * (op.opacidade == null ? 1 : op.opacidade);
      ctx.fillStyle = op.cor || U.TEMA.tinta;
      ctx.fillText(ajuste.linhas[i], x, y + i * lh + (1 - k) * ajuste.tamanho * 0.28);
    }
    ctx.restore();
    return ajuste.linhas.length * lh;
  };

  /* Texto simples de uma linha. */
  U.texto = function (ctx, txt, x, y, op) {
    op = op || {};
    ctx.save();
    if ('letterSpacing' in ctx) ctx.letterSpacing = (op.tracking || 0) + 'px';
    ctx.font = pesoFonte(op.peso || 600, op.tamanho || 40);
    ctx.fillStyle = op.cor || U.TEMA.tinta2;
    ctx.textAlign = op.align || 'left';
    ctx.textBaseline = op.baseline || 'top';
    ctx.globalAlpha = op.opacidade == null ? 1 : op.opacidade;
    ctx.fillText(txt, x, y);
    const larg = ctx.measureText(txt).width;
    ctx.restore();
    return larg;
  };

  U.linhaH = function (ctx, x, y, w, cor) {
    ctx.save();
    ctx.strokeStyle = cor || U.TEMA.linha;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, y + 1);
    ctx.lineTo(x + w, y + 1);
    ctx.stroke();
    ctx.restore();
  };

  /* Ícone de "check" desenhado, sem dependência de fonte de ícones. */
  U.check = function (ctx, cx, cy, r, cor, k) {
    k = k == null ? 1 : clamp(k, 0, 1);
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.fillStyle = cor;
    ctx.globalAlpha = 0.14;
    ctx.fill();
    ctx.globalAlpha = 1;
    ctx.strokeStyle = cor;
    ctx.lineWidth = r * 0.22;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    const p1 = [cx - r * 0.42, cy + r * 0.02];
    const p2 = [cx - r * 0.10, cy + r * 0.34];
    const p3 = [cx + r * 0.46, cy - r * 0.34];
    ctx.beginPath();
    ctx.moveTo(p1[0], p1[1]);
    if (k < 0.5) {
      const t = k / 0.5;
      ctx.lineTo(lerp(p1[0], p2[0], t), lerp(p1[1], p2[1], t));
    } else {
      const t = (k - 0.5) / 0.5;
      ctx.lineTo(p2[0], p2[1]);
      ctx.lineTo(lerp(p2[0], p3[0], t), lerp(p2[1], p3[1], t));
    }
    ctx.stroke();
    ctx.restore();
  };

  U.seta = function (ctx, x1, y1, x2, y2, cor, larg) {
    ctx.save();
    ctx.strokeStyle = cor;
    ctx.fillStyle = cor;
    ctx.lineWidth = larg || 6;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    const ang = Math.atan2(y2 - y1, x2 - x1);
    const s = (larg || 6) * 2.6;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - s * Math.cos(ang - 0.42), y2 - s * Math.sin(ang - 0.42));
    ctx.lineTo(x2 - s * Math.cos(ang + 0.42), y2 - s * Math.sin(ang + 0.42));
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  };

  /* ---------------------------------------------------------------
     MATERIAIS — vidro, metal escovado, luz de estúdio
     É o que separa "gráfico bonito" de "premium". Tudo em canvas puro.
     --------------------------------------------------------------- */

  /* Metal escovado: base em degradê mais fibras finas na horizontal. */
  U.metalEscovado = function (ctx, x, y, w, h, r, op) {
    op = op || {};
    const claro = op.claro || U.TEMA.metal;
    const escuro = op.escuro || U.TEMA.metalEscuro;
    ctx.save();
    U.caminhoArredondado(ctx, x, y, w, h, r);
    ctx.clip();
    const g = ctx.createLinearGradient(x, y, x + w * 0.35, y + h);
    g.addColorStop(0, claro);
    g.addColorStop(0.42, escuro);
    g.addColorStop(0.62, claro);
    g.addColorStop(1, escuro);
    ctx.fillStyle = g;
    ctx.fillRect(x, y, w, h);
    /* fibras */
    ctx.globalAlpha = 0.10;
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 1;
    for (let i = 0; i < h; i += 3) {
      ctx.globalAlpha = 0.04 + ((i * 37) % 11) / 160;
      ctx.beginPath();
      ctx.moveTo(x, y + i + 0.5);
      ctx.lineTo(x + w, y + i + 0.5);
      ctx.stroke();
    }
    ctx.restore();
  };

  /* Varredura especular: a faixa de luz que atravessa vidro e plástico.
     k vai de 0 (fora, à esquerda) a 1 (fora, à direita). */
  U.brilhoVidro = function (ctx, x, y, w, h, r, k, forca) {
    if (k <= 0 || k >= 1) return;
    ctx.save();
    U.caminhoArredondado(ctx, x, y, w, h, r);
    ctx.clip();
    const larg = w * 0.42;
    const cx = x - larg + k * (w + larg * 2);
    const g = ctx.createLinearGradient(cx - larg / 2, y, cx + larg / 2, y + h);
    g.addColorStop(0, 'rgba(255,255,255,0)');
    g.addColorStop(0.5, 'rgba(255,255,255,' + (forca == null ? 0.30 : forca) + ')');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(x, y, w, h);
    ctx.restore();
  };

  /* Sombra de contato: a elipse macia que assenta o objeto na superfície. */
  U.sombraContato = function (ctx, cx, cy, w, h, forca) {
    ctx.save();
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) / 2);
    const a = forca == null ? 0.28 : forca;
    g.addColorStop(0, 'rgba(20,22,26,' + a + ')');
    g.addColorStop(0.55, 'rgba(20,22,26,' + a * 0.45 + ')');
    g.addColorStop(1, 'rgba(20,22,26,0)');
    ctx.translate(cx, cy);
    ctx.scale(1, h / Math.max(1, w));
    ctx.translate(-cx, -cy);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, w / 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  };

  /* Reflexo de estúdio: cópia espelhada logo abaixo do objeto, desbotando. */
  let _espelho = null;
  U.reflexo = function (ctx, x, y, w, h, vao, desenhar, fracao) {
    const frac = fracao == null ? 0.42 : fracao;
    const lw = Math.ceil(w), lh = Math.ceil(h);
    if (!_espelho) _espelho = document.createElement('canvas');
    if (_espelho.width < lw || _espelho.height < lh) {
      _espelho.width = Math.max(_espelho.width, lw);
      _espelho.height = Math.max(_espelho.height, lh);
    }
    const c2 = _espelho.getContext('2d');
    c2.save();
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.clearRect(0, 0, _espelho.width, _espelho.height);
    c2.translate(-x, -y);
    desenhar(c2);
    c2.restore();

    /* apaga o topo (que vira o fundo do reflexo) */
    c2.save();
    c2.setTransform(1, 0, 0, 1, 0, 0);
    c2.globalCompositeOperation = 'destination-out';
    const g = c2.createLinearGradient(0, 0, 0, lh);
    g.addColorStop(0, 'rgba(0,0,0,1)');
    g.addColorStop(0.55, 'rgba(0,0,0,0.86)');
    g.addColorStop(1, 'rgba(0,0,0,0.42)');
    c2.fillStyle = g;
    c2.fillRect(0, 0, lw, lh);
    c2.restore();

    ctx.save();
    ctx.globalAlpha = 0.20;
    /* o recorte vem em coordenadas do quadro, antes de espelhar */
    ctx.beginPath();
    ctx.rect(x, y + h + (vao || 0), w, h * frac);
    ctx.clip();
    ctx.translate(x, y + h + (vao || 0));
    ctx.scale(1, -1);
    ctx.drawImage(_espelho, 0, 0, lw, lh, 0, -lh, lw, lh);
    ctx.restore();
  };

  /* Recorte arredondado reutilizável. */
  U.comRecorte = function (ctx, x, y, w, h, r, fn) {
    ctx.save();
    U.caminhoArredondado(ctx, x, y, w, h, r);
    ctx.clip();
    fn();
    ctx.restore();
  };

})(window.UMM);
