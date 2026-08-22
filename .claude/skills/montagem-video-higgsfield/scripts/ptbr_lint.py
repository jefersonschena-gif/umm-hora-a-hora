#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lint de texto pt-BR para narracao (TTS), legenda e thumbnail.

Roda no sandbox do Higgsfield (ou local) sem dependencias externas.

Uso:
    python3 ptbr_lint.py --mode narracao --text-file roteiro.txt
    python3 ptbr_lint.py --mode narracao --script script_manifest.json
    python3 ptbr_lint.py --mode legenda  --srt final.srt
    python3 ptbr_lint.py --mode thumb    --text "MEDO DE VOAR?"

Saida: JSON {"issues":[{severity,code,line,term,msg,fix}], "counts":{...}}
Exit 1 se houver qualquer issue de severidade "erro".

Importavel:  from ptbr_lint import check_text
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

# --------------------------------------------------------------------------
# 1. Erros ortograficos inequivocos (forma errada -> forma correta)
# --------------------------------------------------------------------------
ORTOGRAFIA = {
    "concerteza": "com certeza", "derrepente": "de repente", "apartir": "a partir",
    "atravez": "através", "atraves": "através", "excessão": "exceção",
    "excessões": "exceções", "previlégio": "privilégio", "previlegio": "privilégio",
    "beneficiente": "beneficente", "menas": "menos", "seje": "seja", "sejem": "sejam",
    "esteje": "esteja", "estejem": "estejam", "poblema": "problema",
    "pobrema": "problema", "rúbrica": "rubrica", "asterístico": "asterisco",
    "asteristico": "asterisco", "entertido": "entretido",
    "entertenimento": "entretenimento", "impecilho": "empecilho",
    "empecílio": "empecilho", "afim de": "a fim de", "afimde": "a fim de",
    "a onde": "aonde", "de baixo de": "debaixo de", "en vez de": "em vez de",
    "haja visto": "haja vista", "vultuoso": "vultoso", "cabeleileiro": "cabeleireiro",
    "bandeija": "bandeja", "mortandela": "mortadela", "prazeiroso": "prazeroso",
    "advinhar": "adivinhar", "frustado": "frustrado", "frustação": "frustração",
    "quisexe": "quisesse", "veio a tona": "veio à tona", "as vezes": "às vezes",
    "as veses": "às vezes", "porisso": "por isso", "porquê que": "por que",
    "porque que": "por que", "pra mim fazer": "para eu fazer",
    "pra mim ver": "para eu ver", "para mim ver": "para eu ver",
    "entre eu e você": "entre mim e você", "houveram": "houve",
    "existe pessoas": "existem pessoas", "fazem anos": "faz anos",
    "fazem meses": "faz meses", "fazem dias": "faz dias", "concenso": "consenso",
    "disperdício": "desperdício", "disperdicio": "desperdício", "iorgute": "iogurte",
    "priviligiado": "privilegiado", "reinvindicar": "reivindicar",
    "reinvindicação": "reivindicação", "supérfulo": "supérfluo",
    "superfulo": "supérfluo", "xuxu": "chuchu", "descriminar": "discriminar",
}

