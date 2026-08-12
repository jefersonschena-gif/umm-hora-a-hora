/* UMM Studio — modelos de roteiro
   Três roteiros completos em pt-BR que já passam no verificador do padrão.
   Servem como ponto de partida e como referência do que é "narração
   autossuficiente" e "texto na tela que conta a história sozinho". */

(function (U) {
  'use strict';

  function c(o) { return U.novaCena(o); }

  U.MODELOS = [

    /* ============================================================ */
    {
      chave: 'tarifas',
      nome: 'As tarifas invisíveis',
      resumo: '7 cenas · ~50s · dado forte na abertura, corte prático no fim',
      projeto: {
        versao: 1,
        titulo: 'As tarifas invisíveis',
        formato: '9x16',
        fps: 30,
        areaSegura: true,
        marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
        voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
        cenas: [
          c({
            tipo: 'gancho', visual: 'numero', selo: 'por ano',
            titulo: 'Quanto sua conta perde por ano',
            apoio: 'sem que ninguém precise avisar você',
            dados: 'valor: R$ 1.240,00\nrotulo: em tarifas e assinaturas esquecidas\nnota: média de quatro cobranças mensais',
            narracao: 'Mil duzentos e quarenta reais por ano. É o que uma conta comum perde em tarifas e assinaturas que ninguém cancelou.'
          }),
          c({
            tipo: 'contexto', visual: 'extrato', selo: 'o vazamento',
            titulo: 'Quase sempre nas mesmas quatro linhas',
            dados: 'itens: Assinatura de streaming=-39,90 | Tarifa de pacote=-34,00 | Seguro nunca usado=-27,50 | Aplicativo esquecido=-19,90\nrodape: R$ 121,30 por mês',
            narracao: 'São quase sempre os mesmos quatro lançamentos, e juntos passam de cento e vinte reais por mês.'
          }),
          c({
            tipo: 'dado', visual: 'comparativo', selo: 'comparação',
            titulo: 'O mesmo serviço custa zero',
            dados: 'aRotulo: Conta com pacote de tarifas\naValor: R$ 408\nbRotulo: Conta digital sem tarifa\nbValor: R$ 0\nvence: b',
            narracao: 'Uma conta digital faz o mesmo serviço por zero real. São quatrocentos e oito reais por ano de diferença.'
          }),
          c({
            tipo: 'dado', visual: 'juros', selo: 'dez anos',
            titulo: 'Cortado hoje, rende por dez anos',
            dados: 'inicial: 0\naporte: 121\ntaxa: 0,9\nanos: 10\nrotulo: R$ 121 por mês a 0,9% ao mês',
            narracao: 'Cento e vinte e um reais por mês, guardados a zero vírgula nove por cento ao mês, viram quase vinte e seis mil reais em dez anos.'
          }),
          c({
            tipo: 'passo', visual: 'checklist', selo: '15 minutos',
            titulo: 'Três passos e acabou',
            dados: 'itens: Abra o extrato dos últimos 30 dias | Marque tudo que se repete | Cancele o que você não usou',
            narracao: 'Abra o extrato dos últimos trinta dias, marque tudo que se repete e cancele o que não foi usado no período.'
          }),
          c({
            tipo: 'passo', visual: 'calendario', selo: 'automático',
            titulo: 'Guardar antes de gastar',
            dados: 'mes: Todo mês\nmarcados: 5\nrotulo: dia 5, transferência automática',
            narracao: 'Depois de cortar, programe uma transferência automática para o dia seguinte ao salário.'
          }),
          c({
            tipo: 'cta', visual: 'chamada', selo: 'agora',
            titulo: 'Leia seu extrato hoje',
            dados: 'acao: Abra o app do banco e anote 3 cobranças que você não reconhece\nreforco: leva menos de 5 minutos',
            narracao: 'Abra o aplicativo do seu banco agora e anote três cobranças que você não reconhece.'
          })
        ]
      }
    },

    /* ============================================================ */
    {
      chave: 'parcelado',
      nome: 'O preço do parcelado sem juros',
      resumo: '6 cenas · ~45s · comparação de preço e efeito no limite',
      projeto: {
        versao: 1,
        titulo: 'O preco do parcelado sem juros',
        formato: '9x16',
        fps: 30,
        areaSegura: true,
        marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
        voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
        cenas: [
          c({
            tipo: 'gancho', visual: 'cartao', selo: 'atenção',
            titulo: 'Parcelado sem juros tem preço',
            apoio: 'ele só não aparece na etiqueta',
            dados: 'banco: Seu cartão\nfinal: 4417\nrotulo: Fatura do mês\nvalor: R$ 3.280,00',
            narracao: 'Parcelar sem juros parece de graça. Essa fatura de três mil duzentos e oitenta reais é a soma de escolhas que pareciam não custar nada.'
          }),
          c({
            tipo: 'dado', visual: 'comparativo', selo: 'mesma compra',
            titulo: 'Mesmo produto, dois preços',
            dados: 'aRotulo: 12x de R$ 118\naValor: R$ 1.418\nbRotulo: À vista com desconto\nbValor: R$ 1.050\nvence: b',
            narracao: 'O mesmo produto sai por mil e cinquenta reais à vista e por mil quatrocentos e dezoito reais em doze vezes.'
          }),
          c({
            tipo: 'dado', visual: 'numero', selo: 'diferença',
            titulo: 'R$ 368 a mais pelo mesmo item',
            dados: 'valor: R$ 368,00\nrotulo: 26% a mais, só por não pagar à vista',
            narracao: 'Trezentos e sessenta e oito reais de diferença. Vinte e seis por cento a mais pelo mesmo item.'
          }),
          c({
            tipo: 'alerta', visual: 'alerta', selo: 'o efeito escondido',
            titulo: 'A parcela trava seu limite',
            dados: 'titulo: O que ninguém conta\nitens: Cada parcela ocupa o limite por 12 meses | Você esquece a compra no terceiro mês | A fatura sobe sem compra nova',
            narracao: 'Cada parcela ocupa o seu limite por doze meses e some do seu controle a partir do terceiro mês.'
          }),
          c({
            tipo: 'passo', visual: 'checklist', selo: 'regra simples',
            titulo: 'Pergunte antes de escolher',
            dados: 'itens: Qual o preço à vista? | Qual a diferença em reais? | Meu dinheiro rende mais que isso?',
            narracao: 'Antes de parcelar, pergunte o preço à vista, calcule a diferença e só parcele se o seu dinheiro render mais do que ela.'
          }),
          c({
            tipo: 'cta', visual: 'chamada', selo: 'próxima compra',
            titulo: 'Peça o preço à vista',
            dados: 'acao: Na próxima compra acima de R$ 500, peça o valor à vista antes de escolher as parcelas\nreforco: uma pergunta, nenhum custo',
            narracao: 'Na próxima compra acima de quinhentos reais, peça o valor à vista antes de escolher as parcelas.'
          })
        ]
      }
    },

    /* ============================================================ */
    {
      chave: 'reserva',
      nome: 'Reserva de emergência',
      resumo: '6 cenas · ~45s · define, dimensiona e dá o primeiro passo',
      projeto: {
        versao: 1,
        titulo: 'Reserva de emergencia',
        formato: '9x16',
        fps: 30,
        areaSegura: true,
        marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
        voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
        cenas: [
          c({
            tipo: 'gancho', visual: 'notificacao', selo: 'terça-feira',
            titulo: 'A conta que chega sem avisar',
            apoio: 'e não espera o seu salário',
            dados: 'app: Oficina\ntitulo: Orçamento aprovado\ncorpo: R$ 2.180,00 em reparo do carro\nhora: agora',
            narracao: 'O carro quebra numa terça e o orçamento chega no mesmo dia. Sem reserva, essa terça vira dívida.'
          }),
          c({
            tipo: 'contexto', visual: 'cofre', selo: 'o conceito',
            titulo: 'Reserva se mede em meses',
            apoio: 'não em um número redondo',
            dados: 'valor: R$ 18.000\nrotulo: seis meses de custo fixo\nmeta: 100',
            narracao: 'Reserva não é um valor bonito. Para quem gasta três mil por mês, são dezoito mil reais parados e disponíveis.'
          }),
          c({
            tipo: 'dado', visual: 'barras', selo: 'custo fixo',
            titulo: 'Some só o que não dá para cortar',
            dados: 'itens: Aluguel=1.800 | Mercado=900 | Contas da casa=300\nsufixo: por mês\nmelhor: maior',
            narracao: 'Some aluguel, mercado e contas da casa. Três mil reais por mês, multiplicados por seis, dão o tamanho da sua reserva.'
          }),
          c({
            tipo: 'dado', visual: 'carteira', selo: 'onde guardar',
            titulo: 'Precisa render e sair no mesmo dia',
            dados: 'rotulo: Reserva aplicada\nvalor: R$ 18.240,00\nvariacao: +1,02% no mês\nitens: 9|10|11|12|13|15|16|18',
            narracao: 'A reserva precisa render pelo menos o CDI, cerca de um por cento ao mês, e sair no mesmo dia. Tesouro Selic e CDB de liquidez diária resolvem.'
          }),
          c({
            tipo: 'passo', visual: 'pix', selo: 'primeiro passo',
            titulo: 'Comece com R$ 100 agendados',
            dados: 'valor: R$ 100,00\npara: Reserva de emergência\nsituacao: Agendado para todo dia 6',
            narracao: 'Agende cem reais para o dia seguinte ao salário. Pequeno e automático vence grande e manual.'
          }),
          c({
            tipo: 'cta', visual: 'chamada', selo: 'hoje',
            titulo: 'Programe a primeira transferência',
            dados: 'acao: Abra o app do banco e agende a transferência para o próximo dia de pagamento\nreforco: dois minutos, uma vez só',
            narracao: 'Abra o aplicativo do banco e programe a primeira transferência automática para o próximo dia de pagamento.'
          })
        ]
      }
    }
  ];

  /* ============================================================
     Segue o arco da referência: cartão premium no claro, mergulho escuro
     na dívida e nos juros, volta ao claro no controle e no investimento.
     ============================================================ */
  U.MODELOS.push({
    chave: 'cartao-conta-controle',
    nome: 'O cartão, a conta e o controle',
    resumo: '7 cenas · ~55s · claro → escuro na dívida → claro no controle',
    projeto: {
      versao: 1,
      titulo: 'O cartao, a conta e o controle',
      formato: '9x16',
      fps: 30,
      escala: 1,
      areaSegura: true,
      marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
      voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
      cenas: [
        U.novaCena({
          tipo: 'gancho', visual: 'cartao', tom: 'claro', selo: 'o começo',
          titulo: 'O cartão não é o vilão',
          apoio: 'o que você faz com ele é',
          dados: 'banco: Seu banco\nfinal: 4417\nrotulo: Limite disponível\nvalor: R$ 8.400,00',
          narracao: 'Um cartão com oito mil e quatrocentos reais de limite não é dívida. Ele vira dívida no dia em que o limite passa a ser tratado como renda.'
        }),
        U.novaCena({
          tipo: 'contexto', visual: 'notificacao', tom: 'claro', selo: 'todo dia',
          titulo: 'Cada compra parece pequena',
          dados: 'app: Seu banco\ntitulo: Compra aprovada\ncorpo: R$ 129,90 em assinatura anual\nhora: agora',
          narracao: 'Cento e vinte e nove reais aqui, oitenta ali. Cada aviso isolado parece pequeno, e é exatamente por isso que ninguém soma.'
        }),
        U.novaCena({
          tipo: 'alerta', visual: 'boleto', tom: 'escuro', selo: 'dia 10',
          titulo: 'A conta chega somada',
          dados: 'valor: R$ 3.280,00\nvencimento: 10/09\nsituacao: VENCIDO\ntom: alerta',
          narracao: 'No dia dez chega a soma: três mil duzentos e oitenta reais. E aqui começa a parte cara.'
        }),
        U.novaCena({
          tipo: 'dado', visual: 'numero', tom: 'escuro', selo: 'rotativo',
          titulo: 'O juro do rotativo é outro patamar',
          dados: 'valor: 431%\nrotulo: ao ano, na média do crédito rotativo\nnota: pagar o mínimo aciona essa taxa',
          narracao: 'O rotativo do cartão trabalha na casa dos quatrocentos por cento ao ano. Pagar o mínimo não adia o problema, ele multiplica.'
        }),
        U.novaCena({
          tipo: 'passo', visual: 'checklist', tom: 'claro', selo: 'a virada',
          titulo: 'Três movimentos para sair',
          dados: 'itens: Troque o rotativo por um empréstimo mais barato | Corte as assinaturas do extrato | Pague a fatura inteira, sempre',
          narracao: 'São três movimentos: trocar o rotativo por um crédito mais barato, cortar as assinaturas do extrato e voltar a pagar a fatura inteira.'
        }),
        U.novaCena({
          tipo: 'dado', visual: 'carteira', tom: 'claro', selo: 'depois',
          titulo: 'O mesmo dinheiro, do outro lado',
          dados: 'rotulo: Investido\nvalor: R$ 24.600,00\nvariacao: +1,04% no mês\nitens: 9|10|12|13|15|17|20|24',
          narracao: 'O que ia para o juro passa a render pouco mais de um por cento ao mês. É o mesmo dinheiro, trabalhando para você.'
        }),
        U.novaCena({
          tipo: 'cta', visual: 'chamada', tom: 'claro', selo: 'hoje',
          titulo: 'Abra a fatura antes do dia 10',
          dados: 'acao: Some as assinaturas da fatura e cancele as duas maiores que você não usou\nreforco: cinco minutos, uma vez',
          narracao: 'Abra a fatura ainda hoje, some as assinaturas e cancele as duas maiores que você não usou neste mês.'
        })
      ]
    }
  });

  /* ============================================================
     AULA — outra estrutura: pergunta, conceito, conta, erro, recapitulação.
     Nada de gancho e chamada; aqui o objetivo é a pessoa saber fazer sozinha.
     ============================================================ */
  U.MODELOS.push({
    chave: 'aula-rotativo',
    nome: 'Aula: como o rotativo do cartão funciona',
    resumo: '7 cenas · ~95s · pergunta → conceito → conta → erro → recapitulação',
    projeto: {
      versao: 1,
      titulo: 'Aula - o rotativo do cartao',
      formato: '9x16',
      fps: 30,
      modo: 'aula',
      clima: 'grafite',
      escala: 1,
      areaSegura: true,
      marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
      voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
      cenas: [
        U.novaCena({
          tipo: 'pergunta', visual: 'pergunta', selo: 'aula 1',
          titulo: 'Quanto custa pagar só o mínimo?',
          dados: 'pergunta: Se a fatura é R$ 3.280 e você paga o mínimo, quanto deve no mês seguinte?\ndica: arrisque um número antes de continuar',
          narracao: 'Se a sua fatura é de três mil duzentos e oitenta reais e você paga só o mínimo, quanto você deve no mês seguinte? Pense num número.'
        }),
        U.novaCena({
          tipo: 'conceito', visual: 'definicao', selo: 'o termo',
          titulo: 'Primeiro, o que é rotativo',
          dados: 'termo: Rotativo\nclasse: crédito automático do cartão\nsignifica: o pedaço da fatura que você não pagou e que o banco empresta para você, cobrando a maior taxa de juros do mercado brasileiro\nnaoConfunda: com o parcelamento da fatura, que é outro contrato e costuma cobrar menos da metade',
          narracao: 'Rotativo é o pedaço da fatura que você não pagou e que o banco empresta automaticamente para você. É o crédito mais caro do país, e ele começa sem ninguém assinar nada.'
        }),
        U.novaCena({
          tipo: 'exemplo', visual: 'conta', selo: 'a conta',
          titulo: 'Agora a conta, linha por linha',
          dados: 'itens: Fatura do mês=R$ 3.280,00 | Você paga o mínimo, 15%=− R$ 492,00 | Sobra no rotativo=R$ 2.788,00 | Juro de 15% no mês=+ R$ 418,20\nresultado: R$ 3.206,20\nrotuloResultado: sua dívida no mês seguinte',
          narracao: 'Você paga quatrocentos e noventa e dois reais e sobram dois mil setecentos e oitenta e oito no rotativo. O juro de quinze por cento devolve quatrocentos e dezoito reais para a conta.'
        }),
        U.novaCena({
          tipo: 'dado', visual: 'numero', selo: 'a resposta',
          titulo: 'Você pagou e deve quase o mesmo',
          dados: 'valor: R$ 3.206,20\nrotulo: depois de pagar R$ 492,00\nnota: a dívida caiu 2% e o mês inteiro passou',
          narracao: 'Você tirou quatrocentos e noventa e dois reais do bolso e a dívida caiu setenta e quatro reais. Dois por cento. Esse é o buraco.'
        }),
        U.novaCena({
          tipo: 'erro', visual: 'erroComum', selo: 'o erro',
          titulo: 'O erro que quase todo mundo comete',
          dados: 'errado: Pagar o mínimo todo mês para manter o nome limpo\ncerto: Trocar a fatura inteira por um empréstimo pessoal e pagar o cartão de uma vez',
          narracao: 'Pagar o mínimo mantém o nome limpo e a dívida viva. Trocar a fatura por um empréstimo pessoal corta o juro para menos de um terço.'
        }),
        U.novaCena({
          tipo: 'passo', visual: 'checklist', selo: 'como sair',
          titulo: 'Como sair, em três passos',
          dados: 'itens: Peça a portabilidade da dívida no seu banco | Compare o custo total, não a parcela | Guarde o cartão até quitar',
          narracao: 'São três passos: pedir a portabilidade da dívida, comparar o custo total em vez da parcela, e guardar o cartão até quitar.'
        }),
        U.novaCena({
          tipo: 'recapitulacao', visual: 'recapitulacao', selo: 'para levar',
          titulo: 'O que precisa ficar',
          dados: 'itens: O rotativo cobra cerca de 15% ao mês | Pagar o mínimo é o que aciona o rotativo | Trocar por empréstimo pessoal corta o juro para menos de um terço',
          narracao: 'Três coisas: o rotativo cobra perto de quinze por cento ao mês, pagar o mínimo é o que aciona ele, e trocar por empréstimo pessoal corta o juro para menos de um terço.'
        })
      ]
    }
  });

  /* ============================================================
     INTERSEÇÃO — cada cena tenta segurar E ensinar ao mesmo tempo.
     A pergunta da abertura volta respondida no fim: o laço fecha.
     ============================================================ */
  U.MODELOS.push({
    chave: 'intersecao-minimo',
    nome: 'Interseção: o mínimo da fatura',
    resumo: '8 cenas · ~85s · pergunta → previsão → conta → surpresa → resgate → laço fechado',
    projeto: {
      versao: 1,
      titulo: 'O minimo da fatura',
      formato: '9x16',
      fps: 30,
      modo: 'intersecao',
      clima: 'grafite',
      escala: 1,
      areaSegura: true,
      marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
      voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
      cenas: [
        U.novaCena({
          tipo: 'pergunta', visual: 'pergunta', selo: 'a pergunta',
          titulo: 'Pagar o mínimo tira quanto da dívida?',
          dados: 'pergunta: Fatura de R$ 3.280. Você paga o mínimo. Quanto a dívida diminui?\ndica: guarde um número na cabeça',
          narracao: 'Numa fatura de três mil duzentos e oitenta reais, quanto a dívida diminui se você pagar só o mínimo? Guarde um número.'
        }),
        U.novaCena({
          tipo: 'previsao', visual: 'comparativo', selo: 'arrisque',
          titulo: 'A maioria chuta um destes dois',
          dados: 'aRotulo: Cai uns 15%\naValor: R$ 492\nbRotulo: Cai quase nada\nbValor: R$ 74\nvence: b',
          narracao: 'Quase todo mundo responde quatrocentos e noventa e dois reais, o valor que saiu do bolso. Segure sua resposta mais dez segundos.'
        }),
        U.novaCena({
          tipo: 'conceito', visual: 'definicao', selo: 'o termo',
          titulo: 'Por que some tão pouco?',
          apoio: 'a resposta tem nome, e não aparece na fatura',
          dados: 'termo: Rotativo\nclasse: crédito automático do cartão\nsignifica: o pedaço da fatura que você não pagou e que o banco empresta na hora, com a maior taxa de juros do mercado brasileiro\nnaoConfunda: com o parcelamento da fatura, que é outro contrato e cobra menos da metade',
          narracao: 'O que sobra da fatura vira rotativo, um empréstimo automático que ninguém assina, mas que cobra a maior taxa do mercado brasileiro.'
        }),
        U.novaCena({
          tipo: 'exemplo', visual: 'conta', selo: 'a conta',
          titulo: 'R$ 492 saem. Quanto some da dívida?',
          dados: 'itens: Fatura do mês=R$ 3.280,00 | Mínimo pago, 15%=− R$ 492,00 | Sobra no rotativo=R$ 2.788,00 | Juro de 15% no mês=+ R$ 418,20\nresultado: R$ 3.206,20\nrotuloResultado: sua dívida no mês seguinte',
          narracao: 'Saem quatrocentos e noventa e dois reais, sobram dois mil setecentos e oitenta e oito, mas o juro de quinze por cento devolve quatrocentos e dezoito para a conta.'
        }),
        U.novaCena({
          tipo: 'surpresa', visual: 'numero', tom: 'escuro', selo: 'a resposta',
          titulo: 'A dívida caiu R$ 74',
          apoio: 'você tirou R$ 492 do bolso',
          dados: 'valor: R$ 74,00\nrotulo: foi só isso que saiu da dívida\nnota: 2% em um mês inteiro',
          narracao: 'Setenta e quatro reais. Você tirou quatrocentos e noventa e dois do bolso, mas a dívida só caiu setenta e quatro, porque o resto virou juro.'
        }),
        U.novaCena({
          tipo: 'erro', visual: 'erroComum', selo: 'o erro',
          titulo: 'Por isso o mínimo não resolve',
          dados: 'errado: Pagar o mínimo todo mês para manter o nome limpo\ncerto: Trocar a fatura inteira por um empréstimo pessoal e quitar o cartão',
          narracao: 'Pagar o mínimo mantém o nome limpo e a dívida viva. Trocar por um empréstimo pessoal corta o juro para menos de um terço.'
        }),
        U.novaCena({
          tipo: 'resgate', visual: 'checklist', selo: 'lembra?',
          titulo: 'Lembra do número que você guardou?',
          dados: 'itens: Você imaginou uma queda grande | A queda real foi de R$ 74 | A diferença tem nome: rotativo',
          narracao: 'Compare com o número que você guardou no começo. A distância entre os dois tem nome, e o nome é rotativo.'
        }),
        U.novaCena({
          tipo: 'recapitulacao', visual: 'recapitulacao', selo: 'a resposta',
          titulo: 'Pagar o mínimo tira R$ 74 da dívida',
          dados: 'itens: O mínimo de R$ 492 derruba só R$ 74 da fatura | O resto vira rotativo, a 15% ao mês | Trocar por empréstimo pessoal corta o juro para menos de um terço',
          narracao: 'Respondendo a pergunta do começo: pagar o mínimo de quatrocentos e noventa e dois reais tira setenta e quatro reais da dívida. O resto vira rotativo.'
        })
      ]
    }
  });

  /* ============================================================
     INFLAÇÃO — a aula que o vídeo de referência quase deu.
     Mesma estrutura (problema → causas → IPCA → conclusão), com o que
     faltava lá: pergunta na abertura, o termo definido, uma conta que a
     pessoa acompanha, fonte na tela e o laço fechado no fim.
     ============================================================ */
  U.MODELOS.push({
    chave: 'inflacao',
    nome: 'Inflação em 1 minuto',
    resumo: '8 cenas · ~60s · editorial, câmera a cada 2,5s, com a conta na tela',
    projeto: {
      versao: 1,
      titulo: 'Inflacao em 1 minuto',
      formato: '9x16',
      fps: 30,
      modo: 'intersecao',
      clima: 'editorial',
      camera: 'editorial',
      escala: 1,
      areaSegura: true,
      marca: { nome: 'Dinheiro Claro', arroba: '@dinheiroclaro' },
      voz: { provedor: 'nenhum', vozId: 'pt_BR-faber-medium', velocidade: 1 },
      cenas: [
        U.novaCena({
          tipo: 'pergunta', visual: 'pergunta', selo: 'em 1 minuto',
          titulo: 'Quanto seu dinheiro perde em um ano?',
          dados: 'pergunta: Você guarda R$ 1.000 embaixo do colchão. Daqui a um ano, compra quanto?\ndica: chute um valor antes de continuar',
          narracao: 'Você guarda mil reais embaixo do colchão. Daqui a um ano, esse dinheiro compra quanto? Chute um valor.'
        }),
        U.novaCena({
          tipo: 'contexto', visual: 'moedas', selo: 'o problema',
          titulo: 'Por que o carrinho volta menor?',
          apoio: 'o número na carteira não muda; o que ele compra, sim',
          dados: 'itens: 10 | 9 | 8 | 7\nrotulo: as mesmas moedas comprando menos a cada ano',
          narracao: 'A nota continua valendo mil reais. O que muda é a quantidade de coisas que mil reais tiram da prateleira.'
        }),
        U.novaCena({
          tipo: 'conceito', visual: 'definicao', selo: 'o termo',
          titulo: 'Quem mede isso, e como?',
          dados: 'termo: IPCA\nclasse: o índice oficial de inflação no Brasil\nsignifica: o preço de uma cesta de produtos e serviços que as famílias realmente compram, acompanhado todo mês pelo IBGE\nnaoConfunda: com o preço de um produto só, porque cada item tem um peso diferente na cesta',
          fonte: 'IBGE — Sistema Nacional de Índices de Preços ao Consumidor',
          narracao: 'IPCA é o índice oficial de inflação no Brasil. O IBGE acompanha todo mês o preço de uma cesta do que as famílias de fato compram.'
        }),
        U.novaCena({
          tipo: 'exemplo', visual: 'conta', selo: 'a conta',
          titulo: 'R$ 1.000 guardados, 4,5% de inflação',
          dados: 'itens: Você guardou=R$ 1.000,00 | Preços sobem 4,5% no ano=× 1,045 | O mesmo carrinho passa a custar=R$ 1.045,00 | Com R$ 1.000 você leva=R$ 956,94\nresultado: − R$ 43,06\nrotuloResultado: foi o que o ano tirou de você',
          narracao: 'Com quatro e meio por cento de inflação, o carrinho de mil reais passa a custar mil e quarenta e cinco. Seus mil reais agora levam novecentos e cinquenta e seis.'
        }),
        U.novaCena({
          tipo: 'surpresa', visual: 'numero', tom: 'escuro', selo: 'a resposta',
          titulo: 'Parado, você perdeu R$ 43',
          apoio: 'sem gastar nada, sem errar nada',
          dados: 'valor: R$ 43,06\nrotulo: evaporaram de mil reais em doze meses\nnota: e o número na nota continuou o mesmo',
          narracao: 'Quarenta e três reais e seis centavos. Você não gastou, não errou, não fez nada. Mas perdeu.'
        }),
        U.novaCena({
          tipo: 'dado', visual: 'fluxo', selo: 'as causas',
          titulo: 'Três forças empurram o preço',
          dados: 'origem: Preço sobe\nitens: Demanda aquecida=puxa | Custo de produção=empurra | Expectativa=antecipa',
          narracao: 'São três as forças que empurram o preço para cima: procura maior que a oferta, custo de produção mais caro e expectativa de alta.'
        }),
        U.novaCena({
          tipo: 'resgate', visual: 'comparativo', selo: 'lembra?',
          titulo: 'Seu chute era maior ou menor?',
          dados: 'aRotulo: Guardado parado\naValor: R$ 956,94\nbRotulo: Rendendo a inflação\nbValor: R$ 1.000,00\nvence: b',
          narracao: 'Compare com o valor que você chutou no começo: parado, sobram novecentos e cinquenta e seis reais, e rendendo a inflação o poder de compra fica de pé.'
        }),
        U.novaCena({
          tipo: 'recapitulacao', visual: 'recapitulacao', selo: 'a resposta',
          titulo: 'Em um ano, R$ 1.000 viram R$ 957',
          dados: 'itens: Inflação é o carrinho encolhendo, não o número mudando | O IPCA mede a cesta que as famílias compram, medida pelo IBGE | Render abaixo da inflação é perder devagar',
          fonte: 'IBGE — IPCA',
          narracao: 'Respondendo o começo: mil reais parados viram novecentos e cinquenta e sete em poder de compra. Render abaixo da inflação é perder devagar.'
        })
      ]
    }
  });

  U.modeloVazio = function () {
    const p = U.novoProjeto();
    p.cenas = [
      U.novaCena({ tipo: 'gancho', visual: 'numero', titulo: '', narracao: '' }),
      U.novaCena({ tipo: 'dado', visual: 'barras', titulo: '', narracao: '' }),
      U.novaCena({ tipo: 'cta', visual: 'chamada', titulo: '', narracao: '' })
    ];
    return p;
  };

})(window.UMM);
