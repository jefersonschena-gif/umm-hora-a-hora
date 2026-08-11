/* UMM Studio — verificador do PADRÃO
   O padrão pedido, virado em regra checável:

   1. O vídeo se entende SEM áudio  -> toda cena tem texto grande e legível.
   2. O áudio se entende SEM vídeo  -> a narração não aponta para a imagem
                                       e fala os números que estão na tela.
   3. Estética fintech premium clara -> paleta e ritmo sob controle.
   4. Faceless                       -> nada de rosto, nada de "eu apareço".
   5. Texto grande em português      -> fonte mínima e vocabulário em pt-BR.
   6. Cenas concretas                -> objeto na tela, não só tipografia. */

(function (U) {
  'use strict';

  /* Referência visual explícita: quebra o "áudio entende sem vídeo". */
  const DEIXIS_FORTE = [
    [/\bna tela\b/, 'na tela'],
    [/\bnesta tela\b/, 'nesta tela'],
    [/\bna imagem\b/, 'na imagem'],
    [/\bna figura\b/, 'na figura'],
    [/\bno video\b/, 'no vídeo'],
    [/\bacima\b(?!\s+de\b)/, 'acima'],
    [/\babaixo\b(?!\s+de\b)/, 'abaixo'],
    [/\bao lado\b/, 'ao lado'],
    [/\bdo lado\b/, 'do lado'],
    [/\ba direita\b/, 'à direita'],
    [/\ba esquerda\b/, 'à esquerda'],
    [/\bem cima\b(?!\s+de\b)/, 'em cima'],
    [/\bembaixo\b(?!\s+de\b)/, 'embaixo'],
    [/\bisso aqui\b/, 'isso aqui'],
    [/\besse aqui\b/, 'esse aqui'],
    [/\bessa aqui\b/, 'essa aqui'],
    [/\baqui (em cima|embaixo|na tela|do lado)\b/, 'aqui + posição'],
    [/\bolha aqui\b/, 'olha aqui'],
    [/\bveja aqui\b/, 'veja aqui'],
    [/\bcomo voce ve\b/, 'como você vê'],
    [/\bcomo voces veem\b/, 'como vocês veem'],
    [/\bprimeira (coluna|linha|barra)\b/, 'primeira coluna/linha'],
    [/\bsegunda (coluna|linha|barra)\b/, 'segunda coluna/linha'],
    [/\bclique no botao\b/, 'clique no botão'],
    [/\baperte aqui\b/, 'aperte aqui'],
    [/\barrast[ae] (pra|para) cima\b/, 'arrasta pra cima']
  ];

  /* Dêixis fraca: costuma indicar que a fala se apoiou na imagem. */
  const DEIXIS_FRACA = [
    [/\bveja\b/, 'veja'], [/\bvejam\b/, 'vejam'], [/\bolha so\b/, 'olha só'],
    [/\bolhe\b/, 'olhe'], [/\brepare\b/, 'repare'], [/\bperceb[ae]\b/, 'perceba'],
    [/\b(esse|este) grafico\b/, 'esse gráfico'], [/\bessa barra\b/, 'essa barra'],
    [/\b(esse|este) numero\b/, 'esse número'], [/\bdesse jeito\b/, 'desse jeito']
  ];

  /* Marcas de que alguém aparece — o formato é faceless. */
  const ROSTO = [
    [/\beu apareco\b/, 'eu apareço'], [/\bmeu rosto\b/, 'meu rosto'],
    [/\bna minha cara\b/, 'na minha cara'], [/\bme filmando\b/, 'me filmando'],
    [/\bgravei minha\b/, 'gravei minha'], [/\bta me vendo\b/, 'tá me vendo']
  ];

  /* Estrangeirismo evitável (os consagrados no Brasil ficam de fora). */
  const INGLES = ['mindset', 'budget', 'savings', 'goals', 'tips', 'money',
    'follow', 'link in bio', 'swipe', 'check', 'insights', 'growth', 'wealth'];

  const NUM_POR_EXTENSO = ['um', 'uma', 'dois', 'duas', 'tres', 'quatro', 'cinco', 'seis',
    'sete', 'oito', 'nove', 'dez', 'onze', 'doze', 'quinze', 'vinte', 'trinta', 'quarenta',
    'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa', 'cem', 'cento', 'duzentos',
    'trezentos', 'mil', 'milhao', 'milhoes', 'bilhao', 'metade', 'dobro', 'triplo',
    'por cento', 'reais', 'real', 'centavos'];

  /* Jargão de finanças que um iniciante não entende sozinho. Quem ensina
     define antes de usar — ou perde a pessoa na primeira frase. */
  const JARGAO = [
    'cdi', 'selic', 'ipca', 'rotativo', 'liquidez', 'amortizacao', 'iof', 'cet',
    'custo efetivo total', 'aporte', 'volatilidade', 'come-cotas', 'come cotas',
    'spread', 'fgc', 'lci', 'lca', 'alavancagem', 'renda variavel', 'renda fixa',
    'taxa de administracao', 'patrimonio liquido', 'dividendo', 'debenture',
    'marcacao a mercado', 'juros compostos', 'score'
  ];

  let ctxMedida = null;
  function medidor() {
    if (!ctxMedida) {
      const cv = document.createElement('canvas');
      cv.width = 10; cv.height = 10;
      ctxMedida = cv.getContext('2d');
    }
    return ctxMedida;
  }

  function achar(lista, txt) {
    for (let i = 0; i < lista.length; i++) if (lista[i][0].test(txt)) return lista[i][1];
    return null;
  }

  function temNumero(txt) {
    if (/\d/.test(txt)) return true;
    const n = U.normalizar(txt);
    return NUM_POR_EXTENSO.some(w => new RegExp('\\b' + w + '\\b').test(n));
  }

  /* ---------------------------------------------------------------
     Verificação
     --------------------------------------------------------------- */
  U.verificarPadrao = function (projeto, motor) {
    const itens = [];
    const cenas = projeto.cenas || [];
    const L = U.layout(projeto);
    const ctx = medidor();
    const add = (nivel, cena, regra, msg, comoResolver) =>
      itens.push({ nivel: nivel, cena: cena, regra: regra, msg: msg, comoResolver: comoResolver });

    if (!cenas.length) {
      add('erro', null, 'estrutura', 'O roteiro está vazio.', 'Adicione ao menos 3 cenas: gancho, dado e chamada.');
      return montar(itens, projeto, motor);
    }

    let abstratas = 0, alertas = 0, escuras = 0;

    cenas.forEach(function (c, i) {
      const n = i + 1;
      const titulo = String(c.titulo || '').trim();
      const narracao = String(c.narracao || '').trim();
      const nn = U.normalizar(narracao);
      const d = U.lerDados(c.dados);
      const dur = motor ? motor.duracoes[i] : 0;

      /* --- 1. entende sem áudio --- */
      if (!titulo) {
        add('erro', n, 'sem-audio', 'Cena ' + n + ' não tem texto na tela.',
          'Escreva a ideia da cena em até 8 palavras. Quem assiste no mudo precisa entender só com isso.');
      } else {
        const palavras = titulo.split(/\s+/).length;
        if (palavras > 9) {
          add('aviso', n, 'texto-grande', 'Cena ' + n + ': título com ' + palavras + ' palavras.',
            'Corte para 8 ou menos. Texto longo obriga a fonte a encolher e deixa de ser "texto grande".');
        }
        const aj = U.ajustar(ctx, titulo, {
          max: L.titulo.max, min: L.titulo.min, peso: 800,
          maxLargura: L.titulo.w, maxLinhas: L.titulo.linhas, entrelinha: 1.06
        });
        const minAceitavel = Math.round(L.u * 0.068);
        if (aj.tamanho < minAceitavel) {
          add('aviso', n, 'texto-grande',
            'Cena ' + n + ': o título coube em apenas ' + aj.tamanho + 'px (o alvo é ' + minAceitavel + 'px ou mais).',
            'Encurte o título ou mova parte dele para a linha de apoio.');
        }
      }

      /* --- 2. entende sem vídeo --- */
      if (!narracao) {
        add('aviso', n, 'sem-video', 'Cena ' + n + ' está sem narração.',
          'Escreva uma frase que faça sentido de olhos fechados. Sem ela o áudio tem um buraco.');
      } else {
        const forte = achar(DEIXIS_FORTE, nn);
        if (forte) {
          add('erro', n, 'sem-video', 'Cena ' + n + ': a narração aponta para a imagem ("' + forte + '").',
            'Diga a informação em vez de apontar. Troque "o número na tela" por "mil duzentos e quarenta reais".');
        } else {
          const fraca = achar(DEIXIS_FRACA, nn);
          if (fraca) {
            add('aviso', n, 'sem-video', 'Cena ' + n + ': "' + fraca + '" costuma esconder dependência da imagem.',
              'Releia só o áudio. Se a frase perde sentido sem a tela, reescreva.');
          }
        }
        if (U.normalizar(titulo) && U.normalizar(titulo) === nn) {
          add('aviso', n, 'sem-video', 'Cena ' + n + ': a narração repete o título palavra por palavra.',
            'A tela dá o resumo, o áudio dá o porquê. Duplicar desperdiça os dois canais.');
        }
        const temNumeroNaTela = temNumero(titulo) ||
          temNumero(String(d.valor || '')) ||
          (d.itens || []).some(it => temNumero(String(it.valor || '')));
        if (temNumeroNaTela && !temNumero(narracao)) {
          add('aviso', n, 'sem-video', 'Cena ' + n + ' mostra um número que a narração não fala.',
            'Quem está com o celular no bolso só ouve. Diga o número em voz alta.');
        }
        const palavrasNarr = narracao.split(/\s+/).length;
        if (palavrasNarr > 34) {
          add('aviso', n, 'ritmo', 'Cena ' + n + ': narração com ' + palavrasNarr + ' palavras (' + dur.toFixed(1) + 's).',
            'Quebre em duas cenas. Acima de ~13 segundos parados o espectador sai.');
        }
        const rosto = achar(ROSTO, nn);
        if (rosto) {
          add('aviso', n, 'faceless', 'Cena ' + n + ': "' + rosto + '" pressupõe alguém na câmera.',
            'O formato é faceless: fale do dinheiro, não de quem grava.');
        }
        const eng = INGLES.find(w => new RegExp('\\b' + w + '\\b').test(nn));
        if (eng) {
          add('aviso', n, 'portugues', 'Cena ' + n + ': "' + eng + '" em inglês.',
            'Escreva em português. O público brasileiro entende mais rápido e o texto na tela fica menor.');
        }
      }

      /* --- 6. cena concreta --- */
      const visual = U.VISUAIS[c.visual];
      if (!visual) {
        add('erro', n, 'concreta', 'Cena ' + n + ' aponta para um visual inexistente ("' + c.visual + '").',
          'Escolha um visual da lista.');
      } else {
        if (visual.abstrato) abstratas++;
        if (visual.precisaMidia) {
          if (!(motor && motor.midias && motor.midias[i])) {
            add('aviso', n, 'concreta', 'Cena ' + n + ' está no visual de mídia própria, mas sem arquivo.',
              'Carregue a imagem ou o vídeo no botão "imagem ou vídeo…" da cena, ou troque para uma cena desenhada.');
          }
        } else {
          const precisaDados = visual.exemplo && visual.exemplo.indexOf(':') >= 0;
          const vazio = !String(c.dados || '').trim();
          if (precisaDados && vazio) {
            add('aviso', n, 'concreta', 'Cena ' + n + ' usa "' + visual.rotulo + '" sem dados.',
              'Preencha os campos do visual. Um gráfico sem número é decoração, não cena concreta.');
          }
        }
      }
      if (c.tipo === 'alerta') alertas++;
      if (c.tom === 'escuro') escuras++;

      /* --- ritmo --- */
      if (dur && dur < 2.2) {
        add('aviso', n, 'ritmo', 'Cena ' + n + ' dura só ' + dur.toFixed(1) + 's.',
          'Menos de 2,2s não dá tempo de ler o texto grande.');
      }
      if (i > 0 && cenas[i - 1].visual === c.visual) {
        add('aviso', n, 'ritmo', 'Cenas ' + i + ' e ' + n + ' usam o mesmo visual.',
          'Alterne o tipo de cena. Duas iguais em sequência parecem um vídeo travado.');
      }
    });

    /* --- projeto --- */
    if (abstratas > 1) {
      add('aviso', null, 'concreta', abstratas + ' cenas são só tipografia.',
        'O padrão pede cena concreta: cartão, extrato, boleto, gráfico, celular. Deixe no máximo uma frase solta.');
    }
    const clima = projeto.clima || 'claro';
    if (clima !== 'escuro' && escuras && escuras > Math.ceil(cenas.length / 3)) {
      add('aviso', null, 'estetica', escuras + ' de ' + cenas.length + ' cenas mergulham no tom escuro.',
        'O mergulho é pontuação para dívida, juros e vencimento: entra, aperta e sai. ' +
        'Passando de um terço do vídeo, ele vira o clima em vez do susto — se é isso que você quer, ' +
        'troque o clima do projeto e devolva as cenas ao tom do projeto.');
    }
    if (clima === 'escuro' && escuras) {
      add('aviso', null, 'estetica', 'O clima já é escuro, e ' + escuras + ' cena(s) ainda pedem mergulho.',
        'Num clima escuro o mergulho não muda quase nada. Devolva essas cenas ao tom do projeto ' +
        'ou troque o clima para grafite, que deixa espaço para o escuro apertar.');
    }
    if (alertas > 1) {
      add('aviso', null, 'estetica', alertas + ' cenas de alerta (vermelho).',
        'Numa estética clara e premium, vermelho é pontuação. Use em uma cena só.');
    }
    const modo = (projeto.modo === 'aula' || projeto.modo === 'intersecao')
      ? projeto.modo : 'retencao';

    if (modo === 'retencao') {
      if (cenas[0] && cenas[0].tipo !== 'gancho') {
        add('aviso', 1, 'estrutura', 'A primeira cena não está marcada como gancho.',
          'Os 2 primeiros segundos decidem o vídeo. Abra com tensão ou com um número.');
      }
      if (cenas.length > 1 && cenas[cenas.length - 1].tipo !== 'cta') {
        add('aviso', cenas.length, 'estrutura', 'A última cena não é uma chamada.',
          'Termine com um passo concreto que a pessoa faz hoje.');
      }
    } else {
      verificarAula(cenas, add, motor, modo);
      if (modo === 'intersecao') verificarIntersecao(cenas, add, motor, projeto);
    }
    if (motor) {
      const t = motor.duracao;
      const faixaModo = U.MODOS[modo] || U.MODOS.retencao;
      if (t < faixaModo.min) {
        add('aviso', null, 'ritmo', 'O vídeo tem ' + t.toFixed(1) + 's.',
          modo === 'aula'
            ? 'Abaixo de ' + faixaModo.min + 's não cabe conceito, exemplo e recapitulação. Falta aula aqui.'
            : 'Abaixo de ' + faixaModo.min + 's não dá para entregar argumento e chamada. Some uma cena de dado.');
      } else if (t > faixaModo.max) {
        add('aviso', null, 'ritmo', 'O vídeo tem ' + t.toFixed(1) + 's.',
          modo === 'aula'
            ? 'Acima de ' + faixaModo.max + 's é melhor quebrar em duas aulas do que perder a pessoa no meio.'
            : 'Acima de 90s a retenção despenca em Reels. Corte a cena mais fraca.');
      }
      const palavrasTitulos = cenas.map(c => c.titulo || '').join(' ').split(/\s+/).filter(Boolean).length;
      if (cenas.length >= 3 && palavrasTitulos < 12) {
        add('aviso', null, 'sem-audio', 'Somados, os textos na tela têm só ' + palavrasTitulos + ' palavras.',
          'Leia os títulos em sequência: eles precisam contar a história inteira sozinhos.');
      }
    }

    return montar(itens, projeto, motor);
  };

  /* ---------------------------------------------------------------
     A CURVA DO VÍDEO

     Duas medidas por cena, na mesma linha do tempo:
       atenção     — o quanto a cena dá motivo para continuar assistindo
       aprendizado — o quanto a cena entrega algo que a pessoa leva embora

     Um vídeo de retenção pura tem atenção alta e aprendizado raso. Uma aula
     mal montada tem o inverso. A interseção é manter as duas curvas altas ao
     mesmo tempo — e o que essa medida serve é mostrar ONDE elas se separam.
     --------------------------------------------------------------- */

  const CONTRASTE = /\b(mas|so que|porem|no entanto|entretanto|e mesmo assim|ainda assim|na verdade)\b/;
  /* "Quanto sua conta perde por ano" é pergunta mesmo sem ponto de interrogação. */
  const INTERROGATIVO = /^(quanto|quantos|quanta|por que|porque|como|o que|que|quando|quem|qual|quais|sera que|vale a pena|e se)\b/;
  const CAUSA = /\b(porque|por isso|ou seja|isso significa|significa que|entao|logo|o motivo|a razao)\b/;

  function pontuarCena(c, i, cenas, motor) {
    const nn = U.normalizar(c.narracao);
    const tn = U.normalizar(c.titulo);
    const d = U.lerDados(c.dados);
    const visual = c.visual;
    let atencao = 0, aprendizado = 0;
    const marcas = [];

    /* --- atenção --- */
    const abreLacuna = c.tipo === 'pergunta' || visual === 'pergunta' ||
      /\?/.test(c.titulo + ' ' + (d.pergunta || '')) || INTERROGATIVO.test(tn);
    if (abreLacuna) { atencao += 0.38; marcas.push('lacuna'); }
    if (c.tipo === 'gancho') atencao += 0.20;
    if (c.tipo === 'previsao') { atencao += 0.22; marcas.push('previsao'); }
    if (c.tipo === 'surpresa' || CONTRASTE.test(nn)) { atencao += 0.30; marcas.push('surpresa'); }
    if (temNumero(c.titulo)) atencao += 0.24;
    if (c.tipo === 'alerta' || c.tipo === 'erro' || c.tom === 'escuro') atencao += 0.14;
    if (visual === 'conta' || visual === 'juros' || visual === 'linha') { atencao += 0.14; }
    if (i > 0 && cenas[i - 1].visual !== visual) atencao += 0.10;
    if (motor && motor.duracoes[i] <= 5) atencao += 0.08;
    if (c.tipo === 'resgate') { atencao += 0.20; marcas.push('resgate'); }

    /* --- aprendizado --- */
    if (visual === 'definicao' || c.tipo === 'conceito') { aprendizado += 0.42; marcas.push('conceito'); }
    if (visual === 'conta') { aprendizado += 0.42; marcas.push('conta'); }
    if (visual === 'recapitulacao' || c.tipo === 'recapitulacao') { aprendizado += 0.38; marcas.push('laco'); }
    if (visual === 'erroComum' || c.tipo === 'erro') aprendizado += 0.26;
    if (visual === 'checklist' || c.tipo === 'passo') aprendizado += 0.22;
    if (visual === 'comparativo') aprendizado += 0.20;
    if (CAUSA.test(nn)) aprendizado += 0.22;
    if (temNumero(c.narracao) && temNumero(c.titulo + ' ' + JSON.stringify(d))) aprendizado += 0.18;
    if (c.tipo === 'resgate') aprendizado += 0.24;
    if (visual === 'citacao' || visual === 'moedas') aprendizado -= 0.10;

    return {
      atencao: Math.max(0, Math.min(1, atencao)),
      aprendizado: Math.max(0, Math.min(1, aprendizado)),
      marcas: marcas
    };
  }

  U.curvaDoVideo = function (projeto, motor) {
    const cenas = projeto.cenas || [];
    const pontos = cenas.map(function (c, i) {
      const p = pontuarCena(c, i, cenas, motor);
      p.indice = i;
      p.inicio = motor ? motor.inicios[i] : i;
      p.dur = motor ? motor.duracoes[i] : 1;
      p.titulo = c.titulo;
      return p;
    });
    const media = function (campo) {
      return pontos.length ? pontos.reduce(function (s, p) { return s + p[campo]; }, 0) / pontos.length : 0;
    };
    const recursos = {};
    U.RECURSOS_INTERSECAO.forEach(function (r) {
      recursos[r.chave] = pontos.some(function (p) { return p.marcas.indexOf(r.chave) >= 0; });
    });
    /* o laço só conta como fechado se a pergunta de abertura for respondida */
    recursos.laco = recursos.laco && lacoFechado(cenas);
    return {
      pontos: pontos,
      atencao: media('atencao'),
      aprendizado: media('aprendizado'),
      recursos: recursos
    };
  };

  const VAZIAS = ['para', 'como', 'quanto', 'quando', 'sobre', 'isso', 'esse', 'essa', 'pelo',
    'pela', 'com', 'sem', 'mais', 'menos', 'você', 'voce', 'seu', 'sua', 'que', 'uma', 'dos', 'das'];

  function conteudo(txt) {
    return U.palavras(txt).filter(function (w) {
      return w.length > 3 && VAZIAS.indexOf(w) < 0 && !/^\d+$/.test(w);
    });
  }

  /* A pergunta que abriu o vídeo aparece respondida nas duas últimas cenas? */
  function lacoFechado(cenas) {
    if (cenas.length < 3) return false;
    const abre = cenas[0];
    const d = U.lerDados(abre.dados);
    const alvo = conteudo([abre.titulo, d.pergunta, abre.narracao].join(' '));
    if (!alvo.length) return false;
    const fim = conteudo(cenas.slice(-2).map(function (c) {
      return [c.titulo, c.apoio, c.narracao, c.dados].join(' ');
    }).join(' '));
    let comuns = 0;
    alvo.forEach(function (w) { if (fim.indexOf(w) >= 0) comuns++; });
    return comuns >= 2;
  }

  /* ---------------------------------------------------------------
     Interseção — retenção e didática no mesmo vídeo
     --------------------------------------------------------------- */
  function verificarIntersecao(cenas, add, motor, projeto) {
    const curva = U.curvaDoVideo(projeto, motor);
    const r = curva.recursos;

    if (!r.lacuna) {
      add('aviso', 1, 'intersecao', 'O vídeo não abre com uma pergunta.',
        'A pergunta que abre lacuna é o único recurso que é gancho e organizador prévio ao mesmo tempo: ' +
        'segura quem ia deslizar e prepara quem vai aprender.');
    }
    if (!r.previsao) {
      add('aviso', null, 'intersecao', 'Ninguém é convidado a arriscar uma resposta.',
        'Coloque uma cena de previsão antes do resultado. Quem arrisca um número fica para conferir ' +
        'e lembra melhor do que quem só recebe a resposta pronta.');
    }
    if (!r.surpresa) {
      add('aviso', null, 'intersecao', 'Nenhuma cena quebra a expectativa.',
        'Sem um "mas" no meio, o vídeo vira lista. Marque a cena onde o resultado contraria o esperado ' +
        'como surpresa — é o que segura e o que fixa.');
    }
    if (!r.conta) {
      add('aviso', null, 'intersecao', 'Não há conta feita na frente de quem assiste.',
        'A conta revelada linha a linha é micro-suspense e exemplo trabalhado no mesmo movimento.');
    }
    if (!r.laco) {
      add('erro', cenas.length, 'intersecao', 'O laço abriu e não fechou.',
        'A pergunta da abertura precisa aparecer respondida, com as mesmas palavras, nas duas últimas cenas. ' +
        'Sem isso o vídeo entrega informação mas quebra a promessa.');
    }
    if (motor && motor.duracao > 60 && !r.resgate) {
      add('aviso', null, 'intersecao', 'Vídeo longo sem nenhum resgate no meio.',
        'Passando de um minuto, inclua uma cena que retome o que já foi dito. Reengaja quem dispersou ' +
        'e obriga a memória a buscar o que aprendeu.');
    }

    /* vales: trechos longos sem nenhum motivo para continuar */
    if (motor) {
      let desde = 0, inicioVale = 0;
      curva.pontos.forEach(function (p, i) {
        if (p.atencao >= 0.45) { desde = 0; inicioVale = p.inicio + p.dur; }
        else {
          desde += p.dur;
          if (desde > 18) {
            add('aviso', i + 1, 'intersecao',
              'Vale de ' + desde.toFixed(0) + 's sem nada que segure, até a cena ' + (i + 1) + '.',
              'Esse é o trecho onde a pessoa sai. Quebre com uma pergunta, um número na tela ou uma ' +
              'quebra de expectativa — qualquer um dos três também ajuda a aprender.');
            desde = 0;
          }
        }
      });

      /* ensinou tarde: a primeira entrega real depois da metade */
      const primeiroAprendizado = curva.pontos.findIndex(function (p) { return p.aprendizado >= 0.4; });
      if (primeiroAprendizado >= 0) {
        const quando = curva.pontos[primeiroAprendizado].inicio;
        if (quando > motor.duracao * 0.45) {
          add('aviso', primeiroAprendizado + 1, 'intersecao',
            'A primeira entrega de conteúdo só chega aos ' + quando.toFixed(0) + 's.',
            'Metade do vídeo passou antes de a pessoa aprender qualquer coisa. Antecipe o conceito ou a conta.');
        }
      } else {
        add('aviso', null, 'intersecao', 'Nenhuma cena entrega conteúdo de verdade.',
          'Tem gancho e ritmo, mas ninguém sai sabendo nada. Falta conceito, conta ou recapitulação.');
      }
    }

    /* desequilíbrio geral */
    if (curva.atencao - curva.aprendizado > 0.30) {
      add('aviso', null, 'intersecao', 'O vídeo segura muito mais do que ensina.',
        'A curva de atenção está bem acima da de aprendizado. Troque uma cena de efeito por uma de conceito ou conta.');
    } else if (curva.aprendizado - curva.atencao > 0.30) {
      add('aviso', null, 'intersecao', 'O vídeo ensina muito mais do que segura.',
        'O conteúdo está lá, mas quase ninguém vai chegar até ele. Some uma pergunta, uma previsão ou uma surpresa.');
    }
  }

  /* ---------------------------------------------------------------
     Didática — roda nos modos aula e interseção
     --------------------------------------------------------------- */
  function verificarAula(cenas, add, motor, modo) {
    const papeis = cenas.map(function (c) { return c.tipo; });
    const visuais = cenas.map(function (c) { return c.visual; });
    /* No modo interseção estas três já são cobradas lá, com outra justificativa. */
    const soAula = modo !== 'intersecao';

    const abre = papeis[0];
    if (soAula && abre !== 'pergunta' && abre !== 'gancho' && abre !== 'conceito') {
      add('aviso', 1, 'didatica', 'A aula não abre com pergunta.',
        'Quem aprende precisa saber o que vai responder. Abra com a pergunta que a aula resolve, ' +
        'e dê tempo da pessoa arriscar uma resposta antes de você dar a sua.');
    }

    const temConceito = papeis.indexOf('conceito') >= 0 || visuais.indexOf('definicao') >= 0;
    if (!temConceito) {
      add('aviso', null, 'didatica', 'A aula não tem nenhuma cena de conceito.',
        'Sem o conceito, o exemplo vira truque decorado: funciona naquele número e em mais nenhum.');
    }

    const temExemplo = papeis.indexOf('exemplo') >= 0 || visuais.indexOf('conta') >= 0;
    if (soAula && !temExemplo) {
      add('aviso', null, 'didatica', 'A aula não tem exemplo com números.',
        'Faça a conta na frente de quem assiste, linha por linha. O visual "Conta passo a passo" existe para isso.');
    }

    const ultimas = papeis.slice(-2).concat(visuais.slice(-2));
    if (soAula && ultimas.indexOf('recapitulacao') < 0) {
      add('aviso', cenas.length, 'didatica', 'A aula termina sem recapitulação.',
        'O que não é repetido no fim não sobra. Feche com até 3 pontos numerados.');
    }

    const definidos = cenas.filter(function (c) { return c.visual === 'definicao'; })
      .map(function (c) { return U.normalizar(U.lerDados(c.dados).termo || ''); })
      .join(' | ');
    const textoTodo = U.normalizar(cenas.map(function (c) {
      return [c.titulo, c.apoio, c.narracao, c.dados].join(' ');
    }).join(' '));
    const semDefinir = JARGAO.filter(function (t) {
      return new RegExp('\\b' + t.replace(/-/g, '[- ]') + '\\b').test(textoTodo) &&
             definidos.indexOf(t) < 0;
    });
    if (semDefinir.length) {
      add('aviso', null, 'didatica',
        'Termo técnico sem definição: ' + semDefinir.slice(0, 4).join(', ') + '.',
        'Adicione uma cena "Definição de termo" antes do primeiro uso. Quem já sabe pula em 3 segundos; ' +
        'quem não sabe abandona o vídeo.');
    }

    cenas.forEach(function (c, i) {
      if (!motor) return;
      const ehConceito = c.tipo === 'conceito' || c.visual === 'definicao';
      if (ehConceito && motor.duracoes[i] < 4.5) {
        add('aviso', i + 1, 'didatica',
          'Cena ' + (i + 1) + ' explica um conceito em só ' + motor.duracoes[i].toFixed(1) + 's.',
          'Conceito precisa de tempo de leitura. Alongue a narração ou fixe a duração em 5 segundos ou mais.');
      }
      const frases = String(c.narracao || '').split(/[.!?]+/).map(function (f) { return f.trim(); })
        .filter(function (f) { return f.split(/\s+/).length > 3; });
      if (frases.length > 2) {
        add('aviso', i + 1, 'didatica', 'Cena ' + (i + 1) + ' tem ' + frases.length + ' ideias na narração.',
          'Uma ideia por cena. Quebre em duas — a tela muda junto e a pessoa acompanha.');
      }
    });
  }

  function montar(itens, projeto, motor) {
    const erros = itens.filter(i => i.nivel === 'erro').length;
    const avisos = itens.length - erros;
    const nota = Math.max(0, Math.min(100, 100 - erros * 12 - avisos * 4));
    const porRegra = {};
    itens.forEach(i => { porRegra[i.regra] = (porRegra[i.regra] || 0) + 1; });
    return {
      itens: itens, erros: erros, avisos: avisos, nota: nota, porRegra: porRegra,
      curva: U.curvaDoVideo(projeto, motor),
      leituraMuda: U.leituraMuda(projeto),
      leituraCega: U.leituraCega(projeto)
    };
  }

  /* O vídeo sem áudio: só o que aparece escrito. */
  U.leituraMuda = function (projeto) {
    return (projeto.cenas || []).map(function (c, i) {
      return (i + 1) + '. ' + (c.titulo || '(vazio)') + (c.apoio ? ' — ' + c.apoio : '');
    }).join('\n');
  };

  /* O áudio sem vídeo: só o que se ouve, corrido. */
  U.leituraCega = function (projeto) {
    return (projeto.cenas || []).map(c => String(c.narracao || '').trim())
      .filter(Boolean).join(' ');
  };

})(window.UMM);