# --------------------------------------------------------------------------
# 2. Palavras que perderam a acentuacao (forma sem acento -> forma correta)
#    So entram formas cuja versao sem acento NAO e' uma palavra valida.
# --------------------------------------------------------------------------
ACENTOS = {
    "nao": "não", "voce": "você", "voces": "vocês", "tambem": "também",
    "alem": "além", "ate": "até", "ja": "já", "sao": "são", "entao": "então",
    "porem": "porém", "alguem": "alguém", "ninguem": "ninguém", "tres": "três",
    "vao": "vão", "pao": "pão", "maes": "mães", "irmao": "irmão", "irmaos": "irmãos",
    "coracao": "coração", "atencao": "atenção", "informacao": "informação",
    "seculo": "século", "historia": "história", "memoria": "memória",
    "ciencia": "ciência", "experiencia": "experiência", "consequencia": "consequência",
    "diferenca": "diferença", "crianca": "criança", "criancas": "crianças",
    "cabeca": "cabeça", "comeca": "começa", "comecar": "começar", "forca": "força",
    "servico": "serviço", "preco": "preço", "aco": "aço", "acucar": "açúcar",
    "musica": "música", "medico": "médico", "publico": "público", "rapido": "rápido",
    "dificil": "difícil", "facil": "fácil", "possivel": "possível", "util": "útil",
    "ultimo": "último", "unico": "único", "proprio": "próprio", "proximo": "próximo",
    "otimo": "ótimo", "pessimo": "péssimo", "basico": "básico", "logico": "lógico",
    "quilometro": "quilômetro", "quilometros": "quilômetros", "numero": "número",
    "numeros": "números", "energia": "energia", "familia": "família",
    "agua": "água", "aguas": "águas", "area": "área", "areas": "áreas",
    "milhoes": "milhões", "bilhoes": "bilhões", "razao": "razão", "razoes": "razões",
    "questao": "questão", "questoes": "questões", "solucao": "solução",
    "solucoes": "soluções", "acao": "ação", "acoes": "ações", "regiao": "região",
    "sera": "será", "estao": "estão", "havera": "haverá",
    "tera": "terá", "fara": "fará", "podera": "poderá", "amanha": "amanhã",
    "manha": "manhã", "so": "só", "pos": "pós",
    "otica": "ótica", "video": "vídeo", "videos": "vídeos", "audio": "áudio",
    "titulo": "título", "titulos": "títulos",
    "protecao": "proteção", "duvida": "dúvida", "duvidas": "dúvidas",
    "sequencia": "sequência", "frequencia": "frequência", "policia": "polícia",
    "materia": "matéria", "misterio": "mistério", "silencio": "silêncio",
    "planicie": "planície", "climatico": "climático",
    "economico": "econômico", "eletrico": "elétrico", "eletronico": "eletrônico",
    "automatico": "automático", "pratica": "prática",
    "analise": "análise", "hipotese": "hipótese", "sintese": "síntese",
    "relogio": "relógio", "cronologia": "cronologia", "orgao": "órgão",
    "orgaos": "órgãos", "padrao": "padrão", "padroes": "padrões",
    "decada": "década", "decadas": "décadas", "epoca": "época", "epocas": "épocas",
    "camera": "câmera", "cameras": "câmeras", "cerebro": "cérebro",
    "estomago": "estômago", "musculo": "músculo", "musculos": "músculos",
    "oxigenio": "oxigênio", "hidrogenio": "hidrogênio", "atomo": "átomo",
    "atomos": "átomos", "molecula": "molécula", "moleculas": "moléculas",
    "satelite": "satélite", "satelites": "satélites", "planeta": "planeta",
    "quimica": "química", "fisica": "física", "matematica": "matemática",
    "geografia": "geografia", "biologia": "biologia", "estatistica": "estatística",
    "credito": "crédito", "creditos": "créditos", "imobiliario": "imobiliário",
    "imobiliaria": "imobiliária", "agronegocio": "agronegócio", "carencia": "carência",
    "desagio": "deságio", "liquida": "líquida", "liquido": "líquido",
    "liquidez": "liquidez", "minima": "mínima", "minimo": "mínimo",
    "maxima": "máxima", "maximo": "máximo", "juros": "juros", "isencao": "isenção",
    "tributacao": "tributação", "aplicacao": "aplicação", "aplicacoes": "aplicações",
    "instituicao": "instituição", "instituicoes": "instituições",
    "garantidor": "garantidor", "emissao": "emissão", "emissoes": "emissões",
    "vencimento": "vencimento", "titulo": "título", "titulos": "títulos",
    "indice": "índice", "indices": "índices", "patrimonio": "patrimônio",
    "divida": "dívida", "dividas": "dívidas", "salario": "salário",
    "deposito": "depósito", "depositos": "depósitos", "cambio": "câmbio",
    "prejuizo": "prejuízo", "prejuizos": "prejuízos", "lastro": "lastro",
}
# formas ambiguas que NAO devem ser marcadas automaticamente (existem sem acento)
AMBIGUAS = {"e", "a", "o", "as", "os", "para", "por", "esta", "este", "sobre",
            "seria", "cara", "mora", "acordo", "pais", "secretaria", "critica",
            "pratico", "publica", "sabia", "esta", "seria", "duvido"}

