/* UMM Studio — voz
   Narração em português sem pagar nada. Três rotas, em ordem de conveniência:

   1. "piper"      — Piper/VITS rodando dentro do navegador (@diffusionstudio/vits-web).
                     Modelos pt-BR da Rhasspy, licença MIT, baixados uma vez e
                     guardados no próprio navegador. Sem chave, sem servidor, sem custo.
   2. "arquivos"   — você grava (ou gera em outra ferramenta gratuita) e sobe o áudio
                     de cada cena. É a rota mais previsível.
   3. "navegador"  — SpeechSynthesis do sistema. Serve para OUVIR enquanto escreve,
                     mas o navegador não deixa capturar esse áudio: não entra no arquivo.

   Sem nenhuma delas o vídeo sai mudo com legenda — e, pelo padrão, ainda se entende. */

(function (U) {
  'use strict';

  const Voz = {};
  U.Voz = Voz;

  Voz.CDN = 'https://esm.sh/@diffusionstudio/vits-web';

  Voz.VOZES_SUGERIDAS = [
    { id: 'pt_BR-faber-medium', rotulo: 'Faber — masculina, neutra (pt-BR)' },
    { id: 'pt_BR-edresson-low', rotulo: 'Edresson — masculina, leve (pt-BR)' },
    { id: 'pt_PT-tugão-medium', rotulo: 'Tugão — pt-PT (use só se quiser sotaque europeu)' }
  ];

  let _mod = null;
  let _ac = null;

  Voz.audioContext = function () {
    if (!_ac) _ac = new (window.AudioContext || window.webkitAudioContext)();
    if (_ac.state === 'suspended') _ac.resume();
    return _ac;
  };

  /* ---------------------------------------------------------------
     Piper no navegador
     --------------------------------------------------------------- */
  Voz.carregarPiper = async function () {
    if (_mod) return _mod;
    try {
      _mod = await import(/* webpackIgnore: true */ Voz.CDN);
    } catch (e) {
      throw new Error(
        'Não consegui carregar o Piper (' + e.message + '). ' +
        'Isso costuma ser bloqueio de rede ou página aberta como arquivo local. ' +
        'Sirva a pasta com "python3 -m http.server" ou use a rota "arquivos".'
      );
    }
    return _mod;
  };

  Voz.vozesPiper = async function () {
    const m = await Voz.carregarPiper();
    try {
      const todas = await m.voices();
      const pt = (todas || []).filter(function (v) {
        const chave = String(v.key || v.name || '');
        return /^pt[_-]/i.test(chave) || /portug/i.test(String(v.language && v.language.name_english || ''));
      }).map(function (v) {
        return { id: v.key || v.name, rotulo: (v.key || v.name) + (v.quality ? ' · ' + v.quality : '') };
      });
      return pt.length ? pt : Voz.VOZES_SUGERIDAS;
    } catch (e) {
      return Voz.VOZES_SUGERIDAS;
    }
  };

  /* Baixa o modelo uma vez (fica no navegador). */
  Voz.baixarVoz = async function (vozId, aoProgredir) {
    const m = await Voz.carregarPiper();
    const jaTem = await m.stored().catch(() => []);
    if ((jaTem || []).indexOf(vozId) >= 0) return true;
    await m.download(vozId, function (p) {
      if (aoProgredir && p && p.total) aoProgredir(p.loaded / p.total);
    });
    return true;
  };

  Voz.sintetizarPiper = async function (texto, vozId) {
    const m = await Voz.carregarPiper();
    return m.predict({ text: texto, voiceId: vozId });
  };

  /* ---------------------------------------------------------------
     Utilitários de áudio
     --------------------------------------------------------------- */
  Voz.decodificar = async function (blobOuArquivo) {
    const buf = await blobOuArquivo.arrayBuffer();
    return await Voz.audioContext().decodeAudioData(buf);
  };

  /* Junta os áudios das cenas numa trilha única, alinhada ao roteiro.
     Cada narração começa 0,22s depois do início da cena — respiro de leitura. */
  Voz.montarTrilha = async function (motor) {
    const indices = Object.keys(motor.audio).map(Number).filter(i => motor.audio[i]);
    if (!indices.length) return null;
    const taxa = motor.audio[indices[0]].sampleRate || 22050;
    const total = Math.max(1, Math.ceil((motor.duracao + 0.4) * taxa));
    const off = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, total, taxa);
    indices.forEach(function (i) {
      const src = off.createBufferSource();
      src.buffer = motor.audio[i];
      src.connect(off.destination);
      src.start(Math.max(0, motor.inicios[i] + 0.22));
    });
    return await off.startRendering();
  };

  /* WAV 16 bits — formato universal, aceito por qualquer editor e pelo ffmpeg. */
  Voz.paraWav = function (audioBuffer) {
    const canais = audioBuffer.numberOfChannels;
    const n = audioBuffer.length;
    const taxa = audioBuffer.sampleRate;
    const dados = [];
    for (let c = 0; c < canais; c++) dados.push(audioBuffer.getChannelData(c));

    const bytes = 44 + n * canais * 2;
    const ab = new ArrayBuffer(bytes);
    const dv = new DataView(ab);
    let o = 0;
    const txt = s => { for (let i = 0; i < s.length; i++) dv.setUint8(o++, s.charCodeAt(i)); };
    const u32 = v => { dv.setUint32(o, v, true); o += 4; };
    const u16 = v => { dv.setUint16(o, v, true); o += 2; };

    txt('RIFF'); u32(bytes - 8); txt('WAVE');
    txt('fmt '); u32(16); u16(1); u16(canais); u32(taxa);
    u32(taxa * canais * 2); u16(canais * 2); u16(16);
    txt('data'); u32(n * canais * 2);

    for (let i = 0; i < n; i++) {
      for (let c = 0; c < canais; c++) {
        const v = Math.max(-1, Math.min(1, dados[c][i]));
        dv.setInt16(o, v < 0 ? v * 0x8000 : v * 0x7fff, true);
        o += 2;
      }
    }
    return new Blob([ab], { type: 'audio/wav' });
  };

  /* ---------------------------------------------------------------
     Geração em lote
     --------------------------------------------------------------- */
  Voz.gerarNarracoes = async function (motor, opcoes, aoProgredir) {
    const vozId = opcoes.vozId;
    const cenas = motor.projeto.cenas;
    aoProgredir && aoProgredir({ fase: 'modelo', texto: 'Baixando a voz ' + vozId + '…', k: 0 });
    await Voz.baixarVoz(vozId, function (k) {
      aoProgredir && aoProgredir({ fase: 'modelo', texto: 'Baixando a voz…', k: k });
    });

    for (let i = 0; i < cenas.length; i++) {
      const txt = String(cenas[i].narracao || '').trim();
      if (!txt) { delete motor.audio[i]; continue; }
      aoProgredir && aoProgredir({
        fase: 'sintese', texto: 'Narrando a cena ' + (i + 1) + ' de ' + cenas.length + '…',
        k: i / cenas.length
      });
      const blob = await Voz.sintetizarPiper(Voz.prepararTexto(txt), vozId);
      motor.audio[i] = await Voz.decodificar(blob);
    }
    motor.recalcular();
    aoProgredir && aoProgredir({ fase: 'pronto', texto: 'Narração pronta.', k: 1 });
    return motor;
  };

  /* Pequenos ajustes que melhoram muito a leitura em pt-BR. */
  function prepararTexto(t) {
    return String(t)
      .replace(/R\$\s?/g, 'reais ')                    /* o cifrão antes confunde o modelo */
      .replace(/(\d)\s?%/g, '$1 por cento')
      .replace(/\bR\$\b/g, 'reais')
      .replace(/\s+/g, ' ')
      .trim();
  }

  /* Reordena "reais 1.240" para "1.240 reais": o modelo lê melhor nessa ordem. */
  Voz.prepararTexto = function (t) {
    return prepararTexto(t).replace(/reais\s+([\d.,]+)/g, '$1 reais');
  };

  /* ---------------------------------------------------------------
     Prévia pelo sistema (não entra no arquivo exportado)
     --------------------------------------------------------------- */
  Voz.vozesNavegador = function () {
    if (!window.speechSynthesis) return [];
    return speechSynthesis.getVoices().filter(v => /^pt/i.test(v.lang));
  };

  Voz.falarPreview = function (texto, velocidade) {
    if (!window.speechSynthesis) return false;
    speechSynthesis.cancel();
    const f = new SpeechSynthesisUtterance(texto);
    const pt = Voz.vozesNavegador();
    if (pt.length) f.voice = pt[0];
    f.lang = 'pt-BR';
    f.rate = velocidade || 1;
    speechSynthesis.speak(f);
    return true;
  };

  Voz.pararPreview = function () {
    if (window.speechSynthesis) speechSynthesis.cancel();
  };

})(window.UMM);
