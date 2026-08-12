/* UMM Studio — motor
   Monta o quadro final: fundo, marca, TEXTO GRANDE, palco da cena concreta,
   legenda sincronizada e barra de progresso.

   Regra de ouro do layout: o texto grande carrega a mensagem sozinho.
   Se você tirar o áudio, o vídeo continua completo. */

(function (U) {
  'use strict';

  const T = U.TEMA;

  /* ---------------------------------------------------------------
     Projeto
     --------------------------------------------------------------- */
  U.novaCena = function (base) {
    return Object.assign({
      id: U.id(),
      tipo: 'dado',
      visual: 'numero',
      selo: '',
      titulo: '',
      apoio: '',
      dados: '',
      narracao: '',
      tom: 'claro',     /* 'escuro' só para dívida, juros, vencimento */
      fonte: '',        /* de onde veio o dado: IBGE, Banco Central, etc. */
      midiaCheia: false,/* mídia própria ocupando o quadro inteiro */
      dur: 0            /* 0 = automático (pela narração ou pelo áudio) */
    }, base || {});
  };

  U.novoProjeto = function () {
    return {
      versao: 1,
      titulo: 'Novo vídeo',
      formato: '9x16',
      fps: 30,
      modo: 'retencao', /* 'retencao' | 'aula' | 'intersecao' */
      camera: 'nenhuma', /* 'nenhuma' | 'suave' | 'editorial' */
      clima: 'claro',   /* 'claro' | 'grafite' | 'escuro' */
      escala: 1,        /* 1 = 1080x1920 · 1.333 = 1440x2560 (2K) */
      areaSegura: true,
      marca: { nome: '', arroba: '' },
      voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
      cenas: [U.novaCena()]
    };
  };

  /* ---------------------------------------------------------------
     Layout
     --------------------------------------------------------------- */
  U.layout = function (projeto) {
    const f = U.FORMATOS[projeto.formato] || U.FORMATOS['9x16'];
    const e = Number(projeto.escala) > 0 ? Number(projeto.escala) : 1;
    /* múltiplo de 2: codificador de vídeo não aceita dimensão ímpar */
    const W = Math.round(f.w * e / 2) * 2, H = Math.round(f.h * e / 2) * 2;
    const vertical = f.orientacao === 'v';
    const alto = H / W >= 1.5;                    /* só 9:16 tem UI da plataforma por cima */
    const seguro = projeto.areaSegura && alto;
    const m = Math.round(W * 0.0667);

    if (!vertical) {
      /* 16:9 — texto à esquerda, cena à direita.
         A tipografia é dimensionada pela COLUNA de texto, não pela largura do
         quadro: 1920 px de quadro não significam título de 200 px. */
      const topo = Math.round(H * 0.115), base = Math.round(H * 0.885);
      const colW = Math.round((W - m * 3) * 0.44);
      const u = Math.round(colW / 0.867);
      return {
        W: W, H: H, m: m, u: u, vertical: false, seguro: false, topo: topo, base: base,
        marca: { x: m, y: Math.round(H * 0.045) },
        titulo: {
          x: m, y: topo, w: colW,
          max: Math.round(u * 0.105), min: Math.round(u * 0.060), linhas: 4
        },
        palco: { x: m * 2 + colW, y: topo, w: W - m * 3 - colW, h: base - topo },
        legenda: { x: m, y: base - Math.round(H * 0.17), w: colW, h: Math.round(H * 0.15) },
        progresso: { x: m, y: Math.round(H * 0.935), w: W - m * 2 }
      };
    }

    const topo = Math.round(seguro ? H * 0.075 : H * 0.048);
    const base = Math.round(seguro ? H * 0.845 : H * 0.950);
    const banda = base - topo;
    return {
      W: W, H: H, m: m, u: W, vertical: true, seguro: seguro, topo: topo, base: base,
      marca: { x: m, y: topo },
      titulo: {
        x: m, y: topo + Math.round(banda * 0.085), w: W - m * 2,
        max: Math.round(W * 0.105), min: Math.round(W * 0.060), linhas: 3
      },
      legenda: { x: m, y: base - Math.round(banda * 0.155), w: W - m * 2, h: Math.round(banda * 0.115) },
      progresso: { x: m, y: base - 8, w: W - m * 2 },
      /* palco é calculado depois do título, que tem altura variável */
      palcoMin: { x: m, w: W - m * 2 }
    };
  };

  /* ---------------------------------------------------------------
     Motor
     --------------------------------------------------------------- */
  function Motor(projeto) {
    this.projeto = projeto;
    this.audio = {};        /* índice da cena -> AudioBuffer (opcional) */
    this.midias = {};       /* índice da cena -> HTMLImageElement | HTMLVideoElement */
    this._cacheDados = {};
    this.recalcular();
  }
  U.Motor = Motor;

  /* Palavras por segundo de uma locução calma em português. Aula fala mais
     devagar e ganha um respiro no fim de cada cena: aprender precisa de tempo. */
  Motor.PPS = 2.55;

  Motor.prototype.ritmo = function () {
    return U.MODOS[this.projeto.modo] || U.MODOS.retencao;
  };

  Motor.prototype.dados = function (cena) {
    const chave = cena.visual + '\n' + (cena.dados || '');
    if (!this._cacheDados[chave]) this._cacheDados[chave] = U.lerDados(cena.dados);
    return this._cacheDados[chave];
  };

  Motor.prototype.duracaoCena = function (i) {
    const c = this.projeto.cenas[i];
    if (!c) return 0;
    if (Number(c.dur) > 0) return Number(c.dur);
    const buf = this.audio[i];
    if (buf) return Math.max(2.2, buf.duration + 0.55 + this.ritmo().respiro);
    const r = this.ritmo();
    const n = String(c.narracao || '').trim().split(/\s+/).filter(Boolean).length;
    if (!n) return 3.0 + r.respiro;
    return Math.max(2.2, Math.min(16, n / r.pps + 0.95 + r.respiro));
  };

  Motor.prototype.recalcular = function () {
    this._cacheDados = {};
    const cenas = this.projeto.cenas;
    this.duracoes = cenas.map((_, i) => this.duracaoCena(i));
    this.inicios = [];
    let acc = 0;
    for (let i = 0; i < this.duracoes.length; i++) { this.inicios.push(acc); acc += this.duracoes[i]; }
    this.duracao = acc;
    cenas.forEach((c, i) => { c._legendas = fatiarLegenda(c.narracao, this.duracoes[i]); });
    return this;
  };

  /* Divide a narração em pedaços curtos e distribui no tempo da cena
     proporcionalmente ao número de caracteres. */
  function fatiarLegenda(narracao, dur) {
    const txt = String(narracao || '').trim();
    if (!txt) return [];
    const MAX = 34;
    const termos = txt.split(/\s+/);
    const pedacos = [];
    let atual = '';
    termos.forEach(function (t) {
      const tentativa = atual ? atual + ' ' + t : t;
      if (tentativa.length > MAX && atual) { pedacos.push(atual); atual = t; }
      else atual = tentativa;
    });
    if (atual) pedacos.push(atual);

    const totalCh = pedacos.reduce((s, p) => s + p.length, 0) || 1;
    const util = Math.max(0.5, dur - 0.28);
    let t0 = 0.10;
    return pedacos.map(function (p) {
      const d = (p.length / totalCh) * util;
      const item = { txt: p, ini: t0, fim: t0 + d };
      t0 += d;
      return item;
    });
  }
  U.fatiarLegenda = fatiarLegenda;

  Motor.prototype.cenaEm = function (t) {
    const n = this.projeto.cenas.length;
    if (!n) return null;
    let i = 0;
    while (i < n - 1 && t >= this.inicios[i] + this.duracoes[i]) i++;
    const local = U.clamp(t - this.inicios[i], 0, this.duracoes[i]);
    return { i: i, local: local, p: this.duracoes[i] ? local / this.duracoes[i] : 0 };
  };

  Motor.prototype.acento = function (cena) {
    if (cena.tipo === 'alerta') return T.alerta;
    const chave = U.ACENTO_POR_TIPO[cena.tipo] || 'dado';
    return T[chave] || T.dado;
  };

  /* ---------------------------------------------------------------
     Desenho de um quadro no tempo t (segundos)
     --------------------------------------------------------------- */
  Motor.prototype.desenhar = function (ctx, t, op) {
    op = op || {};
    const P = this.projeto;
    const L = U.layout(P);
    const pos = this.cenaEm(t);
    ctx.save();
    ctx.clearRect(0, 0, L.W, L.H);
    U.aplicarTom(P.clima, pos ? P.cenas[pos.i].tom : 'claro');
    fundo(ctx, L, pos ? this.acento(P.cenas[pos.i]) : T.ouro);
    if (!pos) { ctx.restore(); return; }

    const cena = P.cenas[pos.i];
    const A = this.acento(cena);
    const p = pos.p;

    /* mídia própria ocupando o quadro inteiro: desfocada e sob véu, porque
       quem carrega a mensagem continua sendo o texto grande. */
    const midia = this.midias[pos.i];
    const fundoCheio = !!(midia && cena.midiaCheia);
    if (fundoCheio) {
      const sobra = Math.round(L.W * 0.06);   /* margem extra: o desfoque come as bordas */
      const camF = U.camera(P.camera, p, this.duracoes[pos.i], pos.i);
      ctx.save();
      aplicarCamera(ctx, { x: 0, y: 0, w: L.W, h: L.H }, camF);
      if ('filter' in ctx) ctx.filter = 'blur(' + Math.round(L.W * 0.016) + 'px)';
      desenharCobrindo(ctx, midia, -sobra, -sobra, L.W + sobra * 2, L.H + sobra * 2);
      ctx.restore();
      veu(ctx, L, cena.tom === 'escuro');
    }

    cabecalho(ctx, L, P, pos.i, P.cenas.length);

    /* ---- TEXTO GRANDE (a mensagem que dispensa o áudio) ---- */
    let y = L.titulo.y;
    if (cena.selo) {
      const kp = U.aparecer(p, 0, 0.22);
      ctx.save();
      ctx.globalAlpha = kp;
      const pil = U.pilula(ctx, L.titulo.x, y, cena.selo.toUpperCase(), {
        altura: Math.round(L.u * 0.052), tamanho: Math.round(L.u * 0.024),
        fundo: A + '18', cor: A, peso: 700
      });
      ctx.restore();
      y += pil.altura + Math.round(L.u * 0.028);
    }

    const aj = U.ajustar(ctx, cena.titulo || '', {
      max: L.titulo.max, min: L.titulo.min, peso: 800,
      maxLargura: L.titulo.w, maxLinhas: L.titulo.linhas, entrelinha: 1.06
    });
    this.ultimoTamanhoTitulo = aj.tamanho;
    U.blocoTexto(ctx, aj, L.titulo.x, y, {
      peso: 800, cor: T.tinta, progresso: p, atraso: 0.01,
      tracking: -Math.round(L.u * 0.0022)
    });
    y += aj.altura;

    if (cena.apoio) {
      y += Math.round(L.u * 0.020);
      const ap = U.ajustar(ctx, cena.apoio, {
        max: Math.round(L.u * 0.045), min: Math.round(L.u * 0.033), peso: 500,
        maxLargura: L.titulo.w, maxLinhas: 2, entrelinha: 1.25
      });
      U.blocoTexto(ctx, ap, L.titulo.x, y, {
        peso: 500, cor: T.tinta2, progresso: p, atraso: 0.12
      });
      y += ap.altura;
    }

    /* ---- PALCO: a cena concreta ---- */
    const palco = L.vertical
      ? {
          x: L.palcoMin.x,
          y: y + Math.round(L.H * 0.030),
          w: L.palcoMin.w,
          h: Math.max(120, L.legenda.y - (y + Math.round(L.H * 0.030)) - Math.round(L.H * 0.026))
        }
      : L.palco;

    /* com a mídia no quadro inteiro, redesenhar o mesmo arquivo no palco só
       duplicaria a imagem — o fundo já é a cena. */
    if (!(fundoCheio && cena.visual === 'midia')) {
      const visual = U.VISUAIS[cena.visual] || U.VISUAIS.citacao;
      const saida = 1 - U.faixa(p, 0.955, 1);
      const cam = U.camera(P.camera, p, this.duracoes[pos.i], pos.i,
        U.CAMERA_LIVRE.indexOf(cena.visual) >= 0);
      ctx.save();
      ctx.globalAlpha = saida;
      if (cam.escala !== 1 || cam.dx || cam.dy) {
        /* o recorte impede o zoom de invadir o título e a legenda */
        const folga = Math.round(L.W * 0.02);
        ctx.beginPath();
        ctx.rect(palco.x - folga, palco.y - folga, palco.w + folga * 2, palco.h + folga * 2);
        ctx.clip();
        aplicarCamera(ctx, palco, cam);
      }
      try {
        visual.desenhar(ctx, palco, p, cena, A, this.dados(cena), this.midias[pos.i]);
      } catch (e) {
        U.texto(ctx, 'erro no visual: ' + e.message, palco.x, palco.y, { tamanho: 26, cor: T.alerta });
      }
      ctx.restore();

      /* fonte do dado, fora da câmera para nunca sair do quadro */
      if (cena.fonte) {
        U.texto(ctx, 'Fonte: ' + cena.fonte, L.titulo.x, palco.y + palco.h + Math.round(L.u * 0.012), {
          tamanho: Math.round(L.u * 0.021), peso: 600, cor: T.tinta3,
          opacidade: U.aparecer(p, 0.35, 0.3)
        });
      }
    }

    /* ---- LEGENDA (o áudio virando texto) ---- */
    if (op.legendas !== false) legenda(ctx, L, cena, pos.local, A);

    /* ---- PROGRESSO ---- */
    barraProgresso(ctx, L, this.duracoes, pos.i, pos.p, A);

    if (op.guias) guias(ctx, L, palco);
    ctx.restore();
  };

  /* ---------------------------------------------------------------
     Peças do quadro
     --------------------------------------------------------------- */
  function fundo(ctx, L, A) {
    const g = ctx.createLinearGradient(0, 0, 0, L.H);
    g.addColorStop(0, T.fundoTopo);
    g.addColorStop(0.52, T.fundo);
    g.addColorStop(1, T.fundoBase);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, L.W, L.H);

    /* luz de estúdio: uma fonte alta à direita, larga e macia */
    const forcaLuz = { claro: [0.85, 0.20], grafite: [0.22, 0.06], escuro: [0.10, 0.03],
      editorial: [0.13, 0.04] }[T.tom] || [0.85, 0.20];
    const luz = ctx.createRadialGradient(
      L.W * 0.78, L.H * 0.06, 0, L.W * 0.78, L.H * 0.06, L.W * (T.tom === 'grafite' ? 0.85 : 1.05));
    luz.addColorStop(0, 'rgba(255,255,255,' + forcaLuz[0] + ')');
    luz.addColorStop(0.45, 'rgba(255,255,255,' + forcaLuz[1] + ')');
    luz.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = luz;
    ctx.fillRect(0, 0, L.W, L.H);

    /* um sopro do acento, quase invisível, para o quadro não ficar neutro demais */
    const halo = ctx.createRadialGradient(
      L.W * 0.18, L.H * 0.86, 0, L.W * 0.18, L.H * 0.86, L.W * 0.85);
    halo.addColorStop(0, A + (T.tom === 'claro' ? '16' : '22'));
    halo.addColorStop(1, A + '00');
    ctx.fillStyle = halo;
    ctx.fillRect(0, 0, L.W, L.H);
  }

  /* Aplica o enquadramento em torno do centro da caixa. */
  function aplicarCamera(ctx, caixa, cam) {
    const cx = caixa.x + caixa.w / 2, cy = caixa.y + caixa.h / 2;
    ctx.translate(cx + cam.dx * caixa.w, cy + cam.dy * caixa.h);
    ctx.scale(cam.escala, cam.escala);
    ctx.translate(-cx, -cy);
  }

  /* Desenha imagem ou vídeo cobrindo a área, sem distorcer (object-fit: cover). */
  function desenharCobrindo(ctx, el, x, y, w, h) {
    const lw = el.videoWidth || el.naturalWidth || el.width;
    const lh = el.videoHeight || el.naturalHeight || el.height;
    if (!lw || !lh) return;
    const escala = Math.max(w / lw, h / lh);
    const dw = lw * escala, dh = lh * escala;
    ctx.save();
    ctx.beginPath();
    ctx.rect(x, y, w, h);
    ctx.clip();
    try {
      ctx.drawImage(el, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
    } catch (e) { /* quadro ainda não decodificado */ }
    ctx.restore();
  }
  U.desenharCobrindo = desenharCobrindo;

  /* Véu sobre a mídia: sem ele o texto grande brigaria com a imagem. */
  function veu(ctx, L, escuro) {
    escuro = escuro || T.tom !== 'claro';
    const g = ctx.createLinearGradient(0, 0, 0, L.H);
    if (escuro) {
      g.addColorStop(0, 'rgba(16,18,22,0.86)');
      g.addColorStop(0.45, 'rgba(16,18,22,0.74)');
      g.addColorStop(1, 'rgba(16,18,22,0.90)');
    } else {
      g.addColorStop(0, 'rgba(250,248,245,0.93)');
      g.addColorStop(0.45, 'rgba(250,248,245,0.82)');
      g.addColorStop(1, 'rgba(250,248,245,0.95)');
    }
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, L.W, L.H);
  }

  function cabecalho(ctx, L, P, i, n) {
    const nome = (P.marca && P.marca.nome) || '';
    const lado = Math.round(L.u * 0.052);
    if (nome) {
      U.caminhoArredondado(ctx, L.marca.x, L.marca.y, lado, lado, lado * 0.32);
      ctx.fillStyle = T.tinta;
      ctx.fill();
      U.texto(ctx, nome.trim().charAt(0).toUpperCase(), L.marca.x + lado / 2, L.marca.y + lado / 2 + 1, {
        tamanho: Math.round(lado * 0.5), peso: 800, align: 'center', baseline: 'middle',
        cor: T.tom === 'claro' ? '#FFFFFF' : T.fundo   /* o chip é da cor da tinta */
      });
      const temArroba = !!P.marca.arroba;
      const tNome = Math.round(L.u * 0.026);
      const tArroba = Math.round(L.u * 0.021);
      const xTexto = L.marca.x + lado + Math.round(L.u * 0.016);
      const yNome = L.marca.y + (temArroba ? 2 : Math.round((lado - tNome) / 2));
      U.texto(ctx, nome, xTexto, yNome, { tamanho: tNome, peso: 700, cor: T.tinta });
      if (temArroba) {
        U.texto(ctx, P.marca.arroba, xTexto, yNome + tNome + Math.round(L.u * 0.007),
          { tamanho: tArroba, peso: 500, cor: T.tinta3 });
      }
    }
    const pad = s => (s < 10 ? '0' : '') + s;
    U.texto(ctx, pad(i + 1) + ' / ' + pad(n), L.W - L.m, L.marca.y + lado * 0.3, {
      tamanho: Math.round(L.u * 0.026), peso: 600, cor: T.tinta3, align: 'right'
    });
  }

  function legenda(ctx, L, cena, tLocal, A) {
    const itens = cena._legendas || [];
    if (!itens.length) return;
    let atual = null;
    for (let i = 0; i < itens.length; i++) {
      if (tLocal >= itens[i].ini - 0.06 && tLocal < itens[i].fim) { atual = itens[i]; break; }
    }
    if (!atual) atual = tLocal < itens[0].ini ? itens[0] : itens[itens.length - 1];

    const k = U.clamp((tLocal - atual.ini + 0.10) / 0.16, 0, 1);
    const tam = Math.round(L.u * 0.042);
    ctx.save();
    ctx.font = U.pesoFonte(700, tam);
    const linhas = U.quebrar(ctx, atual.txt, L.legenda.w - Math.round(L.u * 0.06));
    const lh = tam * 1.22;
    const alt = linhas.length * lh + Math.round(L.u * 0.030);
    const larg = Math.min(
      L.legenda.w,
      Math.max.apply(null, linhas.map(l => ctx.measureText(l).width)) + Math.round(L.u * 0.062)
    );
    const cx = L.vertical ? L.W / 2 : L.legenda.x + larg / 2;
    const y = L.legenda.y + (L.legenda.h - alt) / 2;

    ctx.globalAlpha = 0.35 + k * 0.65;
    U.cartao(ctx, cx - larg / 2, y, larg, alt, alt / 2.6, {
      blur: 30, dy: 10, corSombra: 'rgba(10,21,38,0.08)'
    });
    ctx.globalAlpha = 1;
    ctx.font = U.pesoFonte(700, tam);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    linhas.forEach(function (l, i) {
      ctx.fillStyle = T.tinta;
      ctx.fillText(l, cx, y + Math.round(L.u * 0.015) + i * lh);
    });
    ctx.restore();
  }

  function barraProgresso(ctx, L, duracoes, atual, p, A) {
    const total = duracoes.reduce((s, d) => s + d, 0) || 1;
    const vao = Math.round(L.u * 0.008);
    const h = Math.round(L.u * 0.0072);
    const disponivel = L.progresso.w - vao * (duracoes.length - 1);
    let x = L.progresso.x;
    duracoes.forEach(function (d, i) {
      const w = (d / total) * disponivel;
      U.caminhoArredondado(ctx, x, L.progresso.y, w, h, h / 2);
      ctx.fillStyle = T.linhaForte;
      ctx.fill();
      const preench = i < atual ? 1 : i === atual ? p : 0;
      if (preench > 0) {
        U.caminhoArredondado(ctx, x, L.progresso.y, Math.max(h, w * preench), h, h / 2);
        ctx.fillStyle = A;
        ctx.fill();
      }
      x += w + vao;
    });
  }

  function guias(ctx, L, palco) {
    ctx.save();
    ctx.setLineDash([12, 12]);
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(27,69,232,0.35)';
    ctx.strokeRect(L.m, L.topo, L.W - L.m * 2, L.base - L.topo);
    ctx.strokeStyle = 'rgba(192,52,28,0.35)';
    ctx.strokeRect(palco.x, palco.y, palco.w, palco.h);
    ctx.restore();
  }

  /* ---------------------------------------------------------------
     Mídia própria (imagem ou vídeo) por cena
     --------------------------------------------------------------- */

  /* Exportação exata: cada quadro precisa do vídeo parado no tempo certo. */
  Motor.prototype.prepararQuadro = function (t) {
    const pos = this.cenaEm(t);
    if (!pos) return Promise.resolve();
    const el = this.midias[pos.i];
    if (!el || el.tagName !== 'VIDEO' || !el.duration || !isFinite(el.duration)) return Promise.resolve();
    const alvo = Math.min(el.duration - 0.03, pos.local % Math.max(0.2, el.duration));
    if (Math.abs(el.currentTime - alvo) < 0.006) return Promise.resolve();
    return new Promise(function (ok) {
      let pronto = false;
      const fim = function () {
        if (pronto) return;
        pronto = true;
        el.removeEventListener('seeked', fim);
        ok();
      };
      el.addEventListener('seeked', fim);
      setTimeout(fim, 500);
      try { el.currentTime = alvo; } catch (e) { fim(); }
    });
  };

  /* Prévia e gravação em tempo real: o vídeo da cena atual roda sozinho. */
  Motor.prototype.sincronizarMidias = function (t, tocando) {
    const pos = this.cenaEm(t);
    const chaves = Object.keys(this.midias);
    for (let j = 0; j < chaves.length; j++) {
      const i = Number(chaves[j]);
      const el = this.midias[i];
      if (!el || el.tagName !== 'VIDEO') continue;
      const atual = pos && i === pos.i;
      if (atual && tocando) {
        if (el.paused) {
          try {
            el.currentTime = Math.min(el.duration || 0, pos.local);
            const q = el.play();
            if (q && q.catch) q.catch(function () { /* sem gesto do usuário ainda */ });
          } catch (e) { /* segue mudo */ }
        }
      } else {
        if (!el.paused) el.pause();
        if (atual && !tocando && isFinite(el.duration)) {
          try { el.currentTime = Math.min(el.duration - 0.03, pos.local % Math.max(0.2, el.duration)); }
          catch (e) { /* ignora */ }
        }
      }
    }
  };

  /* ---------------------------------------------------------------
     Saídas de texto
     --------------------------------------------------------------- */
  function tempoSRT(s) {
    const ms = Math.round(s * 1000);
    const h = Math.floor(ms / 3600000);
    const m = Math.floor(ms / 60000) % 60;
    const seg = Math.floor(ms / 1000) % 60;
    const r = ms % 1000;
    const z = (v, n) => String(v).padStart(n, '0');
    return z(h, 2) + ':' + z(m, 2) + ':' + z(seg, 2) + ',' + z(r, 3);
  }

  Motor.prototype.srt = function () {
    const linhas = [];
    let n = 0;
    this.projeto.cenas.forEach((c, i) => {
      (c._legendas || []).forEach(function (l) {
        n++;
        linhas.push(String(n));
        linhas.push(tempoSRT(this.inicios[i] + l.ini) + ' --> ' + tempoSRT(this.inicios[i] + l.fim));
        linhas.push(l.txt);
        linhas.push('');
      }, this);
    });
    return linhas.join('\n');
  };

  /* Roteiro em duas colunas: o que se lê e o que se ouve. */
  Motor.prototype.roteiro = function () {
    const P = this.projeto;
    const out = ['# ' + (P.titulo || 'Vídeo'), '',
      'Formato: ' + P.formato + '  ·  Duração: ' + this.duracao.toFixed(1) + 's  ·  Cenas: ' + P.cenas.length, ''];
    P.cenas.forEach((c, i) => {
      out.push('## Cena ' + (i + 1) + ' — ' + (U.VISUAIS[c.visual] ? U.VISUAIS[c.visual].rotulo : c.visual) +
        ' (' + this.duracoes[i].toFixed(1) + 's)');
      out.push('NA TELA: ' + (c.titulo || '—') + (c.apoio ? ' | ' + c.apoio : ''));
      out.push('NARRAÇÃO: ' + (c.narracao || '—'));
      out.push('');
    });
    out.push('---', '', '## Só a narração (para gravar de uma vez)', '');
    out.push(P.cenas.map(c => c.narracao).filter(Boolean).join(' '));
    return out.join('\n');
  };

})(window.UMM);