SUFIXO_ACENTO = [
    (re.compile(r"^([a-z]{2,})cao$"), "ção"),
    (re.compile(r"^([a-z]{2,})coes$"), "ções"),
    (re.compile(r"^([a-z]{2,})encia$"), "ência"),
    (re.compile(r"^([a-z]{2,})ancia$"), "ância"),
]

# --------------------------------------------------------------------------
# 3. Deixis visual — quebra a autonomia do audio ("so escutando eu entendo")
# --------------------------------------------------------------------------
DEIXIS_ERRO = [
    r"\bcomo (?:voc[êe]|vocês) (?:pode[m]? )?(?:v[êe]r?|est[áa] vendo)\b",
    r"\bcomo (?:se )?v[êe] (?:na|aqui|acima|abaixo)\b",
    r"\b(?:nesta|nessa|nesse|neste) (?:imagem|tela|cena|foto|figura|gr[áa]fico)\b",
    r"\bna (?:imagem|tela|figura|foto) (?:ao lado|acima|abaixo|aqui)\b",
    r"\b(?:olh[ae]|veja|repare|observe) (?:s[óo] )?(?:isso|isto|aqui|a[íi]|essa|esse)\b",
    r"\baqui (?:em cima|embaixo|do lado|na tela)\b",
    r"\b(?:acima|abaixo|ao lado|[àa] (?:direita|esquerda))\b",
    r"\beste (?:gr[áa]fico|n[úu]mero|desenho) (?:aqui|mostra)\b",
]
DEIXIS_AVISO = [
    r"\bisso a[íi]\b", r"\bisto aqui\b", r"\bessa coisa\b",
    r"\bveja s[óo]\b", r"\bd[êe] uma olhada\b",
]

# --------------------------------------------------------------------------
# 4. Muletas / clichê / linguagem de robô
# --------------------------------------------------------------------------
MULETAS = [
    r"\b[ée] importante (?:ressaltar|destacar|lembrar|mencionar)\b",
    r"\bvale (?:lembrar|ressaltar|destacar) que\b",
    r"\bneste v[íi]deo (?:vamos|voc[êe] vai)\b",
    r"\bsem mais delongas\b", r"\bno mundo de hoje\b", r"\bhoje em dia\b",
    r"\bcom certeza absoluta\b", r"\bbasicamente\b", r"\bliteralmente\b",
    r"\bde acordo com (?:estudos|especialistas)\b(?! d[eao])",
    r"\bem resumo,? (?:podemos dizer|conclu[íi]mos)\b",
    r"\bprepare-se para (?:se surpreender|descobrir)\b",
    r"\bvoc[êe] n[ãa]o vai acreditar\b", r"\bo que acontece a seguir\b",
    r"\bcurta,? comente e (?:se )?inscreva\b",
    r"\bfique at[ée] o final\b",
]

# --------------------------------------------------------------------------
# 5. Itens que quebram o TTS (numero, simbolo, sigla, abreviatura)
# --------------------------------------------------------------------------
RE_DIGITO = re.compile(r"\d")
RE_SIMBOLO = re.compile(r"[%$€£&@#/\\+=<>~^*_|°ºª×÷]")
RE_ABREV = re.compile(
    r"\b(dr|dra|sr|sra|srta|prof|profa|etc|ex|obs|p[áa]g|s[ée]c|vs|aprox|"
    r"km|kg|mg|ml|cm|mm|hrs?|min|seg|jan|fev|mar|abr|jun|jul|ago|set|out|nov|dez)\.",
    re.IGNORECASE)
RE_SIGLA = re.compile(r"\b[A-ZÀ-Ý]{2,}(?:-[A-ZÀ-Ý0-9]+)?\b")
RE_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿]")
RE_MARKDOWN = re.compile(r"(\*\*|__|`|\[[^\]]*\]\(|^#{1,6}\s)", re.MULTILINE)
RE_PARENTESE = re.compile(r"[()\[\]{}]")
RE_TOKEN = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", re.UNICODE)

SIGLAS_OK = {"TV", "DNA", "PIB", "CEO", "UTI", "ONU", "OMS", "IA", "PC", "GPS",
             "USB", "CPF", "SUS", "EUA", "UE", "AI", "OK"}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def _issue(sev, code, line, term, msg, fix=""):
    return {"severity": sev, "code": code, "line": line, "term": term,
            "msg": msg, "fix": fix}


