/*
 * Renderiza intro/index.html em MP4 (1920x1080, 30 fps, com áudio), quadro a quadro.
 * Uso (na pasta intro/):
 *   npm i --no-save playwright three@0.160.0
 *   node render-video.cjs && (veja o comando ffmpeg impresso no fim)
 * O CDN do three.js é redirecionado para node_modules/three, então funciona offline.
 */
const { chromium } = require('playwright');
const fs=require('fs'),path=require('path');
const [,, html='index.html', outDir='frames', FPS='30'] = process.argv;
(async()=>{
  const b = await chromium.launch({ args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport:{ width:1920, height:1080 } });
  p.on('pageerror',e=>console.log('ERR',e.message));
  await p.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', r=>{ const rel=r.request().url().split('three@0.160.0/')[1]; r.fulfill({ path: path.join(__dirname,'node_modules/three',rel), contentType:'application/javascript' }); });
  await p.goto('file://'+path.resolve(html)+'?render');
  await p.waitForFunction('window.__ready===true',null,{timeout:60000});
  fs.mkdirSync(outDir,{recursive:true});
  const wav = await p.evaluate(()=>window.__audioWav());
  fs.writeFileSync(path.join(outDir,'audio.wav'), Buffer.from(wav,'base64'));
  const N = 15*FPS;
  for (let i=0;i<N;i++){
    await p.evaluate(t=>window.__renderFrame(t), i/FPS);
    await p.screenshot({ path: path.join(outDir, `${String(i).padStart(4,'0')}.jpg`), type:'jpeg', quality:95 });
    if(i%50===0) console.log('frame',i);
  }
  await b.close();
})();
console.log(`ffmpeg -framerate 30 -i frames/%04d.jpg -i frames/audio.wav -c:v libx264 -b:v 6M -pix_fmt yuv420p -af "volume=-3dB,alimiter=limit=0.89" -c:a aac -b:a 192k -shortest umm-hora-a-hora-15s.mp4`);
