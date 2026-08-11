/* UMM Studio — visuais
   Biblioteca de CENAS CONCRETAS desenhadas em código (zero banco de imagens,
   zero licença, zero custo). Cada visual recebe o "palco" (um retângulo) e o
   progresso p (0..1) da cena, e devolve algo que se entende SEM áudio.

   Assinatura: desenhar(ctx, caixa, p, cena, A, d, midia)
     caixa = {x, y, w, h}   A = cor de acento    d = dados já lidos
     midia = <img>/<video> da cena, quando houver */

(function (U) {
  'use strict';

  const T = U.TEMA;

  /* Lê o campo "dados" da cena (texto chave: valor por linha). */
  U.lerDados = function (txt) {
    const o = { itens: [] };
    String(txt || '').split('\n').forEach(function (linha) {
      const i = linha.indexOf(':');
      if (i < 1) return;
      const chave = U.normalizar(linha.slice(0, i)).replace(/[^a-z0-9]/g, '');
      const valor = linha.slice(i + 1).trim();
      if (!chave) return;
      if (chave === 'itens') {
        o.itens = valor.split('|').map(function (parte) {
          const j = parte.indexOf('=');
          return j < 0
            ? { rotulo: parte.trim(), valor: null }
            : { rotulo: parte.slice(0, j).trim(), valor: parte.slice(j + 1).trim() };
        }).filter(function (x) { return x.rotulo || x.valor; });
      } else {
        o[chave] = valor;
      }
    });
    return o;
  };

  function nums(itens) {
    return itens.map(function (it) {
      /* "itens: 3 | 5 | 8" não tem "=", então o número está no rótulo. */
      const n = U.lerNumero(it.valor != null ? it.valor : it.rotulo);
      return n ? n.valor : 0;
    });
  }

  /* Telefone: moldura usada por várias cenas. Devolve a área útil da tela. */
  function moldura(ctx, cx, cy, larg, alt, k) {
    const r = larg * 0.11;
    const b = larg * 0.035;               /* espessura da borda, proporcional */
    ctx.save();
    ctx.globalAlpha = k;
    ctx.translate(0, (1 - k) * 26);
    U.cartao(ctx, cx - larg / 2, cy - alt / 2, larg, alt, r, { blur: 60, dy: 22, fundo: '#0A1526' });
    U.caminhoArredondado(ctx, cx - larg / 2 + b * 0.8, cy - alt / 2 + b * 0.8,
      larg - b * 1.6, alt - b * 1.6, r - b * 0.7);
    ctx.fillStyle = T.cartaoSuave;
    ctx.fill();
    /* alto-falante */
    U.caminhoArredondado(ctx, cx - larg * 0.13, cy - alt / 2 + b * 1.5,
      larg * 0.26, b * 0.55, b * 0.3);
    ctx.fillStyle = '#0A1526';
    ctx.fill();
    ctx.restore();
    return {
      x: cx - larg / 2 + b * 1.8, y: cy - alt / 2 + b * 3.2,
      w: larg - b * 3.6, h: alt - b * 5.0
    };
  }

  const V = {};
  U.VISUAIS = V;

  /* ============================================================
     1. NÚMERO — o KPI gigante que conta na tela
     ============================================================ */
  V.numero = {
    rotulo: 'Número grande',
    dica: 'Um dado só, enorme, contando. O visual mais forte para abrir.',
    exemplo: 'valor: R$ 1.240,00\nrotulo: é o que some por ano em tarifas\nnota: média de 4 tarifas mensais',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const k = U.ease.saida(U.faixa(p, 0.02, 0.62));
      const texto = U.animarNumero(d.valor || '0', k);
      const aj = U.ajustar(ctx, texto, {
        max: 200 * u, min: 90 * u, peso: 800, maxLargura: c.w - 90 * u, maxLinhas: 1
      });
      const cy = c.y + c.h * (d.rotulo ? 0.40 : 0.5);
      ctx.save();
      if ('letterSpacing' in ctx) ctx.letterSpacing = (-4 * u) + 'px';
      ctx.font = U.pesoFonte(800, aj.tamanho);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = A;
      ctx.globalAlpha = U.aparecer(p, 0, 0.2);
      ctx.fillText(texto, c.x + c.w / 2, cy);
      ctx.restore();

      if (d.rotulo) {
        const ar = U.ajustar(ctx, d.rotulo, {
          max: 50 * u, min: 34 * u, peso: 600, maxLargura: c.w - 140 * u, maxLinhas: 2
        });
        U.blocoTexto(ctx, ar, c.x + c.w / 2, cy + aj.tamanho * 0.62,
          { align: 'center', cor: T.tinta2, peso: 600, progresso: p, atraso: 0.22 });
      }
      if (d.nota) {
        U.texto(ctx, d.nota, c.x + c.w / 2, c.y + c.h - 54 * u, {
          tamanho: 30 * u, peso: 500, cor: T.tinta3, align: 'center',
          opacidade: U.aparecer(p, 0.4, 0.3)
        });
      }
    }
  };

  /* ============================================================
     2. LINHA — evolução no tempo
     ============================================================ */
  V.linha = {
    rotulo: 'Gráfico de linha',
    dica: 'Evolução ao longo do tempo. Use 4 a 7 pontos.',
    exemplo: 'itens: 2020=100 | 2021=112 | 2022=127 | 2023=139 | 2024=158\nsufixo: mil\ndestaque: +58% em 4 anos',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const pad = 56 * u;
      const g = { x: c.x + pad, y: c.y + pad * 0.9, w: c.w - pad * 2, h: c.h - pad * 2.4 };
      const it = d.itens.length ? d.itens : [{ rotulo: '1', valor: '1' }, { rotulo: '2', valor: '2' }];
      const vs = nums(it);
      const max = Math.max.apply(null, vs) * 1.12 || 1;
      const min = Math.min(0, Math.min.apply(null, vs));

      /* grade horizontal discreta */
      for (let i = 0; i <= 3; i++) {
        const y = g.y + (g.h * i) / 3;
        U.linhaH(ctx, g.x, y, g.w, i === 3 ? T.linhaForte : T.linha);
      }

      const px = i => g.x + (g.w * i) / Math.max(1, it.length - 1);
      const py = v => g.y + g.h - ((v - min) / (max - min || 1)) * g.h;
      const k = U.ease.saida(U.faixa(p, 0.06, 0.72));
      const alcance = k * (it.length - 1);

      const pts = [];
      for (let i = 0; i < it.length; i++) pts.push([px(i), py(vs[i])]);

      function traçar(ate) {
        ctx.beginPath();
        ctx.moveTo(pts[0][0], pts[0][1]);
        const inteiro = Math.floor(ate);
        for (let i = 1; i <= inteiro; i++) ctx.lineTo(pts[i][0], pts[i][1]);
        const f = ate - inteiro;
        if (f > 0 && inteiro + 1 < pts.length) {
          ctx.lineTo(U.lerp(pts[inteiro][0], pts[inteiro + 1][0], f),
                     U.lerp(pts[inteiro][1], pts[inteiro + 1][1], f));
        }
      }

      /* área */
      const fim = [
        U.lerp(pts[Math.floor(alcance)][0], (pts[Math.ceil(alcance)] || pts[pts.length - 1])[0], alcance % 1),
        U.lerp(pts[Math.floor(alcance)][1], (pts[Math.ceil(alcance)] || pts[pts.length - 1])[1], alcance % 1)
      ];
      ctx.save();
      traçar(alcance);
      ctx.lineTo(fim[0], g.y + g.h);
      ctx.lineTo(pts[0][0], g.y + g.h);
      ctx.closePath();
      const grad = ctx.createLinearGradient(0, g.y, 0, g.y + g.h);
      grad.addColorStop(0, A + '2E');
      grad.addColorStop(1, A + '00');
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.restore();

      /* linha */
      ctx.save();
      ctx.strokeStyle = A;
      ctx.lineWidth = 8 * u;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      traçar(alcance);
      ctx.stroke();
      ctx.restore();

      /* ponto final + valor */
      ctx.save();
      ctx.fillStyle = '#fff';
      ctx.strokeStyle = A;
      ctx.lineWidth = 8 * u;
      ctx.beginPath();
      ctx.arc(fim[0], fim[1], 15 * u, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.restore();

      if (k > 0.9 && d.destaque) {
        const altP = 62 * u;
        ctx.font = U.pesoFonte(600, 32 * u);
        const largP = ctx.measureText(d.destaque).width + altP * 0.9;
        const cxP = U.clamp(fim[0], c.x + largP / 2, c.x + c.w - largP / 2);
        const cyP = Math.max(c.y + altP, fim[1] - 96 * u);
        U.pilula(ctx, cxP, cyP, d.destaque, {
          align: 'center', altura: altP, tamanho: 32 * u, fundo: A, cor: '#fff'
        });
      }

      /* eixo x */
      it.forEach(function (item, i) {
        U.texto(ctx, item.rotulo, px(i), g.y + g.h + 22 * u, {
          tamanho: 28 * u, peso: 600, cor: T.tinta3, align: 'center',
          opacidade: U.aparecer(p, 0.1 + i * 0.03, 0.3)
        });
      });
      if (d.sufixo) {
        U.texto(ctx, d.sufixo, g.x, c.y + 14 * u, { tamanho: 26 * u, peso: 600, cor: T.tinta3 });
      }
    }
  };

  /* ============================================================
     3. BARRAS — comparação entre poucas opções
     ============================================================ */
  V.barras = {
    rotulo: 'Barras comparativas',
    dica: 'Compare 2 a 5 opções. A maior ganha o acento.',
    exemplo: 'itens: Poupança=6,2 | CDB 100% CDI=11,4 | Tesouro Selic=10,9\nsufixo: % ao ano\nmelhor: maior',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const it = d.itens.slice(0, 5);
      if (!it.length) return;
      const vs = nums(it);
      const max = Math.max.apply(null, vs) || 1;
      const melhorIdx = d.melhor === 'menor' ? vs.indexOf(Math.min.apply(null, vs)) : vs.indexOf(max);
      const alturaLinha = Math.min(112 * u, (c.h - 44 * u) / it.length);
      const y0 = c.y + (c.h - 44 * u - alturaLinha * it.length) / 2;
      const rotW = c.w * 0.30;
      const valW = c.w * 0.17;
      const barX = c.x + rotW + 28 * u;
      const barMax = c.w - rotW - 28 * u - valW;

      it.forEach(function (item, i) {
        const y = y0 + i * alturaLinha;
        const k = U.ease.saida(U.faixa(p, 0.08 + i * 0.09, 0.55 + i * 0.09));
        const destaque = i === melhorIdx;
        const cor = destaque ? A : T.linhaForte;
        const alt = alturaLinha * 0.52;

        U.texto(ctx, item.rotulo, c.x + rotW, y + alturaLinha / 2, {
          tamanho: 34 * u, peso: destaque ? 700 : 600,
          cor: destaque ? T.tinta : T.tinta2, align: 'right', baseline: 'middle',
          opacidade: U.aparecer(p, 0.05 + i * 0.07, 0.25)
        });

        U.caminhoArredondado(ctx, barX, y + (alturaLinha - alt) / 2, barMax, alt, alt / 2);
        ctx.fillStyle = T.cartaoSuave;
        ctx.fill();

        const larg = Math.max(alt, barMax * (vs[i] / max) * k);
        U.caminhoArredondado(ctx, barX, y + (alturaLinha - alt) / 2, larg, alt, alt / 2);
        ctx.fillStyle = cor;
        ctx.fill();

        U.texto(ctx, item.valor != null ? item.valor : item.rotulo,
          c.x + c.w, y + alturaLinha / 2, {
            tamanho: 34 * u, peso: 700, align: 'right', baseline: 'middle',
            cor: destaque ? A : T.tinta2, opacidade: U.faixa(k, 0.7, 1)
          });
      });
      if (d.sufixo) {
        U.texto(ctx, d.sufixo, c.x + c.w, c.y + c.h - 30 * u, {
          tamanho: 26 * u, peso: 600, cor: T.tinta3, align: 'right'
        });
      }
    }
  };

  /* ============================================================
     4. COMPARATIVO — A contra B, lado a lado
     ============================================================ */
  V.comparativo = {
    rotulo: 'A contra B',
    dica: 'Dois caminhos, dois números. Ideal para "antes e depois".',
    exemplo: 'aRotulo: Parcelado no cartão\naValor: R$ 1.418\nbRotulo: À vista com desconto\nbValor: R$ 1.050\nvence: b',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const vao = 32 * u;
      const larg = (c.w - vao) / 2;
      const lados = [
        { rot: d.arotulo || 'Opção A', val: d.avalor || '—', vence: d.vence === 'a', x: c.x },
        { rot: d.brotulo || 'Opção B', val: d.bvalor || '—', vence: d.vence !== 'a', x: c.x + larg + vao }
      ];
      lados.forEach(function (l, i) {
        const k = U.aparecer(p, 0.05 + i * 0.12, 0.32);
        ctx.save();
        ctx.globalAlpha = k;
        ctx.translate((1 - k) * (i === 0 ? -30 : 30) * u, 0);
        const corFundo = l.vence ? A : T.cartao;
        U.cartao(ctx, l.x, c.y, larg, c.h, 36 * u, {
          fundo: corFundo, borda: l.vence ? false : T.linha,
          blur: l.vence ? 60 : 30, dy: l.vence ? 20 : 10
        });
        const tintaP = l.vence ? 'rgba(255,255,255,0.82)' : T.tinta2;
        const tintaF = l.vence ? '#FFFFFF' : T.tinta;

        const ar = U.ajustar(ctx, l.rot, {
          max: 36 * u, min: 26 * u, peso: 600, maxLargura: larg - 60 * u, maxLinhas: 2
        });
        U.blocoTexto(ctx, ar, l.x + larg / 2, c.y + 46 * u,
          { align: 'center', cor: tintaP, peso: 600 });

        const av = U.ajustar(ctx, l.val, {
          max: 88 * u, min: 46 * u, peso: 800, maxLargura: larg - 50 * u, maxLinhas: 1
        });
        ctx.save();
        ctx.font = U.pesoFonte(800, av.tamanho);
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = tintaF;
        ctx.fillText(l.val, l.x + larg / 2, c.y + c.h * 0.58);
        ctx.restore();

        if (l.vence) {
          U.check(ctx, l.x + larg / 2, c.y + c.h - 62 * u, 26 * u, '#FFFFFF',
            U.faixa(p, 0.45, 0.7));
        }
        ctx.restore();
      });
    }
  };

  /* ============================================================
     5. CARTÃO — plástico premium
     ============================================================ */
  V.cartao = {
    rotulo: 'Cartão',
    dica: 'Fatura, anuidade, limite, cashback. Metal escovado, vidro e reflexo de estúdio.',
    exemplo: 'banco: Seu banco\nfinal: 4417\nrotulo: Fatura fechada\nvalor: R$ 3.287,40',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const reservaRotulo = d.valor ? 200 * u : 30 * u;
      const cw = Math.min(c.w * 0.64, 560 * u, (c.h - reservaRotulo) / 0.92);
      const ch = cw * 0.63;
      const cx = c.x + c.w / 2, cy = c.y + ch / 2 + 14 * u;
      const k = U.ease.firme(U.faixa(p, 0.03, 0.42));
      const escuro = T.tom === 'escuro';

      /* o corpo do cartão, isolado para poder ser desenhado de novo no reflexo */
      function corpo(g, ox, oy) {
        const x = ox - cw / 2, y = oy - ch / 2, r = 34 * u;
        U.caminhoArredondado(g, x, y, cw, ch, r);
        const base = g.createLinearGradient(x, y, x + cw, y + ch);
        base.addColorStop(0, escuro ? '#3A4048' : '#2C3138');
        base.addColorStop(0.5, escuro ? '#22272D' : '#161A1F');
        base.addColorStop(1, escuro ? '#31373E' : '#23282E');
        g.fillStyle = base;
        g.fill();

        g.save();
        U.caminhoArredondado(g, x, y, cw, ch, r);
        g.clip();
        /* verniz diagonal */
        const verniz = g.createLinearGradient(x, y, x + cw * 0.7, y + ch);
        verniz.addColorStop(0, 'rgba(255,255,255,0.16)');
        verniz.addColorStop(0.42, 'rgba(255,255,255,0.02)');
        verniz.addColorStop(1, 'rgba(255,255,255,0.09)');
        g.fillStyle = verniz;
        g.fillRect(x, y, cw, ch);
        /* leve calor do acento, canto inferior direito */
        const calor = g.createRadialGradient(x + cw * 0.9, y + ch, 0, x + cw * 0.9, y + ch, cw * 0.7);
        calor.addColorStop(0, A + '4D');
        calor.addColorStop(1, A + '00');
        g.fillStyle = calor;
        g.fillRect(x, y, cw, ch);
        g.restore();

        /* borda de luz */
        U.caminhoArredondado(g, x + 1, y + 1, cw - 2, ch - 2, r - 1);
        g.strokeStyle = 'rgba(255,255,255,0.20)';
        g.lineWidth = 2 * u;
        g.stroke();

        /* chip em metal escovado */
        U.metalEscovado(g, x + 44 * u, y + 84 * u, 70 * u, 54 * u, 10 * u,
          { claro: '#E7D6A4', escuro: '#A98A3F' });
        g.save();
        g.strokeStyle = 'rgba(0,0,0,0.30)';
        g.lineWidth = 1.5 * u;
        for (let i = 1; i < 3; i++) {
          g.beginPath();
          g.moveTo(x + 44 * u, y + 84 * u + (54 * u * i) / 3);
          g.lineTo(x + 114 * u, y + 84 * u + (54 * u * i) / 3);
          g.stroke();
        }
        g.restore();

        const numero = '••••  ••••  ••••  ' + (d.final || '0000');
        const an = U.ajustar(g, numero, {
          max: 34 * u, min: 20 * u, peso: 600, maxLargura: cw - 88 * u, maxLinhas: 1
        });
        U.blocoTexto(g, an, x + 44 * u, y + ch - 100 * u,
          { peso: 600, cor: 'rgba(255,255,255,0.94)', tracking: 1.5 });
        U.texto(g, (d.banco || 'Banco').toUpperCase(), x + 44 * u, y + ch - 52 * u, {
          tamanho: 22 * u, peso: 600, cor: 'rgba(255,255,255,0.52)', tracking: 3
        });
      }

      ctx.save();
      ctx.globalAlpha = Math.min(1, k * 1.4);
      ctx.translate(cx, cy);
      ctx.rotate((1 - k) * -0.05);
      ctx.translate(0, (1 - k) * 40 * u);

      U.sombraContato(ctx, 0, ch / 2 + 26 * u, cw * 1.05, 48 * u, escuro ? 0.5 : 0.3);
      U.reflexo(ctx, -cw / 2, -ch / 2, cw, ch, 14 * u, function (g) { corpo(g, 0, 0); }, 0.38);

      ctx.save();
      ctx.shadowColor = T.sombraForte;
      ctx.shadowBlur = 70 * u;
      ctx.shadowOffsetY = 26 * u;
      corpo(ctx, 0, 0);
      ctx.restore();

      /* a luz atravessa o cartão uma vez, no meio da cena */
      U.brilhoVidro(ctx, -cw / 2, -ch / 2, cw, ch, 34 * u,
        U.faixa(p, 0.30, 0.68), 0.26);
      ctx.restore();

      if (d.valor) {
        const ky = U.aparecer(p, 0.42, 0.3);
        U.texto(ctx, d.rotulo || 'Total', cx, c.y + c.h - 122 * u, {
          tamanho: 30 * u, peso: 600, cor: T.tinta3, align: 'center', opacidade: ky
        });
        const val = U.animarNumero(d.valor, U.ease.saida(U.faixa(p, 0.45, 0.85)));
        U.texto(ctx, val, cx, c.y + c.h - 78 * u, {
          tamanho: 62 * u, peso: 800, cor: T.tinta, align: 'center', opacidade: ky
        });
      }
    }
  };

  /* ============================================================
     6. PIX — celular, QR e confirmação
     ============================================================ */
  V.pix = {
    rotulo: 'Pix no celular',
    dica: 'Transferência, agendamento, comprovante.',
    exemplo: 'valor: R$ 250,00\npara: Reserva de emergência\nsituacao: Agendado para todo dia 5',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const alt = c.h * 0.96, larg = Math.min(alt * 0.5, c.w * 0.36);
      const tela = moldura(ctx, c.x + larg / 2 + 10 * u, c.y + c.h / 2, larg, alt,
        U.aparecer(p, 0.02, 0.3));

      /* QR desenhado de forma determinística */
      const qr = Math.min(tela.w * 0.72, tela.h * 0.46);
      const qx = tela.x + (tela.w - qr) / 2, qy = tela.y + tela.h * 0.06;
      U.cartao(ctx, qx - 14 * u, qy - 14 * u, qr + 28 * u, qr + 28 * u, 18 * u, { blur: 18, dy: 6 });
      const n = 13, cel = qr / n;
      const kq = U.faixa(p, 0.1, 0.5);
      ctx.save();
      ctx.fillStyle = T.tinta;
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
          if ((i * 7 + j * 13 + ((i * j) % 5)) % 3 === 0 && (i + j) / (2 * n) < kq + 0.1) {
            ctx.fillRect(qx + i * cel, qy + j * cel, cel * 0.86, cel * 0.86);
          }
        }
      }
      /* âncoras do QR */
      [[0, 0], [n - 3, 0], [0, n - 3]].forEach(function (a) {
        ctx.fillStyle = T.tinta;
        ctx.fillRect(qx + a[0] * cel, qy + a[1] * cel, cel * 3, cel * 3);
        ctx.fillStyle = '#fff';
        ctx.fillRect(qx + (a[0] + 0.6) * cel, qy + (a[1] + 0.6) * cel, cel * 1.8, cel * 1.8);
        ctx.fillStyle = T.tinta;
        ctx.fillRect(qx + (a[0] + 1) * cel, qy + (a[1] + 1) * cel, cel, cel);
      });
      ctx.restore();

      const avl = U.ajustar(ctx, d.valor || 'R$ 0,00', {
        max: 44 * u, min: 26 * u, peso: 800, maxLargura: tela.w - 16 * u, maxLinhas: 1
      });
      U.blocoTexto(ctx, avl, tela.x + tela.w / 2, tela.y + tela.h * 0.62,
        { align: 'center', cor: T.tinta, peso: 800, opacidade: U.aparecer(p, 0.3, 0.25) });
      const apr = U.ajustar(ctx, d.para || 'Destino', {
        max: 26 * u, min: 19 * u, peso: 600, maxLargura: tela.w - 16 * u, maxLinhas: 2
      });
      U.blocoTexto(ctx, apr, tela.x + tela.w / 2, tela.y + tela.h * 0.62 + avl.altura + 12 * u,
        { align: 'center', cor: T.tinta3, peso: 600, opacidade: U.aparecer(p, 0.34, 0.25) });

      /* confirmação à direita */
      const bx = c.x + larg + 60 * u, bw = c.x + c.w - (c.x + larg + 60 * u);
      const kb = U.aparecer(p, 0.5, 0.3);
      ctx.save();
      ctx.globalAlpha = kb;
      ctx.translate(0, (1 - kb) * 24 * u);
      U.cartao(ctx, bx, c.y + c.h * 0.30, bw, c.h * 0.40, 30 * u, { borda: T.linha, blur: 34 });
      U.check(ctx, bx + bw / 2, c.y + c.h * 0.30 + c.h * 0.14, 46 * u, A, U.faixa(p, 0.55, 0.8));
      const at = U.ajustar(ctx, d.situacao || 'Pix concluído', {
        max: 34 * u, min: 24 * u, peso: 700, maxLargura: bw - 48 * u, maxLinhas: 3
      });
      U.blocoTexto(ctx, at, bx + bw / 2, c.y + c.h * 0.30 + c.h * 0.24,
        { align: 'center', cor: T.tinta, peso: 700 });
      ctx.restore();
    }
  };

  /* ============================================================
     7. BOLETO — documento com código de barras e carimbo
     ============================================================ */
  V.boleto = {
    rotulo: 'Boleto / fatura',
    dica: 'Vencimento, juros por atraso, desconto à vista.',
    exemplo: 'valor: R$ 842,90\nvencimento: 10/09\nsituacao: VENCIDO\ntom: alerta',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const w = Math.min(c.w * 0.74, 620 * u), h = c.h * 0.9;
      const x = c.x + (c.w - w) / 2, y = c.y + (c.h - h) / 2;
      const k = U.aparecer(p, 0.02, 0.3);
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 30 * u);
      U.cartao(ctx, x, y, w, h, 26 * u, { blur: 54, dy: 20 });

      U.texto(ctx, 'PAGAMENTO', x + 40 * u, y + 38 * u, { tamanho: 24 * u, peso: 700, cor: T.tinta3, tracking: 3 });
      U.linhaH(ctx, x + 40 * u, y + 80 * u, w - 80 * u);

      U.texto(ctx, 'Vencimento', x + 40 * u, y + 106 * u, { tamanho: 26 * u, peso: 600, cor: T.tinta3 });
      U.texto(ctx, d.vencimento || '--/--', x + w - 40 * u, y + 102 * u, {
        tamanho: 32 * u, peso: 700, cor: T.tinta, align: 'right'
      });
      U.texto(ctx, 'Valor', x + 40 * u, y + 168 * u, { tamanho: 26 * u, peso: 600, cor: T.tinta3 });
      U.texto(ctx, U.animarNumero(d.valor || 'R$ 0,00', U.ease.saida(U.faixa(p, 0.15, 0.6))),
        x + w - 40 * u, y + 152 * u, { tamanho: 54 * u, peso: 800, cor: T.tinta, align: 'right' });

      /* código de barras */
      const by = y + h - 108 * u;
      ctx.save();
      ctx.fillStyle = T.tinta;
      let bx = x + 40 * u;
      let semente = 7;
      while (bx < x + w - 40 * u) {
        semente = (semente * 31 + 17) % 97;
        const lw = 3 * u + (semente % 4) * 2.6 * u;
        if (semente % 3) ctx.fillRect(bx, by, lw, 56 * u);
        bx += lw + 4 * u;
      }
      ctx.restore();
      ctx.restore();

      /* carimbo */
      if (d.situacao) {
        const cor = (d.tom === 'alerta') ? T.alerta : A;
        const ks = U.ease.firme(U.faixa(p, 0.45, 0.72));
        ctx.save();
        ctx.globalAlpha = Math.min(1, ks * 1.6);
        ctx.translate(x + w * 0.58, y + h * 0.68);
        ctx.rotate(-0.18);
        ctx.scale(0.8 + ks * 0.2, 0.8 + ks * 0.2);
        ctx.font = U.pesoFonte(800, 46 * u);
        const lw2 = ctx.measureText(d.situacao).width + 56 * u;
        U.caminhoArredondado(ctx, -lw2 / 2, -42 * u, lw2, 84 * u, 14 * u);
        ctx.strokeStyle = cor;
        ctx.lineWidth = 6 * u;
        ctx.stroke();
        ctx.fillStyle = cor + '1A';
        ctx.fill();
        ctx.fillStyle = cor;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(d.situacao, 0, 2 * u);
        ctx.restore();
      }
    }
  };

  /* ============================================================
     8. EXTRATO — linhas de lançamento aparecendo
     ============================================================ */
  V.extrato = {
    rotulo: 'Extrato bancário',
    dica: 'Mostre para onde o dinheiro foi. Negativos em vermelho.',
    exemplo: 'itens: Assinatura de streaming=-39,90 | Tarifa de pacote=-34,00 | Seguro não usado=-27,50 | App esquecido=-19,90\nrodape: R$ 121,30 por mês',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const it = d.itens.slice(0, 5);
      const w = Math.min(c.w, 860 * u);
      const x = c.x + (c.w - w) / 2;
      const temRodape = !!d.rodape;
      const hLinha = Math.min(96 * u, (c.h - (temRodape ? 130 * u : 40 * u)) / Math.max(1, it.length));
      const alturaCartao = hLinha * it.length + 44 * u + (temRodape ? 106 * u : 0);
      const y = c.y + (c.h - alturaCartao) / 2;

      U.cartao(ctx, x, y, w, alturaCartao, 32 * u, { blur: 48, dy: 18, borda: T.linha });

      it.forEach(function (item, i) {
        const k = U.aparecer(p, 0.06 + i * 0.11, 0.3);
        if (k <= 0) return;
        const ly = y + 22 * u + i * hLinha;
        ctx.save();
        ctx.globalAlpha = k;
        ctx.translate((1 - k) * 26 * u, 0);
        const n = U.lerNumero(item.valor);
        const negativo = n && n.valor < 0;
        U.texto(ctx, item.rotulo, x + 40 * u, ly + hLinha / 2, {
          tamanho: 33 * u, peso: 600, cor: T.tinta, baseline: 'middle'
        });
        U.texto(ctx, item.valor == null ? '' : String(item.valor).replace('-', '− '),
          x + w - 40 * u, ly + hLinha / 2, {
            tamanho: 34 * u, peso: 700, align: 'right', baseline: 'middle',
            cor: negativo ? T.alerta : T.acento
          });
        if (i < it.length - 1) U.linhaH(ctx, x + 40 * u, ly + hLinha - 1, w - 80 * u);
        ctx.restore();
      });

      if (temRodape) {
        const ky = U.aparecer(p, 0.62, 0.3);
        const ry = y + 22 * u + it.length * hLinha;
        ctx.save();
        ctx.globalAlpha = ky;
        U.caminhoArredondado(ctx, x + 20 * u, ry + 8 * u, w - 40 * u, 84 * u, 20 * u);
        ctx.fillStyle = A + '14';
        ctx.fill();
        U.texto(ctx, 'Some tudo', x + 48 * u, ry + 50 * u, {
          tamanho: 28 * u, peso: 600, cor: T.tinta2, baseline: 'middle'
        });
        U.texto(ctx, d.rodape, x + w - 48 * u, ry + 50 * u, {
          tamanho: 40 * u, peso: 800, cor: A, align: 'right', baseline: 'middle'
        });
        ctx.restore();
      }
    }
  };

  /* ============================================================
     9. NOTIFICAÇÃO — push no celular
     ============================================================ */
  V.notificacao = {
    rotulo: 'Notificação no celular',
    dica: 'Cobrança surpresa, alerta de gasto, lembrete.',
    exemplo: 'app: Seu banco\ntitulo: Compra aprovada\ncorpo: R$ 129,90 em assinatura anual\nhora: agora',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const alt = c.h * 0.96, larg = Math.min(alt * 0.5, c.w * 0.46);
      const tela = moldura(ctx, c.x + c.w / 2, c.y + c.h / 2, larg, alt, U.aparecer(p, 0.02, 0.3));

      U.texto(ctx, '09:41', tela.x + tela.w / 2, tela.y + tela.h * 0.10, {
        tamanho: Math.min(78 * u, tela.h * 0.14), peso: 300, cor: T.tinta3, align: 'center'
      });

      const k = U.ease.firme(U.faixa(p, 0.22, 0.55));
      const nw = tela.w - 24 * u;
      const pad = 20 * u;
      const tApp = Math.min(24 * u, nw * 0.075);

      /* mede antes de posicionar: a altura do cartão vem do conteúdo */
      const at = U.ajustar(ctx, d.titulo || 'Aviso', {
        max: 32 * u, min: 20 * u, peso: 700, maxLargura: nw - pad * 2, maxLinhas: 2
      });
      const ac = U.ajustar(ctx, d.corpo || '', {
        max: 26 * u, min: 17 * u, peso: 500, maxLargura: nw - pad * 2, maxLinhas: 2
      });
      const yApp = pad;
      const yTitulo = yApp + tApp + 14 * u;
      const yCorpo = yTitulo + at.altura + 6 * u;
      const nh = yCorpo + (d.corpo ? ac.altura : 0) + pad;
      const nx = tela.x + 12 * u;
      const ny = tela.y + Math.max(tela.h * 0.30, tela.h - nh - 40 * u) + (1 - k) * -60 * u;

      ctx.save();
      ctx.globalAlpha = Math.min(1, k * 1.5);
      U.cartao(ctx, nx, ny, nw, nh, 22 * u, { blur: 34, dy: 12 });
      const lado = tApp * 1.5;
      U.caminhoArredondado(ctx, nx + pad, ny + yApp - lado * 0.18, lado, lado, lado * 0.28);
      ctx.fillStyle = A;
      ctx.fill();
      U.texto(ctx, d.app || 'Banco', nx + pad + lado + 12 * u, ny + yApp,
        { tamanho: tApp, peso: 700, cor: T.tinta3 });
      U.texto(ctx, d.hora || 'agora', nx + nw - pad, ny + yApp,
        { tamanho: tApp * 0.9, peso: 600, cor: T.tinta3, align: 'right' });
      U.blocoTexto(ctx, at, nx + pad, ny + yTitulo, { cor: T.tinta, peso: 700 });
      if (d.corpo) U.blocoTexto(ctx, ac, nx + pad, ny + yCorpo, { cor: T.tinta2, peso: 500 });
      ctx.restore();
    }
  };

  /* ============================================================
     10. CHECKLIST — passos marcados um a um
     ============================================================ */
  V.checklist = {
    rotulo: 'Lista de passos',
    dica: 'Até 4 passos. Marca um por vez, no ritmo da narração.',
    exemplo: 'itens: Liste as assinaturas | Cancele as não usadas | Agende o Pix da reserva',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const it = d.itens.slice(0, 4);
      if (!it.length) return;
      const h = Math.min(120 * u, c.h / it.length);
      const w = Math.min(c.w, 840 * u);
      const x = c.x + (c.w - w) / 2;
      const y0 = c.y + (c.h - h * it.length) / 2;

      it.forEach(function (item, i) {
        const ini = 0.06 + i * (0.72 / it.length);
        const k = U.aparecer(p, ini, 0.26);
        if (k <= 0) return;
        const y = y0 + i * h;
        ctx.save();
        ctx.globalAlpha = k;
        ctx.translate((1 - k) * 24 * u, 0);
        U.cartao(ctx, x, y + 6 * u, w, h - 14 * u, 24 * u, { blur: 26, dy: 8, borda: T.linha });
        U.check(ctx, x + 54 * u, y + h / 2 - 1 * u, 30 * u, A, U.faixa(p, ini + 0.10, ini + 0.26));
        const at = U.ajustar(ctx, item.rotulo, {
          max: 38 * u, min: 26 * u, peso: 600, maxLargura: w - 150 * u, maxLinhas: 2
        });
        U.blocoTexto(ctx, at, x + 104 * u, y + h / 2 - at.altura / 2 - 2 * u, { cor: T.tinta, peso: 600 });
        ctx.restore();
      });
    }
  };

  /* ============================================================
     11. JUROS — o efeito do tempo, em colunas
     ============================================================ */
  V.juros = {
    rotulo: 'Juros compostos',
    dica: 'Aporte, taxa e prazo. A última coluna carrega o número.',
    exemplo: 'inicial: 500\naporte: 500\ntaxa: 0,9\nanos: 10\nrotulo: aportando R$ 500 por mês a 0,9% ao mês',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const inicial = (U.lerNumero(d.inicial) || { valor: 0 }).valor;
      const aporte = (U.lerNumero(d.aporte) || { valor: 0 }).valor;
      const taxa = (U.lerNumero(d.taxa) || { valor: 0.8 }).valor / 100;
      const anos = Math.max(2, Math.min(20, Math.round((U.lerNumero(d.anos) || { valor: 10 }).valor)));

      const serie = [];
      let saldo = inicial;
      for (let a = 1; a <= anos; a++) {
        for (let m = 0; m < 12; m++) saldo = saldo * (1 + taxa) + aporte;
        serie.push(saldo);
      }
      const max = serie[serie.length - 1] || 1;
      const k = U.ease.saida(U.faixa(p, 0.06, 0.72));

      const pad = 40 * u;
      const g = { x: c.x + pad, y: c.y + 96 * u, w: c.w - pad * 2, h: c.h - 216 * u };
      const bw = (g.w / anos) * 0.62;

      serie.forEach(function (v, i) {
        const kb = U.clamp((k * anos - i) / 0.9, 0, 1);
        if (kb <= 0) return;
        const alt = g.h * (v / max) * kb;
        const x = g.x + (g.w * (i + 0.5)) / anos - bw / 2;
        U.caminhoArredondado(ctx, x, g.y + g.h - alt, bw, alt, Math.min(10 * u, bw / 2));
        ctx.fillStyle = i === anos - 1 ? A : A + '38';
        ctx.fill();
      });
      U.linhaH(ctx, g.x, g.y + g.h, g.w, T.linhaForte);
      U.texto(ctx, 'ano 1', g.x, g.y + g.h + 14 * u, { tamanho: 26 * u, peso: 600, cor: T.tinta3 });
      U.texto(ctx, 'ano ' + anos, g.x + g.w, g.y + g.h + 14 * u, {
        tamanho: 26 * u, peso: 600, cor: T.tinta3, align: 'right'
      });

      const total = U.moedaBR(max * k).replace(/,\d\d$/, '');
      U.texto(ctx, total, c.x + c.w / 2, c.y + 16 * u, {
        tamanho: 66 * u, peso: 800, cor: T.tinta, align: 'center',
        opacidade: U.aparecer(p, 0.08, 0.25)
      });
      if (d.rotulo) {
        U.texto(ctx, d.rotulo, c.x + c.w / 2, c.y + c.h - 36 * u, {
          tamanho: 28 * u, peso: 600, cor: T.tinta3, align: 'center',
          opacidade: U.aparecer(p, 0.5, 0.3)
        });
      }
    }
  };

  /* ============================================================
     12. COFRE — reserva guardada
     ============================================================ */
  V.cofre = {
    rotulo: 'Cofre / reserva',
    dica: 'Reserva de emergência, dinheiro guardado, meta.',
    exemplo: 'valor: R$ 18.000\nrotulo: 6 meses de custo fixo\nmeta: 72',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const lado = Math.min(c.h * 0.86, c.w * 0.42);
      const x = c.x + c.w * 0.06, y = c.y + (c.h - lado) / 2;
      const k = U.aparecer(p, 0.02, 0.32);
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 26 * u);
      U.cartao(ctx, x, y, lado, lado, 34 * u, { blur: 56, dy: 22, fundo: T.tinta });
      U.caminhoArredondado(ctx, x + 26 * u, y + 26 * u, lado - 52 * u, lado - 52 * u, 22 * u);
      ctx.strokeStyle = 'rgba(255,255,255,0.16)';
      ctx.lineWidth = 3 * u;
      ctx.stroke();
      /* volante girando */
      const cxr = x + lado / 2, cyr = y + lado / 2, r = lado * 0.22;
      ctx.save();
      ctx.translate(cxr, cyr);
      ctx.rotate(U.ease.suave(U.faixa(p, 0.1, 0.65)) * Math.PI * 1.6);
      ctx.strokeStyle = '#D8B25E';
      ctx.lineWidth = 10 * u;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.arc(0, 0, r, 0, Math.PI * 2);
      ctx.stroke();
      for (let i = 0; i < 4; i++) {
        ctx.save();
        ctx.rotate((i * Math.PI) / 2);
        ctx.beginPath();
        ctx.moveTo(0, -r * 0.35);
        ctx.lineTo(0, -r * 1.32);
        ctx.stroke();
        ctx.restore();
      }
      ctx.restore();
      ctx.restore();

      /* painel à direita */
      const px = c.x + c.w * 0.53, pw = c.w * 0.42;
      const kp = U.aparecer(p, 0.3, 0.3);
      const val = U.animarNumero(d.valor || 'R$ 0', U.ease.saida(U.faixa(p, 0.3, 0.8)));
      const avl = U.ajustar(ctx, val, {
        max: 76 * u, min: 42 * u, peso: 800, maxLargura: pw, maxLinhas: 1
      });
      U.blocoTexto(ctx, avl, px, c.y + c.h * 0.24, { cor: T.tinta, peso: 800, opacidade: kp });
      if (d.rotulo) {
        const ar = U.ajustar(ctx, d.rotulo, {
          max: 32 * u, min: 24 * u, peso: 600, maxLargura: pw, maxLinhas: 2
        });
        U.blocoTexto(ctx, ar, px, c.y + c.h * 0.24 + avl.altura + 14 * u,
          { cor: T.tinta2, peso: 600, opacidade: kp });
      }
      const meta = (U.lerNumero(d.meta) || { valor: 100 }).valor / 100;
      const barY = c.y + c.h * 0.66;
      U.caminhoArredondado(ctx, px, barY, pw, 22 * u, 11 * u);
      ctx.fillStyle = T.linha;
      ctx.fill();
      U.caminhoArredondado(ctx, px, barY, pw * meta * U.ease.saida(U.faixa(p, 0.4, 0.85)), 22 * u, 11 * u);
      ctx.fillStyle = A;
      ctx.fill();
      U.texto(ctx, Math.round(meta * 100) + '% da meta', px, barY + 36 * u, {
        tamanho: 26 * u, peso: 600, cor: T.tinta3, opacidade: kp
      });
    }
  };

  /* ============================================================
     13. ALERTA — golpe, pegadinha, letra miúda
     ============================================================ */
  V.alerta = {
    rotulo: 'Alerta / pegadinha',
    dica: 'Use no máximo uma vez por vídeo. Vermelho é caro.',
    exemplo: 'titulo: Como reconhecer\nitens: Pedem Pix para liberar crédito | Prometem retorno garantido | Somem quando você pergunta o CNPJ',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const cor = T.alerta;
      const escudoR = Math.min(c.h * 0.30, 130 * u);
      const cx = c.x + c.w / 2;
      const k = U.ease.firme(U.faixa(p, 0.02, 0.36));
      ctx.save();
      ctx.globalAlpha = Math.min(1, k * 1.4);
      ctx.translate(cx, c.y + escudoR * 1.05);
      ctx.scale(0.9 + k * 0.1, 0.9 + k * 0.1);
      ctx.beginPath();
      ctx.moveTo(0, -escudoR);
      ctx.lineTo(escudoR * 0.82, -escudoR * 0.6);
      ctx.lineTo(escudoR * 0.82, escudoR * 0.16);
      ctx.quadraticCurveTo(escudoR * 0.82, escudoR * 0.82, 0, escudoR);
      ctx.quadraticCurveTo(-escudoR * 0.82, escudoR * 0.82, -escudoR * 0.82, escudoR * 0.16);
      ctx.lineTo(-escudoR * 0.82, -escudoR * 0.6);
      ctx.closePath();
      ctx.fillStyle = T.alertaSuave;
      ctx.fill();
      ctx.strokeStyle = cor;
      ctx.lineWidth = 6 * u;
      ctx.stroke();
      ctx.fillStyle = cor;
      ctx.font = U.pesoFonte(800, escudoR * 0.9);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('!', 0, 0);
      ctx.restore();

      const it = d.itens.slice(0, 3);
      const y0 = c.y + escudoR * 2.2 + 24 * u;
      const h = Math.max(64 * u, (c.h - (y0 - c.y) - 10 * u) / Math.max(1, it.length));
      it.forEach(function (item, i) {
        const kk = U.aparecer(p, 0.35 + i * 0.13, 0.28);
        if (kk <= 0) return;
        ctx.save();
        ctx.globalAlpha = kk;
        ctx.translate((1 - kk) * 20 * u, 0);
        const y = y0 + i * h;
        ctx.fillStyle = cor;
        ctx.beginPath();
        ctx.arc(c.x + 40 * u, y + h / 2 - 2 * u, 9 * u, 0, Math.PI * 2);
        ctx.fill();
        const at = U.ajustar(ctx, item.rotulo, {
          max: 36 * u, min: 26 * u, peso: 600, maxLargura: c.w - 100 * u, maxLinhas: 2
        });
        U.blocoTexto(ctx, at, c.x + 72 * u, y + h / 2 - at.altura / 2, { cor: T.tinta, peso: 600 });
        ctx.restore();
      });
    }
  };

  /* ============================================================
     14. FLUXO — para onde vai o dinheiro
     ============================================================ */
  V.fluxo = {
    rotulo: 'Fluxo do dinheiro',
    dica: 'Origem → destinos. Bom para regra de orçamento.',
    exemplo: 'origem: Salário\nitens: Custo fixo=50% | Objetivos=30% | Prazeres=20%',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const it = d.itens.slice(0, 3);
      const oW = c.w * 0.28, oH = 130 * u;
      const oX = c.x, oY = c.y + (c.h - oH) / 2;
      const k0 = U.aparecer(p, 0.02, 0.28);
      ctx.save();
      ctx.globalAlpha = k0;
      U.cartao(ctx, oX, oY, oW, oH, 26 * u, { fundo: T.tinta, blur: 40, dy: 14 });
      const ao = U.ajustar(ctx, d.origem || 'Entrada', {
        max: 38 * u, min: 26 * u, peso: 700, maxLargura: oW - 40 * u, maxLinhas: 2
      });
      U.blocoTexto(ctx, ao, oX + oW / 2, oY + oH / 2 - ao.altura / 2,
        { align: 'center', cor: '#fff', peso: 700 });
      ctx.restore();

      const dX = c.x + c.w * 0.46, dW = c.w * 0.54;
      const dH = Math.min(110 * u, c.h / Math.max(1, it.length));
      const dY0 = c.y + (c.h - dH * it.length) / 2;

      it.forEach(function (item, i) {
        const ini = 0.2 + i * 0.14;
        const ks = U.ease.saida(U.faixa(p, ini, ini + 0.24));
        const y = dY0 + i * dH + dH / 2;
        /* curva de ligação */
        ctx.save();
        ctx.strokeStyle = A + '66';
        ctx.lineWidth = 5 * u;
        ctx.lineCap = 'round';
        ctx.setLineDash([1000, 1000]);
        ctx.lineDashOffset = 1000 * (1 - ks);
        ctx.beginPath();
        ctx.moveTo(oX + oW, oY + oH / 2);
        ctx.bezierCurveTo(oX + oW + 90 * u, oY + oH / 2, dX - 90 * u, y, dX - 8 * u, y);
        ctx.stroke();
        ctx.restore();

        const kc = U.aparecer(p, ini + 0.12, 0.24);
        if (kc <= 0) return;
        ctx.save();
        ctx.globalAlpha = kc;
        U.cartao(ctx, dX, y - dH / 2 + 8 * u, dW, dH - 18 * u, 22 * u, { borda: T.linha, blur: 24, dy: 8 });
        U.texto(ctx, item.rotulo, dX + 32 * u, y - 1 * u, {
          tamanho: 32 * u, peso: 600, cor: T.tinta, baseline: 'middle'
        });
        U.texto(ctx, item.valor || '', dX + dW - 32 * u, y - 1 * u, {
          tamanho: 38 * u, peso: 800, cor: A, align: 'right', baseline: 'middle'
        });
        ctx.restore();
      });
    }
  };

  /* ============================================================
     15. CALENDÁRIO — datas que importam
     ============================================================ */
  V.calendario = {
    rotulo: 'Calendário',
    dica: 'Dia de pagar, dia de investir, ciclo da fatura.',
    exemplo: 'mes: Setembro\nmarcados: 5, 10, 25\nrotulo: dia 5 é o Pix automático',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const w = Math.min(c.w * 0.8, 660 * u), h = Math.min(c.h * 0.94, 470 * u);
      const x = c.x + (c.w - w) / 2, y = c.y + (c.h - h) / 2;
      const k = U.aparecer(p, 0.02, 0.3);
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 24 * u);
      U.cartao(ctx, x, y, w, h, 30 * u, { blur: 50, dy: 18, borda: T.linha });
      U.texto(ctx, d.mes || 'Mês', x + w / 2, y + 30 * u, {
        tamanho: 38 * u, peso: 700, cor: T.tinta, align: 'center'
      });
      const dias = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
      const cel = (w - 56 * u) / 7;
      dias.forEach(function (dd, i) {
        U.texto(ctx, dd, x + 30 * u + cel * (i + 0.5), y + 96 * u, {
          tamanho: 24 * u, peso: 700, cor: T.tinta3, align: 'center'
        });
      });
      const marcados = String(d.marcados || '').split(/[,\s]+/).map(Number).filter(Boolean);
      const linhaH = (h - 168 * u) / 5;
      for (let i = 0; i < 35; i++) {
        const dia = i + 1;
        if (dia > 30) break;
        const col = i % 7, lin = Math.floor(i / 7);
        const cxD = x + 30 * u + cel * (col + 0.5);
        const cyD = y + 150 * u + linhaH * (lin + 0.5);
        const marcado = marcados.indexOf(dia) >= 0;
        if (marcado) {
          const km = U.ease.firme(U.faixa(p, 0.3 + marcados.indexOf(dia) * 0.1, 0.6 + marcados.indexOf(dia) * 0.1));
          ctx.save();
          ctx.globalAlpha = Math.min(1, km * 1.5);
          ctx.beginPath();
          ctx.arc(cxD, cyD, Math.min(cel, linhaH) * 0.40 * (0.7 + km * 0.3), 0, Math.PI * 2);
          ctx.fillStyle = A;
          ctx.fill();
          ctx.restore();
        }
        U.texto(ctx, String(dia), cxD, cyD, {
          tamanho: 26 * u, peso: marcado ? 800 : 500,
          cor: marcado ? '#fff' : T.tinta3, align: 'center', baseline: 'middle'
        });
      }
      ctx.restore();
      if (d.rotulo) {
        U.texto(ctx, d.rotulo, c.x + c.w / 2, y + h + 14 * u, {
          tamanho: 28 * u, peso: 600, cor: T.tinta2, align: 'center',
          opacidade: U.aparecer(p, 0.55, 0.3)
        });
      }
    }
  };

  /* ============================================================
     16. CONTRATO — a letra miúda
     ============================================================ */
  V.contrato = {
    rotulo: 'Contrato / letra miúda',
    dica: 'Cláusula escondida, taxa no rodapé, termo de adesão.',
    exemplo: 'titulo: Termo de adesão\ndestaque: Taxa de administração de 2,3% ao ano\nlinhas: 9',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const w = Math.min(c.w * 0.78, 640 * u), h = c.h * 0.94;
      const x = c.x + (c.w - w) / 2, y = c.y + (c.h - h) / 2;
      const k = U.aparecer(p, 0.02, 0.3);
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 26 * u);
      U.cartao(ctx, x, y, w, h, 20 * u, { blur: 50, dy: 20 });
      U.texto(ctx, (d.titulo || 'Contrato').toUpperCase(), x + 44 * u, y + 40 * u, {
        tamanho: 24 * u, peso: 700, cor: T.tinta3, tracking: 3
      });
      const n = Math.max(4, Math.min(12, Number(d.linhas) || 9));
      const lh = (h - 190 * u) / n;
      const destaqueIdx = Math.floor(n * 0.62);
      for (let i = 0; i < n; i++) {
        const ly = y + 100 * u + i * lh;
        if (i === destaqueIdx && d.destaque) continue;
        ctx.fillStyle = T.linha;
        const larg = (w - 88 * u) * (i % 3 === 2 ? 0.68 : i % 3 === 1 ? 0.92 : 1);
        U.caminhoArredondado(ctx, x + 44 * u, ly, larg, 13 * u, 6 * u);
        ctx.fill();
      }
      if (d.destaque) {
        const ly = y + 100 * u + destaqueIdx * lh;
        const kd = U.faixa(p, 0.34, 0.62);
        ctx.save();
        U.caminhoArredondado(ctx, x + 36 * u, ly - 20 * u, (w - 72 * u) * kd, 70 * u, 12 * u);
        ctx.fillStyle = A + '20';
        ctx.fill();
        ctx.restore();
        const at = U.ajustar(ctx, d.destaque, {
          max: 32 * u, min: 22 * u, peso: 700, maxLargura: w - 100 * u, maxLinhas: 2
        });
        U.blocoTexto(ctx, at, x + 50 * u, ly - 12 * u,
          { cor: A, peso: 700, opacidade: U.aparecer(p, 0.4, 0.3) });
      }
      /* linha de assinatura */
      U.linhaH(ctx, x + 44 * u, y + h - 62 * u, w * 0.42, T.linhaForte);
      U.texto(ctx, 'assinatura', x + 44 * u, y + h - 52 * u, { tamanho: 22 * u, peso: 500, cor: T.tinta3 });
      ctx.restore();
    }
  };

  /* ============================================================
     17. CARTEIRA — saldo do app com mini gráfico
     ============================================================ */
  V.carteira = {
    rotulo: 'Saldo no app',
    dica: 'Patrimônio, rendimento do mês, saldo da conta.',
    exemplo: 'rotulo: Investido\nvalor: R$ 42.180,00\nvariacao: +1,08% no mês\nitens: 8|11|9|14|13|18|17|23',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const w = Math.min(c.w * 0.86, 780 * u), h = Math.min(c.h * 0.92, 430 * u);
      const x = c.x + (c.w - w) / 2, y = c.y + (c.h - h) / 2;
      const k = U.aparecer(p, 0.02, 0.32);
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 26 * u);
      U.cartao(ctx, x, y, w, h, 36 * u, { blur: 60, dy: 22, borda: T.linha });
      U.texto(ctx, d.rotulo || 'Saldo', x + 46 * u, y + 42 * u, { tamanho: 30 * u, peso: 600, cor: T.tinta3 });
      const val = U.animarNumero(d.valor || 'R$ 0,00', U.ease.saida(U.faixa(p, 0.08, 0.66)));
      const av = U.ajustar(ctx, val, {
        max: 92 * u, min: 52 * u, peso: 800, maxLargura: w - 92 * u, maxLinhas: 1
      });
      U.blocoTexto(ctx, av, x + 46 * u, y + 86 * u, { cor: T.tinta, peso: 800, tracking: -2 * u });
      if (d.variacao) {
        const sobe = String(d.variacao).trim().charAt(0) !== '-';
        U.pilula(ctx, x + 46 * u, y + 86 * u + av.altura + 16 * u, d.variacao, {
          altura: 54 * u, tamanho: 28 * u,
          fundo: sobe ? T.acentoSuave : T.alertaSuave,
          cor: sobe ? T.acento : T.alerta
        });
      }
      /* mini gráfico */
      const vs = d.itens.length ? nums(d.itens) : [8, 11, 9, 14, 13, 18, 17, 23];
      const gx = x + 46 * u, gw = w - 92 * u, gh = 96 * u, gy = y + h - gh - 44 * u;
      const max = Math.max.apply(null, vs) || 1;
      const kg = U.ease.saida(U.faixa(p, 0.25, 0.85));
      ctx.save();
      ctx.beginPath();
      ctx.rect(gx - 4 * u, gy - 12 * u, gw * kg + 8 * u, gh + 24 * u);
      ctx.clip();                       /* o recorte precisa vir ANTES do traçado */
      ctx.strokeStyle = A;
      ctx.lineWidth = 6 * u;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.beginPath();
      vs.forEach(function (v, i) {
        const px2 = gx + (gw * i) / Math.max(1, vs.length - 1);
        const py2 = gy + gh - (v / max) * gh;
        if (i === 0) ctx.moveTo(px2, py2); else ctx.lineTo(px2, py2);
      });
      ctx.stroke();
      ctx.restore();
      ctx.restore();
    }
  };

  /* ============================================================
     18. MOEDAS — pilhas crescendo
     ============================================================ */
  V.moedas = {
    rotulo: 'Pilhas de moedas',
    dica: 'Acúmulo simples, sem números. Bom para transição.',
    exemplo: 'itens: 3 | 5 | 8 | 12\nrotulo: cada mês guardado vira base do próximo',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const pilhas = d.itens.length ? nums(d.itens) : [3, 5, 8, 12];
      const n = pilhas.length;
      const max = Math.max.apply(null, pilhas) || 1;
      const raio = Math.min(c.w / (n * 3.2), c.h * 0.16);
      const espessura = raio * 0.42;
      const baseY = c.y + c.h * 0.86;
      pilhas.forEach(function (qtd, i) {
        const cx = c.x + (c.w * (i + 0.5)) / n;
        const k = U.faixa(p, 0.06 + i * 0.12, 0.62 + i * 0.12);
        const visiveis = Math.round(qtd * U.ease.saida(k));
        for (let j = 0; j < visiveis; j++) {
          const cy = baseY - j * espessura * 0.86;
          ctx.save();
          ctx.beginPath();
          ctx.ellipse(cx, cy + espessura * 0.5, raio, espessura, 0, 0, Math.PI * 2);
          ctx.fillStyle = '#C8A24A';
          ctx.fill();
          ctx.beginPath();
          ctx.ellipse(cx, cy, raio, espessura, 0, 0, Math.PI * 2);
          ctx.fillStyle = j === visiveis - 1 ? '#E8CB7E' : '#DFBF6C';
          ctx.fill();
          ctx.restore();
        }
        U.texto(ctx, 'mês ' + (i + 1), cx, baseY + espessura * 2 + 14 * u, {
          tamanho: 26 * u, peso: 600, cor: T.tinta3, align: 'center',
          opacidade: U.aparecer(p, 0.1 + i * 0.08, 0.3)
        });
        if (qtd === max && d.rotulo) {
          /* nada aqui: rótulo é comum, desenhado abaixo */
        }
      });
      if (d.rotulo) {
        U.texto(ctx, d.rotulo, c.x + c.w / 2, c.y + 6 * u, {
          tamanho: 32 * u, peso: 600, cor: T.tinta2, align: 'center',
          opacidade: U.aparecer(p, 0.3, 0.3)
        });
      }
    }
  };

  /* ============================================================
     19. CITAÇÃO — só tipografia (use pouco: o padrão pede cena concreta)
     ============================================================ */
  V.citacao = {
    rotulo: 'Frase em destaque',
    dica: 'Sem objeto na tela. O verificador limita o uso a 1 cena.',
    exemplo: 'frase: Quem não agenda, não guarda.\nautor: regra da casa',
    abstrato: true,
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      U.texto(ctx, '“', c.x + c.w / 2, c.y + 4 * u, {
        tamanho: 160 * u, peso: 800, cor: A + '33', align: 'center'
      });
      const aj = U.ajustar(ctx, d.frase || '', {
        max: 62 * u, min: 36 * u, peso: 700, maxLargura: c.w - 120 * u, maxLinhas: 4
      });
      U.blocoTexto(ctx, aj, c.x + c.w / 2, c.y + c.h / 2 - aj.altura / 2,
        { align: 'center', cor: T.tinta, peso: 700, progresso: p, atraso: 0.05 });
      if (d.autor) {
        U.texto(ctx, '— ' + d.autor, c.x + c.w / 2, c.y + c.h - 46 * u, {
          tamanho: 28 * u, peso: 600, cor: T.tinta3, align: 'center',
          opacidade: U.aparecer(p, 0.4, 0.3)
        });
      }
    }
  };

  /* ============================================================
     20. CHAMADA — cartão de CTA
     ============================================================ */
  V.chamada = {
    rotulo: 'Chamada final',
    dica: 'Um passo só, verbal e concreto. Nada de "curta e compartilhe".',
    exemplo: 'acao: Abra o app e agende R$ 100 para o dia do salário\nreforco: leva 2 minutos',
    desenhar: function (ctx, c, p, cena, A, d) {
      const u = c.w / 936;
      const w = Math.min(c.w, 820 * u);
      const x = c.x + (c.w - w) / 2;
      const k = U.aparecer(p, 0.02, 0.32);
      const aj = U.ajustar(ctx, d.acao || '', {
        max: 52 * u, min: 32 * u, peso: 700, maxLargura: w - 120 * u, maxLinhas: 4
      });
      const h = Math.max(c.h * 0.62, aj.altura + 190 * u);
      const y = c.y + (c.h - h) / 2;
      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 26 * u);
      U.cartao(ctx, x, y, w, h, 40 * u, { fundo: A, blur: 70, dy: 26, corSombra: T.sombraForte });
      U.texto(ctx, 'PRÓXIMO PASSO', x + w / 2, y + 46 * u, {
        tamanho: 24 * u, peso: 700, cor: 'rgba(255,255,255,0.7)', align: 'center', tracking: 4
      });
      U.blocoTexto(ctx, aj, x + w / 2, y + 108 * u,
        { align: 'center', cor: '#FFFFFF', peso: 700, progresso: p, atraso: 0.08 });
      if (d.reforco) {
        U.texto(ctx, d.reforco, x + w / 2, y + h - 56 * u, {
          tamanho: 30 * u, peso: 600, cor: 'rgba(255,255,255,0.78)', align: 'center',
          opacidade: U.aparecer(p, 0.4, 0.3)
        });
      }
      ctx.restore();
    }
  };

  /* ============================================================
     21. MÍDIA PRÓPRIA — a ponte com filmagem gerada fora do Studio
     ============================================================ */
  V.midia = {
    rotulo: 'Mídia própria (imagem ou vídeo)',
    dica: 'Sua filmagem entra como a cena. O texto grande, a legenda e o verificador continuam por cima.',
    exemplo: 'legenda: crédito ou observação (opcional)',
    precisaMidia: true,
    desenhar: function (ctx, c, p, cena, A, d, midia) {
      const u = c.w / 936;
      const r = 34 * u;
      const k = U.aparecer(p, 0.02, 0.32);

      if (!midia) {
        U.cartao(ctx, c.x, c.y, c.w, c.h, r, { fundo: T.cartaoSuave, borda: T.linhaForte, sombra: false });
        const aj = U.ajustar(ctx, 'Nenhuma mídia nesta cena.\nUse o botão “mídia…” no roteiro.', {
          max: 34 * u, min: 24 * u, peso: 600, maxLargura: c.w - 120 * u, maxLinhas: 3
        });
        U.blocoTexto(ctx, aj, c.x + c.w / 2, c.y + c.h / 2 - aj.altura / 2,
          { align: 'center', cor: T.tinta3, peso: 600 });
        return;
      }

      ctx.save();
      ctx.globalAlpha = k;
      ctx.translate(0, (1 - k) * 24 * u);
      U.sombraContato(ctx, c.x + c.w / 2, c.y + c.h + 14 * u, c.w * 0.92, 44 * u,
        T.tom === 'escuro' ? 0.5 : 0.26);
      ctx.save();
      ctx.shadowColor = T.sombraForte;
      ctx.shadowBlur = 60 * u;
      ctx.shadowOffsetY = 22 * u;
      ctx.fillStyle = T.cartao;
      U.caminhoArredondado(ctx, c.x, c.y, c.w, c.h, r);
      ctx.fill();
      ctx.restore();

      U.comRecorte(ctx, c.x, c.y, c.w, c.h, r, function () {
        U.desenharCobrindo(ctx, midia, c.x, c.y, c.w, c.h);
        /* vinheta suave: assenta a imagem no quadro e sustenta a legenda */
        const g = ctx.createLinearGradient(0, c.y, 0, c.y + c.h);
        g.addColorStop(0, 'rgba(0,0,0,0)');
        g.addColorStop(0.62, 'rgba(0,0,0,0)');
        g.addColorStop(1, 'rgba(0,0,0,0.34)');
        ctx.fillStyle = g;
        ctx.fillRect(c.x, c.y, c.w, c.h);
      });

      /* fio de luz na borda, para não parecer imagem colada */
      U.caminhoArredondado(ctx, c.x + 1, c.y + 1, c.w - 2, c.h - 2, r - 1);
      ctx.strokeStyle = T.tom === 'escuro' ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.55)';
      ctx.lineWidth = 2 * u;
      ctx.stroke();

      if (d.legenda) {
        U.texto(ctx, d.legenda, c.x + 34 * u, c.y + c.h - 44 * u, {
          tamanho: 26 * u, peso: 600, cor: 'rgba(255,255,255,0.88)',
          opacidade: U.aparecer(p, 0.3, 0.3)
        });
      }
      ctx.restore();
    }
  };

  U.LISTA_VISUAIS = Object.keys(V);

})(window.UMM);