def check_text(text: str, mode: str = "narracao", line_no: int = 0) -> list:
    """Retorna a lista de issues de UM trecho de texto."""
    out = []
    low = text.lower()
    ascii_low = strip_accents(low)
    is_fala = mode in ("narracao", "legenda")

    # --- ortografia -------------------------------------------------------
    for wrong, right in ORTOGRAFIA.items():
        if re.search(r"(?<!\w)" + re.escape(wrong) + r"(?!\w)", low):
            out.append(_issue("erro", "ORTOGRAFIA", line_no, wrong,
                              f'"{wrong}" nao existe / esta errado', right))

    # --- acentuacao -------------------------------------------------------
    tokens = RE_TOKEN.findall(text)
    sem_acento_total = 0
    for tk in tokens:
        tl = tk.lower()
        if tl in AMBIGUAS:
            continue
        if tl in ACENTOS and ACENTOS[tl].lower() != tl:
            out.append(_issue("erro", "ACENTO", line_no, tk,
                              f'"{tk}" sem acento', ACENTOS[tl]))
            continue
        if tl == strip_accents(tl):
            for rx, term in SUFIXO_ACENTO:
                if rx.match(tl) and len(tl) > 5:
                    out.append(_issue("erro", "ACENTO", line_no, tk,
                                      f'"{tk}" deveria terminar em "{term}"', ""))
                    break
        if tl != strip_accents(tl):
            sem_acento_total += 1
    if len(tokens) >= 25 and sem_acento_total == 0:
        out.append(_issue("erro", "SEM_ACENTUACAO", line_no, "",
                          "texto longo em pt-BR sem NENHUM acento — provavel perda de diacriticos", ""))

    # --- tipografia -------------------------------------------------------
    if "  " in text:
        out.append(_issue("aviso", "ESPACO_DUPLO", line_no, "", "espaco duplo", ""))
    if re.search(r"\s+[,.;:!?]", text):
        out.append(_issue("aviso", "ESPACO_PONTUACAO", line_no, "",
                          "espaco antes de pontuacao", ""))
    if re.search(r"[,.;:!?](?=[^\s\"'’)\]…\d])", text):
        out.append(_issue("aviso", "SEM_ESPACO", line_no, "",
                          "falta espaco depois da pontuacao", ""))
    m = re.search(r"\b(\w+)\s+\1\b", low)
    if m:
        out.append(_issue("aviso", "PALAVRA_REPETIDA", line_no, m.group(1),
                          f'palavra repetida: "{m.group(0)}"', ""))
    if RE_EMOJI.search(text):
        out.append(_issue("erro", "EMOJI", line_no, "", "emoji no texto", "remover"))
    if RE_MARKDOWN.search(text):
        out.append(_issue("erro", "MARKDOWN", line_no, "", "marcacao markdown no texto", "remover"))

    # --- especificos de fala (narracao e legenda espelham a fala) ---------
    if is_fala:
        if RE_DIGITO.search(text):
            out.append(_issue("erro", "NUMERO", line_no,
                              "".join(RE_DIGITO.findall(text))[:12],
                              "digito no texto falado — o TTS le errado",
                              "escrever por extenso (1990 -> mil novecentos e noventa)"))
        sim = RE_SIMBOLO.findall(text)
        if sim:
            out.append(_issue("erro", "SIMBOLO", line_no, "".join(sorted(set(sim)))[:12],
                              "simbolo no texto falado",
                              "escrever por extenso (% -> por cento, R$ -> reais)"))
        ab = RE_ABREV.findall(text)
        if ab:
            out.append(_issue("erro", "ABREVIATURA", line_no, ",".join(sorted(set(ab)))[:30],
                              "abreviatura no texto falado",
                              "escrever por extenso (Dr. -> doutor, etc. -> e assim por diante)"))
        for sg in RE_SIGLA.findall(text):
            if sg in SIGLAS_OK or len(sg) > 6:
                continue
            out.append(_issue("aviso", "SIGLA", line_no, sg,
                              f'sigla "{sg}" pode sair soletrada errado',
                              "grafar como se pronuncia (ex.: ONU -> Onu)"))
        if RE_PARENTESE.search(text):
            out.append(_issue("aviso", "PARENTESE", line_no, "",
                              "parenteses/colchetes no texto falado", "remover"))
        for rx in DEIXIS_ERRO:
            m = re.search(rx, low)
            if m:
                out.append(_issue("erro", "DEIXIS_VISUAL", line_no, m.group(0),
                                  "narracao depende da imagem — quebra o teste 'so escutando'",
                                  "nomear a coisa em vez de apontar para ela"))
        for rx in DEIXIS_AVISO:
            m = re.search(rx, low)
            if m:
                out.append(_issue("aviso", "DEIXIS_FRACA", line_no, m.group(0),
                                  "expressao apontadora — confira se o audio se sustenta sozinho", ""))
        for rx in MULETAS:
            m = re.search(rx, low)
            if m:
                out.append(_issue("aviso", "MULETA", line_no, m.group(0),
                                  "cliche/muleta — deixa a narracao generica", "cortar ou trocar por conteudo"))
        for frase in re.split(r"[.!?…]+", text):
            n = len(RE_TOKEN.findall(frase))
            if n > 28:
                out.append(_issue("aviso", "FRASE_LONGA", line_no, frase.strip()[:40],
                                  f"frase de {n} palavras — prosodia de TTS quebra", "dividir em duas"))
        if re.search(r"\b[A-ZÀ-Ý]{4,}\b", text) and mode == "narracao":
            out.append(_issue("aviso", "CAIXA_ALTA", line_no, "",
                              "palavra em CAIXA ALTA na narracao — o TTS pode soletrar", "usar minusculas"))
        if ascii_low.count(",") == 0 and len(tokens) > 22:
            out.append(_issue("aviso", "SEM_PAUSA", line_no, "",
                              "linha longa sem virgula — narracao sai sem respiro", "inserir virgula"))

    if mode == "thumb":
        n = len(tokens)
        if n > 5:
            out.append(_issue("erro", "THUMB_LONGO", line_no, "",
                              f"{n} palavras na thumbnail (max 5)", "cortar"))
        if len(text) > 30:
            out.append(_issue("aviso", "THUMB_CARACTERES", line_no, "",
                              f"{len(text)} caracteres (ideal <= 24)", ""))
    return out


