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
