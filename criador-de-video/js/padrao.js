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
    if (escuras && escuras > Math.ceil(cenas.length / 3)) {
      add('aviso', null, 'estetica', escuras + ' de ' + cenas.length + ' cenas estão no tom escuro.',
        'A direção é clara. O escuro é pontuação para dívida, juros e vencimento: entra, aperta e sai. ' +
        'Passando de um terço do vídeo, ele vira o clima em vez do susto.');
    }
    if (alertas > 1) {
      add('aviso', null, 'estetica', alertas + ' cenas de alerta (vermelho).',
        'Numa estética clara e premium, vermelho é pontuação. Use em uma cena só.');
    }
    if (cenas[0] && cenas[0].tipo !== 'gancho') {
      add('aviso', 1, 'estrutura', 'A primeira cena não está marcada como gancho.',
        'Os 2 primeiros segundos decidem o vídeo. Abra com tensão ou com um número.');
    }
    if (cenas.length > 1 && cenas[cenas.length - 1].tipo !== 'cta') {
      add('aviso', cenas.length, 'estrutura', 'A última cena não é uma chamada.',
        'Termine com um passo concreto que a pessoa faz hoje.');
    }
    if (motor) {
      const t = motor.duracao;
      if (t < 15) {
        add('aviso', null, 'ritmo', 'O vídeo tem ' + t.toFixed(1) + 's.',
          'Abaixo de 15s não dá para entregar argumento e chamada. Some uma cena de dado.');
      } else if (t > 95) {
        add('aviso', null, 'ritmo', 'O vídeo tem ' + t.toFixed(1) + 's.',
          'Acima de 90s a retenção despenca em Reels. Corte a cena mais fraca.');
      }
      const palavrasTitulos = cenas.map(c => c.titulo || '').join(' ').split(/\s+/).filter(Boolean).length;
      if (cenas.length >= 3 && palavrasTitulos < 12) {
        add('aviso', null, 'sem-audio', 'Somados, os textos na tela têm só ' + palavrasTitulos + ' palavras.',
          'Leia os títulos em sequência: eles precisam contar a história inteira sozinhos.');
      }
    }

    return montar(itens, projeto, motor);
  };

  function montar(itens, projeto, motor) {
    const erros = itens.filter(i => i.nivel === 'erro').length;
    const avisos = itens.length - erros;
    const nota = Math.max(0, Math.min(100, 100 - erros * 12 - avisos * 4));
    const porRegra = {};
    itens.forEach(i => { porRegra[i.regra] = (porRegra[i.regra] || 0) + 1; });
    return {
      itens: itens, erros: erros, avisos: avisos, nota: nota, porRegra: porRegra,
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
