# -*- coding: utf-8 -*-
"""Nomes das abas da planilha, num lugar só."""
ABA_PAINEL = "Painel"             # a primeira tela: o que fazer hoje
ABA_MAPA = "Mapa do Dia"          # o dia inteiro: quem fica em cada ambiente
ABA_AGENDA = "Agenda do Dia"      # as cirurgias vindas do PDF do hospital
ABA_EQUIPE = "Equipe"             # cadastro + o X de habilidade
ABA_FOLGAS = "Folgas e Férias"    # ausências + calendário do período
ABA_CFG = "Configuração"          # plantão, especialidades, postos, feriados, cirurgiões


def sem_texto_vazio(wb):
    """Troca célula com texto vazio ("") por célula realmente vazia.

    O openpyxl grava uma célula cujo valor é "" como t="inlineStr" SEM o <is> dentro, o que o
    formato não permite. O LibreOffice engole; o Excel considera o arquivo danificado e abre
    perguntando se quer recuperar o conteúdo. Chamar isto antes de salvar evita a pergunta.
    """
    for ws in wb.worksheets:
        for linha in ws.iter_rows():
            for c in linha:
                if c.data_type == "s" and c.value == "":
                    c.value = None
