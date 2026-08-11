/* UMM Studio — exportação
   Três saídas, todas gratuitas e sem servidor:

   A. Exato (WebCodecs)      — quadro a quadro, mais rápido que o tempo real,
                               bitrate alto, sem risco de engasgo. MP4/H.264 quando
                               disponível; WebM/VP9 como reserva. Chrome/Edge.
   B. Gravação (MediaRecorder) — funciona em qualquer navegador; grava em tempo real.
   C. Quadros PNG (.zip)     — para montar com ffmpeg local, qualidade máxima.

   Mais SRT, roteiro, narração em WAV e o projeto em JSON. */

(function (U) {
  'use strict';

  const E = {};
  U.Exportar = E;

  E.baixar = function (blob, nome) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nome;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 4000);
  };

  E.baixarTexto = function (texto, nome, tipo) {
    E.baixar(new Blob([texto], { type: (tipo || 'text/plain') + ';charset=utf-8' }), nome);
  };

  E.nomeArquivo = function (projeto, ext) {
    const base = U.normalizar(projeto.titulo || 'video')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 48) || 'video';
    return base + '.' + ext;
  };

  /* ---------------------------------------------------------------
     A. Vídeo determinístico com WebCodecs

     Codifica em VP9 + Opus e empacota com o webm.js daqui do repositório —
     sem CDN, sem instalação, funciona offline. É a saída de melhor qualidade
     e a única cujo resultado não depende do computador estar dando conta em
     tempo real. O YouTube aceita WebM direto; para Instagram e TikTok,
     converta com ffmpeg (o comando aparece na tela) ou use "Gravar", que
     costuma sair em MP4.
     --------------------------------------------------------------- */
  E.suportaWebCodecs = function () {
    return typeof window.VideoEncoder === 'function' && typeof window.VideoFrame === 'function';
  };

  const PERFIS_VIDEO = [
    'vp09.00.10.08',      /* VP9 perfil 0, 8 bits — o mais compatível */
    'vp09.00.41.08',
    'vp8'
  ];

  async function escolherCodecVideo(w, h, fps, bitrate) {
    for (const codec of PERFIS_VIDEO) {
      try {
        const r = await VideoEncoder.isConfigSupported({
          codec: codec, width: w, height: h, bitrate: bitrate, framerate: fps
        });
        if (r && r.supported) return codec;
      } catch (e) { /* tenta o próximo */ }
    }
    return null;
  }

  async function configAudio(trilha) {
    if (!trilha || typeof window.AudioEncoder !== 'function') return null;
    const cfg = {
      codec: 'opus', sampleRate: trilha.sampleRate,
      numberOfChannels: trilha.numberOfChannels, bitrate: 128000
    };
    try {
      const r = await AudioEncoder.isConfigSupported(cfg);
      return r && r.supported ? cfg : null;
    } catch (e) { return null; }
  }

  E.videoExato = async function (motor, canvas, op) {
    op = op || {};
    const fps = op.fps || motor.projeto.fps || 30;
    const W = canvas.width, H = canvas.height;
    const bitrate = op.bitrate || Math.round(W * H * fps * 0.09);
    const ctx = canvas.getContext('2d');

    if (!E.suportaWebCodecs()) throw new Error('Este navegador não tem WebCodecs. Use "Gravar".');
    const codec = await escolherCodecVideo(W, H, fps, bitrate);
    if (!codec) throw new Error('Nenhum codificador de vídeo disponível para ' + W + 'x' + H + '. Use "Gravar".');

    const trilha = op.trilha || null;
    const cfgAudio = await configAudio(trilha);

    const muxer = new U.WebM.Muxer({
      video: { width: W, height: H, frameRate: fps },
      audio: cfgAudio ? { sampleRate: trilha.sampleRate, numberOfChannels: trilha.numberOfChannels } : null
    });

    let falha = null;
    const vEnc = new VideoEncoder({
      output: (chunk, meta) => muxer.addVideoChunk(chunk, meta),
      error: e => { falha = e; }
    });
    vEnc.configure({
      codec: codec, width: W, height: H, bitrate: bitrate,
      framerate: fps, latencyMode: 'quality'
    });

    let aEnc = null;
    if (cfgAudio) {
      aEnc = new AudioEncoder({
        output: (chunk, meta) => muxer.addAudioChunk(chunk, meta),
        error: e => { falha = e; }
      });
      aEnc.configure(cfgAudio);
    }

    const totalQuadros = Math.max(1, Math.round(motor.duracao * fps));
    for (let i = 0; i < totalQuadros; i++) {
      if (falha) throw falha;
      motor.desenhar(ctx, i / fps, { legendas: op.legendas !== false });
      const frame = new VideoFrame(canvas, {
        timestamp: Math.round((i * 1e6) / fps),
        duration: Math.round(1e6 / fps)
      });
      vEnc.encode(frame, { keyFrame: i % (fps * 2) === 0 });
      frame.close();
      if (vEnc.encodeQueueSize > 12) await esperarFila(vEnc);
      if (op.aoProgredir && i % 5 === 0) {
        op.aoProgredir({
          fase: 'video', k: (i / totalQuadros) * (aEnc ? 0.9 : 1),
          texto: 'Codificando quadro ' + (i + 1) + ' de ' + totalQuadros
        });
      }
    }

    if (aEnc) {
      op.aoProgredir && op.aoProgredir({ fase: 'audio', k: 0.92, texto: 'Codificando a narração…' });
      const canais = trilha.numberOfChannels;
      const n = trilha.length;
      const dados = [];
      for (let c = 0; c < canais; c++) dados.push(trilha.getChannelData(c));
      const bloco = 1024;
      for (let off = 0; off < n; off += bloco) {
        if (falha) throw falha;
        const tam = Math.min(bloco, n - off);
        const plano = new Float32Array(tam * canais);
        for (let c = 0; c < canais; c++) plano.set(dados[c].subarray(off, off + tam), c * tam);
        const ad = new AudioData({
          format: 'f32-planar', sampleRate: trilha.sampleRate,
          numberOfFrames: tam, numberOfChannels: canais,
          timestamp: Math.round((off / trilha.sampleRate) * 1e6),
          data: plano
        });
        aEnc.encode(ad);
        ad.close();
        if (aEnc.encodeQueueSize > 24) await esperarFila(aEnc);
      }
      await aEnc.flush();
    }

    await vEnc.flush();
    if (falha) throw falha;

    op.aoProgredir && op.aoProgredir({ fase: 'empacotando', k: 0.98, texto: 'Montando o arquivo…' });
    const bytes = muxer.finalize();
    op.aoProgredir && op.aoProgredir({ fase: 'pronto', k: 1, texto: 'Pronto.' });
    return {
      blob: new Blob([bytes], { type: 'video/webm' }),
      extensao: 'webm',
      codec: codec,
      comAudio: !!aEnc
    };
  };

  function esperarFila(enc) {
    return new Promise(function (r) {
      const olhar = () => (enc.encodeQueueSize <= 4 ? r() : setTimeout(olhar, 6));
      olhar();
    });
  }

  /* ---------------------------------------------------------------
     B. Gravação em tempo real (MediaRecorder)
     --------------------------------------------------------------- */
  E.tipoGravacao = function () {
    const opcoes = [
      'video/mp4;codecs=avc1.640028,mp4a.40.2',
      'video/mp4',
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm'
    ];
    for (const t of opcoes) {
      if (window.MediaRecorder && MediaRecorder.isTypeSupported(t)) return t;
    }
    return '';
  };

  E.gravar = function (motor, canvas, op) {
    op = op || {};
    return new Promise(function (resolver, rejeitar) {
      const fps = op.fps || motor.projeto.fps || 30;
      const ctx = canvas.getContext('2d');
      const stream = canvas.captureStream(fps);
      const tipo = E.tipoGravacao();
      if (!window.MediaRecorder) return rejeitar(new Error('Este navegador não grava vídeo.'));

      let fonte = null;
      if (op.trilha) {
        const ac = U.Voz.audioContext();
        const destino = ac.createMediaStreamDestination();
        fonte = ac.createBufferSource();
        fonte.buffer = op.trilha;
        fonte.connect(destino);
        if (op.ouvir !== false) fonte.connect(ac.destination);
        destino.stream.getAudioTracks().forEach(t => stream.addTrack(t));
      }

      const gravador = new MediaRecorder(stream, {
        mimeType: tipo || undefined,
        videoBitsPerSecond: op.bitrate || Math.round(canvas.width * canvas.height * fps * 0.09),
        audioBitsPerSecond: 128000
      });
      const pedacos = [];
      gravador.ondataavailable = e => { if (e.data && e.data.size) pedacos.push(e.data); };
      gravador.onerror = e => rejeitar(e.error || new Error('Falha na gravação.'));
      gravador.onstop = function () {
        stream.getTracks().forEach(t => t.stop());
        const ext = tipo.indexOf('mp4') >= 0 ? 'mp4' : 'webm';
        resolver({ blob: new Blob(pedacos, { type: tipo || 'video/webm' }), extensao: ext });
      };

      gravador.start(250);
      if (fonte) fonte.start();
      const t0 = performance.now();
      let parando = false;

      (function passo() {
        const t = (performance.now() - t0) / 1000;
        if (t >= motor.duracao) {
          if (!parando) {
            parando = true;
            motor.desenhar(ctx, motor.duracao - 0.001, { legendas: op.legendas !== false });
            setTimeout(() => { try { gravador.stop(); } catch (e) { /* já parou */ } }, 240);
          }
          return;
        }
        motor.desenhar(ctx, t, { legendas: op.legendas !== false });
        op.aoProgredir && op.aoProgredir({ fase: 'gravando', k: t / motor.duracao, texto: 'Gravando… ' + t.toFixed(1) + 's de ' + motor.duracao.toFixed(1) + 's' });
        requestAnimationFrame(passo);
      })();
    });
  };

  /* ---------------------------------------------------------------
     C. Quadros PNG num .zip (sem compressão — PNG já vem comprimido)
     --------------------------------------------------------------- */
  const TABELA_CRC = (function () {
    const t = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32(bytes) {
    let c = 0xffffffff;
    for (let i = 0; i < bytes.length; i++) c = TABELA_CRC[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
    return (c ^ 0xffffffff) >>> 0;
  }

  /* Zip mínimo, método "store". Suficiente e sem dependência externa. */
  E.zip = function (arquivos) {
    const cod = new TextEncoder();
    const locais = [], centrais = [];
    let deslocamento = 0;

    arquivos.forEach(function (f) {
      const nome = cod.encode(f.nome);
      const dados = f.dados;
      const crc = crc32(dados);

      const local = new Uint8Array(30 + nome.length);
      const dv = new DataView(local.buffer);
      dv.setUint32(0, 0x04034b50, true);
      dv.setUint16(4, 20, true);
      dv.setUint16(6, 0, true);
      dv.setUint16(8, 0, true);
      dv.setUint16(10, 0, true);
      dv.setUint16(12, 0, true);
      dv.setUint32(14, crc, true);
      dv.setUint32(18, dados.length, true);
      dv.setUint32(22, dados.length, true);
      dv.setUint16(26, nome.length, true);
      dv.setUint16(28, 0, true);
      local.set(nome, 30);
      locais.push(local, dados);

      const central = new Uint8Array(46 + nome.length);
      const dc = new DataView(central.buffer);
      dc.setUint32(0, 0x02014b50, true);
      dc.setUint16(4, 20, true);
      dc.setUint16(6, 20, true);
      dc.setUint32(16, crc, true);
      dc.setUint32(20, dados.length, true);
      dc.setUint32(24, dados.length, true);
      dc.setUint16(28, nome.length, true);
      dc.setUint32(42, deslocamento, true);
      central.set(nome, 46);
      centrais.push(central);

      deslocamento += local.length + dados.length;
    });

    const tamCentral = centrais.reduce((s, c) => s + c.length, 0);
    const fim = new Uint8Array(22);
    const df = new DataView(fim.buffer);
    df.setUint32(0, 0x06054b50, true);
    df.setUint16(8, arquivos.length, true);
    df.setUint16(10, arquivos.length, true);
    df.setUint32(12, tamCentral, true);
    df.setUint32(16, deslocamento, true);

    return new Blob(locais.concat(centrais, [fim]), { type: 'application/zip' });
  };

  E.quadrosPNG = async function (motor, canvas, op) {
    op = op || {};
    const fps = op.fps || motor.projeto.fps || 30;
    const ctx = canvas.getContext('2d');
    const total = Math.max(1, Math.round(motor.duracao * fps));
    const arquivos = [];
    for (let i = 0; i < total; i++) {
      motor.desenhar(ctx, i / fps, { legendas: op.legendas !== false });
      const blob = await new Promise(r => canvas.toBlob(r, 'image/png'));
      arquivos.push({
        nome: 'quadro_' + String(i + 1).padStart(5, '0') + '.png',
        dados: new Uint8Array(await blob.arrayBuffer())
      });
      if (op.aoProgredir) {
        op.aoProgredir({ fase: 'quadros', k: i / total, texto: 'Gerando quadro ' + (i + 1) + ' de ' + total });
      }
    }
    arquivos.push({
      nome: 'montar.sh',
      dados: new TextEncoder().encode(
        '#!/bin/sh\n' +
        '# Monta o MP4 final com ffmpeg (gratuito). Rode dentro desta pasta.\n' +
        'ffmpeg -y -framerate ' + fps + ' -i quadro_%05d.png \\\n' +
        '  -i narracao.wav -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \\\n' +
        '  -c:a aac -b:a 192k -shortest video.mp4\n' +
        '# Sem narração, apague as duas referências ao áudio acima.\n')
    });
    return E.zip(arquivos);
  };

})(window.UMM);
