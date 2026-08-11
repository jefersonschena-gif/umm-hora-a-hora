/* UMM Studio — empacotador WebM (Matroska) para VP9 + Opus

   Escrito aqui dentro de propósito: assim a exportação exata não depende de
   CDN, de rede nem de pacote instalado. Recebe os pedaços que saem do
   VideoEncoder/AudioEncoder do WebCodecs e devolve um arquivo .webm.

   Escala de tempo: 1 ms (TimestampScale = 1.000.000 ns). Um cluster novo
   começa a cada quadro-chave, o que mantém o deslocamento de cada bloco
   dentro dos ±32 s que o SimpleBlock comporta. */

(function (U) {
  'use strict';

  /* ---------- identificadores EBML ---------- */
  const ID = {
    EBML: 0x1A45DFA3, EBMLVersion: 0x4286, EBMLReadVersion: 0x42F7,
    EBMLMaxIDLength: 0x42F2, EBMLMaxSizeLength: 0x42F3,
    DocType: 0x4282, DocTypeVersion: 0x4287, DocTypeReadVersion: 0x4285,

    Segment: 0x18538067,
    Info: 0x1549A966, TimestampScale: 0x2AD7B1, MuxingApp: 0x4D80,
    WritingApp: 0x5741, Duration: 0x4489,

    Tracks: 0x1654AE6B, TrackEntry: 0xAE, TrackNumber: 0xD7, TrackUID: 0x73C5,
    TrackType: 0x83, FlagLacing: 0x9C, Language: 0x22B59C, CodecID: 0x86,
    CodecPrivate: 0x63A2, CodecDelay: 0x56AA, SeekPreRoll: 0x56BB,
    DefaultDuration: 0x23E383,
    Video: 0xE0, PixelWidth: 0xB0, PixelHeight: 0xBA,
    Audio: 0xE1, SamplingFrequency: 0xB5, Channels: 0x9F,

    Cluster: 0x1F43B675, Timestamp: 0xE7, SimpleBlock: 0xA3,

    Cues: 0x1C53BB6B, CuePoint: 0xBB, CueTime: 0xB3,
    CueTrackPositions: 0xB7, CueTrack: 0xF7, CueClusterPosition: 0xF1
  };

  const TRILHA_VIDEO = 1, TRILHA_AUDIO = 2;

  /* ---------- primitivas ---------- */
  function bytesDeId(id) {
    const b = [];
    let n = id;
    while (n > 0) { b.unshift(n & 0xff); n = Math.floor(n / 256); }
    return Uint8Array.from(b);
  }

  /* Inteiro sem sinal no menor número de bytes. */
  function uint(v) {
    if (v === 0) return Uint8Array.from([0]);
    const b = [];
    let n = v;
    while (n > 0) { b.unshift(n % 256); n = Math.floor(n / 256); }
    return Uint8Array.from(b);
  }

  /* Tamanho em formato "vint": o primeiro bit ligado marca o comprimento. */
  function tamanho(v) {
    let n = 1;
    while (n < 8 && v >= Math.pow(2, 7 * n) - 1) n++;
    const b = new Uint8Array(n);
    let resto = v;
    for (let i = n - 1; i >= 0; i--) { b[i] = resto % 256; resto = Math.floor(resto / 256); }
    b[0] |= 1 << (8 - n);
    return b;
  }

  function float64(v) {
    const b = new Uint8Array(8);
    new DataView(b.buffer).setFloat64(0, v, false);
    return b;
  }

  function texto(s) { return new TextEncoder().encode(s); }

  function juntar(partes) {
    let total = 0;
    partes.forEach(p => { total += p.length; });
    const out = new Uint8Array(total);
    let o = 0;
    partes.forEach(p => { out.set(p, o); o += p.length; });
    return out;
  }

  function elem(id, conteudo) {
    return juntar([bytesDeId(id), tamanho(conteudo.length), conteudo]);
  }
  const elemU = (id, v) => elem(id, uint(v));
  const elemS = (id, v) => elem(id, texto(v));
  const elemF = (id, v) => elem(id, float64(v));

  /* ---------- OpusHead ----------
     O Chrome entrega esse cabeçalho em metadata.decoderConfig.description.
     Se por algum motivo não vier, montamos o mínimo válido. */
  function opusHead(canais, taxa, preSkip) {
    const b = new Uint8Array(19);
    const dv = new DataView(b.buffer);
    b.set(texto('OpusHead'), 0);
    b[8] = 1;
    b[9] = canais;
    dv.setUint16(10, preSkip == null ? 312 : preSkip, true);
    dv.setUint32(12, taxa, true);
    dv.setUint16(16, 0, true);
    b[18] = 0;
    return b;
  }

  /* ---------- Muxer ---------- */
  function Muxer(op) {
    this.video = op.video;                  /* {width, height, frameRate} */
    this.audio = op.audio || null;          /* {sampleRate, numberOfChannels} */
    this.pedacos = [];
    this.opusPrivado = null;
    this.opusPreSkip = null;
    this.finalizado = false;
  }
  U.WebM = { Muxer: Muxer, MAX_CLUSTER_MS: 30000 };

  function guardar(muxer, chunk, tipoTrilha) {
    const dados = new Uint8Array(chunk.byteLength);
    chunk.copyTo(dados);
    muxer.pedacos.push({
      trilha: tipoTrilha,
      ms: chunk.timestamp / 1000,
      chave: chunk.type === 'key',
      dados: dados
    });
  }

  Muxer.prototype.addVideoChunk = function (chunk) {
    guardar(this, chunk, TRILHA_VIDEO);
  };

  Muxer.prototype.addAudioChunk = function (chunk, meta) {
    if (!this.opusPrivado && meta && meta.decoderConfig && meta.decoderConfig.description) {
      const d = meta.decoderConfig.description;
      this.opusPrivado = d instanceof Uint8Array ? d : new Uint8Array(
        d.buffer ? d.buffer.slice(d.byteOffset || 0, (d.byteOffset || 0) + d.byteLength) : d
      );
      if (this.opusPrivado.length >= 12) {
        this.opusPreSkip = new DataView(
          this.opusPrivado.buffer, this.opusPrivado.byteOffset, this.opusPrivado.byteLength
        ).getUint16(10, true);
      }
    }
    guardar(this, chunk, TRILHA_AUDIO);
  };

  function simpleBlock(trilha, relativo, chave, dados) {
    const cab = new Uint8Array(4);
    cab[0] = 0x80 | trilha;                 /* número da trilha como vint de 1 byte */
    cab[1] = (relativo >> 8) & 0xff;
    cab[2] = relativo & 0xff;
    cab[3] = chave ? 0x80 : 0x00;
    return elem(ID.SimpleBlock, juntar([cab, dados]));
  }

  Muxer.prototype.finalize = function () {
    if (this.finalizado) throw new Error('Este empacotador já foi finalizado.');
    this.finalizado = true;

    /* --- cabeçalho EBML --- */
    const cabecalho = elem(ID.EBML, juntar([
      elemU(ID.EBMLVersion, 1), elemU(ID.EBMLReadVersion, 1),
      elemU(ID.EBMLMaxIDLength, 4), elemU(ID.EBMLMaxSizeLength, 8),
      elemS(ID.DocType, 'webm'), elemU(ID.DocTypeVersion, 2), elemU(ID.DocTypeReadVersion, 2)
    ]));

    /* --- ordenação: tempo crescente, vídeo primeiro no empate --- */
    const lista = this.pedacos.slice().sort(function (a, b) {
      return a.ms === b.ms ? a.trilha - b.trilha : a.ms - b.ms;
    });
    const duracaoMs = lista.length
      ? Math.max.apply(null, lista.map(p => p.ms)) + (1000 / (this.video.frameRate || 30))
      : 0;

    /* --- Info --- */
    const info = elem(ID.Info, juntar([
      elemU(ID.TimestampScale, 1000000),
      elemS(ID.MuxingApp, 'UMM Studio'),
      elemS(ID.WritingApp, 'UMM Studio'),
      elemF(ID.Duration, duracaoMs)
    ]));

    /* --- Tracks --- */
    const partesTrilhas = [elem(ID.TrackEntry, juntar([
      elemU(ID.TrackNumber, TRILHA_VIDEO),
      elemU(ID.TrackUID, TRILHA_VIDEO),
      elemU(ID.TrackType, 1),
      elemU(ID.FlagLacing, 0),
      elemS(ID.Language, 'und'),
      elemS(ID.CodecID, 'V_VP9'),
      elemU(ID.DefaultDuration, Math.round(1e9 / (this.video.frameRate || 30))),
      elem(ID.Video, juntar([
        elemU(ID.PixelWidth, this.video.width),
        elemU(ID.PixelHeight, this.video.height)
      ]))
    ]))];

    if (this.audio) {
      const privado = this.opusPrivado ||
        opusHead(this.audio.numberOfChannels, this.audio.sampleRate, null);
      const preSkip = this.opusPreSkip == null ? 312 : this.opusPreSkip;
      partesTrilhas.push(elem(ID.TrackEntry, juntar([
        elemU(ID.TrackNumber, TRILHA_AUDIO),
        elemU(ID.TrackUID, TRILHA_AUDIO),
        elemU(ID.TrackType, 2),
        elemU(ID.FlagLacing, 0),
        elemS(ID.Language, 'por'),
        elemS(ID.CodecID, 'A_OPUS'),
        elem(ID.CodecPrivate, privado),
        elemU(ID.CodecDelay, Math.round((preSkip / 48000) * 1e9)),
        elemU(ID.SeekPreRoll, 80000000),
        elem(ID.Audio, juntar([
          elemF(ID.SamplingFrequency, this.audio.sampleRate),
          elemU(ID.Channels, this.audio.numberOfChannels)
        ]))
      ])));
    }
    const trilhas = elem(ID.Tracks, juntar(partesTrilhas));

    /* --- Clusters --- */
    const clusters = [];
    const cues = [];
    let atual = null;

    function fecharCluster() {
      if (!atual) return;
      clusters.push(elem(ID.Cluster, juntar(
        [elemU(ID.Timestamp, atual.base)].concat(atual.blocos)
      )));
    }

    lista.forEach(function (p) {
      const ms = Math.round(p.ms);
      const precisaNovo = !atual ||
        (p.trilha === TRILHA_VIDEO && p.chave) ||
        (ms - atual.base) > U.WebM.MAX_CLUSTER_MS;
      if (precisaNovo) {
        fecharCluster();
        atual = { base: ms, blocos: [], indice: clusters.length };
        if (p.trilha === TRILHA_VIDEO) cues.push({ ms: ms, cluster: atual.indice });
      }
      const rel = Math.max(-32768, Math.min(32767, ms - atual.base));
      atual.blocos.push(simpleBlock(p.trilha, rel, p.chave, p.dados));
    });
    fecharCluster();

    /* --- Cues: posição de cada cluster dentro dos dados do Segment --- */
    const antesDosClusters = info.length + trilhas.length;
    const deslocamentos = [];
    let acumulado = antesDosClusters;
    clusters.forEach(function (c) { deslocamentos.push(acumulado); acumulado += c.length; });

    const cuePoints = cues.map(function (c) {
      return elem(ID.CuePoint, juntar([
        elemU(ID.CueTime, c.ms),
        elem(ID.CueTrackPositions, juntar([
          elemU(ID.CueTrack, TRILHA_VIDEO),
          elemU(ID.CueClusterPosition, deslocamentos[c.cluster])
        ]))
      ]));
    });
    const cuesElem = cuePoints.length ? elem(ID.Cues, juntar(cuePoints)) : new Uint8Array(0);

    const dadosSegmento = juntar([info, trilhas].concat(clusters, [cuesElem]));
    const segmento = elem(ID.Segment, dadosSegmento);
    return juntar([cabecalho, segmento]);
  };

})(window.UMM);