def _parse_srt(path: str) -> list:
    txt = open(path, encoding="utf-8").read()
    blocks, cur = [], []
    for line in txt.splitlines():
        if line.strip() == "":
            if cur:
                blocks.append(cur)
                cur = []
        else:
            cur.append(line)
    if cur:
        blocks.append(cur)
    cues = []
    for b in blocks:
        body = [l for l in b if "-->" not in l and not re.fullmatch(r"\d+", l.strip())]
        if body:
            cues.append(" ".join(body))
    return cues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["narracao", "legenda", "thumb"], default="narracao")
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--script", help="script_manifest.json (blocks[].vo_line | beats[].phrase)")
    ap.add_argument("--srt")
    ap.add_argument("--json", help="grava o relatorio neste arquivo")
    a = ap.parse_args()

    lines = []
    if a.text:
        lines = [a.text]
    elif a.text_file:
        lines = [l for l in open(a.text_file, encoding="utf-8").read().splitlines() if l.strip()]
    elif a.script:
        d = json.load(open(a.script, encoding="utf-8"))
        rows = d.get("blocks") or d.get("beats") or []
        lines = [(r.get("vo_line") or r.get("phrase") or "") for r in rows]
    elif a.srt:
        lines = _parse_srt(a.srt)
    else:
        print("informe --text, --text-file, --script ou --srt", file=sys.stderr)
        return 2

    issues = []
    for i, line in enumerate(lines, 1):
        if line.strip():
            issues += check_text(line, a.mode, i)

    erros = sum(1 for i in issues if i["severity"] == "erro")
    report = {"mode": a.mode, "linhas": len(lines),
              "counts": {"erro": erros, "aviso": len(issues) - erros},
              "issues": issues}
    js = json.dumps(report, ensure_ascii=False, indent=2)
    if a.json:
        open(a.json, "w", encoding="utf-8").write(js)
    print(js)
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
