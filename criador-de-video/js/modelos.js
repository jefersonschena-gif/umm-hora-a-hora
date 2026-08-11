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
