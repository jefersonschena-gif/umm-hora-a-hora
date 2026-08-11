/* UMM Studio — base
   Tokens do tema, formatos, utilidades e primitivas de desenho em canvas.
   Tudo em coordenadas reais do vídeo (ex.: 1080x1920). */

window.UMM = window.UMM || {};

(function (U) {
  'use strict';

  /* ---------------------------------------------------------------
     TEMA — fintech premium claro
     Fundo porcelana, cartões brancos, sombra baixa, um acento só por cena.
     --------------------------------------------------------------- */
  U.TEMA = {
    fundo:       '#F1F4F8',
    fundoBrilho: '#FFFFFF',
    cartao:      '#FFFFFF',
    cartaoSuave: '#F7F9FC',
    tinta:       '#0A1526',
    tinta2:      '#4B5869',
    tinta3:      '#909CAD',
    linha:       '#E2E8F0',
    linhaForte:  '#CBD5E1',
    acento:      '#0B7A4B',
    acentoSuave: '#E6F3EC',
    dado:        '#1B45E8',
    dadoSuave:   '#E9EDFF',
    alerta:      '#C0341C',
    alertaSuave: '#FBEBE7',
    ouro:        '#B8892B',
    sombra:      'rgba(10,21,38,0.10)',
    sombraForte: 'rgba(10,21,38,0.18)',
    fonte: 'Inter, "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif'
  };

  /* Acento por tipo de cena — mantém a paleta disciplinada. */
  U.ACENTO_POR_TIPO = {
    gancho:      'dado',
    contexto:    'tinta',
    dado:        'dado',
    passo:       'acento',
    comparativo: 'dado',
    alerta:      'alerta',
    cta:         'acento'
  };

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

  /* Recorte arredondado reutilizável. */
  U.comRecorte = function (ctx, x, y, w, h, r, fn) {
    ctx.save();
    U.caminhoArredondado(ctx, x, y, w, h, r);
    ctx.clip();
    fn();
    ctx.restore();
  };

})(window.UMM);
