/* UMM Studio — aplicação
   Junta roteiro, prévia, verificador do padrão, voz e exportação. */

(function (U) {
  'use strict';

  const $ = s => document.querySelector(s);
  const esc = s => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

  const CHAVE = 'umm.studio.projeto';

  let projeto = null;
  let motor = null;
  let sel = 0;
  let tocando = false;
  let t = 0;
  let ultimoQuadro = 0;
  let trilha = null;
  let fonteAudio = null;
  let relatorio = null;

  const tela = $('#tela');
  const ctx = tela.getContext('2d');

  /* =============================================================
     Início
     ============================================================= */
  function iniciar() {
    montarSelects();
    projeto = carregarLocal() || clonar(U.MODELOS[0].projeto);
    motor = new U.Motor(projeto);
    ligarEventos();
    aplicarProjetoNaTopo();
    /* Abre num instante em que a primeira cena já apareceu — t=0 mostraria a tela quase vazia. */
    t = Math.min(1.2, motor.duracoes[0] * 0.7);
    reconstruir();
    window.addEventListener('resize', function () { ajustarTela(); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(desenhar);
  }

  const clonar = o => JSON.parse(JSON.stringify(o));

  function montarSelects() {
    $('#formato').innerHTML = Object.keys(U.FORMATOS)
      .map(k => '<option value="' + k + '">' + esc(U.FORMATOS[k].rotulo) + '</option>').join('');

    $('#clima').innerHTML = Object.keys(U.CLIMAS)
      .map(k => '<option value="' + k + '">' + esc(U.CLIMAS[k].rotulo) + '</option>').join('');

    $('#modelos').innerHTML =
      '<option value="">Começar de um modelo…</option>' +
      U.MODELOS.map(m => '<option value="' + m.chave + '">' + esc(m.nome) + ' — ' + esc(m.resumo) + '</option>').join('') +
      '<option value="__vazio">Roteiro em branco (3 cenas)</option>';

    $('#voz-id').innerHTML = U.Voz.VOZES_SUGERIDAS
      .map(v => '<option value="' + esc(v.id) + '">' + esc(v.rotulo) + '</option>').join('');
  }

  function aplicarProjetoNaTopo() {
    $('#titulo-projeto').value = projeto.titulo || '';
    $('#formato').value = projeto.formato;
    $('#clima').value = projeto.clima || 'claro';
    $('#area-segura').checked = !!projeto.areaSegura;
    $('#fps').value = String(projeto.fps || 30);
    $('#escala').value = String(projeto.escala || 1);
    $('#provedor-voz').value = (projeto.voz && projeto.voz.provedor) || 'nenhum';
    if (projeto.voz && projeto.voz.vozId) $('#voz-id').value = projeto.voz.vozId;
    trocarProvedor();
  }

  /* =============================================================
     Ciclo de atualização
     ============================================================= */
  /* O canvas tem 1080x1920 de verdade; aqui só calculamos o tamanho em CSS,
     porque deixar as duas restrições para o navegador distorce a proporção. */
  function ajustarTela() {
    const area = tela.parentElement;
    const r = area.getBoundingClientRect();
    const disp = Math.max(120, r.width - 32);
    const alt = Math.max(120, r.height - 32);
    const escala = Math.min(disp / tela.width, alt / tela.height);
    tela.style.width = Math.floor(tela.width * escala) + 'px';
    tela.style.height = Math.floor(tela.height * escala) + 'px';
  }

  function reconstruir() {
    const f = U.FORMATOS[projeto.formato] || U.FORMATOS['9x16'];
    if (tela.width !== f.w || tela.height !== f.h) { tela.width = f.w; tela.height = f.h; }
    ajustarTela();
    motor.recalcular();
    if (sel >= projeto.cenas.length) sel = Math.max(0, projeto.cenas.length - 1);
    renderLista();
    verificar();
    atualizarTempo();
    desenhar();
    const alvo = $('#resolucao');
    if (alvo) alvo.textContent = resolucaoAtual();
    salvarLocal();
  }

  function desenhar() {
    motor.sincronizarMidias(t, tocando);
    motor.desenhar(ctx, t, {
      legendas: $('#ver-legendas').checked,
      guias: $('#ver-guias').checked
    });
  }

  function atualizarTempo() {
    const d = motor.duracao || 0;
    $('#tempo').textContent = t.toFixed(1).replace('.', ',') + 's / ' + d.toFixed(1).replace('.', ',') + 's';
    $('#linha-tempo').value = String(d ? Math.round((t / d) * 1000) : 0);
    $('#resumo-roteiro').textContent = projeto.cenas.length + ' cenas · ' + d.toFixed(1).replace('.', ',') + 's';
  }

  /* =============================================================
     Lista de cenas + editor
     ============================================================= */
  function renderLista() {
    const porCena = {};
    if (relatorio) {
      relatorio.itens.forEach(function (it) {
        if (!it.cena) return;
        const atual = porCena[it.cena];
        if (!atual || (atual !== 'erro' && it.nivel === 'erro')) porCena[it.cena] = it.nivel;
      });
    }

    $('#lista-cenas').innerHTML = projeto.cenas.map(function (c, i) {
      const ativo = i === sel;
      const vis = U.VISUAIS[c.visual];
      const nivel = porCena[i + 1];
      return '<article class="cena' + (ativo ? ' ativa' : '') + '" data-i="' + i + '">' +
        '<div class="cabeca" data-acao="selecionar">' +
          '<span class="num">' + (i + 1) + '</span>' +
          '<span class="resumo">' +
            '<b class="' + (c.titulo ? '' : 'vazio') + '">' + esc(c.titulo || 'sem texto na tela') + '</b>' +
            '<small><span class="tipo-chip ' + esc(c.tipo) + '">' + esc(c.tipo) + '</span> ' +
              esc(vis ? vis.rotulo : c.visual) + ' · ' + motor.duracoes[i].toFixed(1).replace('.', ',') + 's</small>' +
          '</span>' +
          (nivel ? '<span class="aviso-ponto ' + nivel + '"></span>' : '') +
        '</div>' +
        (ativo ? editor(c, i) : '') +
      '</article>';
    }).join('');
  }

  function editor(c, i) {
    const vis = U.VISUAIS[c.visual] || {};
    const palavrasT = (c.titulo || '').trim().split(/\s+/).filter(Boolean).length;
    const palavrasN = (c.narracao || '').trim().split(/\s+/).filter(Boolean).length;
    const temAudio = !!motor.audio[i];
    const temMidia = !!motor.midias[i];

    return '<div class="corpo">' +
      '<div class="linha-campos">' +
        '<label class="campo"><span>Papel na história</span>' +
          '<select data-campo="tipo">' + ['gancho', 'contexto', 'dado', 'passo', 'comparativo', 'alerta', 'cta']
            .map(v => '<option' + (c.tipo === v ? ' selected' : '') + '>' + v + '</option>').join('') +
          '</select></label>' +
        '<label class="campo"><span>Cena concreta</span>' +
          '<select data-campo="visual">' + U.LISTA_VISUAIS
            .map(v => '<option value="' + v + '"' + (c.visual === v ? ' selected' : '') + '>' +
              esc(U.VISUAIS[v].rotulo) + '</option>').join('') +
          '</select></label>' +
      '</div>' +
      (vis.dica ? '<p class="ajuda">' + esc(vis.dica) + '</p>' : '') +

      '<label class="campo"><span>Texto grande na tela <em>' + palavrasT + ' palavras</em></span>' +
        '<textarea data-campo="titulo" rows="2" placeholder="A ideia da cena em até 8 palavras">' + esc(c.titulo) + '</textarea></label>' +

      '<div class="linha-campos">' +
        '<label class="campo"><span>Selo</span>' +
          '<input type="text" data-campo="selo" value="' + esc(c.selo) + '" placeholder="opcional"/></label>' +
        '<label class="campo"><span>Duração <em>0 = auto</em></span>' +
          '<input type="number" data-campo="dur" min="0" max="20" step="0.1" value="' + (c.dur || 0) + '"/></label>' +
      '</div>' +

      '<div class="linha-campos">' +
        '<label class="campo"><span>Tom</span>' +
          '<select data-campo="tom">' +
            '<option value="claro"' + (c.tom !== 'escuro' ? ' selected' : '') + '>Clima do projeto</option>' +
            '<option value="escuro"' + (c.tom === 'escuro' ? ' selected' : '') + '>Escuro — dívida, juros, vencimento</option>' +
          '</select></label>' +
        '<label class="campo"><span>Mídia própria ' +
          (temMidia ? '<em>' + esc(c.midiaNome || 'carregada') + '</em>' : '') + '</span>' +
          '<span style="display:flex;gap:6px">' +
            '<button class="btn mini" data-acao="midia" type="button" style="flex:1">' +
              (temMidia ? 'trocar…' : 'imagem ou vídeo…') + '</button>' +
            (temMidia ? '<button class="btn mini" data-acao="tirar-midia" type="button">tirar</button>' : '') +
          '</span>' +
          '<input type="file" accept="image/*,video/*" data-acao="arquivo-midia" hidden/></label>' +
      '</div>' +
      (temMidia
        ? '<label class="opcao-linha"><input type="checkbox" data-campo="midiaCheia"' +
            (c.midiaCheia ? ' checked' : '') + '/> usar a mídia no quadro inteiro, com véu por trás do texto</label>'
        : '') +

      '<label class="campo"><span>Linha de apoio</span>' +
        '<input type="text" data-campo="apoio" value="' + esc(c.apoio) + '" placeholder="opcional, menor, embaixo do título"/></label>' +

      '<label class="campo"><span>Dados do visual ' +
        '<button class="btn mini fantasma" data-acao="exemplo" type="button">usar exemplo</button></span>' +
        '<textarea data-campo="dados" rows="4" placeholder="' + esc(vis.exemplo || '') + '">' + esc(c.dados) + '</textarea></label>' +

      '<label class="campo"><span>Narração <em>' + palavrasN + ' palavras · ~' +
        motor.duracoes[i].toFixed(1).replace('.', ',') + 's' + (temAudio ? ' · áudio pronto' : '') + '</em></span>' +
        '<textarea data-campo="narracao" rows="3" placeholder="Uma frase que faz sentido de olhos fechados">' + esc(c.narracao) + '</textarea></label>' +

      '<div class="acoes">' +
        '<button class="btn mini" data-acao="ouvir">ouvir</button>' +
        '<button class="btn mini" data-acao="audio">áudio…</button>' +
        '<input type="file" accept="audio/*" data-acao="arquivo-audio" hidden/>' +
        (temAudio ? '<button class="btn mini" data-acao="tirar-audio">tirar áudio</button>' : '') +
        '<span class="espaco" style="flex:1"></span>' +
        '<button class="btn mini" data-acao="subir" ' + (i === 0 ? 'disabled' : '') + '>↑</button>' +
        '<button class="btn mini" data-acao="descer" ' + (i === projeto.cenas.length - 1 ? 'disabled' : '') + '>↓</button>' +
        '<button class="btn mini" data-acao="duplicar">duplicar</button>' +
        '<button class="btn mini" data-acao="remover" ' + (projeto.cenas.length < 2 ? 'disabled' : '') + '>remover</button>' +
      '</div>' +
    '</div>';
  }

  /* =============================================================
     Verificador do padrão
     ============================================================= */
  function verificar() {
    relatorio = U.verificarPadrao(projeto, motor);

    const cor = relatorio.nota >= 85 ? 'var(--acento)' : relatorio.nota >= 60 ? '#C98A16' : 'var(--alerta)';
    $('#nota-valor').innerHTML = relatorio.nota + '<small>/100</small>';
    $('#nota-valor').style.color = cor;
    $('#nota-desc').textContent = relatorio.itens.length
      ? relatorio.erros + ' ' + (relatorio.erros === 1 ? 'erro' : 'erros') + ' · ' +
        relatorio.avisos + ' ' + (relatorio.avisos === 1 ? 'aviso' : 'avisos')
      : 'O roteiro está dentro do padrão: entende no mudo, entende no escuro.';

    const badge = $('#badge-padrao');
    if (relatorio.itens.length) { badge.hidden = false; badge.textContent = String(relatorio.itens.length); }
    else badge.hidden = true;

    $('#lista-regras').innerHTML = relatorio.itens.length
      ? relatorio.itens.map(function (it) {
          return '<div class="regra ' + it.nivel + '"' + (it.cena ? ' data-ir="' + (it.cena - 1) + '"' : '') + '>' +
            '<div class="marca-regra">' + esc(rotuloRegra(it.regra)) + (it.cena ? ' · cena ' + it.cena : '') + '</div>' +
            '<div class="msg">' + esc(it.msg) + '</div>' +
            '<div class="como">' + esc(it.comoResolver) + '</div>' +
          '</div>';
        }).join('')
      : '<div class="tudo-certo">Nada a corrigir.</div>';

    $('#leitura-muda').textContent = relatorio.leituraMuda;
    $('#leitura-cega').textContent = relatorio.leituraCega || '(sem narração)';
  }

  function rotuloRegra(r) {
    return {
      'sem-audio': 'entende sem áudio',
      'sem-video': 'entende sem vídeo',
      'texto-grande': 'texto grande',
      'concreta': 'cena concreta',
      'faceless': 'faceless',
      'portugues': 'português',
      'estetica': 'estética',
      'ritmo': 'ritmo',
      'estrutura': 'estrutura'
    }[r] || r;
  }

  /* =============================================================
     Reprodução
     ============================================================= */
  function tocar() {
    if (tocando) return pausar();
    if (t >= motor.duracao - 0.05) t = 0;
    tocando = true;
    $('#btn-tocar').textContent = '❚❚';
    if (trilha) {
      const ac = U.Voz.audioContext();
      fonteAudio = ac.createBufferSource();
      fonteAudio.buffer = trilha;
      fonteAudio.connect(ac.destination);
      fonteAudio.start(0, Math.min(t, trilha.duration));
    }
    ultimoQuadro = performance.now();
    requestAnimationFrame(passo);
  }

  function pausar() {
    tocando = false;
    $('#btn-tocar').textContent = '▶';
    pararAudio();
  }

  function pararAudio() {
    if (fonteAudio) { try { fonteAudio.stop(); } catch (e) { /* já parou */ } fonteAudio = null; }
  }

  function passo(agora) {
    if (!tocando) return;
    t += (agora - ultimoQuadro) / 1000;
    ultimoQuadro = agora;
    if (t >= motor.duracao) { t = motor.duracao; pausar(); }
    desenhar();
    atualizarTempo();
    if (tocando) requestAnimationFrame(passo);
  }

  /* =============================================================
     Eventos
     ============================================================= */
  function ligarEventos() {
    $('#titulo-projeto').addEventListener('input', e => { projeto.titulo = e.target.value; salvarLocal(); });
    $('#formato').addEventListener('change', e => { projeto.formato = e.target.value; reconstruir(); });
    $('#clima').addEventListener('change', e => { projeto.clima = e.target.value; reconstruir(); });
    $('#area-segura').addEventListener('change', e => { projeto.areaSegura = e.target.checked; reconstruir(); });
    $('#fps').addEventListener('change', e => { projeto.fps = Number(e.target.value); salvarLocal(); });
    $('#escala').addEventListener('change', e => { projeto.escala = Number(e.target.value); reconstruir(); });
    $('#ver-legendas').addEventListener('change', desenhar);
    $('#ver-guias').addEventListener('change', desenhar);

    $('#modelos').addEventListener('change', function (e) {
      const v = e.target.value;
      if (!v) return;
      if (!confirm('Isso substitui o roteiro atual. Continuar?')) { e.target.value = ''; return; }
      Object.keys(motor.midias).forEach(k => soltarMidia(Number(k)));
      projeto = v === '__vazio' ? U.modeloVazio() : clonar(U.MODELOS.find(m => m.chave === v).projeto);
      motor = new U.Motor(projeto);
      trilha = null; sel = 0; t = 0;
      e.target.value = '';
      aplicarProjetoNaTopo();
      reconstruir();
    });

    $('#btn-add-cena').addEventListener('click', function () {
      projeto.cenas.splice(sel + 1, 0, U.novaCena({ tipo: 'dado', visual: 'numero' }));
      deslocarAnexos(sel + 1, 1);
      sel = sel + 1;
      reconstruir();
    });

    $('#btn-tocar').addEventListener('click', tocar);
    $('#linha-tempo').addEventListener('input', function (e) {
      pausar();
      t = (Number(e.target.value) / 1000) * motor.duracao;
      desenhar(); atualizarTempo();
    });

    /* --- lista de cenas (delegação) --- */
    const lista = $('#lista-cenas');
    lista.addEventListener('click', function (e) {
      const alvo = e.target.closest('[data-acao]');
      const art = e.target.closest('.cena');
      if (!art) return;
      const i = Number(art.dataset.i);
      if (!alvo) return;
      const acao = alvo.dataset.acao;

      if (acao === 'selecionar') { sel = (sel === i ? sel : i); renderLista(); pularParaCena(i); return; }
      if (acao === 'exemplo') {
        const vis = U.VISUAIS[projeto.cenas[i].visual];
        projeto.cenas[i].dados = (vis && vis.exemplo) || '';
        reconstruir(); return;
      }
      if (acao === 'ouvir') {
        U.Voz.falarPreview(projeto.cenas[i].narracao || projeto.cenas[i].titulo, 1);
        return;
      }
      if (acao === 'audio') { art.querySelector('[data-acao="arquivo-audio"]').click(); return; }
      if (acao === 'midia') { art.querySelector('[data-acao="arquivo-midia"]').click(); return; }
      if (acao === 'tirar-midia') {
        soltarMidia(i);
        delete projeto.cenas[i].midiaNome;
        projeto.cenas[i].midiaCheia = false;
        reconstruir(); return;
      }
      if (acao === 'tirar-audio') { delete motor.audio[i]; refazerTrilha(); reconstruir(); return; }
      if (acao === 'subir' && i > 0) { mover(i, i - 1); return; }
      if (acao === 'descer' && i < projeto.cenas.length - 1) { mover(i, i + 1); return; }
      if (acao === 'duplicar') {
        projeto.cenas.splice(i + 1, 0, Object.assign(clonar(projeto.cenas[i]), { id: U.id() }));
        deslocarAnexos(i + 1, 1); sel = i + 1; reconstruir(); return;
      }
      if (acao === 'remover' && projeto.cenas.length > 1) {
        projeto.cenas.splice(i, 1);
        delete motor.audio[i];
        soltarMidia(i);
        deslocarAnexos(i, -1);
        if (sel >= projeto.cenas.length) sel = projeto.cenas.length - 1;
        refazerTrilha(); reconstruir(); return;
      }
    });

    lista.addEventListener('input', function (e) {
      const campo = e.target.dataset.campo;
      if (!campo) return;
      const i = Number(e.target.closest('.cena').dataset.i);
      projeto.cenas[i][campo] = campo === 'dur' ? Number(e.target.value) : e.target.value;
      motor.recalcular();
      verificar();
      atualizarTempo();
      pularParaCena(i, true);
      atualizarResumoCena(i);
      salvarLocal();
    });

    lista.addEventListener('change', function (e) {
      const campo = e.target.dataset.campo;
      if (campo === 'tipo' || campo === 'visual') reconstruir();
      if (e.target.dataset.acao === 'arquivo-audio' && e.target.files[0]) {
        const i = Number(e.target.closest('.cena').dataset.i);
        carregarAudioCena(i, e.target.files[0]);
      }
      if (e.target.dataset.acao === 'arquivo-midia' && e.target.files[0]) {
        const i = Number(e.target.closest('.cena').dataset.i);
        carregarMidiaCena(i, e.target.files[0]);
      }
      if (e.target.dataset.campo === 'midiaCheia') {
        const i = Number(e.target.closest('.cena').dataset.i);
        projeto.cenas[i].midiaCheia = e.target.checked;
        desenhar(); salvarLocal();
      }
    });

    $('#lista-regras').addEventListener('click', function (e) {
      const r = e.target.closest('[data-ir]');
      if (!r) return;
      sel = Number(r.dataset.ir);
      renderLista();
      pularParaCena(sel);
      const art = $('.cena.ativa');
      if (art) art.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });

    /* --- abas --- */
    document.querySelectorAll('.aba').forEach(function (b) {
      b.addEventListener('click', function () {
        document.querySelectorAll('.aba').forEach(x => x.classList.remove('ativa'));
        b.classList.add('ativa');
        document.querySelectorAll('.conteudo-aba').forEach(x => x.classList.add('oculto'));
        $('#aba-' + b.dataset.aba).classList.remove('oculto');
      });
    });

    /* --- projeto --- */
    $('#btn-salvar').addEventListener('click', function () {
      U.Exportar.baixarTexto(JSON.stringify(projeto, semInternos, 2),
        U.Exportar.nomeArquivo(projeto, 'json'), 'application/json');
    });
    $('#btn-abrir').addEventListener('click', () => $('#arquivo-projeto').click());
    $('#arquivo-projeto').addEventListener('change', function (e) {
      const f = e.target.files[0];
      if (!f) return;
      const leitor = new FileReader();
      leitor.onload = function () {
        try {
          const p = JSON.parse(leitor.result);
          if (!p.cenas || !p.cenas.length) throw new Error('sem cenas');
          projeto = p;
          motor = new U.Motor(projeto);
          trilha = null; sel = 0; t = 0;
          aplicarProjetoNaTopo();
          reconstruir();
        } catch (err) { alert('Não consegui ler esse arquivo: ' + err.message); }
      };
      leitor.readAsText(f);
      e.target.value = '';
    });

    ligarVoz();
    ligarExportacao();

    document.addEventListener('keydown', function (e) {
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
      if (e.code === 'Space') { e.preventDefault(); tocar(); }
    });
  }

  function semInternos(chave, valor) { return chave === '_legendas' ? undefined : valor; }

  function resolucaoAtual() {
    const L = U.layout(projeto);
    return L.W + '×' + L.H;
  }

  function atualizarResumoCena(i) {
    const art = document.querySelector('.cena[data-i="' + i + '"]');
    if (!art) return;
    const b = art.querySelector('.resumo b');
    const c = projeto.cenas[i];
    b.textContent = c.titulo || 'sem texto na tela';
    b.className = c.titulo ? '' : 'vazio';
  }

  function mover(de, para) {
    const c = projeto.cenas.splice(de, 1)[0];
    projeto.cenas.splice(para, 0, c);
    [ 'audio', 'midias' ].forEach(function (campo) {
      const a = motor[campo][de], b = motor[campo][para];
      if (a) motor[campo][para] = a; else delete motor[campo][para];
      if (b) motor[campo][de] = b; else delete motor[campo][de];
    });
    sel = para;
    refazerTrilha();
    reconstruir();
  }

  /* Inserir ou remover cena renumera as cenas: os anexos precisam acompanhar. */
  function deslocarAnexos(apartir, delta) {
    ['audio', 'midias'].forEach(function (campo) {
      const novo = {};
      Object.keys(motor[campo]).forEach(function (k) {
        const i = Number(k);
        novo[i >= apartir ? i + delta : i] = motor[campo][k];
      });
      motor[campo] = novo;
    });
  }

  function pularParaCena(i, manterSeDentro) {
    const ini = motor.inicios[i], fim = ini + motor.duracoes[i];
    if (manterSeDentro && t >= ini && t < fim) { desenhar(); return; }
    pausar();
    t = ini + Math.min(0.9, motor.duracoes[i] * 0.55);
    desenhar();
    atualizarTempo();
  }

  /* =============================================================
     Voz
     ============================================================= */
  function trocarProvedor() {
    const v = $('#provedor-voz').value;
    $('#bloco-piper').hidden = v !== 'piper';
    $('#bloco-arquivos').hidden = v !== 'arquivos';
  }

  function ligarVoz() {
    $('#provedor-voz').addEventListener('change', async function (e) {
      projeto.voz.provedor = e.target.value;
      trocarProvedor();
      salvarLocal();
      if (e.target.value === 'piper') {
        statusVoz('Procurando as vozes em português…');
        try {
          const vozes = await U.Voz.vozesPiper();
          $('#voz-id').innerHTML = vozes.map(v =>
            '<option value="' + esc(v.id) + '">' + esc(v.rotulo) + '</option>').join('');
          if (projeto.voz.vozId) $('#voz-id').value = projeto.voz.vozId;
          statusVoz('');
        } catch (err) { statusVoz(err.message, 'erro'); }
      }
    });

    $('#voz-id').addEventListener('change', e => { projeto.voz.vozId = e.target.value; salvarLocal(); });

    $('#btn-gerar-voz').addEventListener('click', async function () {
      const btn = this;
      btn.disabled = true;
      $('#barra-voz').hidden = false;
      try {
        await U.Voz.gerarNarracoes(motor, { vozId: $('#voz-id').value }, function (p) {
          $('#barra-voz').firstElementChild.style.width = Math.round((p.k || 0) * 100) + '%';
          statusVoz(p.texto);
        });
        await refazerTrilha();
        reconstruir();
        statusVoz('Narração pronta. A duração das cenas passou a seguir o áudio.', 'ok');
      } catch (err) {
        statusVoz(err.message, 'erro');
      } finally {
        btn.disabled = false;
        $('#barra-voz').hidden = true;
      }
    });

    $('#btn-ouvir-cena').addEventListener('click', function () {
      const c = projeto.cenas[sel];
      if (!U.Voz.falarPreview(c.narracao || c.titulo, 1)) {
        statusVoz('Este navegador não tem voz do sistema.', 'erro');
      }
    });
    $('#btn-parar-voz').addEventListener('click', U.Voz.pararPreview);

    $('#btn-baixar-wav').addEventListener('click', async function () {
      await refazerTrilha();
      if (!trilha) return statusVoz('Não há narração para exportar.', 'erro');
      U.Exportar.baixar(U.Voz.paraWav(trilha), 'narracao.wav');
    });

    $('#btn-limpar-voz').addEventListener('click', function () {
      motor.audio = {};
      trilha = null;
      reconstruir();
      atualizarEstadoNarracao();
    });
  }

  function statusVoz(texto, tom) {
    const el = $('#status-voz');
    el.innerHTML = texto ? '<div class="aviso-caixa ' + (tom || '') + '">' + esc(texto) + '</div>' : '';
  }

  async function carregarAudioCena(i, arquivo) {
    try {
      motor.audio[i] = await U.Voz.decodificar(arquivo);
      await refazerTrilha();
      reconstruir();
    } catch (e) {
      alert('Não consegui ler esse áudio: ' + e.message);
    }
  }

  /* Mídia própria: imagem ou vídeo, guardados só na memória desta aba. */
  function soltarMidia(i) {
    const el = motor.midias[i];
    if (el && el.src && el.src.indexOf('blob:') === 0) URL.revokeObjectURL(el.src);
    delete motor.midias[i];
  }

  function carregarMidiaCena(i, arquivo) {
    soltarMidia(i);
    const url = URL.createObjectURL(arquivo);
    const ehVideo = /^video\//.test(arquivo.type);
    const el = document.createElement(ehVideo ? 'video' : 'img');
    el.src = url;
    if (ehVideo) { el.muted = true; el.playsInline = true; el.preload = 'auto'; el.loop = true; }

    const pronto = function () {
      motor.midias[i] = el;
      projeto.cenas[i].midiaNome = arquivo.name;
      if (projeto.cenas[i].visual !== 'midia' && !projeto.cenas[i].midiaCheia) {
        projeto.cenas[i].visual = 'midia';
      }
      reconstruir();
    };
    const falhou = function () {
      URL.revokeObjectURL(url);
      alert('Não consegui ler esse arquivo. Imagens: PNG, JPG, WEBP. Vídeos: MP4 ou WEBM que o navegador saiba tocar.');
    };
    if (ehVideo) {
      el.onloadeddata = pronto;
      el.onerror = falhou;
    } else {
      el.onload = pronto;
      el.onerror = falhou;
    }
  }

  async function refazerTrilha() {
    try { trilha = await U.Voz.montarTrilha(motor); }
    catch (e) { trilha = null; }
    atualizarEstadoNarracao();
    return trilha;
  }

  function atualizarEstadoNarracao() {
    const n = Object.keys(motor.audio).length;
    const el = $('#estado-narracao');
    if (!n) {
      el.className = 'aviso-caixa';
      el.textContent = 'Nenhuma cena tem áudio ainda. O vídeo sai mudo, com legenda gravada.';
    } else {
      el.className = 'aviso-caixa ok';
      el.textContent = n + ' de ' + projeto.cenas.length + ' cenas com narração' +
        (trilha ? ' · trilha de ' + trilha.duration.toFixed(1).replace('.', ',') + 's' : '') + '.';
    }
  }

  /* =============================================================
     Exportação
     ============================================================= */
  function ligarExportacao() {
    $('#btn-mp4').addEventListener('click', () => exportarVideo('mp4'));
    $('#btn-gravar').addEventListener('click', () => exportarVideo('gravar'));
    $('#btn-quadros').addEventListener('click', () => exportarVideo('quadros'));

    $('#btn-srt').addEventListener('click', () =>
      U.Exportar.baixarTexto(motor.srt(), U.Exportar.nomeArquivo(projeto, 'srt')));
    $('#btn-roteiro').addEventListener('click', () =>
      U.Exportar.baixarTexto(motor.roteiro(), U.Exportar.nomeArquivo(projeto, 'md'), 'text/markdown'));
    $('#btn-json').addEventListener('click', () =>
      U.Exportar.baixarTexto(JSON.stringify(projeto, semInternos, 2),
        U.Exportar.nomeArquivo(projeto, 'json'), 'application/json'));
  }

  async function exportarVideo(modo) {
    pausar();
    const botoes = ['#btn-mp4', '#btn-gravar', '#btn-quadros'].map($);
    botoes.forEach(b => b.disabled = true);
    $('#barra-export').hidden = false;
    const legendas = $('#legendas-export').value === '1';
    const fps = Number($('#fps').value) || 30;

    const aoProgredir = function (p) {
      $('#barra-export').firstElementChild.style.width = Math.round((p.k || 0) * 100) + '%';
      statusExport(p.texto);
    };

    try {
      await refazerTrilha();
      if (modo === 'mp4') {
        const r = await U.Exportar.videoExato(motor, tela, { fps, legendas, trilha, aoProgredir });
        const nome = U.Exportar.nomeArquivo(projeto, r.extensao);
        U.Exportar.baixar(r.blob, nome);
        const mb = (r.blob.size / 1048576).toFixed(1).replace('.', ',');
        statusExport('WebM salvo — ' + mb + ' MB. O YouTube aceita direto. ' +
          'Para Instagram e TikTok, converta de graça com: ffmpeg -i ' + nome +
          ' -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -c:a aac video.mp4', 'ok');
      } else if (modo === 'gravar') {
        statusExport('Gravando em tempo real. Deixe esta aba visível até o fim.');
        const r = await U.Exportar.gravar(motor, tela, { fps, legendas, trilha, aoProgredir });
        U.Exportar.baixar(r.blob, U.Exportar.nomeArquivo(projeto, r.extensao));
        statusExport('Vídeo salvo em .' + r.extensao + ' — ' +
          (r.blob.size / 1048576).toFixed(1).replace('.', ',') + ' MB.', 'ok');
      } else {
        const zip = await U.Exportar.quadrosPNG(motor, tela, { fps, legendas, aoProgredir });
        U.Exportar.baixar(zip, U.Exportar.nomeArquivo(projeto, 'zip'));
        if (trilha) U.Exportar.baixar(U.Voz.paraWav(trilha), 'narracao.wav');
        statusExport('Quadros salvos. Rode montar.sh dentro da pasta descompactada.', 'ok');
      }
    } catch (e) {
      statusExport(e.message, 'erro');
    } finally {
      botoes.forEach(b => b.disabled = false);
      $('#barra-export').hidden = true;
      t = 0;
      desenhar();
      atualizarTempo();
    }
  }

  function statusExport(texto, tom) {
    $('#status-export').innerHTML = texto
      ? '<div class="aviso-caixa ' + (tom || '') + '">' + esc(texto) + '</div>' : '';
  }

  /* =============================================================
     Persistência local
     ============================================================= */
  let timerSalvar = null;
  function salvarLocal() {
    clearTimeout(timerSalvar);
    timerSalvar = setTimeout(function () {
      try { localStorage.setItem(CHAVE, JSON.stringify(projeto, semInternos)); }
      catch (e) { /* modo privativo: segue sem salvar */ }
    }, 400);
  }

  function carregarLocal() {
    try {
      const s = localStorage.getItem(CHAVE);
      if (!s) return null;
      const p = JSON.parse(s);
      return (p && p.cenas && p.cenas.length) ? p : null;
    } catch (e) { return null; }
  }

  iniciar();

})(window.UMM);
