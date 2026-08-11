#!/usr/bin/env node
/*
 * tts-edge.mjs — narração em português, de graça, sem chave e sem cadastro.
 *
 * Usa as vozes neurais que o Microsoft Edge expõe para o recurso "Ler em voz
 * alta". São as mesmas vozes do Azure, sem custo e sem conta, mas o endpoint é
 * pensado para o navegador: use com bom senso e não em escala industrial.
 *
 * Quando usar: quando o Piper dentro do navegador não abrir (rede bloqueada,
 * página aberta como arquivo local) ou quando você quiser uma voz mais natural
 * que a do Piper.
 *
 * Uso:
 *   1. No UMM Studio, clique em "Projeto (.json)" e salve o arquivo.
 *   2. node ferramentas/tts-edge.mjs meu-video.json
 *   3. Volte ao Studio, escolha "Subir meus áudios por cena" na aba Voz e
 *      carregue cada arquivo gerado no botão "áudio…" da cena correspondente.
 *
 * Opções:
 *   --voz  <nome>     padrão pt-BR-FranciscaNeural
 *   --saida <pasta>   padrão ./narracao
 *   --ritmo <%>       padrão +0%   (ex.: -8% para falar mais devagar)
 *   --vozes           lista as vozes em português e sai
 *
 * Requer Node 22 ou mais novo (usa o WebSocket embutido).
 */

import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const TOKEN = '6A5AA1D4EAFF4E9FB37E23D68491D6F4';
const WSS = 'wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1';
const LISTA = 'https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list';
const AGENTE = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0';
const VERSAO_GEC = '1-130.0.2849.68';

/* O serviço exige um token derivado do relógio, arredondado para 5 minutos. */
function tokenGEC() {
  let ticks = Math.floor((Date.now() / 1000 + 11644473600) * 10000000);
  ticks -= ticks % 3000000000;
  return crypto.createHash('sha256').update(ticks + TOKEN, 'ascii').digest('hex').toUpperCase();
}

function comToken(base) {
  const u = new URL(base);
  u.searchParams.set('TrustedClientToken', TOKEN);
  u.searchParams.set('Sec-MS-GEC', tokenGEC());
  u.searchParams.set('Sec-MS-GEC-Version', VERSAO_GEC);
  return u.toString();
}

