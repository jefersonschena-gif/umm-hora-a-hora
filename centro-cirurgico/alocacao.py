# -*- coding: utf-8 -*-
"""Distribuição dos técnicos pelos postos do dia.

Regras que a distribuição respeita, nesta ordem:
  1. só entra quem está disponível (ativo e sem folga/férias/atestado na data);
  2. ninguém em dois lugares — a dupla fica o turno inteiro no mesmo posto;
  3. falta gente é a regra: primeiro cada posto recebe o mínimo aceitável, na ordem de
     prioridade, e só depois os que sobram completam as duplas — assim o déficit vira
     posto operando no mínimo, não posto vazio;
  4. dentro do posto, prefere quem marca X nas especialidades que passam ali no dia;
  5. no empate, prefere quem tem menos habilidades, guardando os polivalentes para os
     postos que ainda virão.

Depois da distribuição inicial roda um passe de trocas: qualquer troca de dois técnicos
entre postos que aumente a cobertura total é aceita, até não haver mais ganho.
"""


def _cobertura(esp, equipe, skills):
    """Pontos de um posto: 1 por especialidade coberta, +0,5 se os dois cobrem."""
    if not esp:
        return 0.0
    p = 0.0
    for e in esp:
        n = sum(1 for t in equipe if e in skills.get(t, ()))
        p += 1.0 if n >= 1 else 0.0
        p += 0.5 if n >= 2 else 0.0
    return p


def alocar(postos, esp_por_posto, disponiveis, skills):
    """postos: [(cod, necessarios, minimo, prioridade)] · esp_por_posto: {cod: [especialidades]}
    disponiveis: [nome] · skills: {nome: set(especialidades marcadas com X)}
    Devolve {cod: [nomes]} — na ordem em que devem aparecer como TÉCNICO 1 e 2."""
    ordem = sorted(postos, key=lambda p: (p[3], p[0]))
    livres = sorted(disponiveis)
    aloc = {cod: [] for cod, _, _, _ in postos}

    def preencher(cod, quantos):
        esp = esp_por_posto.get(cod, [])
        for _ in range(quantos):
            if not livres:
                return
            escolhido = min(livres, key=lambda t: (
                -sum(1 for e in esp if e in skills.get(t, ())),   # cobre mais
                len(skills.get(t, ())),                           # menos polivalente
                t))
            livres.remove(escolhido)
            aloc[cod].append(escolhido)

    for cod, nec, minimo, _ in ordem:            # 1ª passada: o mínimo de cada posto
        preencher(cod, min(minimo, nec))
    for cod, nec, minimo, _ in ordem:            # 2ª passada: completa as duplas
        preencher(cod, nec - len(aloc[cod]))

    pesos = {cod: (max(p[3] for p in postos) + 1 - prio) for cod, _, _, prio in postos}

    def total():
        return sum(pesos[c] * _cobertura(esp_por_posto.get(c, []), aloc[c], skills) for c in aloc)

    melhor, codigos = total(), [c for c, _, _, _ in ordem if aloc[c]]
    for _ in range(20):
        ganhou = False
        for i, ca in enumerate(codigos):
            for cb in codigos[i + 1:]:
                for ia in range(len(aloc[ca])):
                    for ib in range(len(aloc[cb])):
                        aloc[ca][ia], aloc[cb][ib] = aloc[cb][ib], aloc[ca][ia]
                        novo = total()
                        if novo > melhor + 1e-9:
                            melhor, ganhou = novo, True
                        else:
                            aloc[ca][ia], aloc[cb][ib] = aloc[cb][ib], aloc[ca][ia]
        if not ganhou:
            break

    for cod in aloc:                       # ordem estável dentro da dupla
        aloc[cod].sort()
    return aloc
