"""Saída dos resultados: JSON, CSV e um painel HTML que abre no navegador."""

from __future__ import annotations

import csv
import json
import os
import datetime as dt

from .licencas import licenca_de
from .modelos import Video, duracao_legivel, numero_curto

COLUNAS_CSV = [
    "score", "risco", "fonte", "titulo", "autor", "licenca", "views",
    "velocidade_dia", "engajamento", "duracao", "publicado", "url",
    "download_url", "credito", "alertas",
]


def salvar_json(videos: list[Video], caminho: str) -> str:
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump([v.como_dict() for v in videos], f, ensure_ascii=False, indent=2)
    return caminho


def carregar_json(caminho: str) -> list[Video]:
    with open(caminho, encoding="utf-8") as f:
        return [Video.de_dict(d) for d in json.load(f)]


def salvar_csv(videos: list[Video], caminho: str) -> str:
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS_CSV, delimiter=";")
        w.writeheader()
        for v in videos:
            w.writerow({
                "score": f"{v.score:.1f}".replace(".", ","),
                "risco": v.risco,
                "fonte": v.fonte,
                "titulo": v.titulo,
                "autor": v.autor,
                "licenca": licenca_de(v).nome,
                "views": v.views,
                "velocidade_dia": int(v.velocidade_dia),
                "engajamento": f"{v.engajamento * 100:.2f}".replace(".", ",") + "%",
                "duracao": duracao_legivel(v.duracao_s),
                "publicado": v.publicado.isoformat() if v.publicado else "",
                "url": v.url,
                "download_url": v.download_url,
                "credito": v.credito,
                "alertas": " | ".join(v.alertas),
            })
    return caminho


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0d0d0d;color:#eee;font:15px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;padding:20px}
h1{font-size:22px;margin-bottom:4px}
.sub{color:#888;font-size:13px;margin-bottom:18px}
.barra{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}
.barra select,.barra input{background:#1c1c1c;color:#eee;border:1px solid #333;border-radius:8px;padding:8px 10px;font-size:14px}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:#161616;border:1px solid #262626;border-radius:12px;overflow:hidden;display:flex;flex-direction:column}
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;background:#222}
.corpo{padding:12px;display:flex;flex-direction:column;gap:8px;flex:1}
.tit{font-weight:600;font-size:15px;line-height:1.3}
.meta{color:#9a9a9a;font-size:12px}
.linha{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.tag{font-size:11px;padding:3px 7px;border-radius:999px;border:1px solid #333;color:#bbb}
.score{font-weight:700;font-size:13px;padding:3px 8px;border-radius:999px;background:#1f3a1f;color:#7ee07e;border:1px solid #2f5a2f}
.risco-BAIXO{background:#14331e;color:#6ee89a;border:1px solid #24603a}
.risco-MEDIO{background:#3a3113;color:#ecc55b;border:1px solid #6b5a1f}
.risco-ALTO{background:#3d1717;color:#f08a8a;border:1px solid #6d2626}
.risco{font-size:11px;padding:3px 8px;border-radius:999px;font-weight:600}
.alertas{font-size:12px;color:#c9a86a;border-left:2px solid #6b5a1f;padding-left:8px}
.acoes{display:flex;gap:8px;margin-top:auto;padding-top:8px}
.acoes a,.acoes button{flex:1;text-align:center;text-decoration:none;font-size:13px;padding:8px;border-radius:8px;border:1px solid #333;background:#1f1f1f;color:#ddd;cursor:pointer}
.acoes a:hover,.acoes button:hover{background:#2a2a2a}
.vazio{color:#777;padding:40px;text-align:center}
footer{margin-top:26px;color:#666;font-size:12px;border-top:1px solid #222;padding-top:14px;line-height:1.7}
"""

JS = """
const dados = __DADOS__;
const $ = s => document.querySelector(s);
function fmt(n){n=Number(n||0);
  for (const [l,s] of [[1e9,'B'],[1e6,'M'],[1e3,'k']]) if(n>=l) return (n/l).toFixed(1).replace(/\\.0$/,'')+s;
  return String(Math.round(n));}
function dur(s){if(!s)return '—';const m=Math.floor(s/60),r=s%60;return m+':'+String(r).padStart(2,'0');}
function card(v){
  const el = document.createElement('div'); el.className='card';
  el.innerHTML = `
    ${v.thumb?`<img loading="lazy" src="${v.thumb}" alt="">`:''}
    <div class="corpo">
      <div class="linha"><span class="score">${v.score.toFixed(0)}</span>
        <span class="risco risco-${v.risco}">risco ${v.risco}</span>
        <span class="tag">${v.fonte}</span></div>
      <div class="tit">${v.titulo}</div>
      <div class="meta">${v.autor||'autor não informado'} · ${fmt(v.views)} views · ${fmt(v.velocidade_dia)}/dia · ${dur(v.duracao_s)}</div>
      <div class="linha"><span class="tag">${v.licenca_nome}</span>${v.publicado?`<span class="tag">${v.publicado}</span>`:''}</div>
      ${v.alertas.length?`<div class="alertas">${v.alertas.join('<br>')}</div>`:''}
      <div class="acoes">
        <a href="${v.url}" target="_blank" rel="noopener">Abrir</a>
        ${v.download_url?`<a href="${v.download_url}" target="_blank" rel="noopener">Baixar</a>`:''}
        <button>Copiar crédito</button>
      </div>
    </div>`;
  el.querySelector('button').onclick = e => {
    navigator.clipboard.writeText(v.credito);
    e.target.textContent = 'Copiado!';
    setTimeout(()=>e.target.textContent='Copiar crédito', 1500);
  };
  return el;
}
function render(){
  const fonte=$('#f-fonte').value, risco=$('#f-risco').value, termo=$('#f-termo').value.toLowerCase();
  const ordem=$('#f-ordem').value;
  const niveis={BAIXO:0,MEDIO:1,ALTO:2};
  let lista = dados.filter(v =>
    (!fonte || v.fonte===fonte) &&
    (risco==='' || niveis[v.risco] <= Number(risco)) &&
    (!termo || (v.titulo+' '+v.autor+' '+(v.tags||[]).join(' ')).toLowerCase().includes(termo)));
  lista.sort((a,b)=> ordem==='views' ? b.views-a.views
                   : ordem==='velocidade' ? b.velocidade_dia-a.velocidade_dia
                   : b.score-a.score);
  const g=$('#grade'); g.innerHTML='';
  if(!lista.length){ g.innerHTML='<div class="vazio">Nada com esses filtros.</div>'; }
  lista.forEach(v => g.appendChild(card(v)));
  $('#contador').textContent = lista.length + ' de ' + dados.length + ' vídeos';
}
['#f-fonte','#f-risco','#f-ordem'].forEach(s=>$(s).onchange=render);
$('#f-termo').oninput = render;
render();
"""


def salvar_html(videos: list[Video], caminho: str, tema: str = "") -> str:
    payload = []
    for v in videos:
        d = v.como_dict()
        d["licenca_nome"] = licenca_de(v).nome
        payload.append(d)

    fontes = sorted({v.fonte for v in videos})
    opcoes_fonte = "".join(f'<option value="{f}">{f}</option>' for f in fontes)
    gerado = dt.datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Garimpo de vídeos — {tema or 'resultados'}</title>
<style>{CSS}</style></head><body>
<h1>Garimpo de vídeos livres de direitos</h1>
<div class="sub">Busca: <b>{tema or '—'}</b> · gerado em {gerado} · <span id="contador"></span></div>
<div class="barra">
  <input id="f-termo" placeholder="filtrar por palavra...">
  <select id="f-fonte"><option value="">todas as fontes</option>{opcoes_fonte}</select>
  <select id="f-risco">
    <option value="0">só risco BAIXO</option>
    <option value="1" selected>risco BAIXO e MÉDIO</option>
    <option value="">todos, inclusive ALTO</option>
  </select>
  <select id="f-ordem">
    <option value="score">ordenar por score</option>
    <option value="velocidade">ordenar por views/dia</option>
    <option value="views">ordenar por views totais</option>
  </select>
</div>
<div class="grade" id="grade"></div>
<footer>
  <b>Antes de publicar cada corte:</b><br>
  1. Confira a licença na página original — ela pode mudar depois da coleta.<br>
  2. Guarde print da página com a licença, na data em que você baixou.<br>
  3. Cole o crédito na descrição E deixe visível no vídeo quando a licença exigir.<br>
  4. Troque a trilha sonora por música livre: a licença do vídeo não cobre a música de terceiros.<br>
  5. Acrescente conteúdo seu (narração, comentário, corte editorial). Repost cru rende pouco alcance e nenhuma proteção.<br>
  <br>Isto é apoio operacional, não parecer jurídico.
</footer>
<script>{JS.replace('__DADOS__', json.dumps(payload, ensure_ascii=False))}</script>
</body></html>"""

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)
    return caminho


def imprimir_tabela(videos: list[Video], limite: int = 20) -> None:
    if not videos:
        print("\nNenhum vídeo encontrado com os filtros usados.")
        return
    print(f"\n{'#':>3} {'SCORE':>6} {'RISCO':<6} {'VIEWS':>8} {'/DIA':>8} {'DUR':>7}  TÍTULO")
    print("-" * 100)
    for i, v in enumerate(videos[:limite], 1):
        titulo = v.titulo if len(v.titulo) <= 46 else v.titulo[:45] + "…"
        print(f"{i:>3} {v.score:>6.1f} {v.risco:<6} {numero_curto(v.views):>8} "
              f"{numero_curto(v.velocidade_dia):>8} {duracao_legivel(v.duracao_s):>7}  {titulo}")
        print(f"{'':>4}{v.fonte} · {licenca_de(v).nome} · {v.url}")
    if len(videos) > limite:
        print(f"\n... e mais {len(videos) - limite}. O relatório completo está nos arquivos gerados.")


def garantir_pasta(caminho: str) -> str:
    os.makedirs(caminho, exist_ok=True)
    return caminho