const escapar = s => String(s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&apos;');

/* Os mesmos ajustes que o Studio faz antes de mandar para o Piper. */
function prepararTexto(t) {
  return String(t)
    .replace(/R\$\s?([\d.,]+)/g, '$1 reais')
    .replace(/(\d)\s?%/g, '$1 por cento')
    .replace(/\s+/g, ' ')
    .trim();
}

async function listarVozes() {
  const r = await fetch(comToken(LISTA), {
    headers: { 'User-Agent': AGENTE, 'Origin': 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold' }
  });
  if (!r.ok) throw new Error('a lista de vozes respondeu ' + r.status);
  return (await r.json()).filter(v => /^pt-/i.test(v.Locale));
}

function sintetizar(texto, voz, ritmo) {
  return new Promise((resolver, rejeitar) => {
    const ws = new WebSocket(comToken(WSS), {
      headers: { 'User-Agent': AGENTE, 'Origin': 'chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold' }
    });
    ws.binaryType = 'arraybuffer';

    const pedacos = [];
    const idPedido = crypto.randomUUID().replace(/-/g, '');
    const relogio = setTimeout(() => { try { ws.close(); } catch {} rejeitar(new Error('tempo esgotado')); }, 45000);

    ws.onerror = e => { clearTimeout(relogio); rejeitar(new Error('falha no WebSocket: ' + (e.message || 'sem detalhe'))); };

    ws.onopen = () => {
      const agora = new Date().toString();
      ws.send(
        'X-Timestamp:' + agora + '\r\n' +
        'Content-Type:application/json; charset=utf-8\r\n' +
        'Path:speech.config\r\n\r\n' +
        JSON.stringify({
          context: {
            synthesis: {
              audio: {
                metadataoptions: { sentenceBoundaryEnabled: 'false', wordBoundaryEnabled: 'false' },
                outputFormat: 'audio-24khz-48kbitrate-mono-mp3'
              }
            }
          }
        })
      );
      ws.send(
        'X-RequestId:' + idPedido + '\r\n' +
        'Content-Type:application/ssml+xml\r\n' +
        'X-Timestamp:' + agora + 'Z\r\n' +
        'Path:ssml\r\n\r\n' +
        "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='pt-BR'>" +
        "<voice name='" + voz + "'>" +
        "<prosody pitch='+0Hz' rate='" + ritmo + "' volume='+0%'>" +
        escapar(texto) +
        '</prosody></voice></speak>'
      );
    };

    ws.onmessage = ev => {
      if (typeof ev.data === 'string') {
        if (ev.data.includes('Path:turn.end')) {
          clearTimeout(relogio);
          try { ws.close(); } catch {}
          if (!pedacos.length) return rejeitar(new Error('o serviço não devolveu áudio'));
          resolver(Buffer.concat(pedacos));
        }
        return;
      }
      const buf = Buffer.from(ev.data);
      const tamCabecalho = buf.readUInt16BE(0);
      const cabecalho = buf.subarray(2, 2 + tamCabecalho).toString('utf8');
      if (cabecalho.includes('Path:audio')) pedacos.push(buf.subarray(2 + tamCabecalho));
    };
  });
}

/* ------------------------------------------------------------------ */
const args = process.argv.slice(2);
const opcao = (nome, padrao) => {
  const i = args.indexOf('--' + nome);
  return i >= 0 && args[i + 1] ? args[i + 1] : padrao;
};

if (args.includes('--vozes')) {
  const vozes = await listarVozes();
  console.log('Vozes em português disponíveis (todas gratuitas):\n');
  vozes.forEach(v => console.log('  ' + v.ShortName.padEnd(34) + v.Gender + '  ' + v.Locale));
  process.exit(0);
}

const arquivo = args.find(a => !a.startsWith('--') && a.endsWith('.json'));
if (!arquivo) {
  console.error('Uso: node ferramentas/tts-edge.mjs projeto.json [--voz pt-BR-FranciscaNeural] [--saida ./narracao] [--ritmo -8%]');
  console.error('     node ferramentas/tts-edge.mjs --vozes');
  process.exit(1);
}

const voz = opcao('voz', 'pt-BR-FranciscaNeural');
const saida = opcao('saida', './narracao');
const ritmo = opcao('ritmo', '+0%');

const projeto = JSON.parse(await fs.readFile(arquivo, 'utf8'));
if (!projeto.cenas || !projeto.cenas.length) {
  console.error('Esse JSON não parece um projeto do UMM Studio: não tem "cenas".');
  process.exit(1);
}

await fs.mkdir(saida, { recursive: true });
console.log('Voz: ' + voz + '  ·  ritmo: ' + ritmo + '  ·  pasta: ' + saida + '\n');

let feitos = 0;
for (let i = 0; i < projeto.cenas.length; i++) {
  const texto = String(projeto.cenas[i].narracao || '').trim();
  const nome = 'cena-' + String(i + 1).padStart(2, '0') + '.mp3';
  if (!texto) { console.log('  cena ' + (i + 1) + ': sem narração, pulando'); continue; }
  process.stdout.write('  cena ' + (i + 1) + ': sintetizando… ');
  try {
    const mp3 = await sintetizar(prepararTexto(texto), voz, ritmo);
    await fs.writeFile(path.join(saida, nome), mp3);
    console.log(nome + '  (' + (mp3.length / 1024).toFixed(0) + ' kB)');
    feitos++;
  } catch (e) {
    console.log('falhou — ' + e.message);
  }
  await new Promise(r => setTimeout(r, 350));   /* respiro entre pedidos */
}

console.log('\n' + feitos + ' de ' + projeto.cenas.length + ' cenas narradas em ' + saida);
console.log('Agora abra o UMM Studio, escolha "Subir meus áudios por cena" na aba Voz');
console.log('e carregue cada arquivo no botão "áudio…" da cena correspondente.');
